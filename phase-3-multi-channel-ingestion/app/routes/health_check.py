from fastapi import APIRouter
from fastapi.responses import JSONResponse
import logging
from datetime import datetime
from typing import Dict, Any

from app.services.kafka_producer import kafka_producer
from app.config.settings import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check():
    """
    Health check endpoint to verify service status
    """
    try:
        # Check Kafka connectivity
        kafka_status = "connected" if kafka_producer.is_connected else "disconnected"

        # We could add more checks here (DB connectivity, etc.)
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "kafka": kafka_status,
                "database": "not_checked_yet",  # Would require DB connection check
                "gmail_api": "not_checked_yet"  # Would require Gmail API check
            },
            "version": "1.0.0"
        }

        return JSONResponse(content=health_status, status_code=200)

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return JSONResponse(
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            },
            status_code=500
        )


@router.get("/metrics")
async def get_metrics():
    """
    Get service metrics
    """
    # Placeholder metrics - in a real implementation, these would come from actual counters
    metrics = {
        "total_messages_processed": 0,
        "messages_per_channel": {
            "whatsapp": 0,
            "gmail": 0,
            "webform": 0
        },
        "avg_processing_time_ms": 0.0,
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": 0
    }

    return JSONResponse(content=metrics, status_code=200)


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint to verify service readiness
    """
    try:
        # For readiness, we might want to check that all critical services are available
        is_ready = kafka_producer.is_connected

        if is_ready:
            return JSONResponse(
                content={
                    "status": "ready",
                    "timestamp": datetime.utcnow().isoformat(),
                    "reason": "All critical services are available"
                },
                status_code=200
            )
        else:
            return JSONResponse(
                content={
                    "status": "not_ready",
                    "timestamp": datetime.utcnow().isoformat(),
                    "reason": "Kafka producer is not connected"
                },
                status_code=503
            )

    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}", exc_info=True)
        return JSONResponse(
            content={
                "status": "not_ready",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            },
            status_code=503
        )