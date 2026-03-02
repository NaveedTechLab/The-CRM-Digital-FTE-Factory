# Customer Success FTE Specification

## Purpose
Handle routine customer support queries with speed and consistency across multiple channels.

## Supported Channels
| Channel | Identifier | Response Style | Max Length |
|---------|------------|----------------|------------|
| Email (Gmail) | Email address | Formal, detailed | 500 words |
| WhatsApp | Phone number | Conversational, concise | 160 chars preferred |
| Web Form | Email address | Semi-formal | 300 words |

## Scope

### In Scope
- Product feature questions
- How-to guidance
- Bug report intake
- Feedback collection
- Cross-channel conversation continuity
- Sentiment analysis and monitoring
- Automatic ticket creation and tracking

### Out of Scope (Escalate)
- Pricing negotiations
- Refund requests
- Legal/compliance questions
- Angry customers (sentiment < 0.3)
- Account deletion requests
- Custom contract terms

## Tools
| Tool | Purpose | Constraints |
|------|---------|-------------|
| search_knowledge_base | Find relevant docs | Max 5 results |
| create_ticket | Log interactions | Required for all chats; include channel |
| get_customer_history | Check prior context | Lookup by email |
| escalate_to_human | Hand off complex issues | Include full context |
| send_response | Reply to customer | Channel-appropriate formatting |
| analyze_sentiment | Detect customer mood | Run on every message |

## Performance Requirements
- Response time: <3 seconds (processing), <30 seconds (delivery)
- Accuracy: >85% on test set
- Escalation rate: <20%
- Cross-channel identification: >95% accuracy
- Uptime: >99.9%

## Guardrails
- NEVER discuss competitor products
- NEVER promise features not in docs
- ALWAYS create ticket before responding
- ALWAYS check sentiment before closing
- ALWAYS use channel-appropriate tone
- NEVER share internal system details
- NEVER process financial transactions

## Architecture Components
| Component | Technology | Purpose |
|-----------|-----------|---------|
| API Layer | FastAPI | Channel webhooks and endpoints |
| Agent | OpenAI Agents SDK | Autonomous customer support |
| Database | PostgreSQL + pgvector | CRM, tickets, vector search |
| Message Queue | Apache Kafka | Event streaming between services |
| Rate Limiting | Redis | API rate limit management |
| Containerization | Docker | Service packaging |
| Orchestration | Kubernetes | Production deployment and scaling |
| Web Form | Next.js / React | Customer-facing support form |

## Data Model
### Core Tables
- **customers:** id, email, name, phone, channel, created_at
- **tickets:** id, customer_id, subject, description, status, priority, channel, category, created_at
- **messages:** id, ticket_id, sender_type, content, direction, channel, created_at
- **vector_embeddings:** id, entity_type, entity_id, embedding vector(1536), content_preview

## Channel Integration
| Channel | Intake Method | Response Method |
|---------|--------------|-----------------|
| Gmail | Gmail API webhook/polling | Send via Gmail API |
| WhatsApp | Twilio webhook handler | Reply via Twilio API |
| Web Form | FastAPI POST endpoint + Next.js UI | API response + Email notification |

## Deployment
- **Infrastructure:** Kubernetes cluster with auto-scaling
- **Minimum replicas:** API (2), Workers (3), Dispatcher (2)
- **Auto-scale trigger:** CPU > 70% utilization
- **Health checks:** HTTP liveness and readiness probes

## 24-Hour Multi-Channel Test Criteria
1. Web Form Traffic: 100+ submissions over 24 hours
2. Email Simulation: 50+ Gmail messages processed
3. WhatsApp Simulation: 50+ WhatsApp messages processed
4. Cross-Channel: 10+ customers contact via multiple channels
5. Uptime > 99.9%
6. P95 latency < 3 seconds
7. Escalation rate < 25%
8. No message loss
