from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime

Base = declarative_base()

class RateLimitState(Base):
    """
    Used for tracking rate limiting state across the system
    """
    __tablename__ = 'rate_limit_states'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    channel_type = Column(String, nullable=False)  # Enum: 'gmail', 'whatsapp', 'webform'
    window_start = Column(DateTime, nullable=False)  # Start time of the current rate limit window
    requests_count = Column(Integer, default=0)  # Number of requests made in the current window
    last_access = Column(DateTime, nullable=False, default=datetime.utcnow)  # Timestamp of last request
    reset_time = Column(DateTime, nullable=False)  # When the rate limit window resets

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, channel_type, window_start, reset_time, **kwargs):
        """
        Initialize a RateLimitState instance

        Args:
            channel_type: Channel type ('gmail', 'whatsapp', 'webform')
            window_start: Start time of the current rate limit window
            reset_time: When the rate limit window resets
        """
        super().__init__()

        # Validate required fields
        if channel_type not in ['gmail', 'whatsapp', 'webform']:
            raise ValueError(f"channel_type must be one of 'gmail', 'whatsapp', 'webform', got '{channel_type}'")
        if requests_count := kwargs.get('requests_count', 0):
            if requests_count < 0:
                raise ValueError(f"requests_count must be non-negative, got {requests_count}")
        if reset_time <= window_start:
            raise ValueError(f"reset_time must be after window_start, got {reset_time} <= {window_start}")

        # Set attributes
        self.channel_type = channel_type
        self.window_start = window_start
        self.reset_time = reset_time

        # Set optional attributes
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def validate(self):
        """
        Validate the RateLimitState instance according to the validation rules
        """
        errors = []

        if self.channel_type not in ['gmail', 'whatsapp', 'webform']:
            errors.append("channel_type must be one of the allowed values")

        if self.requests_count < 0:
            errors.append("requests_count must be non-negative")

        if self.reset_time <= self.window_start:
            errors.append("reset_time must be after window_start")

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

    def increment_request(self):
        """
        Increment the request count and update the last access time
        """
        self.requests_count += 1
        self.last_access = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def reset_window(self, new_window_start, new_reset_time):
        """
        Reset the rate limit window

        Args:
            new_window_start: New start time for the rate limit window
            new_reset_time: New reset time for the rate limit window
        """
        if new_reset_time <= new_window_start:
            raise ValueError(f"new_reset_time must be after new_window_start, got {new_reset_time} <= {new_window_start}")

        self.window_start = new_window_start
        self.reset_time = new_reset_time
        self.requests_count = 0
        self.last_access = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def is_expired(self):
        """
        Check if the current rate limit window has expired

        Returns:
            True if expired, False otherwise
        """
        return datetime.utcnow() >= self.reset_time

    def time_remaining(self):
        """
        Calculate the time remaining in the current rate limit window

        Returns:
            Seconds remaining in the window
        """
        remaining = self.reset_time - datetime.utcnow()
        return max(0, int(remaining.total_seconds()))