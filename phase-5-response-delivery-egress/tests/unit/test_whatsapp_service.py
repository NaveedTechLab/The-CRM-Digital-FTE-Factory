import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from app.services.whatsapp_service import WhatsAppService


class TestWhatsAppService:
    """Test suite for WhatsApp service with Meta -> Twilio -> Store fallback chain"""

    @pytest.fixture
    def whatsapp_service(self):
        with patch('app.services.whatsapp_service.get_retry_mechanism') as mock_retry, \
             patch('app.services.whatsapp_service.get_rate_limiter') as mock_rl, \
             patch('app.services.whatsapp_service.get_delivery_tracker') as mock_dt:
            mock_dt.return_value = AsyncMock()
            mock_rl.return_value = MagicMock()
            mock_retry.return_value = MagicMock()
            service = WhatsAppService()
            service.delivery_tracker = AsyncMock()
            return service

    # ------------------------------------------------------------------
    # Phone number normalization
    # ------------------------------------------------------------------

    def test_normalize_whatsapp_prefix(self, whatsapp_service):
        assert whatsapp_service._normalize_phone_number("whatsapp:+923132303222") == "923132303222"

    def test_normalize_plus_prefix(self, whatsapp_service):
        assert whatsapp_service._normalize_phone_number("+923132303222") == "923132303222"

    def test_normalize_raw_international(self, whatsapp_service):
        assert whatsapp_service._normalize_phone_number("923132303222") == "923132303222"

    def test_normalize_pakistani_local(self, whatsapp_service):
        """Pakistani local 03xx -> 923xx"""
        assert whatsapp_service._normalize_phone_number("03132303222") == "923132303222"

    def test_normalize_non_pakistani(self, whatsapp_service):
        assert whatsapp_service._normalize_phone_number("+14155238886") == "14155238886"

    # ------------------------------------------------------------------
    # Number validation
    # ------------------------------------------------------------------

    def test_valid_whatsapp_number(self, whatsapp_service):
        assert whatsapp_service.is_valid_whatsapp_number("+1234567890") is True
        assert whatsapp_service.is_valid_whatsapp_number("whatsapp:+923132303222") is True
        assert whatsapp_service.is_valid_whatsapp_number("03132303222") is True

    def test_invalid_whatsapp_number(self, whatsapp_service):
        assert whatsapp_service.is_valid_whatsapp_number("invalid") is False
        assert whatsapp_service.is_valid_whatsapp_number("12345") is False
        assert whatsapp_service.is_valid_whatsapp_number("+") is False

    # ------------------------------------------------------------------
    # Meta API delivery
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_send_via_meta_success(self, whatsapp_service):
        """Test successful delivery via Meta Cloud API"""
        whatsapp_service.meta_initialized = True
        whatsapp_service.access_token = "test_token"
        whatsapp_service.phone_number_id = "123456"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messages": [{"id": "wamid.test123"}]
        }

        with patch('httpx.AsyncClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await whatsapp_service._send_via_meta("923132303222", "Hello!", "msg_1", 1)

        assert result['success'] is True
        assert result['method'] == 'meta'
        assert result['message_id'] == "wamid.test123"

    @pytest.mark.asyncio
    async def test_send_via_meta_test_mode_error(self, whatsapp_service):
        """Test Meta API returns test-mode error for unregistered number"""
        whatsapp_service.meta_initialized = True
        whatsapp_service.access_token = "test_token"
        whatsapp_service.phone_number_id = "123456"

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "error"
        mock_response.json.return_value = {
            "error": {
                "message": "Recipient phone number not a valid whatsapp phone",
                "code": 131030
            }
        }

        with patch('httpx.AsyncClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await whatsapp_service._send_via_meta("921234567890", "Hello!", "msg_2", 1)

        assert result['success'] is False
        assert result['is_test_mode_error'] is True
        assert result['method'] == 'meta'

    @pytest.mark.asyncio
    async def test_send_via_meta_not_initialized(self, whatsapp_service):
        """Test Meta API when not initialized"""
        whatsapp_service.meta_initialized = False
        result = await whatsapp_service._send_via_meta("923132303222", "Hello!", "msg_3", 1)
        assert result['success'] is False
        assert 'not initialized' in result['error']

    # ------------------------------------------------------------------
    # Twilio fallback delivery
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_send_via_twilio_success(self, whatsapp_service):
        """Test successful delivery via Twilio fallback"""
        whatsapp_service.twilio_initialized = True
        mock_twilio = MagicMock()
        mock_message = MagicMock()
        mock_message.sid = "SM1234567890"
        mock_message.status = "queued"
        mock_twilio.messages.create.return_value = mock_message
        whatsapp_service.twilio_client = mock_twilio

        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.time.side_effect = [0.0, 0.5]
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=mock_message)

            result = await whatsapp_service._send_via_twilio("923132303222", "Hello!", "msg_4", 1)

        assert result['success'] is True
        assert result['method'] == 'twilio'
        assert result['message_id'] == "SM1234567890"

    @pytest.mark.asyncio
    async def test_send_via_twilio_not_initialized(self, whatsapp_service):
        """Test Twilio when not initialized"""
        whatsapp_service.twilio_initialized = False
        result = await whatsapp_service._send_via_twilio("923132303222", "Hello!", "msg_5", 1)
        assert result['success'] is False
        assert 'not initialized' in result['error']

    # ------------------------------------------------------------------
    # Fallback chain (Meta -> Twilio -> Store)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_send_message_meta_success_no_fallback(self, whatsapp_service):
        """If Meta succeeds, Twilio should not be called"""
        with patch('app.services.whatsapp_service.is_channel_limited', new_callable=AsyncMock, return_value=False), \
             patch.object(whatsapp_service, '_send_via_meta', new_callable=AsyncMock) as mock_meta, \
             patch.object(whatsapp_service, '_send_via_twilio', new_callable=AsyncMock) as mock_twilio:

            mock_meta.return_value = {'success': True, 'method': 'meta', 'message_id': 'wamid.ok'}

            result = await whatsapp_service.send_message(
                to="whatsapp:+923132303222",
                message_body="Test message",
                message_id="test_msg_100"
            )

        assert result['success'] is True
        assert result['method'] == 'meta'
        mock_twilio.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_message_meta_fails_twilio_succeeds(self, whatsapp_service):
        """If Meta fails, should fall back to Twilio"""
        with patch('app.services.whatsapp_service.is_channel_limited', new_callable=AsyncMock, return_value=False), \
             patch.object(whatsapp_service, '_send_via_meta', new_callable=AsyncMock) as mock_meta, \
             patch.object(whatsapp_service, '_send_via_twilio', new_callable=AsyncMock) as mock_twilio:

            mock_meta.return_value = {'success': False, 'error': 'test mode', 'method': 'meta'}
            mock_twilio.return_value = {'success': True, 'method': 'twilio', 'message_id': 'SM123'}

            result = await whatsapp_service.send_message(
                to="+921234567890",
                message_body="Test message",
                message_id="test_msg_101"
            )

        assert result['success'] is True
        assert result['method'] == 'twilio'

    @pytest.mark.asyncio
    async def test_send_message_both_fail_stores_response(self, whatsapp_service):
        """If both Meta and Twilio fail, response is stored for retrieval"""
        with patch('app.services.whatsapp_service.is_channel_limited', new_callable=AsyncMock, return_value=False), \
             patch.object(whatsapp_service, '_send_via_meta', new_callable=AsyncMock) as mock_meta, \
             patch.object(whatsapp_service, '_send_via_twilio', new_callable=AsyncMock) as mock_twilio:

            mock_meta.return_value = {'success': False, 'error': 'test mode', 'method': 'meta'}
            mock_twilio.return_value = {'success': False, 'error': 'sandbox not joined', 'method': 'twilio'}

            result = await whatsapp_service.send_message(
                to="03003627458",
                message_body="Stored message",
                message_id="test_msg_102"
            )

        assert result['success'] is False
        assert result['stored_for_retrieval'] is True
        # Verify the message is stored
        pending = whatsapp_service.get_pending_responses("03003627458")
        assert len(pending) == 1
        assert pending[0]['content'] == "Stored message"

    @pytest.mark.asyncio
    async def test_rate_limit_blocks_send(self, whatsapp_service):
        """Rate limited messages should not attempt delivery"""
        with patch('app.services.whatsapp_service.is_channel_limited', new_callable=AsyncMock, return_value=True):
            result = await whatsapp_service.send_message(
                to="+923132303222",
                message_body="Test",
                message_id="test_msg_103"
            )

        assert result['success'] is False
        assert result.get('rate_limit_hit') is True

    # ------------------------------------------------------------------
    # Pending response storage
    # ------------------------------------------------------------------

    def test_store_and_retrieve_pending(self, whatsapp_service):
        """Test storing and retrieving pending responses"""
        whatsapp_service._store_pending_response("923132303222", "Hello!", "msg_a")
        whatsapp_service._store_pending_response("923132303222", "Follow-up", "msg_b")

        pending = whatsapp_service.get_pending_responses("923132303222")
        assert len(pending) == 2
        assert pending[0]['content'] == "Hello!"
        assert pending[1]['content'] == "Follow-up"

    def test_clear_pending_responses(self, whatsapp_service):
        """Test clearing pending responses"""
        whatsapp_service._store_pending_response("923132303222", "Hello!", "msg_c")
        whatsapp_service.clear_pending_responses("923132303222")
        pending = whatsapp_service.get_pending_responses("923132303222")
        assert len(pending) == 0

    def test_pending_responses_normalized(self, whatsapp_service):
        """Pending responses retrieved with different number formats"""
        whatsapp_service._store_pending_response("923132303222", "Hello!", "msg_d")
        # Retrieve using local Pakistani format
        pending = whatsapp_service.get_pending_responses("03132303222")
        assert len(pending) == 1

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_initialize_neither_configured(self):
        """Both Meta and Twilio unconfigured returns False"""
        with patch('app.services.whatsapp_service.get_retry_mechanism'), \
             patch('app.services.whatsapp_service.get_rate_limiter'), \
             patch('app.services.whatsapp_service.get_delivery_tracker'):
            service = WhatsAppService()
            service.access_token = None
            service.phone_number_id = None
            service.twilio_account_sid = None
            service.twilio_auth_token = None
            service.twilio_whatsapp_number = None

            result = await service.initialize()
            assert result is False

    @pytest.mark.asyncio
    async def test_initialize_meta_only(self):
        """Meta configured, Twilio not -> should still return True"""
        with patch('app.services.whatsapp_service.get_retry_mechanism'), \
             patch('app.services.whatsapp_service.get_rate_limiter'), \
             patch('app.services.whatsapp_service.get_delivery_tracker'):
            service = WhatsAppService()
            service.access_token = "test_token"
            service.phone_number_id = "123456"
            service.twilio_account_sid = None
            service.twilio_auth_token = None
            service.twilio_whatsapp_number = None

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"display_phone_number": "+1234567890"}

            with patch('httpx.AsyncClient') as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.get.return_value = mock_response
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client_cls.return_value = mock_client

                result = await service.initialize()

            assert result is True
            assert service.meta_initialized is True
            assert service.twilio_initialized is False
