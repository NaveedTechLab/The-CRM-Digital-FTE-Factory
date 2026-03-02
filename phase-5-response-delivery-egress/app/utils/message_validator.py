import re
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
from ..models.outbound_message import OutboundMessage

class MessageValidator:
    """
    Validates outbound messages according to the defined validation rules
    """

    def __init__(self):
        """
        Initialize the message validator
        """
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self.phone_pattern = re.compile(r'^\+[1-9]\d{1,14}$')  # E.164 format
        self.whatsapp_pattern = re.compile(r'^whatsapp:[\+]?[1-9]\d{1,14}$')  # WhatsApp format

    def validate_outbound_message(self, message: OutboundMessage) -> List[str]:
        """
        Validate an outbound message according to the defined validation rules

        Args:
            message: The OutboundMessage to validate

        Returns:
            List[str]: List of validation errors, empty if valid
        """
        errors = []

        # Validate message_id
        if not message.message_id:
            errors.append("message_id must be valid")

        # Validate content
        if not message.content:
            errors.append("content must not be empty")

        # Validate channel_destination
        if message.channel_destination not in ['gmail', 'whatsapp', 'webform']:
            errors.append("channel_destination must be one of the allowed values")

        # Validate delivery_status
        if message.delivery_status not in ['pending', 'in_progress', 'delivered', 'failed', 'retrying']:
            errors.append("delivery_status must be one of the allowed values")

        # Validate delivery_attempts
        if (message.delivery_attempts or 0) < 0:
            errors.append("delivery_attempts must be non-negative")

        # Validate priority
        if message.priority not in ['low', 'normal', 'high']:
            errors.append("priority must be one of the allowed values")

        # Validate recipient_identifier based on channel type
        recipient_errors = self.validate_recipient_identifier(
            message.recipient_identifier, message.channel_destination
        )
        errors.extend(recipient_errors)

        return errors

    def validate_recipient_identifier(self, recipient_id: str, channel_type: str) -> List[str]:
        """
        Validate the recipient identifier based on the channel type

        Args:
            recipient_id: The recipient identifier to validate
            channel_type: The channel type ('gmail', 'whatsapp', 'webform')

        Returns:
            List[str]: List of validation errors, empty if valid
        """
        errors = []

        if not recipient_id:
            errors.append("recipient_identifier cannot be empty")
            return errors

        if channel_type == 'gmail':
            if not self.is_valid_email(recipient_id):
                errors.append(f"invalid email address: {recipient_id}")
        elif channel_type == 'whatsapp':
            if not self.is_valid_whatsapp_number(recipient_id):
                errors.append(f"invalid WhatsApp number: {recipient_id}")
        elif channel_type == 'webform':
            # Webform accepts webhook URLs, email addresses, or customer identifiers
            if not (self.is_valid_webhook_url(recipient_id) or self.is_valid_email(recipient_id) or recipient_id):
                errors.append(f"invalid webform recipient: {recipient_id}")
        else:
            errors.append(f"unsupported channel type: {channel_type}")

        return errors

    def is_valid_email(self, email: str) -> bool:
        """
        Validate an email address

        Args:
            email: Email address to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not email:
            return False
        return bool(self.email_pattern.match(email))

    def is_valid_phone_number(self, phone: str) -> bool:
        """
        Validate a phone number in E.164 format

        Args:
            phone: Phone number to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not phone:
            return False
        return bool(self.phone_pattern.match(phone.lstrip('+')))

    def is_valid_whatsapp_number(self, whatsapp: str) -> bool:
        """
        Validate a WhatsApp number - accepts 'whatsapp:+1234567890' or plain E.164 '+1234567890'

        Args:
            whatsapp: WhatsApp number to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not whatsapp:
            return False
        # Accept whatsapp: prefixed format
        if self.whatsapp_pattern.match(whatsapp):
            return True
        # Also accept plain E.164 format like +923003627458
        return bool(self.phone_pattern.match(whatsapp))

    def is_valid_webhook_url(self, url: str) -> bool:
        """
        Validate a webhook URL

        Args:
            url: Webhook URL to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not url:
            return False

        try:
            parsed = urlparse(url)
            return all([parsed.scheme in ['http', 'https'], parsed.netloc])
        except Exception:
            return False

    def validate_message_content(self, content: str, max_length: int = 10000) -> List[str]:
        """
        Validate message content

        Args:
            content: Content to validate
            max_length: Maximum allowed length (default 10000 chars)

        Returns:
            List[str]: List of validation errors, empty if valid
        """
        errors = []

        if not content:
            errors.append("content cannot be empty")
        elif len(content) > max_length:
            errors.append(f"content exceeds maximum length of {max_length} characters")

        # Check for potentially dangerous content
        if '<script>' in content.lower():
            errors.append("content contains potentially dangerous script tags")

        return errors

    def validate_channel_destination(self, channel: str) -> List[str]:
        """
        Validate the channel destination

        Args:
            channel: Channel to validate

        Returns:
            List[str]: List of validation errors, empty if valid
        """
        errors = []

        if channel not in ['gmail', 'whatsapp', 'webform']:
            errors.append(f"channel_destination must be one of 'gmail', 'whatsapp', 'webform', got '{channel}'")

        return errors

    def validate_priority(self, priority: str) -> List[str]:
        """
        Validate the priority level

        Args:
            priority: Priority to validate

        Returns:
            List[str]: List of validation errors, empty if valid
        """
        errors = []

        if priority not in ['low', 'normal', 'high']:
            errors.append(f"priority must be one of 'low', 'normal', 'high', got '{priority}'")

        return errors

    def validate_delivery_status(self, status: str) -> List[str]:
        """
        Validate the delivery status

        Args:
            status: Status to validate

        Returns:
            List[str]: List of validation errors, empty if valid
        """
        errors = []

        if status not in ['pending', 'in_progress', 'delivered', 'failed', 'retrying']:
            errors.append(f"delivery_status must be one of 'pending', 'in_progress', 'delivered', 'failed', 'retrying', got '{status}'")

        return errors

    def validate_delivery_attempts(self, attempts: int) -> List[str]:
        """
        Validate the delivery attempts count

        Args:
            attempts: Number of attempts to validate

        Returns:
            List[str]: List of validation errors, empty if valid
        """
        errors = []

        if attempts < 0:
            errors.append(f"delivery_attempts must be non-negative, got {attempts}")

        return errors


# Global validator instance
validator = MessageValidator()


def get_validator() -> MessageValidator:
    """
    Get the global message validator instance

    Returns:
        MessageValidator: The global validator instance
    """
    return validator


def validate_outbound_message(message: OutboundMessage) -> bool:
    """
    Validate an outbound message and return whether it's valid

    Args:
        message: The OutboundMessage to validate

    Returns:
        bool: True if valid, False otherwise
    """
    errors = validator.validate_outbound_message(message)
    return len(errors) == 0


def validate_and_raise(message: OutboundMessage) -> None:
    """
    Validate an outbound message and raise an exception if invalid

    Args:
        message: The OutboundMessage to validate

    Raises:
        ValueError: If the message is invalid
    """
    errors = validator.validate_outbound_message(message)
    if errors:
        raise ValueError(f"Validation failed: {'; '.join(errors)}")