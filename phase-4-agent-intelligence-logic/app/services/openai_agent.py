import openai
from openai import OpenAI
from typing import Dict, Any, List, Optional
import logging
import asyncio
from app.config.settings import settings

logger = logging.getLogger(__name__)

class OpenAIAgent:
    def __init__(self):
        client_kwargs = {"api_key": settings.OPENAI_API_KEY}
        if settings.OPENAI_BASE_URL:
            client_kwargs["base_url"] = settings.OPENAI_BASE_URL
        self.client = OpenAI(**client_kwargs)
        self.model = settings.OPENAI_MODEL

        # Define specialized agent personas
        self.agent_personas = {
            "product_knowledge": {
                "system_prompt": "You are a product knowledge expert. Answer customer questions about product features, functionality, and usage. Provide accurate, detailed information based on the knowledge base provided.",
                "instructions": "Always refer to the knowledge base for accurate information. If uncertain, acknowledge limitations."
            },
            "triage": {
                "system_prompt": "You are a triage specialist. Assess the urgency and complexity of customer issues. Determine if the issue can be resolved immediately or requires escalation to human support.",
                "instructions": "Evaluate the customer's issue and decide on the appropriate course of action. Consider escalation triggers and confidence levels."
            },
            "support": {
                "system_prompt": "You are a customer support agent. Provide helpful, empathetic responses to customer inquiries. Focus on resolving their issues efficiently.",
                "instructions": "Be helpful and professional. Use tools as needed to resolve customer issues."
            }
        }

    async def process_message(
        self,
        message: str,
        customer_id: str,
        conversation_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a customer message using OpenAI's Assistant API
        """
        try:
            # Prepare the context for the agent
            system_prompt = self._select_persona(message, context)

            # Create a message for the assistant
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]

            # Add context if provided
            if context:
                if "knowledge_base_results" in context:
                    kb_content = "\n".join([article.get("content", "") for article in context["knowledge_base_results"][:3]])
                    if kb_content:
                        messages.insert(1, {"role": "system", "content": f"Knowledge base context:\n{kb_content}"})

                if "customer_history" in context:
                    history_summary = context["customer_history"].get("summary", "")
                    if history_summary:
                        messages.insert(1, {"role": "system", "content": f"Customer history: {history_summary}"})

            # Call the OpenAI API
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000
                )
            )

            # Extract the response
            agent_response = response.choices[0].message.content

            # Calculate a basic confidence score based on response length and certainty
            confidence_score = self._calculate_confidence(agent_response, context)

            return {
                "response": agent_response,
                "confidence_score": confidence_score,
                "tools_used": context.get("tools_used", []) if context else [],
                "persona_used": self._identify_active_persona(system_prompt)
            }

        except Exception as e:
            logger.error(f"Error processing message with OpenAI agent: {e}")
            raise

    def _select_persona(self, message: str, context: Optional[Dict[str, Any]]) -> str:
        """
        Select the appropriate agent persona based on the message and context
        """
        # Default to support persona
        selected_persona = "support"

        # Check for keywords that suggest a different persona
        message_lower = message.lower()

        # Product knowledge keywords
        product_keywords = ["feature", "how to", "function", "usage", "work", "capability", "setting"]
        if any(keyword in message_lower for keyword in product_keywords):
            selected_persona = "product_knowledge"

        # Triage keywords
        elif any(keyword in message_lower for keyword in ["urgent", "critical", "problem", "broken", "error", "issue"]):
            selected_persona = "triage"

        # Use context if available
        if context and "intent" in context:
            intent = context["intent"]
            if intent in ["product_inquiry"]:
                selected_persona = "product_knowledge"
            elif intent in ["technical_issue", "escalation_request"]:
                selected_persona = "triage"

        return self.agent_personas[selected_persona]["system_prompt"]

    def _identify_active_persona(self, system_prompt: str) -> str:
        """
        Identify which persona is being used based on the system prompt
        """
        for persona_name, persona_data in self.agent_personas.items():
            if persona_data["system_prompt"] in system_prompt:
                return persona_name
        return "support"  # default

    def _calculate_confidence(self, response: str, context: Optional[Dict[str, Any]]) -> float:
        """
        Calculate a basic confidence score based on the response and context
        """
        # Start with a base score
        confidence = 0.7

        # Adjust based on response characteristics
        if "I don't know" in response or "I'm not sure" in response:
            confidence -= 0.3
        elif "I can help" in response or "based on the information" in response:
            confidence += 0.1

        # Adjust based on context richness
        if context:
            if "knowledge_base_results" in context and len(context["knowledge_base_results"]) > 0:
                confidence += 0.2
            if "customer_history" in context:
                confidence += 0.1

        # Ensure confidence stays within bounds
        return max(0.0, min(1.0, confidence))

    async def create_assistant(self, name: str, instructions: str, tools: List[Dict[str, Any]] = None):
        """
        Create an OpenAI Assistant with specific tools and instructions
        """
        try:
            assistant = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.beta.assistants.create(
                    name=name,
                    instructions=instructions,
                    tools=tools or [],
                    model=self.model
                )
            )
            return assistant
        except Exception as e:
            logger.error(f"Error creating assistant: {e}")
            raise

    async def create_thread(self):
        """
        Create a thread for conversation management
        """
        try:
            thread = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.beta.threads.create()
            )
            return thread
        except Exception as e:
            logger.error(f"Error creating thread: {e}")
            raise

    async def run_assistant(self, thread_id: str, assistant_id: str):
        """
        Run the assistant on a thread
        """
        try:
            run = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.beta.threads.runs.create(
                    thread_id=thread_id,
                    assistant_id=assistant_id
                )
            )
            return run
        except Exception as e:
            logger.error(f"Error running assistant: {e}")
            raise