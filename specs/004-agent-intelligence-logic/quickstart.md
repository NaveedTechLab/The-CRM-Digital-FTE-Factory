# Quickstart Guide: Phase 4: Agent Intelligence & Logic

## Prerequisites

- Python 3.11+
- Docker and Docker Compose (for local development)
- PostgreSQL with pgvector extension (Phase 2 Core Infrastructure must be running)
- Kafka (Phase 2 Core Infrastructure must be running)
- OpenAI API key for the Agents SDK
- Environment variables configured (see .env.example)

## Setup Instructions

### 1. Clone and Navigate to Project
```bash
cd /phase-4-agent-intelligence-logic
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file based on `.env.example` and set up the required values:
```bash
# Database connection (from Phase 2)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/internal_crm

# Kafka connection (from Phase 2)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# OpenAI configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4-turbo-preview  # Recommended model for agents

# Knowledge base embeddings
EMBEDDING_MODEL=text-embedding-3-small

# Agent configuration
AGENT_TIMEOUT_SECONDS=60
CONFIDENCE_THRESHOLD=0.7  # Below this triggers escalation
MAX_CONVERSATION_HISTORY=50  # Number of messages to keep in context

# Escalation settings
ESCALATION_KEYWORDS="urgent,critical,complaint,unsatisfied,escalate,manager"
ESCALATION_ENABLED=true
```

### 4. Initialize the Knowledge Base
```bash
# Run the migration script to initialize knowledge base
python scripts/migrate_knowledge_base.py

# Or manually populate the knowledge base with articles
# The script will embed the content using OpenAI embeddings
```

### 5. Initialize the Application
```bash
# Run the agent service
python scripts/start_agent.py

# Or using directly
python -m app.main
```

## Core Components

### Agent Orchestrator
- Consumes messages from Kafka `inbound_events` topic
- Maintains idempotency by tracking processed message IDs
- Processes messages through the OpenAI Agent pipeline
- Publishes responses to `outbound_responses` topic

### OpenAI Agent
- Uses OpenAI Assistant API with custom tools
- Maintains conversation state through thread management
- Implements specialized personas for different query types

### RAG Service
- Retrieves relevant knowledge base articles using pgvector
- Performs semantic search on customer queries
- Provides context to the agent for response generation

### Tool Interface
- `create_ticket_tool`: Creates support tickets in the Phase 2 database
- `search_kb_tool`: Searches knowledge base articles
- `get_customer_history_tool`: Retrieves customer interaction history
- `escalate_tool`: Initiates human escalation process

## Usage Examples

### Processing an Incoming Message
When a message arrives in the `inbound_events` Kafka topic:

1. Agent Orchestrator consumes the message
2. Customer history is retrieved from Phase 2 DatabaseManager
3. Relevant knowledge base articles are retrieved using RAG
4. OpenAI Agent processes the query with available context
5. Appropriate tools are called based on query requirements
6. Response is published to `outbound_responses` topic
7. If confidence is below threshold, escalation is triggered

### Escalation Logic
The agent will escalate to human support when:
- Confidence score falls below CONFIDENCE_THRESHOLD
- Customer uses escalation keywords
- Query involves complex technical issues
- Customer expresses dissatisfaction
- Issue requires approval or sensitive operations

## Configuration Options

### Agent Personas
The agent can switch between different personas based on context:
- **Product Knowledge Agent**: For questions about product features and usage
- **Triage Agent**: For determining issue severity and routing
- **Support Agent**: For handling general support queries

### Tool Calling Behavior
- Tools are called asynchronously to minimize response time
- Tool outputs are validated before being used in responses
- Failed tool calls trigger fallback behaviors

### Conversation Management
- Conversation threads are maintained per customer
- Historical context is summarized to prevent token overflow
- Context is preserved across multiple interactions

### Error Handling
- Failed message processing is logged with error details
- Retry logic is applied for transient failures
- Failed messages are placed in a dead letter queue for manual review

## Monitoring and Debugging

### Logs
- Agent decision-making process is logged for audit purposes
- Tool usage and results are logged for debugging
- Escalation reasons are logged for improving agent logic

### Metrics
- Response times are tracked for performance optimization
- Escalation rates are monitored to improve agent effectiveness
- Customer satisfaction scores are collected when available

### Health Checks
- Kafka connectivity is monitored
- OpenAI API availability is checked
- Database connectivity is verified
- Knowledge base search functionality is tested

## Development Commands

### Running in Development Mode
```bash
# With debug logging
export LOG_LEVEL=DEBUG
python scripts/start_agent.py
```

### Running Tests
```bash
# Run all unit tests
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

## Troubleshooting

### Common Issues

#### OpenAI API Access
- Ensure the API key is valid and has the required permissions
- Check that the organization and billing details are correct
- Verify the model names are available in your region

#### Kafka Connection
- Verify Kafka is running and accessible at the configured address
- Check that the 'inbound_events' and 'outbound_responses' topics exist
- Ensure proper network connectivity between services

#### Database Connection
- Confirm Phase 2 DatabaseManager from is accessible
- Verify database credentials and connection string
- Check that required tables exist and have proper indexes

#### Knowledge Base Search
- Verify pgvector extension is properly installed
- Ensure knowledge base articles have been properly embedded
- Check that the embedding dimensions match between queries and stored vectors

### Debugging Tips

#### Enable Verbose Logging
Set `LOG_LEVEL=DEBUG` in your environment to get detailed logs about agent decision-making and tool usage.

#### Test Individual Components
- Test the RAG service in isolation
- Validate tool functions separately
- Check Kafka consumer/producer independently

#### Monitor Agent Performance
Track confidence scores and escalation rates to identify areas for improvement in the agent's knowledge base or decision logic.