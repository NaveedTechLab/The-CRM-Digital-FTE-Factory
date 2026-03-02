<!-- SYNC IMPACT REPORT:
Version change: N/A (initial creation) → 1.0.0
Modified principles: N/A
Added sections: All sections (initial creation)
Removed sections: N/A
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ updated
  - .specify/templates/spec-template.md ✅ updated
  - .specify/templates/tasks-template.md ✅ updated
  - .specify/templates/commands/*.md ⚠ pending review
  - README.md ⚠ pending review
Follow-up TODOs: None
-->
# CUSTOMER SUCCESS DIGITAL FTE Constitution

## Core Principles

### Mission-Driven Development
All development must align with the mission of building a production-grade AI Employee (Digital FTE) that operates 24/7 across Gmail, WhatsApp, and Web Form, utilizing a FastAPI/PostgreSQL/Kafka/K8s stack. Every feature, function, and architectural decision must contribute directly to this mission.

### Phased Evolution
Development follows a strict 6-phase progression: Incubation → Core Infrastructure → Multi-Channel Ingestion → Agent Intelligence → Deployment Orchestration → Production QA. Each phase must be completed before advancing; no skipping or parallel development across phases.

### Manual Implementation Discipline
No auto-implementation; all work must be manually triggered by the user via prompts. This ensures intentional, thoughtful development rather than automated generation. All code must reside in phase-specific folders following the prescribed structure.

### Architecture-First Design
Backend: FastAPI, Python 3.11+; Database: PostgreSQL with pgvector for RAG; Streaming: Kafka for asynchronous message processing; Agent: OpenAI Agents SDK; Deployment: Docker & Kubernetes (K8s). All components must conform to these technology standards.

### Quality Assurance Excellence
Testing: Pytest with 24-hour multi-channel simulation metrics. Every feature must undergo comprehensive testing across all supported channels (Gmail, WhatsApp, Web Form) before phase completion. Performance, reliability, and accuracy metrics must meet production standards.

### Phase Gate Compliance
Each phase must follow the workflow: Specify → Plan → Tasks → Implement. Exit criteria for each phase must be verified before proceeding. Only one phase may be active at a time to ensure focused development and proper validation.

## Technical Standards

### Backend Architecture
All backend services must be built using FastAPI with Python 3.11+ as the primary language. All API endpoints must follow RESTful principles with proper error handling, authentication, and rate limiting. Code must be properly typed with Python type hints and follow PEP 8 standards.

### Database Design
PostgreSQL must be used as the primary database with pgvector extension for RAG (Retrieval Augmented Generation) capabilities. All database schemas must be version-controlled with proper migration scripts. Connection pooling, indexing, and query optimization are mandatory for production performance.

### Streaming Infrastructure
Apache Kafka must be used for all asynchronous message processing between services. All events must follow a consistent schema with proper serialization and deserialization. Consumer groups must be properly configured for scalability and fault tolerance.

## Development Workflow

### Specification Requirements
Every feature must begin with a detailed specification that outlines requirements, acceptance criteria, dependencies, and success metrics. Specifications must align with the phase objectives and overall mission. No implementation should begin without approved specifications.

### Code Review Process
All code changes must undergo peer review before merging. Reviews must verify compliance with architectural standards, security requirements, performance benchmarks, and testing coverage. Automated testing must pass before any manual review begins.

### Deployment Validation
All components must be containerized using Docker and orchestrated with Kubernetes. Deployment manifests must include proper resource limits, health checks, and monitoring configurations. Rollback procedures must be tested and documented.

## Governance

Constitution serves as the authoritative source for all development practices and architectural decisions. All team members must comply with these principles. Amendments require formal documentation, approval from project leadership, and migration plan for existing code. All PRs and reviews must verify constitutional compliance.

**Version**: 1.0.0 | **Ratified**: 2026-02-02 | **Last Amended**: 2026-02-02