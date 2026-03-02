import asyncio
import json
import logging
from typing import Dict, Any, Optional
from aiokafka import AIOKafkaProducer
from datetime import datetime, date


def _json_serializer(obj):
    """JSON serializer that handles datetime objects"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

from app.models.kafka_event import KafkaEvent
from app.config.settings import settings


class KafkaProducerService:
    """Service for producing messages to Kafka"""

    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None
        self.is_connected = False
        self.logger = logging.getLogger(__name__)

    async def connect(self):
        """Connect to Kafka broker"""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                value_serializer=lambda x: json.dumps(x, default=_json_serializer).encode('utf-8'),
                key_serializer=lambda x: x.encode('utf-8') if x else None
            )
            await self.producer.start()
            self.is_connected = True
            self.logger.info(f"Connected to Kafka at {settings.kafka_bootstrap_servers}")
        except Exception as e:
            self.logger.error(f"Failed to connect to Kafka: {str(e)}")
            self.is_connected = False
            raise

    async def disconnect(self):
        """Disconnect from Kafka broker"""
        if self.producer:
            await self.producer.stop()
            self.is_connected = False
            self.logger.info("Disconnected from Kafka")

    async def send_message(self, topic: str, message: Dict[str, Any], key: Optional[str] = None) -> KafkaEvent:
        """Send a message to Kafka and return a KafkaEvent record"""
        if not self.is_connected or not self.producer:
            raise RuntimeError("Kafka producer is not connected")

        # Create KafkaEvent record
        kafka_event = KafkaEvent(
            inbound_message_id=message.get('id', ''),
            topic_name=topic,
            event_payload=message,
            publish_timestamp=datetime.utcnow(),
            delivery_status='pending'
        )

        retry_count = 0
        max_retries = 3

        while retry_count <= max_retries:
            try:
                # Send message to Kafka
                await self.producer.send_and_wait(
                    topic,
                    value=message,
                    key=key
                )

                # Update KafkaEvent with success info
                kafka_event.delivery_status = 'published'
                kafka_event.retry_count = retry_count

                self.logger.info(f"Message sent to topic '{topic}' successfully")
                break

            except Exception as e:
                retry_count += 1
                kafka_event.retry_count = retry_count
                kafka_event.error_message = str(e)

                if retry_count > max_retries:
                    kafka_event.delivery_status = 'failed'
                    self.logger.error(f"Failed to send message to topic '{topic}' after {max_retries} retries: {str(e)}")
                    raise
                else:
                    kafka_event.delivery_status = 'retried'
                    self.logger.warning(f"Failed to send message to topic '{topic}', attempt {retry_count}/{max_retries}: {str(e)}")

                    # Exponential backoff
                    await asyncio.sleep(2 ** retry_count)

        return kafka_event

    async def ensure_topic_exists(self, topic: str):
        """Ensure that a topic exists (in a real implementation, this would interact with Kafka admin client)"""
        # For now, we assume topics exist as they should be created by Phase 2 infrastructure
        self.logger.info(f"Ensuring topic '{topic}' exists")


# Global Kafka producer instance
kafka_producer = KafkaProducerService()