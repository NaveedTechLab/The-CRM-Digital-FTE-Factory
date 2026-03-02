from sqlalchemy import Column, String, Text, DateTime, Float, Integer, Boolean, ForeignKey, ARRAY, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class EscalationRecord(Base):
    __tablename__ = "escalation_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_message_id = Column(String, nullable=False)  # Foreign key to AgentMessage that triggered escalation
    conversation_id = Column(String, nullable=False)  # Identifies the conversation being escalated
    customer_id = Column(String, nullable=False)  # Foreign key to customer in Phase 2 DB
    escalation_reason = Column(String, nullable=False)  # Reason for escalation
    trigger_keywords = Column(ARRAY(String), nullable=True)  # Keywords that triggered escalation
    confidence_at_escalation = Column(Float, nullable=True)  # Confidence score when escalation was triggered, 0.0-1.0
    human_agent_assigned = Column(String, nullable=True)  # ID of human agent assigned to case
    priority_level = Column(String, default='medium')  # Enum: 'low', 'medium', 'high', 'critical'
    estimated_resolution_time = Column(DateTime, nullable=True)  # Estimated time for resolution
    status = Column(String, default='pending_assignment')  # Enum: 'pending_assignment', 'assigned', 'in_progress', 'resolved', 'closed'
    original_agent_notes = Column(Text, nullable=True)  # Notes from the AI agent about the issue
    handover_timestamp = Column(DateTime, nullable=False, default=func.now())  # When escalation was initiated
    resolution_timestamp = Column(DateTime, nullable=True)  # When issue was resolved by human
    resolution_satisfaction = Column(Integer, nullable=True)  # Satisfaction rating after resolution, 1-5

    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())