# Escalation Rules - TechCorp Customer Success

## Immediate Escalation (No AI Response)
These triggers MUST escalate to a human agent immediately:

1. **Legal Mentions:** Customer uses words like "lawyer", "legal", "sue", "attorney", "litigation"
2. **Refund Requests:** Customer explicitly requests a refund or chargeback
3. **Pricing Negotiations:** Customer asks about custom pricing, discounts, or contract terms
4. **Explicit Human Request:** Customer says "human", "agent", "representative", "manager", or "talk to someone"
5. **Account Deletion:** Customer requests account or data deletion (GDPR/privacy)

## Sentiment-Based Escalation
- **Sentiment score < 0.3:** Escalate immediately with empathetic acknowledgment
- **Profanity or aggressive language:** Escalate with priority "urgent"
- **ALL CAPS messages (>50% uppercase):** Treat as frustrated, consider escalation

## Context-Based Escalation
- **Repeated contact (3+ times on same issue):** Escalate with full conversation history
- **Data loss reported:** Escalate as "urgent" with technical context
- **Security incident reported:** Escalate as "critical" to security team
- **HIPAA/compliance questions:** Escalate to compliance team

## Escalation Levels

| Level | Trigger | Response Time | Handler |
|-------|---------|---------------|---------|
| L1 - Standard | General questions AI can't answer | 4 hours | Support team |
| L2 - Priority | Billing, refunds, frustrated customer | 1 hour | Senior support |
| L3 - Urgent | Legal threats, data loss, security | 30 minutes | Team lead |
| L4 - Critical | System-wide issues, legal action | 15 minutes | VP of Support |

## Escalation Message Template
When escalating, the AI MUST include:
- **Ticket ID** and customer details
- **Channel** the customer contacted from
- **Reason** for escalation (specific trigger)
- **Full conversation history**
- **Customer sentiment score**
- **Suggested next action** for the human agent

## What NOT to Escalate
- Product feature questions (search knowledge base first)
- How-to questions (provide documentation links)
- Bug reports (create ticket, acknowledge, inform timeline)
- Feedback/feature requests (thank customer, log in system)
- General greetings or thank-you messages
