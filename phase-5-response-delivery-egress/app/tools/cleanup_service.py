"""
System cleanup and shutdown procedures for the Response Delivery Dispatcher.
Provides utilities for graceful shutdown, resource cleanup, and state reset.
"""

import asyncio
from typing import Dict, Any
from ..services.delivery_tracker import get_delivery_tracker
from ..services.rate_limiter import get_rate_limiter
from ..services.response_dispatcher import get_dispatcher
from ..utils.logger import logger


class CleanupService:
    """
    Manages cleanup operations for the Response Delivery Dispatcher system.
    Handles graceful shutdown, retry queue cleanup, rate limit resets,
    and delivery statistics management.
    """

    def __init__(self):
        self.delivery_tracker = get_delivery_tracker()
        self.rate_limiter = get_rate_limiter()
        self.dispatcher = get_dispatcher()

    async def reset_rate_limits(self) -> Dict[str, Any]:
        """Reset rate limits for all channels."""
        channels = ['gmail', 'whatsapp', 'webform']
        reset_results = {}

        for channel in channels:
            try:
                await self.rate_limiter.reset_channel_limit(channel)
                reset_results[channel] = "reset"
            except Exception as e:
                reset_results[channel] = f"error: {str(e)}"

        logger.info("Rate limits reset", results=reset_results)
        return {"operation": "reset_rate_limits", "results": reset_results}

    async def clear_retry_queue(self) -> Dict[str, Any]:
        """Clear all items from the retry queue."""
        removed = await self.delivery_tracker.clear_retry_queue()
        logger.info(f"Retry queue cleared: {removed} items removed")
        return {"operation": "clear_retry_queue", "items_removed": removed}

    async def reset_delivery_stats(self) -> Dict[str, Any]:
        """Reset all delivery statistics."""
        success = await self.delivery_tracker.reset_delivery_stats()
        logger.info(f"Delivery stats reset: {'success' if success else 'failed'}")
        return {"operation": "reset_stats", "success": success}

    async def full_cleanup(self) -> Dict[str, Any]:
        """
        Perform a full system cleanup: reset rate limits, clear retry queue,
        and reset delivery statistics.
        """
        results = {}
        results["rate_limits"] = await self.reset_rate_limits()
        results["retry_queue"] = await self.clear_retry_queue()
        results["stats"] = await self.reset_delivery_stats()

        logger.info("Full cleanup completed", results=results)
        return {"operation": "full_cleanup", "results": results}

    async def graceful_shutdown(self) -> Dict[str, Any]:
        """
        Perform a graceful shutdown of the dispatcher.
        Stops the consumer, flushes pending operations, and cleans up resources.
        """
        logger.info("Initiating graceful shutdown")

        # Stop the dispatcher
        await self.dispatcher.stop()

        # Cleanup rate limiter resources
        await self.rate_limiter.cleanup()

        logger.info("Graceful shutdown completed")
        return {"operation": "graceful_shutdown", "status": "completed"}


# Singleton instance
_cleanup_service = None


def get_cleanup_service() -> CleanupService:
    """Get or create the global CleanupService instance."""
    global _cleanup_service
    if _cleanup_service is None:
        _cleanup_service = CleanupService()
    return _cleanup_service
