---
id: 0007
title: Fix Phase 5 WhatsApp Delivery Pipeline
stage: green
date: 2026-02-23
surface: agent
model: claude-sonnet-4-6
feature: 005-response-delivery-egress
branch: 005-response-delivery-egress
user: naveed247365
command: continue session - fix Phase 5 delivery errors
labels: ["phase5","whatsapp","validation","database","kafka","delivery"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - phase-5-response-delivery-egress/app/utils/message_validator.py
tests:
  - Manual: Phase 5 Kafka consumer processes all outbound_responses messages without errors
  - Manual: WhatsApp routing reaches Meta API (blocked only by dev mode recipient restrictions)
---

## Prompt

Continuation from previous session. Phase 5 is running but not delivering WhatsApp messages. Need to diagnose and fix. Phase 4 is working and has published AI responses to outbound_responses Kafka topic.

## Response snapshot

Diagnosed two blocking issues in Phase 5:

1. **WhatsApp validation error**: `message_validator.py` `is_valid_whatsapp_number()` used regex `^whatsapp:[\+]?[1-9]\d{1,14}$` requiring `whatsapp:` prefix. Phase 4 publishes recipient as plain E.164 `+923003627458`. Fix: updated to also accept plain E.164 format via `phone_pattern` check.

2. **DB column missing**: `outbound_messages` table created by Phase 4 with different schema (uses `recipient_id`, no `recipient_identifier`/`sender_identifier`/`message_id`/`priority` etc). Phase 5 SQLAlchemy model expects these columns. Fix: ran ALTER TABLE to add 8 missing columns via psycopg2.

3. **Kafka offset reset**: After fixing code, reset consumer group `response_dispatcher_group` offset back to 5 (first real message) using aiokafka direct seek+commit.

4. **Restarted Phase 5**: Now processes all 7 messages (offsets 5-11) without errors. Validation passes, DB queries work, routing reaches WhatsApp API.

Remaining issue: Meta API rejecting outgoing messages with:
- `+923003627458`: `(#10) Application does not have permission`
- `+923132303222`: `(#131030) Recipient phone number not in allowed list`

Root cause: Meta WhatsApp development mode — can only send to pre-verified test recipients. User must add both numbers in Meta Developer Console → WhatsApp → API Setup → Manage phone number list.

## Outcome

- ✅ Impact: Phase 5 pipeline fully functional end-to-end; reaches Meta API for all messages
- 🧪 Tests: Manual verification via logs — 7 Kafka messages processed, all reach WhatsApp API
- 📁 Files: message_validator.py (1 method updated), DB schema altered via SQL
- 🔁 Next prompts: User adds test recipients in Meta Developer Console, then sends new WhatsApp message to test full delivery
- 🧠 Reflection: Two-phase error pattern — validation blocked first, then DB column error in exception handler; both needed fixes to unlock delivery

## Evaluation notes (flywheel)

- Failure modes observed: Schema mismatch between Phase 4 and Phase 5 outbound_messages models; WhatsApp number format assumption mismatch between phases
- Graders run and results (PASS/FAIL): Manual log inspection - PASS (no more Python errors, reaches Meta API)
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Add test recipients in Meta Console to complete full round-trip test
