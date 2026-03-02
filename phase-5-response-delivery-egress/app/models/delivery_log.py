from sqlalchemy import Column, String, Integer, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime
import json

Base = declarative_base()

class DeliveryLog(Base):
    """
    Records delivery attempts with status, timestamps, and error details for audit and troubleshooting
    """
    __tablename__ = 'delivery_logs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    outbound_message_id = Column(String, nullable=False)  # Foreign key to OutboundMessage
    attempt_number = Column(Integer, nullable=False)  # Sequence number of delivery attempt
    channel = Column(String, nullable=False)  # Enum: 'gmail', 'whatsapp', 'webform'
    delivery_method = Column(String)  # Specific delivery method used
    request_payload = Column(String)  # JSON string for payload sent to delivery service
    response_payload = Column(String)  # JSON string for response received from delivery service
    status_code = Column(Integer)  # HTTP status code or service-specific code
    success = Column(Boolean, nullable=False, default=False)  # Whether the delivery attempt was successful
    error_message = Column(String)  # Error details if delivery failed
    rate_limit_hit = Column(Boolean, default=False)  # Whether this failure was due to rate limiting
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)  # When the delivery attempt was made
    processing_time_ms = Column(Integer)  # Time taken for the delivery attempt

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    def __init__(self, outbound_message_id, attempt_number, channel, **kwargs):
        """
        Initialize a DeliveryLog instance

        Args:
            outbound_message_id: Foreign key to OutboundMessage
            attempt_number: Sequence number of delivery attempt
            channel: Channel type ('gmail', 'whatsapp', 'webform')
        """
        super().__init__()

        # Validate required fields
        if not outbound_message_id:
            raise ValueError("outbound_message_id is required")
        if attempt_number is None or attempt_number <= 0:
            raise ValueError(f"attempt_number must be positive, got {attempt_number}")
        if channel not in ['gmail', 'whatsapp', 'webform']:
            raise ValueError(f"channel must be one of 'gmail', 'whatsapp', 'webform', got '{channel}'")
        if success := kwargs.get('success'):
            if not isinstance(success, bool):
                raise ValueError(f"success must be boolean, got {type(success)}")
        if processing_time_ms := kwargs.get('processing_time_ms', 0):
            if processing_time_ms < 0:
                raise ValueError(f"processing_time_ms must be non-negative, got {processing_time_ms}")

        # Set attributes
        self.outbound_message_id = outbound_message_id
        self.attempt_number = attempt_number
        self.channel = channel

        # Set optional attributes
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def validate(self):
        """
        Validate the DeliveryLog instance according to the validation rules
        """
        errors = []

        if not self.outbound_message_id:
            errors.append("outbound_message_id must reference a valid OutboundMessage")

        if self.attempt_number <= 0:
            errors.append("attempt_number must be positive")

        if self.channel not in ['gmail', 'whatsapp', 'webform']:
            errors.append("channel must be one of the allowed values")

        if not isinstance(self.success, bool):
            errors.append("success must be boolean")

        if self.processing_time_ms < 0:
            errors.append("processing_time_ms must be non-negative")

        if errors:
            raise ValueError(f"Validation errors: {'; '.join(errors)}")

    def to_dict(self):
        """Convert the model to a dictionary representation"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            elif column.name in ['request_payload', 'response_payload'] and value:
                # Parse JSON string to dict if it's valid JSON
                try:
                    result[column.name] = json.loads(value)
                except (TypeError, json.JSONDecodeError):
                    result[column.name] = value
            else:
                result[column.name] = value
        return result

    @classmethod
    def create_from_delivery_attempt(cls, outbound_message_id, attempt_number, channel,
                                   delivery_method=None, request_payload=None, response_payload=None,
                                   status_code=None, success=False, error_message=None,
                                   rate_limit_hit=False, processing_time_ms=None):
        """
        Factory method to create a DeliveryLog from a delivery attempt

        Args:
            outbound_message_id: ID of the outbound message
            attempt_number: Attempt number for this delivery
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
            DeliveryLog instance
        """
        return cls(
            outbound_message_id=outbound_message_id,
            attempt_number=attempt_number,
            channel=channel,
            delivery_method=delivery_method,
            request_payload=json.dumps(request_payload) if request_payload else None,
            response_payload=json.dumps(response_payload) if response_payload else None,
            status_code=status_code,
            success=success,
            error_message=error_message,
            rate_limit_hit=rate_limit_hit,
            processing_time_ms=processing_time_ms
        )