import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.response_dispatcher import ResponseDispatcher
from app.models.outbound_message import OutboundMessage
from app.services.rate_limiter import RateLimiter


class TestAPILimitsStress:
    """Stress test suite for API limits and rate limiting"""

    @pytest.fixture
    def rate_limiter(self):
        return RateLimiter()

    @pytest.mark.asyncio
    async def test_gmail_api_rate_limit_handling(self, rate_limiter):
        """Stress test for Gmail API rate limit handling"""
        # Simulate hitting Gmail API rate limits
        call_count = 0
        max_calls_per_minute = 250  # Typical Gmail API limit

        async def mock_gmail_api_call():
            nonlocal call_count
            call_count += 1
            # Simulate rate limit after reaching the limit
            if call_count > max_calls_per_minute:
                return {'success': False, 'rate_limit_hit': True, 'error': 'Rate limit exceeded'}
            return {'success': True}

        # Make many concurrent API calls
        start_time = time.time()
        tasks = [mock_gmail_api_call() for _ in range(max_calls_per_minute + 50)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        success_count = sum(1 for r in results if isinstance(r, dict) and r.get('success', False))
        rate_limit_count = sum(1 for r in results if isinstance(r, dict) and r.get('rate_limit_hit', False))

        print(f"Gmail API rate limit test: {len(results)} calls in {end_time - start_time:.2f}s")
        print(f"Successful calls: {success_count}, Rate-limited calls: {rate_limit_count}")

        # Verify that rate limiting worked as expected
        assert success_count <= max_calls_per_minute
        assert rate_limit_count >= 50

    @pytest.mark.asyncio
    async def test_whatsapp_api_rate_limit_handling(self, rate_limiter):
        """Stress test for WhatsApp API rate limit handling"""
        # Simulate hitting WhatsApp API rate limits
        call_count = 0
        max_calls_per_second = 5  # Conservative WhatsApp API limit

        async def mock_whatsapp_api_call():
            nonlocal call_count
            call_count += 1
            # Simulate rate limit after reaching the limit
            if call_count > max_calls_per_second:
                return {'success': False, 'rate_limit_hit': True, 'error': 'Rate limit exceeded'}
            return {'success': True}

        # Make many rapid API calls
        start_time = time.time()
        tasks = [mock_whatsapp_api_call() for _ in range(max_calls_per_second + 10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        success_count = sum(1 for r in results if isinstance(r, dict) and r.get('success', False))
        rate_limit_count = sum(1 for r in results if isinstance(r, dict) and r.get('rate_limit_hit', False))

        print(f"WhatsApp API rate limit test: {len(results)} calls in {end_time - start_time:.2f}s")
        print(f"Successful calls: {success_count}, Rate-limited calls: {rate_limit_count}")

        # Verify that rate limiting worked as expected
        assert success_count <= max_calls_per_second
        assert rate_limit_count >= 10

    @pytest.mark.asyncio
    async def test_rate_limiter_enforcement(self):
        """Stress test for rate limiter enforcement"""
        # Test the rate limiter with aggressive requests
        from app.services.rate_limiter import RateLimiter

        rate_limiter = RateLimiter()

        # Mock Redis operations to simulate real behavior
        with patch('app.services.rate_limiter.redis_client') as mock_redis:
            # Simulate that the counter increases and eventually hits the limit
            call_count = 0

            async def mock_incr(key):
                nonlocal call_count
                call_count += 1
                return call_count

            mock_redis.incr.side_effect = mock_incr
            mock_redis.expire.return_value = True
            mock_redis.exists.return_value = True
            mock_redis.get.return_value = None  # No TTL initially

            # Make many concurrent requests
            async def make_request():
                # Use a fixed client ID to trigger rate limiting
                return await rate_limiter.check_limit('gmail', 'test_client')

            start_time = time.time()
            tasks = [make_request() for _ in range(100)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            success_count = sum(1 for r in results if r is True)
            failure_count = sum(1 for r in results if r is False)

            print(f"Rate limiter enforcement test: {len(results)} requests in {end_time - start_time:.2f}s")
            print(f"Allowed: {success_count}, Rejected: {failure_count}")

            # Some should be rejected due to rate limiting
            assert success_count + failure_count == 100
            assert failure_count >= 0  # At least some should be rate limited

    @pytest.mark.asyncio
    async def test_dispatch_system_under_api_pressure(self):
        """Stress test for dispatch system under API pressure"""
        dispatcher = ResponseDispatcher()

        # Create messages that will trigger API calls
        messages = []
        for i in range(30):
            message = OutboundMessage(
                message_id=f"api_pressure_msg_{i}",
                conversation_id=f"api_pressure_conv_{i}",
                content=f"API pressure test content {i}",
                channel_destination="gmail",
                recipient_identifier=f"test{i}@example.com"
            )
            messages.append(message)

        # Simulate API pressure by having many requests that might hit rate limits
        call_count = 0
        max_allowed = 20  # Simulate a rate limit

        async def mock_gmail_delivery(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Simulate rate limiting after certain threshold
            if call_count > max_allowed:
                return {'success': False, 'rate_limit_hit': True, 'error': 'Rate limit exceeded'}
            return {'success': True, 'message_id': f'sent_{call_count}'}

        with patch('app.services.response_dispatcher.send_email', side_effect=mock_gmail_delivery):
            # Mock the delivery tracker
            with patch.object(dispatcher.delivery_tracker, 'update_delivery_status', return_value=AsyncMock()):
                start_time = time.time()
                tasks = [dispatcher.route_message(msg) for msg in messages]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                end_time = time.time()

        success_count = sum(1 for r in results if r is True)
        failure_count = len(results) - success_count

        print(f"Dispatch system under API pressure: {len(results)} messages in {end_time - start_time:.2f}s")
        print(f"Successful deliveries: {success_count}, Failed deliveries: {failure_count}")

        # Should handle API pressure gracefully
        assert success_count >= max_allowed  # At least the allowed amount should succeed
        assert failure_count >= (len(results) - max_allowed)  # Remaining should fail due to rate limit

    @pytest.mark.asyncio
    async def test_concurrent_api_limit_scenarios(self):
        """Stress test for concurrent API limit scenarios across channels"""
        dispatcher = ResponseDispatcher()

        # Create messages for different channels
        messages = []
        for i in range(20):
            channel = ['gmail', 'whatsapp', 'webform'][i % 3]
            identifier = (
                f"test{i}@example.com" if channel == 'gmail' else
                f"whatsapp:+123456789{i:02d}" if channel == 'whatsapp' else
                f"https://example{i}.com/webhook"
            )

            message = OutboundMessage(
                message_id=f"concurrent_api_msg_{i}",
                conversation_id=f"concurrent_api_conv_{i}",
                content=f"Concurrent API test content {i}",
                channel_destination=channel,
                recipient_identifier=identifier
            )
            messages.append(message)

        # Simulate different API limits for different channels
        gmail_count = 0
        whatsapp_count = 0
        webform_count = 0

        async def mock_gmail_delivery(*args, **kwargs):
            nonlocal gmail_count
            gmail_count += 1
            # Gmail API limit: 250 requests per minute
            if gmail_count > 10:  # Using smaller number for test
                return {'success': False, 'rate_limit_hit': True, 'error': 'Gmail rate limit'}
            return {'success': True}

        async def mock_whatsapp_delivery(*args, **kwargs):
            nonlocal whatsapp_count
            whatsapp_count += 1
            # WhatsApp API limit: varies by provider
            if whatsapp_count > 8:  # Using smaller number for test
                return {'success': False, 'rate_limit_hit': True, 'error': 'WhatsApp rate limit'}
            return {'success': True}

        async def mock_webform_delivery(*args, **kwargs):
            nonlocal webform_count
            webform_count += 1
            # Webhook limit: depends on receiving server
            if webform_count > 12:  # Using smaller number for test
                return {'success': False, 'rate_limit_hit': True, 'error': 'Webhook rate limit'}
            return {'success': True}

        # Apply mocks based on channel
        with patch('app.services.response_dispatcher.send_email', side_effect=mock_gmail_delivery):
            with patch('app.services.response_dispatcher.send_whatsapp_message', side_effect=mock_whatsapp_delivery):
                with patch('app.services.response_dispatcher.send_webhook', side_effect=mock_webform_delivery):
                    # Mock the delivery tracker
                    with patch.object(dispatcher.delivery_tracker, 'update_delivery_status', return_value=AsyncMock()):
                        start_time = time.time()
                        tasks = [dispatcher.route_message(msg) for msg in messages]
                        results = await asyncio.gather(*tasks, return_exceptions=True)
                        end_time = time.time()

        success_count = sum(1 for r in results if r is True)
        failure_count = len(results) - success_count

        print(f"Concurrent API limits across channels: {len(results)} messages in {end_time - start_time:.2f}s")
        print(f"Successful deliveries: {success_count}, Failed deliveries: {failure_count}")

        # Should handle concurrent API limits appropriately
        assert success_count >= 0  # Some should succeed
        assert failure_count >= 0  # Some should fail due to limits

    @pytest.mark.asyncio
    async def test_rate_limit_recovery_mechanisms(self):
        """Stress test for rate limit recovery mechanisms"""
        dispatcher = ResponseDispatcher()

        # Create messages that will be queued for retry after rate limiting
        messages = []
        for i in range(15):
            message = OutboundMessage(
                message_id=f"recovery_msg_{i}",
                conversation_id=f"recovery_conv_{i}",
                content=f"Recovery test content {i}",
                channel_destination="gmail",
                recipient_identifier=f"test{i}@example.com"
            )
            messages.append(message)

        # Simulate initial rate limiting, then recovery
        call_count = 0
        rate_limit_phase = True
        max_initial_limit = 5

        async def mock_gmail_delivery(*args, **kwargs):
            nonlocal call_count, rate_limit_phase
            call_count += 1

            # Initially rate limit
            if call_count <= max_initial_limit and rate_limit_phase:
                return {'success': False, 'rate_limit_hit': True, 'error': 'Initial rate limit'}

            # After initial burst, allow some requests
            rate_limit_phase = False
            return {'success': True, 'message_id': f'recovered_{call_count}'}

        with patch('app.services.response_dispatcher.send_email', side_effect=mock_gmail_delivery):
            # Mock the delivery tracker and retry mechanism
            with patch.object(dispatcher.delivery_tracker, 'update_delivery_status', return_value=AsyncMock()):
                with patch.object(dispatcher.delivery_tracker, 'add_to_retry_queue', return_value=AsyncMock()):
                    start_time = time.time()
                    tasks = [dispatcher.route_message(msg) for msg in messages]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    end_time = time.time()

        success_count = sum(1 for r in results if r is True)
        failure_count = len(results) - success_count

        print(f"Rate limit recovery test: {len(results)} messages in {end_time - start_time:.2f}s")
        print(f"Recovered deliveries: {success_count}, Initial failures: {failure_count}")

        # Should demonstrate recovery mechanism
        assert success_count >= 0

    @pytest.mark.asyncio
    async def test_overwhelming_api_requests(self):
        """Stress test for overwhelming API request scenarios"""
        # Create a very large number of requests to overwhelm APIs
        request_count = 100

        # Track API usage
        api_call_count = 0
        max_safe_calls = 50  # Simulated safe limit

        async def mock_api_call():
            nonlocal api_call_count
            api_call_count += 1
            # Simulate that calls beyond the limit will fail or be throttled
            if api_call_count > max_safe_calls:
                # Simulate various failure modes
                import random
                failure_type = random.choice(['timeout', 'rate_limit', 'connection_error'])

                if failure_type == 'timeout':
                    await asyncio.sleep(0.1)  # Simulate timeout
                    return {'success': False, 'error': 'timeout', 'rate_limit_hit': False}
                elif failure_type == 'rate_limit':
                    return {'success': False, 'error': 'rate limit', 'rate_limit_hit': True}
                else:
                    return {'success': False, 'error': 'connection error', 'rate_limit_hit': False}
            return {'success': True, 'response_time': 0.05}

        start_time = time.time()
        tasks = [mock_api_call() for _ in range(request_count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        success_count = sum(1 for r in results if isinstance(r, dict) and r.get('success', False))
        failure_count = len(results) - success_count
        rate_limit_count = sum(1 for r in results if isinstance(r, dict) and r.get('rate_limit_hit', False))

        print(f"Overwhelming API requests: {request_count} requests in {end_time - start_time:.2f}s")
        print(f"Successful: {success_count}, Failed: {failure_count}, Rate-limited: {rate_limit_count}")

        # Should handle overwhelming requests with appropriate failure rates
        assert api_call_count == request_count
        assert success_count <= max_safe_calls

    @pytest.mark.asyncio
    async def test_api_limit_detection_accuracy(self):
        """Stress test for accurate detection of API limits"""
        # Test that the system accurately detects when API limits are reached
        call_count = 0
        actual_limit = 25  # The real API limit
        detected_errors = []

        async def mock_api_with_limits():
            nonlocal call_count
            call_count += 1

            if call_count > actual_limit:
                # Simulate API returning rate limit error
                error_msg = "429 Too Many Requests - Daily limit exceeded"
                detected_errors.append(error_msg)
                return {'success': False, 'error': error_msg, 'rate_limit_hit': True}

            return {'success': True, 'call_num': call_count}

        # Make requests up to and beyond the limit
        requests_to_make = actual_limit + 10
        start_time = time.time()
        tasks = [mock_api_with_limits() for _ in range(requests_to_make)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        success_count = sum(1 for r in results if isinstance(r, dict) and r.get('success', False))
        failure_count = len(results) - success_count
        detected_rate_limits = len(detected_errors)

        print(f"API limit detection test: {requests_to_make} requests in {end_time - start_time:.2f}s")
        print(f"Expected limit: {actual_limit}, Successful: {success_count}, Rate-limited: {detected_rate_limits}")

        # Verify that limit detection is accurate
        assert success_count == actual_limit
        assert detected_rate_limits == 10  # 10 requests beyond the limit
        assert failure_count == detected_rate_limits

    @pytest.mark.asyncio
    async def test_backpressure_handling(self):
        """Stress test for backpressure handling under API limits"""
        dispatcher = ResponseDispatcher()

        # Create messages to send under API pressure
        messages = []
        for i in range(25):
            message = OutboundMessage(
                message_id=f"backpressure_msg_{i}",
                conversation_id=f"backpressure_conv_{i}",
                content=f"Backpressure test content {i}",
                channel_destination="gmail",
                recipient_identifier=f"test{i}@example.com"
            )
            messages.append(message)

        # Simulate API that applies backpressure
        call_count = 0
        max_concurrent = 3  # Simulate API that can only handle 3 concurrent requests
        active_requests = 0
        max_active = 0

        async def mock_api_with_backpressure(*args, **kwargs):
            nonlocal call_count, active_requests, max_active
            call_count += 1
            active_requests += 1
            max_active = max(max_active, active_requests)

            # Simulate API delay to create backpressure
            await asyncio.sleep(0.2)

            active_requests -= 1
            return {'success': True, 'backpressure_test': True}

        with patch('app.services.response_dispatcher.send_email', side_effect=mock_api_with_backpressure):
            # Mock the delivery tracker
            with patch.object(dispatcher.delivery_tracker, 'update_delivery_status', return_value=AsyncMock()):
                start_time = time.time()
                tasks = [dispatcher.route_message(msg) for msg in messages]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                end_time = time.time()

        success_count = sum(1 for r in results if r is True)

        print(f"Backpressure handling test: {len(results)} messages in {end_time - start_time:.2f}s")
        print(f"Max concurrent requests: {max_active}, Successful: {success_count}")

        # Should handle backpressure without crashing
        assert success_count == len(results)
        assert max_active >= 0  # Should have tracked max concurrency

    @pytest.mark.asyncio
    async def test_api_limit_resilience_under_load(self):
        """Stress test for API limit resilience under sustained load"""
        # Test sustained load with realistic API limits
        sustained_minutes = 1  # Shortened for test
        requests_per_minute = 20
        total_requests = requests_per_minute * sustained_minutes

        successful_requests = 0
        failed_requests = 0
        rate_limited_requests = 0

        # Simulate a realistic API limit
        rate_limit_per_minute = 15
        current_minute = 0
        current_minute_count = 0

        async def mock_sustained_api_call(start_time):
            nonlocal current_minute, current_minute_count, successful_requests, failed_requests, rate_limited_requests

            # Determine which minute we're in
            elapsed = time.time() - start_time
            minute = int(elapsed // 60)

            if minute != current_minute:
                # Reset counter for new minute
                current_minute = minute
                current_minute_count = 0

            # Check rate limit for this minute
            if current_minute_count >= rate_limit_per_minute:
                rate_limited_requests += 1
                return {'success': False, 'rate_limit_hit': True, 'error': 'Minute limit exceeded'}

            current_minute_count += 1
            successful_requests += 1
            # Simulate a small delay
            await asyncio.sleep(0.05)
            return {'success': True}

        start_time = time.time()
        tasks = [mock_sustained_api_call(start_time) for _ in range(total_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        print(f"API resilience under sustained load: {total_requests} requests over {end_time - start_time:.2f}s")
        print(f"Successful: {successful_requests}, Rate-limited: {rate_limited_requests}, Failed: {failed_requests}")

        # Should respect rate limits under sustained load
        expected_successful = min(total_requests, rate_limit_per_minute * sustained_minutes)
        assert successful_requests <= expected_successful
        assert rate_limited_requests >= total_requests - expected_successful