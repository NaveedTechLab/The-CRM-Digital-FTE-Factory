import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.kafka_producer import KafkaProducerService


class TestKafkaIntegration:
    """Integration tests for Kafka producer functionality"""

    def setup_method(self):
        self.kafka_producer = KafkaProducerService()

    @pytest.mark.asyncio
    async def test_connect_to_kafka(self):
        """Test connecting to Kafka"""
        # Mock the AIOKafkaProducer
        with patch('app.services.kafka_producer.AIOKafkaProducer') as mock_producer_class:
            mock_producer_instance = AsyncMock()
            mock_producer_class.return_value = mock_producer_instance

            # Test connection
            await self.kafka_producer.connect()

            # Verify the producer was started
            mock_producer_instance.start.assert_called_once()
            assert self.kafka_producer.is_connected is True

    @pytest.mark.asyncio
    async def test_disconnect_from_kafka(self):
        """Test disconnecting from Kafka"""
        # Mock the producer
        self.kafka_producer.producer = AsyncMock()
        self.kafka_producer.is_connected = True

        # Test disconnection
        await self.kafka_producer.disconnect()

        # Verify the producer was stopped
        self.kafka_producer.producer.stop.assert_called_once()
        assert self.kafka_producer.is_connected is False

    @pytest.mark.asyncio
    async def test_send_message_success(self):
        """Test sending a message to Kafka successfully"""
        # Mock the producer
        self.kafka_producer.producer = AsyncMock()
        self.kafka_producer.is_connected = True

        test_message = {"id": "test-123", "content": "test message"}
        test_topic = "test-topic"

        # Mock the send_and_wait method
        self.kafka_producer.producer.send_and_wait = AsyncMock(return_value=MagicMock())

        # Test sending message
        result = await self.kafka_producer.send_message(test_topic, test_message)

        # Verify the message was sent
        self.kafka_producer.producer.send_and_wait.assert_called_once_with(
            test_topic,
            value=test_message,
            key=None
        )
        assert result.delivery_status == "published"

    @pytest.mark.asyncio
    async def test_send_message_with_key(self):
        """Test sending a message to Kafka with a key"""
        # Mock the producer
        self.kafka_producer.producer = AsyncMock()
        self.kafka_producer.is_connected = True

        test_message = {"id": "test-123", "content": "test message"}
        test_topic = "test-topic"
        test_key = "test-key"

        # Mock the send_and_wait method
        self.kafka_producer.producer.send_and_wait = AsyncMock(return_value=MagicMock())

        # Test sending message with key
        result = await self.kafka_producer.send_message(test_topic, test_message, key=test_key)

        # Verify the message was sent with the key
        self.kafka_producer.producer.send_and_wait.assert_called_once_with(
            test_topic,
            value=test_message,
            key=test_key
        )
        assert result.delivery_status == "published"

    @pytest.mark.asyncio
    async def test_send_message_failure_and_retry(self):
        """Test handling message send failure with retries"""
        # Mock the producer to fail initially, then succeed
        self.kafka_producer.producer = AsyncMock()
        self.kafka_producer.is_connected = True

        test_message = {"id": "test-123", "content": "test message"}
        test_topic = "test-topic"

        # Configure the send_and_wait to fail twice, then succeed
        call_count = 0
        def mock_send_and_wait(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # Fail first 2 attempts
                raise Exception("Kafka delivery failed")
            return MagicMock()  # Succeed on 3rd attempt

        self.kafka_producer.producer.send_and_wait.side_effect = mock_send_and_wait

        # Patch asyncio.sleep to avoid actual sleeping in tests
        with patch('app.services.kafka_producer.asyncio.sleep', new_callable=AsyncMock):
            # Test sending message (should eventually succeed after retries)
            result = await self.kafka_producer.send_message(test_topic, test_message)

            # Should have been called 3 times (2 failures + 1 success)
            assert self.kafka_producer.producer.send_and_wait.call_count == 3
            assert result.delivery_status == "published"
            assert result.retry_count == 2  # 2 failed attempts before success

    @pytest.mark.asyncio
    async def test_send_message_failure_max_retries_exceeded(self):
        """Test handling message send failure when max retries exceeded"""
        # Mock the producer to always fail
        self.kafka_producer.producer = AsyncMock()
        self.kafka_producer.is_connected = True

        test_message = {"id": "test-123", "content": "test message"}
        test_topic = "test-topic"

        # Configure the send_and_wait to always fail
        self.kafka_producer.producer.send_and_wait.side_effect = Exception("Kafka delivery failed")

        # Patch asyncio.sleep to avoid actual sleeping in tests
        with patch('app.services.kafka_producer.asyncio.sleep', new_callable=AsyncMock):
            # Test sending message (should fail after max retries)
            with pytest.raises(Exception):  # Expect the function to raise after max retries
                await self.kafka_producer.send_message(test_topic, test_message)

    @pytest.mark.asyncio
    async def test_send_message_when_disconnected(self):
        """Test sending a message when Kafka is not connected"""
        # Ensure producer is disconnected
        self.kafka_producer.is_connected = False
        self.kafka_producer.producer = None

        test_message = {"id": "test-123", "content": "test message"}
        test_topic = "test-topic"

        # Attempt to send message should raise RuntimeError
        with pytest.raises(RuntimeError, match="Kafka producer is not connected"):
            await self.kafka_producer.send_message(test_topic, test_message)