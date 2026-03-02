from typing import Dict, Any, Optional
import logging
from app.config.settings import settings

logger = logging.getLogger(__name__)

class SpecializedAgent:
    """
    A specialized agent with different personas for different types of queries
    """
    def __init__(self):
        self.personas = {
            "product_knowledge": {
                "name": "Product Knowledge Agent",
                "system_prompt": "You are a product knowledge expert. Answer customer questions about product features, functionality, and usage. Provide accurate, detailed information based on the knowledge base provided.",
                "instructions": "Always refer to the knowledge base for accurate information. If uncertain, acknowledge limitations."
            },
            "triage": {
                "name": "Triage Agent",
                "system_prompt": "You are a triage specialist. Assess the urgency and complexity of customer issues. Determine if the issue can be resolved immediately or requires escalation to human support.",
                "instructions": "Evaluate the customer's issue and decide on the appropriate course of action. Consider escalation triggers and confidence levels."
            },
            "support": {
                "name": "Support Agent",
                "system_prompt": "You are a customer support agent. Provide helpful, empathetic responses to customer inquiries. Focus on resolving their issues efficiently.",
                "instructions": "Be helpful and professional. Use tools as needed to resolve customer issues."
            }
        }

    def get_persona_for_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Determine which persona is most appropriate for a given query
        """
        query_lower = query.lower()

        # Product knowledge keywords
        product_keywords = ["feature", "how to", "function", "usage", "work", "capability", "setting", "tutorial"]
        if any(keyword in query_lower for keyword in product_keywords):
            return "product_knowledge"

        # Triage keywords
        triage_keywords = ["urgent", "critical", "problem", "broken", "error", "issue", "not working", "crash", "bug"]
        if any(keyword in query_lower for keyword in triage_keywords):
            return "triage"

        # Default to support for general inquiries
        return "support"

    def get_system_prompt(self, persona: str) -> str:
        """
        Get the system prompt for a specific persona
        """
        if persona in self.personas:
            return self.personas[persona]["system_prompt"]
        else:
            # Default to support agent if persona not found
            return self.personas["support"]["system_prompt"]

    def get_instructions(self, persona: str) -> str:
        """
        Get the instructions for a specific persona
        """
        if persona in self.personas:
            return self.personas[persona]["instructions"]
        else:
            # Default to support agent if persona not found
            return self.personas["support"]["instructions"]

    def get_available_personas(self) -> list:
        """
        Get list of available agent personas
        """
        return list(self.personas.keys())

    def switch_persona_during_conversation(self, current_persona: str, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Determine if the agent should switch personas during a conversation
        """
        # Check if the new query suggests a different persona is needed
        suggested_persona = self.get_persona_for_query(query, context)

        # If the suggested persona is different from current, consider switching
        if suggested_persona != current_persona:
            # Additional logic could be added here to determine if the switch is appropriate
            # For example, consider the conversation context, customer history, etc.
            logger.info(f"Switching from {current_persona} to {suggested_persona} persona based on query")
            return suggested_persona

        return current_persona