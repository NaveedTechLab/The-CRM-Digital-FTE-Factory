# Data Model: Phase 1: Incubation & Prototyping

## Customer Entity

### Fields
- **id**: UUID (primary key, auto-generated)
- **name**: String (required, max 255 characters)
- **email**: String (required, valid email format, unique)
- **phone**: String (optional, for WhatsApp channel)
- **contact_preferences**: JSON (optional, channel preferences)
- **created_at**: DateTime (auto-generated)
- **updated_at**: DateTime (auto-generated)
- **last_interaction**: DateTime (nullable, timestamp of last interaction)

### Relationships
- One-to-many with Ticket (via customer_id foreign key)

### Validation Rules
- Email must follow standard email format
- Name must be 1-255 characters
- Contact preferences must be valid JSON structure

## Ticket Entity

### Fields
- **id**: UUID (primary key, auto-generated)
- **customer_id**: UUID (foreign key to Customer)
- **subject**: String (required, max 255 characters)
- **description**: Text (required)
- **status**: String (enum: 'open', 'in-progress', 'resolved', 'closed')
- **priority**: String (enum: 'low', 'medium', 'high', 'critical')
- **channel**: String (enum: 'gmail', 'whatsapp', 'webform')
- **assigned_to**: String (optional, agent identifier)
- **created_at**: DateTime (auto-generated)
- **updated_at**: DateTime (auto-generated)
- **resolved_at**: DateTime (nullable, when status becomes 'resolved')

### Relationships
- Many-to-one with Customer (via customer_id foreign key)

### Validation Rules
- Subject must be 1-255 characters
- Description must be provided
- Status must be one of allowed values
- Priority must be one of allowed values
- Channel must be one of supported channels

## Interaction Entity

### Fields
- **id**: UUID (primary key, auto-generated)
- **ticket_id**: UUID (foreign key to Ticket)
- **sender_type**: String (enum: 'customer', 'agent')
- **content**: Text (required, message content)
- **timestamp**: DateTime (auto-generated)
- **channel_metadata**: JSON (optional, channel-specific data)

### Relationships
- Many-to-one with Ticket (via ticket_id foreign key)

### Validation Rules
- Content must be provided
- Sender type must be 'customer' or 'agent'

## Channel Entity

### Fields
- **id**: String (primary key, enum: 'gmail', 'whatsapp', 'webform')
- **name**: String (display name for the channel)
- **enabled**: Boolean (whether channel is active)
- **created_at**: DateTime (auto-generated)

### Validation Rules
- ID must be one of supported channel types
- Name must be provided