# Data Model: Phase 2: Core Infrastructure & Database

## Customers Table

### Fields
- **id**: UUID (primary key, auto-generated)
- **external_id**: VARCHAR(255) (unique, external reference ID from various channels)
- **name**: VARCHAR(255) (required, customer's name)
- **email**: VARCHAR(320) (indexed, unique email address)
- **phone**: VARCHAR(20) (indexed, phone number for WhatsApp)
- **contact_preferences**: JSONB (optional, channel preferences and settings)
- **created_at**: TIMESTAMP (auto-generated, when customer was created)
- **updated_at**: TIMESTAMP (auto-generated, when customer was last updated)
- **last_interaction**: TIMESTAMP (nullable, timestamp of last interaction)

### Indexes
- Primary: id
- Unique: email
- Regular: external_id, phone, created_at, last_interaction

### Constraints
- Email format validation
- Phone format validation (where applicable)
- Non-null constraints on required fields

## Tickets Table

### Fields
- **id**: UUID (primary key, auto-generated)
- **customer_id**: UUID (foreign key to customers.id)
- **external_reference**: VARCHAR(255) (unique, reference from originating channel)
- **subject**: VARCHAR(500) (required, ticket subject)
- **description**: TEXT (required, detailed description)
- **status**: VARCHAR(50) (enum: 'open', 'in-progress', 'awaiting-response', 'resolved', 'closed')
- **priority**: VARCHAR(50) (enum: 'low', 'medium', 'high', 'critical')
- **channel**: VARCHAR(50) (enum: 'email', 'whatsapp', 'webform', 'other')
- **assigned_agent**: VARCHAR(255) (nullable, agent assigned to ticket)
- **sla_deadline**: TIMESTAMP (nullable, deadline for resolution)
- **created_at**: TIMESTAMP (auto-generated)
- **updated_at**: TIMESTAMP (auto-generated)
- **resolved_at**: TIMESTAMP (nullable, when status became 'resolved')

### Indexes
- Primary: id
- Foreign: customer_id
- Regular: status, priority, channel, created_at, sla_deadline

### Constraints
- Foreign key constraint on customer_id
- Check constraint on status and priority values
- Non-null constraints on required fields

## Messages Table

### Fields
- **id**: UUID (primary key, auto-generated)
- **ticket_id**: UUID (foreign key to tickets.id)
- **sender_type**: VARCHAR(50) (enum: 'customer', 'agent', 'system')
- **sender_id**: VARCHAR(255) (nullable, reference to sender)
- **content**: TEXT (required, message content)
- **content_type**: VARCHAR(50) (enum: 'text', 'html', 'markdown', 'structured')
- **direction**: VARCHAR(50) (enum: 'inbound', 'outbound')
- **channel_metadata**: JSONB (optional, channel-specific metadata)
- **sent_at**: TIMESTAMP (auto-generated, when message was sent)
- **received_at**: TIMESTAMP (nullable, when message was received)

### Indexes
- Primary: id
- Foreign: ticket_id
- Regular: sender_type, direction, sent_at, received_at

### Constraints
- Foreign key constraint on ticket_id
- Check constraint on sender_type and direction values
- Non-null constraints on required fields

## Vector Embeddings Table

### Fields
- **id**: UUID (primary key, auto-generated)
- **entity_type**: VARCHAR(100) (enum: 'customer', 'ticket', 'message', 'knowledge_base')
- **entity_id**: VARCHAR(255) (reference to the entity this embedding represents)
- **embedding**: vector (pgvector column for storing embeddings)
- **content_preview**: TEXT (nullable, text that was embedded)
- **created_at**: TIMESTAMP (auto-generated)
- **updated_at**: TIMESTAMP (auto-generated)

### Indexes
- Primary: id
- Regular: entity_type, entity_id, created_at
- Vector: embedding (using pgvector-specific indexing)

### Constraints
- Check constraint on entity_type values
- Non-null constraints on required fields

## Kafka Topics Configuration

### inbound_events Topic
- Partitions: 6
- Replication Factor: 1 (for local dev, 3 for production)
- Retention: 7 days
- Segment Size: 1GB

### outbound_responses Topic
- Partitions: 6
- Replication Factor: 1 (for local dev, 3 for production)
- Retention: 3 days
- Segment Size: 1GB

### escalations Topic
- Partitions: 3
- Replication Factor: 1 (for local dev, 3 for production)
- Retention: 30 days
- Segment Size: 1GB

## Relationships

### Customer to Ticket
- One-to-many (one customer can have multiple tickets)
- Foreign key: tickets.customer_id → customers.id

### Ticket to Message
- One-to-many (one ticket can have multiple messages)
- Foreign key: messages.ticket_id → tickets.id

### Vector Embeddings
- Polymorphic relationship to customers, tickets, or messages
- Referenced by entity_type and entity_id combination