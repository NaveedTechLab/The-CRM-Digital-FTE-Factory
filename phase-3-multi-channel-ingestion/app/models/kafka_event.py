from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator
import uuid


class KafkaEvent(BaseModel):
    """Model for Kafka events"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    inbound_message_id: str = Field(..., description="Foreign key to InboundMessage")
    topic_name: str = Field(default="inbound_events", description="Name of the Kafka topic")
    partition: Optional[int] = None
    offset: Optional[int] = None
    event_payload: Dict[str, Any] = Field(..., description="The actual payload published to Kafka")
    publish_timestamp: Optional[datetime] = None
    delivery_status: str = Field(default="pending", pattern=r"^(pending|published|failed|retried)$")
    retry_count: int = Field(default=0)
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @validator('partition', 'offset')
    def validate_non_negative_numbers(cls, v):
        """Validate that partition and offset are non-negative"""
        if v is not None and v < 0:
            raise ValueError('Partition and offset must be non-negative')
        return v

    @validator('retry_count')
    def validate_retry_count(cls, v):
        """Validate that retry_count is non-negative"""
        if v < 0:
            raise ValueError('Retry count must be non-negative')
        return v

    @validator('delivery_status')
    def validate_delivery_status(cls, v):
        """Validate that delivery_status is one of the allowed values"""
        if v not in ['pending', 'published', 'failed', 'retried']:
            raise ValueError('Delivery status must be one of: pending, published, failed, retried')
        return v

    @validator('topic_name')
    def validate_topic_name(cls, v):
        """Validate that topic_name is valid"""
        if not v or not isinstance(v, str):
            raise ValueError('Topic name must be a non-empty string')
        return v