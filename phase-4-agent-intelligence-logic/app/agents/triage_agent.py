from typing import Dict, Any
import logging
from app.config.settings import settings
from app.utils.confidence_scoring import ConfidenceScorer

logger = logging.getLogger(__name__)

class TriageAgent:
    """
    Triage agent responsible for determining issue severity and routing
    """
    def __init__(self):
        self.confidence_scorer = ConfidenceScorer()
        self.system_prompt = """
        You are a triage specialist. Assess the urgency and complexity of customer issues.
        Determine if the issue can be resolved immediately or requires escalation to human support.
        Consider the following when making your assessment:

        1. Urgency: How time-sensitive is the issue?
        2. Complexity: How difficult is the issue to resolve?
        3. Customer Sentiment: Is the customer satisfied or frustrated?
        4. Business Impact: What is the potential impact of this issue?

        Respond with your assessment and recommended action.
        """

    def assess_issue(self, query: str, customer_history: Dict[str, Any], confidence_score: float) -> Dict[str, Any]:
        """
        Assess the customer issue and determine appropriate action
        """
        # Define escalation triggers
        escalation_triggers = [
            "urgent", "critical", "emergency", "asap", "immediately",
            "billing", "payment", "charge", "refund", "money", "compensation",
            "manager", "supervisor", "escalate", "speak to human",
            "not helpful", "unsatisfied", "angry", "frustrated", "terrible service"
        ]

        # Check for escalation keywords
        query_lower = query.lower()
        has_escalation_keyword = any(trigger in query_lower for trigger in escalation_triggers)

        # Check customer sentiment
        customer_sentiment = customer_history.get("sentiment_trend", "neutral")
        is_negative_sentiment = customer_sentiment in ["negative", "volatile"]

        # Check issue complexity based on customer history
        has_many_interactions = customer_history.get("total_interactions", 0) > 3
        has_escalations = customer_history.get("escalation_count", 0) > 0

        # Determine action
        should_escalate = (
            has_escalation_keyword or
            is_negative_sentiment or
            confidence_score < settings.CONFIDENCE_THRESHOLD or
            (has_many_interactions and has_escalations) or
            "billing" in query_lower or
            "payment" in query_lower
        )

        # Determine priority
        priority = "medium"
        if has_escalation_keyword or is_negative_sentiment or "urgent" in query_lower:
            priority = "high"
        if "critical" in query_lower or "emergency" in query_lower:
            priority = "critical"

        assessment = {
            "should_escalate": should_escalate,
            "priority": priority,
            "confidence_in_assessment": confidence_score,
            "reasons": []
        }

        if has_escalation_keyword:
            assessment["reasons"].append("Contains escalation keywords")
        if is_negative_sentiment:
            assessment["reasons"].append("Negative customer sentiment detected")
        if confidence_score < settings.CONFIDENCE_THRESHOLD:
            assessment["reasons"].append(f"Confidence score {confidence_score} below threshold {settings.CONFIDENCE_THRESHOLD}")
        if has_many_interactions:
            assessment["reasons"].append("Customer has many past interactions")
        if has_escalations:
            assessment["reasons"].append("Customer has been escalated before")

        logger.info(f"Triage assessment for query: {query[:50]}... - Escalate: {should_escalate}, Priority: {priority}")

        return assessment

    def get_triage_rules(self) -> Dict[str, Any]:
        """
        Return the triage rules used by the agent
        """
        return {
            "confidence_threshold": settings.CONFIDENCE_THRESHOLD,
            "escalation_keywords": [kw.strip() for kw in settings.ESCALATION_KEYWORDS.split(",")],
            "priority_levels": {
                "low": ["general inquiry", "feedback"],
                "medium": ["standard support", "feature request"],
                "high": ["urgent", "important", "billing", "payment"],
                "critical": ["emergency", "critical", "system down"]
            }
        }