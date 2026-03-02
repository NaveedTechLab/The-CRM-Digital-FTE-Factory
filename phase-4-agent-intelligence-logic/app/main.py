import asyncio
import logging
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from typing import Dict, Any
from app.config.settings import settings
from app.services.agent_orchestrator import agent_orchestrator
from app.services.kafka_service import kafka_service
from app.services.rag_service import rag_service

# Configure logging
logging.basicConfig(level=logging.INFO if not settings.DEBUG else logging.DEBUG)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan manager for the FastAPI application
    """
    logger.info("Starting up Customer Success Agent...")

    # Initialize services
    try:
        # Initialize RAG service (index knowledge base if needed)
        logger.info("Initializing RAG service...")
        # rag_service.index_knowledge_base()  # Uncomment if you need to index on startup

        # Connect to Kafka
        logger.info("Connecting to Kafka...")
        await kafka_service.connect_producer()

        logger.info("Services initialized successfully")

        # Start Kafka consumer listener in background
        logger.info("Starting agent orchestrator in background...")
        asyncio.create_task(agent_orchestrator.start_listening())

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

    yield  # Application runs here

    # Cleanup
    logger.info("Shutting down Customer Success Agent...")
    try:
        await kafka_service.disconnect_consumer()
        await kafka_service.disconnect_producer()
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Customer Success Agent using OpenAI Agents SDK",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {"message": "Customer Success Agent is running"}

@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify the agent is operational
    """
    health_status = {
        "status": "operational",
        "timestamp": "2023-01-01T00:00:00Z",
        "services": {
            "kafka_consumer": "connected" if kafka_service.consumer else "disconnected",
            "kafka_producer": "connected" if kafka_service.producer else "disconnected",
            "openai_api": "assumed_available",  # We don't constantly check OpenAI
            "database": "assumed_connected",    # We don't constantly check DB
            "rag_service": "ready"              # Assumed ready if app started
        }
    }
    return health_status

@app.post("/process-message")
async def process_message(message_data: Dict[str, Any]):
    """
    Manually trigger processing of a customer message (primarily for testing)
    """
    try:
        # Process the message synchronously for immediate response
        await agent_orchestrator.process_inbound_message(message_data)

        # For this endpoint, we'll return a simplified response
        # In a real implementation, you might want to return the actual agent response
        return {
            "success": True,
            "message": "Message processed successfully",
            "conversation_id": message_data.get("conversation_id", "unknown")
        }
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@app.get("/metrics")
async def get_metrics():
    """
    Retrieve operational metrics for the Customer Success Agent
    """
    # In a real implementation, these would come from actual metrics collection
    # For now, returning sample data
    return {
        "total_messages_processed": 1250,
        "messages_per_channel": {
            "gmail": 450,
            "whatsapp": 550,
            "webform": 250
        },
        "average_response_time_ms": 2450.5,
        "escalation_rate": 0.15,
        "average_confidence_score": 0.82,
        "knowledge_base_hit_rate": 0.78,
        "successful_resolutions": 1063
    }

@app.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    Retrieve the history of a specific conversation (for debugging)
    """
    # In a real implementation, this would retrieve conversation history from the database
    # For now, returning sample data
    return {
        "conversation_id": conversation_id,
        "messages": [
            {
                "id": "msg-12345",
                "role": "customer",
                "content": "I'm having trouble with the login functionality",
                "timestamp": "2023-01-01T12:00:00Z",
                "confidence_score": 0.85
            },
            {
                "id": "msg-12346",
                "role": "agent",
                "content": "I understand you're having trouble with login. Have you tried clearing your browser cache?",
                "timestamp": "2023-01-01T12:01:00Z",
                "confidence_score": 0.85
            }
        ],
        "status": "active"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )