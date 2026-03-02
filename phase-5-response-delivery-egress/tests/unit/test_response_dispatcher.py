import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.models.outbound_message import OutboundMessage


class TestOutboundMessage:
    """Test suite for OutboundMessage model"""

    def test_create_valid_message(self):
        """Test creating a valid outbound message"""
        message = OutboundMessage(
            message_id="test_msg_123",
            conversation_id="test_conv_123",
            content="Test content",
            channel_destination="gmail",
            recipient_identifier="test@example.com",
            sender_identifier="agent_1"
        )
        assert message.message_id == "test_msg_123"
        assert message.channel_destination == "gmail"
        # SQLAlchemy Column defaults only apply on DB insert, not in-memory
        assert message.delivery_status in ("pending", None)

    def test_create_whatsapp_message(self):
        """Test creating a WhatsApp outbound message"""
        message = OutboundMessage(
            message_id="test_msg_456",
            conversation_id="test_conv_456",
            content="Test WhatsApp content",
            channel_destination="whatsapp",
            recipient_identifier="whatsapp:+1234567890",
            sender_identifier="agent_1"
        )
        assert message.channel_destination == "whatsapp"

    def test_create_webform_message(self):
        """Test creating a webform outbound message"""
        message = OutboundMessage(
            message_id="test_msg_789",
            conversation_id="test_conv_789",
            content="Test webform content",
            channel_destination="webform",
            recipient_identifier="https://example.com/webhook",
            sender_identifier="agent_1"
        )
        assert message.channel_destination == "webform"

    def test_invalid_channel_destination(self):
        """Test creating message with invalid channel"""
        with pytest.raises(ValueError, match="channel_destination"):
            OutboundMessage(
                message_id="test_msg_123",
                conversation_id="test_conv_123",
                content="Test content",
                channel_destination="unknown_channel",
                recipient_identifier="test@example.com",
                sender_identifier="agent_1"
            )

    def test_empty_content_raises_error(self):
        """Test that empty content raises ValueError"""
        with pytest.raises(ValueError, match="content"):
            OutboundMessage(
                message_id="test_msg_123",
                conversation_id="test_conv_123",
                content="",
                channel_destination="gmail",
                recipient_identifier="test@example.com",
                sender_identifier="agent_1"
            )

    def test_update_status(self):
        """Test updating message delivery status"""
        message = OutboundMessage(
            message_id="test_msg_123",
            conversation_id="test_conv_123",
            content="Test content",
            channel_destination="gmail",
            recipient_identifier="test@example.com",
            sender_identifier="agent_1"
        )
        message.update_status("in_progress")
        assert message.delivery_status == "in_progress"

    def test_update_status_with_failure_reason(self):
        """Test updating status with failure reason"""
        message = OutboundMessage(
            message_id="test_msg_123",
            conversation_id="test_conv_123",
            content="Test content",
            channel_destination="gmail",
            recipient_identifier="test@example.com",
            sender_identifier="agent_1"
        )
        message.update_status("failed", failure_reason="Max retry attempts reached")
        assert message.delivery_status == "failed"
        assert message.failure_reason == "Max retry attempts reached"

    def test_invalid_status_update(self):
        """Test that invalid status raises ValueError"""
        message = OutboundMessage(
            message_id="test_msg_123",
            conversation_id="test_conv_123",
            content="Test content",
            channel_destination="gmail",
            recipient_identifier="test@example.com",
            sender_identifier="agent_1"
        )
        with pytest.raises(ValueError, match="Invalid status"):
            message.update_status("invalid_status")

    def test_to_dict(self):
        """Test converting message to dictionary"""
        message = OutboundMessage(
            message_id="test_msg_123",
            conversation_id="test_conv_123",
            content="Test content",
            channel_destination="gmail",
            recipient_identifier="test@example.com",
            sender_identifier="agent_1"
        )
        result = message.to_dict()
        assert result['message_id'] == "test_msg_123"
        assert result['channel_destination'] == "gmail"
        assert result['delivery_status'] in ("pending", None)

    def test_validate_valid_message(self):
        """Test validating a valid message with all fields set"""
        message = OutboundMessage(
            message_id="test_msg_123",
            conversation_id="test_conv_123",
            content="Test content",
            channel_destination="gmail",
            recipient_identifier="test@example.com",
            sender_identifier="agent_1"
        )
        # Set defaults that SQLAlchemy would normally set on DB insert
        message.delivery_status = message.delivery_status or "pending"
        message.delivery_attempts = message.delivery_attempts or 0
        message.priority = message.priority or "normal"
        # Should not raise
        message.validate()

    def test_message_priority(self):
        """Test message with priority"""
        message = OutboundMessage(
            message_id="test_msg_123",
            conversation_id="test_conv_123",
            content="Urgent content",
            channel_destination="gmail",
            recipient_identifier="test@example.com",
            sender_identifier="agent_1",
            priority="high"
        )
        assert message.priority == "high"
