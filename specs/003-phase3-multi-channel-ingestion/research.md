# Research: Phase 3: Multi-Channel Ingestion

## FastAPI Application Structure

### Decision: Modular FastAPI application with clear separation of concerns
- **Models**: Pydantic schemas for data validation and normalization
- **Services**: Business logic for ingestion, normalization, identity resolution, and Kafka publishing
- **Routes**: Webhook endpoints for different channels with proper security
- **Config**: Settings and security configurations
- **Utils**: Helper functions and utilities

### Rationale:
- Follows FastAPI best practices and promotes testability
- Enables clear separation of concerns between data, logic, and presentation layers
- Supports the webhook handler requirements from the specification
- Makes components independently testable

### Alternatives considered:
- Monolithic approach (rejected -不利于测试和 maintenance)
- Microservices architecture (rejected - too complex for this phase)

## InboundMessage Schema Design

### Decision: Unified Pydantic schema with channel-agnostic fields
- **Standard fields**: id, customer_identifier, message_content, timestamp, channel_type
- **Extended fields**: channel_metadata, priority, attachments, customer_context
- **Validation**: Proper field validation and constraints

### Rationale:
- Enables consistent processing across all channels
- Preserves channel-specific metadata for specialized processing
- Supports the message normalization requirement
- Follows Pydantic best practices for data validation

### Alternatives considered:
- Separate schemas per channel (rejected - defeats normalization purpose)
- Generic schema with loose typing (rejected - lacks validation and consistency)

## Gmail API Integration Strategy

### Decision: OAuth2 Service Account with polling approach
- **Polling frequency**: Configurable interval (e.g., every 30 seconds)
- **Authentication**: Service account with proper scopes
- **Rate limiting**: Respectful of Gmail API quotas
- **Error handling**: Retry logic for transient failures

### Rationale:
- Polling is simpler to implement and maintain than push notifications
- Service accounts provide reliable authentication without user interaction
- More predictable than push notifications which can be unreliable
- Aligns with the "no message loss" requirement through proper error handling

### Alternatives considered:
- Push notifications with Pub/Sub (rejected - adds complexity with Pub/Sub setup)
- Periodic full sync (rejected - less efficient than incremental polling)

## Twilio Webhook Security

### Decision: Signature validation using Twilio helper library
- **Signature verification**: Use twilio-python library's validate_request method
- **Webhook URL**: Secure endpoint with HTTPS
- **Secret management**: Environment variables for auth tokens

### Rationale:
- Twilio provides built-in security mechanisms that are industry standard
- Library handles cryptographic validation securely
- Protects against webhook spoofing and unauthorized access
- Aligns with security requirements in the specification

### Alternatives considered:
- Custom signature validation (rejected - reinventing security wheel)
- IP whitelisting only (rejected - not sufficient alone)

## DatabaseManager Integration

### Decision: Dependency injection pattern for DatabaseManager
- **Identity lookup**: Verify customer existence using email/phone before Kafka publication
- **Connection pooling**: Reuse existing connection pool from Phase 2
- **Transaction handling**: Proper transaction management for consistency

### Rationale:
- Leverages existing Phase 2 infrastructure efficiently
- Maintains consistency with previous architecture decisions
- Supports the identity resolution requirement
- Minimizes code duplication

### Alternatives considered:
- Direct database connections (rejected - duplicates Phase 2 work)
- Separate identity service (rejected - overengineering for this phase)

## Kafka Producer Implementation

### Decision: Async producer with error handling and retry logic
- **Async operations**: Use aiokafka for non-blocking operations
- **Error handling**: Comprehensive retry logic for transient failures
- **Message format**: JSON serialization with proper schema validation
- **Topic management**: Automatic topic creation if doesn't exist

### Rationale:
- Async operations prevent blocking the ingestion pipeline
- Retry logic supports the "no message loss" requirement
- JSON format provides flexibility and compatibility
- Aligns with the streaming infrastructure requirements

### Alternatives considered:
- Synchronous producer (rejected - potential blocking issues)
- Message queue alternative (rejected - Kafka is required by constitution)

## Error Handling Strategy

### Decision: Comprehensive error handling with multiple fallbacks
- **Malformed payloads**: Graceful rejection with appropriate HTTP codes
- **Kafka failures**: Retry with exponential backoff and dead letter queue
- **Database failures**: Retry with circuit breaker pattern
- **External API failures**: Graceful degradation with retry logic

### Rationale:
- Critical to meet the "no message loss" requirement
- Provides resilience against transient failures
- Maintains system stability during partial outages
- Supports the 99.9% reliability requirement

### Alternatives considered:
- Simple try-catch (rejected - insufficient for production)
- Immediate failure without retries (rejected - doesn't meet reliability goals)