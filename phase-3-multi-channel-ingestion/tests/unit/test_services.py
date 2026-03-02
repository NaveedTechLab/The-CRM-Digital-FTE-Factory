import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.message_normalizer import MessageNormalizer
from app.services.identity_resolver import IdentityResolver
from app.services.kafka_producer import KafkaProducerService
from app.services.ingestion_service import IngestionService
from app.models.inbound_message import InboundMessage


class TestMessageNormalizer:
    """Test cases for MessageNormalizer service"""

    def setup_method(self):
        self.normalizer = MessageNormalizer()

    def test_normalize_gmail_message(self):
        """Test normalizing a Gmail message"""
        raw_payload = {
            "from": "sender@example.com",
            "body": "Hello from Gmail",
            "subject": "Test Subject",
            "timestamp": "2023-01-01T00:00:00Z",
            "message_id": "gmail-msg-123"
        }

        result = self.normalizer.normalize_gmail_message(raw_payload)

        assert isinstance(result, InboundMessage)
        assert result.sender_id == "sender@example.com"
        assert result.channel == "gmail"
        assert result.text_content == "Hello from Gmail"

    def test_normalize_whatsapp_message(self):
        """Test normalizing a WhatsApp (Twilio) message"""
        raw_payload = {
            "From": "whatsapp:+1234567890",
            "To": "whatsapp:+0987654321",
            "Body": "Hello from WhatsApp",
            "MessageSid": "WA1234567890"
        }

        result = self.normalizer.normalize_whatsapp_message(raw_payload)

        assert isinstance(result, InboundMessage)
        assert result.sender_id == "whatsapp:+1234567890"
        assert result.channel == "whatsapp"
        assert result.text_content == "Hello from WhatsApp"

    def test_normalize_webform_message(self):
        """Test normalizing a Web Form message"""
        raw_payload = {
            "customer_email": "customer@example.com",
            "customer_name": "John Doe",
            "message": "Hello from web form",
            "subject": "Web Form Submission"
        }

        result = self.normalizer.normalize_webform_message(raw_payload)

        assert isinstance(result, InboundMessage)
        assert result.sender_id == "customer@example.com"
        assert result.channel == "webform"
        assert result.text_content == "Hello from web form"


class TestIdentityResolver:
    """Test cases for IdentityResolver service"""

    def setup_method(self):
        self.resolver = IdentityResolver()
        # Mock the db_manager to avoid actual database calls
        self.resolver.db_manager = MagicMock()

    @pytest.mark.asyncio
    async def test_resolve_existing_identity(self):
        """Test resolving an existing customer identity"""
        # Mock the database manager to return an existing customer
        mock_customer = MagicMock()
        mock_customer.id = "cust-123"
        mock_customer.name = "John Doe"

        self.resolver.db_manager.get_customer_by_identifier = AsyncMock(return_value=mock_customer)

        result = await self.resolver.resolve_identity("test@example.com", "gmail", "John Doe")

        assert result["customer_id"] == "cust-123"
        assert result["created_new"] is False

    @pytest.mark.asyncio
    async def test_resolve_new_identity(self):
        """Test resolving a new customer identity (creating a placeholder)"""
        # Mock the database manager to return None (customer doesn't exist)
        self.resolver.db_manager.get_customer_by_identifier = AsyncMock(return_value=None)

        # Mock the create_customer method
        mock_new_customer = MagicMock()
        mock_new_customer.id = "new-cust-456"
        self.resolver.db_manager.create_customer = AsyncMock(return_value=mock_new_customer)

        result = await self.resolver.resolve_identity("newuser@example.com", "gmail", "Jane Smith")

        assert result["customer_id"] == "new-cust-456"
        assert result["created_new"] is True


class TestKafkaProducerService:
    """Test cases for KafkaProducerService"""

    def setup_method(self):
        self.producer = KafkaProducerService()

    @pytest.mark.asyncio
    async def test_send_message_success(self):
        """Test sending a message to Kafka successfully"""
        # Mock the producer
        self.producer.producer = AsyncMock()
        self.producer.is_connected = True

        test_message = {"id": "test-123", "content": "test message"}

        with patch('app.services.kafka_producer.json.dumps'):
            result = await self.producer.send_message("test-topic", test_message)

        # Check that send_and_wait was called
        self.producer.producer.send_and_wait.assert_called_once()


class TestIngestionService:
    """Test cases for IngestionService"""

    def setup_method(self):
        self.service = IngestionService()

        # Mock dependencies
        self.service.logger = MagicMock()

    @pytest.mark.asyncio
    async def test_process_inbound_message(self):
        """Test the complete ingestion pipeline"""
        # Since the actual dependencies are complex, we'll test with mocked components
        with patch('app.services.ingestion_service.message_normalizer') as mock_normalizer, \
             patch('app.services.ingestion_service.identity_resolver') as mock_resolver, \
             patch('app.services.ingestion_service.kafka_producer') as mock_producer:

            # Mock a normalized message
            mock_normalized = MagicMock(spec=InboundMessage)
            mock_normalized.dict.return_value = {"test": "data"}
            mock_normalized.sender_id = "test@example.com"
            mock_normalized.id = "msg-123"
            mock_normalized.customer_identifier = None
            mock_normalized.customer_name = "Test User"
            mock_normalized.processed_status = "received"

            # Configure mocks
            mock_normalizer.normalize_message.return_value = mock_normalized
            mock_resolver.get_or_create_customer = AsyncMock(return_value={
                "customer_id": "cust-123",
                "customer_name": "Test User",
                "created_new": False,
                "timestamp": datetime.now().isoformat()
            })

            mock_kafka_event = MagicMock()
            mock_kafka_event.dict.return_value = {"event": "data"}
            mock_producer.send_message = AsyncMock(return_value=mock_kafka_event)

            # Test the method
            result = await self.service.process_inbound_message(
                {"test": "payload"},
                "gmail"
            )

            # Assertions
            assert result["success"] is True
            assert result["message_id"] == "msg-123"
            assert result["customer_id"] == "cust-123"