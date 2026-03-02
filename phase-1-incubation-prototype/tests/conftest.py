"""
Shared test fixtures for Phase 1 Incubation Prototype tests.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import app
from app.database.mock_db import MockDB
from app.models.customer import Customer
from app.models.ticket import SupportTicket


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Fresh MockDB instance for each test."""
    return MockDB()


@pytest.fixture
def sample_customer():
    """Sample customer for testing."""
    return Customer(
        name="John Doe",
        email="john@example.com",
        phone="+1234567890",
        contact_preferences={"preferred_channel": "email"}
    )


@pytest.fixture
def sample_ticket():
    """Sample ticket for testing."""
    return SupportTicket(
        customer_id="test-customer-id",
        subject="Test Ticket",
        description="I need help with my account",
        channel="email",
        priority="medium"
    )
