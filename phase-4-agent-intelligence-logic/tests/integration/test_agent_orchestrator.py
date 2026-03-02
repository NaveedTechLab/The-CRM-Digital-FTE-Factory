import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.services.agent_orchestrator import AgentOrchestrator

@pytest.fixture
def agent_orchestrator():
    with patch('app.services.agent_orchestrator.OpenAIAgent'), \
         patch('app.services.agent_orchestrator.ConfidenceScorer'), \
         patch('app.services.agent_orchestrator.create_engine'), \
         patch('app.services.agent_orchestrator.sessionmaker'):
        return AgentOrchestrator()

class TestAgentOrchestrator:
    @pytest.mark.asyncio
    async def test_process_inbound_message(self, agent_orchestrator):
        # Mock all dependencies
        with patch.object(agent_orchestrator, '_create_agent_message') as mock_create_msg, \
             patch.object(agent_orchestrator, '_update_message_status'), \
             patch.object(agent_orchestrator, '_update_message_with_response'), \
             patch.object(agent_orchestrator, '_update_message_with_escalation'), \
             patch.object(agent_orchestrator, '_handle_escalation'), \
             patch('app.services.agent_orchestrator.customer_history_service') as mock_hist_service, \
             patch('app.services.agent_orchestrator.rag_service') as mock_rag_service, \
             patch('app.services.agent_orchestrator.response_publisher') as mock_publisher, \
             patch.object(agent_orchestrator.agent, 'process_message') as mock_process:

            # Mock return values
            mock_create_msg.return_value = AsyncMock(id="test_msg_id")
            mock_hist_service.get_customer_history.return_value = {"sentiment_trend": "neutral"}
            mock_rag_service.get_relevant_context.return_value = []
            mock_process.return_value = {
                "response": "Test response",
                "confidence_score": 0.9,
                "tools_used": [],
                "persona_used": "support"
            }

            message_data = {
                "customer_id": "test_customer",
                "message_content": "Hello, I need help",
                "channel": "gmail"
            }

            # This should not raise an exception
            await agent_orchestrator.process_inbound_message(message_data)

            # Verify the main methods were called
            mock_create_msg.assert_called_once()
            mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_agent_message(self, agent_orchestrator):
        with patch.object(agent_orchestrator, 'SessionLocal') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__enter__.return_value = mock_session
            mock_agent_message = AsyncMock()
            mock_agent_message.id = "test_id"
            mock_session.add.return_value = None
            mock_session.commit.return_value = None
            mock_session.refresh.return_value = None
            mock_session.query.return_value.filter.return_value.first.return_value = None

            result = await agent_orchestrator._create_agent_message(
                customer_id="test_customer",
                conversation_id="test_conv",
                inbound_message_id="test_inbound",
                message_type="customer_query",
                content="test content",
                role="customer"
            )

            assert result.id == "test_id"