import asyncio
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import json
import logging
from typing import Dict, Any, Optional
from app.config.settings import settings

logger = logging.getLogger(__name__)

class KafkaService:
    def __init__(self):
        self.consumer = None
        self.producer = None

    async def connect_consumer(self):
        """Initialize and connect the Kafka consumer"""
        def safe_deserialize(x):
            try:
                return json.loads(x.decode('utf-8'))
            except Exception:
                return None

        try:
            self.consumer = AIOKafkaConsumer(
                settings.INBOUND_EVENTS_TOPIC,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_deserializer=safe_deserialize,
                group_id="agent-consumer-group",
                enable_auto_commit=True,
                auto_offset_reset="earliest"
            )
            await self.consumer.start()
            logger.info(f"Connected to Kafka consumer for topic: {settings.INBOUND_EVENTS_TOPIC}")
        except Exception as e:
            logger.error(f"Failed to connect Kafka consumer: {e}")
            raise

    async def disconnect_consumer(self):
        """Disconnect the Kafka consumer"""
        if self.consumer:
            await self.consumer.stop()

    async def connect_producer(self):
        """Initialize and connect the Kafka producer"""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
            await self.producer.start()
            logger.info(f"Connected to Kafka producer for topic: {settings.OUTBOUND_RESPONSES_TOPIC}")
        except Exception as e:
            logger.error(f"Failed to connect Kafka producer: {e}")
            raise

    async def disconnect_producer(self):
        """Disconnect the Kafka producer"""
        if self.producer:
            await self.producer.stop()

    async def consume_messages(self):
        """Consume messages from the inbound events topic"""
        if not self.consumer:
            raise RuntimeError("Consumer not connected")

        try:
            async for msg in self.consumer:
                if msg.value is None:
                    logger.warning(f"Skipping undeserializable message at offset {msg.offset}")
                    continue
                logger.info(f"Received message: {msg.value} from partition {msg.partition}, offset {msg.offset}")
                yield msg.value
        except Exception as e:
            logger.error(f"Error consuming message: {e}")
            raise

    async def publish_message(self, message: Dict[str, Any], topic: Optional[str] = None):
        """Publish a message to the outbound responses topic"""
        if not self.producer:
            raise RuntimeError("Producer not connected")

        target_topic = topic or settings.OUTBOUND_RESPONSES_TOPIC

        try:
            await self.producer.send_and_wait(target_topic, message)
            logger.info(f"Published message to topic {target_topic}: {message}")
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            raise

# Global instance
kafka_service = KafkaService()