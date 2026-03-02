#!/usr/bin/env python3
"""
Gmail Poller Service

Polls Gmail API for new unread messages and processes them through the ingestion pipeline.
This service runs continuously and polls Gmail at regular intervals.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta
import base64
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.services.ingestion_service import ingestion_service
from app.config.settings import settings


class GmailPoller:
    """Service to poll Gmail API for new messages"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.service = None
        self.scopes = ['https://www.googleapis.com/auth/gmail.readonly']

    def authenticate(self):
        """Authenticate with Gmail API using OAuth2"""
        creds = None

        # The file token.json stores the user's access and refresh tokens.
        # This file is created automatically when the authorization flow completes for the first time.
        if settings.gmail_refresh_token:
            # Create credentials from the refresh token
            creds = Credentials(
                token=None,  # Will be refreshed automatically
                refresh_token=settings.gmail_refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=settings.gmail_client_id,
                client_secret=settings.gmail_client_secret,
                scopes=self.scopes
            )
        else:
            self.logger.error("Gmail credentials not configured properly")
            return False

        try:
            # Build the Gmail service
            self.service = build('gmail', 'v1', credentials=creds)
            self.logger.info("Successfully authenticated with Gmail API")
            return True
        except Exception as e:
            self.logger.error(f"Failed to authenticate with Gmail API: {str(e)}")
            return False

    def get_unread_messages(self) -> List[Dict[str, Any]]:
        """Get unread messages from Gmail"""
        if not self.service:
            self.logger.error("Gmail service not initialized")
            return []

        try:
            # Query for unread messages
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=10  # Limit to 10 messages per poll
            ).execute()

            messages = results.get('messages', [])

            # Get full message details for each message
            full_messages = []
            for msg in messages:
                message_detail = self.get_message_details(msg['id'])
                if message_detail:
                    full_messages.append(message_detail)

            self.logger.info(f"Retrieved {len(full_messages)} unread messages")
            return full_messages

        except HttpError as error:
            self.logger.error(f"Gmail API error: {error}")
            return []
        except Exception as e:
            self.logger.error(f"Error retrieving messages: {str(e)}")
            return []

    def get_message_details(self, msg_id: str) -> Dict[str, Any]:
        """Get full details of a specific message"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id
            ).execute()

            # Parse the message
            parsed_message = self.parse_message(message)
            return parsed_message

        except HttpError as error:
            self.logger.error(f"Error getting message {msg_id}: {error}")
            return {}
        except Exception as e:
            self.logger.error(f"Error parsing message {msg_id}: {str(e)}")
            return {}

    def parse_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Gmail message into our standard format"""
        try:
            # Extract headers
            headers = {header['name'].lower(): header['value'] for header in message['payload'].get('headers', [])}

            # Extract message parts
            body = ""
            attachments = []

            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain' and not body:
                        if 'data' in part['body']:
                            body_data = part['body']['data']
                            body = base64.urlsafe_b64decode(body_data.encode('ASCII')).decode('utf-8')
            else:
                # Single part message
                if 'body' in message['payload'] and 'data' in message['payload']['body']:
                    body_data = message['payload']['body']['data']
                    body = base64.urlsafe_b64decode(body_data.encode('ASCII')).decode('utf-8')

            # Create standardized message format
            parsed_msg = {
                'message_id': message['id'],
                'thread_id': message.get('threadId', ''),
                'from': headers.get('from', ''),
                'to': headers.get('to', ''),
                'subject': headers.get('subject', ''),
                'body': body,
                'snippet': message.get('snippet', ''),
                'timestamp': datetime.fromtimestamp(int(message['internalDate']) / 1000).isoformat(),
                'size_estimate': message.get('sizeEstimate', 0),
                'raw_payload': message,  # Store original payload
                'attachments': attachments
            }

            return parsed_msg

        except Exception as e:
            self.logger.error(f"Error parsing message: {str(e)}")
            return {}

    async def mark_as_read(self, msg_id: str) -> bool:
        """Mark a message as read to prevent reprocessing"""
        if not self.service:
            return False

        try:
            # Modify message labels to remove 'UNREAD' label
            self.service.users().messages().modify(
                userId='me',
                id=msg_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()

            self.logger.debug(f"Marked message {msg_id} as read")
            return True

        except Exception as e:
            self.logger.error(f"Error marking message {msg_id} as read: {str(e)}")
            return False

    async def process_message(self, message: Dict[str, Any]):
        """Process a single Gmail message through the ingestion pipeline"""
        try:
            self.logger.info(f"Processing Gmail message: {message.get('subject', 'No Subject')}")

            # Process the message through the ingestion pipeline
            result = await ingestion_service.ingest_gmail_message(message)

            if result.get("success"):
                # Mark as read only after successful processing
                await self.mark_as_read(message['message_id'])
                self.logger.info(f"Successfully processed Gmail message: {message['message_id']}")
            else:
                self.logger.error(f"Failed to process Gmail message {message['message_id']}: {result.get('error')}")

        except Exception as e:
            self.logger.error(f"Error processing Gmail message: {str(e)}", exc_info=True)

    async def poll_once(self):
        """Poll Gmail once and process all unread messages"""
        try:
            self.logger.info("Starting Gmail poll cycle...")

            # Get unread messages
            messages = self.get_unread_messages()

            # Process each message
            for message in messages:
                await self.process_message(message)

            self.logger.info(f"Completed poll cycle. Processed {len(messages)} messages.")

        except Exception as e:
            self.logger.error(f"Error during poll cycle: {str(e)}", exc_info=True)

    async def start_polling(self):
        """Start continuous polling"""
        if not self.authenticate():
            self.logger.error("Cannot start polling - authentication failed")
            return

        self.logger.info(f"Starting Gmail polling service with {settings.gmail_polling_interval}s interval")

        while True:
            try:
                await self.poll_once()
                await asyncio.sleep(settings.gmail_polling_interval)
            except KeyboardInterrupt:
                self.logger.info("Gmail poller stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in polling loop: {str(e)}", exc_info=True)
                # Wait before retrying to avoid rapid restart loops
                await asyncio.sleep(settings.gmail_polling_interval)


async def main():
    """Main function to run the Gmail poller"""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    poller = GmailPoller()

    try:
        await poller.start_polling()
    except KeyboardInterrupt:
        print("Gmail poller stopped by user")


if __name__ == "__main__":
    asyncio.run(main())