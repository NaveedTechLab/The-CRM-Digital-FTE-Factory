# Research & Technical Decisions: Phase 5: Response Delivery & Egress

## Response Dispatcher Implementation

### Decision: aiokafka vs confluent-kafka-python for Kafka Consumer
- **Chosen**: aiokafka for asynchronous consumption
- **Rationale**: Better integration with async Python ecosystem, non-blocking operations that suit message processing patterns, consistent with Phase 4's approach
- **Alternatives considered**: confluent-kafka-python - synchronous but more mature, python-kafka - also synchronous

### Decision: Message Routing Strategy
- **Chosen**: Channel-based routing using message metadata
- **Rationale**: Clean separation of concerns where the dispatcher inspects channel metadata and routes to appropriate delivery service
- **Implementation**: Check 'channel_destination' field in outbound message and route accordingly

## Gmail Delivery Service Implementation

### Decision: Gmail API vs SMTP for Email Delivery
- **Chosen**: Gmail API via google-api-python-client
- **Rationale**: Better integration with Google Workspace, more reliable delivery, proper threading with Message-ID references, built-in rate limiting awareness
- **Alternatives considered**: SMTP - simpler but less reliable delivery, harder threading implementation

### Decision: Email Threading Implementation
- **Chosen**: Use In-Reply-To and References headers with original Message-ID
- **Rationale**: Maintains proper email conversation threads for customer continuity
- **Implementation**: Extract original Message-ID from inbound message and set as In-Reply-To header

## Twilio WhatsApp Service Implementation

### Decision: Twilio API Version and Message Format
- **Chosen**: Twilio Conversations API with proper WhatsApp message formatting
- **Rationale**: Most robust WhatsApp Business API implementation, handles rate limiting automatically, provides delivery receipts
- **Alternatives considered**: Direct WhatsApp Business API - more complex setup, less documentation

## Web Notification Implementation

### Decision: Webhook vs WebSocket for Real-time Updates
- **Chosen**: Webhook approach with HTTP callbacks for web form responses
- **Rationale**: Simpler implementation, better compatibility with web forms, easier to track delivery status
- **Implementation**: HTTP POST to customer's registered webhook URL with response payload

## Rate Limiting Strategy

### Decision: Redis vs In-Memory Rate Limiting
- **Chosen**: Redis-based rate limiting with sliding window counters
- **Rationale**: Distributed rate limiting that works across multiple instances, persistent counters, shared state for API quotas
- **Implementation**: Sliding window algorithm with Redis for Gmail and Twilio API limits

### Decision: Rate Limiting Algorithm
- **Chosen**: Token bucket algorithm with configurable burst rates
- **Rationale**: Balances smooth delivery with ability to handle traffic spikes, prevents API blacklisting
- **Implementation**: Track requests per time window and enforce limits based on provider guidelines

## Retry Mechanism Design

### Decision: Exponential Backoff with Jitter
- **Chosen**: Exponential backoff with random jitter for retry delays
- **Rationale**: Prevents thundering herd problems, handles temporary failures gracefully, respects API limits
- **Implementation**: Start with 1s, double each attempt up to 5 minutes, with 10% jitter

### Decision: Retry Queue Architecture
- **Chosen**: Separate retry queue with priority based on failure type
- **Rationale**: Allows different handling of temporary vs permanent failures, maintains delivery order where possible
- **Implementation**: Redis-backed queue with TTL and failure counting

## Database Synchronization

### Decision: Synchronous vs Asynchronous Status Updates
- **Chosen**: Synchronous status updates for critical delivery states
- **Rationale**: Ensures delivery status is immediately available for audit and troubleshooting
- **Implementation**: Update PostgreSQL messages table before acknowledging Kafka message

## System Shutdown/Cleanup Procedures

### Decision: Graceful Shutdown Implementation
- **Chosen**: Signal handlers with graceful Kafka consumer shutdown
- **Rationale**: Ensures no message loss during shutdown, proper cleanup of resources
- **Implementation**: Handle SIGTERM/SIGINT, stop consumer, flush pending deliveries, close connections

### Decision: Stress Test Cleanup Strategy
- **Chosen**: Comprehensive cleanup script that resets all state
- **Rationale**: Ensures clean state for subsequent tests, prevents cross-test contamination
- **Implementation**: Clear Redis caches, reset rate limit counters, purge Kafka queues if needed
