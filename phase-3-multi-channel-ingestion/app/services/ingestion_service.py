import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.models.inbound_message import InboundMessage
from app.services.message_normalizer import message_normalizer
from app.services.identity_resolver import identity_resolver
from app.services.kafka_producer import kafka_producer
from app.config.settings import settings


class IngestionService:
    """Core ingestion service that orchestrates the Receive -> Normalize -> Identify -> Publish flow"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def process_inbound_message(self, raw_payload: Dict[str, Any], channel_type: str) -> Dict[str, Any]:
        """
        Process an inbound message through the complete ingestion pipeline:
        Receive -> Normalize -> Identify -> Publish

        Args:
            raw_payload: The raw message payload from the channel
            channel_type: The type of channel (gmail, whatsapp, webform)

        Returns:
            Dictionary with processing results
        """
        try:
            # Step 1: Normalize the message
            self.logger.info(f"Starting ingestion process for {channel_type} message")

            normalized_message = message_normalizer.normalize_message(raw_payload, channel_type)
            normalized_message.processed_status = "normalized"

            self.logger.info(f"Message normalized successfully for {normalized_message.sender_id}")

            # Step 2: Identify the customer
            identity_result = await identity_resolver.get_or_create_customer(
                sender_id=normalized_message.sender_id,
                channel=channel_type,
                customer_name=normalized_message.customer_name
            )

            # Link the customer to the message
            normalized_message.customer_identifier = identity_result.get("customer_id")
            normalized_message.processed_status = "identified"

            self.logger.info(f"Customer identity resolved: {identity_result}")

            # Step 3: Publish to Kafka
            kafka_event = await kafka_producer.send_message(
                topic=settings.kafka_topic_inbound_events,
                message=normalized_message.dict(),
                key=normalized_message.sender_id
            )

            normalized_message.processed_status = "published"

            self.logger.info(f"Message published to Kafka topic: {settings.kafka_topic_inbound_events}")

            # Return success result
            return {
                "success": True,
                "message_id": normalized_message.id,
                "customer_id": identity_result.get("customer_id"),
                "created_new_customer": identity_result.get("created_new", False),
                "kafka_event": kafka_event.dict(),
                "processed_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error in ingestion pipeline: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "processed_at": datetime.utcnow().isoformat()
            }

    async def ingest_gmail_message(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest a Gmail message"""
        return await self.process_inbound_message(raw_payload, "gmail")

    async def ingest_whatsapp_message(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest a WhatsApp message"""
        return await self.process_inbound_message(raw_payload, "whatsapp")

    async def ingest_webform_message(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest a Web Form message"""
        return await self.process_inbound_message(raw_payload, "webform")


# Global ingestion service instance
ingestion_service = IngestionService()