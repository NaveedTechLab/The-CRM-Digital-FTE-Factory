# Data Model: Phase 5: Response Delivery & Egress

## OutboundMessage Entity

### Fields
- **id**: UUID (primary key, auto-generated)
- **message_id**: String (reference to original message in Phase 2 DB)
- **conversation_id**: String (identifies related messages in conversation)
- **content**: Text (the message content to be delivered)
- **channel_destination**: String (enum: 'gmail', 'whatsapp', 'webform', required)
- **recipient_identifier**: String (email address, phone number, or webhook URL depending on channel)
- **sender_identifier**: String (identifier for the sending agent/service)
- **timestamp**: DateTime (when the message was created)
- **delivery_status**: String (enum: 'pending', 'in_progress', 'delivered', 'failed', 'retrying', default: 'pending')
- **delivery_attempts**: Integer (number of delivery attempts, default: 0)
- **last_delivery_attempt**: DateTime (timestamp of last delivery attempt)
- **delivery_metadata**: JSON (channel-specific delivery metadata like message IDs)
- **failure_reason**: String (reason for delivery failure if applicable)
- **priority**: String (enum: 'low', 'normal', 'high', default: 'normal')
- **scheduled_delivery**: DateTime (when the message should be delivered)
- **actual_delivery**: DateTime (when the message was actually delivered)
- **created_at**: DateTime (auto-generated when message is created)
- **updated_at**: DateTime (auto-generated when message is updated)

### Relationships
- References to Conversation entity via conversation_id for thread management
- References to Customer identity via recipient_identifier for delivery tracking

### Validation Rules
- message_id must be valid
- content must not be empty
- channel_destination must be one of the allowed values
- delivery_status must be one of the allowed values
- delivery_attempts must be non-negative
- priority must be one of the allowed values

### State Transitions
- 'pending' → 'in_progress' (when delivery attempt begins)
- 'in_progress' → 'delivered' (when delivery succeeds)
- 'in_progress' → 'failed' (when delivery fails permanently)
- 'in_progress' → 'retrying' (when delivery fails temporarily)
- 'retrying' → 'in_progress' (when retry is attempted)

## DeliveryLog Entity

### Fields
- **id**: UUID (primary key, auto-generated)
- **outbound_message_id**: String (foreign key to OutboundMessage)
- **attempt_number**: Integer (sequence number of delivery attempt)
- **channel**: String (enum: 'gmail', 'whatsapp', 'webform', required)
- **delivery_method**: String (specific delivery method used)
- **request_payload**: JSON (payload sent to delivery service)
- **response_payload**: JSON (response received from delivery service)
- **status_code**: Integer (HTTP status code or service-specific code)
- **success**: Boolean (whether the delivery attempt was successful)
- **error_message**: String (error details if delivery failed)
- **rate_limit_hit**: Boolean (whether this failure was due to rate limiting)
- **timestamp**: DateTime (when the delivery attempt was made)
- **processing_time_ms**: Integer (time taken for the delivery attempt)

### Relationships
- Many-to-one with OutboundMessage (via outbound_message_id)

### Validation Rules
- outbound_message_id must reference a valid OutboundMessage
- attempt_number must be positive
- channel must be one of the allowed values
- success must be boolean
- processing_time_ms must be non-negative

## ChannelConfig Entity

### Fields
- **id**: UUID (primary key, auto-generated)
- **channel_type**: String (enum: 'gmail', 'whatsapp', 'webform', required)
- **api_endpoint**: String (API endpoint URL for the channel)
- **rate_limit_requests**: Integer (max requests per time window)
- **rate_limit_window_seconds**: Integer (time window for rate limiting)
- **burst_limit**: Integer (max burst requests allowed)
- **retry_attempts**: Integer (number of retry attempts for failed deliveries)
- **retry_delay_base**: Integer (base delay for exponential backoff in seconds)
- **timeout_seconds**: Integer (timeout for delivery attempts)
- **enabled**: Boolean (whether this channel is enabled for delivery)
- **credentials_config**: JSON (configuration for API credentials)
- **created_at**: DateTime (auto-generated when config is created)
- **updated_at**: DateTime (auto-generated when config is updated)

### Relationships
- One-to-many with OutboundMessage (via channel_destination)

### Validation Rules
- channel_type must be one of the allowed values
- rate_limit_requests must be positive
- rate_limit_window_seconds must be positive
- retry_attempts must be non-negative
- retry_delay_base must be positive
- timeout_seconds must be positive
- enabled must be boolean

## RateLimitState Entity

### Fields
- **id**: UUID (primary key, auto-generated)
- **channel_type**: String (enum: 'gmail', 'whatsapp', 'webform', required)
- **window_start**: DateTime (start time of the current rate limit window)
- **requests_count**: Integer (number of requests made in the current window)
- **last_access**: DateTime (timestamp of last request)
- **reset_time**: DateTime (when the rate limit window resets)

### Relationships
- Used for tracking rate limiting state across the system

### Validation Rules
- channel_type must be one of the allowed values
- requests_count must be non-negative
- reset_time must be after window_start

## RetryQueueItem Entity

### Fields
- **id**: UUID (primary key, auto-generated)
- **outbound_message_id**: String (foreign key to OutboundMessage)
- **attempt_number**: Integer (current attempt number)
- **scheduled_retry**: DateTime (when to attempt the retry)
- **failure_reason**: String (reason for previous failure)
- **priority**: Integer (priority for processing, higher numbers processed first)
- **created_at**: DateTime (auto-generated when item is queued)
- **updated_at**: DateTime (auto-generated when item is updated)

### Relationships
- Many-to-one with OutboundMessage (via outbound_message_id)

### Validation Rules
- outbound_message_id must reference a valid OutboundMessage
- attempt_number must be positive
- priority must be non-negative
