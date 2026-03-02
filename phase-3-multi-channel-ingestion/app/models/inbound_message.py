import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, validator
import uuid


class Attachment(BaseModel):
    """Attachment model for message attachments"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    content_type: str
    file_size: int
    download_url: Optional[str] = None
    stored_location: Optional[str] = None
    upload_status: str = Field(default="pending", pattern=r"^(pending|uploaded|failed)$")


class InboundMessage(BaseModel):
    """Pydantic model to unify fields from all channels"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = Field(..., description="Unique identifier for the sender (email, phone number, etc.)")
    channel: str = Field(..., pattern=r"^(gmail|whatsapp|webform)$", description="Channel through which the message was received")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the message was received")
    raw_payload: Dict[str, Any] = Field(..., description="Original payload from the channel")
    text_content: str = Field(..., description="The actual text content of the message")

    # Optional fields
    customer_name: Optional[str] = None
    customer_identifier: Optional[str] = None
    message_content: Optional[str] = None
    channel_message_id: Optional[str] = None
    priority: str = Field(default="medium", pattern=r"^(low|medium|high|critical)$")
    attachments: List[Attachment] = []
    channel_metadata: Optional[Dict[str, Any]] = {}
    processed_status: str = Field(default="received", pattern=r"^(received|normalized|identified|published)$")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @validator('sender_id')
    def validate_sender_id(cls, v):
        """Validate that sender_id is a valid email or phone number format"""
        if '@' in v:  # Likely an email
            # Basic email format validation
            if not re.match(r'^[^@]+@[^@]+\.[^@]+$', v):
                raise ValueError('Invalid email format')
        elif v.startswith(('whatsapp:', '+', 'tel:')):  # Likely a phone number
            # Remove prefixes and validate digits
            clean_num = v.replace('whatsapp:', '').replace('tel:', '').replace('+', '').replace('-', '').replace(' ', '')
            if not clean_num.isdigit():
                raise ValueError('Invalid phone number format')
        else:
            # Check if it's a plain phone number
            clean_num = v.replace('+', '').replace('-', '').replace(' ', '')
            if not clean_num.isdigit() or len(clean_num) < 10:
                raise ValueError('Invalid sender identifier format')
        return v

    @validator('timestamp')
    def validate_timestamp(cls, v):
        """Validate that timestamp is not in the future and not older than 24 hours"""
        now = datetime.utcnow()
        if v > now:
            raise ValueError('Timestamp cannot be in the future')
        if (now - v).days > 1:
            raise ValueError('Timestamp cannot be older than 24 hours')
        return v

    def __init__(self, **data):
        super().__init__(**data)
        self.updated_at = datetime.utcnow()