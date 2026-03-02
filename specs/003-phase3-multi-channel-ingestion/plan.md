# Implementation Plan: Phase 3: Multi-Channel Ingestion

**Branch**: `003-phase3-multi-channel-ingestion` | **Date**: 2026-02-02 | **Spec**: specs/003-phase3-multi-channel-ingestion/spec.md
**Input**: Feature specification from `/specs/003-phase3-multi-channel-ingestion/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implementation of production-grade multi-channel ingestion services for the Customer Success Digital FTE. This includes FastAPI webhook handlers for Twilio (WhatsApp) and Web Support Form, Gmail API integration using polling strategy, message normalization layer to unify channel payloads into a single InboundMessage schema, and Kafka Producer to publish to inbound_events topic. The system integrates with Phase 2 DatabaseManager for identity resolution and implements robust error handling to ensure no message loss.

## Technical Context

**Language/Version**: Python 3.11 (as per constitution)
**Primary Dependencies**: FastAPI, Pydantic, SQLAlchemy, aiokafka, google-api-python-client, twilio, python-dotenv
**Storage**: PostgreSQL with pgvector extension (as per constitution) via DatabaseManager from Phase 2
**Testing**: pytest with 24-hour multi-channel simulation metrics (as per constitution)
**Target Platform**: Linux server environment with Docker orchestration
**Project Type**: Web application with webhook handlers and background services
**Performance Goals**: Support 10,000+ concurrent connections with 99.9% uptime, message normalization within 100ms for 95% of messages, identity lookups within 200ms for 95% of messages
**Constraints**: All components must be contained within /phase-3-multi-channel-ingestion directory, ensure no message loss during ingestion, maintain 99.9% reliability across all channels
**Scale/Scope**: Production-grade infrastructure supporting multi-channel customer interactions with identity resolution and message normalization

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Architecture-First Design**: Uses FastAPI and PostgreSQL as mandated by constitution
- **Quality Assurance Excellence**: Will implement pytest-based testing with 24-hour simulation metrics as required
- **Phased Evolution**: Following proper Phase 3 (Multi-Channel Ingestion) approach before advancement
- **Manual Implementation Discipline**: All implementation will be manually triggered
- **Phase Gate Compliance**: Following proper Specify → Plan → Tasks → Implement workflow

## Project Structure

### Documentation (this feature)

```text
specs/003-phase3-multi-channel-ingestion/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
/phase-3-multi-channel-ingestion/
├── app/
│   ├── __init__.py
│   ├── main.py                          # FastAPI application entry point
│   ├── models/
│   │   ├── __init__.py
│   │   ├── inbound_message.py           # Pydantic schema for unified message format
│   │   ├── channel_payload.py           # Raw channel-specific message formats
│   │   └── kafka_event.py               # Schema for Kafka events
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ingestion_service.py         # Core ingestion logic: Receive -> Normalize -> Identify -> Publish
│   │   ├── message_normalizer.py        # Message normalization layer
│   │   ├── identity_resolver.py         # Integration with DatabaseManager for customer lookups
│   │   ├── gmail_integrator.py          # Gmail API integration with OAuth2
│   │   ├── twilio_validator.py          # Twilio webhook signature validation
│   │   └── kafka_producer.py            # Kafka producer for inbound_events topic
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── whatsapp_webhook.py          # Twilio webhook handler for WhatsApp
│   │   ├── webform_endpoint.py          # Web Support Form endpoint with API key validation
│   │   └── health_check.py              # Health check endpoints
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py                  # Application settings and environment variables
│   │   └── security.py                  # Security configurations
│   └── utils/
│       ├── __init__.py
│       ├── error_handlers.py            # Error handling and retry logic
│       ├── validators.py                # Custom validators
│       └── logger.py                    # Logging utilities
├── scripts/
│   ├── start_server.py                  # Server startup script
│   └── gmail_poller.py                  # Background script for Gmail polling
├── tests/
│   ├── unit/
│   │   ├── test_models.py
│   │   ├── test_services.py
│   │   └── test_routes.py
│   ├── integration/
│   │   ├── test_ingestion_flow.py
│   │   ├── test_webhooks.py
│   │   └── test_kafka_integration.py
│   └── conftest.py
├── requirements.txt                     # Dependencies
├── docker-compose.yml                   # Docker orchestration (if needed)
└── README.md                           # Documentation
```

**Structure Decision**: Selected web application structure with clear separation of concerns between models, services, routes, and configuration. All components are contained within the phase-3-multi-channel-ingestion directory as required. The design enables independent testing of each component while maintaining the required integration with Phase 2 DatabaseManager for identity resolution.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
