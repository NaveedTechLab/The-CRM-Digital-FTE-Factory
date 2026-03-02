import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.ingestion_service import IngestionService
from app.services.message_normalizer import message_normalizer
from app.services.identity_resolver import identity_resolver
from app.services.kafka_producer import kafka_producer


class TestIngestionFlow:
    """Integration tests for the complete ingestion flow"""

    def setup_method(self):
        self.ingestion_service = IngestionService()

    @pytest.mark.asyncio
    async def test_complete_gmail_ingestion_flow(self):
        """Test the complete Gmail ingestion flow: Receive -> Normalize -> Identify -> Publish"""
        # Prepare test data
        raw_gmail_payload = {
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "subject": "Test Gmail Message",
            "body": "This is a test message from Gmail",
            "message_id": "gmail-test-123",
            "timestamp": datetime.utcnow().isoformat()
        }

        # Mock dependencies
        with patch.object(message_normalizer, 'normalize_gmail_message') as mock_normalize, \
             patch.object(identity_resolver, 'get_or_create_customer', new_callable=AsyncMock) as mock_resolve, \
             patch.object(kafka_producer, 'send_message', new_callable=AsyncMock) as mock_publish:

            # Set up mock return values
            mock_normalized_msg = MagicMock()
            mock_normalized_msg.dict.return_value = {"normalized": "data", "sender_id": "sender@example.com"}
            mock_normalized_msg.sender_id = "sender@example.com"
            mock_normalized_msg.id = "normalized-123"
            mock_normalized_msg.customer_identifier = None
            mock_normalized_msg.processed_status = "received"

            mock_normalize.return_value = mock_normalized_msg
            mock_resolve.return_value = {
                "customer_id": "customer-123",
                "customer_name": "Test Customer",
                "created_new": False,
                "timestamp": datetime.utcnow().isoformat()
            }
            mock_publish.return_value = MagicMock()
            mock_publish.return_value.dict.return_value = {"event": "published"}

            # Run the ingestion flow
            result = await self.ingestion_service.ingest_gmail_message(raw_gmail_payload)

            # Assertions
            assert result["success"] is True
            assert result["message_id"] == "normalized-123"
            assert result["customer_id"] == "customer-123"

            # Verify all steps were called
            mock_normalize.assert_called_once()
            mock_resolve.assert_called_once()
            mock_publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_whatsapp_ingestion_flow(self):
        """Test the complete WhatsApp ingestion flow: Receive -> Normalize -> Identify -> Publish"""
        # Prepare test data
        raw_whatsapp_payload = {
            "From": "whatsapp:+1234567890",
            "To": "whatsapp:+0987654321",
            "Body": "This is a test message from WhatsApp",
            "MessageSid": "WA1234567890",
            "AccountSid": "AC1234567890"
        }

        # Mock dependencies
        with patch.object(message_normalizer, 'normalize_whatsapp_message') as mock_normalize, \
             patch.object(identity_resolver, 'get_or_create_customer', new_callable=AsyncMock) as mock_resolve, \
             patch.object(kafka_producer, 'send_message', new_callable=AsyncMock) as mock_publish:

            # Set up mock return values
            mock_normalized_msg = MagicMock()
            mock_normalized_msg.dict.return_value = {"normalized": "data", "sender_id": "whatsapp:+1234567890"}
            mock_normalized_msg.sender_id = "whatsapp:+1234567890"
            mock_normalized_msg.id = "normalized-456"
            mock_normalized_msg.customer_identifier = None
            mock_normalized_msg.processed_status = "received"

            mock_normalize.return_value = mock_normalized_msg
            mock_resolve.return_value = {
                "customer_id": "customer-456",
                "customer_name": "Test WhatsApp User",
                "created_new": True,  # New customer created
                "timestamp": datetime.utcnow().isoformat()
            }
            mock_publish.return_value = MagicMock()
            mock_publish.return_value.dict.return_value = {"event": "published"}

            # Run the ingestion flow
            result = await self.ingestion_service.ingest_whatsapp_message(raw_whatsapp_payload)

            # Assertions
            assert result["success"] is True
            assert result["message_id"] == "normalized-456"
            assert result["customer_id"] == "customer-456"
            assert result["created_new_customer"] is True

            # Verify all steps were called
            mock_normalize.assert_called_once()
            mock_resolve.assert_called_once()
            mock_publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_webform_ingestion_flow(self):
        """Test the complete Web Form ingestion flow: Receive -> Normalize -> Identify -> Publish"""
        # Prepare test data
        raw_webform_payload = {
            "customer_email": "webform@example.com",
            "customer_name": "Web Form User",
            "message": "This is a test message from web form",
            "subject": "Web Form Test",
            "priority": "medium"
        }

        # Mock dependencies
        with patch.object(message_normalizer, 'normalize_webform_message') as mock_normalize, \
             patch.object(identity_resolver, 'get_or_create_customer', new_callable=AsyncMock) as mock_resolve, \
             patch.object(kafka_producer, 'send_message', new_callable=AsyncMock) as mock_publish:

            # Set up mock return values
            mock_normalized_msg = MagicMock()
            mock_normalized_msg.dict.return_value = {"normalized": "data", "sender_id": "webform@example.com"}
            mock_normalized_msg.sender_id = "webform@example.com"
            mock_normalized_msg.id = "normalized-789"
            mock_normalized_msg.customer_identifier = None
            mock_normalized_msg.processed_status = "received"

            mock_normalize.return_value = mock_normalized_msg
            mock_resolve.return_value = {
                "customer_id": "customer-789",
                "customer_name": "Web Form User",
                "created_new": False,  # Existing customer
                "timestamp": datetime.utcnow().isoformat()
            }
            mock_publish.return_value = MagicMock()
            mock_publish.return_value.dict.return_value = {"event": "published"}

            # Run the ingestion flow
            result = await self.ingestion_service.ingest_webform_message(raw_webform_payload)

            # Assertions
            assert result["success"] is True
            assert result["message_id"] == "normalized-789"
            assert result["customer_id"] == "customer-789"
            assert result["created_new_customer"] is False

            # Verify all steps were called
            mock_normalize.assert_called_once()
            mock_resolve.assert_called_once()
            mock_publish.assert_called_once()