import asyncio
from typing import Dict, Any, Optional
import logging
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.models.agent_message import AgentMessage, Base as AgentMessageBase
from app.models.outbound_message import Base as OutboundMessageBase
from app.models.knowledge_base_article import Base as KBBase
from app.models.customer_interaction_history import Base as HistoryBase
from app.models.agent_tool_call import Base as ToolCallBase
from app.models.escalation_record import Base as EscalationBase
from app.services.openai_agent import OpenAIAgent
from app.services.tool_interface import tool_interface
from app.services.rag_service import rag_service
from app.services.customer_history import customer_history_service
from app.services.response_publisher import response_publisher
from app.services.kafka_service import kafka_service
from app.utils.confidence_scoring import ConfidenceScorer
from app.config.settings import settings

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    def __init__(self):
        self.agent = OpenAIAgent()
        self.confidence_scorer = ConfidenceScorer()
        self.engine = create_engine(settings.DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        # Create all tables if they don't exist
        for base in [AgentMessageBase, OutboundMessageBase, KBBase, HistoryBase, ToolCallBase, EscalationBase]:
            base.metadata.create_all(self.engine)

    async def process_inbound_message(self, message_data: Dict[str, Any]):
        """
        Process an inbound message through the agent pipeline
        """
        try:
            # Extract message details (try multiple field names for compatibility)
            customer_id = message_data.get("customer_id") or message_data.get("customer_identifier") or message_data.get("sender_id", "unknown")
            message_content = message_data.get("message_content") or message_data.get("text_content", "")
            channel = message_data.get("channel")
            conversation_id = message_data.get("conversation_id", f"conv_{customer_id}_{int(datetime.now().timestamp())}")

            # Create a record of the inbound message
            agent_message = await self._create_agent_message(
                customer_id=customer_id,
                conversation_id=conversation_id,
                inbound_message_id=message_data.get("id"),
                message_type="customer_query",
                content=message_content,
                role="customer"
            )

            # Update message status to processing
            await self._update_message_status(agent_message.id, "processing")

            # Get customer history
            customer_history = await customer_history_service.get_customer_history(customer_id)

            # Get relevant knowledge base articles
            kb_results = rag_service.get_relevant_context(message_content)

            # Prepare context for the agent
            context = {
                "knowledge_base_results": kb_results,
                "customer_history": customer_history,
                "channel": channel
            }

            # Process the message with the OpenAI agent
            agent_response = await self.agent.process_message(
                message=message_content,
                customer_id=customer_id,
                conversation_id=conversation_id,
                context=context
            )

            # Evaluate confidence and determine if escalation is needed
            confidence_score = agent_response["confidence_score"]
            tools_used = agent_response["tools_used"]
            persona_used = agent_response["persona_used"]

            # Calculate final confidence considering multiple factors
            final_confidence = self.confidence_scorer.calculate_overall_confidence(
                agent_confidence=confidence_score,
                kb_relevance=[result["similarity_score"] for result in kb_results if "similarity_score" in result],
                tools_used=tools_used
            )

            # Check if escalation is needed
            escalation_needed = self.confidence_scorer.should_escalate(
                confidence_score=final_confidence,
                message_content=message_content,
                customer_sentiment=customer_history.get("sentiment_trend", "neutral")
            )

            if escalation_needed:
                # Handle escalation
                escalation_result = await self._handle_escalation(
                    customer_id=customer_id,
                    reason="Low confidence or escalation keywords detected",
                    message_content=message_content,
                    agent_message_id=str(agent_message.id)
                )

                # Update agent message with escalation flag
                await self._update_message_with_escalation(agent_message.id, True, final_confidence)

                # Create escalation response
                response_content = "Your issue has been escalated to a human support agent who will contact you shortly."
                response_type = "escalation"
            else:
                # Use agent's response
                response_content = agent_response["response"]
                response_type = "answer"

            # Update the agent message with response details
            await self._update_message_with_response(
                agent_message.id,
                response_content,
                final_confidence,
                [result["id"] for result in kb_results],
                escalation_needed
            )

            # Publish the response to outbound topic
            await response_publisher.publish_response(
                agent_message_id=str(agent_message.id),
                conversation_id=conversation_id,
                content=response_content,
                channel_destination=channel,
                recipient_id=self._get_recipient_id(customer_id, channel),
                confidence_score=final_confidence,
                response_type=response_type,
                kb_sources=[result["id"] for result in kb_results],
                tools_used=tools_used
            )

            # Update message status to processed
            status = "escalated" if escalation_needed else "processed"
            await self._update_message_status(agent_message.id, status)

            logger.info(f"Successfully processed message for customer {customer_id}. Escalation: {escalation_needed}")

        except Exception as e:
            logger.error(f"Error processing inbound message: {e}")
            # Update message status to failed
            if 'agent_message' in locals():
                await self._update_message_status(agent_message.id, "failed")
            raise

    async def _create_agent_message(
        self,
        customer_id: str,
        conversation_id: str,
        inbound_message_id: Optional[str],
        message_type: str,
        content: str,
        role: str
    ) -> AgentMessage:
        """
        Create an agent message record in the database
        """
        db = self.SessionLocal()

        try:
            agent_message = AgentMessage(
                customer_id=customer_id,
                conversation_id=conversation_id,
                inbound_message_id=inbound_message_id,
                message_type=message_type,
                content=content,
                role=role,
                confidence_score=None,  # Will be set after processing
                intents=[],  # Could be populated with NLP in the future
                entities={},  # Could be populated with NLP in the future
                kb_articles_used=[],
                escalation_flag=False,
                processed_status="received"
            )

            db.add(agent_message)
            db.commit()
            db.refresh(agent_message)

            return agent_message

        finally:
            db.close()

    async def _update_message_status(self, message_id: str, status: str):
        """
        Update the processing status of an agent message
        """
        db = self.SessionLocal()

        try:
            agent_message = db.query(AgentMessage).filter(AgentMessage.id == message_id).first()
            if agent_message:
                agent_message.processed_status = status
                db.commit()

        finally:
            db.close()

    async def _update_message_with_response(
        self,
        message_id: str,
        response_content: str,
        confidence_score: float,
        kb_articles_used: list,
        escalation_flag: bool
    ):
        """
        Update an agent message with response details
        """
        db = self.SessionLocal()

        try:
            agent_message = db.query(AgentMessage).filter(AgentMessage.id == message_id).first()
            if agent_message:
                agent_message.content = f"{agent_message.content}\n\nAgent Response: {response_content}"
                agent_message.confidence_score = confidence_score
                agent_message.kb_articles_used = kb_articles_used
                agent_message.escalation_flag = escalation_flag
                db.commit()

        finally:
            db.close()

    async def _update_message_with_escalation(self, message_id: str, escalation_flag: bool, confidence_score: float):
        """
        Update an agent message with escalation details
        """
        db = self.SessionLocal()

        try:
            agent_message = db.query(AgentMessage).filter(AgentMessage.id == message_id).first()
            if agent_message:
                agent_message.escalation_flag = escalation_flag
                agent_message.confidence_score = confidence_score
                db.commit()

        finally:
            db.close()

    async def _handle_escalation(self, customer_id: str, reason: str, message_content: str, agent_message_id: str):
        """
        Handle escalation to human support
        """
        # Use the escalate tool to create an escalation record
        escalation_result = await tool_interface.escalate(
            customer_id=customer_id,
            reason=reason,
            message_content=message_content
        )

        logger.info(f"Escalation initiated for customer {customer_id}: {escalation_result}")

        return escalation_result

    def _get_recipient_id(self, customer_id: str, channel: str) -> str:
        """
        Get the recipient ID based on customer ID and channel
        In a real implementation, this would look up the actual email/phone number
        """
        # This is a placeholder - in reality, you'd look up the actual contact info
        # based on the customer_id and channel from the customer database
        if channel == "gmail":
            return customer_id if "@" in customer_id else f"{customer_id}@example.com"
        elif channel == "whatsapp":
            # Extract phone from "whatsapp:+923001234567" or "mock-whatsapp:+923001234567"
            phone = customer_id.replace("mock-", "").replace("whatsapp:", "")
            return phone if phone.startswith("+") else f"+{phone}"
        else:
            return customer_id

    async def start_listening(self):
        """
        Start listening for inbound messages from Kafka
        """
        logger.info("Starting agent orchestrator...")

        # Connect to Kafka consumer and producer
        await kafka_service.connect_consumer()
        await kafka_service.connect_producer()

        while True:
            try:
                async for message in kafka_service.consume_messages():
                    await self.process_inbound_message(message)
            except KeyboardInterrupt:
                logger.info("Shutting down agent orchestrator...")
                break
            except Exception as e:
                logger.error(f"Error in agent orchestrator: {e}")
                logger.info("Restarting consumer in 5 seconds...")
                await asyncio.sleep(5)
                try:
                    await kafka_service.connect_consumer()
                except Exception as ce:
                    logger.error(f"Failed to reconnect consumer: {ce}")

# Global instance
agent_orchestrator = AgentOrchestrator()