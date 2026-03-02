# Customer Success Agent

Production Customer Success Agent using OpenAI Agents SDK for multi-channel customer support.

## Overview

The Customer Success Agent is an intelligent system that processes customer messages from multiple channels (Gmail, WhatsApp, Web Forms) using OpenAI's Assistant API. The agent maintains conversation state, retrieves relevant knowledge base articles using RAG (Retrieval-Augmented Generation), and makes intelligent decisions about when to escalate issues to human support.

## Architecture

The system consists of several key components:

- **Agent Orchestrator**: Kafka consumer that processes inbound messages and coordinates agent responses
- **OpenAI Agent**: Uses OpenAI Assistant API with specialized personas for different query types
- **RAG Service**: Retrieves relevant knowledge base articles using pgvector for semantic search
- **Tool Interface**: Provides integration with customer history, ticket creation, and escalation systems
- **Response Publisher**: Wraps agent responses in OutboundMessage and publishes to Kafka

## Prerequisites

- Python 3.11+
- PostgreSQL with pgvector extension
- Apache Kafka
- OpenAI API key
- Docker and Docker Compose (for local development)

## Setup

1. Clone the repository and navigate to the agent directory:
   ```bash
   cd phase-4-agent-intelligence-logic
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables by creating a `.env` file based on the template:
   ```bash
   # Database connection (from Phase 2)
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/internal_crm

   # Kafka connection (from Phase 2)
   KAFKA_BOOTSTRAP_SERVERS=localhost:9092

   # OpenAI configuration
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_MODEL=gpt-4-turbo-preview

   # Knowledge base embeddings
   EMBEDDING_MODEL=text-embedding-3-small

   # Agent configuration
   AGENT_TIMEOUT_SECONDS=60
   CONFIDENCE_THRESHOLD=0.7
   MAX_CONVERSATION_HISTORY=50

   # Escalation settings
   ESCALATION_KEYWORDS="urgent,critical,complaint,unsatisfied,escalate,manager"
   ESCALATION_ENABLED=true
   ```

4. Initialize the knowledge base:
   ```bash
   python scripts/migrate_knowledge_base.py
   ```

5. Start the agent service:
   ```bash
   python scripts/start_agent.py
   ```

   Or alternatively:
   ```bash
   python -m app.main
   ```

## Usage

The agent automatically processes messages from the Kafka `inbound_events` topic and publishes responses to the `outbound_responses` topic. The system maintains conversation state, retrieves customer history, performs semantic search on the knowledge base, and makes intelligent escalation decisions based on confidence scores and predefined triggers.

### Manual Testing

You can manually trigger message processing using the `/process-message` endpoint:

```bash
curl -X POST http://localhost:8000/process-message \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "customer-12345",
    "message_content": "I am having trouble with the login functionality",
    "channel": "webform",
    "conversation_id": "conv-67890"
  }'
```

## Configuration

### Agent Personas

The agent can switch between different personas based on context:

- **Product Knowledge Agent**: For questions about product features and usage
- **Triage Agent**: For determining issue severity and routing
- **Support Agent**: For handling general support queries

### Escalation Logic

The agent will escalate to human support when:
- Confidence score falls below the configured threshold (default 0.7)
- Customer uses escalation keywords
- Query involves complex technical issues
- Customer expresses dissatisfaction
- Issue requires approval or sensitive operations

## API Endpoints

- `GET /health`: Check agent operational status
- `POST /process-message`: Manually process a customer message
- `GET /metrics`: Retrieve operational metrics
- `GET /conversation/{conversation_id}`: Get conversation history

## Development

### Running Tests

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run end-to-end tests
pytest tests/integration/test_end_to_end.py
```

### Docker Deployment

```bash
# Build and run with Docker
docker-compose up --build

# Run only the agent service
docker-compose up agent-service
```

## Error Handling and Resilience

- Failed message processing is logged with error details
- Retry logic is applied for transient failures
- Failed messages are placed in a dead letter queue for manual review
- Circuit breaker pattern for service outages
- Graceful degradation when knowledge base unavailable