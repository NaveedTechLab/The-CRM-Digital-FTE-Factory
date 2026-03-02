#!/usr/bin/env python3
"""
Start script for the Response Delivery Dispatcher service
"""

import asyncio
import signal
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.response_dispatcher import ResponseDispatcher, initialize_dispatcher
from app.config.settings import settings
from app.utils.logger import logger


class DispatcherRunner:
    """
    Runner class to manage the lifecycle of the response dispatcher
    """

    def __init__(self):
        """
        Initialize the dispatcher runner
        """
        self.dispatcher = ResponseDispatcher(
            kafka_bootstrap_servers=settings.kafka_bootstrap_servers,
            database_url=settings.database_url
        )
        self.running = False

    async def initialize(self):
        """
        Initialize the dispatcher
        """
        logger.info("Initializing Response Dispatcher...")
        await initialize_dispatcher()
        logger.info("Response Dispatcher initialized successfully")

    async def run(self, topic: str = 'outbound_responses'):
        """
        Run the dispatcher service

        Args:
            topic: Kafka topic to consume from (default: 'outbound_responses')
        """
        self.running = True

        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.running = False

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        try:
            logger.info(f"Starting Response Dispatcher for topic: {topic}")

            # Initialize the dispatcher
            await self.initialize()

            # Start the consumer
            await self.dispatcher.start_consumer(topic)

        except Exception as e:
            logger.error(f"Error running dispatcher: {str(e)}", error=str(e))
            raise
        finally:
            await self.shutdown()

    async def shutdown(self):
        """
        Perform graceful shutdown
        """
        logger.info("Shutting down Response Dispatcher...")

        if self.dispatcher:
            await self.dispatcher.stop()

        logger.info("Response Dispatcher shutdown complete")


async def main():
    """
    Main entry point - starts both the FastAPI server and Kafka consumer
    """
    import uvicorn

    runner = DispatcherRunner()

    try:
        # Get topic from command line argument or use default
        topic = 'outbound_responses'
        if len(sys.argv) > 1:
            topic = sys.argv[1]

        # Start FastAPI server in background
        config = uvicorn.Config(
            "app.main:app",
            host=settings.host,
            port=settings.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        api_task = asyncio.create_task(server.serve())

        # Start the Kafka dispatcher
        dispatcher_task = asyncio.create_task(runner.run(topic=topic))

        # Wait for either to complete (or fail)
        done, pending = await asyncio.wait(
            [api_task, dispatcher_task],
            return_when=asyncio.FIRST_EXCEPTION
        )

        for task in pending:
            task.cancel()

    except KeyboardInterrupt:
        logger.info("Dispatcher interrupted by user")
        await runner.shutdown()
    except Exception as e:
        logger.error(f"Fatal error in dispatcher: {str(e)}", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())