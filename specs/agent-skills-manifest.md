# Agent Skills Manifest - Customer Success Digital FTE

## Overview
This manifest defines the 5 core skills of the Customer Success Digital FTE agent, as discovered and refined during the Incubation Phase and implemented in the Specialization Phase.

---

## Skill 1: Knowledge Retrieval

| Property | Value |
|----------|-------|
| **Name** | Knowledge Retrieval |
| **Tool** | `search_knowledge_base` |
| **Purpose** | Find relevant product documentation and FAQ answers |
| **Input** | Customer query (natural language) |
| **Output** | Up to 5 ranked results with relevance scores |
| **Implementation** | pgvector similarity search (1536-dim embeddings) via RAG service |
| **Accuracy** | 87% (vector search) vs 45% (string matching) |
| **Latency** | Avg 0.385s, Max 0.752s |

### Behavior
1. Convert customer query to embedding vector using OpenAI embeddings API
2. Perform cosine similarity search against `knowledge_base` table
3. Return top-5 matches with confidence scores
4. Filter results below 0.6 confidence threshold
5. If no results found, acknowledge gap and suggest escalation

### Constraints
- Maximum 5 results returned per query
- Minimum confidence threshold: 0.6
- Fallback to keyword search if vector search unavailable

---

## Skill 2: Sentiment Analysis

| Property | Value |
|----------|-------|
| **Name** | Sentiment Analysis |
| **Tool** | `analyze_sentiment` |
| **Purpose** | Detect customer mood and emotional state |
| **Input** | Customer message text |
| **Output** | Sentiment score (0.0-1.0), sentiment label, escalation recommendation |
| **Implementation** | OpenAI-powered analysis + heuristic signals |
| **Accuracy** | >90% on test set |

### Behavior
1. Analyze message text for emotional indicators
2. Check for strong negative signals: ALL CAPS (>50%), profanity, exclamation marks (3+)
3. Compute sentiment score from 0.0 (very negative) to 1.0 (very positive)
4. Apply escalation recommendation:
   - Score < 0.3: **Escalate immediately** with empathetic acknowledgment
   - Score 0.3-0.5: **Monitor closely**, provide empathetic response
   - Score 0.5-0.7: **Normal processing**
   - Score > 0.7: **Positive interaction**, reinforce satisfaction

### Constraints
- MUST run on every incoming message before response generation
- NEVER dismiss negative sentiment signals
- ALL CAPS detection requires >50% uppercase characters

---

## Skill 3: Escalation Decision

| Property | Value |
|----------|-------|
| **Name** | Escalation Decision |
| **Tool** | `escalate_to_human` |
| **Purpose** | Determine when and how to hand off to human agents |
| **Input** | Ticket ID, escalation reason, full conversation context |
| **Output** | Escalation ID, assigned level, estimated response time |
| **Implementation** | Rule-based triggers + sentiment-based logic |

### Behavior
1. Check for immediate escalation triggers:
   - Legal mentions: "lawyer", "legal", "sue", "attorney"
   - Refund/chargeback requests
   - Pricing/contract negotiations
   - Explicit human request: "human", "agent", "manager"
   - Account/data deletion requests
2. Check sentiment-based triggers (sentiment < 0.3)
3. Check context-based triggers (repeated contact 3+, data loss, security)
4. Assign escalation level:

| Level | Trigger | Response Time | Handler |
|-------|---------|---------------|---------|
| L1 - Standard | General questions AI can't answer | 4 hours | Support team |
| L2 - Priority | Billing, refunds, frustrated customer | 1 hour | Senior support |
| L3 - Urgent | Legal threats, data loss, security | 30 minutes | Team lead |
| L4 - Critical | System-wide issues, legal action | 15 minutes | VP of Support |

### Constraints
- MUST include: ticket ID, channel, reason, full conversation history, sentiment score, suggested next action
- NEVER attempt to handle legal, refund, or pricing queries autonomously
- ALWAYS preserve full context for the human agent

---

## Skill 4: Channel Adaptation

| Property | Value |
|----------|-------|
| **Name** | Channel Adaptation |
| **Tool** | Integrated into `send_response` |
| **Purpose** | Format responses appropriately for each communication channel |
| **Input** | Raw response text, target channel |
| **Output** | Channel-formatted response |
| **Implementation** | Channel-specific formatters in response delivery (Phase 5) |

### Channel Formatting Rules

| Channel | Greeting | Tone | Max Length | Closing | Special Rules |
|---------|----------|------|-----------|---------|---------------|
| Email (Gmail) | "Dear [Name]," | Formal, detailed | 500 words | "Best regards,\nTechCorp Support" | Use paragraphs, bullet points for lists |
| WhatsApp | "Hi [Name]!" | Conversational, concise | 160 chars preferred | "Let me know if you need anything!" | Short sentences, minimal formatting |
| Web Form | "Hello [Name]," | Semi-formal, clear | 300 words | "Thank you for contacting us." | Structured with next steps |

### Behavior
1. Detect original channel from message metadata
2. Apply channel-specific formatting rules
3. Adjust response length to channel limits
4. Add appropriate greeting and closing
5. Validate formatted response before sending

### Constraints
- NEVER send a long email-style response via WhatsApp
- ALWAYS include greeting and closing for email
- Web form responses should include clear next steps
- Response MUST be in the customer's original channel

---

## Skill 5: Customer Identification

| Property | Value |
|----------|-------|
| **Name** | Customer Identification |
| **Tool** | Integrated into message processing pipeline |
| **Purpose** | Identify and link customers across multiple channels |
| **Input** | Channel identifier (email address or phone number) |
| **Output** | Unified customer profile with cross-channel history |
| **Implementation** | Identity resolver service (Phase 3) + PostgreSQL customer tables |
| **Accuracy** | 96% cross-channel identification |

### Resolution Strategy
1. **Email channel**: Look up by email address (primary key)
2. **WhatsApp channel**: Look up by phone number → link to email if found
3. **Web Form channel**: Look up by email address
4. **Cross-channel linking**: Email is the primary unifier across all channels

### Behavior
1. Extract identifier from incoming message (email or phone)
2. Query `customers` table for existing match
3. If found: retrieve full profile including all channel identifiers
4. If not found: create new customer record
5. Merge conversation history across all channels for context
6. Update `last_interaction` timestamp and channel

### Constraints
- Email is the PRIMARY identifier for cross-channel resolution
- Phone number is SECONDARY (WhatsApp → email linking)
- NEVER create duplicate customer records for the same person
- ALWAYS merge history when cross-channel match is found
- Customer context MUST include interactions from ALL channels

---

## Skill Interaction Flow

```
Incoming Message
    │
    ▼
[Customer Identification] ─── Resolve/create customer profile
    │
    ▼
[Sentiment Analysis] ─── Score 0.0-1.0, check escalation triggers
    │
    ├── Score < 0.3 ──► [Escalation Decision] ──► Human Agent
    │
    ▼
[Knowledge Retrieval] ─── Search KB for relevant answers
    │
    ▼
[Channel Adaptation] ─── Format response for channel
    │
    ▼
Response Delivered
```

## Tool Execution Order (Enforced)
1. `create_ticket` — Always first, ensures tracking
2. `get_customer_history` — Context for personalization
3. `analyze_sentiment` — Check if escalation needed
4. `search_knowledge_base` — If product question
5. `send_response` — Always last, channel-adapted
