from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator
import uuid


class ChannelPayload(BaseModel):
    """Model to represent raw payloads from different channels"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    raw_payload: Dict[str, Any] = Field(..., description="The original, unprocessed payload from the channel")
    channel_type: str = Field(..., pattern=r"^(gmail|whatsapp|webform)$", description="Type of channel the payload came from")
    webhook_signature: Optional[str] = None
    security_validated: bool = Field(default=False, description="Whether the payload passed security validation")
    validation_errors: List[str] = Field(default=[], description="Errors that occurred during validation")
    normalized_message_id: Optional[str] = None  # Foreign key to InboundMessage when normalized
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @validator('raw_payload')
    def validate_raw_payload(cls, v):
        """Validate that raw_payload is valid JSON-like structure"""
        if not isinstance(v, dict):
            raise ValueError('Raw payload must be a dictionary')
        return v

    @validator('channel_type')
    def validate_channel_type(cls, v):
        """Validate that channel_type is one of the allowed values"""
        if v not in ['gmail', 'whatsapp', 'webform']:
            raise ValueError('Channel type must be one of: gmail, whatsapp, webform')
        return v

    @validator('security_validated')
    def validate_security_validated(cls, v):
        """Validate that security_validated is a boolean"""
        if not isinstance(v, bool):
            raise ValueError('Security validated must be a boolean')
        return v