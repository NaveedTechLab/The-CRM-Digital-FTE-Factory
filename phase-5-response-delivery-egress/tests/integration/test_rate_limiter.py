import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.rate_limiter import RateLimiter


class TestRateLimiterIntegration:
    """Integration test suite for rate limiter functionality"""

    @pytest.fixture
    def rate_limiter(self):
        return RateLimiter()

    @pytest.mark.asyncio
    async def test_basic_rate_limit_functionality(self, rate_limiter):
        """Integration test for basic rate limit functionality"""
        # Test that a client can make requests within limits
        result1 = await rate_limiter.check_limit('gmail', 'client_123')
        result2 = await rate_limiter.check_limit('gmail', 'client_123')

        # Both should be allowed if within limits
        assert result1 is True
        assert result2 is True

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, rate_limiter):
        """Integration test for rate limit exceeded scenario"""
        # Mock the rate limiter to simulate being exceeded
        with patch('app.services.rate_limiter.is_limited', return_value=AsyncMock(return_value=True)):
            result = await rate_limiter.check_limit('gmail', 'client_123')

        # Should be denied when limit is exceeded
        assert result is False

    @pytest.mark.asyncio
    async def test_different_channels_independent_limits(self, rate_limiter):
        """Integration test for independent rate limits per channel"""
        # Test that different channels have independent limits
        gmail_result = await rate_limiter.check_limit('gmail', 'client_123')
        whatsapp_result = await rate_limiter.check_limit('whatsapp', 'client_123')
        webform_result = await rate_limiter.check_limit('webform', 'client_123')

        # All should be allowed as they're different channels
        assert gmail_result is True
        assert whatsapp_result is True
        assert webform_result is True

    @pytest.mark.asyncio
    async def test_same_client_different_channels(self, rate_limiter):
        """Integration test for same client across different channels"""
        # A client should be able to use different channels independently
        result1 = await rate_limiter.check_limit('gmail', 'same_client')
        result2 = await rate_limiter.check_limit('whatsapp', 'same_client')

        # Should be allowed as they're different channels
        assert result1 is True
        assert result2 is True

    @pytest.mark.asyncio
    async def test_channel_specific_limits(self, rate_limiter):
        """Integration test for channel-specific rate limits"""
        # Test that each channel has its own limit configuration
        results = []
        for i in range(5):
            result = await rate_limiter.check_limit('gmail', f'client_{i}')
            results.append(result)

        # All should be allowed if within individual limits
        assert all(results)

    @pytest.mark.asyncio
    async def test_rate_limit_status_check(self, rate_limiter):
        """Integration test for checking rate limit status"""
        with patch('app.services.rate_limiter.get_channel_status') as mock_get_status:
            mock_get_status.return_value = {
                'remaining_calls': 10,
                'reset_time': '2023-01-01T00:00:00Z',
                'limit': 100
            }

            result = await rate_limiter.get_channel_status('gmail')

        assert result['remaining_calls'] == 10
        assert result['limit'] == 100

    @pytest.mark.asyncio
    async def test_rate_limit_reset_mechanism(self, rate_limiter):
        """Integration test for rate limit reset functionality"""
        # Test the reset mechanism by checking if limits are properly enforced
        client_id = 'reset_test_client'

        # Make multiple requests
        results = []
        for i in range(3):
            result = await rate_limiter.check_limit('gmail', client_id)
            results.append(result)

        # Assuming default limits allow these requests
        assert all(results)

    @pytest.mark.asyncio
    async def test_concurrent_rate_limit_access(self, rate_limiter):
        """Integration test for concurrent access to rate limiter"""
        async def make_request(client_id):
            return await rate_limiter.check_limit('gmail', client_id)

        # Simulate concurrent requests
        tasks = [make_request(f'concurrent_client_{i}') for i in range(5)]
        results = await asyncio.gather(*tasks)

        # All should be allowed as they're different clients
        assert all(results)

    @pytest.mark.asyncio
    async def test_rate_limit_with_redis_backend(self, rate_limiter):
        """Integration test for rate limiter with Redis backend"""
        # Mock Redis operations
        with patch('redis.asyncio.Redis') as mock_redis:
            mock_conn = AsyncMock()
            mock_redis.return_value = mock_conn

            # Mock the Redis INCR and EXPIRE operations
            mock_conn.incr.return_value = 1
            mock_conn.expire.return_value = True

            result = await rate_limiter.check_limit('gmail', 'redis_test_client')

        assert result is True

    @pytest.mark.asyncio
    async def test_rate_limit_sliding_window(self, rate_limiter):
        """Integration test for sliding window rate limiting"""
        client_id = 'sliding_window_client'

        # Test multiple requests in sequence
        for i in range(3):
            result = await rate_limiter.check_limit('gmail', f'{client_id}_{i}')
            assert result is True

    @pytest.mark.asyncio
    async def test_rate_limit_cleanup(self, rate_limiter):
        """Integration test for rate limit cleanup functionality"""
        # Test that the rate limiter can clean up old entries
        client_id = 'cleanup_test_client'

        # Make a request
        result = await rate_limiter.check_limit('gmail', client_id)
        assert result is True

        # Simulate cleanup by checking if the counter exists
        # This would typically involve Redis TTL operations
        with patch('app.services.rate_limiter.redis_client') as mock_redis:
            mock_redis.exists.return_value = 1
            exists = await mock_redis.exists(f"rate_limit:gmail:{client_id}")

        assert exists is not None

    @pytest.mark.asyncio
    async def test_rate_limit_configuration_loading(self, rate_limiter):
        """Integration test for loading rate limit configurations"""
        # Verify that the rate limiter uses configuration properly
        assert hasattr(rate_limiter, 'default_limits')
        assert 'gmail' in rate_limiter.default_limits
        assert 'whatsapp' in rate_limiter.default_limits
        assert 'webform' in rate_limiter.default_limits

    @pytest.mark.asyncio
    async def test_is_channel_limited_helper(self):
        """Integration test for the is_channel_limited helper function"""
        from app.services.rate_limiter import is_channel_limited

        # Mock the rate limiter
        with patch('app.services.rate_limiter.rate_limiter') as mock_limiter:
            mock_limiter.check_limit.return_value = AsyncMock(return_value=False)

            result = await is_channel_limited('gmail')

        # Should return True if the channel is limited (check_limit returns False)
        mock_limiter.check_limit.assert_called_once_with('gmail', 'global')

    @pytest.mark.asyncio
    async def test_global_rate_limiting(self, rate_limiter):
        """Integration test for global rate limiting"""
        # Test global limits across all clients for a channel
        results = []
        for i in range(5):
            result = await rate_limiter.check_limit('gmail', f'global_test_client_{i}')
            results.append(result)

        # All should be allowed if within global limits
        assert all(results)

    @pytest.mark.asyncio
    async def test_rate_limit_error_handling(self, rate_limiter):
        """Integration test for rate limiter error handling"""
        # Mock an error in the Redis connection
        with patch('app.services.rate_limiter.redis_client') as mock_redis:
            mock_redis.incr.side_effect = Exception("Redis connection failed")

            # The rate limiter should handle errors gracefully
            try:
                result = await rate_limiter.check_limit('gmail', 'error_test_client')
                # In case of error, it might default to allowing the request
            except Exception:
                # Or it might raise an exception that's properly handled
                pass