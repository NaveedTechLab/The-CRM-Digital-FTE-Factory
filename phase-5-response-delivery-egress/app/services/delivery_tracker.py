import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from ..models.outbound_message import OutboundMessage, Base
from ..models.delivery_log import DeliveryLog
from ..models.retry_queue_item import RetryQueueItem
from ..config.settings import settings
from ..utils.logger import logger
from ..utils.retry_mechanism import get_retry_mechanism


class DeliveryTracker:
    """
    Tracks delivery status and manages retry queue logic
    """

    def __init__(self, database_url: str = None):
        """
        Initialize the delivery tracker

        Args:
            database_url: Database URL for storing delivery data (defaults to settings.database_url)
        """
        self.database_url = database_url or settings.database_url
        self.engine = create_engine(self.database_url)
        self.Session = sessionmaker(bind=self.engine)
        self.retry_mechanism = get_retry_mechanism()

    def initialize_database(self):
        """
        Initialize the database tables
        """
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully", database_url=self.database_url)
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}", error=str(e))
            raise

    async def update_delivery_status(self, message_id: str, new_status: str, failure_reason: str = None) -> bool:
        """
        Update the delivery status for a message

        Args:
            message_id: ID of the message to update
            new_status: New delivery status
            failure_reason: Reason for failure (if applicable)

        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            session = self.Session()
            try:
                message = session.query(OutboundMessage).filter(OutboundMessage.message_id == message_id).first()

                if not message:
                    logger.warning(f"Message not found for ID: {message_id}")
                    return False

                message.update_status(new_status, failure_reason)
                session.commit()

                logger.info(
                    f"Delivery status updated for message {message_id}",
                    message_id=message_id,
                    new_status=new_status,
                    failure_reason=failure_reason
                )
                return True
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Failed to update delivery status: {str(e)}", error=str(e), message_id=message_id)
            return False

    async def log_delivery_attempt(self, outbound_message_id: str, attempt_number: int, channel: str,
                                delivery_method: str = None, request_payload: Any = None,
                                response_payload: Any = None, status_code: int = None,
                                success: bool = False, error_message: str = None,
                                rate_limit_hit: bool = False, processing_time_ms: int = None) -> bool:
        """
        Log a delivery attempt

        Args:
            outbound_message_id: ID of the outbound message
            attempt_number: Attempt number
            channel: Channel used for delivery
            delivery_method: Method used for delivery
            request_payload: Payload sent to delivery service
            response_payload: Response received from delivery service
            status_code: Status code from delivery service
            success: Whether the delivery was successful
            error_message: Error message if delivery failed
            rate_limit_hit: Whether rate limit was hit
            processing_time_ms: Processing time in milliseconds

        Returns:
            bool: True if logging was successful, False otherwise
        """
        try:
            session = self.Session()
            try:
                delivery_log = DeliveryLog.create_from_delivery_attempt(
                    outbound_message_id=outbound_message_id,
                    attempt_number=attempt_number,
                    channel=channel,
                    delivery_method=delivery_method,
                    request_payload=request_payload,
                    response_payload=response_payload,
                    status_code=status_code,
                    success=success,
                    error_message=error_message,
                    rate_limit_hit=rate_limit_hit,
                    processing_time_ms=processing_time_ms
                )

                session.add(delivery_log)
                session.commit()

                logger.info(
                    f"Delivery attempt logged for message {outbound_message_id}",
                    outbound_message_id=outbound_message_id,
                    attempt_number=attempt_number,
                    channel=channel,
                    success=success
                )
                return True
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Failed to log delivery attempt: {str(e)}", error=str(e), outbound_message_id=outbound_message_id)
            return False

    async def add_to_retry_queue(self, outbound_message_id: str, attempt_number: int,
                               scheduled_retry: datetime, failure_reason: str = None,
                               priority: int = 0) -> bool:
        """
        Add a message to the retry queue

        Args:
            outbound_message_id: ID of the outbound message
            attempt_number: Current attempt number
            scheduled_retry: When to retry
            failure_reason: Reason for failure
            priority: Priority for processing

        Returns:
            bool: True if addition was successful, False otherwise
        """
        try:
            session = self.Session()
            try:
                retry_item = RetryQueueItem(
                    outbound_message_id=outbound_message_id,
                    attempt_number=attempt_number,
                    scheduled_retry=scheduled_retry,
                    failure_reason=failure_reason,
                    priority=priority
                )

                session.add(retry_item)
                session.commit()

                logger.info(
                    f"Added message to retry queue: {outbound_message_id}",
                    outbound_message_id=outbound_message_id,
                    attempt_number=attempt_number,
                    scheduled_retry=scheduled_retry.isoformat()
                )
                return True
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Failed to add to retry queue: {str(e)}", error=str(e), outbound_message_id=outbound_message_id)
            return False

    async def get_pending_retries(self) -> List[RetryQueueItem]:
        """
        Get all retry queue items that are ready for retry

        Returns:
            List[RetryQueueItem]: List of retry queue items ready for retry
        """
        try:
            session = self.Session()
            try:
                current_time = datetime.utcnow()
                retry_items = session.query(RetryQueueItem).filter(
                    RetryQueueItem.scheduled_retry <= current_time
                ).order_by(RetryQueueItem.priority.desc()).all()

                logger.info(f"Found {len(retry_items)} pending retry items")
                return retry_items
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Failed to get pending retries: {str(e)}", error=str(e))
            return []

    async def remove_from_retry_queue(self, item_id: str) -> bool:
        """
        Remove an item from the retry queue after processing

        Args:
            item_id: ID of the item to remove

        Returns:
            bool: True if removal was successful, False otherwise
        """
        try:
            session = self.Session()
            try:
                item = session.query(RetryQueueItem).filter(RetryQueueItem.id == item_id).first()

                if not item:
                    logger.warning(f"Retry queue item not found for ID: {item_id}")
                    return False

                session.delete(item)
                session.commit()

                logger.info(f"Removed item from retry queue: {item_id}")
                return True
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Failed to remove from retry queue: {str(e)}", error=str(e), item_id=item_id)
            return False

    async def get_message_status(self, message_id: str) -> Optional[Dict]:
        """
        Get the current status of a message

        Args:
            message_id: ID of the message to check

        Returns:
            Optional[Dict]: Message status information or None if not found
        """
        try:
            session = self.Session()
            try:
                message = session.query(OutboundMessage).filter(OutboundMessage.message_id == message_id).first()

                if not message:
                    logger.warning(f"Message not found for ID: {message_id}")
                    return None

                status_info = {
                    'message_id': message.message_id,
                    'conversation_id': message.conversation_id,
                    'channel_destination': message.channel_destination,
                    'delivery_status': message.delivery_status,
                    'delivery_attempts': message.delivery_attempts,
                    'last_delivery_attempt': message.last_delivery_attempt.isoformat() if message.last_delivery_attempt else None,
                    'failure_reason': message.failure_reason,
                    'priority': message.priority,
                    'created_at': message.created_at.isoformat(),
                    'updated_at': message.updated_at.isoformat()
                }

                return status_info
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Failed to get message status: {str(e)}", error=str(e), message_id=message_id)
            return None

    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get real delivery metrics from the database

        Returns:
            Dict: Aggregated delivery metrics by channel
        """
        try:
            session = self.Session()
            try:
                from sqlalchemy import func, case

                channels = ['gmail', 'whatsapp', 'webform']

                # Total messages processed
                total = session.query(func.count(OutboundMessage.id)).scalar() or 0

                # Per-channel counts from delivery logs
                delivery_by_channel = {}
                success_rate = {}
                avg_delivery_time = {}
                rate_limit_hits = {}

                for ch in channels:
                    total_ch = session.query(func.count(DeliveryLog.id)).filter(
                        DeliveryLog.channel == ch
                    ).scalar() or 0

                    success_ch = session.query(func.count(DeliveryLog.id)).filter(
                        DeliveryLog.channel == ch,
                        DeliveryLog.success == True
                    ).scalar() or 0

                    avg_time = session.query(func.avg(DeliveryLog.processing_time_ms)).filter(
                        DeliveryLog.channel == ch,
                        DeliveryLog.success == True
                    ).scalar() or 0.0

                    rl_hits = session.query(func.count(DeliveryLog.id)).filter(
                        DeliveryLog.channel == ch,
                        DeliveryLog.rate_limit_hit == True
                    ).scalar() or 0

                    delivery_by_channel[ch] = total_ch
                    success_rate[ch] = round((success_ch / total_ch * 100), 2) if total_ch > 0 else 0.0
                    avg_delivery_time[ch] = round(float(avg_time), 2)
                    rate_limit_hits[ch] = rl_hits

                # Retry queue sizes per channel
                retry_queue_size = {}
                for ch in channels:
                    # Join retry queue with outbound messages to get channel
                    count = session.query(func.count(RetryQueueItem.id)).join(
                        OutboundMessage,
                        RetryQueueItem.outbound_message_id == OutboundMessage.message_id
                    ).filter(
                        OutboundMessage.channel_destination == ch
                    ).scalar() or 0
                    retry_queue_size[ch] = count

                return {
                    "total_messages_processed": total,
                    "delivery_by_channel": delivery_by_channel,
                    "delivery_success_rate": success_rate,
                    "average_delivery_time_ms": avg_delivery_time,
                    "rate_limit_hits": rate_limit_hits,
                    "retry_queue_size": retry_queue_size
                }
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Failed to get metrics: {str(e)}", error=str(e))
            return {
                "total_messages_processed": 0,
                "delivery_by_channel": {"gmail": 0, "whatsapp": 0, "webform": 0},
                "delivery_success_rate": {"gmail": 0.0, "whatsapp": 0.0, "webform": 0.0},
                "average_delivery_time_ms": {"gmail": 0.0, "whatsapp": 0.0, "webform": 0.0},
                "rate_limit_hits": {"gmail": 0, "whatsapp": 0, "webform": 0},
                "retry_queue_size": {"gmail": 0, "whatsapp": 0, "webform": 0}
            }

    async def clear_retry_queue(self) -> int:
        """
        Clear all items from the retry queue

        Returns:
            int: Number of items removed
        """
        try:
            session = self.Session()
            try:
                count = session.query(RetryQueueItem).delete()
                session.commit()
                logger.info(f"Cleared {count} items from retry queue")
                return count
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Failed to clear retry queue: {str(e)}", error=str(e))
            return 0

    async def reset_delivery_stats(self) -> bool:
        """
        Reset delivery statistics by clearing delivery logs

        Returns:
            bool: True if reset was successful
        """
        try:
            session = self.Session()
            try:
                session.query(DeliveryLog).delete()
                session.commit()
                logger.info("Delivery statistics reset successfully")
                return True
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Failed to reset delivery stats: {str(e)}", error=str(e))
            return False

    async def get_delivery_logs(self, message_id: str) -> List[Dict]:
        """
        Get delivery logs for a specific message

        Args:
            message_id: ID of the message

        Returns:
            List[Dict]: List of delivery log entries
        """
        try:
            session = self.Session()
            try:
                logs = session.query(DeliveryLog).filter(
                    DeliveryLog.outbound_message_id == message_id
                ).order_by(DeliveryLog.timestamp.desc()).all()

                log_list = []
                for log in logs:
                    log_dict = {
                        'id': str(log.id),
                        'attempt_number': log.attempt_number,
                        'channel': log.channel,
                        'delivery_method': log.delivery_method,
                        'success': log.success,
                        'error_message': log.error_message,
                        'rate_limit_hit': log.rate_limit_hit,
                        'timestamp': log.timestamp.isoformat(),
                        'processing_time_ms': log.processing_time_ms
                    }
                    log_list.append(log_dict)

                logger.info(f"Retrieved {len(log_list)} delivery logs for message {message_id}")
                return log_list
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Failed to get delivery logs: {str(e)}", error=str(e), message_id=message_id)
            return []

    async def process_retry_queue(self, delivery_handler: callable) -> Dict[str, int]:
        """
        Process all items in the retry queue

        Args:
            delivery_handler: Function to handle the delivery (should accept message_id as parameter)

        Returns:
            Dict[str, int]: Statistics about retry processing
        """
        stats = {
            'processed': 0,
            'successful': 0,
            'failed_again': 0,
            'removed': 0
        }

        retry_items = await self.get_pending_retries()

        for item in retry_items:
            try:
                logger.info(
                    f"Processing retry for message {item.outbound_message_id}",
                    retry_item_id=str(item.id),
                    attempt_number=item.attempt_number
                )

                # Call the delivery handler
                success = await delivery_handler(item.outbound_message_id, item.attempt_number)

                if success:
                    # If successful, update status and remove from queue
                    await self.update_delivery_status(item.outbound_message_id, 'delivered')
                    await self.remove_from_retry_queue(str(item.id))

                    stats['successful'] += 1
                    stats['removed'] += 1
                else:
                    # If still failed, check if we should retry again or mark as failed
                    if item.attempt_number >= settings.delivery_retry_attempts:
                        # Max attempts reached, mark as failed permanently
                        await self.update_delivery_status(item.outbound_message_id, 'failed', 'Max retry attempts reached')
                        await self.remove_from_retry_queue(str(item.id))

                        stats['failed_again'] += 1
                        stats['removed'] += 1
                    else:
                        # Schedule next retry
                        next_retry_time = self.retry_mechanism.calculate_next_retry_time(item.attempt_number + 1)
                        await self.add_to_retry_queue(
                            item.outbound_message_id,
                            item.attempt_number + 1,
                            next_retry_time,
                            'Temporary failure, scheduled for retry',
                            item.priority
                        )

                        stats['failed_again'] += 1

                stats['processed'] += 1
            except Exception as e:
                logger.error(
                    f"Error processing retry for message {item.outbound_message_id}: {str(e)}",
                    error=str(e),
                    retry_item_id=str(item.id)
                )
                stats['failed_again'] += 1

        logger.info("Retry queue processing completed", stats=stats)
        return stats


# Global delivery tracker instance
delivery_tracker = DeliveryTracker()


def initialize_delivery_tracker():
    """
    Initialize the global delivery tracker instance
    """
    delivery_tracker.initialize_database()


def get_delivery_tracker() -> DeliveryTracker:
    """
    Get the global delivery tracker instance

    Returns:
        DeliveryTracker: The global delivery tracker instance
    """
    return delivery_tracker