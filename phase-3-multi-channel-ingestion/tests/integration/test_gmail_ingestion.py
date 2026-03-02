import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.ingestion_service import ingestion_service


class TestGmailIngestion:
    """Test suite for Gmail message ingestion"""

    @pytest.mark.asyncio
    async def test_gmail_message_ingestion_simulation(self):
        """Simulate Gmail message ingestion through the complete pipeline"""
        # Prepare test data that simulates what the Gmail poller would find
        gmail_payload = {
            "message_id": "gmail-test-123",
            "thread_id": "thread-456",
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "subject": "Test Gmail Message",
            "body": "This is a test message from Gmail for verification.",
            "snippet": "This is a test message...",
            "timestamp": datetime.utcnow().isoformat(),
            "size_estimate": 1024,
            "raw_payload": {
                "id": "gmail-test-123",
                "threadId": "thread-456",
                "labelIds": ["UNREAD", "INBOX"],
                "payload": {
                    "headers": [
                        {"name": "From", "value": "sender@example.com"},
                        {"name": "To", "value": "recipient@example.com"},
                        {"name": "Subject", "value": "Test Gmail Message"}
                    ],
                    "body": {"data": "VGhpcyBpcyBhIHRlc3QgbWVzc2FnZSBmcm9tIEdtYWlsIGZvciB2ZXJpZmljYXRpb24u"}
                }
            }
        }

        # Mock all dependencies to verify the flow
        with patch.object(ingestion_service, 'process_inbound_message', new_callable=AsyncMock) as mock_process:
            # Set up the mock to return a successful result
            mock_process.return_value = {
                "success": True,
                "message_id": "normalized-gmail-123",
                "customer_id": "customer-456",
                "created_new_customer": True,
                "kafka_event": {"event_id": "kafka-event-789", "status": "published"},
                "processed_at": datetime.utcnow().isoformat()
            }

            # Call the Gmail ingestion method
            result = await ingestion_service.ingest_gmail_message(gmail_payload)

            # Verify the result
            assert result["success"] is True
            assert result["message_id"] == "normalized-gmail-123"
            assert result["customer_id"] == "customer-456"
            assert "kafka_event" in result

            # Verify that the process method was called with the right parameters
            mock_process.assert_called_once_with(gmail_payload, "gmail")

    @pytest.mark.asyncio
    async def test_gmail_message_normalization(self):
        """Test that Gmail messages are properly normalized"""
        from app.services.message_normalizer import message_normalizer

        # Test data
        raw_gmail = {
            "from": "John Doe <john.doe@example.com>",
            "body": "Hello from Gmail! This is a test message.",
            "subject": "Gmail Test",
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": "test-gmail-123",
            "raw_payload": {"original": "gmail_data"}
        }

        # Normalize the message
        normalized = message_normalizer.normalize_gmail_message(raw_gmail)

        # Verify normalization worked correctly
        assert normalized.sender_id == "john.doe@example.com"  # Extracted from the 'from' field
        assert normalized.channel == "gmail"
        assert normalized.text_content == "Hello from Gmail! This is a test message."
        assert normalized.channel_message_id == "test-gmail-123"
        assert "raw_payload" in normalized.raw_payload or "from" in normalized.raw_payload

    @pytest.mark.asyncio
    async def test_gmail_message_with_attachments(self):
        """Test Gmail message normalization with attachments"""
        from app.services.message_normalizer import message_normalizer

        # Test data with attachments
        raw_gmail = {
            "from": "sender@example.com",
            "body": "Message with attachment",
            "subject": "With Attachment",
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": "gmail-with-att-123",
            "attachments": [
                {
                    "filename": "document.pdf",
                    "contentType": "application/pdf",
                    "size": 2048,
                    "download_url": "https://example.com/download/123",
                    "stored_location": "/storage/docs/123.pdf",
                    "upload_status": "pending"
                }
            ],
            "raw_payload": {"original": "gmail_data_with_attachments"}
        }

        # Normalize the message
        normalized = message_normalizer.normalize_gmail_message(raw_gmail)

        # Verify normalization worked correctly
        assert len(normalized.attachments) == 1
        assert normalized.attachments[0].filename == "document.pdf"
        assert normalized.attachments[0].content_type == "application/pdf"
        assert normalized.attachments[0].file_size == 2048