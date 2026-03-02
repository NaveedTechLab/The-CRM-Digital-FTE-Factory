# Data Model: Phase 4: Agent Intelligence & Logic

## AgentMessage Entity

### Fields
- **id**: UUID (primary key, auto-generated)
- **customer_id**: String (foreign key to customer in Phase 2 DB)
- **conversation_id**: String (identifies related messages in conversation)
- **inbound_message_id**: String (reference to original inbound message from Phase 3)
- **message_type**: String (enum: 'customer_query', 'agent_response', 'system_note', required)
- **content**: Text (the actual message content)
- **role**: String (enum: 'customer', 'agent', 'system', required)
- **timestamp**: DateTime (when the message was created)
- **confidence_score**: Float (confidence in agent's response or query understanding, 0.0-1.0)
- **intents**: Array of Strings (detected intents from customer query)
- **entities**: JSON (extracted entities from customer query)
- **kb_articles_used**: Array of Strings (IDs of knowledge base articles referenced)
- **escalation_flag**: Boolean (whether this message triggered escalation)
- **processed_status**: String (enum: 'received', 'processing', 'processed', 'escalated', 'failed', default: 'received')
- **created_at**: DateTime (auto-generated when message is created)
- **updated_at**: DateTime (auto-generated when message is updated)

### Relationships
- One-to-many with AgentResponse objects (via conversation_id)
- References to Customer entity via customer_id for identity resolution
- References to KnowledgeBaseArticle via kb_articles_used

### Validation Rules
- customer_id must be valid
- content must not be empty for customer_query or agent_response
- message_type must be one of the allowed values
- role must be one of the allowed values
- confidence_score must be between 0.0 and 1.0
- processed_status must be one of the allowed values

### State Transitions
- 'received' → 'processing' (when agent begins processing)
- 'processing' → 'processed' (when agent completes response)
- 'processing' → 'escalated' (when escalation is triggered)
- 'processing' → 'failed' (when processing encounters an error)

## OutboundMessage Entity

### Fields
- **id**: UUID (primary key, auto-generated)
- **agent_message_id**: String (foreign key to AgentMessage that generated this response)
- **conversation_id**: String (identifies related messages in conversation)
- **response_type**: String (enum: 'answer', 'escalation', 'ticket_created', 'follow_up', required)
- **content**: Text (the agent's response content)
- **channel_destination**: String (enum: 'gmail', 'whatsapp', 'webform', required)
- **recipient_id**: String (email, phone number, or other identifier for recipient)
- **confidence_score**: Float (confidence in the response, 0.0-1.0)
- **kb_sources**: Array of Strings (IDs of knowledge base articles used)
- **tools_used**: Array of Strings (names of tools invoked during response generation)
- **escalation_reason**: String (reason for escalation if applicable)
- **ticket_reference**: String (ID of ticket created if applicable)
- **delivery_status**: String (enum: 'pending', 'delivered', 'failed', 'retracted', default: 'pending')
- **delivery_attempts**: Integer (number of delivery attempts)
- **scheduled_delivery**: DateTime (when the message should be sent)
- **actual_delivery**: DateTime (when the message was actually sent)
- **created_at**: DateTime (auto-generated when message is created)
- **updated_at**: DateTime (auto-generated when message is updated)

### Relationships
- Many-to-one with AgentMessage (via agent_message_id)
- Many-to-many with KnowledgeBaseArticle (via kb_sources)

### Validation Rules
- agent_message_id must reference a valid AgentMessage
- response_type must be one of the allowed values
- channel_destination must be one of the allowed values
- confidence_score must be between 0.0 and 1.0
- delivery_status must be one of the allowed values
- delivery_attempts must be non-negative

## KnowledgeBaseArticle Entity

### Fields
- **id**: UUID (primary key, auto-generated)
- **title**: String (title of the knowledge base article)
- **content**: Text (full content of the article)
- **summary**: String (brief summary of the article)
- **category**: String (category or topic classification)
- **tags**: Array of Strings (keywords/tags for the article)
- **embeddings**: Vector (pgvector embeddings for semantic search)
- **version**: String (version number of the article)
- **author**: String (author of the article)
- **last_updated**: DateTime (when the article was last updated)
- **status**: String (enum: 'draft', 'published', 'archived', default: 'published')
- **relevance_score**: Float (average relevance score based on usage)
- **usage_count**: Integer (number of times article has been referenced)
- **created_at**: DateTime (auto-generated when article is created)
- **updated_at**: DateTime (auto-generated when article is updated)

### Relationships
- Many-to-many with AgentMessage (articles used in message processing)

### Validation Rules
- title must not be empty
- content must not be empty
- embeddings must be a valid vector format
- status must be one of the allowed values
- relevance_score must be between 0.0 and 1.0
- usage_count must be non-negative

## AgentToolCall Entity

### Fields
- **id**: UUID (primary key, auto-generated)
- **agent_message_id**: String (foreign key to AgentMessage)
- **tool_name**: String (name of the tool that was called)
- **tool_input**: JSON (input parameters for the tool call)
- **tool_output**: JSON (output returned by the tool)
- **execution_time_ms**: Integer (time taken for tool execution in milliseconds)
- **success**: Boolean (whether the tool call was successful)
- **error_message**: String (error details if tool call failed)
- **confidence_impact**: Float (how much this tool call affected the final confidence score)
- **invocation_order**: Integer (order in which tools were called)
- **created_at**: DateTime (auto-generated when tool call is recorded)

### Relationships
- Many-to-one with AgentMessage (via agent_message_id)

### Validation Rules
- agent_message_id must reference a valid AgentMessage
- tool_name must not be empty
- execution_time_ms must be non-negative
- confidence_impact must be between -1.0 and 1.0

## CustomerInteractionHistory Entity

### Fields
- **id**: UUID (primary key, auto-generated)
- **customer_id**: String (foreign key to customer in Phase 2 DB)
- **conversation_id**: String (identifies related messages in conversation)
- **first_contact_date**: DateTime (when customer first contacted support)
- **last_interaction_date**: DateTime (when customer last interacted)
- **total_interactions**: Integer (total number of interactions with this customer)
- **successful_resolutions**: Integer (number of issues resolved without escalation)
- **escalation_count**: Integer (number of times issues were escalated)
- **preferred_channels**: Array of Strings (customer's preferred communication channels)
- **communication_preferences**: JSON (customer's communication preferences)
- **issue_categories**: Array of Strings (categories of issues frequently raised)
- **sentiment_trend**: String (enum: 'positive', 'neutral', 'negative', 'volatile')
- **support_tier**: String (enum: 'standard', 'premium', 'vip', default: 'standard')
- **notes**: Text (free-form notes about the customer)
- **created_at**: DateTime (auto-generated when record is created)
- **updated_at**: DateTime (auto-generated when record is updated)

### Relationships
- Many-to-one with Customer (via customer_id)
- Many-to-many with AgentMessage (interactions in this history)

### Validation Rules
- customer_id must be valid
- total_interactions must be non-negative
- successful_resolutions must be non-negative
- escalation_count must be non-negative
- sentiment_trend must be one of the allowed values
- support_tier must be one of the allowed values

## EscalationRecord Entity

### Fields
- **id**: UUID (primary key, auto-generated)
- **agent_message_id**: String (foreign key to AgentMessage that triggered escalation)
- **conversation_id**: String (identifies the conversation being escalated)
- **customer_id**: String (foreign key to customer in Phase 2 DB)
- **escalation_reason**: String (reason for escalation)
- **trigger_keywords**: Array of Strings (keywords that triggered escalation)
- **confidence_at_escalation**: Float (confidence score when escalation was triggered)
- **human_agent_assigned**: String (ID of human agent assigned to case)
- **priority_level**: String (enum: 'low', 'medium', 'high', 'critical', default: 'medium')
- **estimated_resolution_time**: DateTime (estimated time for resolution)
- **status**: String (enum: 'pending_assignment', 'assigned', 'in_progress', 'resolved', 'closed', default: 'pending_assignment')
- **original_agent_notes**: Text (notes from the AI agent about the issue)
- **handover_timestamp**: DateTime (when escalation was initiated)
- **resolution_timestamp**: DateTime (when issue was resolved by human)
- **resolution_satisfaction**: Integer (satisfaction rating after resolution, 1-5)
- **created_at**: DateTime (auto-generated when escalation is recorded)
- **updated_at**: DateTime (auto-generated when escalation record is updated)

### Relationships
- Many-to-one with AgentMessage (via agent_message_id)
- Many-to-one with Customer (via customer_id)

### Validation Rules
- agent_message_id must reference a valid AgentMessage
- escalation_reason must not be empty
- confidence_at_escalation must be between 0.0 and 1.0
- priority_level must be one of the allowed values
- status must be one of the allowed values
- resolution_satisfaction must be between 1 and 5 if provided