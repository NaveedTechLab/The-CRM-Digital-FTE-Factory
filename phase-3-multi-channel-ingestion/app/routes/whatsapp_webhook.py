from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse, PlainTextResponse
import logging
import hashlib
import hmac
from typing import Dict, Any

from app.services.ingestion_service import ingestion_service
from app.config.settings import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/meta-whatsapp")
async def whatsapp_webhook_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    """
    Meta WhatsApp Cloud API webhook verification (GET request)
    Meta sends this to verify the webhook URL
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_webhook_verify_token:
        logger.info("WhatsApp webhook verified successfully")
        return PlainTextResponse(content=hub_challenge)

    logger.warning(f"WhatsApp webhook verification failed. token={hub_verify_token}")
    raise HTTPException(status_code=403, detail="Webhook verification failed")


@router.post("/meta-whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Handle incoming WhatsApp messages from Meta Cloud API

    Meta payload format:
    {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "value": {
                    "contacts": [{"profile": {"name": "..."}, "wa_id": "..."}],
                    "messages": [{
                        "from": "PHONE",
                        "id": "MSG_ID",
                        "text": {"body": "MESSAGE"},
                        "type": "text",
                        "timestamp": "..."
                    }]
                }
            }]
        }]
    }
    """
    try:
        body = await request.json()

        # Verify it's a WhatsApp message
        if body.get("object") != "whatsapp_business_account":
            return JSONResponse(status_code=200, content={"status": "not_whatsapp"})

        # Process each entry
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                contacts = value.get("contacts", [])

                # Get contact name mapping
                contact_map = {}
                for contact in contacts:
                    contact_map[contact.get("wa_id")] = contact.get("profile", {}).get("name", "Unknown")

                for message in messages:
                    msg_type = message.get("type")

                    # Only process text messages for now
                    if msg_type != "text":
                        logger.info(f"Skipping non-text message type: {msg_type}")
                        continue

                    phone = message.get("from")
                    msg_id = message.get("id")
                    text = message.get("text", {}).get("body", "")
                    customer_name = contact_map.get(phone, "WhatsApp User")

                    meta_data = {
                        "From": f"whatsapp:+{phone}",
                        "Body": text,
                        "MessageSid": msg_id,
                        "ProfileName": customer_name,
                        "WaId": phone,
                        "source": "meta_cloud_api"
                    }

                    background_tasks.add_task(process_whatsapp_message, meta_data)
                    logger.info(f"WhatsApp message queued from {phone}: {text[:50]}")

        return JSONResponse(status_code=200, content={"status": "received"})

    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {str(e)}", exc_info=True)
        # Always return 200 to Meta (otherwise it will retry)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


async def process_whatsapp_message(form_data: Dict[str, Any]):
    """Process WhatsApp message through ingestion pipeline"""
    try:
        msg_id = form_data.get("MessageSid", "unknown")
        logger.info(f"Processing WhatsApp message: {msg_id}")

        result = await ingestion_service.ingest_whatsapp_message(form_data)

        if result.get("success"):
            logger.info(f"WhatsApp message {msg_id} processed successfully")
        else:
            logger.error(f"Failed to process WhatsApp message {msg_id}: {result.get('error')}")

    except Exception as e:
        logger.error(f"Background processing error for WhatsApp message: {str(e)}", exc_info=True)


# Keep old Twilio endpoint for backwards compatibility
@router.post("/twilio-whatsapp")
async def whatsapp_webhook_twilio(request: Request, background_tasks: BackgroundTasks):
    """Legacy Twilio webhook - redirects to same processing"""
    try:
        form_data = await request.form()
        form_dict = dict(form_data)
        background_tasks.add_task(process_whatsapp_message, form_dict)
        return JSONResponse(status_code=200, content={"status": "received"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/twilio-whatsapp")
async def whatsapp_webhook_challenge():
    return {"status": "webhook endpoint ready"}
