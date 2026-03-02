#!/bin/bash

echo "============================================"
echo "  CRM Digital FTE Factory"
echo "  Starting on HuggingFace Spaces..."
echo "============================================"

# Set defaults for optional env vars
export GMAIL_SENDER_EMAIL="${GMAIL_SENDER_EMAIL:-}"
export GMAIL_APP_PASSWORD="${GMAIL_APP_PASSWORD:-}"
export WHATSAPP_PHONE_NUMBER_ID="${WHATSAPP_PHONE_NUMBER_ID:-}"
export WHATSAPP_ACCESS_TOKEN="${WHATSAPP_ACCESS_TOKEN:-}"
export WHATSAPP_VERIFY_TOKEN="${WHATSAPP_VERIFY_TOKEN:-}"

# Create log directory
mkdir -p /var/log/supervisor

echo "[INFO] DATABASE_URL configured: $(echo $DATABASE_URL | sed 's/:.*@/:***@/')"
echo "[INFO] Starting services via supervisor..."

# Start all services
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
