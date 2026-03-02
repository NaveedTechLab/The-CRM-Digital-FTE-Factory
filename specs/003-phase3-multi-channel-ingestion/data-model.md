# Data Model: Phase 3: Multi-Channel Ingestion

## InboundMessage Entity

### Fields
- **id**: UUID (primary key, auto-generated)
- **customer_identifier**: String (email or phone number, used for identity lookup)
- **customer_name**: String (optional, customer's name from channel)
- **message_content**: Text (the actual message content from the customer)
- **channel_type**: String (enum: 'gmail', 'whatsapp', 'webform', required)
- **channel_message_id**: String (unique identifier from the channel provider)
- **timestamp**: DateTime (when the message was received)
- **priority**: String (enum: 'low', 'medium', 'high', 'critical', default: 'medium')
- **attachments**: Array of Attachment objects (optional, file attachments)
- **channel_metadata**: JSON (channel-specific metadata like sender info)
- **processed_status**: String (enum: 'received', 'normalized', 'identified', 'published', default: 'received')
- **created_at**: DateTime (auto-generated when message is ingested)
- **updated_at**: DateTime (auto-generated when message is updated)

### Relationships
- One-to-many with Attachment objects (via attachments field)
- References to Customer entity via customer_identifier for identity resolution

### Validation Rules
- customer_identifier must be a valid email or phone number format
- message_content must not be empty
- channel_type must be one of the allowed values
- timestamp must be within reasonable range (not in the future, not older than 24 hours)
- priority must be one of the allowed values
- processed_status must be one of the allowed values

### State Transitions
- 'received' → 'normalized' (when message normalization is complete)
- 'normalized' → 'identified' (when customer identity is resolved)
- 'identified' → 'published' (when message is published to Kafka)

## ChannelPayload Entity

### Fields
- **id**: UUID (primary key, auto-generated)
- **raw_payload**: JSON (the original, unprocessed payload from the channel)
- **channel_type**: String (enum: 'gmail', 'whatsapp', 'webform', required)
- **webhook_signature**: String (signature for webhook validation)
- **security_validated**: Boolean (whether the payload passed security validation)
- **validation_errors**: Array of Strings (errors during validation)
- **normalized_message_id**: UUID (foreign key to InboundMessage when normalized)
- **created_at**: DateTime (auto-generated when payload is received)

### Relationships
- Many-to-one with InboundMessage (via normalized_message_id when normalization is complete)

### Validation Rules
- raw_payload must be valid JSON
- channel_type must be one of the allowed values
- webhook_signature validation depends on channel_type
- security_validated must be boolean

## Attachment Entity

### Fields
- **id**: UUID (primary key, auto-generated)
- **message_id**: UUID (foreign key to InboundMessage)
- **filename**: String (original filename)
- **content_type**: String (MIME type of the attachment)
- **file_size**: Integer (size in bytes)
- **download_url**: String (secure URL to download the attachment)
- **stored_location**: String (internal storage location)
- **upload_status**: String (enum: 'pending', 'uploaded', 'failed', default: 'pending')
- **created_at**: DateTime (auto-generated when attachment record is created)

### Relationships
- Many-to-one with InboundMessage (via message_id)

### Validation Rules
- filename must not be empty
- content_type must be a valid MIME type
- file_size must be positive and within allowed limits
- upload_status must be one of the allowed values

## KafkaEvent Entity

### Fields
- **id**: UUID (primary key, auto-generated)
- **inbound_message_id**: UUID (foreign key to InboundMessage)
- **topic_name**: String (name of the Kafka topic, default: 'inbound_events')
- **partition**: Integer (Kafka partition number)
- **offset**: Integer (Kafka offset within partition)
- **event_payload**: JSON (the actual payload published to Kafka)
- **publish_timestamp**: DateTime (when the event was published)
- **delivery_status**: String (enum: 'pending', 'published', 'failed', 'retried')
- **retry_count**: Integer (number of times publication was retried)
- **error_message**: String (error details if delivery failed)
- **created_at**: DateTime (auto-generated when event record is created)

### Relationships
- Many-to-one with InboundMessage (via inbound_message_id)

### Validation Rules
- topic_name must be valid
- partition must be non-negative
- offset must be non-negative
- delivery_status must be one of the allowed values
- retry_count must be non-negative

## NormalizationRule Entity

### Fields
- **id**: UUID (primary key, auto-generated)
- **channel_type**: String (enum: 'gmail', 'whatsapp', 'webform', required)
- **rule_name**: String (descriptive name for the rule)
- **input_field**: String (the field in the raw payload to transform)
- **output_field**: String (the field in the InboundMessage to populate)
- **transformation_type**: String (enum: 'direct', 'mapping', 'regex', 'function', required)
- **transformation_params**: JSON (parameters for the transformation)
- **priority**: Integer (order in which rules are applied)
- **enabled**: Boolean (whether the rule is currently active)
- **created_at**: DateTime (auto-generated when rule is created)
- **updated_at**: DateTime (auto-generated when rule is updated)

### Validation Rules
- channel_type must be one of the allowed values
- rule_name must not be empty
- input_field must not be empty
- output_field must not be empty
- transformation_type must be one of the allowed values
- priority must be non-negative
- enabled must be boolean

## SecurityCredential Entity

### Fields
- **id**: UUID (primary key, auto-generated)
- **credential_type**: String (enum: 'twilio_signature', 'api_key', 'oauth_token', required)
- **credential_value**: String (the actual credential value)
- **channel_type**: String (enum: 'gmail', 'whatsapp', 'webform', required)
- **is_active**: Boolean (whether the credential is currently active)
- **valid_from**: DateTime (when the credential becomes active)
- **expires_at**: DateTime (when the credential expires, null for permanent)
- **description**: String (optional description of the credential)
- **created_at**: DateTime (auto-generated when credential is created)
- **updated_at**: DateTime (auto-generated when credential is updated)

### Validation Rules
- credential_type must be one of the allowed values
- credential_value must not be empty
- channel_type must be one of the allowed values
- is_active must be boolean
- valid_from must not be in the future compared to created_at
- expires_at must be after valid_from if specified