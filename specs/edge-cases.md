# Edge Cases Document - Customer Success Digital FTE

## Overview
This document catalogs 20+ edge cases per channel discovered during incubation, with handling strategies and corresponding test cases.

---

## Global Edge Cases (All Channels)

| # | Edge Case | Handling Strategy | Test Case | Priority |
|---|-----------|-------------------|-----------|----------|
| G1 | Empty message body | Return friendly prompt: "It looks like your message was empty. How can I help you today?" | `test_empty_message_all_channels` | High |
| G2 | Single word "help" | Provide general assistance menu with common topics | `test_single_word_help` | Medium |
| G3 | Single word "hi" or "hello" | Greet and ask how to assist | `test_greeting_message` | Low |
| G4 | ALL CAPS message (>50% uppercase) | Flag as frustrated customer, run sentiment analysis, consider escalation | `test_all_caps_detection` | High |
| G5 | Non-English language message | Acknowledge, attempt response in English, offer human support if needed | `test_non_english_message` | Medium |
| G6 | Very long message (>1000 words) | Process full text, truncate display if needed, store complete in ticket | `test_long_message_processing` | Medium |
| G7 | Message with only special characters | Treat as empty, ask for clarification | `test_special_chars_only` | Low |
| G8 | Repeated identical messages (spam) | Acknowledge once, deduplicate, flag if >3 repetitions | `test_duplicate_message_handling` | Medium |
| G9 | Message with profanity/slurs | Escalate as urgent, do not repeat profanity in response | `test_profanity_escalation` | High |
| G10 | Legal threat ("lawyer", "sue") | Immediate L3 escalation, empathetic acknowledgment only | `test_legal_threat_escalation` | Critical |
| G11 | Refund request (explicit) | Immediate escalation to billing, do not process | `test_refund_request_escalation` | Critical |
| G12 | Pricing negotiation | Escalate to sales team, do not quote prices | `test_pricing_negotiation_escalation` | Critical |
| G13 | Explicit human request ("agent", "manager") | Immediate escalation with context | `test_explicit_human_request` | High |
| G14 | Account deletion / GDPR request | Escalate to compliance team as priority | `test_account_deletion_request` | Critical |
| G15 | Security incident reported | Critical escalation to security team | `test_security_incident_report` | Critical |
| G16 | Data loss reported | Urgent escalation with technical context | `test_data_loss_report` | Critical |
| G17 | SQL injection attempt in message | Sanitize input, log security event, do not execute | `test_sql_injection_prevention` | Critical |
| G18 | XSS attempt in message | Strip HTML/script tags, sanitize, log event | `test_xss_prevention` | Critical |
| G19 | Message with attachment reference | Acknowledge attachment, note in ticket, process text | `test_attachment_reference` | Medium |
| G20 | Repeated contact (3+ same issue) | Escalate with full conversation history | `test_repeated_contact_escalation` | High |

---

## Email Channel Edge Cases

| # | Edge Case | Handling Strategy | Test Case | Priority |
|---|-----------|-------------------|-----------|----------|
| E1 | Email with only subject, no body | Use subject as message, create ticket | `test_email_subject_only` | Medium |
| E2 | Email with large attachment (>10MB) | Process text content only, note attachment in ticket | `test_email_large_attachment` | Medium |
| E3 | Email reply chain (RE: RE: RE:) | Parse latest reply only, preserve chain in ticket | `test_email_reply_chain_parsing` | High |
| E4 | HTML-only email (no plain text) | Convert HTML to plain text, strip tags | `test_email_html_only` | Medium |
| E5 | Email from noreply@ address | Create ticket but skip response delivery | `test_email_noreply_sender` | Medium |
| E6 | Email with multiple recipients (CC) | Process for primary recipient only | `test_email_cc_handling` | Low |
| E7 | Forwarded email (FW:) | Extract original content, identify actual customer | `test_email_forward_parsing` | Medium |
| E8 | Email with inline images | Process text, note images in ticket | `test_email_inline_images` | Low |
| E9 | Email encoding issues (non-UTF8) | Attempt encoding detection, fallback to UTF-8 replace | `test_email_encoding_fallback` | Medium |
| E10 | Auto-reply / out-of-office email | Detect auto-reply headers, skip processing, log | `test_email_auto_reply_detection` | High |
| E11 | Email bounce-back notification | Detect bounce, mark delivery failed, alert | `test_email_bounce_handling` | High |
| E12 | Email from blocked/spam sender | Check sender reputation, flag for review | `test_email_spam_sender` | Medium |
| E13 | Email with calendar invite | Process text, ignore calendar data | `test_email_calendar_invite` | Low |
| E14 | Email thread with multiple topics | Create separate tickets per distinct topic if detected | `test_email_multi_topic` | Medium |
| E15 | Gmail API rate limit hit (250/min) | Exponential backoff, queue pending, retry | `test_gmail_rate_limit_recovery` | High |
| E16 | Gmail OAuth token expired | Refresh token automatically, retry failed request | `test_gmail_token_refresh` | High |
| E17 | Email with signature containing phone | Do not treat signature phone as WhatsApp contact | `test_email_signature_parsing` | Medium |
| E18 | Very long email subject (>255 chars) | Truncate subject, preserve full in ticket body | `test_email_long_subject` | Low |
| E19 | Email sent to wrong support address | Route to correct department or return generic ack | `test_email_misrouted` | Medium |
| E20 | Encrypted/S-MIME email | Cannot process encrypted content, escalate | `test_email_encrypted_content` | Medium |

---

## WhatsApp Channel Edge Cases

| # | Edge Case | Handling Strategy | Test Case | Priority |
|---|-----------|-------------------|-----------|----------|
| W1 | WhatsApp voice note (audio message) | Acknowledge receipt, note media type, create text ticket | `test_whatsapp_voice_note` | Medium |
| W2 | WhatsApp image/photo message | Acknowledge receipt, ask to describe issue in text | `test_whatsapp_image_message` | Medium |
| W3 | WhatsApp video message | Acknowledge receipt, ask to describe issue in text | `test_whatsapp_video_message` | Low |
| W4 | WhatsApp location share | Note location, ask how to help | `test_whatsapp_location_share` | Low |
| W5 | WhatsApp contact card share | Ignore contact data, ask for support query | `test_whatsapp_contact_share` | Low |
| W6 | WhatsApp "pocket dial" (empty/accidental) | Ignore or send gentle check-in after 2nd occurrence | `test_whatsapp_pocket_dial` | Medium |
| W7 | WhatsApp message with emojis only | Ask for text description of the issue | `test_whatsapp_emoji_only` | Medium |
| W8 | WhatsApp rapid-fire messages (5+ in 10s) | Aggregate messages, process as single thread | `test_whatsapp_rapid_messages` | High |
| W9 | WhatsApp group message (not 1:1) | Only process direct messages, ignore group | `test_whatsapp_group_message_filter` | Medium |
| W10 | WhatsApp message from new number (no customer record) | Create new customer with phone, request email for linking | `test_whatsapp_new_customer` | High |
| W11 | WhatsApp status message (not a support query) | Ignore status updates, only process direct messages | `test_whatsapp_status_update` | Low |
| W12 | Twilio webhook signature validation failure | Reject message, log security event | `test_whatsapp_invalid_signature` | Critical |
| W13 | WhatsApp 24-hour session window expired | Use template message to re-engage | `test_whatsapp_session_expired` | High |
| W14 | WhatsApp message in non-Latin script (Arabic, Hindi) | Process with Unicode support, respond in English | `test_whatsapp_non_latin_script` | Medium |
| W15 | Twilio API rate limit hit (50/min) | Backoff and queue, retry with exponential delay | `test_twilio_rate_limit_recovery` | High |
| W16 | WhatsApp number format variations (+1, 001, etc.) | Normalize to E.164 format before lookup | `test_whatsapp_number_normalization` | High |
| W17 | WhatsApp message with URL/link | Process text normally, do not follow links | `test_whatsapp_url_handling` | Medium |
| W18 | WhatsApp delivery receipt (not a message) | Filter out, do not create ticket | `test_whatsapp_delivery_receipt` | Medium |
| W19 | WhatsApp message exceeds 4096 char limit | Split response into multiple messages | `test_whatsapp_long_response_split` | Medium |
| W20 | Twilio account suspended/quota exceeded | Alert ops, switch to degraded mode, queue messages | `test_twilio_account_issue` | Critical |

---

## Web Form Channel Edge Cases

| # | Edge Case | Handling Strategy | Test Case | Priority |
|---|-----------|-------------------|-----------|----------|
| WF1 | Form submitted with all fields empty | Return validation error, do not create ticket | `test_webform_empty_submission` | High |
| WF2 | Invalid email format in form | Client-side + server-side validation, reject | `test_webform_invalid_email` | High |
| WF3 | Form double-submit (user clicks twice) | Deduplicate by request ID, process once | `test_webform_double_submit` | High |
| WF4 | Very large form submission (>10KB text) | Accept with size limit, truncate for processing | `test_webform_large_submission` | Medium |
| WF5 | Form submission with HTML/script tags | Sanitize input, strip dangerous tags, store clean | `test_webform_xss_sanitization` | Critical |
| WF6 | Form submission from bot/crawler | Rate limit by IP, CAPTCHA validation | `test_webform_bot_detection` | High |
| WF7 | Concurrent form submissions (100+/sec) | Rate limiting, queue via Kafka | `test_webform_high_concurrency` | High |
| WF8 | Form with special characters in name | Accept Unicode names, sanitize for display | `test_webform_special_chars_name` | Medium |
| WF9 | Form submitted without JavaScript | Progressive enhancement, server-side validation | `test_webform_no_js_submission` | Low |
| WF10 | Form session timeout | Return friendly timeout message, preserve draft | `test_webform_session_timeout` | Medium |
| WF11 | API key missing or invalid | Return 401 Unauthorized, log attempt | `test_webform_invalid_api_key` | Critical |
| WF12 | Form submission during maintenance | Queue message, acknowledge with maintenance notice | `test_webform_maintenance_mode` | Medium |
| WF13 | Form with file upload attempt | Reject file, explain text-only support | `test_webform_file_upload_reject` | Medium |
| WF14 | Browser back button resubmit | Detect duplicate, show previous submission status | `test_webform_back_button_resubmit` | Medium |
| WF15 | Form submitted from unauthorized origin (CORS) | Reject with CORS error | `test_webform_cors_violation` | High |
| WF16 | Network timeout during submission | Client-side retry, server idempotency key | `test_webform_network_timeout` | Medium |
| WF17 | Form with phone number in email field | Validate email format strictly, reject | `test_webform_phone_in_email_field` | Medium |
| WF18 | Multiple browser tabs submitting same form | Deduplicate by session + content hash | `test_webform_multi_tab_submit` | Medium |
| WF19 | Form submitted with extremely long name (>255 chars) | Truncate name, preserve in ticket | `test_webform_long_name` | Low |
| WF20 | Form category dropdown invalid value | Server-side validation, reject invalid category | `test_webform_invalid_category` | Medium |

---

## Infrastructure Edge Cases

| # | Edge Case | Handling Strategy | Test Case | Priority |
|---|-----------|-------------------|-----------|----------|
| I1 | PostgreSQL connection pool exhausted | Queue requests, increase pool, alert ops | `test_db_pool_exhaustion` | Critical |
| I2 | Kafka broker down | Buffer messages locally, reconnect with backoff | `test_kafka_broker_failure` | Critical |
| I3 | Redis cache unavailable | Bypass rate limiter (degrade gracefully), alert | `test_redis_unavailable` | High |
| I4 | Kubernetes pod OOM killed | Auto-restart via K8s, alert on repeated OOM | `test_pod_oom_recovery` | High |
| I5 | DNS resolution failure | Retry with exponential backoff, fallback IP | `test_dns_failure_recovery` | Medium |
| I6 | SSL certificate expired | Alert ops, auto-renew if configured | `test_ssl_cert_expiry` | Critical |
| I7 | Disk space full | Alert ops, rotate logs, clean temp files | `test_disk_space_monitoring` | High |
| I8 | Network partition between services | Detect via health checks, queue locally | `test_network_partition_handling` | High |
| I9 | Concurrent database deadlock | Retry transaction with backoff (2 handled in stress test) | `test_db_deadlock_recovery` | High |
| I10 | API response payload too large | Paginate results, limit response size | `test_large_response_handling` | Medium |

---

## Summary Statistics
- **Total edge cases documented:** 90+
- **Per-channel breakdown:** Global (20) + Email (20) + WhatsApp (20) + Web Form (20) + Infrastructure (10)
- **Critical priority:** 15 cases
- **High priority:** 28 cases
- **Medium priority:** 33 cases
- **Low priority:** 14 cases
