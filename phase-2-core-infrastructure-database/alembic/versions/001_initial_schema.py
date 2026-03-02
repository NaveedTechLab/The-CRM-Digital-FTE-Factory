"""Initial schema - all tables for CRM Digital FTE

Revision ID: 001
Revises: None
Create Date: 2026-02-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Create customers table
    op.create_table(
        'customers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('external_id', sa.String(255), unique=True, nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(320), unique=True, nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('contact_preferences', JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_interaction', sa.DateTime(timezone=True), nullable=True),
    )

    # Create tickets table
    op.create_table(
        'tickets',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('external_reference', sa.String(255), unique=True, nullable=True),
        sa.Column('subject', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('status', sa.String(50), server_default='open'),
        sa.Column('priority', sa.String(50), server_default='medium'),
        sa.Column('channel', sa.String(50), server_default='webform'),
        sa.Column('assigned_agent', sa.String(255), nullable=True),
        sa.Column('sla_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('ticket_id', UUID(as_uuid=True), sa.ForeignKey('tickets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sender_type', sa.String(50), nullable=False),
        sa.Column('sender_id', sa.String(255), nullable=True),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('content_type', sa.String(50), server_default='text'),
        sa.Column('direction', sa.String(50), nullable=False),
        sa.Column('channel_metadata', JSONB, server_default='{}'),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Create customer_identifiers table
    op.create_table(
        'customer_identifiers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('channel', sa.String(50), nullable=False),
        sa.Column('identifier_value', sa.String(320), nullable=False),
        sa.Column('identifier_type', sa.String(50), nullable=False),
        sa.Column('is_primary', sa.Boolean, server_default='false'),
        sa.Column('verified', sa.Boolean, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('channel', 'identifier_value'),
    )

    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ticket_id', UUID(as_uuid=True), sa.ForeignKey('tickets.id', ondelete='SET NULL'), nullable=True),
        sa.Column('channel', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), server_default='active'),
        sa.Column('subject', sa.String(500), nullable=True),
        sa.Column('thread_id', sa.String(255), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_message_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', JSONB, server_default='{}'),
    )

    # Create knowledge_base table
    op.create_table(
        'knowledge_base',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('tags', sa.ARRAY(sa.Text), server_default='{}'),
        sa.Column('status', sa.String(50), server_default='published'),
        sa.Column('version', sa.Integer, server_default='1'),
        sa.Column('author', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create channel_configs table
    op.create_table(
        'channel_configs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('channel', sa.String(50), unique=True, nullable=False),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('config', JSONB, server_default='{}'),
        sa.Column('rate_limit_per_minute', sa.Integer, server_default='100'),
        sa.Column('webhook_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create agent_metrics table
    op.create_table(
        'agent_metrics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('metric_type', sa.String(100), nullable=False),
        sa.Column('metric_value', sa.Numeric(10, 4), nullable=False),
        sa.Column('channel', sa.String(50), nullable=True),
        sa.Column('ticket_id', UUID(as_uuid=True), sa.ForeignKey('tickets.id', ondelete='SET NULL'), nullable=True),
        sa.Column('conversation_id', UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metadata', JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create vector_embeddings table
    op.create_table(
        'vector_embeddings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_id', sa.String(255), nullable=False),
        sa.Column('content_preview', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    # Note: vector(1536) column and IVFFlat index are created via raw SQL in 01-init-db.sql
    # as Alembic doesn't have native pgvector support


def downgrade() -> None:
    op.drop_table('vector_embeddings')
    op.drop_table('agent_metrics')
    op.drop_table('channel_configs')
    op.drop_table('knowledge_base')
    op.drop_table('conversations')
    op.drop_table('customer_identifiers')
    op.drop_table('messages')
    op.drop_table('tickets')
    op.drop_table('customers')
    op.execute('DROP EXTENSION IF EXISTS vector')
