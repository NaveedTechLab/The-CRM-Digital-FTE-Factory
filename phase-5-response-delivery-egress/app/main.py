from fastapi import FastAPI, HTTPException, Depends
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
import uvicorn
from .config.settings import settings
from .services.response_dispatcher import initialize_dispatcher, start_dispatcher
from .services.gmail_service import initialize_gmail_service
from .services.whatsapp_service import initialize_whatsapp_service, get_whatsapp_service
from .services.rate_limiter import get_rate_limiter
from .services.delivery_tracker import get_delivery_tracker
from .utils.logger import logger

# Create FastAPI app
app = FastAPI(
    title="Response Delivery Dispatcher API",
    description="API for the Response Delivery Dispatcher system that handles outbound customer messages",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """
    Initialize services on startup
    """
    logger.info("Starting up Response Delivery Service")

    # Initialize the response dispatcher
    await initialize_dispatcher()

    # Initialize services
    await initialize_gmail_service()
    await initialize_whatsapp_service()

    logger.info("All services initialized successfully")

    # Start Kafka consumer loop in background
    asyncio.create_task(start_dispatcher())


@app.get("/dispatcher/status", summary="Dispatcher status check")
async def get_dispatcher_status():
    """
    Check the operational status of the Response Delivery Dispatcher
    """
    rate_limiter = get_rate_limiter()
    delivery_tracker = get_delivery_tracker()

    # Check service statuses
    try:
        gmail_status = await rate_limiter.get_channel_status('gmail')
        whatsapp_status = await rate_limiter.get_channel_status('whatsapp')
        webform_status = await rate_limiter.get_channel_status('webform')

        status = {
            "status": "operational",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "services": {
                "database": "connected",  # Assuming DB connection is working if we get here
                "gmail_service": "available" if gmail_status else "unavailable",
                "whatsapp_service": "available" if whatsapp_status else "unavailable",
                "webform_service": "available" if webform_status else "unavailable",
                "rate_limiter": "ready"
            }
        }

        return status
    except Exception as e:
        logger.error(f"Error getting dispatcher status: {str(e)}", error=str(e))
        raise HTTPException(status_code=500, detail="Unable to check dispatcher status")


@app.get("/dispatcher/delivery-status/{message_id}", summary="Get delivery status")
async def get_delivery_status(message_id: str):
    """
    Retrieve the delivery status for a specific outbound message
    """
    delivery_tracker = get_delivery_tracker()

    try:
        status_info = await delivery_tracker.get_message_status(message_id)

        if not status_info:
            raise HTTPException(status_code=404, detail="Message not found")

        return status_info
    except Exception as e:
        logger.error(f"Error getting delivery status: {str(e)}", error=str(e), message_id=message_id)
        raise HTTPException(status_code=500, detail="Unable to get delivery status")


@app.get("/dispatcher/channel-config", summary="Get channel configurations")
async def get_channel_configs():
    """
    Retrieve current configuration for all delivery channels
    """
    from .config.channel_configs import get_channel_config_manager

    try:
        config_manager = get_channel_config_manager()
        all_configs = config_manager.get_all_default_configs()

        channels_info = []
        rate_limiter = get_rate_limiter()

        for channel_type, config in all_configs.items():
            # Get current rate limit status for each channel
            try:
                rate_status = await rate_limiter.get_channel_status(channel_type)
                status = "available" if not rate_status.get("is_limited") else "limited"
            except:
                status = "unavailable"

            channels_info.append({
                "channel_type": channel_type,
                "enabled": config['enabled'],
                "rate_limit": {
                    "requests_per_minute": config['rate_limit_requests'],
                    "burst_limit": config['burst_limit']
                },
                "status": status
            })

        return {"channels": channels_info}
    except Exception as e:
        logger.error(f"Error getting channel configurations: {str(e)}", error=str(e))
        raise HTTPException(status_code=500, detail="Unable to get channel configurations")


@app.put("/dispatcher/channel-config", summary="Update channel configuration")
async def update_channel_config(
    channel_type: str,
    enabled: Optional[bool] = None,
    requests_per_minute: Optional[int] = None,
    burst_limit: Optional[int] = None
):
    """
    Update configuration for a specific delivery channel
    """
    from .config.channel_configs import get_channel_config_manager

    try:
        config_manager = get_channel_config_manager()

        # Validate channel type
        if channel_type not in ['gmail', 'whatsapp', 'webform']:
            raise HTTPException(status_code=400, detail="Invalid channel type")

        # Prepare updates
        updates = {}
        if enabled is not None:
            updates['enabled'] = enabled
        if requests_per_minute is not None:
            updates['rate_limit_requests'] = requests_per_minute
        if burst_limit is not None:
            updates['burst_limit'] = burst_limit

        # Update the configuration
        config_manager.update_default_config(channel_type, **updates)

        return {"success": True}
    except Exception as e:
        logger.error(f"Error updating channel configuration: {str(e)}", error=str(e))
        raise HTTPException(status_code=500, detail="Unable to update channel configuration")


@app.get("/dispatcher/retry-queue", summary="Get retry queue status")
async def get_retry_queue_status(
    channel: Optional[str] = None,
    limit: Optional[int] = 100
):
    """
    Retrieve the status and contents of the retry queue
    """
    delivery_tracker = get_delivery_tracker()

    try:
        # Get pending retries
        retry_items = await delivery_tracker.get_pending_retries()

        # Filter by channel if specified
        if channel:
            if channel not in ['gmail', 'whatsapp', 'webform']:
                raise HTTPException(status_code=400, detail="Invalid channel type")
            retry_items = [item for item in retry_items if item.channel_type == channel]

        # Limit results
        retry_items = retry_items[:limit]

        # Convert to dict format
        queued_items = []
        for item in retry_items:
            queued_items.append({
                "message_id": item.outbound_message_id,
                "channel": item.channel_type,  # This should be extracted differently
                "scheduled_retry": item.scheduled_retry.isoformat() + "Z",
                "attempt_number": item.attempt_number,
                "failure_reason": item.failure_reason
            })

        # Get rate limit info
        rate_limiter = get_rate_limiter()
        rate_limits = {}
        for ch_type in ['gmail', 'whatsapp', 'webform']:
            try:
                rate_status = await rate_limiter.get_channel_status(ch_type)
                rate_limits[ch_type] = {
                    "remaining": rate_status.get("remaining_requests", 0),
                    "reset_time": rate_status.get("reset_time", "")
                }
            except:
                rate_limits[ch_type] = {"remaining": 0, "reset_time": ""}

        return {
            "total_items": len(queued_items),
            "queued_items": queued_items,
            "rate_limits": rate_limits
        }
    except Exception as e:
        logger.error(f"Error getting retry queue status: {str(e)}", error=str(e))
        raise HTTPException(status_code=500, detail="Unable to get retry queue status")


@app.get("/dispatcher/metrics", summary="Dispatcher metrics")
async def get_dispatcher_metrics():
    """
    Retrieve operational metrics for the Response Delivery Dispatcher
    """
    delivery_tracker = get_delivery_tracker()

    try:
        metrics = await delivery_tracker.get_metrics()
        metrics["timestamp"] = datetime.utcnow().isoformat() + "Z"
        return metrics
    except Exception as e:
        logger.error(f"Error getting dispatcher metrics: {str(e)}", error=str(e))
        raise HTTPException(status_code=500, detail="Unable to get dispatcher metrics")


@app.post("/dispatcher/cleanup", summary="Cleanup dispatcher")
async def cleanup_dispatcher(
    operation: str,
    force: bool = False
):
    """
    Perform cleanup operations for stress testing or shutdown
    """
    from .services.rate_limiter import get_rate_limiter
    delivery_tracker = get_delivery_tracker()

    try:
        rate_limiter = get_rate_limiter()
        details = ""

        if operation == "reset_rate_limits":
            for channel in ['gmail', 'whatsapp', 'webform']:
                await rate_limiter.reset_channel_limit(channel)
            details = "All rate limits reset"
        elif operation == "clear_retry_queue":
            removed_count = await delivery_tracker.clear_retry_queue()
            details = f"Retry queue cleared: {removed_count} items removed"
        elif operation == "reset_stats":
            success = await delivery_tracker.reset_delivery_stats()
            details = "Delivery statistics reset successfully" if success else "Failed to reset statistics"
        elif operation == "full_cleanup":
            for channel in ['gmail', 'whatsapp', 'webform']:
                await rate_limiter.reset_channel_limit(channel)
            removed_count = await delivery_tracker.clear_retry_queue()
            await delivery_tracker.reset_delivery_stats()
            details = f"Full cleanup complete: rate limits reset, {removed_count} retry items cleared, statistics reset"
        else:
            raise HTTPException(status_code=400, detail="Invalid operation")

        return {
            "success": True,
            "operation": operation,
            "details": details
        }
    except Exception as e:
        logger.error(f"Error performing cleanup: {str(e)}", error=str(e))
        raise HTTPException(status_code=500, detail="Unable to perform cleanup operation")


@app.get("/whatsapp/pending-responses/{phone}", summary="Get pending WhatsApp responses")
async def get_pending_whatsapp_responses(phone: str):
    """
    Retrieve pending WhatsApp responses for a phone number.
    When both Meta and Twilio delivery fail, responses are stored
    and can be retrieved via this endpoint.
    """
    ws = get_whatsapp_service()
    responses = ws.get_pending_responses(phone)
    if not responses:
        return {"phone": phone, "pending_count": 0, "responses": []}
    return {
        "phone": phone,
        "pending_count": len(responses),
        "responses": responses,
    }


@app.delete("/whatsapp/pending-responses/{phone}", summary="Clear pending WhatsApp responses")
async def clear_pending_whatsapp_responses(phone: str):
    """
    Clear pending WhatsApp responses after they have been retrieved.
    """
    ws = get_whatsapp_service()
    ws.clear_pending_responses(phone)
    return {"phone": phone, "cleared": True}


@app.get("/", summary="Root endpoint")
async def root():
    """
    Root endpoint for the API
    """
    return {
        "message": "Response Delivery Dispatcher API",
        "version": "1.0.0",
        "status": "operational"
    }


async def run_dispatcher():
    """
    Run the response dispatcher service
    """
    try:
        await start_dispatcher()
    except KeyboardInterrupt:
        logger.info("Dispatcher interrupted by user")
    except Exception as e:
        logger.error(f"Error running dispatcher: {str(e)}", error=str(e))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Response Delivery Dispatcher")
    parser.add_argument("--dispatcher-only", action="store_true",
                       help="Run only the dispatcher without the API server")
    args = parser.parse_args()

    if args.dispatcher_only:
        # Run only the dispatcher
        asyncio.run(run_dispatcher())
    else:
        # Run both the API server and dispatcher
        # Start the dispatcher in the background
        dispatcher_task = asyncio.create_task(run_dispatcher())

        # Run the API server
        uvicorn.run(
            "app.main:app",
            host=settings.host,
            port=settings.port,
            reload=False  # Set to True for development
        )