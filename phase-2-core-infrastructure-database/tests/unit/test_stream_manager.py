"""
Unit tests for StreamManager Kafka operations.
Tests Kafka producer/consumer lifecycle and message handling.
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.stream_manager import StreamManager


class TestStreamManagerInit:
    """Tests for StreamManager initialization."""

    def test_default_bootstrap_servers(self):
        sm = StreamManager()
        assert sm.bootstrap_servers == "localhost:9092"

    def test_custom_bootstrap_servers(self):
        sm = StreamManager(bootstrap_servers="kafka:29092")
        assert sm.bootstrap_servers == "kafka:29092"

    def test_initial_state(self):
        sm = StreamManager()
        assert sm.producer is None
        assert sm.consumer is None
        assert sm.topics_configured is False


class TestStreamManagerTopics:
    """Tests for topic initialization."""

    @pytest.mark.asyncio
    async def test_initialize_topics(self):
        sm = StreamManager()
        await sm.initialize_topics(["inbound_events", "outbound_responses"])
        assert sm.topics_configured is True

    @pytest.mark.asyncio
    async def test_create_inbound_events_topic(self):
        sm = StreamManager()
        await sm.create_inbound_events_topic(num_partitions=6)
        # Should not raise

    @pytest.mark.asyncio
    async def test_create_outbound_responses_topic(self):
        sm = StreamManager()
        await sm.create_outbound_responses_topic(num_partitions=6)
        # Should not raise


class TestStreamManagerProducer:
    """Tests for Kafka producer operations."""

    @pytest.mark.asyncio
    async def test_start_producer(self):
        sm = StreamManager()
        with patch('app.stream_manager.AIOKafkaProducer') as MockProducer:
            mock_producer = AsyncMock()
            MockProducer.return_value = mock_producer
            await sm.start_producer()
            assert sm.producer is not None
            mock_producer.start.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_stop_producer(self):
        sm = StreamManager()
        sm.producer = AsyncMock()
        await sm.stop_producer()
        assert sm.producer is None

    @pytest.mark.asyncio
    async def test_stop_producer_when_none(self):
        sm = StreamManager()
        await sm.stop_producer()
        assert sm.producer is None

    @pytest.mark.asyncio
    async def test_send_message(self):
        sm = StreamManager()
        sm.topics_configured = True
        sm.producer = AsyncMock()
        sm.producer.send_and_wait = AsyncMock()

        message = {"event_type": "test", "content": "Hello"}
        await sm.send_message("test_topic", message, key="test_key")

        sm.producer.send_and_wait.assert_awaited_once()
        assert 'timestamp' in message

    @pytest.mark.asyncio
    async def test_send_message_auto_starts_producer(self):
        sm = StreamManager()
        sm.topics_configured = True
        with patch('app.stream_manager.AIOKafkaProducer') as MockProducer:
            mock_producer = AsyncMock()
            mock_producer.send_and_wait = AsyncMock()
            MockProducer.return_value = mock_producer
            await sm.send_message("test_topic", {"data": "test"})
            mock_producer.start.assert_awaited_once()


class TestStreamManagerConsumer:
    """Tests for Kafka consumer operations."""

    @pytest.mark.asyncio
    async def test_start_consumer(self):
        sm = StreamManager()
        with patch('app.stream_manager.AIOKafkaConsumer') as MockConsumer:
            mock_consumer = AsyncMock()
            MockConsumer.return_value = mock_consumer
            await sm.start_consumer("test_topic", "test_group")
            assert sm.consumer is not None
            mock_consumer.start.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_stop_consumer(self):
        sm = StreamManager()
        sm.consumer = AsyncMock()
        await sm.stop_consumer()
        assert sm.consumer is None

    @pytest.mark.asyncio
    async def test_stop_consumer_when_none(self):
        sm = StreamManager()
        await sm.stop_consumer()
        assert sm.consumer is None


class TestStreamManagerHealthCheck:
    """Tests for Kafka health check."""

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        sm = StreamManager()
        with patch('app.stream_manager.AIOKafkaConsumer') as MockConsumer:
            mock_consumer = AsyncMock()
            MockConsumer.return_value = mock_consumer
            result = await sm.health_check()
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        sm = StreamManager()
        with patch('app.stream_manager.AIOKafkaConsumer') as MockConsumer:
            MockConsumer.return_value = AsyncMock(
                start=AsyncMock(side_effect=Exception("Connection refused"))
            )
            result = await sm.health_check()
            assert result is False
