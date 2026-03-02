import asyncio
import base64
from typing import Dict, Optional, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httplib2
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
import os
from ..config.settings import settings
from ..utils.logger import logger, log_delivery_attempt, log_rate_limit_event
from ..utils.retry_mechanism import get_retry_mechanism
from ..services.rate_limiter import get_rate_limiter, is_channel_limited, get_channel_status
from ..services.delivery_tracker import get_delivery_tracker


class GmailService:
    """
    Gmail API integration for email delivery with proper threading
    """

    def __init__(self):
        """
        Initialize the Gmail service
        """
        self.credentials_path = settings.gmail_credentials_path
        self.token_path = settings.gmail_token_path
        self.sender_email = settings.gmail_sender_email
        self.service = None
        self.retry_mechanism = get_retry_mechanism()
        self.rate_limiter = get_rate_limiter()
        self.delivery_tracker = get_delivery_tracker()

    async def initialize(self):
        """
        Initialize the Gmail API service
        """
        try:
            # Load credentials
            creds = None
            if os.path.exists(self.token_path):
                creds = Credentials.from_authorized_user_file(self.token_path, ['https://www.googleapis.com/auth/gmail.send'])

            # If there are no (valid) credentials available, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                    except RefreshError:
                        logger.error("Failed to refresh credentials. Please re-authenticate.")
                        return False
                else:
                    logger.error("No valid credentials found. Please authenticate.")
                    return False

            # Build the Gmail service
            self.service = build('gmail', 'v1', credentials=creds, cache_discovery=False)
            logger.info("Gmail service initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Gmail service: {str(e)}", error=str(e))
            return False

    def _create_message(self, sender: str, to: str, subject: str, message_text: str,
                       in_reply_to: Optional[str] = None, references: Optional[str] = None) -> Dict:
        """
        Create a message for an email

        Args:
            sender: Email address of the sender
            to: Email address of the recipient
            subject: Subject of the email
            message_text: Body of the email
            in_reply_to: Message-ID of the original message (for threading)
            references: References header for threading

        Returns:
            Dict: Message object
        """
        message = MIMEText(message_text)

        # Create multipart message if we have headers to add
        if in_reply_to or references:
            msg = MIMEMultipart()
            msg.attach(message)

            # Add threading headers
            if in_reply_to:
                msg['In-Reply-To'] = in_reply_to
            if references:
                msg['References'] = references

            # Set other required headers
            msg['From'] = sender
            msg['To'] = to
            msg['Subject'] = subject
            raw_message = msg.as_string()
        else:
            message['From'] = sender
            message['To'] = to
            message['Subject'] = subject
            raw_message = message.as_string()

        # Encode the message
        encoded_message = base64.urlsafe_b64encode(raw_message.encode()).decode()

        return {
            'raw': encoded_message
        }

    async def send_email(self, to: str, subject: str, body: str,
                        in_reply_to: Optional[str] = None,
                        references: Optional[str] = None,
                        message_id: Optional[str] = None,
                        attempt_number: int = 1) -> Dict[str, Any]:
        """
        Send an email via Gmail API

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
            in_reply_to: Message-ID to reply to (for threading)
            references: References header for threading
            message_id: ID of the outbound message (for tracking)
            attempt_number: Current delivery attempt number

        Returns:
            Dict[str, Any]: Result of the email sending operation
        """
        start_time = asyncio.get_event_loop().time()

        # Check rate limit before attempting to send
        is_limited = await is_channel_limited('gmail')
        if is_limited:
            logger.warning(f"Gmail rate limit exceeded for message {message_id}")
            return {
                'success': False,
                'error': 'Rate limit exceeded',
                'rate_limit_hit': True
            }

        try:
            # Create the message
            message = self._create_message(
                sender=self.sender_email,
                to=to,
                subject=subject,
                message_text=body,
                in_reply_to=in_reply_to,
                references=references
            )

            # Send the email
            if not self.service:
                raise Exception("Gmail service not initialized")

            sent_message = self.service.users().messages().send(
                userId="me",
                body=message
            ).execute()

            end_time = asyncio.get_event_loop().time()
            processing_time_ms = int((end_time - start_time) * 1000)

            logger.info(
                f"Email sent successfully to {to}",
                to=to,
                message_id=message_id,
                thread_id=sent_message.get('id'),
                processing_time_ms=processing_time_ms
            )

            # Log the delivery attempt
            await self.delivery_tracker.log_delivery_attempt(
                outbound_message_id=message_id,
                attempt_number=attempt_number,
                channel='gmail',
                delivery_method='gmail_api',
                request_payload={'to': to, 'subject': subject},
                response_payload={'message_id': sent_message.get('id')},
                status_code=200,
                success=True,
                processing_time_ms=processing_time_ms
            )

            return {
                'success': True,
                'message_id': sent_message.get('id'),
                'thread_id': sent_message.get('threadId'),
                'processing_time_ms': processing_time_ms
            }
        except Exception as e:
            end_time = asyncio.get_event_loop().time()
            processing_time_ms = int((end_time - start_time) * 1000)

            error_msg = str(e)
            logger.error(
                f"Failed to send email to {to}: {error_msg}",
                to=to,
                message_id=message_id,
                attempt_number=attempt_number,
                processing_time_ms=processing_time_ms
            )

            # Determine if this is a rate limit error
            rate_limit_hit = 'quota' in error_msg.lower() or 'rate' in error_msg.lower()

            # Log the failed delivery attempt
            await self.delivery_tracker.log_delivery_attempt(
                outbound_message_id=message_id,
                attempt_number=attempt_number,
                channel='gmail',
                delivery_method='gmail_api',
                request_payload={'to': to, 'subject': subject},
                response_payload={'error': error_msg},
                status_code=500,
                success=False,
                error_message=error_msg,
                rate_limit_hit=rate_limit_hit,
                processing_time_ms=processing_time_ms
            )

            return {
                'success': False,
                'error': error_msg,
                'rate_limit_hit': rate_limit_hit,
                'processing_time_ms': processing_time_ms
            }

    async def send_email_with_retry(self, to: str, subject: str, body: str,
                                   in_reply_to: Optional[str] = None,
                                   references: Optional[str] = None,
                                   message_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send an email with retry logic

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
            in_reply_to: Message-ID to reply to (for threading)
            references: References header for threading
            message_id: ID of the outbound message (for tracking)

        Returns:
            Dict[str, Any]: Result of the email sending operation
        """
        attempt_count = 0

        async def attempt_send():
            nonlocal attempt_count
            attempt_count += 1
            return await self.send_email(
                to=to,
                subject=subject,
                body=body,
                in_reply_to=in_reply_to,
                references=references,
                message_id=message_id,
                attempt_number=attempt_count
            )

        try:
            result = await self.retry_mechanism.execute_delivery_with_retry(
                attempt_send,
                message_id=message_id,
                channel='gmail'
            )
            return result
        except Exception as e:
            logger.error(
                f"All retry attempts failed for message {message_id}",
                message_id=message_id,
                error=str(e)
            )
            return {
                'success': False,
                'error': str(e),
                'final_attempt': attempt_count
            }

    async def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get the current rate limit status for Gmail

        Returns:
            Dict[str, Any]: Rate limit status information
        """
        return await get_channel_status('gmail')

    def is_valid_email(self, email: str) -> bool:
        """
        Basic email validation

        Args:
            email: Email address to validate

        Returns:
            bool: True if valid, False otherwise
        """
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None


# Global Gmail service instance
gmail_service = GmailService()


async def initialize_gmail_service():
    """
    Initialize the global Gmail service instance
    """
    return await gmail_service.initialize()


def get_gmail_service() -> GmailService:
    """
    Get the global Gmail service instance

    Returns:
        GmailService: The global Gmail service instance
    """
    return gmail_service


async def send_email(to: str, subject: str, body: str,
                    in_reply_to: Optional[str] = None,
                    references: Optional[str] = None,
                    message_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Send an email using the global Gmail service instance

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body
        in_reply_to: Message-ID to reply to (for threading)
        references: References header for threading
        message_id: ID of the outbound message (for tracking)

    Returns:
        Dict[str, Any]: Result of the email sending operation
    """
    return await gmail_service.send_email_with_retry(
        to=to,
        subject=subject,
        body=body,
        in_reply_to=in_reply_to,
        references=references,
        message_id=message_id
    )