from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any

from app.services.ingestion_service import ingestion_service
from app.config.security import verify_web_form_api_key

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/support-form")
async def web_support_form(request: Request, background_tasks: BackgroundTasks):
    """
    Handle incoming support requests from the web form

    Expected JSON payload:
    - customer_email: The customer's email address
    - customer_name: The customer's name (optional)
    - customer_phone: The customer's phone number (optional)
    - subject: Subject of the support request
    - message: The main content of the message
    - priority: Priority level of the request (low, medium, high, critical)
    - attachments: Array of attachment objects (optional)
    """
    try:
        # Validate API key for security
        api_key = request.headers.get("X-API-Key")

        if not verify_web_form_api_key(api_key):
            logger.warning(f"Unauthorized access attempt to web form endpoint from {request.client.host}")
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key"
            )

        # Parse JSON payload
        try:
            payload = await request.json()
        except Exception as e:
            logger.error(f"Invalid JSON payload: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON payload"
            )

        # Validate required fields
        required_fields = ["customer_email", "message"]
        for field in required_fields:
            if field not in payload or not payload[field]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {field}"
                )

        # Process the message asynchronously to return response quickly
        background_tasks.add_task(process_webform_message, payload)

        # Return success response immediately
        return JSONResponse(
            status_code=200,
            content={
                "status": "received",
                "ticket_id": payload.get('submission_id', 'generated_on_process')
            }
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing web form: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


async def process_webform_message(payload: Dict[str, Any]):
    """
    Process the web form message in the background

    Args:
        payload: The JSON payload from the web form
    """
    try:
        logger.info(f"Processing web form submission from: {payload.get('customer_email', 'unknown')}")

        # Process the message through the ingestion pipeline
        result = await ingestion_service.ingest_webform_message(payload)

        if result.get("success"):
            logger.info(f"Web form message from {payload.get('customer_email')} processed successfully")
        else:
            logger.error(f"Failed to process web form message: {result.get('error')}")

    except Exception as e:
        logger.error(f"Background processing error for web form: {str(e)}", exc_info=True)


@router.get("/support-form")
async def webform_endpoint_info():
    """
    Information about the web form endpoint
    """
    return {
        "endpoint": "/api/v1/support-form",
        "method": "POST",
        "description": "Submit support requests via web form",
        "authentication": "X-API-Key header required",
        "required_fields": ["customer_email", "message"]
    }