from sqlalchemy import Column, String, Text, DateTime, Float, Integer, Boolean, ForeignKey, ARRAY, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class AgentToolCall(Base):
    __tablename__ = "agent_tool_calls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_message_id = Column(String, nullable=False)  # Foreign key to AgentMessage
    tool_name = Column(String, nullable=False)  # Name of the tool that was called
    tool_input = Column(JSON, nullable=True)  # Input parameters for the tool call
    tool_output = Column(JSON, nullable=True)  # Output returned by the tool
    execution_time_ms = Column(Integer, nullable=True)  # Time taken for tool execution in milliseconds
    success = Column(Boolean, default=False)  # Whether the tool call was successful
    error_message = Column(String, nullable=True)  # Error details if tool call failed
    confidence_impact = Column(Float, nullable=True)  # How much this tool call affected the final confidence score, -1.0 to 1.0
    invocation_order = Column(Integer, nullable=True)  # Order in which tools were called

    created_at = Column(DateTime, nullable=False, default=func.now())