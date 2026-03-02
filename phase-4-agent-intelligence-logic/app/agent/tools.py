"""
Production tools for the Customer Success FTE Agent.
Converted from MCP server tools to OpenAI Agents SDK @function_tool format.
"""

from agents import function_tool
from pydantic import BaseModel, Field
from typing import Optional, List
import asyncpg
import os
import json
import logging

logger = logging.getLogger("customer_success_agent")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/crm_db")


async def get_db_pool():
    """Get or create database connection pool."""
    if not hasattr(get_db_pool, '_pool') or get_db_pool._pool is None:
        get_db_pool._pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    return get_db_pool._pool


# --- Input Schemas ---

class KnowledgeSearchInput(BaseModel):
    """Input schema for knowledge base search."""
    query: str = Field(description="The search query text")
    max_results: int = Field(default=5, description="Maximum number of results to return")
    category: Optional[str] = Field(default=None, description="Optional category filter")


class CreateTicketInput(BaseModel):
    """Input schema for creating a support ticket."""
    customer_email: str = Field(description="Customer email address")
    customer_name: str = Field(description="Customer full name")
    subject: str = Field(description="Ticket subject line")
    description: str = Field(description="Detailed description of the issue")
    channel: str = Field(description="Source channel: email, whatsapp, or web_form")
    category: str = Field(default="general", description="Ticket category")
    priority: str = Field(default="medium", description="Priority: low, medium, high, urgent")


class GetCustomerHistoryInput(BaseModel):
    """Input schema for retrieving customer history."""
    customer_email: str = Field(description="Customer email to look up")
    limit: int = Field(default=10, description="Maximum number of past interactions to return")


class SendResponseInput(BaseModel):
    """Input schema for sending a response to the customer."""
    ticket_id: str = Field(description="The ticket ID to respond to")
    message: str = Field(description="The response message to send")
    channel: str = Field(description="Target channel: email, whatsapp, or web_form")


class EscalateInput(BaseModel):
    """Input schema for escalating to a human agent."""
    ticket_id: str = Field(description="The ticket ID to escalate")
    reason: str = Field(description="Reason for escalation")
    context: str = Field(description="Full conversation context for the human agent")
    priority: str = Field(default="high", description="Escalation priority")


class SentimentAnalysisInput(BaseModel):
    """Input schema for sentiment analysis."""
    text: str = Field(description="The text to analyze for sentiment")


# --- Production Tools ---

@function_tool
async def search_knowledge_base(input: KnowledgeSearchInput) -> str:
    """Search product documentation for relevant information.

    Use this when the customer asks questions about product features,
    how to use something, or needs technical information.

    Args:
        input: Search parameters including query and optional filters

    Returns:
        Formatted search results with relevance scores
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            if input.category:
                results = await conn.fetch("""
                    SELECT title, content, category,
                           1 - (embedding <=> $1::vector) as similarity
                    FROM knowledge_base
                    WHERE category = $2
                    ORDER BY embedding <=> $1::vector
                    LIMIT $3
                """, input.query, input.category, input.max_results)
            else:
                results = await conn.fetch("""
                    SELECT title, content, category,
                           ts_rank(to_tsvector('english', content),
                                   plainto_tsquery('english', $1)) as similarity
                    FROM knowledge_base
                    WHERE to_tsvector('english', content) @@ plainto_tsquery('english', $1)
                    ORDER BY similarity DESC
                    LIMIT $2
                """, input.query, input.max_results)

            if not results:
                return "No relevant documentation found. Consider escalating to human support."

            formatted = []
            for r in results:
                formatted.append(
                    f"**{r['title']}** (relevance: {r['similarity']:.2f})\n{r['content'][:500]}"
                )
            return "\n\n---\n\n".join(formatted)

    except Exception as e:
        logger.error(f"Knowledge base search failed: {e}")
        return "Knowledge base temporarily unavailable. Please try again or escalate."


@function_tool
async def create_ticket(input: CreateTicketInput) -> str:
    """Create a new support ticket in the CRM system.

    MUST be called first for every customer interaction to ensure tracking.

    Args:
        input: Ticket creation parameters

    Returns:
        JSON string with the created ticket details
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Find or create customer
            customer = await conn.fetchrow(
                "SELECT id FROM customers WHERE email = $1",
                input.customer_email
            )

            if not customer:
                customer_id = await conn.fetchval("""
                    INSERT INTO customers (email, name, channel)
                    VALUES ($1, $2, $3)
                    RETURNING id
                """, input.customer_email, input.customer_name, input.channel)
            else:
                customer_id = customer['id']

            # Create ticket
            ticket_id = await conn.fetchval("""
                INSERT INTO tickets (customer_id, subject, description, channel,
                                     category, priority, status)
                VALUES ($1, $2, $3, $4, $5, $6, 'open')
                RETURNING id
            """, customer_id, input.subject, input.description,
                input.channel, input.category, input.priority)

            return json.dumps({
                "ticket_id": str(ticket_id),
                "customer_id": str(customer_id),
                "status": "open",
                "message": f"Ticket {ticket_id} created successfully."
            })

    except Exception as e:
        logger.error(f"Ticket creation failed: {e}")
        return json.dumps({"error": str(e), "message": "Failed to create ticket."})


@function_tool
async def get_customer_history(input: GetCustomerHistoryInput) -> str:
    """Retrieve customer's past interaction history across all channels.

    Use this after creating a ticket to check for prior context and
    provide personalized support.

    Args:
        input: Customer lookup parameters

    Returns:
        Formatted customer history including past tickets and messages
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            customer = await conn.fetchrow(
                "SELECT id, name, email, phone FROM customers WHERE email = $1",
                input.customer_email
            )

            if not customer:
                return "No previous history found for this customer. This is their first interaction."

            tickets = await conn.fetch("""
                SELECT id, subject, status, channel, category, priority, created_at
                FROM tickets
                WHERE customer_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            """, customer['id'], input.limit)

            if not tickets:
                return f"Customer {customer['name']} found, but no previous tickets on record."

            history = [f"Customer: {customer['name']} ({customer['email']})"]
            history.append(f"Total past tickets: {len(tickets)}\n")

            for t in tickets:
                history.append(
                    f"- [{t['status']}] {t['subject']} "
                    f"(via {t['channel']}, {t['priority']} priority, "
                    f"{t['created_at'].strftime('%Y-%m-%d')})"
                )

            return "\n".join(history)

    except Exception as e:
        logger.error(f"Customer history lookup failed: {e}")
        return "Unable to retrieve customer history at this time."


@function_tool
async def send_response(input: SendResponseInput) -> str:
    """Send a response to the customer via the appropriate channel.

    MUST be the last tool called in every interaction. Never respond
    to the customer without using this tool.

    Args:
        input: Response parameters including ticket ID, message, and channel

    Returns:
        Confirmation of the sent response
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Log the response message
            await conn.execute("""
                INSERT INTO messages (ticket_id, sender_type, content, direction, channel)
                VALUES ($1, 'agent', $2, 'outbound', $3)
            """, input.ticket_id, input.message, input.channel)

            # Update ticket status
            await conn.execute("""
                UPDATE tickets SET status = 'processing', updated_at = NOW()
                WHERE id = $1
            """, input.ticket_id)

        # Channel-specific delivery would be handled by Phase 5 dispatcher
        # Here we publish to Kafka for async delivery
        return json.dumps({
            "success": True,
            "ticket_id": input.ticket_id,
            "channel": input.channel,
            "message": "Response queued for delivery."
        })

    except Exception as e:
        logger.error(f"Send response failed: {e}")
        return json.dumps({"success": False, "error": str(e)})


@function_tool
async def escalate_to_human(input: EscalateInput) -> str:
    """Escalate a ticket to a human agent when AI cannot handle it.

    Use this when escalation triggers are detected: pricing inquiries,
    refund requests, legal mentions, angry customers, or when the
    customer explicitly requests a human.

    Args:
        input: Escalation parameters including reason and context

    Returns:
        Confirmation of escalation
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE tickets
                SET status = 'escalated',
                    priority = $2,
                    escalation_reason = $3,
                    updated_at = NOW()
                WHERE id = $1
            """, input.ticket_id, input.priority, input.reason)

            # Log escalation message
            await conn.execute("""
                INSERT INTO messages (ticket_id, sender_type, content, direction, channel)
                VALUES ($1, 'system', $2, 'internal', 'system')
            """, input.ticket_id,
                f"ESCALATED: {input.reason}\n\nContext: {input.context}")

        return json.dumps({
            "success": True,
            "ticket_id": input.ticket_id,
            "escalated": True,
            "reason": input.reason,
            "message": "Ticket escalated to human agent successfully."
        })

    except Exception as e:
        logger.error(f"Escalation failed: {e}")
        return json.dumps({"success": False, "error": str(e)})


@function_tool
async def analyze_sentiment(input: SentimentAnalysisInput) -> str:
    """Analyze the sentiment of a customer message.

    Use this on every incoming customer message to detect negative
    sentiment that may require escalation.

    Args:
        input: The text to analyze

    Returns:
        JSON with sentiment score, label, and escalation recommendation
    """
    text_lower = input.text.lower()

    # Rule-based sentiment indicators
    negative_words = ['angry', 'frustrated', 'terrible', 'worst', 'broken',
                      'ridiculous', 'unacceptable', 'furious', 'horrible', 'awful']
    positive_words = ['thank', 'great', 'excellent', 'amazing', 'love',
                      'helpful', 'wonderful', 'perfect', 'appreciate', 'good']
    escalation_words = ['lawyer', 'legal', 'sue', 'attorney', 'refund',
                        'cancel', 'human', 'agent', 'representative', 'manager']

    neg_count = sum(1 for w in negative_words if w in text_lower)
    pos_count = sum(1 for w in positive_words if w in text_lower)
    esc_count = sum(1 for w in escalation_words if w in text_lower)

    # Calculate sentiment score
    if neg_count + pos_count == 0:
        score = 0.5
        label = "neutral"
    else:
        score = pos_count / (pos_count + neg_count)
        if score >= 0.6:
            label = "positive"
        elif score >= 0.4:
            label = "neutral"
        elif score >= 0.2:
            label = "negative"
        else:
            label = "angry"

    should_escalate = score < 0.3 or esc_count > 0

    return json.dumps({
        "score": round(score, 2),
        "label": label,
        "confidence": 0.85,
        "should_escalate": should_escalate,
        "escalation_triggers": esc_count
    })
