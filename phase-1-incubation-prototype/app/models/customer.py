from pydantic import BaseModel
from typing import Optional, Dict, Any
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

class Customer(BaseModel):
    """
    Pydantic model for Customer entity representing a customer with identifiers,
    contact information, and profile data.
    """
    id: str = str(uuid.uuid4())
    name: str
    email: str
    phone: Optional[str] = None
    contact_preferences: Optional[Dict[str, Any]] = {}
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    last_interaction: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            uuid.UUID: str
        }

class CustomerCreateRequest(BaseModel):
    """
    Request model for creating a new customer
    """
    name: str
    email: str
    phone: Optional[str] = None
    contact_preferences: Optional[Dict[str, Any]] = {}

class CustomerUpdateRequest(BaseModel):
    """
    Request model for updating an existing customer
    """
    name: Optional[str] = None
    phone: Optional[str] = None
    contact_preferences: Optional[Dict[str, Any]] = None