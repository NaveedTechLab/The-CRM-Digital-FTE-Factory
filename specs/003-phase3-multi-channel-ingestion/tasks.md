# Implementation Tasks: Phase 3: Multi-Channel Ingestion

**Feature**: Phase 3: Multi-Channel Ingestion
**Branch**: `003-phase3-multi-channel-ingestion`
**Created**: 2026-02-02
**Input**: Feature specification and implementation plan

## Phase 1: Setup

Initialize the project directory structure and dependencies.

### Setup Tasks

- [X] T001 Create the /phase-3-multi-channel-ingestion directory structure with all subdirectories
- [X] T002 Create requirements.txt with FastAPI, Pydantic, SQLAlchemy, aiokafka, google-api-python-client, twilio dependencies
- [X] T003 Create app/__init__.py and app/main.py with basic FastAPI application

## Phase 2: Foundational

Create foundational components that all user stories depend on.

### Foundational Tasks

- [X] T004 [P] Implement the 'InboundMessage' Pydantic model to unify fields (sender_id, channel, timestamp, raw_payload, text_content) in /phase-3-multi-channel-ingestion/app/models/inbound_message.py
- [X] T005 [P] Create ChannelPayload model in /phase-3-multi-channel-ingestion/app/models/channel_payload.py
- [X] T006 [P] Create KafkaEvent model in /phase-3-multi-channel-ingestion/app/models/kafka_event.py
- [X] T007 Create settings.py configuration in /phase-3-multi-channel-ingestion/app/config/settings.py
- [X] T008 Create security.py configuration in /phase-3-multi-channel-ingestion/app/config/security.py
- [X] T009 Create KafkaProducer integration in /phase-3-multi-channel-ingestion/app/services/kafka_producer.py
- [X] T010 Create IdentityResolver module that uses Phase 2 DatabaseManager in /phase-3-multi-channel-ingestion/app/services/identity_resolver.py

## Phase 3: User Story 1 - Multi-Channel Message Reception (Priority: P1)

A customer sends a message via any supported channel (WhatsApp, Gmail, or Web Support Form), and the system receives, normalizes, and publishes the message to the ingestion pipeline for processing.

### Independent Test Criteria

Can be fully tested by sending messages through each channel and verifying that they are properly received, normalized, and published to the Kafka ingestion topic.

### Implementation Tasks

- [X] T011 [US1] Develop the FastAPI Web Support Form endpoint with API Key validation in /phase-3-multi-channel-ingestion/app/routes/webform_endpoint.py
- [X] T012 [US1] Develop the Twilio WhatsApp webhook endpoint with signature verification logic in /phase-3-multi-channel-ingestion/app/routes/whatsapp_webhook.py
- [X] T013 [US1] Implement the Gmail Poller service using Google API Client in /phase-3-multi-channel-ingestion/scripts/gmail_poller.py
- [X] T014 [US1] Create MessageNormalizer service in /phase-3-multi-channel-ingestion/app/services/message_normalizer.py
- [X] T015 [US1] Implement IngestionService logic: Receive -> Normalize -> Identify -> Publish in /phase-3-multi-channel-ingestion/app/services/ingestion_service.py

## Phase 4: User Story 2 - Secure Channel Integration (Priority: P2)

The system must validate the authenticity of incoming messages from external channels (Twilio webhook signatures, API keys for web forms) to prevent unauthorized access.

### Independent Test Criteria

Can be tested by attempting to send messages with invalid signatures/keys and verifying they are rejected, while valid ones are accepted.

### Implementation Tasks

- [X] T016 [US2] Implement Twilio signature verification logic in /phase-3-multi-channel-ingestion/app/services/twilio_validator.py
- [X] T017 [US2] Enhance Web Support Form endpoint to include comprehensive API key validation
- [X] T018 [US2] Create security middleware for protecting endpoints in /phase-3-multi-channel-ingestion/app/middleware/security.py

## Phase 5: User Story 3 - Message Normalization (Priority: P3)

The system must convert diverse channel-specific message formats into a unified InboundMessage schema to ensure consistent processing across all channels.

### Independent Test Criteria

Can be tested by sending messages from different channels and verifying they all conform to the unified InboundMessage schema when published to Kafka.

### Implementation Tasks

- [X] T019 [US3] Enhance MessageNormalizer to handle all three channel types (Gmail, WhatsApp, Web Form)
- [X] T020 [US3] Create NormalizationRule model for transformation rules in /phase-3-multi-channel-ingestion/app/models/normalization_rule.py
- [X] T021 [US3] Implement channel-specific normalization strategies in /phase-3-multi-channel-ingestion/app/services/message_normalizer.py

## Phase 6: Verification & Testing

Verification: A test suite that simulates a Gmail message, a WhatsApp webhook, and a Web Form POST, then verifies they all appear as normalized JSON in the Kafka 'inbound_events' topic.

### Verification Tasks

- [X] T022 [P] Create test suite that simulates Gmail message ingestion
- [X] T023 [P] Create test suite that simulates WhatsApp webhook processing
- [X] T024 [P] Create test suite that simulates Web Form POST request
- [X] T025 [P] Create test verification that normalized messages appear in Kafka 'inbound_events' topic
- [X] T026 Run complete verification test suite and confirm all channels work correctly

## Dependencies

- T001-T003 must complete before any other tasks
- T004-T010 must complete before User Story tasks
- T010 (IdentityResolver) required before T015 (IngestionService)
- T009 (KafkaProducer) required before T015 (IngestionService)
- T016 (TwilioValidator) required before T012 (WhatsApp webhook)
- T019-T021 (Normalization enhancements) required before T015 (IngestionService)

## Parallel Execution Opportunities

- T004, T005, T006 can run in parallel (model implementations)
- T022, T023, T024 can run in parallel (test suites for different channels)
- T016, T017, T018 can run in parallel (security implementations)

## Implementation Strategy

1. **MVP Scope**: Complete Phase 1, 2, and core User Story 1 (T001-T015) to achieve basic multi-channel ingestion functionality
2. **Incremental Delivery**: Each phase builds on the previous to provide independently testable increments
3. **Early Verification**: Implement verification tests early (T022-T026) to validate progress