# Phase 3: Multi-Channel Ingestion

Production-grade ingestion services for the Customer Success Digital FTE system. This module handles customer messages from multiple channels (Gmail, WhatsApp via Twilio, and Web Form) and processes them through a unified pipeline.

## Features

- **Multi-Channel Support**: Handles messages from Gmail, WhatsApp (Twilio), and Web Form
- **Unified Message Schema**: All channels normalize to a common `InboundMessage` format
- **Identity Resolution**: Links messages to existing customers or creates new placeholder records
- **Kafka Integration**: Publishes normalized messages to the `inbound_events` topic
- **Security**: Implements API key validation for web forms and Twilio signature verification
- **Asynchronous Processing**: Non-blocking message handling for high throughput

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Gmail API   │    │  Twilio Webhook  │    │  Web Form API   │
│   (Polling)   │    │     (POST)       │    │    (POST)       │
└─────────┬─────┘    └─────────┬────────┘    └─────────┬───────┘
          │                    │                       │
          └────────────────────┼───────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Message Normalizer │
                    │ (Unified Schema)    │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Identity Resolver  │
                    │ (Customer Lookup)   │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Kafka Publisher   │
                    │ (inbound_events)    │
                    └─────────────────────┘
```

## Components

### Models
- `InboundMessage`: Unified schema for all incoming messages
- `ChannelPayload`: Raw payload representation
- `KafkaEvent`: Kafka event tracking
- `NormalizationRule`: Rules for transforming channel-specific data

### Services
- `IngestionService`: Main orchestration service (Receive → Normalize → Identify → Publish)
- `MessageNormalizer`: Converts channel-specific formats to unified schema
- `IdentityResolver`: Integrates with Phase 2 DatabaseManager for customer lookups
- `KafkaProducerService`: Handles message publishing to Kafka
- `TwilioValidator`: Validates Twilio webhook signatures for security

### Routes
- `/webhooks/twilio-whatsapp`: Twilio WhatsApp webhook endpoint
- `/api/v1/support-form`: Web form submission endpoint with API key validation
- `/health`, `/metrics`, `/ready`: Health check endpoints

## Security

- **Twilio Signature Verification**: All WhatsApp webhooks are validated using Twilio's signature mechanism
- **API Key Authentication**: Web form submissions require a valid API key in the `X-API-Key` header
- **Input Validation**: All payloads are validated against strict schemas

## Environment Variables

```bash
# Database connection (from Phase 2)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/internal_crm

# Kafka connection (from Phase 2)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_INBOUND_EVENTS=inbound_events

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

## Usage

### Running the Service

```bash
# Install dependencies
pip install -r requirements.txt

# Start the main service
python scripts/start_server.py

# Or with uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start the Gmail poller separately
python scripts/gmail_poller.py
```

### API Endpoints

#### WhatsApp Webhook
```
POST /webhooks/twilio-whatsapp
```
Configure this as your Twilio webhook URL for WhatsApp messages.

#### Web Form Submission
```
POST /api/v1/support-form
Headers: X-API-Key: your-api-key
```

#### Health Checks
```
GET /health
GET /metrics
GET /ready
```

## Testing

Run the complete test suite:
```bash
pytest tests/ -v
```

Or run specific test suites:
```bash
pytest tests/unit/ -v
pytest tests/integration/ -v
```

## Verification

The system has been verified with the following test scenarios:

1. **Gmail Message Ingestion**: Simulated via the Gmail poller service
2. **WhatsApp Message Ingestion**: Verified with Twilio webhook signature validation
3. **Web Form Ingestion**: Confirmed with API key validation
4. **Message Normalization**: All channels produce consistent `InboundMessage` format
5. **Identity Resolution**: Customers are looked up/created correctly
6. **Kafka Publishing**: All messages successfully published to `inbound_events` topic

## Dependencies

- FastAPI: Web framework
- Pydantic: Data validation
- SQLAlchemy: Database ORM
- aiokafka: Async Kafka client
- google-api-python-client: Gmail API integration
- twilio: Twilio API client
- python-dotenv: Environment variable management

## Project Structure

```
phase-3-multi-channel-ingestion/
├── app/
│   ├── models/           # Pydantic models
│   ├── services/         # Business logic services
│   ├── routes/           # API endpoints
│   ├── config/           # Configuration and settings
│   ├── middleware/       # Security and request processing middleware
│   └── main.py          # FastAPI application
├── scripts/
│   ├── start_server.py  # Server startup script
│   └── gmail_poller.py  # Gmail polling service
├── tests/
│   ├── unit/            # Unit tests
│   └── integration/     # Integration tests
├── requirements.txt     # Dependencies
└── README.md           # This file
```

## Error Handling

The system implements comprehensive error handling:

- Malformed payloads are rejected with 400 status
- Security validation failures return 403 status
- Kafka delivery failures trigger retry with exponential backoff
- Failed messages are tracked in the system for monitoring
- All operations are logged for debugging and monitoring