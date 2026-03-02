#!/usr/bin/env python3
"""
Start Server Script for Multi-Channel Ingestion Service

This script initializes all required services and starts the FastAPI application.
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from uvicorn import Config, Server

from app.config.settings import settings
from app.services.kafka_producer import kafka_producer


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    # Startup
    print("Starting Multi-Channel Ingestion Service...")

    # Initialize Kafka producer
    try:
        await kafka_producer.connect()
        print("✓ Kafka producer connected")
    except Exception as e:
        print(f"✗ Failed to connect to Kafka: {e}")
        # Don't raise exception here as we want the server to start anyway
        # The service can still function but with limited capability

    yield

    # Shutdown
    print("Shutting down Multi-Channel Ingestion Service...")
    try:
        await kafka_producer.disconnect()
        print("✓ Kafka producer disconnected")
    except Exception as e:
        print(f"✗ Error disconnecting Kafka producer: {e}")


def create_app():
    """Create and configure the FastAPI application"""
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create FastAPI app with lifespan
    app = FastAPI(lifespan=lifespan)

    # Import and include routers
    from app.routes import whatsapp_webhook, webform_endpoint, health_check
    app.include_router(whatsapp_webhook.router, prefix="/webhooks", tags=["whatsapp"])
    app.include_router(webform_endpoint.router, prefix="/api/v1", tags=["support"])
    app.include_router(health_check.router, tags=["health"])

    @app.get("/")
    async def root():
        return {"message": "Multi-Channel Ingestion Service is running"}

    return app


async def main():
    """Main function to start the server"""
    app = create_app()

    config = Config(
        app=app,
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload in production
        log_level=settings.log_level.lower()
    )

    server = Server(config)

    print(f"Starting server on http://{config.host}:{config.port}")
    print(f"Log level: {settings.log_level}")

    try:
        await server.serve()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())