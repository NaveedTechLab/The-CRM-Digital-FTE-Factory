import asyncio
import httpx
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
from ..config.settings import settings
from ..utils.logger import logger, log_delivery_attempt
from ..utils.retry_mechanism import get_retry_mechanism
from ..services.rate_limiter import get_rate_limiter, is_channel_limited, get_channel_status
from ..services.delivery_tracker import get_delivery_tracker


class WebNotificationService:
    """
    Webhook delivery service for web form responses
    """

    def __init__(self):
        """
        Initialize the web notification service
        """
        self.retry_mechanism = get_retry_mechanism()
        self.rate_limiter = get_rate_limiter()
        self.delivery_tracker = get_delivery_tracker()
        self.timeout = settings.delivery_timeout_seconds

    async def send_webhook(self, webhook_url: str, payload: Dict[str, Any],
                          message_id: Optional[str] = None,
                          attempt_number: int = 1) -> Dict[str, Any]:
        """
        Send a webhook notification to a customer's endpoint

        Args:
            webhook_url: URL to send the webhook to
            payload: Payload to send in the webhook
            message_id: ID of the outbound message (for tracking)
            attempt_number: Current delivery attempt number

        Returns:
            Dict[str, Any]: Result of the webhook sending operation
        """
        start_time = asyncio.get_event_loop().time()

        # Check rate limit before attempting to send
        is_limited = await is_channel_limited('webform')
        if is_limited:
            logger.warning(f"Webhook rate limit exceeded for message {message_id}")
            return {
                'success': False,
                'error': 'Rate limit exceeded',
                'rate_limit_hit': True
            }

        try:
            # Validate URL
            parsed_url = urlparse(webhook_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError(f"Invalid webhook URL: {webhook_url}")

            # Create HTTP client with timeout
            async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout)) as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers={
                        'Content-Type': 'application/json',
                        'User-Agent': f'{settings.app_name}/1.0'
                    }
                )

            end_time = asyncio.get_event_loop().time()
            processing_time_ms = int((end_time - start_time) * 1000)

            # Determine success based on status code
            success = 200 <= response.status_code < 300

            logger.info(
                f"Webhook sent to {webhook_url}",
                webhook_url=webhook_url,
                message_id=message_id,
                status_code=response.status_code,
                success=success,
                processing_time_ms=processing_time_ms
            )

            # Log the delivery attempt
            await self.delivery_tracker.log_delivery_attempt(
                outbound_message_id=message_id,
                attempt_number=attempt_number,
                channel='webform',
                delivery_method='webhook_post',
                request_payload=payload,
                response_payload=response.json() if response.content else {'status_code': response.status_code},
                status_code=response.status_code,
                success=success,
                processing_time_ms=processing_time_ms
            )

            return {
                'success': success,
                'status_code': response.status_code,
                'response': response.json() if response.content else None,
                'processing_time_ms': processing_time_ms
            }
        except httpx.TimeoutException as e:
            end_time = asyncio.get_event_loop().time()
            processing_time_ms = int((end_time - start_time) * 1000)

            error_msg = f"Request timed out after {self.timeout} seconds"
            logger.error(
                f"Webhook timeout for {webhook_url}: {error_msg}",
                webhook_url=webhook_url,
                message_id=message_id,
                attempt_number=attempt_number,
                processing_time_ms=processing_time_ms
            )

            # Log the failed delivery attempt
            await self.delivery_tracker.log_delivery_attempt(
                outbound_message_id=message_id,
                attempt_number=attempt_number,
                channel='webform',
                delivery_method='webhook_post',
                request_payload=payload,
                response_payload={'error': error_msg},
                status_code=408,  # Request Timeout
                success=False,
                error_message=error_msg,
                rate_limit_hit=False,
                processing_time_ms=processing_time_ms
            )

            return {
                'success': False,
                'error': error_msg,
                'rate_limit_hit': False,
                'processing_time_ms': processing_time_ms
            }
        except httpx.RequestError as e:
            end_time = asyncio.get_event_loop().time()
            processing_time_ms = int((end_time - start_time) * 1000)

            error_msg = str(e)
            logger.error(
                f"Request error sending webhook to {webhook_url}: {error_msg}",
                webhook_url=webhook_url,
                message_id=message_id,
                attempt_number=attempt_number,
                processing_time_ms=processing_time_ms
            )

            # Log the failed delivery attempt
            await self.delivery_tracker.log_delivery_attempt(
                outbound_message_id=message_id,
                attempt_number=attempt_number,
                channel='webform',
                delivery_method='webhook_post',
                request_payload=payload,
                response_payload={'error': error_msg},
                status_code=500,
                success=False,
                error_message=error_msg,
                rate_limit_hit=False,
                processing_time_ms=processing_time_ms
            )

            return {
                'success': False,
                'error': error_msg,
                'rate_limit_hit': False,
                'processing_time_ms': processing_time_ms
            }
        except Exception as e:
            end_time = asyncio.get_event_loop().time()
            processing_time_ms = int((end_time - start_time) * 1000)

            error_msg = str(e)
            logger.error(
                f"Unexpected error sending webhook to {webhook_url}: {error_msg}",
                webhook_url=webhook_url,
                message_id=message_id,
                attempt_number=attempt_number,
                processing_time_ms=processing_time_ms
            )

            # Log the failed delivery attempt
            await self.delivery_tracker.log_delivery_attempt(
                outbound_message_id=message_id,
                attempt_number=attempt_number,
                channel='webform',
                delivery_method='webhook_post',
                request_payload=payload,
                response_payload={'error': error_msg},
                status_code=500,
                success=False,
                error_message=error_msg,
                rate_limit_hit=False,
                processing_time_ms=processing_time_ms
            )

            return {
                'success': False,
                'error': error_msg,
                'rate_limit_hit': False,
                'processing_time_ms': processing_time_ms
            }

    async def send_webhook_with_retry(self, webhook_url: str, payload: Dict[str, Any],
                                    message_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a webhook with retry logic

        Args:
            webhook_url: URL to send the webhook to
            payload: Payload to send in the webhook
            message_id: ID of the outbound message (for tracking)

        Returns:
            Dict[str, Any]: Result of the webhook sending operation
        """
        attempt_count = 0

        async def attempt_send():
            nonlocal attempt_count
            attempt_count += 1
            return await self.send_webhook(
                webhook_url=webhook_url,
                payload=payload,
                message_id=message_id,
                attempt_number=attempt_count
            )

        try:
            result = await self.retry_mechanism.execute_delivery_with_retry(
                attempt_send,
                message_id=message_id,
                channel='webform'
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

    async def simulate_web_notification(self, session_id: str, message: str,
                                     message_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Simulate a web notification for web form responses (e.g., on-site alert)

        Args:
            session_id: Session ID for the web session
            message: Message to display as notification
            message_id: ID of the outbound message (for tracking)

        Returns:
            Dict[str, Any]: Result of the notification simulation
        """
        logger.info(
            f"Simulating web notification for session {session_id}",
            session_id=session_id,
            message_id=message_id
        )

        # In a real implementation, this might connect to a WebSocket server
        # or update a database that triggers a client-side notification
        # For now, we'll just log the simulated notification

        return {
            'success': True,
            'session_id': session_id,
            'message': message,
            'notification_type': 'web_form_alert',
            'simulated': True
        }

    async def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get the current rate limit status for web notifications

        Returns:
            Dict[str, Any]: Rate limit status information
        """
        return await get_channel_status('webform')

    def is_valid_webhook_url(self, url: str) -> bool:
        """
        Validate a webhook URL

        Args:
            url: Webhook URL to validate

        Returns:
            bool: True if valid, False otherwise
        """
        try:
            parsed = urlparse(url)
            return all([parsed.scheme in ['http', 'https'], parsed.netloc])
        except Exception:
            return False

    async def send_batch_webhooks(self, urls: List[str], payloads: List[Dict[str, Any]],
                                 message_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Send multiple webhooks in batch

        Args:
            urls: List of URLs to send webhooks to
            payloads: List of payloads to send
            message_ids: List of message IDs for tracking

        Returns:
            List[Dict[str, Any]]: Results of the webhook sending operations
        """
        results = []
        for url, payload, msg_id in zip(urls, payloads, message_ids):
            result = await self.send_webhook_with_retry(
                webhook_url=url,
                payload=payload,
                message_id=msg_id
            )
            results.append(result)

        return results


# Global web notification service instance
web_notification_service = WebNotificationService()


def get_web_notification_service() -> WebNotificationService:
    """
    Get the global web notification service instance

    Returns:
        WebNotificationService: The global web notification service instance
    """
    return web_notification_service


async def send_webhook(webhook_url: str, payload: Dict[str, Any],
                      message_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Send a webhook using the global web notification service instance

    Args:
        webhook_url: URL to send the webhook to
        payload: Payload to send in the webhook
        message_id: ID of the outbound message (for tracking)

    Returns:
        Dict[str, Any]: Result of the webhook sending operation
    """
    return await web_notification_service.send_webhook_with_retry(
        webhook_url=webhook_url,
        payload=payload,
        message_id=message_id
    )


async def simulate_web_notification(session_id: str, message: str,
                                 message_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Simulate a web notification using the global web notification service instance

    Args:
        session_id: Session ID for the web session
        message: Message to display as notification
        message_id: ID of the outbound message (for tracking)

    Returns:
        Dict[str, Any]: Result of the notification simulation
    """
    return await web_notification_service.simulate_web_notification(
        session_id=session_id,
        message=message,
        message_id=message_id
    )