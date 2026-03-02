from typing import List, Dict, Any
import logging
from app.config.settings import settings

logger = logging.getLogger(__name__)

class ConfidenceScorer:
    def __init__(self):
        self.confidence_threshold = settings.CONFIDENCE_THRESHOLD
        self.escalation_keywords = [kw.strip() for kw in settings.ESCALATION_KEYWORDS.split(",")]

    def calculate_overall_confidence(
        self,
        agent_confidence: float,
        kb_relevance: List[float],
        tools_used: List[str]
    ) -> float:
        """
        Calculate overall confidence based on multiple factors
        """
        # Start with agent's confidence
        confidence = agent_confidence

        # Adjust based on knowledge base relevance
        if kb_relevance:
            avg_kb_relevance = sum(kb_relevance) / len(kb_relevance)
            # Higher KB relevance increases confidence
            confidence = (confidence + avg_kb_relevance) / 2

        # Adjust based on tools used
        if tools_used:
            # Using relevant tools increases confidence
            confidence *= 1.1
            # Cap at 1.0
            confidence = min(1.0, confidence)

        # Ensure confidence stays within bounds
        return max(0.0, min(1.0, confidence))

    def should_escalate(
        self,
        confidence_score: float,
        message_content: str,
        customer_sentiment: str = "neutral"
    ) -> bool:
        """
        Determine if a message should be escalated based on confidence and other factors
        """
        # Check if confidence is below threshold
        if confidence_score < self.confidence_threshold:
            logger.debug(f"Escalating due to low confidence: {confidence_score} < {self.confidence_threshold}")
            return True

        # Check for escalation keywords in the message
        message_lower = message_content.lower()
        for keyword in self.escalation_keywords:
            if keyword.lower() in message_lower:
                logger.debug(f"Escalating due to keyword: {keyword}")
                return True

        # Check for negative sentiment indicators
        negative_indicators = [
            "angry", "frustrated", "disappointed", "terrible", "worst",
            "complain", "dissatisfied", "refund", "cancel", "unhappy",
            "not working", "broken", "error", "bug"
        ]

        for indicator in negative_indicators:
            if indicator in message_lower:
                # If confidence is already low and sentiment is negative, escalate
                if confidence_score < 0.8:
                    logger.debug(f"Escalating due to negative sentiment indicator: {indicator}")
                    return True

        # Check for repeated questions (possible sign of confusion)
        # This is a simplified check - in reality, you'd want more sophisticated conversation history analysis
        if "?" in message_content and message_content.count("?") > 2:
            if confidence_score < 0.75:
                logger.debug("Escalating due to multiple questions in message")
                return True

        return False

    def calculate_confidence_impact(self, tool_name: str, success: bool) -> float:
        """
        Calculate the impact of a tool call on the overall confidence
        """
        # Define impact values for different tools
        tool_impacts = {
            "search_kb": 0.15 if success else -0.1,  # Knowledge base search adds positive confidence if successful
            "get_customer_history": 0.1 if success else -0.05,  # Customer history adds some confidence
            "create_ticket": 0.05 if success else -0.15,  # Creating ticket slightly helps confidence
            "escalate": -0.2 if success else -0.25  # Escalation indicates low confidence
        }

        base_impact = tool_impacts.get(tool_name, 0.0)
        return base_impact if success else base_impact * 1.5  # Greater penalty for tool failure