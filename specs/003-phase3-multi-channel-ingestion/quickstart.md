# Quickstart Guide: Phase 3: Multi-Channel Ingestion

## Prerequisites

- Python 3.11+
- Docker and Docker Compose (for local development)
- PostgreSQL (Phase 2 Core Infrastructure must be running)
- Kafka (Phase 2 Core Infrastructure must be running)
- Google Cloud Project with Gmail API enabled
- Twilio account for WhatsApp integration
- Environment variables configured (see .env.example)

## Setup Instructions

### 1. Clone and Navigate to Project
```bash
cd /phase-3-multi-channel-ingestion
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

# Twilio configuration for WhatsApp
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp_number

# Gmail API configuration
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_REFRESH_TOKEN=your_refresh_token
GMAIL_POLLING_INTERVAL=30  # seconds

# Web Form API Key
WEB_FORM_API_KEY=your_api_key
```

### 4. Initialize the Application
```bash
# Run the main application
python scripts/start_server.py

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Start Gmail Polling Service (separate terminal)
```bash
python scripts/gmail_poller.py
```

## Webhook Endpoints

### Twilio WhatsApp Webhook
- Endpoint: `POST /webhooks/twilio-whatsapp`
- Expected payload format from Twilio
- Secured with Twilio signature validation

### Web Support Form Endpoint
- Endpoint: `POST /api/v1/support-form`
- Requires `X-API-Key` header for authentication
- Accepts JSON payload with message content

## Testing

### Unit Tests
```bash
# Run all unit tests
pytest tests/unit/

# Run specific test file
pytest tests/unit/test_ingestion_service.py
```

### Integration Tests
```bash
# Run integration tests
pytest tests/integration/

# Test ingestion flow
pytest tests/integration/test_ingestion_flow.py
```

### End-to-End Tests
```bash
# Test complete flow from webhook to Kafka
pytest tests/integration/test_end_to_end.py
```

## Configuration Options

### Message Processing Pipeline
The ingestion service follows this pipeline:
1. **Receive**: Accept message from any channel
2. **Validate**: Verify security credentials (webhook signatures, API keys)
3. **Normalize**: Convert to unified InboundMessage schema
4. **Identify**: Lookup customer identity using DatabaseManager
5. **Publish**: Send to Kafka 'inbound_events' topic

### Error Handling
- Malformed payloads are rejected with 400 status
- Security validation failures return 403 status
- Kafka delivery failures trigger retry with exponential backoff
- Failed messages are logged to dead letter queue

### Monitoring
- Health check endpoint: `GET /health`
- Metrics endpoint: `GET /metrics`
- Logging configured to output structured JSON logs

## Development Commands

### Running in Development Mode
```bash
# With auto-reload
uvicorn app.main:app --reload

# With specific host/port
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Running Tests with Coverage
```bash
# Run tests with coverage report
pytest --cov=app --cov-report=html
```

### Docker Deployment
```bash
# Build and run with Docker
docker-compose up --build

# Run only the ingestion service
docker-compose up ingestion-service
```

## Troubleshooting

### Common Issues

#### Gmail API Access
- Ensure the refresh token is valid and has the required scopes
- Check that the Google Cloud Project has Gmail API enabled
- Verify the service account has proper permissions

#### Twilio Webhook Validation
- Confirm that the auth token matches what's configured in Twilio
- Ensure webhook URL is publicly accessible (use ngrok for local development)

#### Kafka Connection
- Verify Kafka is running and accessible at the configured address
- Check that the 'inbound_events' topic exists
- Ensure proper network connectivity between services

#### Database Connection
- Confirm DatabaseManager from Phase 2 is accessible
- Verify database credentials and connection string
- Check that required tables exist

### Debugging Tips

#### Enable Verbose Logging
Set `LOG_LEVEL=DEBUG` in your environment to get detailed logs.

#### Test Individual Components
- Test the message normalizer in isolation
- Validate Kafka producer separately
- Test database lookups independently

#### Check Message Flow
Monitor the processed_status field in the InboundMessage to track where messages are getting stuck in the pipeline.