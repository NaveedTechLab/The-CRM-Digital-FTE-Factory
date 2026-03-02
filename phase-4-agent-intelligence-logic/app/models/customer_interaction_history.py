from sqlalchemy import Column, String, Text, DateTime, Float, Integer, Boolean, ForeignKey, ARRAY, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class CustomerInteractionHistory(Base):
    __tablename__ = "customer_interaction_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String, nullable=False)  # Foreign key to customer in Phase 2 DB
    conversation_id = Column(String, nullable=True)  # Identifies related messages in conversation
    first_contact_date = Column(DateTime, nullable=False, default=func.now())  # When customer first contacted support
    last_interaction_date = Column(DateTime, nullable=True)  # When customer last interacted
    total_interactions = Column(Integer, default=0)  # Total number of interactions with this customer
    successful_resolutions = Column(Integer, default=0)  # Number of issues resolved without escalation
    escalation_count = Column(Integer, default=0)  # Number of times issues were escalated
    preferred_channels = Column(ARRAY(String), nullable=True)  # Customer's preferred communication channels
    communication_preferences = Column(JSON, nullable=True)  # Customer's communication preferences
    issue_categories = Column(ARRAY(String), nullable=True)  # Categories of issues frequently raised
    sentiment_trend = Column(String, nullable=True)  # Enum: 'positive', 'neutral', 'negative', 'volatile'
    support_tier = Column(String, default='standard')  # Enum: 'standard', 'premium', 'vip'
    notes = Column(Text, nullable=True)  # Free-form notes about the customer

    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())