"""
Integration tests for database operations.
Tests DatabaseManager with mocked PostgreSQL connection.
"""
import pytest
import uuid
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.database_manager import (
    DatabaseManager, Customer, Ticket, Message,
    CustomerIdentifier, Conversation, KnowledgeBase, ChannelConfig, AgentMetric,
    Base
)


class TestCustomerCRUDIntegration:
    """Integration tests for customer CRUD operations."""

    @patch('app.database_manager.create_engine')
    @patch('app.database_manager.Base')
    def test_create_customer_integration(self, mock_base, mock_engine, sample_customer_data):
        """Test creating a customer through DatabaseManager."""
        mock_session = MagicMock()
        mock_customer = Customer(**sample_customer_data)
        mock_customer.id = uuid.uuid4()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_customer

        with patch.object(DatabaseManager, '__init__', lambda self, *a, **kw: None):
            dm = DatabaseManager.__new__(DatabaseManager)
            dm.SessionLocal = MagicMock(return_value=mock_session)

            # Simulate create
            mock_session.add = MagicMock()
            mock_session.commit = MagicMock()
            mock_session.refresh = MagicMock()

            result = dm.create_customer(sample_customer_data)
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    @patch('app.database_manager.create_engine')
    def test_get_customer_by_email(self, mock_engine, sample_customer_data):
        """Test retrieving a customer by email."""
        mock_session = MagicMock()
        expected = Customer(**sample_customer_data)

        mock_session.query.return_value.filter.return_value.first.return_value = expected

        with patch.object(DatabaseManager, '__init__', lambda self, *a, **kw: None):
            dm = DatabaseManager.__new__(DatabaseManager)
            dm.SessionLocal = MagicMock(return_value=mock_session)

            result = dm.get_customer_by_email(sample_customer_data['email'])
            assert result.email == sample_customer_data['email']

    @patch('app.database_manager.create_engine')
    def test_update_customer(self, mock_engine, sample_customer_data):
        """Test updating a customer."""
        mock_session = MagicMock()
        existing = Customer(**sample_customer_data)
        existing.id = uuid.uuid4()
        mock_session.query.return_value.filter.return_value.first.return_value = existing

        with patch.object(DatabaseManager, '__init__', lambda self, *a, **kw: None):
            dm = DatabaseManager.__new__(DatabaseManager)
            dm.SessionLocal = MagicMock(return_value=mock_session)

            result = dm.update_customer(str(existing.id), {"name": "Updated Name"})
            mock_session.commit.assert_called_once()

    @patch('app.database_manager.create_engine')
    def test_delete_customer(self, mock_engine, sample_customer_data):
        """Test deleting a customer."""
        mock_session = MagicMock()
        existing = Customer(**sample_customer_data)
        existing.id = uuid.uuid4()
        mock_session.query.return_value.filter.return_value.first.return_value = existing

        with patch.object(DatabaseManager, '__init__', lambda self, *a, **kw: None):
            dm = DatabaseManager.__new__(DatabaseManager)
            dm.SessionLocal = MagicMock(return_value=mock_session)

            result = dm.delete_customer(str(existing.id))
            assert result is True
            mock_session.delete.assert_called_once()


class TestTicketCRUDIntegration:
    """Integration tests for ticket CRUD operations."""

    @patch('app.database_manager.create_engine')
    def test_create_and_retrieve_ticket(self, mock_engine, sample_ticket_data):
        """Test creating and retrieving a ticket."""
        mock_session = MagicMock()
        customer_id = uuid.uuid4()
        sample_ticket_data['customer_id'] = customer_id
        ticket = Ticket(**sample_ticket_data)
        ticket.id = uuid.uuid4()

        mock_session.query.return_value.filter.return_value.first.return_value = ticket

        with patch.object(DatabaseManager, '__init__', lambda self, *a, **kw: None):
            dm = DatabaseManager.__new__(DatabaseManager)
            dm.SessionLocal = MagicMock(return_value=mock_session)

            result = dm.get_ticket_by_id(str(ticket.id))
            assert result.subject == "Test Support Ticket"

    @patch('app.database_manager.create_engine')
    def test_get_tickets_by_customer(self, mock_engine):
        """Test getting all tickets for a customer."""
        mock_session = MagicMock()
        customer_id = uuid.uuid4()
        tickets = [
            Ticket(customer_id=customer_id, subject="Ticket 1", description="Desc 1"),
            Ticket(customer_id=customer_id, subject="Ticket 2", description="Desc 2")
        ]
        mock_session.query.return_value.filter.return_value.all.return_value = tickets

        with patch.object(DatabaseManager, '__init__', lambda self, *a, **kw: None):
            dm = DatabaseManager.__new__(DatabaseManager)
            dm.SessionLocal = MagicMock(return_value=mock_session)

            result = dm.get_tickets_by_customer_id(str(customer_id))
            assert len(result) == 2


class TestMessageCRUDIntegration:
    """Integration tests for message operations."""

    @patch('app.database_manager.create_engine')
    def test_create_message(self, mock_engine, sample_message_data):
        """Test creating a message."""
        mock_session = MagicMock()
        ticket_id = uuid.uuid4()
        sample_message_data['ticket_id'] = ticket_id

        with patch.object(DatabaseManager, '__init__', lambda self, *a, **kw: None):
            dm = DatabaseManager.__new__(DatabaseManager)
            dm.SessionLocal = MagicMock(return_value=mock_session)

            dm.create_message(sample_message_data)
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    @patch('app.database_manager.create_engine')
    def test_get_messages_by_ticket(self, mock_engine):
        """Test retrieving messages for a ticket."""
        mock_session = MagicMock()
        ticket_id = uuid.uuid4()
        messages = [
            Message(ticket_id=ticket_id, sender_type="customer", content="Help", direction="inbound"),
            Message(ticket_id=ticket_id, sender_type="agent", content="Sure!", direction="outbound")
        ]
        mock_session.query.return_value.filter.return_value.all.return_value = messages

        with patch.object(DatabaseManager, '__init__', lambda self, *a, **kw: None):
            dm = DatabaseManager.__new__(DatabaseManager)
            dm.SessionLocal = MagicMock(return_value=mock_session)

            result = dm.get_messages_by_ticket_id(str(ticket_id))
            assert len(result) == 2


class TestHealthCheck:
    """Integration tests for database health check."""

    @patch('app.database_manager.create_engine')
    def test_health_check_success(self, mock_engine):
        """Test successful health check."""
        mock_session = MagicMock()
        mock_session.execute.return_value.fetchone.return_value = ("PostgreSQL 16.1",)

        with patch.object(DatabaseManager, '__init__', lambda self, *a, **kw: None):
            dm = DatabaseManager.__new__(DatabaseManager)
            dm.SessionLocal = MagicMock(return_value=mock_session)

            assert dm.health_check() is True

    @patch('app.database_manager.create_engine')
    def test_health_check_failure(self, mock_engine):
        """Test failed health check."""
        mock_session = MagicMock()
        mock_session.execute.side_effect = Exception("Connection refused")

        with patch.object(DatabaseManager, '__init__', lambda self, *a, **kw: None):
            dm = DatabaseManager.__new__(DatabaseManager)
            dm.SessionLocal = MagicMock(return_value=mock_session)

            assert dm.health_check() is False
