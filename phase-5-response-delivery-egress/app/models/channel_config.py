from sqlalchemy import Column, String, Integer, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime
import json

Base = declarative_base()

class ChannelConfig(Base):
    """
    Stores configuration settings for each communication channel including rate limits and credentials
    """
    __tablename__ = 'channel_configs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    channel_type = Column(String, nullable=False)  # Enum: 'gmail', 'whatsapp', 'webform'
    api_endpoint = Column(String)  # API endpoint URL for the channel
    rate_limit_requests = Column(Integer)  # Max requests per time window
    rate_limit_window_seconds = Column(Integer)  # Time window for rate limiting
    burst_limit = Column(Integer)  # Max burst requests allowed
    retry_attempts = Column(Integer)  # Number of retry attempts for failed deliveries
    retry_delay_base = Column(Integer)  # Base delay for exponential backoff in seconds
    timeout_seconds = Column(Integer)  # Timeout for delivery attempts
    enabled = Column(Boolean, default=True)  # Whether this channel is enabled for delivery
    credentials_config = Column(String)  # JSON string for configuration for API credentials

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, channel_type, **kwargs):
        """
        Initialize a ChannelConfig instance

        Args:
            channel_type: Channel type ('gmail', 'whatsapp', 'webform')
        """
        super().__init__()

        # Validate required fields
        if channel_type not in ['gmail', 'whatsapp', 'webform']:
            raise ValueError(f"channel_type must be one of 'gmail', 'whatsapp', 'webform', got '{channel_type}'")
        if rate_limit_requests := kwargs.get('rate_limit_requests', 0):
            if rate_limit_requests <= 0:
                raise ValueError(f"rate_limit_requests must be positive, got {rate_limit_requests}")
        if rate_limit_window_seconds := kwargs.get('rate_limit_window_seconds', 0):
            if rate_limit_window_seconds <= 0:
                raise ValueError(f"rate_limit_window_seconds must be positive, got {rate_limit_window_seconds}")
        if retry_attempts := kwargs.get('retry_attempts', 0):
            if retry_attempts < 0:
                raise ValueError(f"retry_attempts must be non-negative, got {retry_attempts}")
        if retry_delay_base := kwargs.get('retry_delay_base', 0):
            if retry_delay_base <= 0:
                raise ValueError(f"retry_delay_base must be positive, got {retry_delay_base}")
        if timeout_seconds := kwargs.get('timeout_seconds', 0):
            if timeout_seconds <= 0:
                raise ValueError(f"timeout_seconds must be positive, got {timeout_seconds}")
        if enabled := kwargs.get('enabled'):
            if not isinstance(enabled, bool):
                raise ValueError(f"enabled must be boolean, got {type(enabled)}")

        # Set attributes
        self.channel_type = channel_type

        # Set optional attributes
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def validate(self):
        """
        Validate the ChannelConfig instance according to the validation rules
        """
        errors = []

        if self.channel_type not in ['gmail', 'whatsapp', 'webform']:
            errors.append("channel_type must be one of the allowed values")

        if self.rate_limit_requests is not None and self.rate_limit_requests <= 0:
            errors.append("rate_limit_requests must be positive")

        if self.rate_limit_window_seconds is not None and self.rate_limit_window_seconds <= 0:
            errors.append("rate_limit_window_seconds must be positive")

        if self.retry_attempts is not None and self.retry_attempts < 0:
            errors.append("retry_attempts must be non-negative")

        if self.retry_delay_base is not None and self.retry_delay_base <= 0:
            errors.append("retry_delay_base must be positive")

        if self.timeout_seconds is not None and self.timeout_seconds <= 0:
            errors.append("timeout_seconds must be positive")

        if self.enabled is not None and not isinstance(self.enabled, bool):
            errors.append("enabled must be boolean")

        if errors:
            raise ValueError(f"Validation errors: {'; '.join(errors)}")

    def to_dict(self):
        """Convert the model to a dictionary representation"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            elif column.name == 'credentials_config' and value:
                # Parse JSON string to dict if it's valid JSON
                try:
                    result[column.name] = json.loads(value)
                except (TypeError, json.JSONDecodeError):
                    result[column.name] = value
            else:
                result[column.name] = value
        return result

    def is_rate_limited(self, current_requests, current_window_start):
        """
        Check if the channel is currently rate limited

        Args:
            current_requests: Number of requests made in the current window
            current_window_start: Start time of the current rate limit window

        Returns:
            True if rate limited, False otherwise
        """
        if self.rate_limit_requests is None:
            return False  # No rate limit configured

        return current_requests >= self.rate_limit_requests

    def update_credentials(self, credentials):
        """
        Update the credentials configuration for this channel

        Args:
            credentials: Dictionary containing credential information
        """
        if isinstance(credentials, dict):
            self.credentials_config = json.dumps(credentials)
        else:
            self.credentials_config = credentials