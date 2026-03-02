from sqlalchemy import Column, String, Text, DateTime, Float, Integer, Boolean, ForeignKey, ARRAY, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class OutboundMessage(Base):
    __tablename__ = "outbound_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_message_id = Column(String, nullable=False)  # Foreign key to AgentMessage that generated this response
    conversation_id = Column(String, nullable=False)  # Identifies related messages in conversation
    response_type = Column(String, nullable=False)  # Enum: 'answer', 'escalation', 'ticket_created', 'follow_up'
    content = Column(Text, nullable=False)  # The agent's response content
    channel_destination = Column(String, nullable=False)  # Enum: 'gmail', 'whatsapp', 'webform'
    recipient_id = Column(String, nullable=False)  # Email, phone number, or other identifier for recipient
    confidence_score = Column(Float, nullable=True)  # Confidence in the response, 0.0-1.0
    kb_sources = Column(ARRAY(String), nullable=True)  # IDs of knowledge base articles used
    tools_used = Column(ARRAY(String), nullable=True)  # Names of tools invoked during response generation
    escalation_reason = Column(String, nullable=True)  # Reason for escalation if applicable
    ticket_reference = Column(String, nullable=True)  # ID of ticket created if applicable
    delivery_status = Column(String, default='pending')  # Enum: 'pending', 'delivered', 'failed', 'retracted'
    delivery_attempts = Column(Integer, default=0)  # Number of delivery attempts
    scheduled_delivery = Column(DateTime, nullable=True)  # When the message should be sent
    actual_delivery = Column(DateTime, nullable=True)  # When the message was actually sent

    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())