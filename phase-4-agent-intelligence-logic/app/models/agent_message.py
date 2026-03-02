from sqlalchemy import Column, String, Text, DateTime, Float, Integer, Boolean, ForeignKey, ARRAY, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class AgentMessage(Base):
    __tablename__ = "agent_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String, nullable=False)  # Foreign key to customer in Phase 2 DB
    conversation_id = Column(String, nullable=False)  # Identifies related messages in conversation
    inbound_message_id = Column(String, nullable=True)  # Reference to original inbound message from Phase 3
    message_type = Column(String, nullable=False)  # Enum: 'customer_query', 'agent_response', 'system_note'
    content = Column(Text, nullable=False)  # The actual message content
    role = Column(String, nullable=False)  # Enum: 'customer', 'agent', 'system'
    timestamp = Column(DateTime, nullable=False, default=func.now())
    confidence_score = Column(Float, nullable=True)  # Confidence in agent's response or query understanding, 0.0-1.0
    intents = Column(ARRAY(String), nullable=True)  # Detected intents from customer query
    entities = Column(JSON, nullable=True)  # Extracted entities from customer query
    kb_articles_used = Column(ARRAY(String), nullable=True)  # IDs of knowledge base articles referenced
    escalation_flag = Column(Boolean, default=False)  # Whether this message triggered escalation
    processed_status = Column(String, default='received')  # Enum: 'received', 'processing', 'processed', 'escalated', 'failed'

    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())