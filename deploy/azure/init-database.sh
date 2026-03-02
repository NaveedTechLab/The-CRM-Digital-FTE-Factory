#!/bin/bash
set -euo pipefail

###############################################################################
# Initialize Azure PostgreSQL Flexible Server with CRM schema
# - Enables pgvector extension
# - Runs 01-init-db.sql schema creation
# - Seeds knowledge base with sample data
###############################################################################

RESOURCE_GROUP="rg-customer-success-fte"
PG_SERVER="pg-fte-server"
PG_DB="crm_db"
PG_ADMIN_USER="fteadmin"
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SQL_FILE="${PROJECT_ROOT}/phase-2-core-infrastructure-database/postgresql/init-scripts/01-init-db.sql"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ── Pre-flight ───────────────────────────────────────────────────────────────
command -v psql >/dev/null 2>&1 || error "psql not found. Install: apt-get install postgresql-client"

[ -f "$SQL_FILE" ] || error "SQL file not found: $SQL_FILE"

# Get PostgreSQL FQDN
PG_FQDN=$(az postgres flexible-server show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$PG_SERVER" \
    --query fullyQualifiedDomainName -o tsv)
info "PostgreSQL FQDN: $PG_FQDN"

# Prompt for password if not set
if [ -z "${PG_PASSWORD:-}" ]; then
    # Try to get from Key Vault first
    PG_PASSWORD=$(az keyvault secret show \
        --vault-name kv-fte-secrets \
        --name pg-password \
        --query value -o tsv 2>/dev/null || true)

    if [ -z "$PG_PASSWORD" ]; then
        read -sp "Enter PostgreSQL admin password: " PG_PASSWORD
        echo
    else
        info "Password retrieved from Key Vault"
    fi
fi

export PGPASSWORD="$PG_PASSWORD"

# ── Allow current IP through firewall (temporarily) ─────────────────────────
MY_IP=$(curl -s https://ifconfig.me)
info "Adding temporary firewall rule for current IP: $MY_IP..."
az postgres flexible-server firewall-rule create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$PG_SERVER" \
    --rule-name "TempInitRule-$(date +%s)" \
    --start-ip-address "$MY_IP" \
    --end-ip-address "$MY_IP" 2>/dev/null || warn "Firewall rule may already exist"

# ── Step 1: Enable pgvector ─────────────────────────────────────────────────
info "Enabling pgvector extension..."
psql "host=${PG_FQDN} port=5432 dbname=${PG_DB} user=${PG_ADMIN_USER} sslmode=require" \
    -c "CREATE EXTENSION IF NOT EXISTS vector;" || warn "pgvector may already be enabled"

# ── Step 2: Run schema creation ─────────────────────────────────────────────
info "Running schema creation from: $SQL_FILE"
psql "host=${PG_FQDN} port=5432 dbname=${PG_DB} user=${PG_ADMIN_USER} sslmode=require" \
    -f "$SQL_FILE"

# ── Step 3: Seed knowledge base ─────────────────────────────────────────────
info "Seeding knowledge base with sample data..."
psql "host=${PG_FQDN} port=5432 dbname=${PG_DB} user=${PG_ADMIN_USER} sslmode=require" <<'SEED_SQL'
INSERT INTO knowledge_base (title, content, category, tags, status, author) VALUES
('Getting Started', 'Welcome to our platform. Here is how to get started with your account setup and first steps.', 'general', ARRAY['onboarding', 'setup'], 'published', 'system'),
('Password Reset Guide', 'To reset your password: 1. Go to login page 2. Click Forgot Password 3. Enter your email 4. Check inbox for reset link 5. Create new password (min 8 chars, mixed case + digits).', 'troubleshooting', ARRAY['password', 'login', 'security'], 'published', 'system'),
('Billing FAQ', 'Our billing cycle runs monthly. You can view invoices in Settings > Billing. Accepted payment methods: credit card, PayPal, bank transfer. Contact support for refund requests within 30 days.', 'billing', ARRAY['payment', 'invoice', 'refund'], 'published', 'system'),
('API Rate Limits', 'API rate limits: Free tier 100 req/min, Pro tier 1000 req/min, Enterprise unlimited. Rate limit headers included in all responses. Contact sales for custom limits.', 'product', ARRAY['api', 'limits', 'technical'], 'published', 'system'),
('Data Privacy Policy', 'We comply with GDPR and CCPA. Your data is encrypted at rest and in transit. Data retention: 90 days for logs, 2 years for account data. Request data export or deletion via Settings > Privacy.', 'policy', ARRAY['privacy', 'gdpr', 'security'], 'published', 'system'),
('Escalation Process', 'Support tickets are auto-triaged by AI. Escalation triggers: critical priority, unresolved after 24h, customer request. Escalated tickets go to human agents with full context.', 'faq', ARRAY['escalation', 'support', 'sla'], 'published', 'system')
ON CONFLICT DO NOTHING;
SEED_SQL

# ── Step 4: Create Phase 4/5 tables if not present ──────────────────────────
info "Ensuring Phase 4/5 tables exist..."
psql "host=${PG_FQDN} port=5432 dbname=${PG_DB} user=${PG_ADMIN_USER} sslmode=require" <<'PHASE_SQL'
-- Agent messages table (Phase 4)
CREATE TABLE IF NOT EXISTS agent_messages (
    id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(255),
    channel VARCHAR(50),
    sender_name VARCHAR(255),
    sender_id VARCHAR(255),
    message_text TEXT,
    agent_response TEXT,
    confidence_score FLOAT,
    intent VARCHAR(100),
    status VARCHAR(50) DEFAULT 'processed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Outbound messages table (Phase 5)
CREATE TABLE IF NOT EXISTS outbound_messages (
    id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(255),
    channel VARCHAR(50),
    recipient_id VARCHAR(255),
    message_text TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    delivery_attempts INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Delivery logs table (Phase 5)
CREATE TABLE IF NOT EXISTS delivery_logs (
    id SERIAL PRIMARY KEY,
    outbound_message_id INTEGER REFERENCES outbound_messages(id),
    channel VARCHAR(50),
    status VARCHAR(50),
    response_code INTEGER,
    response_body TEXT,
    latency_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Retry queue table (Phase 5)
CREATE TABLE IF NOT EXISTS retry_queue (
    id SERIAL PRIMARY KEY,
    outbound_message_id INTEGER REFERENCES outbound_messages(id),
    retry_count INTEGER DEFAULT 0,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    max_retries INTEGER DEFAULT 3,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Dashboard tickets table
CREATE TABLE IF NOT EXISTS dashboard_tickets (
    id SERIAL PRIMARY KEY,
    reference VARCHAR(255) UNIQUE,
    customer_name VARCHAR(255),
    customer_email VARCHAR(320),
    customer_phone VARCHAR(20),
    channel VARCHAR(50),
    category VARCHAR(100),
    subject VARCHAR(500),
    description TEXT,
    status VARCHAR(50) DEFAULT 'open',
    priority VARCHAR(50) DEFAULT 'medium',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Dashboard messages table
CREATE TABLE IF NOT EXISTS dashboard_messages (
    id SERIAL PRIMARY KEY,
    ticket_reference VARCHAR(255),
    sender_type VARCHAR(50),
    content TEXT,
    channel VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_agent_messages_conversation ON agent_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_agent_messages_channel ON agent_messages(channel);
CREATE INDEX IF NOT EXISTS idx_outbound_messages_conversation ON outbound_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_outbound_messages_status ON outbound_messages(status);
CREATE INDEX IF NOT EXISTS idx_delivery_logs_outbound ON delivery_logs(outbound_message_id);
CREATE INDEX IF NOT EXISTS idx_retry_queue_next ON retry_queue(next_retry_at);
CREATE INDEX IF NOT EXISTS idx_dashboard_tickets_ref ON dashboard_tickets(reference);
CREATE INDEX IF NOT EXISTS idx_dashboard_tickets_status ON dashboard_tickets(status);
PHASE_SQL

# ── Step 5: Verify ──────────────────────────────────────────────────────────
info "Verifying database tables..."
TABLE_COUNT=$(psql "host=${PG_FQDN} port=5432 dbname=${PG_DB} user=${PG_ADMIN_USER} sslmode=require" \
    -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")
info "Total tables: $(echo $TABLE_COUNT | tr -d ' ')"

psql "host=${PG_FQDN} port=5432 dbname=${PG_DB} user=${PG_ADMIN_USER} sslmode=require" \
    -c "\dt" 2>/dev/null || true

KB_COUNT=$(psql "host=${PG_FQDN} port=5432 dbname=${PG_DB} user=${PG_ADMIN_USER} sslmode=require" \
    -t -c "SELECT count(*) FROM knowledge_base;" 2>/dev/null || echo "0")
info "Knowledge base entries: $(echo $KB_COUNT | tr -d ' ')"

unset PGPASSWORD

echo ""
echo "============================================================"
info "Database initialization complete!"
echo "============================================================"
echo ""
echo "Next step: ./deploy-to-aks.sh"
