"""
Customer Success FTE Agent - Production Implementation
Built with OpenAI Agents SDK for autonomous 24/7 operation.
"""

from agents import Agent, Runner, ModelSettings
from .prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT, TRIAGE_PROMPT
from .tools import (
    search_knowledge_base,
    create_ticket,
    get_customer_history,
    send_response,
    escalate_to_human,
    analyze_sentiment,
)
from .formatters import format_response_for_channel

import logging
import json

logger = logging.getLogger("customer_success_agent")


# --- Agent Definitions ---

triage_agent = Agent(
    name="Triage Agent",
    instructions=TRIAGE_PROMPT,
    model="gpt-4o-mini",
    tools=[analyze_sentiment],
)

customer_success_agent = Agent(
    name="Customer Success FTE",
    instructions=CUSTOMER_SUCCESS_SYSTEM_PROMPT,
    model="gpt-4o",
    tools=[
        search_knowledge_base,
        create_ticket,
        get_customer_history,
        send_response,
        escalate_to_human,
        analyze_sentiment,
    ],
    model_settings=ModelSettings(
        temperature=0.3,
        top_p=0.9,
    ),
)


async def process_customer_message(
    message: str,
    channel: str,
    customer_email: str,
    customer_name: str = "Customer",
    conversation_id: str | None = None,
) -> dict:
    """
    Process an incoming customer message through the agent pipeline.

    Args:
        message: The customer's message text
        channel: Source channel (email, whatsapp, web_form)
        customer_email: Customer's email address
        customer_name: Customer's name
        conversation_id: Existing conversation ID (if continuing)

    Returns:
        dict with ticket_id, response, channel, escalated status
    """
    try:
        # Step 1: Triage - analyze sentiment and categorize
        triage_result = await Runner.run(
            triage_agent,
            input=f"Analyze this customer message from {channel} channel:\n\n{message}",
        )
        logger.info(f"Triage result: {triage_result.final_output}")

        # Step 2: Parse triage to check for immediate escalation
        try:
            triage_data = json.loads(triage_result.final_output)
        except (json.JSONDecodeError, TypeError):
            triage_data = {"should_escalate": False, "category": "general", "priority": "medium"}

        # Step 3: Run main agent with full context
        context_msg = (
            f"Channel: {channel}\n"
            f"Customer: {customer_name} ({customer_email})\n"
            f"Triage: category={triage_data.get('category', 'general')}, "
            f"priority={triage_data.get('priority', 'medium')}, "
            f"sentiment={triage_data.get('sentiment', 'neutral')}\n\n"
            f"Customer Message:\n{message}"
        )

        result = await Runner.run(
            customer_success_agent,
            input=context_msg,
        )

        # Step 4: Format response for the target channel
        formatted_response = format_response_for_channel(result.final_output, channel)

        # Step 5: Extract tool call info
        tool_calls = []
        for item in result.new_items:
            if hasattr(item, 'tool_name'):
                tool_calls.append(item.tool_name)

        escalated = "escalate_to_human" in tool_calls

        return {
            "success": True,
            "response": formatted_response,
            "channel": channel,
            "escalated": escalated,
            "triage": triage_data,
            "tool_calls": tool_calls,
        }

    except Exception as e:
        logger.error(f"Agent processing failed: {e}")
        return {
            "success": False,
            "response": "We're experiencing technical difficulties. A human agent will follow up shortly.",
            "channel": channel,
            "escalated": True,
            "error": str(e),
        }


async def handle_web_form_submission(
    name: str,
    email: str,
    subject: str,
    category: str,
    message: str,
) -> dict:
    """
    Handle a web form submission specifically.

    Args:
        name: Customer name from form
        email: Customer email from form
        subject: Support subject from form
        category: Selected category from form
        message: Message body from form

    Returns:
        dict with ticket_id and initial response
    """
    full_message = f"Subject: {subject}\nCategory: {category}\n\n{message}"
    return await process_customer_message(
        message=full_message,
        channel="web_form",
        customer_email=email,
        customer_name=name,
    )


async def handle_email_message(
    sender_email: str,
    sender_name: str,
    subject: str,
    body: str,
    message_id: str | None = None,
) -> dict:
    """
    Handle an incoming email message.

    Args:
        sender_email: Sender's email address
        sender_name: Sender's display name
        subject: Email subject line
        body: Email body text
        message_id: Gmail message ID for threading

    Returns:
        dict with ticket_id and response
    """
    full_message = f"Subject: {subject}\n\n{body}"
    return await process_customer_message(
        message=full_message,
        channel="email",
        customer_email=sender_email,
        customer_name=sender_name,
    )


async def handle_whatsapp_message(
    phone_number: str,
    sender_name: str,
    message: str,
) -> dict:
    """
    Handle an incoming WhatsApp message.

    Args:
        phone_number: Sender's phone number
        sender_name: Sender's WhatsApp profile name
        message: Message text

    Returns:
        dict with response
    """
    return await process_customer_message(
        message=message,
        channel="whatsapp",
        customer_email=f"{phone_number}@whatsapp.bridge",
        customer_name=sender_name,
    )
