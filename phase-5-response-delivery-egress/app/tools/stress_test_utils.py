"""
Stress testing utilities for the Response Delivery Dispatcher.
Generates synthetic load to validate throughput, rate limiting, and retry mechanisms.
"""

import asyncio
import uuid
import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from aiokafka import AIOKafkaProducer
from ..config.settings import settings
from ..utils.logger import logger


class StressTestGenerator:
    """
    Generates synthetic outbound messages for stress testing the dispatcher.
    Supports configurable message rates, channel distribution, and failure injection.
    """

    def __init__(self, kafka_bootstrap_servers: str = None):
        self.kafka_servers = kafka_bootstrap_servers or settings.kafka_bootstrap_servers
        self.producer = None
        self.stats = {
            "messages_sent": 0,
            "messages_failed": 0,
            "start_time": None,
            "end_time": None,
            "by_channel": {"gmail": 0, "whatsapp": 0, "webform": 0}
        }

    async def initialize(self):
        """Initialize the Kafka producer for sending test messages."""
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.kafka_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await self.producer.start()
        logger.info("Stress test generator initialized")

    async def cleanup(self):
        """Cleanup resources."""
        if self.producer:
            await self.producer.stop()

    def _generate_test_message(self, channel: str, priority: str = "normal") -> Dict[str, Any]:
        """Generate a synthetic outbound message."""
        message_id = str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())

        recipients = {
            "gmail": f"test-{uuid.uuid4().hex[:8]}@example.com",
            "whatsapp": f"+1555{uuid.uuid4().hex[:7][:7]}",
            "webform": f"https://webhook.example.com/test/{uuid.uuid4().hex[:8]}"
        }

        return {
            "message_id": message_id,
            "conversation_id": conversation_id,
            "content": f"Stress test message {message_id[:8]} via {channel}",
            "channel_destination": channel,
            "recipient_identifier": recipients[channel],
            "sender_identifier": "stress_test_generator",
            "priority": priority,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    async def send_batch(
        self,
        total_messages: int = 100,
        channel_distribution: Optional[Dict[str, float]] = None,
        messages_per_second: int = 10,
        topic: str = "outbound_responses"
    ) -> Dict[str, Any]:
        """
        Send a batch of test messages to the outbound_responses Kafka topic.

        Args:
            total_messages: Total number of messages to send
            channel_distribution: Distribution ratio per channel (must sum to 1.0)
            messages_per_second: Target send rate
            topic: Kafka topic to send to

        Returns:
            Dict with send statistics
        """
        if not self.producer:
            raise RuntimeError("Generator not initialized. Call initialize() first.")

        if channel_distribution is None:
            channel_distribution = {"gmail": 0.4, "whatsapp": 0.35, "webform": 0.25}

        self.stats = {
            "messages_sent": 0,
            "messages_failed": 0,
            "start_time": datetime.utcnow().isoformat() + "Z",
            "end_time": None,
            "by_channel": {"gmail": 0, "whatsapp": 0, "webform": 0}
        }

        # Calculate messages per channel
        channel_counts = {}
        remaining = total_messages
        for channel, ratio in channel_distribution.items():
            count = int(total_messages * ratio)
            channel_counts[channel] = count
            remaining -= count
        # Assign remainder to first channel
        first_channel = list(channel_distribution.keys())[0]
        channel_counts[first_channel] += remaining

        # Build message queue
        messages = []
        for channel, count in channel_counts.items():
            for _ in range(count):
                messages.append(self._generate_test_message(channel))

        # Shuffle for realistic distribution
        import random
        random.shuffle(messages)

        # Send at target rate
        delay = 1.0 / messages_per_second if messages_per_second > 0 else 0

        for msg in messages:
            try:
                await self.producer.send_and_wait(topic, msg)
                self.stats["messages_sent"] += 1
                self.stats["by_channel"][msg["channel_destination"]] += 1
            except Exception as e:
                self.stats["messages_failed"] += 1
                logger.error(f"Failed to send stress test message: {str(e)}")

            if delay > 0:
                await asyncio.sleep(delay)

        self.stats["end_time"] = datetime.utcnow().isoformat() + "Z"

        logger.info("Stress test batch completed", stats=self.stats)
        return self.stats

    def get_stats(self) -> Dict[str, Any]:
        """Get current stress test statistics."""
        return self.stats


def calculate_throughput(stats: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate throughput metrics from stress test stats.

    Returns:
        Dict with messages_per_second, success_rate, and per-channel rates
    """
    if not stats.get("start_time") or not stats.get("end_time"):
        return {"messages_per_second": 0.0, "success_rate": 0.0}

    start = datetime.fromisoformat(stats["start_time"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(stats["end_time"].replace("Z", "+00:00"))
    duration = (end - start).total_seconds()

    if duration <= 0:
        return {"messages_per_second": 0.0, "success_rate": 0.0}

    total = stats["messages_sent"] + stats["messages_failed"]
    success_rate = (stats["messages_sent"] / total * 100) if total > 0 else 0.0

    return {
        "messages_per_second": round(stats["messages_sent"] / duration, 2),
        "success_rate": round(success_rate, 2),
        "duration_seconds": round(duration, 2),
        "total_sent": stats["messages_sent"],
        "total_failed": stats["messages_failed"]
    }
