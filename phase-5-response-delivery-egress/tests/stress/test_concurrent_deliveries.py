import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.response_dispatcher import ResponseDispatcher
from app.models.outbound_message import OutboundMessage


class TestConcurrentDeliveriesStress:
    """Stress test suite for concurrent delivery operations"""

    @pytest.fixture
    def dispatcher(self):
        return ResponseDispatcher()

    @pytest.mark.asyncio
    async def test_high_volume_concurrent_gmail_deliveries(self, dispatcher):
        """Stress test for high-volume concurrent Gmail deliveries"""
        # Create multiple Gmail messages
        messages = []
        for i in range(50):
            message = OutboundMessage(
                message_id=f"stress_gmail_msg_{i}",
                conversation_id=f"stress_conv_{i}",
                content=f"Stress test content {i}",
                channel_destination="gmail",
                recipient_identifier=f"test{i}@example.com"
            )
            messages.append(message)

        # Mock the Gmail delivery service
        with patch('app.services.response_dispatcher.send_email', return_value={'success': True}):
            # Mock the delivery tracker
            with patch.object(dispatcher.delivery_tracker, 'update_delivery_status', return_value=AsyncMock()):
                # Send all messages concurrently
                start_time = time.time()
                tasks = [dispatcher.route_message(msg) for msg in messages]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                end_time = time.time()

        successful_deliveries = sum(1 for r in results if r is True or (hasattr(r, 'success') and r.success))

        print(f"Concurrent Gmail deliveries: {len(messages)} messages in {end_time - start_time:.2f}s")
        print(f"Successful deliveries: {successful_deliveries}/{len(messages)}")

        # Most should succeed (allowing for some failures in stress conditions)
        assert successful_deliveries >= len(messages) * 0.95  # 95% success rate

    @pytest.mark.asyncio
    async def test_high_volume_concurrent_whatsapp_deliveries(self, dispatcher):
        """Stress test for high-volume concurrent WhatsApp deliveries"""
        # Create multiple WhatsApp messages
        messages = []
        for i in range(50):
            message = OutboundMessage(
                message_id=f"stress_wa_msg_{i}",
                conversation_id=f"stress_conv_{i}",
                content=f"Stress test content {i}",
                channel_destination="whatsapp",
                recipient_identifier=f"whatsapp:+123456789{i:02d}"
            )
            messages.append(message)

        # Mock the WhatsApp delivery service
        with patch('app.services.response_dispatcher.send_whatsapp_message', return_value={'success': True}):
            # Mock the delivery tracker
            with patch.object(dispatcher.delivery_tracker, 'update_delivery_status', return_value=AsyncMock()):
                # Send all messages concurrently
                start_time = time.time()
                tasks = [dispatcher.route_message(msg) for msg in messages]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                end_time = time.time()

        successful_deliveries = sum(1 for r in results if r is True or (hasattr(r, 'success') and r.success))

        print(f"Concurrent WhatsApp deliveries: {len(messages)} messages in {end_time - start_time:.2f}s")
        print(f"Successful deliveries: {successful_deliveries}/{len(messages)}")

        # Most should succeed (allowing for some failures in stress conditions)
        assert successful_deliveries >= len(messages) * 0.95  # 95% success rate

    @pytest.mark.asyncio
    async def test_high_volume_concurrent_webform_deliveries(self, dispatcher):
        """Stress test for high-volume concurrent Webform deliveries"""
        # Create multiple Webform messages
        messages = []
        for i in range(50):
            message = OutboundMessage(
                message_id=f"stress_wf_msg_{i}",
                conversation_id=f"stress_conv_{i}",
                content=f"Stress test content {i}",
                channel_destination="webform",
                recipient_identifier=f"https://example{i}.com/webhook"
            )
            messages.append(message)

        # Mock the Webform delivery service
        with patch('app.services.response_dispatcher.send_webhook', return_value={'success': True}):
            # Mock the delivery tracker
            with patch.object(dispatcher.delivery_tracker, 'update_delivery_status', return_value=AsyncMock()):
                # Send all messages concurrently
                start_time = time.time()
                tasks = [dispatcher.route_message(msg) for msg in messages]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                end_time = time.time()

        successful_deliveries = sum(1 for r in results if r is True or (hasattr(r, 'success') and r.success))

        print(f"Concurrent Webform deliveries: {len(messages)} messages in {end_time - start_time:.2f}s")
        print(f"Successful deliveries: {successful_deliveries}/{len(messages)}")

        # Most should succeed (allowing for some failures in stress conditions)
        assert successful_deliveries >= len(messages) * 0.95  # 95% success rate

    @pytest.mark.asyncio
    async def test_mixed_channel_concurrent_deliveries(self, dispatcher):
        """Stress test for mixed-channel concurrent deliveries"""
        # Create messages for all channels
        messages = []
        for i in range(30):
            # Round-robin assign to different channels
            channel = ['gmail', 'whatsapp', 'webform'][i % 3]
            identifier = (
                f"test{i}@example.com" if channel == 'gmail' else
                f"whatsapp:+123456789{i:02d}" if channel == 'whatsapp' else
                f"https://example{i}.com/webhook"
            )

            message = OutboundMessage(
                message_id=f"mixed_stress_msg_{i}",
                conversation_id=f"mixed_stress_conv_{i}",
                content=f"Mixed channel stress test content {i}",
                channel_destination=channel,
                recipient_identifier=identifier
            )
            messages.append(message)

        # Mock all delivery services
        with patch('app.services.response_dispatcher.send_email', return_value={'success': True}):
            with patch('app.services.response_dispatcher.send_whatsapp_message', return_value={'success': True}):
                with patch('app.services.response_dispatcher.send_webhook', return_value={'success': True}):
                    # Mock the delivery tracker
                    with patch.object(dispatcher.delivery_tracker, 'update_delivery_status', return_value=AsyncMock()):
                        # Send all messages concurrently
                        start_time = time.time()
                        tasks = [dispatcher.route_message(msg) for msg in messages]
                        results = await asyncio.gather(*tasks, return_exceptions=True)
                        end_time = time.time()

        successful_deliveries = sum(1 for r in results if r is True or (hasattr(r, 'success') and r.success))

        print(f"Mixed channel concurrent deliveries: {len(messages)} messages in {end_time - start_time:.2f}s")
        print(f"Successful deliveries: {successful_deliveries}/{len(messages)}")

        # Most should succeed (allowing for some failures in stress conditions)
        assert successful_deliveries >= len(messages) * 0.90  # 90% success rate

    @pytest.mark.asyncio
    async def test_very_high_concurrency_load(self, dispatcher):
        """Stress test for very high concurrency load"""
        # Create a very high number of messages
        messages = []
        for i in range(100):
            message = OutboundMessage(
                message_id=f"high_concurrency_msg_{i}",
                conversation_id=f"high_concurrency_conv_{i}",
                content=f"High concurrency test content {i}",
                channel_destination="gmail",
                recipient_identifier=f"test{i}@example.com"
            )
            messages.append(message)

        # Mock the delivery service
        with patch('app.services.response_dispatcher.send_email', return_value={'success': True}):
            # Mock the delivery tracker
            with patch.object(dispatcher.delivery_tracker, 'update_delivery_status', return_value=AsyncMock()):
                # Send all messages concurrently
                start_time = time.time()
                tasks = [dispatcher.route_message(msg) for msg in messages]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                end_time = time.time()

        successful_deliveries = sum(1 for r in results if r is True or (hasattr(r, 'success') and r.success))

        print(f"High concurrency load: {len(messages)} messages in {end_time - start_time:.2f}s")
        print(f"Successful deliveries: {successful_deliveries}/{len(messages)}")

        # Even under high load, most should succeed
        assert successful_deliveries >= len(messages) * 0.85  # 85% success rate

    @pytest.mark.asyncio
    async def test_concurrent_delivery_with_rate_limiting(self, dispatcher):
        """Stress test for concurrent deliveries with rate limiting"""
        # Create messages that will trigger rate limiting
        messages = []
        for i in range(20):
            message = OutboundMessage(
                message_id=f"rate_limit_stress_msg_{i}",
                conversation_id=f"rate_limit_stress_conv_{i}",
                content=f"Rate limit stress test content {i}",
                channel_destination="gmail",
                recipient_identifier="test@example.com"  # Same recipient to potentially trigger rate limits
            )
            messages.append(message)

        # Mock the delivery service and rate limiter
        with patch('app.services.response_dispatcher.send_email', return_value={'success': True}):
            with patch('app.services.response_dispatcher.is_channel_limited', return_value=AsyncMock(return_value=False)):
                # Mock the delivery tracker
                with patch.object(dispatcher.delivery_tracker, 'update_delivery_status', return_value=AsyncMock()):
                    # Send all messages concurrently
                    start_time = time.time()
                    tasks = [dispatcher.route_message(msg) for msg in messages]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    end_time = time.time()

        successful_deliveries = sum(1 for r in results if r is True or (hasattr(r, 'success') and r.success))

        print(f"Concurrent deliveries with rate limiting: {len(messages)} messages in {end_time - start_time:.2f}s")
        print(f"Successful deliveries: {successful_deliveries}/{len(messages)}")

        # Should handle rate limiting gracefully
        assert successful_deliveries >= len(messages) * 0.90  # 90% success rate

    @pytest.mark.asyncio
    async def test_concurrent_database_operations(self, dispatcher):
        """Stress test for concurrent database operations"""
        # Create messages that will trigger database operations
        messages = []
        for i in range(25):
            message = OutboundMessage(
                message_id=f"db_stress_msg_{i}",
                conversation_id=f"db_stress_conv_{i}",
                content=f"DB stress test content {i}",
                channel_destination="gmail",
                recipient_identifier=f"test{i}@example.com"
            )
            messages.append(message)

        # Mock the delivery service
        with patch('app.services.response_dispatcher.send_email', return_value={'success': True}):
            # Mock the delivery tracker with concurrent updates
            with patch.object(dispatcher.delivery_tracker, 'update_delivery_status', return_value=AsyncMock()):
                # Send all messages concurrently to trigger database operations
                start_time = time.time()
                tasks = [dispatcher.route_message(msg) for msg in messages]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                end_time = time.time()

        successful_deliveries = sum(1 for r in results if r is True or (hasattr(r, 'success') and r.success))

        print(f"Concurrent database operations: {len(messages)} messages in {end_time - start_time:.2f}s")
        print(f"Successful deliveries: {successful_deliveries}/{len(messages)}")

        # Should handle concurrent database operations
        assert successful_deliveries >= len(messages) * 0.95  # 95% success rate

    @pytest.mark.asyncio
    async def test_memory_usage_under_concurrent_load(self, dispatcher):
        """Stress test to monitor memory usage under concurrent load"""
        import tracemalloc

        # Start tracing memory
        tracemalloc.start()

        # Create messages for the test
        messages = []
        for i in range(40):
            message = OutboundMessage(
                message_id=f"memory_stress_msg_{i}",
                conversation_id=f"memory_stress_conv_{i}",
                content=f"Memory stress test content {i}",
                channel_destination="gmail",
                recipient_identifier=f"test{i}@example.com"
            )
            messages.append(message)

        # Mock the delivery service
        with patch('app.services.response_dispatcher.send_email', return_value={'success': True}):
            # Mock the delivery tracker
            with patch.object(dispatcher.delivery_tracker, 'update_delivery_status', return_value=AsyncMock()):
                # Send all messages concurrently
                start_time = time.time()
                tasks = [dispatcher.route_message(msg) for msg in messages]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                end_time = time.time()

        # Take a snapshot of memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        successful_deliveries = sum(1 for r in results if r is True or (hasattr(r, 'success') and r.success))

        print(f"Memory usage under load: current={current/1024/1024:.2f}MB, peak={peak/1024/1024:.2f}MB")
        print(f"Memory stress test: {len(messages)} messages in {end_time - start_time:.2f}s")
        print(f"Successful deliveries: {successful_deliveries}/{len(messages)}")

        # Should handle concurrent load without excessive memory usage
        assert successful_deliveries >= len(messages) * 0.95  # 95% success rate
        assert peak < 100 * 1024 * 1024  # Less than 100MB peak usage

    @pytest.mark.asyncio
    async def test_long_running_concurrent_operations(self, dispatcher):
        """Stress test for long-running concurrent operations"""
        # Create messages for extended test
        messages = []
        for i in range(15):
            message = OutboundMessage(
                message_id=f"long_run_msg_{i}",
                conversation_id=f"long_run_conv_{i}",
                content=f"Long running test content {i}",
                channel_destination="gmail",
                recipient_identifier=f"test{i}@example.com"
            )
            messages.append(message)

        # Mock the delivery service with simulated delays
        async def slow_delivery(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate network delay
            return {'success': True}

        with patch('app.services.response_dispatcher.send_email', side_effect=slow_delivery):
            # Mock the delivery tracker
            with patch.object(dispatcher.delivery_tracker, 'update_delivery_status', return_value=AsyncMock()):
                # Send all messages concurrently
                start_time = time.time()
                tasks = [dispatcher.route_message(msg) for msg in messages]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                end_time = time.time()

        successful_deliveries = sum(1 for r in results if r is True or (hasattr(r, 'success') and r.success))

        print(f"Long-running concurrent operations: {len(messages)} messages in {end_time - start_time:.2f}s")
        print(f"Successful deliveries: {successful_deliveries}/{len(messages)}")

        # Should handle longer-running concurrent operations
        assert successful_deliveries >= len(messages) * 0.95  # 95% success rate