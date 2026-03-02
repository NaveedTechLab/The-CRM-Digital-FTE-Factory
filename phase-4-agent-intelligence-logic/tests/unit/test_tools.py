import pytest
from unittest.mock import AsyncMock, patch
from app.tools.get_customer_history_tool import get_customer_history_tool, GetCustomerHistoryInput
from app.tools.create_ticket_tool import create_ticket_tool, CreateTicketInput
from app.tools.search_kb_tool import search_kb_tool, SearchKBInput
from app.tools.escalate_tool import escalate_tool, EscalateInput

class TestGetCustomerHistoryTool:
    @pytest.mark.asyncio
    async def test_get_customer_history_success(self):
        with patch('app.tools.get_customer_history_tool.customer_history_service') as mock_service:
            mock_service.get_customer_history = AsyncMock(return_value={
                "customer_id": "test_id",
                "total_interactions": 5
            })

            input_data = GetCustomerHistoryInput(customer_id="test_id")
            result = await get_customer_history_tool(input_data)

            assert result["success"] is True
            assert "customer_history" in result
            assert result["customer_history"]["customer_id"] == "test_id"

    @pytest.mark.asyncio
    async def test_get_customer_history_failure(self):
        with patch('app.tools.get_customer_history_tool.customer_history_service') as mock_service:
            mock_service.get_customer_history = AsyncMock(side_effect=Exception("DB Error"))

            input_data = GetCustomerHistoryInput(customer_id="test_id")
            result = await get_customer_history_tool(input_data)

            assert result["success"] is False
            assert "error" in result

class TestCreateTicketTool:
    @pytest.mark.asyncio
    async def test_create_ticket_success(self):
        input_data = CreateTicketInput(
            customer_id="test_id",
            title="Test Ticket",
            description="Test Description"
        )

        result = await create_ticket_tool(input_data)

        assert result["success"] is True
        assert "ticket_id" in result
        assert result["result"]["customer_id"] == "test_id"

    @pytest.mark.asyncio
    async def test_create_ticket_with_priority(self):
        input_data = CreateTicketInput(
            customer_id="test_id",
            title="Test Ticket",
            description="Test Description",
            priority="high"
        )

        result = await create_ticket_tool(input_data)

        assert result["result"]["priority"] == "high"

class TestSearchKBTool:
    @pytest.mark.asyncio
    async def test_search_kb_success(self):
        with patch('app.tools.search_kb_tool.rag_service') as mock_service:
            mock_results = [{"id": "test_id", "title": "Test Article", "content": "Test content"}]
            mock_service.get_relevant_context.return_value = mock_results

            input_data = SearchKBInput(query="test query")
            result = await search_kb_tool(input_data)

            assert result["success"] is True
            assert result["results"] == mock_results

    @pytest.mark.asyncio
    async def test_search_kb_failure(self):
        with patch('app.tools.search_kb_tool.rag_service') as mock_service:
            mock_service.get_relevant_context.side_effect = Exception("Search Error")

            input_data = SearchKBInput(query="test query")
            result = await search_kb_tool(input_data)

            assert result["success"] is False
            assert "error" in result

class TestEscalateTool:
    @pytest.mark.asyncio
    async def test_escalate_success(self):
        input_data = EscalateInput(
            customer_id="test_id",
            reason="Test reason",
            message_content="Test message"
        )

        result = await escalate_tool(input_data)

        assert result["success"] is True
        assert "escalation_id" in result
        assert result["result"]["customer_id"] == "test_id"