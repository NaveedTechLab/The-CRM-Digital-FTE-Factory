#!/usr/bin/env python3
"""
Agent service startup script
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.main import app
from app.services.agent_orchestrator import agent_orchestrator
from app.config.settings import settings

def setup_logging():
    """Setup logging configuration"""
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

async def main():
    """Main entry point for the agent service"""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting Customer Success Agent...")
    logger.info(f"App: {settings.APP_NAME}")
    logger.info(f"Environment: {'development' if settings.DEBUG else 'production'}")

    try:
        # Start the agent orchestrator to listen for Kafka messages
        await agent_orchestrator.start_listening()

    except KeyboardInterrupt:
        logger.info("Received interrupt signal. Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Unexpected error in agent service: {e}")
        raise
    finally:
        logger.info("Agent service stopped.")

if __name__ == "__main__":
    asyncio.run(main())