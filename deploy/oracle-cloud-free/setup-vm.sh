#!/bin/bash
set -euo pipefail

###############################################################################
# Oracle Cloud Free Tier VM Setup Script
# Run this ON the VM after SSH-ing in
# Target: Ubuntu 22.04 on ARM (Ampere A1, 4 OCPU, 24GB RAM)
###############################################################################

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

info "=== CRM Digital FTE Factory - VM Setup ==="
info "Target: Oracle Cloud Free Tier ARM VM"
echo ""

# ── Step 1: System updates ──────────────────────────────────────────────────
info "Step 1/6: Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# ── Step 2: Install Docker ──────────────────────────────────────────────────
info "Step 2/6: Installing Docker..."
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker $USER
    info "Docker installed. You may need to log out and back in for group changes."
else
    info "Docker already installed: $(docker --version)"
fi

# ── Step 3: Install Docker Compose ──────────────────────────────────────────
info "Step 3/6: Installing Docker Compose..."
if ! command -v docker-compose &>/dev/null && ! docker compose version &>/dev/null 2>&1; then
    sudo apt-get install -y docker-compose-plugin
    info "Docker Compose plugin installed"
else
    info "Docker Compose already installed"
fi

# ── Step 4: Install Git ─────────────────────────────────────────────────────
info "Step 4/6: Installing Git..."
sudo apt-get install -y git

# ── Step 5: Configure firewall ──────────────────────────────────────────────
info "Step 5/6: Configuring firewall (iptables)..."

# Oracle Cloud uses iptables, not ufw
# Open required ports
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT    # HTTP
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT   # HTTPS
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 3000 -j ACCEPT  # Web Form (direct)
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT  # API (direct)
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8001 -j ACCEPT  # Dispatcher (direct)
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8002 -j ACCEPT  # Dashboard (direct)
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 9090 -j ACCEPT  # Prometheus
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 3001 -j ACCEPT  # Grafana

# Save iptables rules
sudo netfilter-persistent save 2>/dev/null || sudo sh -c "iptables-save > /etc/iptables/rules.v4" 2>/dev/null || warn "Could not persist iptables rules"

info "Firewall configured for ports: 80, 443, 3000, 8000-8002, 3001, 9090"

# ── Step 6: Configure swap (recommended for 24GB RAM) ───────────────────────
info "Step 6/6: Configuring swap space..."
if [ ! -f /swapfile ]; then
    sudo fallocate -l 4G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    info "4GB swap created"
else
    info "Swap already configured"
fi

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo "============================================================"
info "VM setup complete!"
echo "============================================================"
echo ""
echo "System info:"
echo "  CPU:    $(nproc) cores"
echo "  RAM:    $(free -h | awk '/Mem:/ {print $2}')"
echo "  Disk:   $(df -h / | awk 'NR==2 {print $4}') free"
echo "  Docker: $(docker --version 2>/dev/null || echo 'restart session first')"
echo ""
echo "Next steps:"
echo "  1. Clone the repo:"
echo "     git clone <your-repo-url> ~/crm-fte"
echo ""
echo "  2. Create .env file:"
echo "     cd ~/crm-fte/deploy/oracle-cloud-free"
echo "     cp .env.example .env"
echo "     nano .env   # fill in your API keys"
echo ""
echo "  3. Start everything:"
echo "     docker compose up -d --build"
echo ""
echo "  4. Check status:"
echo "     docker compose ps"
echo "     docker compose logs -f"
echo ""
echo "NOTE: If docker commands fail, log out and log back in"
echo "      (for docker group membership to take effect)"
