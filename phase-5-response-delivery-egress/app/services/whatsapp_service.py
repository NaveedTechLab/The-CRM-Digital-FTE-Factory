import asyncio
import httpx
import re
from typing import Dict, Any, Optional
from twilio.rest import Client as TwilioClient
from ..config.settings import settings
from ..utils.logger import logger, log_delivery_attempt
from ..utils.retry_mechanism import get_retry_mechanism
from ..services.rate_limiter import get_rate_limiter, is_channel_limited, get_channel_status
from ..services.delivery_tracker import get_delivery_tracker

META_API_URL = "https://graph.facebook.com/v21.0"


class WhatsAppService:
    """
    WhatsApp message delivery with automatic fallback:
      1. Try Meta WhatsApp Cloud API first
      2. If Meta fails (test-mode / unregistered recipient), fall back to Twilio
      3. If both fail, store response for retrieval via API

    This ensures ANY number gets a response regardless of Meta test-mode restrictions.
    """

    def __init__(self):
        # Meta Cloud API credentials
        self.access_token = settings.whatsapp_access_token
        self.phone_number_id = settings.whatsapp_phone_number_id

        # Twilio credentials (fallback)
        self.twilio_account_sid = settings.twilio_account_sid
        self.twilio_auth_token = settings.twilio_auth_token
        self.twilio_whatsapp_number = settings.twilio_whatsapp_number
        self.twilio_client = None

        self.retry_mechanism = get_retry_mechanism()
        self.rate_limiter = get_rate_limiter()
        self.delivery_tracker = get_delivery_tracker()
        self.meta_initialized = False
        self.twilio_initialized = False

        # In-memory store for pending responses (fallback when both APIs fail)
        # Maps phone_number -> list of pending response dicts
        self._pending_responses: Dict[str, list] = {}

    async def initialize(self):
        """Initialize Meta Cloud API and Twilio (fallback) credentials"""
        # --- Meta Cloud API ---
        try:
            if self.access_token and self.phone_number_id:
                url = f"{META_API_URL}/{self.phone_number_id}"
                headers = {"Authorization": f"Bearer {self.access_token}"}
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.get(url, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        logger.info(f"Meta WhatsApp initialized - Number: {data.get('display_phone_number', 'unknown')}")
                        self.meta_initialized = True
                    else:
                        logger.warning(f"Meta WhatsApp credentials invalid: {resp.status_code}")
            else:
                logger.warning("Meta WhatsApp credentials not configured")
        except Exception as e:
            logger.warning(f"Meta WhatsApp init failed: {e}")

        # --- Twilio (fallback) ---
        try:
            if self.twilio_account_sid and self.twilio_auth_token and self.twilio_whatsapp_number:
                self.twilio_client = TwilioClient(self.twilio_account_sid, self.twilio_auth_token)
                self.twilio_initialized = True
                logger.info(f"Twilio WhatsApp fallback initialized - Number: {self.twilio_whatsapp_number}")
            else:
                logger.warning("Twilio credentials not configured - fallback disabled")
        except Exception as e:
            logger.warning(f"Twilio init failed: {e}")

        if not self.meta_initialized and not self.twilio_initialized:
            logger.error("Neither Meta nor Twilio WhatsApp configured - delivery will fail")
            return False

        return True

    # ------------------------------------------------------------------
    # Phone number normalization
    # ------------------------------------------------------------------

    def _normalize_phone_number(self, raw_number: str) -> str:
        """
        Normalize phone number to international format (digits only, no leading 0).

        Handles formats:
          - whatsapp:+923132303222 -> 923132303222
          - +923132303222          -> 923132303222
          - 923132303222           -> 923132303222
          - 03132303222            -> 923132303222  (Pakistani local -> international)
        """
        phone = raw_number.replace('whatsapp:', '').replace('+', '').strip()

        # Pakistani local numbers: 03xx -> 923xx
        if phone.startswith('0') and len(phone) == 11:
            phone = '92' + phone[1:]

        return phone

    # ------------------------------------------------------------------
    # Meta Cloud API delivery
    # ------------------------------------------------------------------

    async def _send_via_meta(self, phone: str, message_body: str,
                             message_id: Optional[str] = None,
                             attempt_number: int = 1) -> Dict[str, Any]:
        """Send via Meta WhatsApp Cloud API. Returns result dict with 'success' key."""
        if not self.meta_initialized:
            return {'success': False, 'error': 'Meta API not initialized', 'method': 'meta'}

        start_time = asyncio.get_event_loop().time()

        try:
            url = f"{META_API_URL}/{self.phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": phone,
                "type": "text",
                "text": {"preview_url": False, "body": message_body}
            }

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(url, headers=headers, json=payload)

            end_time = asyncio.get_event_loop().time()
            processing_time_ms = int((end_time - start_time) * 1000)

            if response.status_code == 200:
                data = response.json()
                msg_id_returned = data.get("messages", [{}])[0].get("id", "unknown")
                logger.info(f"[META] WhatsApp message sent to +{phone} (id={msg_id_returned})")

                await self.delivery_tracker.log_delivery_attempt(
                    outbound_message_id=message_id,
                    attempt_number=attempt_number,
                    channel='whatsapp',
                    delivery_method='meta_cloud_api',
                    request_payload={'to': phone, 'body': message_body},
                    response_payload=data,
                    status_code=200,
                    success=True,
                    processing_time_ms=processing_time_ms
                )

                return {
                    'success': True,
                    'message_id': msg_id_returned,
                    'to': phone,
                    'method': 'meta',
                    'processing_time_ms': processing_time_ms
                }
            else:
                error_data = response.json()
                error_obj = error_data.get("error", {})
                error_msg = error_obj.get("message", response.text)
                error_code = error_obj.get("code", 0)

                # Detect test-mode / unregistered recipient errors
                is_test_mode_error = (
                    error_code in (131030, 131026, 131047, 131031, 131009) or
                    "not a valid whatsapp" in error_msg.lower() or
                    "recipient" in error_msg.lower() or
                    "not part of" in error_msg.lower() or
                    "incapable" in error_msg.lower()
                )

                if is_test_mode_error:
                    logger.warning(
                        f"[META] Test-mode rejection for +{phone} (code={error_code}). "
                        f"Will try Twilio fallback. Error: {error_msg}"
                    )
                else:
                    logger.error(f"[META] API error for +{phone}: {response.status_code} - {error_msg}")

                await self.delivery_tracker.log_delivery_attempt(
                    outbound_message_id=message_id,
                    attempt_number=attempt_number,
                    channel='whatsapp',
                    delivery_method='meta_cloud_api',
                    request_payload={'to': phone, 'body': message_body},
                    response_payload=error_data,
                    status_code=response.status_code,
                    success=False,
                    error_message=error_msg,
                    processing_time_ms=processing_time_ms
                )

                return {
                    'success': False,
                    'error': error_msg,
                    'error_code': error_code,
                    'is_test_mode_error': is_test_mode_error,
                    'method': 'meta',
                    'processing_time_ms': processing_time_ms
                }

        except Exception as e:
            logger.error(f"[META] Exception sending to +{phone}: {e}")
            return {'success': False, 'error': str(e), 'method': 'meta'}

    # ------------------------------------------------------------------
    # Twilio fallback delivery
    # ------------------------------------------------------------------

    async def _send_via_twilio(self, phone: str, message_body: str,
                               message_id: Optional[str] = None,
                               attempt_number: int = 1) -> Dict[str, Any]:
        """Send via Twilio WhatsApp API (fallback). Returns result dict with 'success' key."""
        if not self.twilio_initialized or not self.twilio_client:
            return {'success': False, 'error': 'Twilio not initialized', 'method': 'twilio'}

        start_time = asyncio.get_event_loop().time()

        try:
            # Twilio expects whatsapp:+XXXXXXXXXXX format
            to_number = f"whatsapp:+{phone}"
            from_number = self.twilio_whatsapp_number

            # Run Twilio SDK call in executor (it's synchronous)
            loop = asyncio.get_event_loop()
            message = await loop.run_in_executor(
                None,
                lambda: self.twilio_client.messages.create(
                    body=message_body,
                    from_=from_number,
                    to=to_number
                )
            )

            end_time = asyncio.get_event_loop().time()
            processing_time_ms = int((end_time - start_time) * 1000)

            logger.info(f"[TWILIO] WhatsApp message sent to +{phone} (sid={message.sid})")

            await self.delivery_tracker.log_delivery_attempt(
                outbound_message_id=message_id,
                attempt_number=attempt_number,
                channel='whatsapp',
                delivery_method='twilio_api',
                request_payload={'to': to_number, 'body': message_body},
                response_payload={'sid': message.sid, 'status': message.status},
                status_code=200,
                success=True,
                processing_time_ms=processing_time_ms
            )

            return {
                'success': True,
                'message_id': message.sid,
                'to': phone,
                'method': 'twilio',
                'processing_time_ms': processing_time_ms
            }

        except Exception as e:
            end_time = asyncio.get_event_loop().time()
            processing_time_ms = int((end_time - start_time) * 1000)
            error_msg = str(e)
            logger.error(f"[TWILIO] Failed to send to +{phone}: {error_msg}")

            await self.delivery_tracker.log_delivery_attempt(
                outbound_message_id=message_id,
                attempt_number=attempt_number,
                channel='whatsapp',
                delivery_method='twilio_api',
                request_payload={'to': f"whatsapp:+{phone}", 'body': message_body},
                response_payload={'error': error_msg},
                status_code=500,
                success=False,
                error_message=error_msg,
                processing_time_ms=processing_time_ms
            )

            return {
                'success': False,
                'error': error_msg,
                'method': 'twilio',
                'processing_time_ms': processing_time_ms
            }

    # ------------------------------------------------------------------
    # Pending response storage (last-resort fallback)
    # ------------------------------------------------------------------

    def _store_pending_response(self, phone: str, message_body: str,
                                message_id: Optional[str] = None) -> Dict[str, Any]:
        """Store response for later retrieval when both Meta and Twilio fail."""
        import time
        entry = {
            'message_id': message_id,
            'content': message_body,
            'timestamp': time.time(),
            'phone': phone,
            'delivered': False
        }
        if phone not in self._pending_responses:
            self._pending_responses[phone] = []
        self._pending_responses[phone].append(entry)
        logger.info(f"[STORED] Response stored for +{phone} (message_id={message_id}). "
                     f"Total pending: {len(self._pending_responses[phone])}")
        return entry

    def get_pending_responses(self, phone: str) -> list:
        """Retrieve pending responses for a phone number (used by status API)."""
        normalized = self._normalize_phone_number(phone)
        return self._pending_responses.get(normalized, [])

    def clear_pending_responses(self, phone: str):
        """Clear pending responses after retrieval."""
        normalized = self._normalize_phone_number(phone)
        self._pending_responses.pop(normalized, None)

    # ------------------------------------------------------------------
    # Main send method with Meta -> Twilio -> Store fallback chain
    # ------------------------------------------------------------------

    async def send_message(self, to: str, message_body: str, message_id: Optional[str] = None,
                          attempt_number: int = 1) -> Dict[str, Any]:
        """
        Send a WhatsApp message with automatic fallback:
          1. Try Meta Cloud API
          2. If Meta fails, try Twilio
          3. If both fail, store response for retrieval

        Args:
            to: Recipient phone number (any format)
            message_body: Message text
            message_id: Tracking ID
            attempt_number: Retry attempt number
        """
        # Check rate limit
        is_limited = await is_channel_limited('whatsapp')
        if is_limited:
            logger.warning(f"WhatsApp rate limit exceeded for message {message_id}")
            return {'success': False, 'error': 'Rate limit exceeded', 'rate_limit_hit': True}

        # Normalize phone number
        phone = self._normalize_phone_number(to)

        # --- Step 1: Try Meta Cloud API ---
        meta_result = await self._send_via_meta(phone, message_body, message_id, attempt_number)
        if meta_result.get('success'):
            return meta_result

        # --- Step 2: If Meta failed, try Twilio fallback ---
        logger.info(f"Meta delivery failed for +{phone}, trying Twilio fallback...")
        twilio_result = await self._send_via_twilio(phone, message_body, message_id, attempt_number)
        if twilio_result.get('success'):
            return twilio_result

        # --- Step 3: Both failed - store response for retrieval ---
        logger.warning(f"Both Meta and Twilio failed for +{phone}. Storing response for retrieval.")
        stored = self._store_pending_response(phone, message_body, message_id)

        return {
            'success': False,
            'error': f"Meta: {meta_result.get('error', 'unknown')} | Twilio: {twilio_result.get('error', 'unknown')}",
            'stored_for_retrieval': True,
            'to': phone,
            'message_id': message_id,
            'hint': (
                "Message stored for retrieval. To fix delivery permanently: "
                "1) Add test numbers in Meta Developer Console, or "
                "2) Switch Meta app to Live mode, or "
                "3) Ensure Twilio sandbox is joined (send 'join <keyword>' to sandbox number)"
            )
        }

    async def send_message_with_retry(self, to: str, message_body: str,
                                     message_id: Optional[str] = None) -> Dict[str, Any]:
        """Send with retry logic"""
        attempt_count = 0

        async def attempt_send():
            nonlocal attempt_count
            attempt_count += 1
            return await self.send_message(to=to, message_body=message_body,
                                          message_id=message_id, attempt_number=attempt_count)
        try:
            return await self.retry_mechanism.execute_delivery_with_retry(
                attempt_send, message_id=message_id, channel='whatsapp'
            )
        except Exception as e:
            return {'success': False, 'error': str(e), 'final_attempt': attempt_count}

    def is_valid_whatsapp_number(self, number: str) -> bool:
        normalized = self._normalize_phone_number(number)
        return bool(re.match(r'^[1-9]\d{6,14}$', normalized))


# Global instance
whatsapp_service = WhatsAppService()


async def initialize_whatsapp_service():
    return await whatsapp_service.initialize()


def get_whatsapp_service() -> WhatsAppService:
    return whatsapp_service


async def send_whatsapp_message(to: str, message_body: str,
                                message_id: Optional[str] = None) -> Dict[str, Any]:
    return await whatsapp_service.send_message_with_retry(
        to=to, message_body=message_body, message_id=message_id
    )
