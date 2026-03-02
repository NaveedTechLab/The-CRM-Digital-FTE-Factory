import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.specialized_agent import SpecializedAgent
from app.agents.triage_agent import TriageAgent
from app.agents.knowledge_agent import KnowledgeAgent
from app.services.openai_agent import OpenAIAgent

@pytest.fixture
def specialized_agent():
    return SpecializedAgent()

@pytest.fixture
def triage_agent():
    return TriageAgent()

@pytest.fixture
def knowledge_agent():
    return KnowledgeAgent()

class TestSpecializedAgent:
    def test_get_persona_for_query_product_knowledge(self, specialized_agent):
        query = "How do I use the reporting feature?"
        persona = specialized_agent.get_persona_for_query(query)
        assert persona == "product_knowledge"

    def test_get_persona_for_query_triage(self, specialized_agent):
        query = "My account is broken and urgent!"
        persona = specialized_agent.get_persona_for_query(query)
        assert persona == "triage"

    def test_get_persona_for_query_support(self, specialized_agent):
        query = "I have a question about my subscription"
        persona = specialized_agent.get_persona_for_query(query)
        assert persona == "support"

    def test_get_system_prompt(self, specialized_agent):
        prompt = specialized_agent.get_system_prompt("support")
        assert "customer support agent" in prompt.lower()

    def test_get_available_personas(self, specialized_agent):
        personas = specialized_agent.get_available_personas()
        assert "support" in personas
        assert "product_knowledge" in personas
        assert "triage" in personas

class TestTriageAgent:
    def test_assess_issue_low_confidence_should_escalate(self, triage_agent):
        query = "I'm having trouble with login"
        customer_history = {
            "sentiment_trend": "neutral",
            "total_interactions": 1,
            "escalation_count": 0
        }
        result = triage_agent.assess_issue(query, customer_history, 0.5)  # Low confidence

        # With low confidence, it should escalate
        assert result["should_escalate"] is True

    def test_assess_issue_high_confidence_no_escalation(self, triage_agent):
        query = "Simple question about features"
        customer_history = {
            "sentiment_trend": "neutral",
            "total_interactions": 1,
            "escalation_count": 0
        }
        result = triage_agent.assess_issue(query, customer_history, 0.9)  # High confidence

        # With high confidence and no negative sentiment, shouldn't escalate
        assert result["should_escalate"] is False

    def test_get_triage_rules(self, triage_agent):
        rules = triage_agent.get_triage_rules()
        assert "confidence_threshold" in rules
        assert "escalation_keywords" in rules

class TestKnowledgeAgent:
    def test_search_knowledge_base_no_results(self, knowledge_agent):
        query = "test query"
        context = {"knowledge_base_results": []}

        result = knowledge_agent.search_knowledge_base(query, context)

        assert result["query"] == query
        assert result["relevant_articles_count"] == 0
        assert result["has_sufficient_information"] is False

    def test_format_knowledge_response_insufficient_info(self, knowledge_agent):
        query = "test query"
        search_results = {
            "has_sufficient_information": False,
            "articles": []
        }

        response = knowledge_agent.format_knowledge_response(query, search_results)

        assert "don't have specific information" in response

    def test_get_knowledge_domains(self, knowledge_agent):
        domains = knowledge_agent.get_knowledge_domains()
        assert len(domains) > 0
        assert "Product Features" in domains