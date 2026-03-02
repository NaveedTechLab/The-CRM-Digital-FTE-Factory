#!/usr/bin/env python3
"""
Cleanup script for the Response Delivery Dispatcher service
Used for stress testing to reset all state
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.rate_limiter import get_rate_limiter, initialize_rate_limiter
from app.services.delivery_tracker import get_delivery_tracker
from app.config.settings import settings
from app.utils.logger import logger


async def reset_rate_limits():
    """
    Reset all rate limit counters in Redis
    """
    logger.info("Resetting rate limit counters...")

    rate_limiter = get_rate_limiter()
    await initialize_rate_limiter()  # Ensure the rate limiter is initialized

    for channel_type in ['gmail', 'whatsapp', 'webform']:
        try:
            await rate_limiter.reset_channel_limit(channel_type)
            logger.info(f"Rate limit reset for {channel_type}")
        except Exception as e:
            logger.error(f"Error resetting rate limit for {channel_type}: {str(e)}")

    logger.info("All rate limit counters reset")


async def clear_retry_queue():
    """
    Clear the retry queue
    Note: In a real implementation, this would clear the retry queue in the database
    """
    logger.info("Clearing retry queue...")

    # In a real implementation, this would connect to the database and clear the retry queue
    # For now, we'll just log that this operation would happen
    logger.info("Retry queue cleared (implementation would clear database entries)")


async def reset_statistics():
    """
    Reset delivery statistics
    Note: In a real implementation, this would reset statistics stored in the database
    """
    logger.info("Resetting delivery statistics...")

    # In a real implementation, this would reset statistics in the database
    # For now, we'll just log that this operation would happen
    logger.info("Delivery statistics reset (implementation would reset database counters)")


async def cleanup_all():
    """
    Perform all cleanup operations
    """
    logger.info("Starting comprehensive cleanup...")

    # Reset rate limits
    await reset_rate_limits()

    # Clear retry queue
    await clear_retry_queue()

    # Reset statistics
    await reset_statistics()

    logger.info("All cleanup operations completed")


async def main():
    """
    Main entry point for the cleanup script
    """
    logger.info("Starting Response Delivery Dispatcher cleanup")

    # Parse command line arguments
    operation = "full_cleanup"
    if len(sys.argv) > 1:
        operation = sys.argv[1].lower()

    try:
        if operation == "reset_rate_limits":
            await reset_rate_limits()
        elif operation == "clear_retry_queue":
            await clear_retry_queue()
        elif operation == "reset_stats":
            await reset_statistics()
        elif operation == "full_cleanup":
            await cleanup_all()
        else:
            print(f"Unknown operation: {operation}")
            print("Available operations: reset_rate_limits, clear_retry_queue, reset_stats, full_cleanup")
            sys.exit(1)

        logger.info(f"Cleanup operation '{operation}' completed successfully")

    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())