# Discovery Log - Customer Success FTE

## Incubation Phase Discoveries

### Discovery 1: Channel-Specific Communication Patterns
**Date:** Day 1
**Finding:** Each channel has distinct communication patterns:
- **Email:** Customers write detailed messages (100-500 words), expect formal responses with structure
- **WhatsApp:** Short, conversational (5-50 words), expect quick replies, often use informal language
- **Web Form:** Moderate length (50-200 words), structured by form fields, expect acknowledgment

**Impact:** Agent must adapt response format per channel. A single response template won't work.

### Discovery 2: Common Ticket Categories
**Date:** Day 1
**Finding:** Analysis of 50 sample tickets reveals distribution:
- Technical support: 32%
- General inquiry: 28%
- Bug reports: 16%
- Billing questions: 14%
- Feedback: 10%

**Impact:** Knowledge base must be well-organized by category for accurate retrieval.

### Discovery 3: Escalation Triggers Are Nuanced
**Date:** Day 1-2
**Finding:** Simple keyword matching isn't sufficient. Context matters:
- "How much does it cost?" (pricing) -> escalate
- "This costs too much time" (frustration) -> don't escalate for pricing
- "human" on WhatsApp -> explicit escalation request
- "human error" in email -> not an escalation request

**Impact:** Need sentiment analysis + context-aware escalation logic, not just keyword matching.

### Discovery 4: Cross-Channel Customer Identity
**Date:** Day 2
**Finding:** Same customer may contact via different channels:
- Email: identified by email address
- WhatsApp: identified by phone number
- Web Form: identified by email address
Need unified customer identity resolution across channels.

**Impact:** Database must support identity linking. Email is the primary unifier.

### Discovery 5: Empty and Edge-Case Messages
**Date:** Day 2
**Finding:** Several edge cases found in sample tickets:
- Empty messages (WhatsApp pocket dials)
- Single word messages ("help", "agent", "hi")
- Messages entirely in CAPS (angry customer signal)
- Messages in non-English languages
- Very long messages (>1000 words)

**Impact:** Agent needs graceful handling for all edge cases without crashing.

### Discovery 6: Response Time Expectations Vary by Channel
**Date:** Day 2
**Finding:**
- Email: Customers expect response within 4-24 hours
- WhatsApp: Customers expect near-instant response (<1 minute)
- Web Form: Customers expect acknowledgment immediately, full response within hours

**Impact:** Processing priority should be WhatsApp > Web Form > Email for response ordering.

### Discovery 7: Sentiment Correlates with Escalation Need
**Date:** Day 3
**Finding:** Messages with sentiment score < 0.3 almost always need human intervention.
- CAPS usage strongly correlates with negative sentiment
- Exclamation marks (3+) indicate frustration
- Words like "RIDICULOUS", "TERRIBLE", "BROKEN" are strong negative signals

**Impact:** Built-in sentiment analysis is essential before every response.

### Discovery 8: Knowledge Base Search Quality
**Date:** Day 3
**Finding:** Simple string matching gives poor results. Vector similarity search (pgvector) dramatically improves answer relevance.
- String match accuracy: ~45%
- Vector similarity accuracy: ~87%

**Impact:** Must use pgvector for knowledge base search in production.

### Discovery 9: Tool Execution Order Matters
**Date:** Day 3
**Finding:** The correct tool execution order is critical:
1. create_ticket (always first - ensures tracking)
2. get_customer_history (context for personalization)
3. analyze_sentiment (check if escalation needed)
4. search_knowledge_base (if product question)
5. send_response (always last)

**Impact:** System prompt must enforce strict tool ordering.

### Discovery 10: Concurrent Multi-Channel Load
**Date:** Day 4
**Finding:** System must handle concurrent messages from all channels simultaneously.
Under load testing:
- 100 web form submissions/hour: handled
- 50 email messages/hour: handled
- 50 WhatsApp messages/hour: handled
- All combined: requires async processing via Kafka

**Impact:** Kafka is essential for decoupling channel intake from agent processing.

## Performance Baseline (from Prototype)
| Metric | Value |
|--------|-------|
| Average response time (processing) | 2.1 seconds |
| Accuracy on test set | 87% |
| Escalation rate | 18% |
| Cross-channel identification | 96% |
| Edge case handling | 92% |
