# Quickstart Guide: Phase 5: Response Delivery & Egress

## Prerequisites

- Python 3.11+
- Docker and Docker Compose (for local development)
- PostgreSQL with pgvector extension (Phase 2 Core Infrastructure must be running)
- Kafka (Phase 2 Core Infrastructure must be running)
- Redis for rate limiting
- Gmail API credentials for email delivery
- Twilio credentials for WhatsApp delivery
- Environment variables configured (see .env.example)

## Setup Instructions

### 1. Clone and Navigate to Project
```bash
cd /phase-5-response-delivery-egress
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

# Redis for rate limiting
REDIS_URL=redis://localhost:6379/0

# Gmail API configuration
GMAIL_CREDENTIALS_PATH=/path/to/gmail-credentials.json
GMAIL_TOKEN_PATH=/path/to/token.json
GMAIL_SENDER_EMAIL=your-email@gmail.com

# Twilio configuration
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890

# Rate limiting settings
RATE_LIMIT_WINDOW_SECONDS=60
GMAIL_MAX_REQUESTS_PER_MINUTE=250
TWILIO_MAX_REQUESTS_PER_MINUTE=100

# Delivery settings
DELIVERY_RETRY_ATTEMPTS=3
DELIVERY_RETRY_DELAY_BASE=5
DELIVERY_TIMEOUT_SECONDS=30

# Application settings
APP_NAME=Response Delivery Service
DEBUG=false
HOST=0.0.0.0
PORT=8001
```

### 4. Initialize the Application
```bash
# Run the response dispatcher service
python scripts/start_dispatcher.py

# Or using directly
python -m app.main
```

## Core Components

### Response Dispatcher
- Consumes messages from Kafka `outbound_responses` topic
- Routes messages based on `channel_destination` metadata
- Maintains delivery status tracking
- Handles retry logic for failed deliveries

### Gmail Service
- Delivers responses via Gmail API with proper threading
- Uses In-Reply-To and References headers to maintain conversation threads
- Implements rate limiting to prevent account suspension
- Tracks delivery status and error conditions

### WhatsApp Service
- Delivers responses via Twilio WhatsApp API
- Formats messages appropriately for WhatsApp
- Implements rate limiting per Twilio guidelines
- Handles delivery receipts and error tracking

### Web Notification Service
- Delivers responses via HTTP webhooks to customer endpoints
- Simulates on-site alerts for web form responses
- Tracks delivery status and response codes
- Handles retry for failed webhook deliveries

## Usage Examples

### Processing an Outbound Message
When a message arrives in the `outbound_responses` Kafka topic:

1. Response Dispatcher consumes the message
2. Message is routed based on `channel_destination` field
3. Appropriate delivery service attempts to deliver the message
4. Delivery status is tracked in the database
5. If delivery fails temporarily, message is queued for retry
6. If delivery fails permanently, error is logged and reported

### Rate Limiting
The system implements rate limiting for all API providers:
- Gmail: Limited to 250 requests per minute by default
- Twilio: Limited to 100 requests per minute by default
- Limits are configurable and enforced via Redis counters

### Retry Logic
Failed deliveries follow an exponential backoff strategy:
- Initial delay: 5 seconds (configurable)
- Each subsequent attempt doubles the delay
- Maximum of 3 attempts by default
- Permanent failures are logged and reported

## Configuration Options

### Channel Configuration
Each delivery channel can be configured separately:
- Rate limits and burst allowances
- Retry attempts and delay strategies
- Timeout values
- Credentials and endpoints

### Delivery Priorities
Messages can be assigned different priorities:
- High priority: Faster delivery attempts
- Normal priority: Standard delivery processing
- Low priority: Delayed delivery when system is busy

### Error Handling
- Temporary failures trigger retry logic
- Permanent failures are logged and reported
- Rate limit hits are tracked separately
- Unreachable recipients are flagged for manual review

## Monitoring and Debugging

### Logs
- Delivery attempts and results are logged
- Rate limit hits are tracked separately
- Error conditions and retries are documented
- Performance metrics are recorded

### Health Checks
- Kafka connectivity is monitored
- Database connectivity is verified
- Rate limit status is checked
- Delivery service availability is tested

### Metrics
- Delivery success/failure rates
- Average delivery times by channel
- Rate limit utilization
- Retry queue lengths

## Development Commands

### Running in Development Mode
```bash
# With debug logging
export LOG_LEVEL=DEBUG
python scripts/start_dispatcher.py
```

### Running Tests
```bash
# Run all unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run stress tests
pytest tests/stress/
```

### Docker Deployment
```bash
# Build and run with Docker
docker-compose up --build

# Run only the dispatcher service
docker-compose up dispatcher-service
```

## Cleanup and Shutdown

### Graceful Shutdown
The system supports graceful shutdown with signal handling:
- SIGTERM initiates graceful shutdown
- Active deliveries are completed
- Kafka consumers are stopped properly
- Resources are released cleanly

### Stress Test Cleanup
For stress testing scenarios, use the cleanup script:
```bash
python scripts/cleanup_dispatcher.py
```

This script:
- Clears Redis rate limit counters
- Purges retry queues
- Resets delivery statistics
- Cleans up temporary resources
