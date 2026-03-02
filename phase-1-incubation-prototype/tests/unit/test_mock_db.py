"""
Unit tests for MockDB in-memory database.
Tests CRUD operations for customers, tickets, and interactions.
"""
import pytest
import asyncio

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.database.mock_db import MockDB
from app.models.customer import Customer
from app.models.ticket import SupportTicket


class TestMockDBCustomers:
    """Tests for MockDB customer operations."""

    @pytest.mark.asyncio
    async def test_create_customer(self, mock_db):
        customer = Customer(name="Test User", email="test@example.com")
        result = await mock_db.create_customer(customer)
        assert result.name == "Test User"
        assert result.email == "test@example.com"
        assert result.id is not None

    @pytest.mark.asyncio
    async def test_get_customer_by_email(self, mock_db):
        customer = Customer(name="Jane", email="jane@example.com")
        await mock_db.create_customer(customer)
        result = await mock_db.get_customer_by_email("jane@example.com")
        assert result is not None
        assert result.name == "Jane"

    @pytest.mark.asyncio
    async def test_get_customer_by_email_case_insensitive(self, mock_db):
        customer = Customer(name="Jane", email="Jane@Example.com")
        await mock_db.create_customer(customer)
        result = await mock_db.get_customer_by_email("jane@example.com")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_customer_by_email_not_found(self, mock_db):
        result = await mock_db.get_customer_by_email("nonexistent@example.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_customer_by_phone(self, mock_db):
        customer = Customer(name="Bob", email="bob@example.com", phone="+1234567890")
        await mock_db.create_customer(customer)
        result = await mock_db.get_customer_by_phone("+1234567890")
        assert result is not None
        assert result.name == "Bob"

    @pytest.mark.asyncio
    async def test_get_customer_by_phone_not_found(self, mock_db):
        result = await mock_db.get_customer_by_phone("+9999999999")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_customer_by_id(self, mock_db):
        customer = Customer(name="Alice", email="alice@example.com")
        created = await mock_db.create_customer(customer)
        result = await mock_db.get_customer_by_id(created.id)
        assert result is not None
        assert result.email == "alice@example.com"

    @pytest.mark.asyncio
    async def test_update_customer(self, mock_db):
        customer = Customer(name="Old Name", email="update@example.com")
        created = await mock_db.create_customer(customer)
        updated = await mock_db.update_customer(created.id, {"name": "New Name"})
        assert updated is not None
        assert updated.name == "New Name"

    @pytest.mark.asyncio
    async def test_update_customer_not_found(self, mock_db):
        result = await mock_db.update_customer("nonexistent-id", {"name": "Test"})
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_customers(self, mock_db):
        await mock_db.create_customer(Customer(name="A", email="a@example.com"))
        await mock_db.create_customer(Customer(name="B", email="b@example.com"))
        result = await mock_db.get_all_customers()
        assert len(result) == 2


class TestMockDBTickets:
    """Tests for MockDB ticket operations."""

    @pytest.mark.asyncio
    async def test_create_ticket(self, mock_db):
        ticket = SupportTicket(
            customer_id="cust-1",
            subject="Test Ticket",
            description="Test description",
            channel="email"
        )
        result = await mock_db.create_ticket(ticket)
        assert result.subject == "Test Ticket"
        assert result.id is not None

    @pytest.mark.asyncio
    async def test_get_ticket_by_id(self, mock_db):
        ticket = SupportTicket(
            customer_id="cust-1",
            subject="Lookup Ticket",
            description="For lookup test",
            channel="whatsapp"
        )
        created = await mock_db.create_ticket(ticket)
        result = await mock_db.get_ticket_by_id(created.id)
        assert result is not None
        assert result.subject == "Lookup Ticket"

    @pytest.mark.asyncio
    async def test_get_tickets_by_customer_id(self, mock_db):
        for i in range(3):
            await mock_db.create_ticket(SupportTicket(
                customer_id="cust-multi",
                subject=f"Ticket {i}",
                description=f"Desc {i}",
                channel="webform"
            ))
        results = await mock_db.get_tickets_by_customer_id("cust-multi")
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_update_ticket(self, mock_db):
        ticket = SupportTicket(
            customer_id="cust-1",
            subject="Update Test",
            description="To be updated",
            channel="email"
        )
        created = await mock_db.create_ticket(ticket)
        updated = await mock_db.update_ticket(created.id, {"status": "resolved"})
        assert updated.status == "resolved"

    @pytest.mark.asyncio
    async def test_get_all_tickets(self, mock_db):
        await mock_db.create_ticket(SupportTicket(
            customer_id="c1", subject="T1", description="D1", channel="email"
        ))
        await mock_db.create_ticket(SupportTicket(
            customer_id="c2", subject="T2", description="D2", channel="whatsapp"
        ))
        result = await mock_db.get_all_tickets()
        assert len(result) == 2


class TestMockDBInteractions:
    """Tests for MockDB interaction logging."""

    @pytest.mark.asyncio
    async def test_add_interaction(self, mock_db):
        interaction = {
            "ticket_id": "ticket-1",
            "sender_type": "customer",
            "content": "Hello, I need help"
        }
        result = await mock_db.add_interaction(interaction)
        assert result['id'] is not None
        assert result['timestamp'] is not None

    @pytest.mark.asyncio
    async def test_get_interactions_by_ticket(self, mock_db):
        for i in range(3):
            await mock_db.add_interaction({
                "ticket_id": "ticket-interactions",
                "sender_type": "customer" if i % 2 == 0 else "agent",
                "content": f"Message {i}"
            })
        results = await mock_db.get_interactions_by_ticket_id("ticket-interactions")
        assert len(results) == 3
