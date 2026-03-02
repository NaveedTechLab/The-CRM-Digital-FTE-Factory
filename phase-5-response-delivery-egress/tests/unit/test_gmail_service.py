import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.gmail_service import GmailService


class TestGmailService:
    """Test suite for Gmail service functionality"""

    @pytest.fixture
    def gmail_service(self):
        with patch('app.services.gmail_service.get_retry_mechanism') as mock_retry, \
             patch('app.services.gmail_service.get_rate_limiter') as mock_rl, \
             patch('app.services.gmail_service.get_delivery_tracker') as mock_dt:
            mock_dt.return_value = AsyncMock()
            mock_rl.return_value = MagicMock()
            mock_retry.return_value = MagicMock()
            service = GmailService()
            service.delivery_tracker = AsyncMock()
            service.sender_email = "test@techcorp.com"

            # Mock the Gmail API service chain
            mock_send = MagicMock()
            mock_send.execute.return_value = {'id': 'gmail_msg_123', 'threadId': 'thread_456'}
            mock_messages = MagicMock()
            mock_messages.send.return_value = mock_send
            mock_users = MagicMock()
            mock_users.messages.return_value = mock_messages
            mock_service = MagicMock()
            mock_service.users.return_value = mock_users
            service.service = mock_service

            return service

    @pytest.mark.asyncio
    async def test_send_email_success(self, gmail_service):
        """Test successful email sending"""
        with patch('app.services.gmail_service.is_channel_limited', new_callable=AsyncMock, return_value=False):
            result = await gmail_service.send_email(
                to="test@example.com",
                subject="Test Subject",
                body="Test Body",
                message_id="test_msg_123"
            )

        assert result['success'] is True
        assert result['message_id'] == 'gmail_msg_123'
        assert result['thread_id'] == 'thread_456'

    @pytest.mark.asyncio
    async def test_send_email_with_threading(self, gmail_service):
        """Test email sending with threading headers"""
        with patch('app.services.gmail_service.is_channel_limited', new_callable=AsyncMock, return_value=False):
            result = await gmail_service.send_email(
                to="test@example.com",
                subject="Test Subject",
                body="Test Body",
                in_reply_to="original_msg_id",
                references="original_refs",
                message_id="test_msg_123"
            )

        assert result['success'] is True

    @pytest.mark.asyncio
    async def test_send_email_rate_limited(self, gmail_service):
        """Test email sending when rate limited"""
        with patch('app.services.gmail_service.is_channel_limited', new_callable=AsyncMock, return_value=True):
            result = await gmail_service.send_email(
                to="test@example.com",
                subject="Test Subject",
                body="Test Body",
                message_id="test_msg_123"
            )

        assert result['success'] is False
        assert result['rate_limit_hit'] is True

    @pytest.mark.asyncio
    async def test_send_email_api_error(self, gmail_service):
        """Test email sending with API error"""
        gmail_service.service.users.return_value.messages.return_value.send.return_value.execute.side_effect = Exception("API Error")

        with patch('app.services.gmail_service.is_channel_limited', new_callable=AsyncMock, return_value=False):
            result = await gmail_service.send_email(
                to="test@example.com",
                subject="Test Subject",
                body="Test Body",
                message_id="test_msg_123"
            )

        assert result['success'] is False
        assert 'error' in result

    @pytest.mark.asyncio
    async def test_send_email_not_initialized(self, gmail_service):
        """Test email sending when service not initialized"""
        gmail_service.service = None

        with patch('app.services.gmail_service.is_channel_limited', new_callable=AsyncMock, return_value=False):
            result = await gmail_service.send_email(
                to="test@example.com",
                subject="Test Subject",
                body="Test Body",
                message_id="test_msg_123"
            )

        assert result['success'] is False
        assert 'not initialized' in result['error']

    def test_is_valid_email(self, gmail_service):
        """Test email validation"""
        assert gmail_service.is_valid_email("test@example.com") is True
        assert gmail_service.is_valid_email("user.name+tag@domain.co") is True

        assert gmail_service.is_valid_email("invalid") is False
        assert gmail_service.is_valid_email("@example.com") is False
        assert gmail_service.is_valid_email("test@") is False

    @pytest.mark.asyncio
    async def test_rate_limit_status(self, gmail_service):
        """Test rate limit status check"""
        with patch('app.services.gmail_service.get_channel_status', new_callable=AsyncMock) as mock_status:
            mock_status.return_value = {'remaining_calls': 50, 'limit': 100}

            result = await gmail_service.get_rate_limit_status()

            assert result['remaining_calls'] == 50
