from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class SupportTicket(BaseModel):
    """
    Pydantic model for SupportTicket entity representing a support request
    with status, category, priority, and interaction history.
    """
    id: str = str(uuid.uuid4())
    customer_id: str
    subject: str
    description: str
    status: str = "open"  # Enum: 'open', 'in-progress', 'resolved', 'closed'
    priority: str = "medium"  # Enum: 'low', 'medium', 'high', 'critical'
    channel: str  # Enum: 'gmail', 'whatsapp', 'webform'
    assigned_to: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    resolved_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            uuid.UUID: str
        }

class TicketCreateRequest(BaseModel):
    """
    Request model for creating a new ticket
    """
    customer_id: str
    subject: str
    description: str
    priority: str = "medium"  # Enum: 'low', 'medium', 'high', 'critical'
    channel: str  # Enum: 'gmail', 'whatsapp', 'webform'

class TicketUpdateRequest(BaseModel):
    """
    Request model for updating an existing ticket
    """
    status: Optional[str] = None  # Enum: 'open', 'in-progress', 'resolved', 'closed'
    assigned_to: Optional[str] = None
    resolved_at: Optional[datetime] = None