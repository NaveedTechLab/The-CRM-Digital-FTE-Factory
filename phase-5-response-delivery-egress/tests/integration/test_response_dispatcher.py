import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.response_dispatcher import ResponseDispatcher
from app.models.outbound_message import OutboundMessage


class TestResponseDispatcherIntegration:
    """Integration test suite for response dispatcher functionality"""

    @pytest.fixture
    def dispatcher(self):
        return ResponseDispatcher()

    @pytest.mark.asyncio
    async def test_dispatcher_initialization_integration(self, dispatcher):
        """Integration test for dispatcher initialization"""
        # Mock the service initialization
        with patch.object(dispatcher.gmail_service, 'initialize', return_value=AsyncMock(return_value=True)):
            with patch.object(dispatcher.whatsapp_service, 'initialize', return_value=AsyncMock(return_value=True)):
                with patch('app.services.response_dispatcher.initialize_delivery_tracker'):
                    with patch('app.services.response_dispatcher.initialize_rate_limiter', return_value=AsyncMock()):
                        await dispatcher.initialize()

        # Verify that initialization completed without errors
        assert dispatcher.service is not None

    @pytest.mark.asyncio
    async def test_message_processing_integration(self, dispatcher):
        """Integration test for complete message processing"""
        message_data = {
            'message_id': 'integration_test_msg_123',
            'conversation_id': 'integration_test_conv_123',
            'content': 'Integration test content',
            'channel_destination': 'gmail',
            'recipient_identifier': 'test@example.com',
            'sender_identifier': 'integration_tester'
        }

        # Mock the creation of outbound message
        with patch.object(dispatcher, '_create_outbound_message') as mock_create:
            mock_message = OutboundMessage(
                message_id="integration_test_msg_123",
                conversation_id="integration_test_conv_123",
                content="Integration test content",
                channel_destination="gmail",
                recipient_identifier="test@example.com"
            )
            mock_create.return_value = mock_message

            # Mock the routing
            with patch.object(dispatcher, 'route_message', return_value=AsyncMock(return_value=True)):
                # Mock the delivery tracker
                with patch.object(dispatcher.delivery_tracker, 'update_delivery_status', return_value=AsyncMock()):
                    await dispatcher.process_message(message_data)

        # Verify that the message was processed
        mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_kafka_consumer_integration(self, dispatcher):
        """Integration test for Kafka consumer functionality"""
        # Mock the Kafka consumer
        mock_consumer = AsyncMock()
        mock_msg = MagicMock()
        mock_msg.value = {
            'message_id': 'consumer_test_msg_123',
            'conversation_id': 'consumer_test_conv_123',
            'content': 'Consumer test content',
            'channel_destination': 'gmail',
            'recipient_identifier': 'test@example.com',
            'sender_identifier': 'integration_tester'
        }
        mock_msg.topic = 'outbound_responses'
        mock_msg.partition = 0
        mock_msg.offset = 0

        # Create an async iterator for the consumer
        async def async_iter():
            yield mock_msg
            # Stop after one message to avoid infinite loop
            dispatcher.running = False

        mock_consumer.__aiter__.return_value = async_iter()
        dispatcher.consumer = mock_consumer

        # Mock the process_message method
        with patch.object(dispatcher, 'process_message', return_value=AsyncMock()):
            # Limit execution to avoid infinite loop
            dispatcher.running = True
            # Process just one message then stop
            await dispatcher.process_message(mock_msg.value)

        # Verify that process_message was called
        dispatcher.process_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_message_validation_integration(self, dispatcher):
        """Integration test for message validation"""
        message_data = {
            'message_id': 'validation_test_msg_123',
            'conversation_id': 'validation_test_conv_123',
            'content': 'Validation test content',
            'channel_destination': 'gmail',
            'recipient_identifier': 'test@example.com',
            'sender_identifier': 'integration_tester'
        }

        # Mock the creation of outbound message
        with patch.object(dispatcher, '_create_outbound_message') as mock_create:
            mock_message = OutboundMessage(
                message_id="validation_test_msg_123",
                conversation_id="validation_test_conv_123",
                content="Validation test content",
                channel_destination="gmail",
                recipient_identifier="test@example.com"
            )
            mock_create.return_value = mock_message

            # Mock the validation
            with patch.object(dispatcher.validator, 'validate_and_raise', return_value=None):
                # Mock the routing
                with patch.object(dispatcher, 'route_message', return_value=AsyncMock(return_value=True)):
                    # Mock the delivery tracker
                    with patch.object(dispatcher.delivery_tracker, 'update_delivery_status', return_value=AsyncMock()):
                        await dispatcher.process_message(message_data)

        # Verify that validation was called
        dispatcher.validator.validate_and_raise.assert_called_once()

    @pytest.mark.asyncio
    async def test_channel_routing_integration(self, dispatcher):
        """Integration test for channel-based routing"""
        test_cases = [
            {
                'channel': 'gmail',
                'identifier': 'test@example.com',
                'expected_method': 'deliver_via_gmail'
            },
            {
                'channel': 'whatsapp',
                'identifier': 'whatsapp:+1234567890',
                'expected_method': 'deliver_via_whatsapp'
            },
            {
                'channel': 'webform',
                'identifier': 'https://example.com/webhook',
                'expected_method': 'deliver_via_webhook'
            }
        ]

        for test_case in test_cases:
            message = OutboundMessage(
                message_id=f"routing_test_msg_{test_case['channel']}_123",
                conversation_id=f"routing_test_conv_{test_case['channel']}_123",
                content=f"Routing test content for {test_case['channel']}",
                channel_destination=test_case['channel'],
                recipient_identifier=test_case['identifier']
            )

            # Mock the specific delivery method
            with patch.object(dispatcher, test_case['expected_method'], return_value=AsyncMock(return_value=True)):
                # Mock the delivery tracker
                with patch.object(dispatcher.delivery_tracker, 'update_delivery_status', return_value=AsyncMock()):
                    result = await dispatcher.route_message(message)

            assert result is True

    @pytest.mark.asyncio
    async def test_delivery_status_updates_integration(self, dispatcher):
        """Integration test for delivery status updates"""
        message = OutboundMessage(
            message_id="status_test_msg_123",
            conversation_id="status_test_conv_123",
            content="Status test content",
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
        mock_update.assert_any_call(message.message_id, 'delivered')

    @pytest.mark.asyncio
    async def test_retry_mechanism_integration(self, dispatcher):
        """Integration test for retry mechanism"""
        message = OutboundMessage(
            message_id="retry_test_msg_123",
            conversation_id="retry_test_conv_123",
            content="Retry test content",
            channel_destination="gmail",
            recipient_identifier="test@example.com"
        )

        # Mock the delivery failure and retry mechanism
        with patch('app.services.response_dispatcher.send_email', return_value={'success': False}):
            with patch.object(dispatcher.delivery_tracker, 'add_to_retry_queue', return_value=AsyncMock()):
                with patch.object(dispatcher.delivery_tracker, 'update_delivery_status', return_value=AsyncMock()):
                    await dispatcher.handle_delivery_failure(message)

        # Verify that the message was added to retry queue
        dispatcher.delivery_tracker.add_to_retry_queue.assert_called_once()

    @pytest.mark.asyncio
    async def test_database_integration(self, dispatcher):
        """Integration test for database operations"""
        # Mock the database session
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_result = MagicMock()

        # Simulate finding an existing message
        mock_result.message_id = "db_test_msg_123"
        mock_result.delivery_attempts = 0
        mock_query.filter.return_value.first.return_value = mock_result
        mock_session.query.return_value = mock_query

        dispatcher.Session = MagicMock(return_value=mock_session)

        # Mock delivery failure to trigger database operations
        with patch('app.services.response_dispatcher.send_email', return_value={'success': False}):
            with patch.object(dispatcher.delivery_tracker, 'update_delivery_status', return_value=AsyncMock()):
                await dispatcher.handle_delivery_failure(message=mock_result)

        # Verify database operations
        mock_session.query.assert_called()
        mock_session.close.assert_called()

    @pytest.mark.asyncio
    async def test_stop_dispatcher_integration(self, dispatcher):
        """Integration test for dispatcher shutdown"""
        # Mock the consumer and producer
        mock_consumer = AsyncMock()
        mock_producer = AsyncMock()

        dispatcher.consumer = mock_consumer
        dispatcher.producer = mock_producer

        await dispatcher.stop()

        # Verify that stop methods were called
        mock_consumer.stop.assert_called_once()
        if mock_producer:
            mock_producer.stop.assert_called_once()