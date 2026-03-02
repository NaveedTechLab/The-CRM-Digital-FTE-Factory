import asyncio
import json
import signal
from typing import Dict, Any, Optional, Callable
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import uuid
from datetime import datetime
from ..models.outbound_message import OutboundMessage, Base as OutboundBase
from ..models.delivery_log import Base as DeliveryLogBase
from ..models.retry_queue_item import Base as RetryQueueBase
from ..config.settings import settings
from ..utils.logger import logger, log_delivery_attempt, log_retry_event, log_rate_limit_event
from ..utils.message_validator import get_validator, validate_and_raise
from ..services.gmail_service import get_gmail_service, send_email
from ..services.whatsapp_service import get_whatsapp_service, send_whatsapp_message
from ..services.web_notification_service import get_web_notification_service, send_webhook, simulate_web_notification
from ..services.delivery_tracker import get_delivery_tracker, initialize_delivery_tracker
from ..services.rate_limiter import get_rate_limiter, initialize_rate_limiter


class ResponseDispatcher:
    """
    Kafka Consumer that pulls from 'outbound_responses' and routes messages based on channel metadata
    """

    def __init__(self, kafka_bootstrap_servers: str = None, database_url: str = None):
        """
        Initialize the response dispatcher

        Args:
            kafka_bootstrap_servers: Kafka bootstrap servers (defaults to settings.kafka_bootstrap_servers)
            database_url: Database URL (defaults to settings.database_url)
        """
        self.kafka_servers = kafka_bootstrap_servers or settings.kafka_bootstrap_servers
        self.database_url = database_url or settings.database_url
        self.consumer = None
        self.producer = None
        self.engine = create_engine(self.database_url)
        self.Session = sessionmaker(bind=self.engine)
        self.running = False
        self.validator = get_validator()
        self.delivery_tracker = get_delivery_tracker()
        self.rate_limiter = get_rate_limiter()

        # Service instances
        self.gmail_service = get_gmail_service()
        self.whatsapp_service = get_whatsapp_service()
        self.web_notification_service = get_web_notification_service()

    async def initialize(self):
        """
        Initialize the response dispatcher services
        """
        logger.info("Initializing Response Dispatcher")

        # Initialize database - create all tables
        OutboundBase.metadata.create_all(self.engine)
        DeliveryLogBase.metadata.create_all(self.engine)
        RetryQueueBase.metadata.create_all(self.engine)
        initialize_delivery_tracker()

        # Initialize rate limiter
        await initialize_rate_limiter()

        # Initialize services
        await self.gmail_service.initialize()
        await self.whatsapp_service.initialize()

        logger.info("Response Dispatcher initialized successfully")

    async def start_consumer(self, topic: str = 'outbound_responses'):
        """
        Start the Kafka consumer to listen for outbound responses

        Args:
            topic: Kafka topic to consume from (default: 'outbound_responses')
        """
        logger.info(f"Starting consumer for topic: {topic}")

        self.consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=self.kafka_servers,
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            group_id='response_dispatcher_group'
        )

        await self.consumer.start()
        self.running = True

        logger.info("Kafka consumer started successfully")

        try:
            async for msg in self.consumer:
                if not self.running:
                    break

                logger.info(
                    f"Received message from Kafka",
                    topic=msg.topic,
                    partition=msg.partition,
                    offset=msg.offset
                )

                try:
                    await self.process_message(msg.value)
                except Exception as e:
                    logger.error(
                        f"Error processing message: {str(e)}",
                        message_value=msg.value,
                        error=str(e)
                    )
        except Exception as e:
            logger.error(f"Error in consumer loop: {str(e)}", error=str(e))
        finally:
            await self.stop_consumer()

    async def process_message(self, message_data: Dict[str, Any]):
        """
        Process an incoming message from Kafka

        Args:
            message_data: The message data received from Kafka
        """
        logger.info("Processing outbound message", message_data=message_data)

        try:
            # Create OutboundMessage instance from message data
            outbound_message = self._create_outbound_message(message_data)

            # Validate the message
            validate_and_raise(outbound_message)

            # Update status to in_progress
            await self.delivery_tracker.update_delivery_status(
                outbound_message.message_id,
                'in_progress'
            )

            # Route the message based on channel_destination
            success = await self.route_message(outbound_message)

            if success:
                # Update status to delivered
                await self.delivery_tracker.update_delivery_status(
                    outbound_message.message_id,
                    'delivered'
                )
                logger.info(
                    f"Message {outbound_message.message_id} delivered successfully",
                    message_id=outbound_message.message_id
                )
            else:
                # Update status to retrying or failed based on error type
                await self.handle_delivery_failure(outbound_message)

        except Exception as e:
            logger.error(
                f"Error processing message: {str(e)}",
                message_data=message_data,
                error=str(e)
            )
            # Log the error in the database
            session = self.Session()
            try:
                # Find the message if it exists
                existing_msg = session.query(OutboundMessage).filter(
                    OutboundMessage.message_id == message_data.get('message_id')
                ).first()

                if existing_msg:
                    await self.delivery_tracker.update_delivery_status(
                        message_data.get('message_id'),
                        'failed',
                        failure_reason=str(e)
                    )
            finally:
                session.close()

    def _create_outbound_message(self, message_data: Dict[str, Any]) -> OutboundMessage:
        """
        Create an OutboundMessage instance from message data

        Args:
            message_data: The message data from Kafka

        Returns:
            OutboundMessage: The created OutboundMessage instance
        """
        # Extract required fields (try multiple field names for cross-phase compatibility)
        message_id = message_data.get('message_id') or message_data.get('id')
        conversation_id = message_data.get('conversation_id', str(uuid.uuid4()))
        content = message_data.get('content')
        channel_destination = message_data.get('channel_destination')
        recipient_identifier = message_data.get('recipient_identifier') or message_data.get('recipient_id')
        sender_identifier = message_data.get('sender_identifier', 'response_dispatcher')

        # Extract optional fields
        priority = message_data.get('priority', 'normal')
        scheduled_delivery = message_data.get('scheduled_delivery')
        if scheduled_delivery:
            scheduled_delivery = datetime.fromisoformat(scheduled_delivery.replace('Z', '+00:00'))

        # Create the OutboundMessage instance
        outbound_message = OutboundMessage(
            message_id=message_id,
            conversation_id=conversation_id,
            content=content,
            channel_destination=channel_destination,
            recipient_identifier=recipient_identifier,
            sender_identifier=sender_identifier,
            priority=priority,
            scheduled_delivery=scheduled_delivery,
            delivery_attempts=0,
            delivery_status='pending'
        )

        return outbound_message

    async def route_message(self, outbound_message: OutboundMessage) -> bool:
        """
        Route the message to the appropriate delivery service based on channel_destination

        Args:
            outbound_message: The OutboundMessage to route

        Returns:
            bool: True if delivery was successful, False otherwise
        """
        channel = outbound_message.channel_destination
        logger.info(
            f"Routing message {outbound_message.message_id} to channel: {channel}",
            message_id=outbound_message.message_id,
            channel=channel
        )

        if channel == 'gmail':
            return await self.deliver_via_gmail(outbound_message)
        elif channel == 'whatsapp':
            return await self.deliver_via_whatsapp(outbound_message)
        elif channel == 'webform':
            return await self.deliver_via_webhook(outbound_message)
        else:
            logger.error(
                f"Unknown channel destination: {channel}",
                message_id=outbound_message.message_id,
                channel=channel
            )
            return False

    async def deliver_via_gmail(self, outbound_message: OutboundMessage) -> bool:
        """
        Deliver the message via Gmail service

        Args:
            outbound_message: The OutboundMessage to deliver

        Returns:
            bool: True if delivery was successful, False otherwise
        """
        try:
            # Extract threading information from metadata if available
            in_reply_to = None
            references = None

            # For now, we'll use a placeholder subject
            subject = f"Re: Customer Inquiry #{outbound_message.conversation_id[:8]}"

            result = await send_email(
                to=outbound_message.recipient_identifier,
                subject=subject,
                body=outbound_message.content,
                in_reply_to=in_reply_to,
                references=references,
                message_id=outbound_message.message_id
            )

            return result.get('success', False)
        except Exception as e:
            logger.error(
                f"Error delivering via Gmail: {str(e)}",
                message_id=outbound_message.message_id,
                error=str(e)
            )
            return False

    async def deliver_via_whatsapp(self, outbound_message: OutboundMessage) -> bool:
        """
        Deliver the message via WhatsApp service

        Args:
            outbound_message: The OutboundMessage to deliver

        Returns:
            bool: True if delivery was successful, False otherwise
        """
        try:
            result = await send_whatsapp_message(
                to=outbound_message.recipient_identifier,
                message_body=outbound_message.content,
                message_id=outbound_message.message_id
            )

            return result.get('success', False)
        except Exception as e:
            logger.error(
                f"Error delivering via WhatsApp: {str(e)}",
                message_id=outbound_message.message_id,
                error=str(e)
            )
            return False

    async def deliver_via_webhook(self, outbound_message: OutboundMessage) -> bool:
        """
        Deliver the message via webhook

        Args:
            outbound_message: The OutboundMessage to deliver

        Returns:
            bool: True if delivery was successful, False otherwise
        """
        try:
            # Create payload for webhook/notification
            timestamp = outbound_message.timestamp or datetime.utcnow()
            payload = {
                'message_id': outbound_message.message_id,
                'conversation_id': outbound_message.conversation_id,
                'content': outbound_message.content,
                'timestamp': timestamp.isoformat(),
                'sender': outbound_message.sender_identifier
            }

            # If recipient is not a valid URL, simulate web notification
            recipient = outbound_message.recipient_identifier
            if not recipient or not recipient.startswith(('http://', 'https://')):
                result = await simulate_web_notification(
                    session_id=recipient or 'unknown',
                    message=outbound_message.content,
                    message_id=outbound_message.message_id
                )
            else:
                result = await send_webhook(
                    webhook_url=recipient,
                    payload=payload,
                    message_id=outbound_message.message_id
                )

            return result.get('success', False)
        except Exception as e:
            logger.error(
                f"Error delivering via webhook: {str(e)}",
                message_id=outbound_message.message_id,
                error=str(e)
            )
            return False

    async def handle_delivery_failure(self, outbound_message: OutboundMessage):
        """
        Handle a delivery failure by updating status and potentially adding to retry queue

        Args:
            outbound_message: The OutboundMessage that failed to deliver
        """
        # Increment delivery attempts
        outbound_message.delivery_attempts += 1

        # Check if we should retry
        if outbound_message.delivery_attempts < settings.delivery_retry_attempts:
            # Update status to retrying
            await self.delivery_tracker.update_delivery_status(
                outbound_message.message_id,
                'retrying',
                failure_reason='Temporary failure, will retry'
            )

            # Add to retry queue
            from ..utils.retry_mechanism import calculate_next_retry_time
            scheduled_retry = calculate_next_retry_time(
                outbound_message.delivery_attempts + 1
            )

            await self.delivery_tracker.add_to_retry_queue(
                outbound_message.message_id,
                outbound_message.delivery_attempts,
                scheduled_retry,
                'Temporary failure, scheduled for retry'
            )

            log_retry_event(
                outbound_message.message_id,
                outbound_message.channel_destination,
                outbound_message.delivery_attempts,
                settings.delivery_retry_attempts,
                'Temporary failure, scheduled for retry'
            )
        else:
            # Max attempts reached, mark as failed
            await self.delivery_tracker.update_delivery_status(
                outbound_message.message_id,
                'failed',
                failure_reason='Max retry attempts reached'
            )

            logger.error(
                f"Max retry attempts reached for message {outbound_message.message_id}",
                message_id=outbound_message.message_id,
                attempts=outbound_message.delivery_attempts
            )

    async def start_retry_processor(self):
        """
        Start the retry processor to handle failed deliveries
        """
        logger.info("Starting retry processor")

        while self.running:
            try:
                # Process retry queue
                stats = await self.delivery_tracker.process_retry_queue(
                    self.retry_message_delivery
                )

                logger.info("Retry queue processing completed", stats=stats)

                # Sleep for a while before next processing cycle
                await asyncio.sleep(30)  # Process every 30 seconds
            except Exception as e:
                logger.error(f"Error in retry processor: {str(e)}", error=str(e))
                await asyncio.sleep(5)  # Wait before retrying

    async def retry_message_delivery(self, message_id: str, attempt_number: int) -> bool:
        """
        Retry delivering a specific message

        Args:
            message_id: ID of the message to retry
            attempt_number: Current attempt number

        Returns:
            bool: True if delivery was successful, False otherwise
        """
        logger.info(
            f"Retrying delivery for message {message_id}",
            message_id=message_id,
            attempt_number=attempt_number
        )

        # Get the message from the database
        session = self.Session()
        try:
            message = session.query(OutboundMessage).filter(
                OutboundMessage.message_id == message_id
            ).first()

            if not message:
                logger.error(f"Message not found for retry: {message_id}")
                return False

            # Update delivery attempt count
            message.delivery_attempts = attempt_number
            session.commit()

            # Route the message again
            success = await self.route_message(message)

            if success:
                # Update status to delivered
                await self.delivery_tracker.update_delivery_status(
                    message_id,
                    'delivered'
                )
            else:
                # Update status to reflect failed retry
                await self.delivery_tracker.update_delivery_status(
                    message_id,
                    'retrying' if attempt_number < settings.delivery_retry_attempts else 'failed',
                    failure_reason=f'Retry attempt {attempt_number} failed'
                )

            return success
        finally:
            session.close()

    async def stop_consumer(self):
        """
        Stop the Kafka consumer
        """
        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka consumer stopped")

    async def stop(self):
        """
        Stop the response dispatcher
        """
        logger.info("Stopping Response Dispatcher")
        self.running = False

        if self.consumer:
            await self.consumer.stop()

        if self.producer:
            await self.producer.stop()

        logger.info("Response Dispatcher stopped")

    def setup_signal_handlers(self):
        """
        Set up signal handlers for graceful shutdown
        """
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown")
            self.running = False

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)


# Global response dispatcher instance
response_dispatcher = ResponseDispatcher()


async def initialize_dispatcher():
    """
    Initialize the global response dispatcher instance
    """
    await response_dispatcher.initialize()


def get_dispatcher() -> ResponseDispatcher:
    """
    Get the global response dispatcher instance

    Returns:
        ResponseDispatcher: The global dispatcher instance
    """
    return response_dispatcher


async def start_dispatcher(topic: str = 'outbound_responses'):
    """
    Start the response dispatcher to listen for outbound responses

    Args:
        topic: Kafka topic to consume from (default: 'outbound_responses')
    """
    response_dispatcher.setup_signal_handlers()

    # Start retry processor as a background task alongside the consumer
    retry_task = asyncio.create_task(response_dispatcher.start_retry_processor())

    try:
        await response_dispatcher.start_consumer(topic)
    finally:
        # Ensure retry processor stops when consumer stops
        response_dispatcher.running = False
        retry_task.cancel()
        try:
            await retry_task
        except asyncio.CancelledError:
            pass