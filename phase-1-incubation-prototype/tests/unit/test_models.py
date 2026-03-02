"""
Unit tests for Phase 1 Pydantic models.
Tests Customer, SupportTicket, and UnifiedMessage models.
"""
import pytest
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.models.customer import Customer, CustomerCreateRequest, CustomerUpdateRequest
from app.models.ticket import SupportTicket, TicketCreateRequest, TicketUpdateRequest
from app.models.message_format import UnifiedMessage, NormalizedMessageRequest, ChannelSpecificMetadata


class TestCustomerModel:
    """Tests for Customer Pydantic model."""

    def test_customer_creation(self):
        customer = Customer(name="Jane Doe", email="jane@example.com")
        assert customer.name == "Jane Doe"
        assert customer.email == "jane@example.com"
        assert customer.phone is None
        assert customer.contact_preferences == {}

    def test_customer_with_all_fields(self):
        customer = Customer(
            name="John Smith",
            email="john@example.com",
            phone="+1234567890",
            contact_preferences={"preferred_channel": "whatsapp"}
        )
        assert customer.phone == "+1234567890"
        assert customer.contact_preferences["preferred_channel"] == "whatsapp"

    def test_customer_has_timestamps(self):
        customer = Customer(name="Test", email="test@example.com")
        assert isinstance(customer.created_at, datetime)
        assert isinstance(customer.updated_at, datetime)

    def test_customer_create_request(self):
        req = CustomerCreateRequest(name="New User", email="new@example.com")
        assert req.name == "New User"
        assert req.phone is None

    def test_customer_update_request_partial(self):
        req = CustomerUpdateRequest(name="Updated Name")
        assert req.name == "Updated Name"
        assert req.phone is None
        assert req.contact_preferences is None


class TestSupportTicketModel:
    """Tests for SupportTicket Pydantic model."""

    def test_ticket_creation(self):
        ticket = SupportTicket(
            customer_id="cust-123",
            subject="Help needed",
            description="Cannot login to my account",
            channel="email"
        )
        assert ticket.customer_id == "cust-123"
        assert ticket.status == "open"
        assert ticket.priority == "medium"
        assert ticket.channel == "email"

    def test_ticket_with_priority(self):
        ticket = SupportTicket(
            customer_id="cust-456",
            subject="Urgent issue",
            description="System is down",
            channel="whatsapp",
            priority="critical"
        )
        assert ticket.priority == "critical"

    def test_ticket_defaults(self):
        ticket = SupportTicket(
            customer_id="cust-789",
            subject="General inquiry",
            description="Question about pricing",
            channel="webform"
        )
        assert ticket.assigned_to is None
        assert ticket.resolved_at is None
        assert ticket.status == "open"

    def test_ticket_create_request(self):
        req = TicketCreateRequest(
            customer_id="cust-123",
            subject="Test",
            description="Test description",
            channel="email"
        )
        assert req.priority == "medium"

    def test_ticket_update_request(self):
        req = TicketUpdateRequest(status="resolved")
        assert req.status == "resolved"
        assert req.assigned_to is None


class TestUnifiedMessageModel:
    """Tests for UnifiedMessage model."""

    def test_unified_message_creation(self):
        msg = UnifiedMessage(
            source_channel="email",
            customer_identifier="user@example.com",
            customer_name="User",
            original_content="Hello, I need help",
            normalized_content="hello i need help"
        )
        assert msg.source_channel == "email"
        assert msg.customer_identifier == "user@example.com"
        assert isinstance(msg.timestamp, datetime)

    def test_unified_message_channels(self):
        for channel in ["email", "whatsapp", "webform"]:
            msg = UnifiedMessage(
                source_channel=channel,
                customer_identifier="test",
                customer_name="Test",
                original_content="Test",
                normalized_content="test"
            )
            assert msg.source_channel == channel

    def test_normalized_message_request(self):
        req = NormalizedMessageRequest(
            source_channel="whatsapp",
            customer_identifier="+1234567890",
            customer_name="User",
            message="Help me"
        )
        assert req.source_channel == "whatsapp"
        assert req.timestamp is None

    def test_channel_specific_metadata(self):
        meta = ChannelSpecificMetadata(
            email_address="user@example.com",
            phone_number="+1234567890"
        )
        assert meta.email_address == "user@example.com"
        assert meta.phone_number == "+1234567890"
