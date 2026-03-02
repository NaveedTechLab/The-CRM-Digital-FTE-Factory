# Research & Technical Decisions: Phase 4: Agent Intelligence & Logic

## OpenAI Agents SDK Implementation

### Decision: Using OpenAI Assistant API vs Custom Agent Framework
- **Chosen**: OpenAI Assistant API with custom tools
- **Rationale**: The Assistant API provides built-in memory management, thread handling, and state preservation, which aligns well with our requirement to maintain conversation state using Phase 2 DatabaseManager. It also provides reliable tool calling capabilities for our custom functions.
- **Alternatives considered**:
  - Custom agent with LangGraph/LangChain - More complex but offers greater control
  - OpenAI Functions API - Less state management but simpler tool calling

### Decision: Agent Persona and Instructions
- **Chosen**: Specialized Customer Success Agent with role-specific personas
- **Rationale**: Different personas (Product Knowledge, Triage, Support) can be activated based on conversation context, allowing for specialized responses while maintaining consistency
- **Implementation**: System prompts will be dynamically selected based on customer query type and conversation state

## Kafka Consumer Implementation

### Decision: aiokafka vs confluent-kafka-python
- **Chosen**: aiokafka for asynchronous consumption
- **Rationale**: Better integration with async Python ecosystem, non-blocking operations that suit agent processing patterns
- **Alternatives considered**: confluent-kafka-python - synchronous but more mature, python-kafka - also synchronous

### Decision: Idempotency and Message Deduplication
- **Chosen**: Consumer group with message key hashing + database tracking
- **Rationale**: Using customer ID as message key ensures ordering per customer while tracking processed message IDs in the database prevents duplicate processing
- **Implementation**: Store message ID and processing status in a 'processed_messages' table

## RAG (Retrieval-Augmented Generation) Implementation

### Decision: pgvector vs Dedicated Vector Database
- **Chosen**: pgvector integrated with existing PostgreSQL
- **Rationale**: Maintains consistency with existing architecture, reduces operational complexity, leverages existing connection pooling and backup strategies
- **Alternatives considered**: Pinecone, Weaviate, ChromaDB - would require separate infrastructure

### Decision: Embedding Model Selection
- **Chosen**: OpenAI text-embedding-3-small model
- **Rationale**: Good balance of performance and cost, consistent with OpenAI Agents SDK usage, sufficient dimensionality for semantic search
- **Alternatives considered**: Sentence Transformers (local) - no additional API dependency but requires model hosting

## Tool Integration Design

### Decision: Tool Calling Interface Architecture
- **Chosen**: Pydantic models for tool schemas with async function wrappers
- **Rationale**: Clean integration with FastAPI ecosystem, proper type validation, easy testing of individual tools
- **Implementation**: Each tool will have a Pydantic schema for parameters and an async function for execution

### Decision: Ticket Management Integration
- **Chosen**: Direct integration with Phase 2 DatabaseManager
- **Rationale**: Consistent with existing architecture, maintains single source of truth for customer data
- **Implementation**: Reuse existing ticket models and CRUD operations from Phase 2

## Response Routing and Escalation Logic

### Decision: Confidence Scoring Method
- **Chosen**: Multi-factor confidence scoring combining LLM self-assessment, KB relevance scores, and triage rules
- **Rationale**: More robust than single metric, allows for nuanced escalation decisions
- **Factors**: Answer certainty, KB article relevance, keyword matching for escalation triggers

### Decision: Escalation Triggers
- **Chosen**: Combination of keyword matching, confidence thresholds, and conversation context
- **Rationale**: Prevents both false positives and missed escalations
- **Triggers**: Explicit customer requests ("speak to human"), anger indicators, repeated unanswered questions, critical issue keywords

## Error Handling and Resilience

### Decision: Retry and Circuit Breaker Strategy
- **Chosen**: Exponential backoff with jitter for transient failures, circuit breaker for service outages
- **Rationale**: Maintains system stability during partial outages while maximizing successful processing
- **Implementation**: Use tenacity for retry logic, implement circuit breaker pattern for external service calls

### Decision: Graceful Degradation
- **Chounced**: Fallback responses when KB unavailable, manual ticket creation when automation fails
- **Rationale**: Ensures service remains available even when some components are degraded
- **Implementation**: Predefined fallback responses, direct database insertion for ticket creation when tools fail