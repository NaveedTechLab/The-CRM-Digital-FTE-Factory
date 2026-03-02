"""
Shared test fixtures for Phase 2 Core Infrastructure tests.
"""
import pytest
import uuid
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone


@pytest.fixture
def sample_customer_data():
    """Sample customer data for testing."""
    return {
        "name": "John Doe",
        "email": f"john.doe.{uuid.uuid4().hex[:8]}@example.com",
        "phone": "+1234567890",
        "contact_preferences": {"preferred_channel": "email"}
    }


@pytest.fixture
def sample_ticket_data():
    """Sample ticket data for testing."""
    return {
        "subject": "Test Support Ticket",
        "description": "I need help with my account settings.",
        "status": "open",
        "priority": "medium",
        "channel": "email"
    }


@pytest.fixture
def sample_message_data():
    """Sample message data for testing."""
    return {
        "sender_type": "customer",
        "sender_id": "customer@example.com",
        "content": "I need help resetting my password.",
        "content_type": "text",
        "direction": "inbound",
        "channel_metadata": {"source": "email", "subject": "Password Reset"}
    }


@pytest.fixture
def sample_knowledge_base_data():
    """Sample knowledge base article for testing."""
    return {
        "title": "How to Reset Your Password",
        "content": "To reset your password, go to Settings > Security > Change Password.",
        "category": "faq",
        "status": "published",
        "author": "admin"
    }


@pytest.fixture
def sample_kafka_message():
    """Sample Kafka message for testing."""
    return {
        "event_type": "inbound_message",
        "channel": "email",
        "sender_id": "customer@example.com",
        "content": "Hello, I need help with my order.",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    session.refresh = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    session.query = MagicMock()
    return session
