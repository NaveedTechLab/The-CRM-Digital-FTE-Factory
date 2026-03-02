# Research: Phase 2: Core Infrastructure & Database

## PostgreSQL Schema Design

### Decision: Comprehensive schema with proper relationships and indexing
- **Customers table**: Primary customer information with indexes on email and phone for quick lookups
- **Tickets table**: Support ticket data with foreign key to customers and indexes on status and priority
- **Messages table**: Interaction history with foreign key to tickets and full-text search capabilities
- **Vector_embeddings table**: For RAG functionality with pgvector-specific data types and indexing

### Rationale:
- Ensures data integrity through foreign key constraints
- Optimizes query performance with appropriate indexing
- Supports the multi-channel interaction tracking required
- Enables future RAG capabilities through vector storage

### Alternatives considered:
- Denormalized approach (rejected - lacks data integrity)
- Single table for all entities (rejected - poor performance and maintainability)

## Docker Compose Architecture

### Decision: Separate services for PostgreSQL and Kafka with Zookeeper
- PostgreSQL service with pgvector extension pre-installed
- Zookeeper service for Kafka coordination
- Kafka broker service with proper configuration for high availability

### Rationale:
- Clear separation of concerns between data storage and messaging
- Standard architecture for Kafka clusters
- Easy to scale and maintain individually
- Supports local development requirements

### Alternatives considered:
- Embedded database approach (rejected - not production-grade)
- Single container with all services (rejected - poor isolation and scaling)

## Kafka Topic Lifecycle Management

### Decision: Pre-defined topics with specific partition counts and retention policies
- **inbound_events**: 6 partitions, 7-day retention for incoming messages
- **outbound_responses**: 6 partitions, 3-day retention for responses
- **escalations**: 3 partitions, 30-day retention for critical issues

### Rationale:
- Different retention periods based on business importance
- Partition counts based on expected throughput
- Proper cleanup to prevent storage issues
- Supports the event streaming requirements from the spec

### Alternatives considered:
- Dynamic topic creation (rejected - lacks control and predictability)
- Single topic for all events (rejected - poor organization and performance)

## Database Utility Module Architecture

### Decision: SQLAlchemy-based utility with connection pooling and transaction management
- ORM models that map to the PostgreSQL schema
- Connection pooling for performance
- Transaction management for data consistency
- Integration-ready for the existing FastAPI application

### Rationale:
- Leverages existing Python/SQLAlchemy ecosystem
- Provides robust connection management
- Ensures data consistency through transactions
- Easy integration with FastAPI app from Phase 1

### Alternatives considered:
- Raw SQL queries (rejected - lacks safety and maintainability)
- Multiple database connectors (rejected - increases complexity)