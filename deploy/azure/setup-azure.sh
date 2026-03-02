#!/bin/bash
set -euo pipefail

###############################################################################
# Azure Resource Provisioning for CRM Digital FTE Factory
# Creates: Resource Group, AKS, ACR, PostgreSQL, Redis, Key Vault
###############################################################################

# ── Configuration ────────────────────────────────────────────────────────────
RESOURCE_GROUP="rg-customer-success-fte"
LOCATION="eastus"
AKS_CLUSTER="aks-fte-cluster"
ACR_NAME="acrftecr"
PG_SERVER="pg-fte-server"
PG_DB="crm_db"
PG_ADMIN_USER="fteadmin"
REDIS_NAME="redis-fte-cache"
KEYVAULT_NAME="kv-fte-secrets"
NODE_COUNT=3
NODE_VM_SIZE="Standard_D2s_v3"

# ── Color output helpers ─────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ── Pre-flight checks ───────────────────────────────────────────────────────
command -v az >/dev/null 2>&1 || error "Azure CLI not found. Install: https://aka.ms/install-azure-cli"

info "Checking Azure login status..."
az account show >/dev/null 2>&1 || { warn "Not logged in. Running az login..."; az login; }

SUBSCRIPTION=$(az account show --query id -o tsv)
info "Using subscription: $SUBSCRIPTION"

# Prompt for PostgreSQL password if not set
if [ -z "${PG_PASSWORD:-}" ]; then
    read -sp "Enter PostgreSQL admin password (min 8 chars, mixed case + digits): " PG_PASSWORD
    echo
fi

# ── Step 1: Resource Group ───────────────────────────────────────────────────
info "Creating Resource Group: $RESOURCE_GROUP in $LOCATION..."
az group create \
    --name "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --tags project=customer-success-fte environment=production

# ── Step 2: Azure Container Registry ────────────────────────────────────────
info "Creating Azure Container Registry: $ACR_NAME..."
az acr create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$ACR_NAME" \
    --sku Basic \
    --admin-enabled true

ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --query loginServer -o tsv)
info "ACR Login Server: $ACR_LOGIN_SERVER"

# ── Step 3: AKS Cluster ─────────────────────────────────────────────────────
info "Creating AKS Cluster: $AKS_CLUSTER ($NODE_COUNT x $NODE_VM_SIZE)..."
az aks create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$AKS_CLUSTER" \
    --node-count "$NODE_COUNT" \
    --node-vm-size "$NODE_VM_SIZE" \
    --enable-managed-identity \
    --attach-acr "$ACR_NAME" \
    --network-plugin azure \
    --generate-ssh-keys \
    --enable-addons monitoring \
    --tags project=customer-success-fte

# Get AKS credentials
info "Fetching AKS credentials..."
az aks get-credentials \
    --resource-group "$RESOURCE_GROUP" \
    --name "$AKS_CLUSTER" \
    --overwrite-existing

# ── Step 4: PostgreSQL Flexible Server ───────────────────────────────────────
info "Creating Azure Database for PostgreSQL Flexible Server: $PG_SERVER..."
az postgres flexible-server create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$PG_SERVER" \
    --location "$LOCATION" \
    --admin-user "$PG_ADMIN_USER" \
    --admin-password "$PG_PASSWORD" \
    --sku-name Standard_B1ms \
    --tier Burstable \
    --storage-size 32 \
    --version 16 \
    --yes

# Allow Azure services to connect
info "Configuring PostgreSQL firewall for Azure services..."
az postgres flexible-server firewall-rule create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$PG_SERVER" \
    --rule-name AllowAzureServices \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 0.0.0.0

# Enable pgvector extension
info "Enabling pgvector extension..."
az postgres flexible-server parameter set \
    --resource-group "$RESOURCE_GROUP" \
    --server-name "$PG_SERVER" \
    --name azure.extensions \
    --value vector

# Create the database
info "Creating database: $PG_DB..."
az postgres flexible-server db create \
    --resource-group "$RESOURCE_GROUP" \
    --server-name "$PG_SERVER" \
    --database-name "$PG_DB"

PG_FQDN=$(az postgres flexible-server show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$PG_SERVER" \
    --query fullyQualifiedDomainName -o tsv)
info "PostgreSQL FQDN: $PG_FQDN"

# ── Step 5: Azure Cache for Redis ───────────────────────────────────────────
info "Creating Azure Cache for Redis: $REDIS_NAME..."
az redis create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$REDIS_NAME" \
    --location "$LOCATION" \
    --sku Basic \
    --vm-size C0 \
    --tags project=customer-success-fte

REDIS_HOST=$(az redis show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$REDIS_NAME" \
    --query hostName -o tsv)
REDIS_KEY=$(az redis list-keys \
    --resource-group "$RESOURCE_GROUP" \
    --name "$REDIS_NAME" \
    --query primaryKey -o tsv)
info "Redis Host: $REDIS_HOST"

# ── Step 6: Azure Key Vault ─────────────────────────────────────────────────
info "Creating Azure Key Vault: $KEYVAULT_NAME..."
az keyvault create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$KEYVAULT_NAME" \
    --location "$LOCATION" \
    --enable-rbac-authorization false

# Store secrets in Key Vault
info "Storing secrets in Key Vault..."
az keyvault secret set --vault-name "$KEYVAULT_NAME" --name "pg-password" --value "$PG_PASSWORD"
az keyvault secret set --vault-name "$KEYVAULT_NAME" --name "pg-connection-string" \
    --value "postgresql://${PG_ADMIN_USER}:${PG_PASSWORD}@${PG_FQDN}:5432/${PG_DB}?sslmode=require"
az keyvault secret set --vault-name "$KEYVAULT_NAME" --name "redis-connection-string" \
    --value "rediss://:${REDIS_KEY}@${REDIS_HOST}:6380/0"

# Prompt for API secrets and store them
echo ""
info "Now storing API credentials in Key Vault..."
echo "  (Leave blank to skip and set later via: az keyvault secret set)"
echo ""

read -p "OpenAI API Key: " OPENAI_KEY
[ -n "$OPENAI_KEY" ] && az keyvault secret set --vault-name "$KEYVAULT_NAME" --name "openai-api-key" --value "$OPENAI_KEY"

read -p "Twilio Account SID: " TWILIO_SID
[ -n "$TWILIO_SID" ] && az keyvault secret set --vault-name "$KEYVAULT_NAME" --name "twilio-account-sid" --value "$TWILIO_SID"

read -p "Twilio Auth Token: " TWILIO_TOKEN
[ -n "$TWILIO_TOKEN" ] && az keyvault secret set --vault-name "$KEYVAULT_NAME" --name "twilio-auth-token" --value "$TWILIO_TOKEN"

read -p "Twilio WhatsApp Number (e.g. whatsapp:+1234567890): " TWILIO_WA
[ -n "$TWILIO_WA" ] && az keyvault secret set --vault-name "$KEYVAULT_NAME" --name "twilio-whatsapp-number" --value "$TWILIO_WA"

read -p "Gmail Sender Email: " GMAIL_EMAIL
[ -n "$GMAIL_EMAIL" ] && az keyvault secret set --vault-name "$KEYVAULT_NAME" --name "gmail-sender-email" --value "$GMAIL_EMAIL"

# ── Step 7: Grant AKS access to Key Vault ───────────────────────────────────
info "Granting AKS managed identity access to Key Vault..."
AKS_IDENTITY=$(az aks show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$AKS_CLUSTER" \
    --query identityProfile.kubeletidentity.objectId -o tsv)

az keyvault set-policy \
    --name "$KEYVAULT_NAME" \
    --object-id "$AKS_IDENTITY" \
    --secret-permissions get list

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo "============================================================"
info "Azure resource provisioning complete!"
echo "============================================================"
echo ""
echo "  Resource Group:  $RESOURCE_GROUP"
echo "  AKS Cluster:     $AKS_CLUSTER ($NODE_COUNT nodes)"
echo "  ACR:             $ACR_LOGIN_SERVER"
echo "  PostgreSQL:      $PG_FQDN"
echo "  Redis:           $REDIS_HOST"
echo "  Key Vault:       $KEYVAULT_NAME"
echo ""
echo "  DATABASE_URL: postgresql://${PG_ADMIN_USER}:***@${PG_FQDN}:5432/${PG_DB}?sslmode=require"
echo "  REDIS_URL:    rediss://***@${REDIS_HOST}:6380/0"
echo ""
echo "Next steps:"
echo "  1. Run: ./init-database.sh   (initialize schema)"
echo "  2. Run: ./build-push.sh      (build & push Docker images)"
echo "  3. Run: ./deploy-to-aks.sh   (deploy to AKS)"
echo ""
