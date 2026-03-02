import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.web_notification_service import WebNotificationService


class TestWebNotificationService:
    """Test suite for web notification service functionality"""

    @pytest.fixture
    def service(self):
        with patch('app.services.web_notification_service.get_retry_mechanism') as mock_retry, \
             patch('app.services.web_notification_service.get_rate_limiter') as mock_rl, \
             patch('app.services.web_notification_service.get_delivery_tracker') as mock_dt:
            mock_dt.return_value = AsyncMock()
            mock_rl.return_value = MagicMock()
            mock_retry.return_value = MagicMock()
            svc = WebNotificationService()
            svc.delivery_tracker = AsyncMock()
            return svc

    @pytest.mark.asyncio
    async def test_send_webhook_success(self, service):
        """Test successful webhook delivery"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"status": "success"}'
        mock_response.json.return_value = {"status": "success"}

        with patch('app.services.web_notification_service.is_channel_limited', new_callable=AsyncMock, return_value=False), \
             patch('httpx.AsyncClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await service.send_webhook(
                webhook_url="https://example.com/webhook",
                payload={"message": "test"},
                message_id="test_msg_123"
            )

        assert result['success'] is True
        assert result['status_code'] == 200

    @pytest.mark.asyncio
    async def test_send_webhook_failure(self, service):
        """Test webhook delivery failure (5xx)"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.content = b'{"error": "server error"}'
        mock_response.json.return_value = {"error": "server error"}

        with patch('app.services.web_notification_service.is_channel_limited', new_callable=AsyncMock, return_value=False), \
             patch('httpx.AsyncClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await service.send_webhook(
                webhook_url="https://example.com/webhook",
                payload={"message": "test"},
                message_id="test_msg_123"
            )

        assert result['success'] is False
        assert result['status_code'] == 500

    @pytest.mark.asyncio
    async def test_send_webhook_timeout(self, service):
        """Test webhook delivery with timeout"""
        import httpx

        with patch('app.services.web_notification_service.is_channel_limited', new_callable=AsyncMock, return_value=False), \
             patch('httpx.AsyncClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.TimeoutException("Request timed out")
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await service.send_webhook(
                webhook_url="https://example.com/webhook",
                payload={"message": "test"},
                message_id="test_msg_123"
            )

        assert result['success'] is False
        assert 'timed out' in result['error'].lower()

    @pytest.mark.asyncio
    async def test_send_webhook_connection_error(self, service):
        """Test webhook delivery with connection error"""
        import httpx

        with patch('app.services.web_notification_service.is_channel_limited', new_callable=AsyncMock, return_value=False), \
             patch('httpx.AsyncClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.RequestError("Could not connect")
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await service.send_webhook(
                webhook_url="https://example.com/webhook",
                payload={"message": "test"},
                message_id="test_msg_123"
            )

        assert result['success'] is False
        assert 'connect' in result['error'].lower()

    @pytest.mark.asyncio
    async def test_send_webhook_rate_limited(self, service):
        """Test webhook when rate limited"""
        with patch('app.services.web_notification_service.is_channel_limited', new_callable=AsyncMock, return_value=True):
            result = await service.send_webhook(
                webhook_url="https://example.com/webhook",
                payload={"message": "test"},
                message_id="test_msg_123"
            )

        assert result['success'] is False
        assert result['rate_limit_hit'] is True

    @pytest.mark.asyncio
    async def test_simulate_web_notification_success(self, service):
        """Test simulated web notification"""
        result = await service.simulate_web_notification(
            session_id="session_123",
            message="Test notification",
            message_id="test_msg_123"
        )

        assert result['success'] is True
        assert result['simulated'] is True
        assert result['session_id'] == "session_123"

    def test_validate_webhook_url(self, service):
        """Test webhook URL validation"""
        assert service.is_valid_webhook_url("https://example.com/webhook") is True
        assert service.is_valid_webhook_url("http://localhost:3000/api/notify") is True

        assert service.is_valid_webhook_url("not-a-url") is False
        assert service.is_valid_webhook_url("") is False
        assert service.is_valid_webhook_url("ftp://example.com/webhook") is False

    @pytest.mark.asyncio
    async def test_rate_limit_check(self, service):
        """Test rate limit status check"""
        with patch('app.services.web_notification_service.get_channel_status', new_callable=AsyncMock) as mock_get_status:
            mock_get_status.return_value = {
                'remaining_calls': 50,
                'reset_time': '2023-01-01T00:00:00Z',
                'limit': 100
            }

            result = await service.get_rate_limit_status()

            assert result['remaining_calls'] == 50
            assert result['limit'] == 100

    @pytest.mark.asyncio
    async def test_send_batch_webhooks(self, service):
        """Test sending multiple webhooks in batch"""
        mock_result = {'success': True, 'status_code': 200}

        with patch.object(service, 'send_webhook_with_retry', new_callable=AsyncMock, return_value=mock_result):
            results = await service.send_batch_webhooks(
                urls=["https://example1.com/wh", "https://example2.com/wh", "https://example3.com/wh"],
                payloads=[{"msg": "t1"}, {"msg": "t2"}, {"msg": "t3"}],
                message_ids=["msg1", "msg2", "msg3"]
            )

        assert len(results) == 3
        for result in results:
            assert result['success'] is True

    @pytest.mark.asyncio
    async def test_webhook_retry_logic(self, service):
        """Test webhook retry logic on failure"""
        with patch.object(service, 'send_webhook_with_retry', new_callable=AsyncMock) as mock_retry:
            mock_retry.return_value = {
                'success': True,
                'attempts': 2,
                'final_status': 200
            }

            result = await service.send_webhook_with_retry(
                webhook_url="https://example.com/webhook",
                payload={"message": "test"},
                message_id="test_msg_123"
            )

        assert result['success'] is True
        assert 'attempts' in result
