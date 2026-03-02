import hmac
import hashlib
from urllib.parse import urlencode
from typing import Dict, Any
import logging

from app.config.settings import settings


class TwilioValidator:
    """Service to validate Twilio webhook signatures for security"""

    def __init__(self):
        self.auth_token = settings.twilio_auth_token
        self.logger = logging.getLogger(__name__)

    def validate_request(self, url: str, params: Dict[str, str], signature: str) -> bool:
        """
        Validate the Twilio webhook request signature.

        Args:
            url: The URL the webhook was sent to
            params: The POST parameters from the webhook
            signature: The X-Twilio-Signature header value

        Returns:
            True if the signature is valid, False otherwise
        """
        if not self.auth_token:
            self.logger.error("Twilio auth token not configured")
            return False

        if not signature:
            self.logger.warning("No signature provided in webhook request")
            return False

        # Sort the parameters by key
        sorted_params = sorted(params.items())

        # Create the signature base string
        # The URL without query parameters + sorted parameter key-value pairs
        signature_base = url.encode('utf-8')

        for key, value in sorted_params:
            signature_base += key.encode('utf-8')
            signature_base += value.encode('utf-8')

        # Calculate the expected signature using HMAC-SHA1
        expected_signature = hmac.new(
            self.auth_token.encode('utf-8'),
            signature_base,
            hashlib.sha1
        ).digest()

        # Encode the expected signature in base64 format and remove trailing newline
        import base64
        expected_signature_b64 = base64.b64encode(expected_signature).decode('utf-8')

        # Compare the provided signature with the expected one
        is_valid = hmac.compare_digest(signature, expected_signature_b64)

        if not is_valid:
            self.logger.warning("Twilio webhook signature validation failed")
        else:
            self.logger.info("Twilio webhook signature validation passed")

        return is_valid

    def validate_webhook_signature(self, url: str, form_data: Dict[str, str], twilio_signature: str) -> bool:
        """
        Validate Twilio webhook signature for form data.

        Args:
            url: The webhook URL
            form_data: The form data from the request
            twilio_signature: The X-Twilio-Signature header value

        Returns:
            True if the signature is valid, False otherwise
        """
        return self.validate_request(url, form_data, twilio_signature)


# Global Twilio validator instance
twilio_validator = TwilioValidator()