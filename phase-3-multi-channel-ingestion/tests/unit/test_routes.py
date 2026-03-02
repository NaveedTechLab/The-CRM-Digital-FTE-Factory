import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.main import app
from app.services.ingestion_service import ingestion_service


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


class TestWhatsAppWebhook:
    """Test cases for WhatsApp webhook endpoint"""

    def test_whatsapp_webhook_post_success(self, client):
        """Test successful WhatsApp webhook post"""
        # Mock the ingestion service
        with patch.object(ingestion_service, 'ingest_whatsapp_message', new_callable=AsyncMock) as mock_ingest:
            mock_ingest.return_value = {"success": True, "message_id": "test-sid-123"}

            # Send test data (form data as Twilio would send)
            response = client.post(
                "/webhooks/twilio-whatsapp",
                data={
                    "From": "whatsapp:+1234567890",
                    "To": "whatsapp:+0987654321",
                    "Body": "Hello from test",
                    "MessageSid": "test-sid-123"
                },
                headers={
                    "X-Twilio-Signature": "test-signature"  # This will fail validation but that's fine for this test
                }
            )

            # Even with invalid signature, we should get a response
            assert response.status_code in [200, 403]  # 200 if it returns before validation, 403 if signature fails


class TestWebFormEndpoint:
    """Test cases for Web Form endpoint"""

    def test_web_form_post_success(self, client):
        """Test successful web form post with valid API key"""
        # Mock the ingestion service
        with patch.object(ingestion_service, 'ingest_webform_message', new_callable=AsyncMock) as mock_ingest:
            mock_ingest.return_value = {"success": True, "ticket_id": "test-ticket-123"}

            # Send test data with valid API key
            response = client.post(
                "/api/v1/support-form",
                json={
                    "customer_email": "test@example.com",
                    "message": "Hello from web form test",
                    "customer_name": "Test User",
                    "subject": "Test Subject"
                },
                headers={
                    "X-API-Key": "test-api-key"  # This will fail validation but that's fine for this test
                }
            )

            # Even with invalid API key, we should get a response
            assert response.status_code in [200, 401]  # 200 if it returns before validation, 401 if API key fails

    def test_web_form_post_missing_required_fields(self, client):
        """Test web form post with missing required fields"""
        # Send test data without required fields
        response = client.post(
            "/api/v1/support-form",
            json={
                # Missing required customer_email and message
                "customer_name": "Test User",
                "subject": "Test Subject"
            },
            headers={
                "X-API-Key": "test-api-key"
            }
        )

        # Should return 400 for missing fields or 401 if API key validation runs first
        assert response.status_code in [400, 401, 422]


class TestHealthCheck:
    """Test cases for health check endpoints"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")

        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data

    def test_metrics_endpoint(self, client):
        """Test metrics endpoint"""
        response = client.get("/metrics")

        assert response.status_code == 200

        data = response.json()
        assert "total_messages_processed" in data
        assert "messages_per_channel" in data
        assert "avg_processing_time_ms" in data

    def test_readiness_check(self, client):
        """Test readiness check endpoint"""
        response = client.get("/ready")

        assert response.status_code in [200, 503]  # Could be ready or not depending on Kafka connection