import asyncio
import time
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import redis.asyncio as redis
from ..config.settings import settings
from ..utils.logger import logger


class RateLimiter:
    """
    Implements Redis-based rate limiting with sliding window counters
    """

    def __init__(self, redis_url: str = None):
        """
        Initialize the rate limiter

        Args:
            redis_url: Redis URL for storing rate limit data (defaults to settings.redis_url)
        """
        self.redis_url = redis_url or settings.redis_url
        self.redis_client = None
        self.default_window_seconds = settings.rate_limit_window_seconds

    async def initialize(self):
        """
        Initialize the Redis connection
        """
        try:
            self.redis_client = redis.from_url(self.redis_url)
            # Test the connection
            await self.redis_client.ping()
            logger.info("Rate limiter initialized successfully", redis_url=self.redis_url)
        except Exception as e:
            logger.error(f"Failed to initialize rate limiter: {str(e)}", error=str(e))
            raise

    async def check_limit(self, channel_type: str, max_requests: int, window_seconds: int = None) -> Tuple[bool, int, str]:
        """
        Check if a request is within the rate limit for a channel

        Args:
            channel_type: The channel type ('gmail', 'whatsapp', 'webform')
            max_requests: Maximum number of requests allowed
            window_seconds: Time window in seconds (defaults to settings.rate_limit_window_seconds)

        Returns:
            Tuple[bool, int, str]: (is_allowed, remaining_requests, reset_time_iso)
        """
        if not self.redis_client:
            raise RuntimeError("Rate limiter not initialized")

        window_seconds = window_seconds or self.default_window_seconds

        # Create a unique key for this channel and time window
        current_time = int(time.time())
        window_start = current_time - (current_time % window_seconds)
        key = f"rate_limit:{channel_type}:{window_start}"

        # Use Redis INCR to atomically increment the counter
        pipe = self.redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds * 2)  # Expire after 2 windows to ensure cleanup
        result = await pipe.execute()

        current_requests = result[0]

        # Calculate remaining requests and reset time
        remaining = max(0, max_requests - current_requests)
        reset_timestamp = window_start + window_seconds
        reset_time_iso = datetime.utcfromtimestamp(reset_timestamp).isoformat() + "Z"

        is_allowed = current_requests <= max_requests

        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded for {channel_type}",
                channel_type=channel_type,
                max_requests=max_requests,
                current_requests=current_requests,
                window_seconds=window_seconds
            )

        return is_allowed, remaining, reset_time_iso

    async def is_limited(self, channel_type: str, max_requests: int, window_seconds: int = None) -> bool:
        """
        Check if a channel is currently rate limited

        Args:
            channel_type: The channel type ('gmail', 'whatsapp', 'webform')
            max_requests: Maximum number of requests allowed
            window_seconds: Time window in seconds (defaults to settings.rate_limit_window_seconds)

        Returns:
            bool: True if rate limited, False otherwise
        """
        is_allowed, _, _ = await self.check_limit(channel_type, max_requests, window_seconds)
        return not is_allowed

    async def get_rate_limit_status(self, channel_type: str, max_requests: int, window_seconds: int = None) -> Dict:
        """
        Get the current rate limit status for a channel

        Args:
            channel_type: The channel type ('gmail', 'whatsapp', 'webform')
            max_requests: Maximum number of requests allowed
            window_seconds: Time window in seconds (defaults to settings.rate_limit_window_seconds)

        Returns:
            Dict: Rate limit status information
        """
        if not self.redis_client:
            raise RuntimeError("Rate limiter not initialized")

        window_seconds = window_seconds or self.default_window_seconds

        # Find the current window
        current_time = int(time.time())
        window_start = current_time - (current_time % window_seconds)
        key = f"rate_limit:{channel_type}:{window_start}"

        # Get the current count
        current_requests = await self.redis_client.get(key)
        current_requests = int(current_requests) if current_requests else 0

        # Calculate remaining requests and reset time
        remaining = max(0, max_requests - current_requests)
        reset_timestamp = window_start + window_seconds
        reset_time_iso = datetime.utcfromtimestamp(reset_timestamp).isoformat() + "Z"

        return {
            "channel_type": channel_type,
            "max_requests": max_requests,
            "current_requests": current_requests,
            "remaining_requests": remaining,
            "window_seconds": window_seconds,
            "reset_time": reset_time_iso,
            "is_limited": current_requests >= max_requests
        }

    async def reset_channel_limit(self, channel_type: str):
        """
        Reset the rate limit for a specific channel (useful for testing)

        Args:
            channel_type: The channel type to reset
        """
        if not self.redis_client:
            raise RuntimeError("Rate limiter not initialized")

        # Find the current window
        current_time = int(time.time())
        window_seconds = self.default_window_seconds
        window_start = current_time - (current_time % window_seconds)
        key = f"rate_limit:{channel_type}:{window_start}"

        # Delete the current window's counter
        await self.redis_client.delete(key)

        logger.info(f"Rate limit reset for {channel_type}", channel_type=channel_type)

    async def cleanup(self):
        """
        Cleanup resources used by the rate limiter
        """
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Rate limiter resources cleaned up")


class ChannelRateLimiter(RateLimiter):
    """
    Specialized rate limiter that manages different limits for different channels
    """

    def __init__(self, redis_url: str = None):
        """
        Initialize the channel rate limiter

        Args:
            redis_url: Redis URL for storing rate limit data
        """
        super().__init__(redis_url)
        self.channel_limits = {
            'gmail': {
                'max_requests': settings.gmail_max_requests_per_minute,
                'window_seconds': 60  # 1 minute window for Gmail
            },
            'whatsapp': {
                'max_requests': settings.twilio_max_requests_per_minute,
                'window_seconds': 60  # 1 minute window for Twilio
            },
            'webform': {
                'max_requests': 1000,  # Higher limit for webhooks
                'window_seconds': 60
            }
        }

    async def check_channel_limit(self, channel_type: str) -> Tuple[bool, int, str]:
        """
        Check if a request is within the rate limit for a specific channel

        Args:
            channel_type: The channel type ('gmail', 'whatsapp', 'webform')

        Returns:
            Tuple[bool, int, str]: (is_allowed, remaining_requests, reset_time_iso)
        """
        if channel_type not in self.channel_limits:
            raise ValueError(f"Unknown channel type: {channel_type}")

        limit_config = self.channel_limits[channel_type]
        return await self.check_limit(
            channel_type,
            limit_config['max_requests'],
            limit_config['window_seconds']
        )

    async def is_channel_limited(self, channel_type: str) -> bool:
        """
        Check if a specific channel is currently rate limited

        Args:
            channel_type: The channel type ('gmail', 'whatsapp', 'webform')

        Returns:
            bool: True if rate limited, False otherwise
        """
        if channel_type not in self.channel_limits:
            raise ValueError(f"Unknown channel type: {channel_type}")

        limit_config = self.channel_limits[channel_type]
        return await self.is_limited(
            channel_type,
            limit_config['max_requests'],
            limit_config['window_seconds']
        )

    async def get_channel_status(self, channel_type: str) -> Dict:
        """
        Get the current rate limit status for a specific channel

        Args:
            channel_type: The channel type ('gmail', 'whatsapp', 'webform')

        Returns:
            Dict: Rate limit status information
        """
        if channel_type not in self.channel_limits:
            raise ValueError(f"Unknown channel type: {channel_type}")

        limit_config = self.channel_limits[channel_type]
        return await self.get_rate_limit_status(
            channel_type,
            limit_config['max_requests'],
            limit_config['window_seconds']
        )

    def update_channel_limit(self, channel_type: str, max_requests: int, window_seconds: int = None):
        """
        Update the rate limit configuration for a channel

        Args:
            channel_type: The channel type to update
            max_requests: New maximum requests allowed
            window_seconds: New time window in seconds (optional)
        """
        if channel_type not in self.channel_limits:
            raise ValueError(f"Unknown channel type: {channel_type}")

        self.channel_limits[channel_type]['max_requests'] = max_requests
        if window_seconds is not None:
            self.channel_limits[channel_type]['window_seconds'] = window_seconds

        logger.info(
            f"Updated rate limit for {channel_type}",
            channel_type=channel_type,
            max_requests=max_requests,
            window_seconds=window_seconds
        )


# Global rate limiter instance
rate_limiter = ChannelRateLimiter()


async def initialize_rate_limiter():
    """
    Initialize the global rate limiter instance
    """
    await rate_limiter.initialize()


def get_rate_limiter() -> ChannelRateLimiter:
    """
    Get the global rate limiter instance

    Returns:
        ChannelRateLimiter: The global rate limiter instance
    """
    return rate_limiter


async def check_channel_limit(channel_type: str) -> Tuple[bool, int, str]:
    """
    Check if a request is within the rate limit for a specific channel

    Args:
        channel_type: The channel type ('gmail', 'whatsapp', 'webform')

    Returns:
        Tuple[bool, int, str]: (is_allowed, remaining_requests, reset_time_iso)
    """
    return await rate_limiter.check_channel_limit(channel_type)


async def is_channel_limited(channel_type: str) -> bool:
    """
    Check if a specific channel is currently rate limited

    Args:
        channel_type: The channel type ('gmail', 'whatsapp', 'webform')

    Returns:
        bool: True if rate limited, False otherwise
    """
    return await rate_limiter.is_channel_limited(channel_type)


async def get_channel_status(channel_type: str) -> Dict:
    """
    Get the current rate limit status for a specific channel

    Args:
        channel_type: The channel type ('gmail', 'whatsapp', 'webform')

    Returns:
        Dict: Rate limit status information
    """
    return await rate_limiter.get_channel_status(channel_type)