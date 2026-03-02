"""
Message normalizer utility for converting messages from different channels
into a consistent format for the Customer Success Agent.
"""
from typing import Dict, Any, Optional
from datetime import datetime

class MessageNormalizer:
    """
    Utility class for normalizing messages from different channels
    into a consistent format for agent processing.
    """

    @staticmethod
    def normalize_email_message(
        email: str,
        name: str,
        message: str,
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Normalize an email message to a standard format.

        Args:
            email: Customer's email address
            name: Customer's name
            message: The message content
            timestamp: Optional timestamp (defaults to now)

        Returns:
            Dictionary with normalized message format
        """
        if timestamp is None:
            timestamp = datetime.now()

        return {
            "source_channel": "email",
            "customer_identifier": email,
            "customer_name": name,
            "original_content": message,
            "normalized_content": message.strip(),
            "timestamp": timestamp,
            "metadata": {
                "channel_specific": {
                    "email_address": email
                },
                "processing_info": {
                    "original_length": len(message),
                    "normalized_at": timestamp.isoformat()
                }
            }
        }

    @staticmethod
    def normalize_whatsapp_message(
        phone: str,
        name: str,
        message: str,
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Normalize a WhatsApp message to a standard format.

        Args:
            phone: Customer's phone number
            name: Customer's name
            message: The message content
            timestamp: Optional timestamp (defaults to now)

        Returns:
            Dictionary with normalized message format
        """
        if timestamp is None:
            timestamp = datetime.now()

        return {
            "source_channel": "whatsapp",
            "customer_identifier": phone,
            "customer_name": name,
            "original_content": message,
            "normalized_content": message.strip(),
            "timestamp": timestamp,
            "metadata": {
                "channel_specific": {
                    "phone_number": phone
                },
                "processing_info": {
                    "original_length": len(message),
                    "normalized_at": timestamp.isoformat()
                }
            }
        }

    @staticmethod
    def normalize_webform_message(
        email: str,
        name: str,
        message: str,
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Normalize a web form message to a standard format.

        Args:
            email: Customer's email address
            name: Customer's name
            message: The message content
            timestamp: Optional timestamp (defaults to now)

        Returns:
            Dictionary with normalized message format
        """
        if timestamp is None:
            timestamp = datetime.now()

        return {
            "source_channel": "webform",
            "customer_identifier": email,
            "customer_name": name,
            "original_content": message,
            "normalized_content": message.strip(),
            "timestamp": timestamp,
            "metadata": {
                "channel_specific": {
                    "email_address": email
                },
                "processing_info": {
                    "original_length": len(message),
                    "normalized_at": timestamp.isoformat()
                }
            }
        }

    @staticmethod
    def normalize_message(
        source_channel: str,
        customer_identifier: str,
        customer_name: str,
        message: str,
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generic method to normalize a message based on source channel.

        Args:
            source_channel: The channel the message came from ('email', 'whatsapp', 'webform')
            customer_identifier: Identifier for the customer (email or phone)
            customer_name: Customer's name
            message: The message content
            timestamp: Optional timestamp (defaults to now)

        Returns:
            Dictionary with normalized message format
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Determine the correct normalization based on channel
        if source_channel.lower() == "email":
            return MessageNormalizer.normalize_email_message(
                email=customer_identifier,
                name=customer_name,
                message=message,
                timestamp=timestamp
            )
        elif source_channel.lower() == "whatsapp":
            return MessageNormalizer.normalize_whatsapp_message(
                phone=customer_identifier,
                name=customer_name,
                message=message,
                timestamp=timestamp
            )
        elif source_channel.lower() == "webform":
            return MessageNormalizer.normalize_webform_message(
                email=customer_identifier,
                name=customer_name,
                message=message,
                timestamp=timestamp
            )
        else:
            # Default to a generic format if channel is unknown
            return {
                "source_channel": source_channel,
                "customer_identifier": customer_identifier,
                "customer_name": customer_name,
                "original_content": message,
                "normalized_content": message.strip(),
                "timestamp": timestamp,
                "metadata": {
                    "channel_specific": {},
                    "processing_info": {
                        "original_length": len(message),
                        "normalized_at": timestamp.isoformat()
                    }
                }
            }


# Global instance of the message normalizer
message_normalizer = MessageNormalizer()