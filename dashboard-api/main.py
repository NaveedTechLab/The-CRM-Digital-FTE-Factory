"""
CRM Dashboard API - Real-time backend for the CRM Dashboard UI.
Connects to Neon PostgreSQL and serves data from actual project tables:
  - agent_messages (conversations from Phase 4)
  - outbound_messages (responses from Phase 4/5)
  - delivery_logs (delivery attempts from Phase 5)
  - retry_queue_items (retry queue from Phase 5)
Also creates/manages: customers, tickets, messages tables for the dashboard.
Runs on port 8002.
"""

import os
import sys
import uuid
import smtplib
import imaplib
import email as email_lib
import threading
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import (
    create_engine, func, text, Column, String, Text, Integer, Boolean,
    DateTime, Float, ForeignKey, desc, asc
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# ── Database Setup ──────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "")
# Remove channel_binding for psycopg2 compatibility
if "channel_binding" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("&channel_binding=require", "").replace("?channel_binding=require", "")

engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── ORM Models matching ACTUAL database ─────────────────────────────
class AgentMessage(Base):
    __tablename__ = 'agent_messages'
    __table_args__ = {'extend_existing': True}
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(255))
    conversation_id = Column(String(255))
    inbound_message_id = Column(String(255))
    message_type = Column(String(50))
    content = Column(Text)
    role = Column(String(50))
    timestamp = Column(DateTime)
    confidence_score = Column(Float)
    escalation_flag = Column(Boolean, default=False)
    processed_status = Column(String(50))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class OutboundMessage(Base):
    __tablename__ = 'outbound_messages'
    __table_args__ = {'extend_existing': True}
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_message_id = Column(String(255))
    conversation_id = Column(String(255))
    response_type = Column(String(50))
    content = Column(Text)
    channel_destination = Column(String(50))
    recipient_id = Column(String(255))
    confidence_score = Column(Float)
    escalation_reason = Column(String(255))
    ticket_reference = Column(String(255))
    delivery_status = Column(String(50))
    delivery_attempts = Column(Integer, default=0)
    priority = Column(String(50))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    message_id = Column(String(255))
    failure_reason = Column(String(255))


class DeliveryLog(Base):
    __tablename__ = 'delivery_logs'
    __table_args__ = {'extend_existing': True}
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    outbound_message_id = Column(String(255))
    attempt_number = Column(Integer)
    channel = Column(String(50))
    delivery_method = Column(String(50))
    status_code = Column(Integer)
    success = Column(Boolean)
    error_message = Column(String(500))
    rate_limit_hit = Column(Boolean, default=False)
    timestamp = Column(DateTime)
    processing_time_ms = Column(Integer)
    created_at = Column(DateTime)


class RetryQueueItem(Base):
    __tablename__ = 'retry_queue_items'
    __table_args__ = {'extend_existing': True}
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    outbound_message_id = Column(String(255))
    attempt_number = Column(Integer)
    scheduled_retry = Column(DateTime)
    failure_reason = Column(String(500))
    priority = Column(Integer)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


# ── Dashboard-specific tables (created if not exist) ────────────────
class DashboardTicket(Base):
    __tablename__ = 'dashboard_tickets'
    __table_args__ = {'extend_existing': True}
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_ref = Column(String(50), unique=True)
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(320), nullable=False)
    subject = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), default='general')
    status = Column(String(50), default='open')
    priority = Column(String(50), default='medium')
    channel = Column(String(50), default='webform')
    assigned_agent = Column(String(255), default='AI Agent')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class DashboardMessage(Base):
    __tablename__ = 'dashboard_messages'
    __table_args__ = {'extend_existing': True}
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_ref = Column(String(50))
    sender_type = Column(String(50))
    sender_name = Column(String(255))
    content = Column(Text)
    direction = Column(String(50))
    channel = Column(String(50), default='webform')
    sent_at = Column(DateTime(timezone=True), server_default=func.now())


# Create dashboard tables
Base.metadata.create_all(bind=engine, tables=[DashboardTicket.__table__, DashboardMessage.__table__])


# ── Pydantic Schemas ────────────────────────────────────────────────
class SupportFormRequest(BaseModel):
    name: str
    email: str
    subject: str
    category: str = "general"
    message: str


class TicketUpdateRequest(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_agent: Optional[str] = None


# ── FastAPI App ─────────────────────────────────────────────────────
app = FastAPI(title="CRM Dashboard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ──────────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected", "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}
    finally:
        db.close()


# ── Dashboard Stats (real data) ─────────────────────────────────────
@app.get("/api/stats")
def get_stats():
    db = SessionLocal()
    try:
        # From actual agent_messages
        total_conversations = db.execute(text("SELECT COUNT(DISTINCT conversation_id) FROM agent_messages")).scalar() or 0
        total_agent_messages = db.execute(text("SELECT COUNT(*) FROM agent_messages")).scalar() or 0
        customer_messages = db.execute(text("SELECT COUNT(*) FROM agent_messages WHERE role='customer'")).scalar() or 0
        agent_responses = db.execute(text("SELECT COUNT(*) FROM agent_messages WHERE role='agent' OR role='assistant'")).scalar() or 0
        escalated = db.execute(text("SELECT COUNT(*) FROM agent_messages WHERE escalation_flag=true")).scalar() or 0

        # Unique customers
        unique_customers = db.execute(text("SELECT COUNT(DISTINCT customer_id) FROM agent_messages")).scalar() or 0

        # From outbound_messages
        total_outbound = db.execute(text("SELECT COUNT(*) FROM outbound_messages")).scalar() or 0
        pending_delivery = db.execute(text("SELECT COUNT(*) FROM outbound_messages WHERE delivery_status='pending'")).scalar() or 0
        delivered = db.execute(text("SELECT COUNT(*) FROM outbound_messages WHERE delivery_status='delivered' OR delivery_status='sent'")).scalar() or 0
        failed_delivery = db.execute(text("SELECT COUNT(*) FROM outbound_messages WHERE delivery_status='failed'")).scalar() or 0

        # Channel distribution from outbound
        whatsapp_count = db.execute(text("SELECT COUNT(*) FROM outbound_messages WHERE channel_destination='whatsapp'")).scalar() or 0
        email_count = db.execute(text("SELECT COUNT(*) FROM outbound_messages WHERE channel_destination='email'")).scalar() or 0
        webform_count = db.execute(text("SELECT COUNT(*) FROM outbound_messages WHERE channel_destination='webform' OR channel_destination='web'")).scalar() or 0

        # From delivery_logs
        total_deliveries = db.execute(text("SELECT COUNT(*) FROM delivery_logs")).scalar() or 0
        successful_deliveries = db.execute(text("SELECT COUNT(*) FROM delivery_logs WHERE success=true")).scalar() or 0
        avg_processing_time = db.execute(text("SELECT COALESCE(AVG(processing_time_ms), 0) FROM delivery_logs")).scalar() or 0

        # From retry_queue_items
        retry_count = db.execute(text("SELECT COUNT(*) FROM retry_queue_items")).scalar() or 0

        # Dashboard tickets
        dash_total = db.execute(text("SELECT COUNT(*) FROM dashboard_tickets")).scalar() or 0
        dash_open = db.execute(text("SELECT COUNT(*) FROM dashboard_tickets WHERE status='open'")).scalar() or 0
        dash_progress = db.execute(text("SELECT COUNT(*) FROM dashboard_tickets WHERE status='in-progress'")).scalar() or 0
        dash_resolved = db.execute(text("SELECT COUNT(*) FROM dashboard_tickets WHERE status='resolved' OR status='closed'")).scalar() or 0
        dash_critical = db.execute(text("SELECT COUNT(*) FROM dashboard_tickets WHERE priority='critical' AND status NOT IN ('resolved','closed')")).scalar() or 0

        delivery_rate = round((successful_deliveries / total_deliveries * 100), 1) if total_deliveries > 0 else 0

        return {
            "conversations": {
                "total": total_conversations,
                "agent_messages": total_agent_messages,
                "customer_messages": customer_messages,
                "agent_responses": agent_responses,
                "escalated": escalated,
            },
            "customers": {
                "unique": unique_customers,
            },
            "delivery": {
                "total_outbound": total_outbound,
                "pending": pending_delivery,
                "delivered": delivered,
                "failed": failed_delivery,
                "delivery_rate": delivery_rate,
                "avg_processing_ms": round(avg_processing_time, 1),
            },
            "channels": {
                "email": email_count,
                "whatsapp": whatsapp_count,
                "webform": webform_count,
            },
            "tickets": {
                "total": dash_total,
                "open": dash_open,
                "in_progress": dash_progress,
                "resolved": dash_resolved,
                "critical": dash_critical,
            },
            "retry_queue": retry_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    finally:
        db.close()


# ── Conversations (from agent_messages) ─────────────────────────────
@app.get("/api/conversations")
def list_conversations(limit: int = 50):
    db = SessionLocal()
    try:
        rows = db.execute(text("""
            SELECT conversation_id, customer_id,
                   COUNT(*) as message_count,
                   MIN(timestamp) as started_at,
                   MAX(timestamp) as last_message,
                   BOOL_OR(escalation_flag) as has_escalation
            FROM agent_messages
            GROUP BY conversation_id, customer_id
            ORDER BY MAX(timestamp) DESC
            LIMIT :limit
        """), {"limit": limit}).fetchall()

        return {
            "conversations": [
                {
                    "conversation_id": r.conversation_id,
                    "customer_id": r.customer_id,
                    "message_count": r.message_count,
                    "started_at": r.started_at.isoformat() if r.started_at else None,
                    "last_message": r.last_message.isoformat() if r.last_message else None,
                    "has_escalation": r.has_escalation or False,
                }
                for r in rows
            ],
            "total": len(rows),
        }
    finally:
        db.close()


@app.get("/api/conversations/{conversation_id}")
def get_conversation(conversation_id: str):
    db = SessionLocal()
    try:
        messages = db.execute(text("""
            SELECT id, customer_id, content, role, timestamp, confidence_score, escalation_flag
            FROM agent_messages
            WHERE conversation_id = :cid
            ORDER BY timestamp ASC
        """), {"cid": conversation_id}).fetchall()

        if not messages:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Get matching outbound
        outbound = db.execute(text("""
            SELECT id, content, channel_destination, delivery_status, created_at
            FROM outbound_messages
            WHERE conversation_id = :cid
            ORDER BY created_at ASC
        """), {"cid": conversation_id}).fetchall()

        return {
            "conversation_id": conversation_id,
            "customer_id": messages[0].customer_id,
            "messages": [
                {
                    "id": str(m.id),
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                    "confidence_score": m.confidence_score,
                    "escalation_flag": m.escalation_flag,
                }
                for m in messages
            ],
            "outbound": [
                {
                    "id": str(o.id),
                    "content": o.content,
                    "channel": o.channel_destination,
                    "delivery_status": o.delivery_status,
                    "created_at": o.created_at.isoformat() if o.created_at else None,
                }
                for o in outbound
            ],
        }
    finally:
        db.close()


# ── Agent Messages (all) ───────────────────────────────────────────
@app.get("/api/messages")
def list_messages(
    role: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
):
    db = SessionLocal()
    try:
        conditions = []
        params = {"limit": limit, "offset": offset}

        if role and role != 'all':
            conditions.append("role = :role")
            params["role"] = role
        if search:
            conditions.append("content ILIKE :search")
            params["search"] = f"%{search}%"

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        total = db.execute(text(f"SELECT COUNT(*) FROM agent_messages {where}"), params).scalar() or 0

        rows = db.execute(text(f"""
            SELECT id, customer_id, conversation_id, content, role, timestamp,
                   confidence_score, escalation_flag
            FROM agent_messages {where}
            ORDER BY timestamp DESC
            LIMIT :limit OFFSET :offset
        """), params).fetchall()

        return {
            "messages": [
                {
                    "id": str(r.id),
                    "customer_id": r.customer_id,
                    "conversation_id": r.conversation_id,
                    "content": r.content,
                    "role": r.role,
                    "direction": "inbound" if r.role == "customer" else "outbound",
                    "channel": _extract_channel(r.customer_id),
                    "sender_name": _extract_name(r.customer_id) if r.role == "customer" else "AI Agent",
                    "sender_type": r.role,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    "confidence_score": r.confidence_score,
                    "escalation_flag": r.escalation_flag,
                }
                for r in rows
            ],
            "total": total,
        }
    finally:
        db.close()


# ── Outbound Messages ──────────────────────────────────────────────
@app.get("/api/outbound")
def list_outbound(
    status: Optional[str] = None,
    channel: Optional[str] = None,
    limit: int = Query(default=50, le=200),
):
    db = SessionLocal()
    try:
        conditions = []
        params = {"limit": limit}

        if status and status != 'all':
            conditions.append("delivery_status = :status")
            params["status"] = status
        if channel and channel != 'all':
            conditions.append("channel_destination = :channel")
            params["channel"] = channel

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        rows = db.execute(text(f"""
            SELECT id, conversation_id, content, channel_destination, recipient_id,
                   delivery_status, delivery_attempts, ticket_reference, priority, created_at
            FROM outbound_messages {where}
            ORDER BY created_at DESC
            LIMIT :limit
        """), params).fetchall()

        return {
            "outbound_messages": [
                {
                    "id": str(r.id),
                    "conversation_id": r.conversation_id,
                    "content": r.content[:200] if r.content else "",
                    "channel": r.channel_destination,
                    "recipient_id": r.recipient_id,
                    "delivery_status": r.delivery_status,
                    "delivery_attempts": r.delivery_attempts,
                    "ticket_reference": r.ticket_reference,
                    "priority": r.priority,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ],
            "total": len(rows),
        }
    finally:
        db.close()


# ── Delivery Logs ──────────────────────────────────────────────────
@app.get("/api/delivery-logs")
def list_delivery_logs(limit: int = 50):
    db = SessionLocal()
    try:
        rows = db.execute(text("""
            SELECT id, outbound_message_id, attempt_number, channel, delivery_method,
                   status_code, success, error_message, rate_limit_hit, processing_time_ms, created_at
            FROM delivery_logs
            ORDER BY created_at DESC
            LIMIT :limit
        """), {"limit": limit}).fetchall()

        return {
            "delivery_logs": [
                {
                    "id": str(r.id),
                    "outbound_message_id": r.outbound_message_id,
                    "attempt_number": r.attempt_number,
                    "channel": r.channel,
                    "method": r.delivery_method,
                    "status_code": r.status_code,
                    "success": r.success,
                    "error_message": r.error_message,
                    "rate_limit_hit": r.rate_limit_hit,
                    "processing_time_ms": r.processing_time_ms,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ],
            "total": len(rows),
        }
    finally:
        db.close()


# ── Dashboard Tickets (web form) ───────────────────────────────────
@app.get("/api/tickets")
def list_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, le=200),
):
    db = SessionLocal()
    try:
        q = db.query(DashboardTicket).order_by(desc(DashboardTicket.created_at))
        if status and status != 'all':
            q = q.filter(DashboardTicket.status == status)
        if priority and priority != 'all':
            q = q.filter(DashboardTicket.priority == priority)
        if search:
            pattern = f"%{search}%"
            q = q.filter(
                (DashboardTicket.subject.ilike(pattern)) |
                (DashboardTicket.customer_name.ilike(pattern)) |
                (DashboardTicket.ticket_ref.ilike(pattern))
            )

        total = q.count()
        tickets = q.limit(limit).all()

        return {
            "tickets": [
                {
                    "id": str(t.id),
                    "ticket_ref": t.ticket_ref,
                    "customer_name": t.customer_name,
                    "customer_email": t.customer_email,
                    "subject": t.subject,
                    "description": t.description,
                    "category": t.category,
                    "status": t.status,
                    "priority": t.priority,
                    "channel": t.channel,
                    "assigned_agent": t.assigned_agent or "AI Agent",
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "updated_at": t.updated_at.isoformat() if t.updated_at else None,
                    "resolved_at": t.resolved_at.isoformat() if t.resolved_at else None,
                }
                for t in tickets
            ],
            "total": total,
        }
    finally:
        db.close()


@app.get("/api/tickets/{ticket_ref}")
def get_ticket(ticket_ref: str):
    db = SessionLocal()
    try:
        ticket = db.query(DashboardTicket).filter(DashboardTicket.ticket_ref == ticket_ref).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        messages = db.query(DashboardMessage).filter(
            DashboardMessage.ticket_ref == ticket_ref
        ).order_by(DashboardMessage.sent_at).all()

        return {
            "id": str(ticket.id),
            "ticket_ref": ticket.ticket_ref,
            "customer_name": ticket.customer_name,
            "customer_email": ticket.customer_email,
            "subject": ticket.subject,
            "description": ticket.description,
            "category": ticket.category,
            "status": ticket.status,
            "priority": ticket.priority,
            "channel": ticket.channel,
            "assigned_agent": ticket.assigned_agent,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
            "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
            "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None,
            "messages": [
                {
                    "id": str(m.id),
                    "sender_type": m.sender_type,
                    "sender_name": m.sender_name,
                    "content": m.content,
                    "direction": m.direction,
                    "channel": m.channel,
                    "sent_at": m.sent_at.isoformat() if m.sent_at else None,
                }
                for m in messages
            ],
        }
    finally:
        db.close()


@app.patch("/api/tickets/{ticket_ref}")
def update_ticket(ticket_ref: str, body: TicketUpdateRequest):
    db = SessionLocal()
    try:
        ticket = db.query(DashboardTicket).filter(DashboardTicket.ticket_ref == ticket_ref).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        if body.status:
            ticket.status = body.status
            if body.status in ('resolved', 'closed'):
                ticket.resolved_at = datetime.now(timezone.utc)
        if body.priority:
            ticket.priority = body.priority
        if body.assigned_agent:
            ticket.assigned_agent = body.assigned_agent
        ticket.updated_at = datetime.now(timezone.utc)
        db.commit()
        return {"message": "Ticket updated", "ticket_ref": ticket.ticket_ref}
    finally:
        db.close()


# ── Email Sending via Gmail SMTP ────────────────────────────────────
GMAIL_SENDER = os.getenv("GMAIL_SENDER_EMAIL", "pakmonsters@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "hwym hyhf mqvf lmgq")


def send_email_to_customer(to_email: str, customer_name: str, ticket_ref: str,
                           subject: str, category: str, original_message: str):
    """Send email response to customer via Gmail SMTP (runs in background thread)."""
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = f"CRM Digital FTE Support <{GMAIL_SENDER}>"
        msg['To'] = to_email
        msg['Subject'] = f"Support Ticket {ticket_ref} - {subject}"

        # Plain text version
        text_body = f"""Dear {customer_name},

Thank you for contacting our support team!

Your support request has been received and assigned Ticket ID: {ticket_ref}

Ticket Details:
- Subject: {subject}
- Category: {category}
- Status: Open
- Assigned To: AI Agent

Your Message:
{original_message}

Our AI-powered support team is actively reviewing your request and will respond shortly.
You can track your ticket status using Ticket ID: {ticket_ref}

Best regards,
CRM Digital FTE Support Team
Powered by AI Customer Success Agent
"""

        # HTML version
        html_body = f"""
<html>
<body style="font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6f9; margin: 0; padding: 20px;">
<div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.08);">

  <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
    <h1 style="color: white; margin: 0; font-size: 22px;">CRM Digital FTE Support</h1>
    <p style="color: rgba(255,255,255,0.85); margin: 8px 0 0;">AI-Powered Customer Success</p>
  </div>

  <div style="padding: 30px;">
    <p style="color: #374151; font-size: 16px;">Dear <strong>{customer_name}</strong>,</p>

    <p style="color: #374151;">Thank you for contacting our support team! Your request has been received and is being processed by our AI-powered system.</p>

    <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center;">
      <p style="color: #166534; font-size: 13px; margin: 0 0 6px;">YOUR TICKET ID</p>
      <p style="color: #166534; font-size: 24px; font-weight: 700; margin: 0; letter-spacing: 2px;">{ticket_ref}</p>
      <p style="color: #16a34a; font-size: 12px; margin: 6px 0 0;">Save this ID to track your request</p>
    </div>

    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
      <tr>
        <td style="padding: 10px 12px; background: #f9fafb; border: 1px solid #e5e7eb; font-weight: 600; color: #374151; width: 35%;">Subject</td>
        <td style="padding: 10px 12px; border: 1px solid #e5e7eb; color: #4b5563;">{subject}</td>
      </tr>
      <tr>
        <td style="padding: 10px 12px; background: #f9fafb; border: 1px solid #e5e7eb; font-weight: 600; color: #374151;">Category</td>
        <td style="padding: 10px 12px; border: 1px solid #e5e7eb; color: #4b5563;">{category.replace('_', ' ').title()}</td>
      </tr>
      <tr>
        <td style="padding: 10px 12px; background: #f9fafb; border: 1px solid #e5e7eb; font-weight: 600; color: #374151;">Status</td>
        <td style="padding: 10px 12px; border: 1px solid #e5e7eb;"><span style="background: #dbeafe; color: #1d4ed8; padding: 3px 10px; border-radius: 12px; font-size: 13px;">Open</span></td>
      </tr>
      <tr>
        <td style="padding: 10px 12px; background: #f9fafb; border: 1px solid #e5e7eb; font-weight: 600; color: #374151;">Assigned To</td>
        <td style="padding: 10px 12px; border: 1px solid #e5e7eb; color: #4b5563;">AI Agent</td>
      </tr>
    </table>

    <div style="background: #f9fafb; border-radius: 8px; padding: 16px; margin: 20px 0;">
      <p style="font-weight: 600; color: #374151; margin: 0 0 8px;">Your Message:</p>
      <p style="color: #6b7280; margin: 0; line-height: 1.6;">{original_message}</p>
    </div>

    <p style="color: #374151;">Our AI-powered support team is actively reviewing your request and will respond shortly.</p>
  </div>

  <div style="background: #f9fafb; padding: 20px 30px; border-top: 1px solid #e5e7eb; text-align: center;">
    <p style="color: #9ca3af; font-size: 12px; margin: 0;">CRM Digital FTE Factory | AI Customer Success Agent</p>
    <p style="color: #9ca3af; font-size: 11px; margin: 4px 0 0;">This is an automated response. Our team will follow up shortly.</p>
  </div>
</div>
</body>
</html>
"""

        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        # Send via Gmail SMTP
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.send_message(msg)

        print(f"[EMAIL] Sent confirmation email to {to_email} for ticket {ticket_ref}", flush=True)
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send email to {to_email}: {e}", flush=True)


# ── Support Form Submit ─────────────────────────────────────────────
@app.post("/support/submit")
def submit_support_form(body: SupportFormRequest):
    db = SessionLocal()
    try:
        ticket_ref = f"TKT-{str(uuid.uuid4())[:8].upper()}"
        ticket = DashboardTicket(
            id=uuid.uuid4(),
            ticket_ref=ticket_ref,
            customer_name=body.name,
            customer_email=body.email,
            subject=body.subject,
            description=body.message,
            category=body.category,
            status='open',
            priority='medium',
            channel='webform',
            assigned_agent='AI Agent',
        )
        db.add(ticket)
        db.flush()

        # Customer message
        msg1 = DashboardMessage(
            id=uuid.uuid4(),
            ticket_ref=ticket_ref,
            sender_type='customer',
            sender_name=body.name,
            content=body.message,
            direction='inbound',
            channel='webform',
        )
        db.add(msg1)

        # AI auto-response
        auto_response = f"Thank you {body.name}! Your {body.category} request has been received (Ticket: {ticket_ref}). Our AI-powered team is reviewing it and will respond shortly."
        msg2 = DashboardMessage(
            id=uuid.uuid4(),
            ticket_ref=ticket_ref,
            sender_type='agent',
            sender_name='AI Agent',
            content=auto_response,
            direction='outbound',
            channel='webform',
        )
        db.add(msg2)
        db.commit()

        # Send email confirmation to customer in background thread
        email_thread = threading.Thread(
            target=send_email_to_customer,
            args=(body.email, body.name, ticket_ref, body.subject,
                  body.category, body.message),
            daemon=True,
        )
        email_thread.start()

        return {"ticket_id": ticket_ref, "message": auto_response, "status": "open",
                "email_sent_to": body.email}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ── Email Inbound (simulates email channel) ─────────────────────────
class EmailInboundRequest(BaseModel):
    email: str
    name: str
    subject: str = "Support Request"
    message: str


@app.post("/channel/email")
def handle_email_inbound(body: EmailInboundRequest):
    """Handle inbound email - process with AI and send email response back."""
    db = SessionLocal()
    try:
        ticket_ref = f"TKT-{str(uuid.uuid4())[:8].upper()}"
        ticket = DashboardTicket(
            id=uuid.uuid4(),
            ticket_ref=ticket_ref,
            customer_name=body.name,
            customer_email=body.email,
            subject=body.subject,
            description=body.message,
            category='general',
            status='open',
            priority='medium',
            channel='email',
            assigned_agent='AI Agent',
        )
        db.add(ticket)
        db.flush()

        # Customer inbound message
        db.add(DashboardMessage(
            id=uuid.uuid4(), ticket_ref=ticket_ref,
            sender_type='customer', sender_name=body.name,
            content=body.message, direction='inbound', channel='email',
        ))

        # AI response
        ai_response = (
            f"Dear {body.name},\n\n"
            f"Thank you for reaching out via email. We have received your inquiry regarding \"{body.subject}\".\n\n"
            f"Your support ticket {ticket_ref} has been created and assigned to our AI agent for immediate processing.\n\n"
            f"We will analyze your request and provide a detailed response shortly.\n\n"
            f"Best regards,\nCRM Digital FTE Support Team"
        )
        db.add(DashboardMessage(
            id=uuid.uuid4(), ticket_ref=ticket_ref,
            sender_type='agent', sender_name='AI Agent',
            content=ai_response, direction='outbound', channel='email',
        ))
        db.commit()

        # Send actual email response
        email_thread = threading.Thread(
            target=send_email_to_customer,
            args=(body.email, body.name, ticket_ref, body.subject,
                  'general', body.message),
            daemon=True,
        )
        email_thread.start()

        return {
            "success": True,
            "channel": "email",
            "ticket_id": ticket_ref,
            "response": ai_response,
            "email_sent_to": body.email,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ── WhatsApp Inbound ─────────────────────────────────────────────────
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
META_API_URL = "https://graph.facebook.com/v21.0"


def send_whatsapp_response(phone: str, message_body: str, ticket_ref: str):
    """Send WhatsApp message via Meta Cloud API (runs in background thread)."""
    import httpx
    clean_phone = phone.replace('whatsapp:', '').replace('+', '').strip()
    try:
        url = f"{META_API_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_phone,
            "type": "text",
            "text": {"preview_url": False, "body": message_body}
        }
        with httpx.Client(timeout=30) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                print(f"[WHATSAPP] Sent response to +{clean_phone} for {ticket_ref}", flush=True)
            else:
                print(f"[WHATSAPP] Meta API error {resp.status_code}: {resp.text}", flush=True)
    except Exception as e:
        print(f"[WHATSAPP ERROR] Failed to send to +{clean_phone}: {e}", flush=True)


class WhatsAppInboundRequest(BaseModel):
    phone: str
    name: str
    message: str


@app.post("/channel/whatsapp")
def handle_whatsapp_inbound(body: WhatsAppInboundRequest):
    """Handle inbound WhatsApp - process and send WhatsApp response back."""
    db = SessionLocal()
    try:
        ticket_ref = f"TKT-{str(uuid.uuid4())[:8].upper()}"
        ticket = DashboardTicket(
            id=uuid.uuid4(),
            ticket_ref=ticket_ref,
            customer_name=body.name,
            customer_email=f"{body.phone}@whatsapp",
            subject=f"WhatsApp: {body.message[:50]}",
            description=body.message,
            category='general',
            status='open',
            priority='medium',
            channel='whatsapp',
            assigned_agent='AI Agent',
        )
        db.add(ticket)
        db.flush()

        # Customer inbound
        db.add(DashboardMessage(
            id=uuid.uuid4(), ticket_ref=ticket_ref,
            sender_type='customer', sender_name=body.name,
            content=body.message, direction='inbound', channel='whatsapp',
        ))

        # AI response for WhatsApp
        ai_response = (
            f"Hi {body.name}! 👋\n\n"
            f"Thank you for contacting CRM Digital FTE Support via WhatsApp.\n\n"
            f"Your ticket *{ticket_ref}* has been created.\n\n"
            f"We've received your message:\n_{body.message}_\n\n"
            f"Our AI agent is processing your request and will respond shortly. "
            f"You can reference ticket *{ticket_ref}* for follow-ups."
        )
        db.add(DashboardMessage(
            id=uuid.uuid4(), ticket_ref=ticket_ref,
            sender_type='agent', sender_name='AI Agent',
            content=ai_response, direction='outbound', channel='whatsapp',
        ))
        db.commit()

        # Send WhatsApp response via Meta API
        wa_thread = threading.Thread(
            target=send_whatsapp_response,
            args=(body.phone, ai_response, ticket_ref),
            daemon=True,
        )
        wa_thread.start()

        return {
            "success": True,
            "channel": "whatsapp",
            "ticket_id": ticket_ref,
            "response": ai_response,
            "whatsapp_sent_to": body.phone,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ── Meta WhatsApp Webhook (for real 2-way WhatsApp) ──────────────────
WEBHOOK_VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "crm_fte_webhook_2026")


@app.get("/webhook")
def verify_webhook(mode: str = Query(None, alias="hub.mode"),
                   token: str = Query(None, alias="hub.verify_token"),
                   challenge: str = Query(None, alias="hub.challenge")):
    """Meta webhook verification endpoint."""
    if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
        print(f"[WEBHOOK] Verified successfully!", flush=True)
        return int(challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def receive_webhook(request_body: dict):
    """Receive incoming WhatsApp messages from Meta webhook."""
    try:
        print(f"[WEBHOOK] Received: {request_body}", flush=True)

        entry = request_body.get("entry", [])
        for e in entry:
            changes = e.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])
                contacts = value.get("contacts", [])

                for msg in messages:
                    if msg.get("type") != "text":
                        continue

                    phone = msg.get("from", "")
                    text_body = msg.get("text", {}).get("body", "")

                    # Get contact name
                    sender_name = "WhatsApp User"
                    for c in contacts:
                        if c.get("wa_id") == phone:
                            sender_name = c.get("profile", {}).get("name", sender_name)
                            break

                    print(f"[WEBHOOK] Message from +{phone} ({sender_name}): {text_body}", flush=True)

                    # Process like normal WhatsApp inbound
                    db = SessionLocal()
                    try:
                        ticket_ref = f"TKT-{str(uuid.uuid4())[:8].upper()}"
                        ticket = DashboardTicket(
                            id=uuid.uuid4(),
                            ticket_ref=ticket_ref,
                            customer_name=sender_name,
                            customer_email=f"+{phone}@whatsapp",
                            subject=f"WhatsApp: {text_body[:50]}",
                            description=text_body,
                            category='general',
                            status='open',
                            priority='medium',
                            channel='whatsapp',
                            assigned_agent='AI Agent',
                        )
                        db.add(ticket)
                        db.flush()

                        db.add(DashboardMessage(
                            id=uuid.uuid4(), ticket_ref=ticket_ref,
                            sender_type='customer', sender_name=sender_name,
                            content=text_body, direction='inbound', channel='whatsapp',
                        ))

                        ai_response = (
                            f"Hi {sender_name}!\n\n"
                            f"Thank you for contacting CRM Digital FTE Support.\n\n"
                            f"Your ticket *{ticket_ref}* has been created.\n\n"
                            f"Your message: _{text_body}_\n\n"
                            f"Our AI agent is processing your request and will respond shortly."
                        )
                        db.add(DashboardMessage(
                            id=uuid.uuid4(), ticket_ref=ticket_ref,
                            sender_type='agent', sender_name='AI Agent',
                            content=ai_response, direction='outbound', channel='whatsapp',
                        ))
                        db.commit()

                        # Send reply via Meta API
                        wa_thread = threading.Thread(
                            target=send_whatsapp_response,
                            args=(phone, ai_response, ticket_ref),
                            daemon=True,
                        )
                        wa_thread.start()

                        print(f"[WEBHOOK] Ticket {ticket_ref} created, reply sent to +{phone}", flush=True)
                    except Exception as ex:
                        db.rollback()
                        print(f"[WEBHOOK ERROR] DB error: {ex}", flush=True)
                    finally:
                        db.close()

        return {"status": "ok"}
    except Exception as e:
        print(f"[WEBHOOK ERROR] {e}", flush=True)
        return {"status": "ok"}


@app.get("/support/ticket/{ticket_ref}")
def get_support_ticket_status(ticket_ref: str):
    db = SessionLocal()
    try:
        ticket = db.query(DashboardTicket).filter(DashboardTicket.ticket_ref == ticket_ref).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        last_msg = db.query(DashboardMessage).filter(
            DashboardMessage.ticket_ref == ticket_ref,
            DashboardMessage.sender_type == 'agent'
        ).order_by(desc(DashboardMessage.sent_at)).first()

        return {
            "ticket_id": ticket.ticket_ref,
            "status": ticket.status,
            "subject": ticket.subject,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
            "ai_response": last_msg.content if last_msg else None,
        }
    finally:
        db.close()


# ── Customers (derived from agent_messages) ─────────────────────────
@app.get("/api/customers")
def list_customers(search: Optional[str] = None, limit: int = 50):
    db = SessionLocal()
    try:
        rows = db.execute(text("""
            SELECT customer_id,
                   COUNT(*) as total_messages,
                   COUNT(DISTINCT conversation_id) as total_conversations,
                   MIN(timestamp) as first_seen,
                   MAX(timestamp) as last_active,
                   BOOL_OR(escalation_flag) as has_escalation
            FROM agent_messages
            GROUP BY customer_id
            ORDER BY MAX(timestamp) DESC
            LIMIT :limit
        """), {"limit": limit}).fetchall()

        customers = []
        for r in rows:
            cid = r.customer_id or ""
            if search and search.lower() not in cid.lower():
                continue
            customers.append({
                "id": cid,
                "name": _extract_name(cid),
                "email": cid if "@" in cid else "",
                "phone": _extract_phone(cid),
                "channel": _extract_channel(cid),
                "total_messages": r.total_messages,
                "total_conversations": r.total_conversations,
                "first_seen": r.first_seen.isoformat() if r.first_seen else None,
                "last_active": r.last_active.isoformat() if r.last_active else None,
                "has_escalation": r.has_escalation or False,
            })

        return {"customers": customers, "total": len(customers)}
    finally:
        db.close()


# ── Helpers ─────────────────────────────────────────────────────────
def _extract_channel(customer_id: str) -> str:
    if not customer_id:
        return "unknown"
    if "whatsapp" in customer_id.lower():
        return "whatsapp"
    if "@" in customer_id:
        return "email"
    return "webform"


def _extract_name(customer_id: str) -> str:
    if not customer_id:
        return "Unknown"
    if "whatsapp:" in customer_id:
        phone = customer_id.split(":")[-1]
        return f"WhatsApp {phone[-4:]}"
    if "mock-whatsapp:" in customer_id:
        phone = customer_id.split(":")[-1]
        return f"WhatsApp {phone[-4:]}"
    if "@" in customer_id:
        parts = customer_id.replace("mock-", "").split("@")
        return parts[0].replace(".", " ").replace("_", " ").title()
    return customer_id[:20]


def _extract_phone(customer_id: str) -> str:
    if "whatsapp:" in customer_id or "mock-whatsapp:" in customer_id:
        return customer_id.split(":")[-1]
    return ""


# ── Gmail IMAP Poller (2-way email) ─────────────────────────────────
PROCESSED_EMAIL_IDS = set()


def decode_mime_header(header_val):
    """Decode MIME encoded header value."""
    if not header_val:
        return ""
    decoded_parts = decode_header(header_val)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or 'utf-8', errors='replace'))
        else:
            result.append(part)
    return " ".join(result)


def get_email_body(msg):
    """Extract plain text body from email message."""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or 'utf-8'
                    return payload.decode(charset, errors='replace')
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or 'utf-8'
            return payload.decode(charset, errors='replace')
    return ""


def process_incoming_email(from_email: str, sender_name: str, subject: str, body: str, msg_id: str):
    """Process an incoming email and send auto-reply."""
    # Skip our own sent emails
    if GMAIL_SENDER.lower() in from_email.lower():
        return
    # Skip already processed
    if msg_id in PROCESSED_EMAIL_IDS:
        return
    PROCESSED_EMAIL_IDS.add(msg_id)

    print(f"[EMAIL POLLER] New email from {from_email} ({sender_name}): {subject}".encode('ascii', 'replace').decode(), flush=True)

    db = SessionLocal()
    try:
        ticket_ref = f"TKT-{str(uuid.uuid4())[:8].upper()}"
        ticket = DashboardTicket(
            id=uuid.uuid4(),
            ticket_ref=ticket_ref,
            customer_name=sender_name,
            customer_email=from_email,
            subject=subject,
            description=body[:2000],
            category='general',
            status='open',
            priority='medium',
            channel='email',
            assigned_agent='AI Agent',
        )
        db.add(ticket)
        db.flush()

        db.add(DashboardMessage(
            id=uuid.uuid4(), ticket_ref=ticket_ref,
            sender_type='customer', sender_name=sender_name,
            content=body[:2000], direction='inbound', channel='email',
        ))

        ai_response = (
            f"Dear {sender_name},\n\n"
            f"Thank you for your email regarding \"{subject}\".\n\n"
            f"Your support ticket {ticket_ref} has been created and assigned to our AI agent.\n\n"
            f"We will review your request and respond with a detailed solution shortly.\n\n"
            f"Best regards,\nCRM Digital FTE Support Team"
        )
        db.add(DashboardMessage(
            id=uuid.uuid4(), ticket_ref=ticket_ref,
            sender_type='agent', sender_name='AI Agent',
            content=ai_response, direction='outbound', channel='email',
        ))
        db.commit()

        # Send reply email
        send_email_to_customer(from_email, sender_name, ticket_ref, subject, 'general', body[:500])

        print(f"[EMAIL POLLER] Ticket {ticket_ref} created, reply sent to {from_email}", flush=True)
    except Exception as e:
        db.rollback()
        print(f"[EMAIL POLLER ERROR] DB error: {e}", flush=True)
    finally:
        db.close()


def email_poll_loop():
    """Background thread: poll Gmail inbox via IMAP every 15 seconds."""
    print("[EMAIL POLLER] Starting Gmail IMAP poller...", flush=True)
    time.sleep(5)  # Initial delay

    while True:
        try:
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            mail.select('INBOX')

            # Search for unread emails
            status, messages = mail.search(None, 'UNSEEN')
            if status == 'OK' and messages[0]:
                email_ids = messages[0].split()
                for eid in email_ids[-5:]:  # Process last 5 unread
                    status, msg_data = mail.fetch(eid, '(RFC822)')
                    if status != 'OK':
                        continue

                    raw_email = msg_data[0][1]
                    msg = email_lib.message_from_bytes(raw_email)

                    msg_id = msg.get('Message-ID', str(eid))
                    from_header = decode_mime_header(msg.get('From', ''))
                    subject = decode_mime_header(msg.get('Subject', 'No Subject'))
                    body = get_email_body(msg)

                    # Parse sender name and email
                    if '<' in from_header and '>' in from_header:
                        sender_name = from_header.split('<')[0].strip().strip('"')
                        from_email = from_header.split('<')[1].split('>')[0]
                    else:
                        sender_name = from_header.split('@')[0]
                        from_email = from_header.strip()

                    if not sender_name:
                        sender_name = from_email.split('@')[0]

                    # Skip our own emails, system emails, newsletters, noreply
                    skip_patterns = [
                        GMAIL_SENDER.lower(), 'noreply', 'no-reply', 'mailer-daemon',
                        'newsletter', 'announce', 'marketing', 'promo', 'digest',
                        'notify', 'notification', 'updates@', 'info@', 'team@',
                        'webinar', 'learn.', 'docker.com', 'fiverr', 'heygen',
                        'accounts.google', 'security-noreply',
                    ]
                    from_lower = from_email.lower()
                    if any(pat in from_lower for pat in skip_patterns):
                        continue

                    try:
                        process_incoming_email(from_email, sender_name, subject, body, msg_id)
                    except Exception as pe:
                        print(f"[EMAIL POLLER ERROR] Processing: {pe}", flush=True)

            mail.logout()
        except Exception as e:
            print(f"[EMAIL POLLER ERROR] {e}", flush=True)

        time.sleep(15)  # Poll every 15 seconds


# ── FastAPI Startup Event ──────────────────────────────────────────
@app.on_event("startup")
def start_email_poller():
    """Start email poller background thread on API startup."""
    poller_thread = threading.Thread(target=email_poll_loop, daemon=True)
    poller_thread.start()
    print("[STARTUP] Email poller thread started", flush=True)


# ── Run ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("Starting CRM Dashboard API on http://localhost:8002")
    uvicorn.run(app, host="0.0.0.0", port=8002)
