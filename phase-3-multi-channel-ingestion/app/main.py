from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routes import whatsapp_webhook, webform_endpoint, health_check
from app.services.kafka_producer import kafka_producer
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await kafka_producer.connect()
        logger.info("Kafka producer connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect Kafka producer on startup: {e}")
    yield
    # Shutdown
    await kafka_producer.disconnect()


app = FastAPI(
    title="Multi-Channel Ingestion API",
    description="API for ingesting customer messages from multiple channels (WhatsApp, Gmail, Web Form) into the Customer Success Digital FTE system",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(whatsapp_webhook.router, prefix="/webhooks", tags=["whatsapp"])
app.include_router(webform_endpoint.router, prefix="/api/v1", tags=["support"])
app.include_router(health_check.router, tags=["health"])

@app.get("/")
async def root():
    return {"message": "Multi-Channel Ingestion Service is running"}