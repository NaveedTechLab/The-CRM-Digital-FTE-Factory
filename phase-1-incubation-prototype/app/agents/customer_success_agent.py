"""
Customer Success Agent skeleton using OpenAI Chat Completion for handling
product Q&A and triage requests in the prototype.
"""
import os
from typing import Dict, Any, Optional
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CustomerSuccessAgent:
    """
    A skeleton agent that uses OpenAI's Chat Completion API to process customer
    inquiries and generate appropriate responses.
    """

    def __init__(self):
        # Initialize the OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")

        # For the prototype, if no API key is provided, use a mock mode
        if not api_key:
            print("Warning: OPENAI_API_KEY not found. Using mock agent mode for prototype.")
            self.use_mock = True
        else:
            self.client = AsyncOpenAI(api_key=api_key)
            self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
            self.use_mock = False

    async def process_inquiry(self,
                            customer_query: str,
                            customer_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a customer inquiry and generate a response.

        Args:
            customer_query: The customer's question or request
            customer_context: Optional context about the customer (name, history, etc.)

        Returns:
            Dictionary containing the agent's response and any additional metadata
        """

        # If in mock mode, return a simulated response
        if self.use_mock:
            return self._mock_process_inquiry(customer_query, customer_context)

        # Construct the prompt for the agent
        prompt = self._construct_prompt(customer_query, customer_context)

        try:
            # Call the OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            # Extract the agent's response
            agent_response = response.choices[0].message.content

            # Determine if triage is needed (simple heuristic for prototype)
            needs_triage = self._needs_triage(agent_response, customer_query)

            return {
                "response": agent_response,
                "needs_triage": needs_triage,
                "confidence": 0.8,  # Placeholder for confidence score
                "tokens_used": response.usage.total_tokens if response.usage else 0
            }
        except Exception as e:
            # Handle any errors from the API call
            return {
                "response": f"I apologize, but I'm currently unable to process your request. Please try again later.",
                "needs_triage": True,
                "confidence": 0.0,
                "error": str(e)
            }

    def _mock_process_inquiry(self, customer_query: str, customer_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a customer inquiry using mock responses for prototype mode.

        Args:
            customer_query: The customer's question or request
            customer_context: Optional context about the customer (name, history, etc.)

        Returns:
            Dictionary containing the mock agent's response and any additional metadata
        """
        # Simple mock responses based on keywords in the customer query
        customer_query_lower = customer_query.lower()

        if any(keyword in customer_query_lower for keyword in ['refund', 'return', 'cancel', 'complaint']):
            response = "I understand your concern regarding refunds. While I can't process refunds directly, I'll make sure your request is escalated to our billing department who can assist you further."
            needs_triage = True
        elif any(keyword in customer_query_lower for keyword in ['password', 'login', 'access', 'account']):
            response = "For account-related issues, I recommend resetting your password using the 'Forgot Password' link on our login page. If you continue to experience issues, our technical support team can provide further assistance."
            needs_triage = True
        elif any(keyword in customer_query_lower for keyword in ['question', 'help', 'info', 'information', 'product']):
            response = "Thank you for your inquiry about our products. Our premium package offers advanced features including 24/7 support, priority processing, and enhanced security options. Would you like me to connect you with our sales team for more details?"
            needs_triage = False
        else:
            response = f"Thank you for reaching out. I've received your inquiry: '{customer_query}'. Our support team will review your request and get back to you within 24 hours. If your issue is urgent, please let me know and I can prioritize your request."
            needs_triage = False

        return {
            "response": response,
            "needs_triage": needs_triage,
            "confidence": 0.7,  # Mock confidence score
            "tokens_used": 0,  # No tokens used in mock mode
            "mock_response": True
        }

    def _construct_prompt(self, query: str, context: Optional[Dict[str, Any]]) -> str:
        """
        Construct the prompt to send to the OpenAI API.
        """
        prompt_parts = []

        if context:
            prompt_parts.append(f"Customer Information:\n")
            prompt_parts.append(f"- Name: {context.get('name', 'Unknown')}\n")
            prompt_parts.append(f"- Email: {context.get('email', 'Not provided')}\n")
            prompt_parts.append(f"- Previous interactions: {len(context.get('interaction_history', []))}\n")
            if context.get('tickets'):
                prompt_parts.append(f"- Previous tickets: {len(context['tickets'])}\n")
            prompt_parts.append("\n")

        prompt_parts.append(f"Customer Query: {query}")
        prompt_parts.append(f"\nPlease provide a helpful and accurate response to the customer's query.")

        return "".join(prompt_parts)

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt that defines the agent's role and behavior.
        """
        return (
            "You are an expert customer success agent for a technology company. "
            "Your role is to help customers with their questions about our products and services. "
            "Provide accurate, helpful, and friendly responses. If a customer's issue is complex "
            "or requires human attention, acknowledge their concern and indicate that a human "
            "representative will follow up shortly. Maintain a professional but friendly tone. "
            "If you don't know the answer to a specific technical question, suggest that a "
            "specialist will contact them directly rather than guessing."
        )

    def _needs_triage(self, response: str, query: str) -> bool:
        """
        Simple heuristic to determine if the inquiry needs human triage.
        This is a basic implementation for the prototype.
        """
        # Keywords that might indicate the need for human triage
        triage_keywords = [
            "escalat", "urgent", "emergency", "immediately", "critical",
            "complaint", "refund", "cancel", "terminate", "serious", "bug"
        ]

        response_lower = response.lower()
        query_lower = query.lower()

        for keyword in triage_keywords:
            if keyword in response_lower or keyword in query_lower:
                return True

        # If the response contains phrases indicating inability to help
        if any(phrase in response_lower for phrase in [
            "i cannot", "i'm unable", "human representative",
            "customer service", "support team"
        ]):
            return True

        return False


# Global instance of the agent
customer_success_agent = CustomerSuccessAgent()