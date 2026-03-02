---
id: 1
title: "Customer Success Digital FTE Constitution"
stage: constitution
date: "2026-02-02"
model: "claude-sonnet-4-5-20250929"
surface: "agent"
command: "sp.constitution"
labels: ["constitution", "governance", "standards"]
files:
  - ".specify/memory/constitution.md"
tests: []
link:
  spec: null
  ticket: null
  adr: null
  pr: null
---

# Prompt History Record: Customer Success Digital FTE Constitution

## PROMPT_TEXT

create content="

# PROJECT CONSTITUTION: CUSTOMER SUCCESS DIGITAL FTE



## 1. MISSION & SCOPE

Build a production-grade AI Employee (Digital FTE) that operates 24/7 across Gmail, WhatsApp, and Web Form, utilizing a FastAPI/PostgreSQL/Kafka/K8s stack.



## 2. ARCHITECTURAL RULES

- STAGE 1 (Incubation): Prototyping and requirement discovery.

- STAGE 2 (Specialization): Hardening via OpenAI Agents SDK and production infrastructure.

- All code must reside in phase-specific folders.

- Internal SpecifyPlus folders (./.specify) are strictly OFF-LIMITS.

- No auto-implementation; all work must be manually triggered by the user via prompts.



## 3. PROJECT STRUCTURE

/phase-1-incubation-prototype

/phase-2-core-infrastructure-database

/phase-3-multi-channel-ingestion

/phase-4-agent-intelligence-logic

/phase-5-deployment-orchestration-k8s

/phase-6-production-qa-hardening



## 4. PHASE CONTROLS

- Only one phase may be active at a time.

- Every phase must follow the workflow: Specify -> Plan -> Tasks -> Implement.

- Exit criteria for each phase must be verified before proceeding.



## 5. TECHNICAL STANDARDS

- Backend: FastAPI, Python 3.11+

- Database: PostgreSQL with pgvector for RAG

- Streaming: Kafka for asynchronous message processing

- Agent: OpenAI Agents SDK

- Deployment: Docker & Kubernetes (K8s)

- Testing: Pytest with 24-hour multi-channel simulation metrics

"

## RESPONSE_TEXT

Created a comprehensive project constitution for the Customer Success Digital FTE project based on the user's requirements. The constitution includes:

- Six core principles aligned with the mission and phased development approach
- Technical standards for backend, database, and streaming infrastructure
- Development workflow requirements
- Governance rules

The constitution enforces the phased evolution approach (6 phases), manual implementation discipline, architecture-first design with the specified technology stack (FastAPI, PostgreSQL, Kafka, K8s), and quality assurance excellence with comprehensive testing requirements. It also establishes the proper development workflow with specification requirements, code review processes, and deployment validation procedures.

## OUTCOME

Successfully created project constitution at `.specify/memory/constitution.md` that captures all requirements from the user input, organized into appropriate sections with clear principles and governance rules.

## EVALUATION

The constitution properly enforces the mission-driven development approach, phased evolution requirements, manual implementation discipline, and technical standards specified by the user. It provides a solid governance foundation for the project.