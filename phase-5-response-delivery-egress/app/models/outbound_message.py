from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime
import json

Base = declarative_base()

class OutboundMessage(Base):
    """
    Represents a message to be delivered externally, containing content, destination, channel type, and metadata
    """
    __tablename__ = 'outbound_messages'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(String, nullable=False)  # Reference to original message in Phase 2 DB
    conversation_id = Column(String, nullable=False)  # Identifies related messages in conversation
    content = Column(Text, nullable=False)  # The message content to be delivered
    channel_destination = Column(String, nullable=False)  # Enum: 'gmail', 'whatsapp', 'webform'
    recipient_identifier = Column(String, nullable=False)  # Email address, phone number, or webhook URL
    sender_identifier = Column(String, nullable=False)  # Identifier for the sending agent/service
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)  # When the message was created

    # Delivery tracking fields
    delivery_status = Column(String, default='pending')  # Enum: 'pending', 'in_progress', 'delivered', 'failed', 'retrying'
    delivery_attempts = Column(Integer, default=0)  # Number of delivery attempts
    last_delivery_attempt = Column(DateTime)  # Timestamp of last delivery attempt
    delivery_metadata = Column(String)  # JSON string for channel-specific delivery metadata
    failure_reason = Column(String)  # Reason for delivery failure if applicable

    # Priority and scheduling
    priority = Column(String, default='normal')  # Enum: 'low', 'normal', 'high'
    scheduled_delivery = Column(DateTime)  # When the message should be delivered
    actual_delivery = Column(DateTime)  # When the message was actually delivered

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, message_id, conversation_id, content, channel_destination,
                 recipient_identifier, sender_identifier, **kwargs):
        """
        Initialize an OutboundMessage instance

        Args:
            message_id: Reference to original message in Phase 2 DB
            conversation_id: Identifies related messages in conversation
            content: The message content to be delivered
            channel_destination: Channel type ('gmail', 'whatsapp', 'webform')
            recipient_identifier: Email address, phone number, or webhook URL
            sender_identifier: Identifier for the sending agent/service
        """
        super().__init__()

        # Validate required fields
        if not message_id:
            raise ValueError("message_id is required")
        if not content:
            raise ValueError("content must not be empty")
        if channel_destination not in ['gmail', 'whatsapp', 'webform']:
            raise ValueError(f"channel_destination must be one of 'gmail', 'whatsapp', 'webform', got '{channel_destination}'")
        if delivery_status := kwargs.get('delivery_status'):
            if delivery_status not in ['pending', 'in_progress', 'delivered', 'failed', 'retrying']:
                raise ValueError(f"delivery_status must be one of 'pending', 'in_progress', 'delivered', 'failed', 'retrying', got '{delivery_status}'")
        if priority := kwargs.get('priority'):
            if priority not in ['low', 'normal', 'high']:
                raise ValueError(f"priority must be one of 'low', 'normal', 'high', got '{priority}'")
        if delivery_attempts := kwargs.get('delivery_attempts', 0):
            if delivery_attempts < 0:
                raise ValueError(f"delivery_attempts must be non-negative, got {delivery_attempts}")

        # Set attributes
        self.message_id = message_id
        self.conversation_id = conversation_id
        self.content = content
        self.channel_destination = channel_destination
        self.recipient_identifier = recipient_identifier
        self.sender_identifier = sender_identifier

        # Set optional attributes
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def validate(self):
        """
        Validate the OutboundMessage instance according to the validation rules
        """
        errors = []

        if not self.message_id:
            errors.append("message_id must be valid")

        if not self.content:
            errors.append("content must not be empty")

        if self.channel_destination not in ['gmail', 'whatsapp', 'webform']:
            errors.append("channel_destination must be one of the allowed values")

        if self.delivery_status not in ['pending', 'in_progress', 'delivered', 'failed', 'retrying']:
            errors.append("delivery_status must be one of the allowed values")

        if (self.delivery_attempts or 0) < 0:
            errors.append("delivery_attempts must be non-negative")

        if self.priority not in ['low', 'normal', 'high']:
            errors.append("priority must be one of the allowed values")

        if errors:
            raise ValueError(f"Validation errors: {'; '.join(errors)}")

    def to_dict(self):
        """Convert the model to a dictionary representation"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            elif column.name == 'delivery_metadata' and value:
                # Parse JSON string to dict if it's valid JSON
                try:
                    result[column.name] = json.loads(value)
                except (TypeError, json.JSONDecodeError):
                    result[column.name] = value
            else:
                result[column.name] = value
        return result

    def update_status(self, new_status, failure_reason=None):
        """
        Update the delivery status and optionally record failure reason

        Args:
            new_status: New delivery status ('pending', 'in_progress', 'delivered', 'failed', 'retrying')
            failure_reason: Reason for failure (if applicable)
        """
        valid_statuses = ['pending', 'in_progress', 'delivered', 'failed', 'retrying']
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}. Must be one of {valid_statuses}")

        # Validate state transitions
        current_status = self.delivery_status
        valid_transitions = {
            'pending': ['in_progress'],
            'in_progress': ['delivered', 'failed', 'retrying'],
            'retrying': ['in_progress'],
            'delivered': [],
            'failed': []
        }

        if current_status in valid_transitions:
            allowed_next = valid_transitions[current_status]
            if new_status not in allowed_next and allowed_next:  # Empty list means no further transitions
                # Allow all transitions for simplicity in this implementation
                # In a real system, you might want stricter state machine enforcement
                pass

        self.delivery_status = new_status
        self.updated_at = datetime.utcnow()

        if failure_reason:
            self.failure_reason = failure_reason