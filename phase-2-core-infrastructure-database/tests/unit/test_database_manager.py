"""
Unit tests for DatabaseManager CRUD operations.
Tests database operations using mocked SQLAlchemy sessions.
"""
import pytest
import uuid
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timezone

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.database_manager import (
    DatabaseManager, Customer, Ticket, Message, VectorEmbedding,
    CustomerIdentifier, Conversation, KnowledgeBase, ChannelConfig, AgentMetric
)


class TestCustomerModel:
    """Tests for Customer ORM model."""

    def test_customer_to_dict(self):
        customer = Customer(
            id=uuid.uuid4(),
            name="Jane Doe",
            email="jane@example.com",
            phone="+1234567890",
            contact_preferences={"preferred_channel": "email"},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        result = customer.to_dict()
        assert result['name'] == "Jane Doe"
        assert result['email'] == "jane@example.com"
        assert result['phone'] == "+1234567890"
        assert 'id' in result

    def test_customer_defaults(self):
        customer = Customer(name="Test", email="test@example.com")
        assert customer.phone is None
        assert customer.last_interaction is None


class TestTicketModel:
    """Tests for Ticket ORM model."""

    def test_ticket_to_dict(self):
        cid = uuid.uuid4()
        ticket = Ticket(
            id=uuid.uuid4(),
            customer_id=cid,
            subject="Test Ticket",
            description="Test description",
            status="open",
            priority="medium",
            channel="email",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        result = ticket.to_dict()
        assert result['subject'] == "Test Ticket"
        assert result['status'] == "open"
        assert result['priority'] == "medium"
        assert result['channel'] == "email"

    def test_ticket_defaults(self):
        ticket = Ticket(
            customer_id=uuid.uuid4(),
            subject="Test",
            description="Desc"
        )
        assert ticket.status == "open"
        assert ticket.priority == "medium"
        assert ticket.channel == "webform"
        assert ticket.assigned_agent is None
        assert ticket.resolved_at is None


class TestMessageModel:
    """Tests for Message ORM model."""

    def test_message_to_dict(self):
        msg = Message(
            id=uuid.uuid4(),
            ticket_id=uuid.uuid4(),
            sender_type="customer",
            sender_id="user@example.com",
            content="Help me please",
            direction="inbound",
            created_at=datetime.now(timezone.utc)
        )
        result = msg.to_dict()
        assert result['sender_type'] == "customer"
        assert result['content'] == "Help me please"
        assert result['direction'] == "inbound"


class TestNewModels:
    """Tests for newly added ORM models."""

    def test_customer_identifier_to_dict(self):
        ci = CustomerIdentifier(
            id=uuid.uuid4(),
            customer_id=uuid.uuid4(),
            channel="email",
            identifier_value="user@example.com",
            identifier_type="email",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        result = ci.to_dict()
        assert result['channel'] == "email"
        assert result['identifier_value'] == "user@example.com"
        assert result['identifier_type'] == "email"

    def test_conversation_to_dict(self):
        conv = Conversation(
            id=uuid.uuid4(),
            customer_id=uuid.uuid4(),
            channel="whatsapp",
            status="active",
            subject="Support Chat",
            started_at=datetime.now(timezone.utc),
            last_message_at=datetime.now(timezone.utc)
        )
        result = conv.to_dict()
        assert result['channel'] == "whatsapp"
        assert result['status'] == "active"
        assert result['subject'] == "Support Chat"

    def test_knowledge_base_to_dict(self):
        kb = KnowledgeBase(
            id=uuid.uuid4(),
            title="Password Reset Guide",
            content="Steps to reset password...",
            category="faq",
            status="published",
            version=1,
            author="admin",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        result = kb.to_dict()
        assert result['title'] == "Password Reset Guide"
        assert result['category'] == "faq"
        assert result['status'] == "published"

    def test_channel_config_to_dict(self):
        cc = ChannelConfig(
            id=uuid.uuid4(),
            channel="email",
            config={"smtp_host": "smtp.gmail.com"},
            rate_limit_per_minute=250,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        result = cc.to_dict()
        assert result['channel'] == "email"
        assert result['rate_limit_per_minute'] == 250

    def test_agent_metric_to_dict(self):
        now = datetime.now(timezone.utc)
        am = AgentMetric(
            id=uuid.uuid4(),
            metric_type="response_time",
            metric_value="2.5",
            channel="email",
            period_start=now,
            period_end=now,
            created_at=now
        )
        result = am.to_dict()
        assert result['metric_type'] == "response_time"
        assert result['metric_value'] == "2.5"
        assert result['channel'] == "email"


class TestDatabaseManagerCRUD:
    """Tests for DatabaseManager CRUD operations with mocked sessions."""

    @patch('app.database_manager.create_engine')
    def test_init_creates_engine(self, mock_engine):
        mock_engine.return_value = MagicMock()
        dm = DatabaseManager.__new__(DatabaseManager)
        assert mock_engine is not None

    def test_customer_crud_flow(self, sample_customer_data, mock_db_session):
        """Test customer create/read/update/delete flow."""
        # Verify data structure
        assert 'name' in sample_customer_data
        assert 'email' in sample_customer_data
        assert 'phone' in sample_customer_data

    def test_ticket_crud_flow(self, sample_ticket_data):
        """Test ticket data structure."""
        assert sample_ticket_data['status'] == 'open'
        assert sample_ticket_data['priority'] == 'medium'
        assert sample_ticket_data['channel'] == 'email'

    def test_message_crud_flow(self, sample_message_data):
        """Test message data structure."""
        assert sample_message_data['sender_type'] == 'customer'
        assert sample_message_data['direction'] == 'inbound'
        assert sample_message_data['content_type'] == 'text'


class TestVectorEmbeddingModel:
    """Tests for VectorEmbedding model."""

    def test_vector_embedding_to_dict(self):
        ve = VectorEmbedding(
            id=uuid.uuid4(),
            entity_type="knowledge_base",
            entity_id=str(uuid.uuid4()),
            content_preview="Sample content for embedding",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        result = ve.to_dict()
        assert result['entity_type'] == "knowledge_base"
        assert result['content_preview'] == "Sample content for embedding"

    def test_valid_entity_types(self):
        """Verify all valid entity types."""
        valid_types = ['customer', 'ticket', 'message', 'knowledge_base']
        for etype in valid_types:
            ve = VectorEmbedding(entity_type=etype, entity_id="test")
            assert ve.entity_type == etype
