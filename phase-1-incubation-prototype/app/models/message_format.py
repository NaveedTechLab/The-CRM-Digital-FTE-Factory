"""
Pydantic models for unified message format used in the Customer Success Digital FTE.
"""
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

class UnifiedMessage(BaseModel):
    """
    A unified message format that standardizes input from all channels
    (email, WhatsApp, webform) for processing by the Customer Success Agent.
    """
    source_channel: str  # 'email', 'whatsapp', 'webform'
    customer_identifier: str  # email or phone number
    customer_name: str
    original_content: str
    normalized_content: str
    timestamp: datetime = datetime.now()
    metadata: Dict[str, Any] = {}

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class NormalizedMessageRequest(BaseModel):
    """
    Request model for normalizing a message from any channel.
    """
    source_channel: str  # 'email', 'whatsapp', 'webform'
    customer_identifier: str  # email or phone number
    customer_name: str
    message: str
    timestamp: Optional[datetime] = None

class ChannelSpecificMetadata(BaseModel):
    """
    Metadata specific to each communication channel.
    """
    email_address: Optional[str] = None
    phone_number: Optional[str] = None
    # Additional channel-specific fields can be added here

class ProcessingInfo(BaseModel):
    """
    Information about message processing.
    """
    original_length: int
    normalized_at: str
    # Additional processing information can be added here