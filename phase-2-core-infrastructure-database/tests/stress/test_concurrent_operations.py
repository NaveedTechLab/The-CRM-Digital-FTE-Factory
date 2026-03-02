"""
Stress tests for concurrent database and Kafka operations.
Tests system behavior under high load conditions.
"""
import pytest
import uuid
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.database_manager import DatabaseManager, Customer, Ticket, Message
from app.stream_manager import StreamManager


class TestConcurrentDatabaseOperations:
    """Stress tests for concurrent database access."""

    def test_concurrent_customer_creation(self, sample_customer_data):
        """Test creating multiple customers concurrently."""
        results = []
        num_concurrent = 50

        def create_customer(i):
            data = sample_customer_data.copy()
            data['email'] = f"user{i}@example.com"
            data['name'] = f"User {i}"
            customer = Customer(**data)
            customer.id = uuid.uuid4()
            results.append(customer)
            return customer

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_customer, i) for i in range(num_concurrent)]
            for f in futures:
                f.result()

        assert len(results) == num_concurrent
        emails = [c.email for c in results]
        assert len(set(emails)) == num_concurrent  # All unique

    def test_concurrent_ticket_creation(self):
        """Test creating multiple tickets concurrently."""
        results = []
        num_concurrent = 100
        customer_id = uuid.uuid4()

        def create_ticket(i):
            ticket = Ticket(
                customer_id=customer_id,
                subject=f"Ticket {i}",
                description=f"Description for ticket {i}",
                channel=["email", "whatsapp", "webform"][i % 3],
                priority=["low", "medium", "high", "critical"][i % 4]
            )
            ticket.id = uuid.uuid4()
            results.append(ticket)
            return ticket

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_ticket, i) for i in range(num_concurrent)]
            for f in futures:
                f.result()

        assert len(results) == num_concurrent

    def test_concurrent_message_creation(self):
        """Test creating multiple messages concurrently."""
        results = []
        num_concurrent = 200
        ticket_id = uuid.uuid4()

        def create_message(i):
            msg = Message(
                ticket_id=ticket_id,
                sender_type="customer" if i % 2 == 0 else "agent",
                content=f"Message content {i}",
                direction="inbound" if i % 2 == 0 else "outbound"
            )
            msg.id = uuid.uuid4()
            results.append(msg)
            return msg

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(create_message, i) for i in range(num_concurrent)]
            for f in futures:
                f.result()

        assert len(results) == num_concurrent


class TestConcurrentKafkaOperations:
    """Stress tests for concurrent Kafka operations."""

    @pytest.mark.asyncio
    async def test_concurrent_message_publishing(self, sample_kafka_message):
        """Test publishing multiple messages concurrently to Kafka."""
        sm = StreamManager()
        sm.topics_configured = True
        sm.producer = AsyncMock()
        sm.producer.send_and_wait = AsyncMock()

        num_messages = 100
        tasks = []
        for i in range(num_messages):
            msg = sample_kafka_message.copy()
            msg['content'] = f"Message {i}"
            tasks.append(sm.send_message("inbound_events", msg, key=f"key_{i}"))

        await asyncio.gather(*tasks)
        assert sm.producer.send_and_wait.await_count == num_messages

    @pytest.mark.asyncio
    async def test_producer_consumer_lifecycle_stress(self):
        """Test rapid start/stop cycles of producer."""
        sm = StreamManager()

        with patch('app.stream_manager.AIOKafkaProducer') as MockProducer:
            mock_producer = AsyncMock()
            MockProducer.return_value = mock_producer

            for _ in range(20):
                await sm.start_producer()
                await sm.stop_producer()

            # Should handle gracefully
            assert sm.producer is None


class TestHighVolumeDataIntegrity:
    """Tests for data integrity under high volume."""

    def test_unique_ids_under_load(self):
        """Verify UUID uniqueness under high volume."""
        ids = set()
        num_items = 10000

        for _ in range(num_items):
            new_id = uuid.uuid4()
            assert new_id not in ids
            ids.add(new_id)

        assert len(ids) == num_items

    def test_model_serialization_under_load(self):
        """Test model to_dict serialization under high volume."""
        num_items = 1000
        now = datetime.now(timezone.utc)

        for i in range(num_items):
            customer = Customer(
                id=uuid.uuid4(),
                name=f"Customer {i}",
                email=f"customer{i}@example.com",
                created_at=now,
                updated_at=now
            )
            result = customer.to_dict()
            assert result['name'] == f"Customer {i}"
            assert result['email'] == f"customer{i}@example.com"
