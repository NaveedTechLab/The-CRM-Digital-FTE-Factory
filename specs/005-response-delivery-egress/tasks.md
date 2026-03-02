# Implementation Tasks: Phase 5: Response Delivery & Egress

**Feature**: 005-response-delivery-egress | **Spec**: specs/005-response-delivery-egress/spec.md | **Plan**: specs/005-response-delivery-egress/plan.md

## Phase 1: Setup and Project Initialization

- [X] T001 Create project structure per implementation plan in /phase-5-response-delivery-egress/
- [X] T002 Create requirements.txt with Python 3.11+ dependencies (aiokafka, google-api-python-client, twilio, SQLAlchemy, fastapi, pydantic, redis)
- [X] T003 Create .env.example with required environment variables for Gmail, Twilio, Kafka, PostgreSQL, Redis
- [X] T004 Create docker-compose.yml for local development with Kafka, PostgreSQL, and Redis services
- [X] T005 Create .gitignore with Python project patterns and sensitive files

## Phase 2: Foundational Components (Blocking Prerequisites)

- [X] T010 [P] Create app/models/__init__.py and base model structure
- [X] T011 [P] [US1] [US2] [US3] [US4] Create OutboundMessage model in app/models/outbound_message.py based on data-model.md
- [X] T012 [P] [US1] [US2] [US3] [US4] Create DeliveryLog model in app/models/delivery_log.py based on data-model.md
- [X] T013 [P] [US1] [US2] [US3] [US4] Create ChannelConfig model in app/models/channel_config.py based on data-model.md
- [X] T014 [P] [US1] [US2] [US3] [US4] Create RateLimitState model in app/models/rate_limit_state.py based on data-model.md
- [X] T015 [P] [US1] [US2] [US3] [US4] Create RetryQueueItem model in app/models/retry_queue_item.py based on data-model.md
- [X] T020 [P] Create app/config/settings.py with environment variable loading and validation
- [X] T021 [P] Create app/config/channel_configs.py with default channel configurations
- [X] T025 [P] Create app/utils/logger.py with structured logging configuration
- [X] T026 [P] Create app/utils/message_validator.py with message validation utilities
- [X] T030 [P] Create app/utils/retry_mechanism.py with exponential backoff and retry logic
- [X] T035 [P] Create app/services/rate_limiter.py with Redis-based rate limiting implementation
- [X] T040 [P] Create app/services/delivery_tracker.py with delivery status tracking and retry queue logic

## Phase 3: [US1] Deliver Agent Response via Email (Priority: P1)

- [X] T100 [US1] Create app/services/gmail_service.py with Gmail API integration for email delivery
- [X] T101 [P] [US1] Implement email threading logic in gmail_service.py using Message-ID references
- [X] T102 [P] [US1] Implement Gmail API authentication and error handling in gmail_service.py
- [X] T103 [P] [US1] Add rate limiting to gmail_service.py using the rate limiter service
- [X] T104 [P] [US1] Create unit tests for gmail_service.py in tests/unit/test_gmail_service.py
- [X] T105 [P] [US1] Implement email delivery status tracking in gmail_service.py

## Phase 4: [US2] Deliver Agent Response via WhatsApp (Priority: P2)

- [X] T200 [US2] Create app/services/whatsapp_service.py with Twilio WhatsApp API integration
- [X] T201 [P] [US2] Implement WhatsApp message formatting and validation in whatsapp_service.py
- [X] T202 [P] [US2] Add rate limiting to whatsapp_service.py using the rate limiter service
- [X] T203 [P] [US2] Implement Twilio API error handling in whatsapp_service.py
- [X] T204 [P] [US2] Create unit tests for whatsapp_service.py in tests/unit/test_whatsapp_service.py
- [X] T205 [P] [US2] Implement WhatsApp delivery status tracking in whatsapp_service.py

## Phase 5: [US3] Deliver Agent Response via Web Notification (Priority: P2)

- [X] T300 [US3] Create app/services/web_notification_service.py with webhook delivery logic
- [X] T301 [P] [US3] Implement HTTP webhook delivery with error handling in web_notification_service.py
- [X] T302 [P] [US3] Add retry logic for failed webhook deliveries in web_notification_service.py
- [X] T303 [P] [US3] Create unit tests for web_notification_service.py in tests/unit/test_web_notifications.py
- [X] T304 [P] [US3] Implement web notification delivery status tracking in web_notification_service.py

## Phase 6: [US4] Maintain Communication Log (Priority: P1)

- [X] T400 [US4] Create app/services/response_dispatcher.py with Kafka consumer for outbound_responses
- [X] T401 [P] [US4] Implement message routing logic in response_dispatcher.py based on channel_destination metadata
- [X] T402 [P] [US4] Integrate delivery services with response_dispatcher.py for message delivery
- [X] T403 [P] [US4] Implement database synchronization in response_dispatcher.py for message status updates
- [X] T404 [P] [US4] Add delivery status tracking integration in response_dispatcher.py
- [X] T405 [P] [US4] Create unit tests for response_dispatcher.py in tests/unit/test_response_dispatcher.py

## Phase 7: Integration and Testing

- [X] T500 Create integration tests for multi-channel delivery in tests/integration/test_multi_channel_delivery.py
- [X] T501 Create integration tests for response dispatcher in tests/integration/test_response_dispatcher.py
- [X] T502 Create integration tests for rate limiting in tests/integration/test_rate_limiter.py
- [X] T503 Create stress tests for concurrent deliveries in tests/stress/test_concurrent_deliveries.py
- [X] T504 Create stress tests for API limits in tests/stress/test_api_limits.py

## Phase 8: API and Monitoring

- [X] T600 Create app/main.py with FastAPI application and response dispatcher initialization
- [X] T601 Create API endpoints for delivery status tracking based on dispatcher_api.yaml
- [X] T602 Create API endpoints for channel configuration management based on dispatcher_api.yaml
- [X] T603 Create API endpoints for retry queue management based on dispatcher_api.yaml
- [X] T604 Create API endpoints for metrics and monitoring based on dispatcher_api.yaml

## Phase 9: System Operations

- [X] T700 Create scripts/start_dispatcher.py with proper signal handling and graceful startup
- [X] T701 Create scripts/cleanup_dispatcher.py with system cleanup for stress testing
- [X] T702 Create graceful shutdown logic in response_dispatcher.py with signal handlers
- [X] T703 Create health check endpoints in app/main.py for monitoring
- [X] T704 Create monitoring and metrics collection in app/services/response_dispatcher.py

## Phase 10: Polish and Cross-Cutting Concerns

- [X] T800 Create comprehensive README.md with setup and usage instructions
- [X] T801 Add proper error handling and logging throughout all services
- [X] T802 Perform security review of credential handling and API access
- [X] T803 Optimize performance for high-volume message processing
- [X] T804 Conduct end-to-end testing of all delivery channels
- [X] T805 Update documentation with operational procedures

## Phase 11: Additional Requirements from User Prompt

- [X] T900 Implement ResponseDispatcher as Kafka Consumer that reads from 'outbound_responses' and selects delivery method based on 'channel' field in app/services/response_dispatcher.py
- [X] T901 Develop Gmail Sender module with Gmail API integration ensuring 'In-Reply-To' and 'References' headers are set for email threading in app/services/gmail_service.py
- [X] T902 Develop WhatsApp Sender module integrating Twilio REST API to send outbound WhatsApp messages in app/services/whatsapp_service.py
- [X] T903 Implement Egress Logger module that updates PostgreSQL 'messages' table with final status and timestamp of outbound message in app/services/delivery_tracker.py
- [X] T904 Create Retry Manager with exponential backoff for failed API calls to external providers (Google/Twilio) in app/utils/retry_mechanism.py
- [X] T905 Build Unified Dashboard CLI script to query DB and show count of Inbound vs. Outbound messages across all channels in scripts/dashboard_cli.py
- [X] T906 Create stress test verification script that triggers 10 messages across 3 channels and verifies all 10 are marked 'delivered' in database in scripts/verification_stress_test.py

## Dependencies

- **US1 (Email)** depends on: Foundational Components (Phase 2)
- **US2 (WhatsApp)** depends on: Foundational Components (Phase 2)
- **US3 (Web Notifications)** depends on: Foundational Components (Phase 2)
- **US4 (Communication Log)** depends on: Foundational Components (Phase 2), US1, US2, US3
- **Integration** depends on: US1, US2, US3, US4
- **System Operations** depends on: US4
- **Additional Requirements** depends on: All previous phases

## Parallel Execution Opportunities

- T101-T105 can run in parallel with T201-T205
- T101-T105 can run in parallel with T301-T304
- T201-T205 can run in parallel with T301-T304
- T500-T502 can run in parallel with T600-T604
- T801-T805 can run in parallel after Phase 8 completion
- T900-T906 can run in parallel after all previous phases completion

## Implementation Strategy

**MVP Scope**: Complete Phase 1, Phase 2, and Phase 3 (US1) to establish the foundational email delivery capability. This provides a minimal but functional response delivery system that can be tested and validated early.

**Incremental Delivery**: After MVP, add WhatsApp (US2), then Web Notifications (US3), then Communication Logging (US4), followed by integration and polish phases.