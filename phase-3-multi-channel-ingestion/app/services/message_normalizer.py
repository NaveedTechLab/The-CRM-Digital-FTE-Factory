import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.models.inbound_message import InboundMessage, Attachment
from app.models.normalization_rule import NormalizationRule


class MessageNormalizer:
    """Service to normalize messages from different channels into a unified format"""

    def __init__(self):
        self.normalization_rules = self._load_default_rules()

    def _load_default_rules(self) -> List[NormalizationRule]:
        """Load default normalization rules for different channels"""
        rules = [
            # Gmail rules
            NormalizationRule(
                channel_type="gmail",
                rule_name="gmail_body_extraction",
                input_field="body",
                output_field="text_content",
                transformation_type="direct",
                transformation_params={}
            ),
            NormalizationRule(
                channel_type="gmail",
                rule_name="gmail_sender_extraction",
                input_field="from",
                output_field="sender_id",
                transformation_type="direct",
                transformation_params={}
            ),

            # WhatsApp (Twilio) rules
            NormalizationRule(
                channel_type="whatsapp",
                rule_name="whatsapp_body_extraction",
                input_field="Body",
                output_field="text_content",
                transformation_type="direct",
                transformation_params={}
            ),
            NormalizationRule(
                channel_type="whatsapp",
                rule_name="whatsapp_sender_extraction",
                input_field="From",
                output_field="sender_id",
                transformation_type="direct",
                transformation_params={}
            ),

            # Web Form rules
            NormalizationRule(
                channel_type="webform",
                rule_name="webform_message_extraction",
                input_field="message",
                output_field="text_content",
                transformation_type="direct",
                transformation_params={}
            ),
            NormalizationRule(
                channel_type="webform",
                rule_name="webform_email_extraction",
                input_field="customer_email",
                output_field="sender_id",
                transformation_type="direct",
                transformation_params={}
            ),
        ]

        return rules

    def normalize_gmail_message(self, raw_payload: Dict[str, Any]) -> InboundMessage:
        """Normalize a Gmail message to the unified InboundMessage format"""
        # Extract sender information
        sender_email = self._extract_email_from_gmail(raw_payload.get('from', ''))

        # Extract message content
        message_content = raw_payload.get('body', raw_payload.get('snippet', ''))

        # Extract attachments if present
        attachments = self._extract_attachments_from_gmail(raw_payload.get('attachments', []))

        # Create normalized message
        normalized_message = InboundMessage(
            sender_id=sender_email,
            channel="gmail",
            raw_payload=raw_payload,
            text_content=message_content,
            customer_name=raw_payload.get('sender_name', ''),
            message_content=message_content,
            channel_message_id=raw_payload.get('message_id', ''),
            priority=raw_payload.get('priority', 'medium'),
            attachments=attachments,
            channel_metadata={
                'subject': raw_payload.get('subject', ''),
                'timestamp': raw_payload.get('timestamp'),
                'thread_id': raw_payload.get('thread_id', '')
            }
        )

        return normalized_message

    def normalize_whatsapp_message(self, raw_payload: Dict[str, Any]) -> InboundMessage:
        """Normalize a WhatsApp (Twilio) message to the unified InboundMessage format"""
        # Extract sender information
        sender_id = raw_payload.get('From', '')

        # Extract message content
        message_content = raw_payload.get('Body', '')

        # Create normalized message
        normalized_message = InboundMessage(
            sender_id=sender_id,
            channel="whatsapp",
            raw_payload=raw_payload,
            text_content=message_content,
            customer_name=raw_payload.get('CustomerName', ''),
            message_content=message_content,
            channel_message_id=raw_payload.get('MessageSid', ''),
            priority=raw_payload.get('Priority', 'medium'),
            attachments=[],
            channel_metadata={
                'account_sid': raw_payload.get('AccountSid', ''),
                'api_version': raw_payload.get('ApiVersion', ''),
                'num_media': raw_payload.get('NumMedia', '0'),
                'to': raw_payload.get('To', '')
            }
        )

        return normalized_message

    def normalize_webform_message(self, raw_payload: Dict[str, Any]) -> InboundMessage:
        """Normalize a Web Form message to the unified InboundMessage format"""
        # Extract sender information
        sender_id = raw_payload.get('customer_email', raw_payload.get('customer_phone', ''))

        # Extract message content
        message_content = raw_payload.get('message', '')

        # Extract attachments if present
        attachments = self._extract_attachments_from_webform(raw_payload.get('attachments', []))

        # Create normalized message
        normalized_message = InboundMessage(
            sender_id=sender_id,
            channel="webform",
            raw_payload=raw_payload,
            text_content=message_content,
            customer_name=raw_payload.get('customer_name', ''),
            message_content=message_content,
            channel_message_id=raw_payload.get('submission_id', ''),
            priority=raw_payload.get('priority', 'medium'),
            attachments=attachments,
            channel_metadata={
                'subject': raw_payload.get('subject', ''),
                'customer_phone': raw_payload.get('customer_phone', ''),
                'submission_timestamp': raw_payload.get('timestamp', datetime.utcnow().isoformat())
            }
        )

        return normalized_message

    def _extract_email_from_gmail(self, from_field: str) -> str:
        """Extract email address from Gmail 'From' field which may contain name and email"""
        if '<' in from_field and '>' in from_field:
            # Format: "Name <email@domain.com>"
            email_match = re.search(r'<([^>]+)>', from_field)
            if email_match:
                return email_match.group(1).strip()
        return from_field.strip()

    def _extract_attachments_from_gmail(self, attachments_data: List[Dict[str, Any]]) -> List[Attachment]:
        """Extract attachments from Gmail message data"""
        attachments = []
        for att_data in attachments_data:
            attachment = Attachment(
                filename=att_data.get('filename', 'unknown'),
                content_type=att_data.get('contentType', 'application/octet-stream'),
                file_size=att_data.get('size', 0),
                download_url=att_data.get('download_url', ''),
                stored_location=att_data.get('stored_location', ''),
                upload_status=att_data.get('upload_status', 'pending')
            )
            attachments.append(attachment)
        return attachments

    def _extract_attachments_from_webform(self, attachments_data: List[Dict[str, Any]]) -> List[Attachment]:
        """Extract attachments from Web Form data"""
        attachments = []
        for att_data in attachments_data:
            attachment = Attachment(
                filename=att_data.get('filename', 'unknown'),
                content_type=att_data.get('content_type', 'application/octet-stream'),
                file_size=att_data.get('file_size', 0),
                download_url=att_data.get('download_url', ''),
                stored_location=att_data.get('stored_location', ''),
                upload_status=att_data.get('upload_status', 'pending')
            )
            attachments.append(attachment)
        return attachments

    def normalize_message(self, raw_payload: Dict[str, Any], channel_type: str) -> InboundMessage:
        """Normalize a message from any channel to the unified InboundMessage format"""
        if channel_type == "gmail":
            return self.normalize_gmail_message(raw_payload)
        elif channel_type == "whatsapp":
            return self.normalize_whatsapp_message(raw_payload)
        elif channel_type == "webform":
            return self.normalize_webform_message(raw_payload)
        else:
            raise ValueError(f"Unsupported channel type: {channel_type}")


# Global message normalizer instance
message_normalizer = MessageNormalizer()