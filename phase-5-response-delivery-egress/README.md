# Response Delivery & Egress Service

The Response Delivery & Egress service is responsible for consuming outbound messages from the `outbound_responses` Kafka topic and delivering them to customers via their preferred communication channel (Gmail, WhatsApp, or Web Notification). The service includes rate limiting to prevent API blacklisting and maintains delivery status tracking.

## Features

- **Multi-channel delivery**: Supports Gmail, WhatsApp, and Web Form notifications
- **Rate limiting**: Prevents API blacklisting with Redis-based rate limiting
- **Retry mechanism**: Automatic retry with exponential backoff for failed deliveries
- **Delivery tracking**: Comprehensive logging of delivery attempts and status
- **Kafka integration**: Consumes messages from the `outbound_responses` topic
- **API endpoints**: RESTful API for monitoring and management

## Prerequisites

- Python 3.11+
- Docker and Docker Compose (for local development)
- PostgreSQL with pgvector extension (Phase 2 Core Infrastructure must be running)
- Kafka (Phase 2 Core Infrastructure must be running)
- Redis for rate limiting
- Gmail API credentials for email delivery
- Twilio credentials for WhatsApp delivery

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd phase-5-response-delivery-egress
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create and configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials and settings
   ```

## Configuration

The service is configured using environment variables in the `.env` file:

- `DATABASE_URL`: PostgreSQL database connection string
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka broker addresses
- `REDIS_URL`: Redis server URL for rate limiting
- `GMAIL_*`: Gmail API configuration
- `TWILIO_*`: Twilio API configuration
- `RATE_LIMIT_*`: Rate limiting settings
- `DELIVERY_*`: Delivery settings
- `APP_*`: Application settings

## Usage

### Running Locally

1. Start the required services with Docker Compose:
   ```bash
   docker-compose up -d
   ```

2. Run the dispatcher service:
   ```bash
   python scripts/start_dispatcher.py
   ```

Or run the API server with the dispatcher:
   ```bash
   python -m app.main
   ```

### Running with Docker

Build and run the service with Docker Compose:
```bash
docker-compose up --build
```

## API Endpoints

- `GET /dispatcher/status`: Check operational status
- `GET /dispatcher/delivery-status/{message_id}`: Get delivery status for a message
- `GET /dispatcher/channel-config`: Get channel configurations
- `PUT /dispatcher/channel-config`: Update channel configuration
- `GET /dispatcher/retry-queue`: Get retry queue status
- `GET /dispatcher/metrics`: Get operational metrics
- `POST /dispatcher/cleanup`: Perform cleanup operations

## Architecture

The service follows a modular architecture with the following components:

- **Models**: SQLAlchemy models for data persistence
- **Services**: Business logic for delivery and rate limiting
- **Config**: Application configuration and settings
- **Utils**: Helper functions and utilities
- **Main**: FastAPI application and startup logic

### Key Components

1. **Response Dispatcher**: Kafka consumer that routes messages based on channel metadata
2. **Gmail Service**: Handles email delivery via Gmail API with threading support
3. **WhatsApp Service**: Handles WhatsApp delivery via Twilio API
4. **Web Notification Service**: Handles webhook delivery for web form responses
5. **Rate Limiter**: Redis-based rate limiting to prevent API blacklisting
6. **Delivery Tracker**: Tracks delivery status and manages retry queue

## Rate Limiting

The service implements rate limiting for all API providers:

- **Gmail**: Limited to 250 requests per minute by default
- **Twilio**: Limited to 100 requests per minute by default
- **Web Form**: Higher limits for webhook notifications

Rate limits are configurable and enforced via Redis counters using a sliding window algorithm.

## Retry Logic

Failed deliveries follow an exponential backoff strategy:

- Initial delay: 5 seconds (configurable)
- Each subsequent attempt doubles the delay
- Maximum of 3 attempts by default
- Permanent failures are logged and reported

## Monitoring and Logging

The service includes comprehensive logging with structured data and metrics endpoints for monitoring delivery success rates, average delivery times, rate limit utilization, and retry queue lengths.

## Testing

Unit tests are located in the `tests/unit/` directory.
Integration tests are located in the `tests/integration/` directory.
Stress tests are located in the `tests/stress/` directory.

Run tests with pytest:
```bash
# Run all unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run stress tests
pytest tests/stress/
```

## Cleanup

For stress testing scenarios, use the cleanup script:
```bash
python scripts/cleanup_dispatcher.py
```

This script clears Redis rate limit counters, purges retry queues, and resets delivery statistics.

## License

This project is licensed under the terms specified in the repository.