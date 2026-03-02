import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from app.models.inbound_message import InboundMessage, Attachment
from app.models.channel_payload import ChannelPayload
from app.models.kafka_event import KafkaEvent


class TestInboundMessage:
    """Test cases for InboundMessage model"""

    def test_inbound_message_creation(self):
        """Test creating an InboundMessage with valid data"""
        message = InboundMessage(
            sender_id="test@example.com",
            channel="gmail",
            raw_payload={"test": "data"},
            text_content="Hello world"
        )

        assert message.sender_id == "test@example.com"
        assert message.channel == "gmail"
        assert message.text_content == "Hello world"
        assert message.id is not None
        assert message.timestamp is not None

    def test_inbound_message_with_attachment(self):
        """Test creating an InboundMessage with attachments"""
        attachment = Attachment(
            filename="test.pdf",
            content_type="application/pdf",
            file_size=1024
        )

        message = InboundMessage(
            sender_id="test@example.com",
            channel="gmail",
            raw_payload={"test": "data"},
            text_content="Hello world",
            attachments=[attachment]
        )

        assert len(message.attachments) == 1
        assert message.attachments[0].filename == "test.pdf"

    def test_inbound_message_validation_email_format(self):
        """Test validation of email format in sender_id"""
        # Valid email should pass
        message = InboundMessage(
            sender_id="test@example.com",
            channel="gmail",
            raw_payload={"test": "data"},
            text_content="Hello world"
        )
        assert message.sender_id == "test@example.com"

    def test_inbound_message_validation_phone_format(self):
        """Test validation of phone format in sender_id"""
        # Valid WhatsApp format should pass
        message = InboundMessage(
            sender_id="whatsapp:+1234567890",
            channel="whatsapp",
            raw_payload={"test": "data"},
            text_content="Hello world"
        )
        assert message.sender_id == "whatsapp:+1234567890"


class TestChannelPayload:
    """Test cases for ChannelPayload model"""

    def test_channel_payload_creation(self):
        """Test creating a ChannelPayload with valid data"""
        payload = ChannelPayload(
            raw_payload={"key": "value"},
            channel_type="gmail"
        )

        assert payload.raw_payload == {"key": "value"}
        assert payload.channel_type == "gmail"
        assert payload.id is not None

    def test_channel_payload_validation(self):
        """Test validation of ChannelPayload"""
        payload = ChannelPayload(
            raw_payload={"test": "data"},
            channel_type="whatsapp"
        )

        assert payload.channel_type in ["gmail", "whatsapp", "webform"]


class TestKafkaEvent:
    """Test cases for KafkaEvent model"""

    def test_kafka_event_creation(self):
        """Test creating a KafkaEvent with valid data"""
        event = KafkaEvent(
            inbound_message_id="test-id",
            event_payload={"message": "test"}
        )

        assert event.inbound_message_id == "test-id"
        assert event.event_payload == {"message": "test"}
        assert event.delivery_status == "pending"

    def test_kafka_event_status_validation(self):
        """Test validation of KafkaEvent delivery status"""
        event = KafkaEvent(
            inbound_message_id="test-id",
            event_payload={"message": "test"},
            delivery_status="published"
        )

        assert event.delivery_status in ["pending", "published", "failed", "retried"]