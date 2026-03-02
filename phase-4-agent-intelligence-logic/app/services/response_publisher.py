from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from typing import Dict, Any, Optional
import logging
from app.models.outbound_message import OutboundMessage, Base
from app.services.kafka_service import kafka_service
from app.config.settings import settings

logger = logging.getLogger(__name__)

class ResponsePublisher:
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    async def create_outbound_message(
        self,
        agent_message_id: str,
        conversation_id: str,
        response_type: str,
        content: str,
        channel_destination: str,
        recipient_id: str,
        confidence_score: float,
        kb_sources: Optional[list] = None,
        tools_used: Optional[list] = None,
        escalation_reason: Optional[str] = None,
        ticket_reference: Optional[str] = None
    ) -> OutboundMessage:
        """
        Create an outbound message in the database
        """
        try:
            db = self.SessionLocal()

            try:
                outbound_message = OutboundMessage(
                    agent_message_id=agent_message_id,
                    conversation_id=conversation_id,
                    response_type=response_type,
                    content=content,
                    channel_destination=channel_destination,
                    recipient_id=recipient_id,
                    confidence_score=confidence_score,
                    kb_sources=kb_sources or [],
                    tools_used=tools_used or [],
                    escalation_reason=escalation_reason,
                    ticket_reference=ticket_reference
                )

                db.add(outbound_message)
                db.commit()
                db.refresh(outbound_message)

                return outbound_message

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error creating outbound message: {e}")
            raise

    async def publish_response(
        self,
        agent_message_id: str,
        conversation_id: str,
        content: str,
        channel_destination: str,
        recipient_id: str,
        confidence_score: float,
        response_type: str = "answer",
        kb_sources: Optional[list] = None,
        tools_used: Optional[list] = None,
        escalation_reason: Optional[str] = None,
        ticket_reference: Optional[str] = None
    ):
        """
        Create and publish an outbound message to Kafka
        """
        try:
            # Create the outbound message in the database
            outbound_msg = await self.create_outbound_message(
                agent_message_id=agent_message_id,
                conversation_id=conversation_id,
                response_type=response_type,
                content=content,
                channel_destination=channel_destination,
                recipient_id=recipient_id,
                confidence_score=confidence_score,
                kb_sources=kb_sources,
                tools_used=tools_used,
                escalation_reason=escalation_reason,
                ticket_reference=ticket_reference
            )

            # Prepare the message for Kafka
            kafka_message = {
                "id": str(outbound_msg.id),
                "agent_message_id": outbound_msg.agent_message_id,
                "conversation_id": outbound_msg.conversation_id,
                "response_type": outbound_msg.response_type,
                "content": outbound_msg.content,
                "channel_destination": outbound_msg.channel_destination,
                "recipient_id": outbound_msg.recipient_id,
                "confidence_score": outbound_msg.confidence_score,
                "kb_sources": outbound_msg.kb_sources,
                "tools_used": outbound_msg.tools_used,
                "escalation_reason": outbound_msg.escalation_reason,
                "ticket_reference": outbound_msg.ticket_reference,
                "delivery_status": outbound_msg.delivery_status,
                "created_at": outbound_msg.created_at.isoformat()
            }

            # Publish to Kafka
            await kafka_service.publish_message(kafka_message)

            logger.info(f"Published response message to Kafka: {outbound_msg.id}")

            return outbound_msg

        except Exception as e:
            logger.error(f"Error publishing response: {e}")
            raise

    async def update_delivery_status(self, message_id: str, status: str, delivery_attempts: Optional[int] = None):
        """
        Update the delivery status of an outbound message
        """
        try:
            db = self.SessionLocal()

            try:
                # Find the message
                outbound_message = db.query(OutboundMessage).filter(
                    OutboundMessage.id == message_id
                ).first()

                if outbound_message:
                    outbound_message.delivery_status = status
                    if delivery_attempts is not None:
                        outbound_message.delivery_attempts = delivery_attempts

                    db.commit()
                    db.refresh(outbound_message)

                    logger.info(f"Updated delivery status for message {message_id} to {status}")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error updating delivery status: {e}")
            raise

# Global instance
response_publisher = ResponsePublisher()