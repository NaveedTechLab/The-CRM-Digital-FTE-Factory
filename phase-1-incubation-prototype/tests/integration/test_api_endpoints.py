"""
Integration tests for Phase 1 FastAPI endpoints.
Tests the /inbound/email, /inbound/whatsapp, /inbound/webform endpoints.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.main import app
from app.models.customer import Customer
from app.models.ticket import SupportTicket


class TestRootEndpoints:
    """Tests for root and health endpoints."""

    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Customer Success Digital FTE" in data["message"]

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestEmailInbound:
    """Tests for email inbound endpoint."""

    @patch('app.routes.inbound_routes.customer_success_agent')
    @patch('app.routes.inbound_routes.customer_service')
    @patch('app.routes.inbound_routes.ticket_service')
    @patch('app.routes.inbound_routes.message_normalizer')
    def test_email_inbound_new_customer(self, mock_normalizer, mock_ticket_svc, mock_customer_svc, mock_agent):
        """Test email inbound with a new customer."""
        mock_normalizer.normalize_email_message.return_value = {
            "normalized_content": "I need help with my account",
            "metadata": {"channel_specific": {"source": "email"}}
        }
        mock_customer_svc.check_customer_exists = AsyncMock(return_value=False)
        mock_customer_svc.create_customer = AsyncMock(return_value=Customer(
            name="John", email="john@example.com"
        ))
        mock_customer_svc.get_customer_context = AsyncMock(return_value={})
        mock_ticket_svc.create_ticket = AsyncMock(return_value=SupportTicket(
            customer_id="test", subject="Test", description="Test", channel="email"
        ))
        mock_agent.process_inquiry = AsyncMock(return_value={
            "response": "I can help you with that!",
            "needs_triage": False
        })

        from fastapi.testclient import TestClient
        client = TestClient(app)
        response = client.post(
            "/inbound/email",
            params={"email": "john@example.com", "name": "John", "message": "I need help"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["ticket_created"] is True
        assert "response" in data


class TestWhatsAppInbound:
    """Tests for WhatsApp inbound endpoint."""

    @patch('app.routes.inbound_routes.customer_success_agent')
    @patch('app.routes.inbound_routes.customer_service')
    @patch('app.routes.inbound_routes.ticket_service')
    @patch('app.routes.inbound_routes.message_normalizer')
    def test_whatsapp_inbound(self, mock_normalizer, mock_ticket_svc, mock_customer_svc, mock_agent):
        """Test WhatsApp inbound message processing."""
        mock_normalizer.normalize_whatsapp_message.return_value = {
            "normalized_content": "Hello need support",
            "metadata": {"channel_specific": {"source": "whatsapp"}}
        }
        mock_customer_svc.check_customer_exists = AsyncMock(return_value=False)
        mock_customer_svc.create_customer = AsyncMock(return_value=Customer(
            name="Alice", email="alice@temp-email.com", phone="+1234567890"
        ))
        mock_customer_svc.get_customer_context = AsyncMock(return_value={})
        mock_ticket_svc.create_ticket = AsyncMock(return_value=SupportTicket(
            customer_id="test", subject="WhatsApp", description="Test", channel="whatsapp"
        ))
        mock_agent.process_inquiry = AsyncMock(return_value={
            "response": "Hi! How can I help?",
            "needs_triage": False
        })

        from fastapi.testclient import TestClient
        client = TestClient(app)
        response = client.post(
            "/inbound/whatsapp",
            params={"phone": "+1234567890", "name": "Alice", "message": "Hello need support"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestWebFormInbound:
    """Tests for web form inbound endpoint."""

    @patch('app.routes.inbound_routes.customer_success_agent')
    @patch('app.routes.inbound_routes.customer_service')
    @patch('app.routes.inbound_routes.ticket_service')
    @patch('app.routes.inbound_routes.message_normalizer')
    def test_webform_inbound(self, mock_normalizer, mock_ticket_svc, mock_customer_svc, mock_agent):
        """Test web form inbound message processing."""
        mock_normalizer.normalize_webform_message.return_value = {
            "normalized_content": "Having trouble with billing",
            "metadata": {"channel_specific": {"source": "webform"}}
        }
        mock_customer_svc.check_customer_exists = AsyncMock(return_value=True)
        mock_customer_svc.get_customer_by_email = AsyncMock(return_value=Customer(
            name="Bob", email="bob@example.com"
        ))
        mock_customer_svc.update_customer = AsyncMock()
        mock_customer_svc.get_customer_context = AsyncMock(return_value={})
        mock_ticket_svc.create_ticket = AsyncMock(return_value=SupportTicket(
            customer_id="test", subject="Billing", description="Test", channel="webform"
        ))
        mock_agent.process_inquiry = AsyncMock(return_value={
            "response": "I can look into your billing issue.",
            "needs_triage": False
        })

        from fastapi.testclient import TestClient
        client = TestClient(app)
        response = client.post(
            "/inbound/webform",
            params={"email": "bob@example.com", "name": "Bob", "message": "Having trouble with billing"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["customer_exists"] is True
