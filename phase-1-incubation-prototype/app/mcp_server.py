"""
MCP (Model Context Protocol) Server for the Customer Success Digital FTE.

Exposes 5+ prototype capabilities as tools that can be called by any MCP client.
This is the incubation prototype MCP server - tools are later transformed
to @function_tool decorators in Phase 4 (OpenAI Agents SDK).

Tools exposed:
  1. search_knowledge_base - Search product docs for relevant answers
  2. create_ticket - Create a support ticket to track interaction
  3. get_customer_history - Retrieve customer's past interactions across channels
  4. escalate_to_human - Escalate to human agent with context
  5. send_response - Send formatted response via customer's channel
  6. analyze_sentiment - Detect customer mood from message text
"""

import asyncio
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# In-memory stores (prototype – replaced by PostgreSQL + pgvector in Phase 2)
# ---------------------------------------------------------------------------

_knowledge_base: List[Dict[str, Any]] = [
    {
        "id": "kb-001",
        "title": "Getting Started with ProjectFlow",
        "content": "ProjectFlow is a project management and team collaboration platform. To get started, create an account at app.projectflow.com, set up your first project, and invite team members.",
        "category": "getting-started",
        "keywords": ["setup", "start", "account", "create", "begin", "new"],
    },
    {
        "id": "kb-002",
        "title": "ProjectFlow Pricing Plans",
        "content": "ProjectFlow offers three plans: Starter ($12/user/month), Professional ($29/user/month), and Enterprise ($59/user/month). All plans include core project management features.",
        "category": "pricing",
        "keywords": ["price", "cost", "plan", "subscription", "billing", "pay"],
    },
    {
        "id": "kb-003",
        "title": "Password Reset Guide",
        "content": "To reset your password: 1) Go to app.projectflow.com/login 2) Click 'Forgot Password' 3) Enter your email 4) Check your inbox for the reset link 5) Create a new password.",
        "category": "account",
        "keywords": ["password", "reset", "forgot", "login", "access", "locked"],
    },
    {
        "id": "kb-004",
        "title": "Integration Guide",
        "content": "ProjectFlow integrates with Slack, GitHub, Jira, Google Drive, and Zapier. Go to Settings > Integrations to connect your tools.",
        "category": "integrations",
        "keywords": ["integrate", "connect", "slack", "github", "jira", "zapier"],
    },
    {
        "id": "kb-005",
        "title": "Bug Reporting Process",
        "content": "To report a bug: 1) Go to Help > Report Bug 2) Describe the issue 3) Attach screenshots if possible 4) Submit. Our team reviews bugs within 24-48 hours.",
        "category": "support",
        "keywords": ["bug", "error", "issue", "broken", "not working", "crash"],
    },
    {
        "id": "kb-006",
        "title": "Data Export and Backup",
        "content": "Export your data from Settings > Data Management > Export. Supports CSV and JSON formats. Automatic backups run daily for Professional and Enterprise plans.",
        "category": "data",
        "keywords": ["export", "backup", "download", "data", "csv", "json"],
    },
]

_tickets: Dict[str, Dict[str, Any]] = {}
_customers: Dict[str, Dict[str, Any]] = {
    "customer-001": {
        "id": "customer-001",
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "phone": "+15551234567",
        "channels": ["email", "webform"],
        "interactions": [
            {
                "date": "2024-12-01",
                "channel": "email",
                "summary": "Asked about integrations",
                "resolution": "Provided integration guide",
            }
        ],
    },
    "customer-002": {
        "id": "customer-002",
        "name": "Bob Smith",
        "email": "bob@example.com",
        "phone": "+15559876543",
        "channels": ["whatsapp", "email"],
        "interactions": [
            {
                "date": "2024-12-10",
                "channel": "whatsapp",
                "summary": "Reported login issue",
                "resolution": "Guided through password reset",
            },
            {
                "date": "2024-12-15",
                "channel": "email",
                "summary": "Asked about pricing",
                "resolution": "Escalated to sales",
            },
        ],
    },
}

_escalations: Dict[str, Dict[str, Any]] = {}

# ---------------------------------------------------------------------------
# MCP Tool implementations
# ---------------------------------------------------------------------------


async def search_knowledge_base(query: str) -> Dict[str, Any]:
    """
    Search the product knowledge base for relevant documentation.

    Args:
        query: Natural language search query from the customer.

    Returns:
        Dict with matched articles ranked by relevance.
    """
    query_lower = query.lower()
    results = []

    for article in _knowledge_base:
        score = 0.0
        # Keyword matching (prototype – replaced by pgvector in Phase 2)
        for keyword in article["keywords"]:
            if keyword in query_lower:
                score += 0.2
        # Title match boost
        if any(word in article["title"].lower() for word in query_lower.split()):
            score += 0.15
        # Content match
        if any(word in article["content"].lower() for word in query_lower.split() if len(word) > 3):
            score += 0.1

        if score > 0:
            results.append(
                {
                    "id": article["id"],
                    "title": article["title"],
                    "content": article["content"],
                    "category": article["category"],
                    "relevance_score": min(score, 1.0),
                }
            )

    # Sort by relevance and limit to top 5
    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    results = results[:5]

    return {
        "query": query,
        "results": results,
        "total_matches": len(results),
        "search_method": "keyword_matching",  # Upgraded to vector_similarity in Phase 2
    }


async def create_ticket(
    customer_id: str,
    issue: str,
    priority: str = "medium",
    channel: str = "webform",
) -> Dict[str, Any]:
    """
    Create a support ticket to track the customer interaction.
    MUST be called first in every interaction to ensure tracking.

    Args:
        customer_id: The unique customer identifier.
        issue: Description of the customer's issue.
        priority: Ticket priority (low, medium, high, critical).
        channel: Source channel (gmail, whatsapp, webform).

    Returns:
        Dict with the created ticket details including ticket_id.
    """
    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc).isoformat()

    ticket = {
        "ticket_id": ticket_id,
        "customer_id": customer_id,
        "issue": issue,
        "priority": priority,
        "channel": channel,
        "status": "open",
        "created_at": now,
        "updated_at": now,
    }

    _tickets[ticket_id] = ticket

    return {
        "ticket_id": ticket_id,
        "status": "created",
        "priority": priority,
        "channel": channel,
        "message": f"Ticket {ticket_id} created successfully.",
    }


async def get_customer_history(customer_id: str) -> Dict[str, Any]:
    """
    Retrieve a customer's past interactions across ALL channels.
    Used for context and personalization before generating a response.

    Args:
        customer_id: The unique customer identifier (or email address).

    Returns:
        Dict with customer profile and full interaction history.
    """
    # Look up by ID or email
    customer = _customers.get(customer_id)
    if not customer:
        for cust in _customers.values():
            if cust.get("email") == customer_id or cust.get("phone") == customer_id:
                customer = cust
                break

    if not customer:
        return {
            "customer_id": customer_id,
            "found": False,
            "message": "Customer not found. This may be a new customer.",
            "interactions": [],
            "channels_used": [],
        }

    # Gather tickets for this customer
    customer_tickets = [
        t for t in _tickets.values() if t["customer_id"] == customer["id"]
    ]

    return {
        "customer_id": customer["id"],
        "found": True,
        "name": customer["name"],
        "email": customer["email"],
        "phone": customer.get("phone"),
        "channels_used": customer.get("channels", []),
        "total_interactions": len(customer.get("interactions", [])),
        "interactions": customer.get("interactions", []),
        "open_tickets": [t for t in customer_tickets if t["status"] == "open"],
        "total_tickets": len(customer_tickets),
    }


async def escalate_to_human(
    ticket_id: str,
    reason: str,
    urgency: str = "standard",
) -> Dict[str, Any]:
    """
    Escalate a ticket to a human agent when AI cannot resolve the issue.

    Escalation triggers:
      - Legal mentions (lawyer, sue, legal)
      - Refund/chargeback requests
      - Pricing negotiations
      - Explicit human request
      - Sentiment < 0.3
      - Account deletion / GDPR

    Args:
        ticket_id: The ticket to escalate.
        reason: Detailed reason for escalation.
        urgency: Escalation level (standard, priority, urgent, critical).

    Returns:
        Dict with escalation details and estimated response time.
    """
    escalation_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc).isoformat()

    response_times = {
        "standard": "4 hours",
        "priority": "1 hour",
        "urgent": "30 minutes",
        "critical": "15 minutes",
    }

    escalation = {
        "escalation_id": escalation_id,
        "ticket_id": ticket_id,
        "reason": reason,
        "urgency": urgency,
        "status": "pending",
        "created_at": now,
        "estimated_response": response_times.get(urgency, "4 hours"),
    }

    _escalations[escalation_id] = escalation

    # Update ticket status if it exists
    if ticket_id in _tickets:
        _tickets[ticket_id]["status"] = "escalated"
        _tickets[ticket_id]["updated_at"] = now

    return {
        "escalation_id": escalation_id,
        "ticket_id": ticket_id,
        "urgency": urgency,
        "estimated_response": response_times.get(urgency, "4 hours"),
        "message": f"Ticket {ticket_id} escalated to human agent. Estimated response: {response_times.get(urgency, '4 hours')}.",
    }


async def send_response(
    ticket_id: str,
    message: str,
    channel: str = "webform",
) -> Dict[str, Any]:
    """
    Send a formatted response to the customer via their original channel.
    This is always the LAST tool called in an interaction.

    The response is automatically formatted based on the target channel:
      - Email: Formal with greeting/closing, up to 500 words
      - WhatsApp: Concise and conversational, ~160 chars preferred
      - Web Form: Semi-formal with next steps, up to 300 words

    Args:
        ticket_id: The ticket this response belongs to.
        message: The response text to send.
        channel: Target channel (gmail, whatsapp, webform).

    Returns:
        Dict with delivery status.
    """
    now = datetime.now(timezone.utc).isoformat()

    # Channel-specific formatting (prototype version)
    if channel == "gmail":
        formatted = f"Dear Customer,\n\n{message}\n\nBest regards,\nTechCorp Support Team"
    elif channel == "whatsapp":
        # Truncate for WhatsApp if too long
        if len(message) > 300:
            formatted = message[:297] + "..."
        else:
            formatted = message
    else:
        formatted = f"Hello,\n\n{message}\n\nThank you for contacting TechCorp Support."

    # Update ticket if exists
    if ticket_id in _tickets:
        _tickets[ticket_id]["updated_at"] = now
        _tickets[ticket_id]["last_response"] = now

    return {
        "ticket_id": ticket_id,
        "channel": channel,
        "delivery_status": "sent",
        "formatted_length": len(formatted),
        "timestamp": now,
        "message": f"Response delivered via {channel}.",
    }


async def analyze_sentiment(text: str) -> Dict[str, Any]:
    """
    Analyze customer message sentiment to determine emotional state.
    MUST be run on every incoming message before generating a response.

    Scoring:
      - 0.0 - 0.3: Very negative (escalate immediately)
      - 0.3 - 0.5: Negative (monitor closely)
      - 0.5 - 0.7: Neutral
      - 0.7 - 1.0: Positive

    Args:
        text: The customer message text to analyze.

    Returns:
        Dict with sentiment score, label, and escalation recommendation.
    """
    text_lower = text.lower()

    # Heuristic sentiment analysis (prototype – replaced by ML in production)
    score = 0.5  # Start neutral

    # Negative signals
    negative_words = [
        "angry", "furious", "terrible", "awful", "horrible", "hate",
        "worst", "ridiculous", "unacceptable", "broken", "useless",
        "disappointed", "frustrated", "annoyed",
    ]
    strong_negative = ["lawyer", "sue", "legal", "refund", "cancel"]

    for word in negative_words:
        if word in text_lower:
            score -= 0.15

    for word in strong_negative:
        if word in text_lower:
            score -= 0.25

    # ALL CAPS detection (>50% uppercase)
    alpha_chars = [c for c in text if c.isalpha()]
    if alpha_chars and sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars) > 0.5:
        score -= 0.2

    # Exclamation marks (3+)
    if text.count("!") >= 3:
        score -= 0.1

    # Positive signals
    positive_words = [
        "thank", "thanks", "great", "awesome", "excellent", "love",
        "perfect", "wonderful", "helpful", "appreciate",
    ]
    for word in positive_words:
        if word in text_lower:
            score += 0.15

    # Clamp
    score = max(0.0, min(1.0, score))

    # Determine label and recommendation
    if score < 0.3:
        label = "very_negative"
        recommendation = "escalate_immediately"
    elif score < 0.5:
        label = "negative"
        recommendation = "monitor_closely"
    elif score < 0.7:
        label = "neutral"
        recommendation = "normal_processing"
    else:
        label = "positive"
        recommendation = "reinforce_satisfaction"

    return {
        "sentiment_score": round(score, 2),
        "sentiment_label": label,
        "recommendation": recommendation,
        "signals_detected": {
            "caps_ratio": round(
                sum(1 for c in alpha_chars if c.isupper()) / max(len(alpha_chars), 1), 2
            ) if alpha_chars else 0,
            "exclamation_count": text.count("!"),
        },
    }


# ---------------------------------------------------------------------------
# MCP Server registry and runner
# ---------------------------------------------------------------------------

# Tool registry – maps tool names to their async handlers
MCP_TOOLS = {
    "search_knowledge_base": {
        "handler": search_knowledge_base,
        "description": "Search product documentation and FAQ for relevant answers to customer queries.",
        "parameters": {
            "query": {"type": "string", "description": "Natural language search query", "required": True}
        },
    },
    "create_ticket": {
        "handler": create_ticket,
        "description": "Create a support ticket to track customer interaction. ALWAYS call this first.",
        "parameters": {
            "customer_id": {"type": "string", "description": "Unique customer identifier", "required": True},
            "issue": {"type": "string", "description": "Description of the issue", "required": True},
            "priority": {"type": "string", "description": "low, medium, high, critical", "required": False},
            "channel": {"type": "string", "description": "gmail, whatsapp, webform", "required": False},
        },
    },
    "get_customer_history": {
        "handler": get_customer_history,
        "description": "Retrieve customer's past interactions across ALL channels for context.",
        "parameters": {
            "customer_id": {"type": "string", "description": "Customer ID or email", "required": True}
        },
    },
    "escalate_to_human": {
        "handler": escalate_to_human,
        "description": "Escalate to human agent when AI cannot resolve. Include full context.",
        "parameters": {
            "ticket_id": {"type": "string", "description": "Ticket to escalate", "required": True},
            "reason": {"type": "string", "description": "Reason for escalation", "required": True},
            "urgency": {"type": "string", "description": "standard, priority, urgent, critical", "required": False},
        },
    },
    "send_response": {
        "handler": send_response,
        "description": "Send formatted response to customer via their channel. Always called last.",
        "parameters": {
            "ticket_id": {"type": "string", "description": "Ticket this response belongs to", "required": True},
            "message": {"type": "string", "description": "Response text", "required": True},
            "channel": {"type": "string", "description": "gmail, whatsapp, webform", "required": False},
        },
    },
    "analyze_sentiment": {
        "handler": analyze_sentiment,
        "description": "Detect customer mood from message text. Run on every message.",
        "parameters": {
            "text": {"type": "string", "description": "Customer message to analyze", "required": True}
        },
    },
}


def list_tools() -> List[Dict[str, Any]]:
    """List all available MCP tools with their descriptions and parameters."""
    return [
        {
            "name": name,
            "description": info["description"],
            "parameters": info["parameters"],
        }
        for name, info in MCP_TOOLS.items()
    ]


async def call_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call an MCP tool by name with the given arguments.

    Args:
        tool_name: Name of the tool to invoke.
        arguments: Dictionary of arguments to pass.

    Returns:
        Tool execution result.

    Raises:
        ValueError: If tool_name is not registered.
    """
    if tool_name not in MCP_TOOLS:
        raise ValueError(f"Unknown tool: {tool_name}. Available: {list(MCP_TOOLS.keys())}")

    handler = MCP_TOOLS[tool_name]["handler"]
    return await handler(**arguments)


# ---------------------------------------------------------------------------
# Standalone runner (for testing / direct invocation)
# ---------------------------------------------------------------------------

async def _demo():
    """Demonstrate MCP server capabilities."""
    print("=" * 60)
    print("Customer Success FTE – MCP Server (Prototype)")
    print(f"Tools available: {len(MCP_TOOLS)}")
    print("=" * 60)

    for tool in list_tools():
        print(f"\n  - {tool['name']}: {tool['description']}")

    print("\n--- Demo: search_knowledge_base ---")
    result = await call_tool("search_knowledge_base", {"query": "how to reset my password"})
    print(json.dumps(result, indent=2))

    print("\n--- Demo: create_ticket ---")
    result = await call_tool(
        "create_ticket",
        {"customer_id": "customer-001", "issue": "Cannot login", "priority": "high", "channel": "gmail"},
    )
    ticket_id = result["ticket_id"]
    print(json.dumps(result, indent=2))

    print("\n--- Demo: get_customer_history ---")
    result = await call_tool("get_customer_history", {"customer_id": "customer-001"})
    print(json.dumps(result, indent=2))

    print("\n--- Demo: analyze_sentiment ---")
    result = await call_tool("analyze_sentiment", {"text": "This is RIDICULOUS! I've been waiting for HOURS!!!"})
    print(json.dumps(result, indent=2))

    print("\n--- Demo: escalate_to_human ---")
    result = await call_tool(
        "escalate_to_human",
        {"ticket_id": ticket_id, "reason": "Customer is very frustrated and requesting refund", "urgency": "priority"},
    )
    print(json.dumps(result, indent=2))

    print("\n--- Demo: send_response ---")
    result = await call_tool(
        "send_response",
        {"ticket_id": ticket_id, "message": "We apologize for the inconvenience. A senior agent will contact you within 1 hour.", "channel": "gmail"},
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(_demo())
