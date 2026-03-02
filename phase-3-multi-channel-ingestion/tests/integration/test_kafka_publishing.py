import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import json

from app.services.ingestion_service import ingestion_service
from app.services.kafka_producer import kafka_producer


class TestKafkaPublishing:
    """Test suite for verifying messages are published to Kafka"""

    @pytest.mark.asyncio
    async def test_gmail_message_published_to_kafka(self):
        """Test that Gmail messages are published to Kafka"""
        # Prepare test data
        gmail_payload = {
            "from": "gmail.sender@example.com",
            "body": "Test Gmail message for Kafka verification",
            "subject": "Kafka Test",
            "message_id": "gmail-kafka-test-123",
            "timestamp": datetime.utcnow().isoformat()
        }

        # Mock dependencies to verify Kafka publishing
        with patch('app.services.ingestion_service.message_normalizer') as mock_normalizer, \
             patch('app.services.ingestion_service.identity_resolver') as mock_resolver, \
             patch.object(kafka_producer, 'send_message', new_callable=AsyncMock) as mock_kafka_send:

            # Set up mocks
            mock_normalized = MagicMock()
            mock_normalized.dict.return_value = {"normalized": "gmail_data", "sender_id": "gmail.sender@example.com"}
            mock_normalized.sender_id = "gmail.sender@example.com"
            mock_normalized.id = "normalized-gmail-123"
            mock_normalized.customer_identifier = "customer-123"
            mock_normalized.processed_status = "received"

            mock_normalizer.normalize_message.return_value = mock_normalized
            mock_resolver.get_or_create_customer = AsyncMock(return_value={
                "customer_id": "customer-123",
                "customer_name": "Gmail Sender",
                "created_new": False,
                "timestamp": datetime.utcnow().isoformat()
            })

            mock_kafka_event = MagicMock()
            mock_kafka_event.dict.return_value = {"event": "published", "status": "published"}
            mock_kafka_send.return_value = mock_kafka_event

            # Process the Gmail message
            result = await ingestion_service.ingest_gmail_message(gmail_payload)

            # Verify that Kafka send was called
            assert result["success"] is True
            mock_kafka_send.assert_called_once()

            # Verify the call was made with the correct parameters
            call_args = mock_kafka_send.call_args
            topic_arg = call_args.kwargs.get('topic', call_args.args[0] if call_args.args else None)
            assert topic_arg == "inbound_events"  # topic name

    @pytest.mark.asyncio
    async def test_whatsapp_message_published_to_kafka(self):
        """Test that WhatsApp messages are published to Kafka"""
        # Prepare test data
        whatsapp_payload = {
            "From": "whatsapp:+1234567890",
            "Body": "Test WhatsApp message for Kafka verification",
            "MessageSid": "WA-kafka-test-123"
        }

        # Mock dependencies to verify Kafka publishing
        with patch('app.services.ingestion_service.message_normalizer') as mock_normalizer, \
             patch('app.services.ingestion_service.identity_resolver') as mock_resolver, \
             patch.object(kafka_producer, 'send_message', new_callable=AsyncMock) as mock_kafka_send:

            # Set up mocks
            mock_normalized = MagicMock()
            mock_normalized.dict.return_value = {"normalized": "whatsapp_data", "sender_id": "whatsapp:+1234567890"}
            mock_normalized.sender_id = "whatsapp:+1234567890"
            mock_normalized.id = "normalized-whatsapp-123"
            mock_normalized.customer_identifier = "customer-456"
            mock_normalized.processed_status = "received"

            mock_normalizer.normalize_message.return_value = mock_normalized
            mock_resolver.get_or_create_customer = AsyncMock(return_value={
                "customer_id": "customer-456",
                "customer_name": "WhatsApp User",
                "created_new": True,
                "timestamp": datetime.utcnow().isoformat()
            })

            mock_kafka_event = MagicMock()
            mock_kafka_event.dict.return_value = {"event": "published", "status": "published"}
            mock_kafka_send.return_value = mock_kafka_event

            # Process the WhatsApp message
            result = await ingestion_service.ingest_whatsapp_message(whatsapp_payload)

            # Verify that Kafka send was called
            assert result["success"] is True
            mock_kafka_send.assert_called_once()

            # Verify the call was made with the correct parameters
            call_args = mock_kafka_send.call_args
            topic_arg = call_args.kwargs.get('topic', call_args.args[0] if call_args.args else None)
            assert topic_arg == "inbound_events"  # topic name

    @pytest.mark.asyncio
    async def test_webform_message_published_to_kafka(self):
        """Test that Web Form messages are published to Kafka"""
        # Prepare test data
        webform_payload = {
            "customer_email": "webform.sender@example.com",
            "message": "Test Web Form message for Kafka verification",
            "subject": "Web Form Kafka Test"
        }

        # Mock dependencies to verify Kafka publishing
        with patch('app.services.ingestion_service.message_normalizer') as mock_normalizer, \
             patch('app.services.ingestion_service.identity_resolver') as mock_resolver, \
             patch.object(kafka_producer, 'send_message', new_callable=AsyncMock) as mock_kafka_send:

            # Set up mocks
            mock_normalized = MagicMock()
            mock_normalized.dict.return_value = {"normalized": "webform_data", "sender_id": "webform.sender@example.com"}
            mock_normalized.sender_id = "webform.sender@example.com"
            mock_normalized.id = "normalized-webform-123"
            mock_normalized.customer_identifier = "customer-789"
            mock_normalized.processed_status = "received"

            mock_normalizer.normalize_message.return_value = mock_normalized
            mock_resolver.get_or_create_customer = AsyncMock(return_value={
                "customer_id": "customer-789",
                "customer_name": "Web Form User",
                "created_new": False,
                "timestamp": datetime.utcnow().isoformat()
            })

            mock_kafka_event = MagicMock()
            mock_kafka_event.dict.return_value = {"event": "published", "status": "published"}
            mock_kafka_send.return_value = mock_kafka_event

            # Process the Web Form message
            result = await ingestion_service.ingest_webform_message(webform_payload)

            # Verify that Kafka send was called
            assert result["success"] is True
            mock_kafka_send.assert_called_once()

            # Verify the call was made with the correct parameters
            call_args = mock_kafka_send.call_args
            topic_arg = call_args.kwargs.get('topic', call_args.args[0] if call_args.args else None)
            assert topic_arg == "inbound_events"  # topic name

    @pytest.mark.asyncio
    async def test_all_channels_publish_same_schema_to_kafka(self):
        """Test that all channels publish messages in the same schema to Kafka"""
        # This test verifies that regardless of the source channel,
        # the message published to Kafka has a consistent structure

        from app.services.message_normalizer import message_normalizer

        # Test data for each channel
        gmail_data = {
            "from": "gmail.sender@example.com",
            "body": "Gmail test message",
            "message_id": "gmail-123"
        }

        whatsapp_data = {
            "From": "whatsapp:+1234567890",
            "Body": "WhatsApp test message",
            "MessageSid": "WA1234567890"
        }

        webform_data = {
            "customer_email": "webform.sender@example.com",
            "message": "Web form test message"
        }

        # Normalize messages from all channels
        gmail_normalized = message_normalizer.normalize_gmail_message(gmail_data)
        whatsapp_normalized = message_normalizer.normalize_whatsapp_message(whatsapp_data)
        webform_normalized = message_normalizer.normalize_webform_message(webform_data)

        # Convert to dict for Kafka publishing
        gmail_dict = gmail_normalized.dict()
        whatsapp_dict = whatsapp_normalized.dict()
        webform_dict = webform_normalized.dict()

        # Verify that all have the same required fields for Kafka
        required_fields = [
            "id", "sender_id", "channel", "timestamp", "raw_payload",
            "text_content", "processed_status", "created_at", "updated_at"
        ]

        for field in required_fields:
            assert field in gmail_dict, f"Missing field {field} in Gmail normalized message"
            assert field in whatsapp_dict, f"Missing field {field} in WhatsApp normalized message"
            assert field in webform_dict, f"Missing field {field} in Web Form normalized message"

        # Verify that the channel field correctly identifies the source
        assert gmail_dict["channel"] == "gmail"
        assert whatsapp_dict["channel"] == "whatsapp"
        assert webform_dict["channel"] == "webform"

        # All should have the same processed_status progression
        assert gmail_dict["processed_status"] == "received"  # Default
        assert whatsapp_dict["processed_status"] == "received"  # Default
        assert webform_dict["processed_status"] == "received"  # Default