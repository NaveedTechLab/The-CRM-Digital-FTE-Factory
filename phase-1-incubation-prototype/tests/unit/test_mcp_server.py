"""
Tests for MCP Server tools.
Validates all 6 tools: search_knowledge_base, create_ticket, get_customer_history,
escalate_to_human, send_response, analyze_sentiment.
"""

import pytest
from app.mcp_server import (
    search_knowledge_base,
    create_ticket,
    get_customer_history,
    escalate_to_human,
    send_response,
    analyze_sentiment,
    list_tools,
    call_tool,
)


class TestMCPToolRegistry:
    """Test the MCP tool registry and call_tool dispatcher."""

    def test_list_tools_returns_6_tools(self):
        tools = list_tools()
        assert len(tools) == 6
        tool_names = {t["name"] for t in tools}
        assert tool_names == {
            "search_knowledge_base",
            "create_ticket",
            "get_customer_history",
            "escalate_to_human",
            "send_response",
            "analyze_sentiment",
        }

    def test_all_tools_have_description(self):
        for tool in list_tools():
            assert tool["description"], f"Tool {tool['name']} has no description"

    @pytest.mark.asyncio
    async def test_call_tool_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown tool"):
            await call_tool("nonexistent_tool", {})

    @pytest.mark.asyncio
    async def test_call_tool_dispatches_correctly(self):
        result = await call_tool("analyze_sentiment", {"text": "I love this product!"})
        assert "sentiment_score" in result


class TestSearchKnowledgeBase:
    """Test the search_knowledge_base tool."""

    @pytest.mark.asyncio
    async def test_search_returns_results_for_known_query(self):
        result = await search_knowledge_base("how to reset my password")
        assert result["total_matches"] > 0
        assert any("Password" in r["title"] for r in result["results"])

    @pytest.mark.asyncio
    async def test_search_max_5_results(self):
        result = await search_knowledge_base("project flow help support product")
        assert len(result["results"]) <= 5

    @pytest.mark.asyncio
    async def test_search_no_results_for_gibberish(self):
        result = await search_knowledge_base("xyzzy12345")
        assert result["total_matches"] == 0

    @pytest.mark.asyncio
    async def test_search_results_sorted_by_relevance(self):
        result = await search_knowledge_base("pricing cost plan subscription")
        if len(result["results"]) > 1:
            scores = [r["relevance_score"] for r in result["results"]]
            assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_search_returns_required_fields(self):
        result = await search_knowledge_base("getting started")
        for r in result["results"]:
            assert "id" in r
            assert "title" in r
            assert "content" in r
            assert "relevance_score" in r


class TestCreateTicket:
    """Test the create_ticket tool."""

    @pytest.mark.asyncio
    async def test_create_ticket_success(self):
        result = await create_ticket(
            customer_id="customer-001",
            issue="Cannot login to account",
            priority="high",
            channel="gmail",
        )
        assert result["status"] == "created"
        assert result["ticket_id"].startswith("TKT-")
        assert result["priority"] == "high"
        assert result["channel"] == "gmail"

    @pytest.mark.asyncio
    async def test_create_ticket_default_priority(self):
        result = await create_ticket(
            customer_id="customer-001",
            issue="General question",
        )
        assert result["status"] == "created"

    @pytest.mark.asyncio
    async def test_create_ticket_unique_ids(self):
        r1 = await create_ticket(customer_id="c1", issue="issue1")
        r2 = await create_ticket(customer_id="c2", issue="issue2")
        assert r1["ticket_id"] != r2["ticket_id"]


class TestGetCustomerHistory:
    """Test the get_customer_history tool."""

    @pytest.mark.asyncio
    async def test_known_customer_by_id(self):
        result = await get_customer_history("customer-001")
        assert result["found"] is True
        assert result["name"] == "Alice Johnson"
        assert len(result["interactions"]) > 0

    @pytest.mark.asyncio
    async def test_known_customer_by_email(self):
        result = await get_customer_history("alice@example.com")
        assert result["found"] is True
        assert result["name"] == "Alice Johnson"

    @pytest.mark.asyncio
    async def test_unknown_customer(self):
        result = await get_customer_history("unknown-999")
        assert result["found"] is False
        assert result["interactions"] == []

    @pytest.mark.asyncio
    async def test_cross_channel_history(self):
        result = await get_customer_history("customer-002")
        assert result["found"] is True
        assert len(result["channels_used"]) >= 2
        assert result["total_interactions"] >= 2


class TestEscalateToHuman:
    """Test the escalate_to_human tool."""

    @pytest.mark.asyncio
    async def test_escalation_success(self):
        ticket = await create_ticket(customer_id="c1", issue="Need refund")
        result = await escalate_to_human(
            ticket_id=ticket["ticket_id"],
            reason="Customer requesting refund",
            urgency="priority",
        )
        assert result["escalation_id"].startswith("ESC-")
        assert result["urgency"] == "priority"
        assert result["estimated_response"] == "1 hour"

    @pytest.mark.asyncio
    async def test_escalation_levels(self):
        for level, expected_time in [
            ("standard", "4 hours"),
            ("priority", "1 hour"),
            ("urgent", "30 minutes"),
            ("critical", "15 minutes"),
        ]:
            result = await escalate_to_human(
                ticket_id="TKT-TEST",
                reason="Test",
                urgency=level,
            )
            assert result["estimated_response"] == expected_time


class TestSendResponse:
    """Test the send_response tool."""

    @pytest.mark.asyncio
    async def test_send_via_gmail(self):
        ticket = await create_ticket(customer_id="c1", issue="test")
        result = await send_response(
            ticket_id=ticket["ticket_id"],
            message="We can help you with that.",
            channel="gmail",
        )
        assert result["delivery_status"] == "sent"
        assert result["channel"] == "gmail"

    @pytest.mark.asyncio
    async def test_send_via_whatsapp(self):
        result = await send_response(
            ticket_id="TKT-TEST",
            message="Quick answer for you!",
            channel="whatsapp",
        )
        assert result["delivery_status"] == "sent"
        assert result["channel"] == "whatsapp"

    @pytest.mark.asyncio
    async def test_send_via_webform(self):
        result = await send_response(
            ticket_id="TKT-TEST",
            message="Thank you for reaching out.",
            channel="webform",
        )
        assert result["delivery_status"] == "sent"

    @pytest.mark.asyncio
    async def test_whatsapp_truncation(self):
        long_msg = "A" * 500
        result = await send_response(
            ticket_id="TKT-TEST",
            message=long_msg,
            channel="whatsapp",
        )
        assert result["formatted_length"] <= 303  # 300 + "..."


class TestAnalyzeSentiment:
    """Test the analyze_sentiment tool."""

    @pytest.mark.asyncio
    async def test_positive_sentiment(self):
        result = await analyze_sentiment("Thank you so much! This is great!")
        assert result["sentiment_score"] > 0.5
        assert result["sentiment_label"] in ("positive", "neutral")

    @pytest.mark.asyncio
    async def test_negative_sentiment(self):
        result = await analyze_sentiment("This is terrible and ridiculous! I hate this service!")
        assert result["sentiment_score"] < 0.5
        assert result["sentiment_label"] in ("very_negative", "negative")

    @pytest.mark.asyncio
    async def test_very_negative_triggers_escalation(self):
        result = await analyze_sentiment("I will sue you! This is unacceptable! Call my lawyer!")
        assert result["sentiment_score"] < 0.3
        assert result["recommendation"] == "escalate_immediately"

    @pytest.mark.asyncio
    async def test_neutral_sentiment(self):
        result = await analyze_sentiment("I have a question about your product.")
        assert 0.3 <= result["sentiment_score"] <= 0.8

    @pytest.mark.asyncio
    async def test_caps_detection(self):
        result = await analyze_sentiment("THIS IS COMPLETELY BROKEN AND UNUSABLE")
        assert result["signals_detected"]["caps_ratio"] > 0.5

    @pytest.mark.asyncio
    async def test_exclamation_detection(self):
        result = await analyze_sentiment("Fix this now!!!")
        assert result["signals_detected"]["exclamation_count"] >= 3

    @pytest.mark.asyncio
    async def test_empty_message(self):
        result = await analyze_sentiment("")
        assert "sentiment_score" in result
        assert 0.0 <= result["sentiment_score"] <= 1.0
