from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime

Base = declarative_base()

class RetryQueueItem(Base):
    """
    Represents an item in the retry queue for failed delivery attempts
    """
    __tablename__ = 'retry_queue_items'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    outbound_message_id = Column(String, nullable=False)  # Foreign key to OutboundMessage
    attempt_number = Column(Integer, nullable=False)  # Current attempt number
    scheduled_retry = Column(DateTime, nullable=False)  # When to attempt the retry
    failure_reason = Column(String)  # Reason for previous failure
    priority = Column(Integer, default=0)  # Priority for processing, higher numbers processed first

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, outbound_message_id, attempt_number, scheduled_retry, **kwargs):
        """
        Initialize a RetryQueueItem instance

        Args:
            outbound_message_id: Foreign key to OutboundMessage
            attempt_number: Current attempt number
            scheduled_retry: When to attempt the retry
        """
        super().__init__()

        # Validate required fields
        if not outbound_message_id:
            raise ValueError("outbound_message_id is required")
        if attempt_number is None or attempt_number <= 0:
            raise ValueError(f"attempt_number must be positive, got {attempt_number}")
        if scheduled_retry is None:
            raise ValueError("scheduled_retry is required")
        if priority := kwargs.get('priority', 0):
            if priority < 0:
                raise ValueError(f"priority must be non-negative, got {priority}")

        # Set attributes
        self.outbound_message_id = outbound_message_id
        self.attempt_number = attempt_number
        self.scheduled_retry = scheduled_retry

        # Set optional attributes
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def validate(self):
        """
        Validate the RetryQueueItem instance according to the validation rules
        """
        errors = []

        if not self.outbound_message_id:
            errors.append("outbound_message_id must reference a valid OutboundMessage")

        if self.attempt_number <= 0:
            errors.append("attempt_number must be positive")

        if self.priority < 0:
            errors.append("priority must be non-negative")

        if errors:
            raise ValueError(f"Validation errors: {'; '.join(errors)}")

    def to_dict(self):
        """Convert the model to a dictionary representation"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        return result

    def is_ready_for_retry(self):
        """
        Check if this retry queue item is ready to be processed

        Returns:
            True if ready for retry, False otherwise
        """
        return datetime.utcnow() >= self.scheduled_retry

    def update_scheduled_retry(self, new_scheduled_retry):
        """
        Update the scheduled retry time

        Args:
            new_scheduled_retry: New time for the retry attempt
        """
        self.scheduled_retry = new_scheduled_retry
        self.updated_at = datetime.utcnow()