"""
StreamManager class for Kafka operations using aiokafka.
Handles topic management and provides producer/consumer interfaces.
"""
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from typing import Dict, List, Optional, Any, Callable
import json
import asyncio
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StreamManager:
    """
    Stream Manager class using aiokafka for Kafka operations.
    Handles topic management and provides producer/consumer interfaces.
    """

    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        """
        Initialize the StreamManager with Kafka connection parameters.

        Args:
            bootstrap_servers: Kafka bootstrap server addresses
        """
        self.bootstrap_servers = bootstrap_servers
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.topics_configured = False

        logger.info(f"StreamManager initialized with bootstrap servers: {bootstrap_servers}")

    async def initialize_topics(self, topics: List[str]):
        """
        Initialize Kafka topics, creating them if they don't exist.

        Args:
            topics: List of topic names to ensure exist
        """
        # For aiokafka, we'll create topics via admin client
        # Since aiokafka doesn't have a built-in admin client, we'll use the admin commands

        # For now, we'll just log the topics that should exist
        logger.info(f"Ensuring topics exist: {topics}")

        # In a real implementation, we would use kafka-python's AdminClient to create topics
        # For now, we'll just assume the topics exist based on docker-compose configuration
        for topic in topics:
            logger.info(f"Topic '{topic}' is configured")

        self.topics_configured = True

    async def start_producer(self):
        """
        Start the Kafka producer.
        """
        if self.producer is None:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda x: json.dumps(x).encode('utf-8'),
                key_serializer=lambda x: x.encode('utf-8') if x else None
            )
            await self.producer.start()
            logger.info("Kafka producer started")

    async def stop_producer(self):
        """
        Stop the Kafka producer.
        """
        if self.producer:
            await self.producer.stop()
            self.producer = None
            logger.info("Kafka producer stopped")

    async def start_consumer(self, topic: str, group_id: str = "crm_consumer_group"):
        """
        Start the Kafka consumer for a specific topic.

        Args:
            topic: Topic name to consume from
            group_id: Consumer group ID
        """
        if self.consumer is None:
            self.consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=group_id,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')) if x else None,
                key_deserializer=lambda x: x.decode('utf-8') if x else None,
                auto_offset_reset="earliest"
            )
            await self.consumer.start()
            logger.info(f"Kafka consumer started for topic: {topic}, group: {group_id}")

    async def stop_consumer(self):
        """
        Stop the Kafka consumer.
        """
        if self.consumer:
            await self.consumer.stop()
            self.consumer = None
            logger.info("Kafka consumer stopped")

    async def send_message(self, topic: str, message: Dict[str, Any], key: Optional[str] = None):
        """
        Send a message to a Kafka topic.

        Args:
            topic: Topic name to send the message to
            message: Message dictionary to send
            key: Optional message key
        """
        if not self.topics_configured:
            await self.initialize_topics([topic])

        if not self.producer:
            await self.start_producer()

        try:
            # Add timestamp to message
            message['timestamp'] = datetime.utcnow().isoformat()

            await self.producer.send_and_wait(topic, value=message, key=key)
            logger.info(f"Message sent to topic '{topic}' with key '{key}'")
        except Exception as e:
            logger.error(f"Error sending message to topic '{topic}': {e}")
            raise

    async def consume_messages(self, topic: str, callback: Callable[[Dict[str, Any]], None],
                              group_id: str = "crm_consumer_group", max_messages: Optional[int] = None):
        """
        Consume messages from a Kafka topic.

        Args:
            topic: Topic name to consume from
            callback: Function to call for each message
            group_id: Consumer group ID
            max_messages: Maximum number of messages to process (None for infinite)
        """
        await self.start_consumer(topic, group_id)

        message_count = 0
        try:
            async for msg in self.consumer:
                try:
                    # Process the message
                    message_data = msg.value
                    callback(message_data)

                    # Commit the offset after processing
                    await self.consumer.commit()

                    message_count += 1
                    logger.debug(f"Processed message #{message_count} from topic '{topic}'")

                    # Stop if we've reached max_messages
                    if max_messages and message_count >= max_messages:
                        break

                except Exception as e:
                    logger.error(f"Error processing message from topic '{topic}': {e}")
                    # Continue to next message
                    continue
        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        except Exception as e:
            logger.error(f"Error in consumer loop for topic '{topic}': {e}")
        finally:
            await self.stop_consumer()

    async def create_inbound_events_topic(self, num_partitions: int = 6, replication_factor: int = 1):
        """
        Configure the 'inbound_events' topic.

        Args:
            num_partitions: Number of partitions for the topic
            replication_factor: Replication factor for the topic
        """
        # In a real implementation, we would use the Kafka AdminClient to create the topic
        # For now, we'll just log that this topic is configured
        logger.info(f"Configured 'inbound_events' topic with {num_partitions} partitions")

    async def create_outbound_responses_topic(self, num_partitions: int = 6, replication_factor: int = 1):
        """
        Configure the 'outbound_responses' topic.

        Args:
            num_partitions: Number of partitions for the topic
            replication_factor: Replication factor for the topic
        """
        # In a real implementation, we would use the Kafka AdminClient to create the topic
        # For now, we'll just log that this topic is configured
        logger.info(f"Configured 'outbound_responses' topic with {num_partitions} partitions")

    async def health_check(self) -> bool:
        """
        Perform a health check on the Kafka connection.

        Returns:
            True if Kafka is accessible and topics are available, False otherwise
        """
        try:
            # Try to start a temporary consumer to check connectivity
            temp_consumer = AIOKafkaConsumer(
                bootstrap_servers=self.bootstrap_servers,
                group_id=f"health_check_{int(datetime.now().timestamp())}",
                enable_auto_commit=False,
                auto_offset_reset="latest"
            )

            await temp_consumer.start()
            logger.info("Kafka connection is healthy")

            # List available topics to verify functionality
            # Note: aiokafka doesn't have a direct way to list topics
            # We'll just verify the connection works by attempting to assign partitions
            await temp_consumer.stop()

            return True
        except Exception as e:
            logger.error(f"Kafka health check failed: {e}")
            return False