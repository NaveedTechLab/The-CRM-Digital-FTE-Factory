import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.response_dispatcher import ResponseDispatcher
from app.models.outbound_message import OutboundMessage


class TestMultiChannelDelivery:
    """Integration test suite for multi-channel delivery functionality"""

    @pytest.fixture
    def dispatcher(self):
        return ResponseDispatcher()

    @pytest.mark.asyncio
    async def test_gmail_delivery_integration(self, dispatcher):
        """Integration test for Gmail delivery end-to-end"""
        message = OutboundMessage(
            message_id="test_gmail_msg_123",
            conversation_id="test_conv_123",
            content="Test content for Gmail delivery",
            channel_destination="gmail",
            recipient_identifier="test@example.com"
        )

        # Mock the actual delivery service call
        with patch('app.services.response_dispatcher.send_email') as mock_send:
            mock_send.return_value = {'success': True, 'message_id': 'sent_msg_123'}

            # Mock the delivery tracker
            with patch.object(dispatcher.delivery_tracker, 'update_delivery_status', return_value=AsyncMock()):
                result = await dispatcher.route_message(message)

        assert result is True
        mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_whatsapp_delivery_integration(self, dispatcher):
        """Integration test for WhatsApp delivery end-to-end"""
        message = OutboundMessage(
            message_id="test_wa_msg_456",
            conversation_id="test_conv_456",
            content="Test content for WhatsApp delivery",
            channel_destination="whatsapp",
            recipient_identifier="whatsapp:+1234567890"
        )

        # Mock the actual delivery service call
        with patch('app.services.response_dispatcher.send_whatsapp_message') as mock_send:
            mock_send.return_value = {'success': True, 'message_sid': 'SM1234567890'}

            # Mock the delivery tracker
            with patch.object(dispatcher.delivery_tracker, 'update_delivery_status', return_value=AsyncMock()):
                result = await dispatcher.route_message(message)

        assert result is True
        mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_webform_delivery_integration(self, dispatcher):
        """Integration test for Webform delivery end-to-end"""
        message = OutboundMessage(
            message_id="test_wf_msg_789",
            conversation_id="test_conv_789",
            content="Test content for Webform delivery",
            channel_destination="webform",
            recipient_identifier="https://example.com/webhook"
        )

        # Mock the actual delivery service call
        with patch('app.services.response_dispatcher.send_webhook') as mock_send:
            mock_send.return_value = {'success': True, 'status_code': 200}

            # Mock the delivery tracker
            with patch.object(dispatcher.delivery_tracker, 'update_delivery_status', return_value=AsyncMock()):
                result = await dispatcher.route_message(message)

        assert result is True
        mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_cross_channel_routing_integration(self, dispatcher):
        """Integration test for routing messages across all channels"""
        messages = [
            OutboundMessage(
                message_id="test_msg_gmail",
                conversation_id="test_conv_multi",
                content="Test Gmail content",
                channel_destination="gmail",
                recipient_identifier="test@example.com"
            ),
            OutboundMessage(
                message_id="test_msg_wa",
                conversation_id="test_conv_multi",
                content="Test WhatsApp content",
                channel_destination="whatsapp",
                recipient_identifier="whatsapp:+1234567890"
            ),
            OutboundMessage(
                message_id="test_msg_wf",
                conversation_id="test_conv_multi",
                content="Test Webform content",
                channel_destination="webform",
                recipient_identifier="https://example.com/webhook"
            )
        ]

        # Mock all delivery services
        with patch('app.services.response_dispatcher.send_email', return_value={'success': True}):
            with patch('app.services.response_dispatcher.send_whatsapp_message', return_value={'success': True}):
                with patch('app.services.response_dispatcher.send_webhook', return_value={'success': True}):
                    # Mock the delivery tracker
                    with patch.object(dispatcher.delivery_tracker, 'update_delivery_status', return_value=AsyncMock()):
                        results = []
                        for message in messages:
                            result = await dispatcher.route_message(message)
                            results.append(result)

        # All should succeed
        assert all(results)

    @pytest.mark.asyncio
    async def test_concurrent_multi_channel_delivery(self, dispatcher):
        """Integration test for concurrent delivery across channels"""
        messages = [
            (OutboundMessage(
                message_id="concurrent_msg_1",
                conversation_id="test_conv_concurrent",
                content="Concurrent Gmail content",
                channel_destination="gmail",
                recipient_identifier="test1@example.com"
            ), "gmail"),
            (OutboundMessage(
                message_id="concurrent_msg_2",
                conversation_id="test_conv_concurrent",
                content="Concurrent WhatsApp content",
                channel_destination="whatsapp",
                recipient_identifier="whatsapp:+1234567890"
            ), "whatsapp"),
            (OutboundMessage(
                message_id="concurrent_msg_3",
                conversation_id="test_conv_concurrent",
                content="Concurrent Webform content",
                channel_destination="webform",
                recipient_identifier="https://example.com/webhook"
            ), "webform")
        ]

        # Mock delivery services to simulate concurrent behavior
        async def mock_delivery(message, channel):
            if channel == "gmail":
                with patch('app.services.response_dispatcher.send_email', return_value={'success': True}):
                    with patch.object(dispatcher.delivery_tracker, 'update_delivery_status', return_value=AsyncMock()):
                        return await dispatcher.route_message(message)
            elif channel == "whatsapp":
                with patch('app.services.response_dispatcher.send_whatsapp_message', return_value={'success': True}):
                    with patch.object(dispatcher.delivery_tracker, 'update_delivery_status', return_value=AsyncMock()):
                        return await dispatcher.route_message(message)
            elif channel == "webform":
                with patch('app.services.response_dispatcher.send_webhook', return_value={'success': True}):
                    with patch.object(dispatcher.delivery_tracker, 'update_delivery_status', return_value=AsyncMock()):
                        return await dispatcher.route_message(message)

        # Run concurrently
        tasks = [mock_delivery(msg, ch) for msg, ch in messages]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(results)

    @pytest.mark.asyncio
    async def test_delivery_status_tracking_integration(self, dispatcher):
        """Integration test for delivery status tracking across channels"""
        message = OutboundMessage(
            message_id="tracking_msg_123",
            conversation_id="test_conv_tracking",
            content="Test content for tracking",
            channel_destination="gmail",
            recipient_identifier="test@example.com"
        )

        # Mock successful delivery
        with patch('app.services.response_dispatcher.send_email', return_value={'success': True}):
            # Mock the delivery tracker to verify status updates
            with patch.object(dispatcher.delivery_tracker, 'update_delivery_status', return_value=AsyncMock()) as mock_update:
                result = await dispatcher.route_message(message)

        assert result is True
        # Verify that status was updated to 'delivered'
        mock_update.assert_called_with(message.message_id, 'delivered')

    @pytest.mark.asyncio
    async def test_rate_limiting_integration(self, dispatcher):
        """Integration test for rate limiting across channels"""
        message = OutboundMessage(
            message_id="rate_limit_msg_123",
            conversation_id="test_conv_rate",
            content="Test content for rate limiting",
            channel_destination="gmail",
            recipient_identifier="test@example.com"
        )

        # Mock rate limited scenario
        with patch('app.services.response_dispatcher.is_channel_limited', return_value=AsyncMock(return_value=True)):
            result = await dispatcher.route_message(message)

        # Should fail due to rate limiting
        assert result is False

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, dispatcher):
        """Integration test for error handling across channels"""
        message = OutboundMessage(
            message_id="error_msg_123",
            conversation_id="test_conv_error",
            content="Test content for error handling",
            channel_destination="gmail",
            recipient_identifier="test@example.com"
        )

        # Mock delivery failure
        with patch('app.services.response_dispatcher.send_email', return_value={'success': False, 'error': 'Delivery failed'}):
            with patch.object(dispatcher, 'handle_delivery_failure', return_value=AsyncMock()):
                result = await dispatcher.route_message(message)

        # Should still complete (failure is handled internally)
        assert result is not None

    @pytest.mark.asyncio
    async def test_message_processing_flow_integration(self, dispatcher):
        """Integration test for complete message processing flow"""
        message_data = {
            'message_id': 'flow_test_msg_123',
            'conversation_id': 'flow_test_conv_123',
            'content': 'Test content for flow',
            'channel_destination': 'gmail',
            'recipient_identifier': 'test@example.com',
            'sender_identifier': 'integration_tester'
        }

        # Mock the complete flow
        with patch.object(dispatcher, '_create_outbound_message') as mock_create:
            mock_message = OutboundMessage(
                message_id="flow_test_msg_123",
                conversation_id="flow_test_conv_123",
                content="Test content for flow",
                channel_destination="gmail",
                recipient_identifier="test@example.com"
            )
            mock_create.return_value = mock_message

            with patch.object(dispatcher, 'route_message', return_value=AsyncMock(return_value=True)):
                with patch.object(dispatcher.delivery_tracker, 'update_delivery_status', return_value=AsyncMock()):
                    await dispatcher.process_message(message_data)

        # Verify that the flow completed without errors
        mock_create.assert_called_once()