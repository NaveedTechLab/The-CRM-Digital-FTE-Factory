# Oracle Cloud Free Tier Deployment

## CRM Digital FTE Factory - FREE Forever Deployment

### Cost: $0/month (Oracle Cloud Always Free Tier)

### What You Get (Free)

| Resource | Spec | Free? |
|---|---|---|
| ARM VM (Ampere A1) | 4 cores, 24GB RAM, 200GB disk | Forever Free |
| Public IP | 1 static IP | Forever Free |
| Bandwidth | 10 TB/month outbound | Forever Free |
| Load Balancer | 1 instance, 10 Mbps | Forever Free |

### Architecture (Single VM)

```
Oracle Cloud ARM VM (4 cores, 24GB RAM)
├── NGINX (port 80) ─── reverse proxy
├── PostgreSQL + pgvector (port 5432)
├── Redis (port 6379)
├── Zookeeper (port 2181)
├── Kafka (port 9092)
├── fte-api (port 8000) ─── Phase 3 Ingestion
├── fte-worker ─── Phase 4 Agent
├── fte-dispatcher (port 8001) ─── Phase 5 Delivery
├── fte-dashboard (port 8002) ─── Dashboard API
├── fte-web-form (port 3000) ─── Next.js Frontend
├── Prometheus (port 9090)
└── Grafana (port 3001)
```

---

## Step-by-Step Setup

### Step 1: Create Oracle Cloud Account

1. Go to [cloud.oracle.com](https://cloud.oracle.com) and sign up
2. Requires credit card for verification (you will NOT be charged)
3. Select your home region (pick closest to your users)
4. Wait for account activation (~5 minutes)

### Step 2: Create ARM VM (Always Free)

1. Go to **Compute > Instances > Create Instance**
2. Configure:
   - **Name:** `crm-fte-server`
   - **Image:** Ubuntu 22.04 (Canonical)
   - **Shape:** Click "Change Shape" > **Ampere** > **VM.Standard.A1.Flex**
     - OCPUs: **4**
     - Memory: **24 GB**
   - **Networking:** Create new VCN or use default
     - Check "Assign a public IPv4 address"
   - **SSH Key:** Upload your public key or generate one
   - **Boot Volume:** 200 GB (max free)
3. Click **Create**
4. Wait for instance to be RUNNING (~2 minutes)
5. Note the **Public IP Address**

### Step 3: Configure Security List (Firewall)

1. Go to **Networking > Virtual Cloud Networks**
2. Click your VCN > **Security Lists** > Default
3. Add **Ingress Rules:**

| Source CIDR | Port | Description |
|---|---|---|
| 0.0.0.0/0 | 80 | HTTP |
| 0.0.0.0/0 | 443 | HTTPS |
| 0.0.0.0/0 | 3000 | Web Form (direct) |
| 0.0.0.0/0 | 8002 | Dashboard API (direct) |
| 0.0.0.0/0 | 3001 | Grafana |

### Step 4: SSH into VM and Setup

```bash
ssh -i ~/.ssh/your_key ubuntu@<PUBLIC_IP>
```

Copy the setup script to the VM and run it:

```bash
# Option A: Clone repo directly on VM
git clone <your-repo-url> ~/crm-fte
cd ~/crm-fte/deploy/oracle-cloud-free
chmod +x setup-vm.sh
./setup-vm.sh

# Log out and back in (for docker group)
exit
ssh -i ~/.ssh/your_key ubuntu@<PUBLIC_IP>
```

### Step 5: Configure Environment

```bash
cd ~/crm-fte/deploy/oracle-cloud-free
cp .env.example .env
nano .env
```

Fill in your API keys:
- `POSTGRES_PASSWORD` - any strong password
- `OPENAI_API_KEY` - from OpenAI dashboard
- `GMAIL_SENDER_EMAIL` + `GMAIL_APP_PASSWORD` - from Google
- `TWILIO_*` - from Twilio console (optional)
- `WHATSAPP_*` - from Meta developer portal (optional)

### Step 6: Deploy!

```bash
cd ~/crm-fte/deploy/oracle-cloud-free

# Build and start everything
docker compose up -d --build

# Watch the logs
docker compose logs -f

# Check status
docker compose ps
```

First build takes ~5-10 minutes (downloading images + building).

### Step 7: Verify

```bash
# Check all containers are running
docker compose ps

# Test API health
curl http://localhost/health

# Test from outside (use your VM's public IP)
curl http://<PUBLIC_IP>/health
curl http://<PUBLIC_IP>/api/stats
```

---

## Access Points

| Service | URL |
|---|---|
| Web Support Form | `http://<PUBLIC_IP>/` |
| Dashboard | `http://<PUBLIC_IP>/dashboard` |
| API Stats | `http://<PUBLIC_IP>/api/stats` |
| Dispatcher Status | `http://<PUBLIC_IP>/dispatcher/status` |
| Grafana | `http://<PUBLIC_IP>:3001` (admin/admin) |
| Prometheus | `http://<PUBLIC_IP>:9090` |
| WhatsApp Webhook | `http://<PUBLIC_IP>/webhook` |

---

## Common Commands

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# Rebuild and restart a single service
docker compose up -d --build fte-api

# View logs for a specific service
docker compose logs -f fte-worker

# Check resource usage
docker stats

# Restart everything
docker compose restart

# Full reset (deletes data!)
docker compose down -v
docker compose up -d --build
```

---

## Resource Usage (Expected)

On 4 cores / 24GB RAM:

| Service | CPU | RAM |
|---|---|---|
| PostgreSQL | ~0.2 core | ~512MB |
| Redis | ~0.05 core | ~256MB |
| Kafka + Zookeeper | ~0.3 core | ~1.5GB |
| fte-api | ~0.1 core | ~256MB |
| fte-worker | ~0.2 core | ~512MB |
| fte-dispatcher | ~0.1 core | ~256MB |
| fte-dashboard | ~0.1 core | ~256MB |
| fte-web-form | ~0.1 core | ~256MB |
| Prometheus | ~0.1 core | ~256MB |
| Grafana | ~0.1 core | ~128MB |
| NGINX | ~0.05 core | ~64MB |
| **Total** | **~1.4 cores** | **~4.2GB** |

Plenty of headroom on the free tier VM.

---

## Troubleshooting

```bash
# Service won't start
docker compose logs <service-name>

# Database connection issues
docker compose exec postgres psql -U postgres -d crm_db -c "\dt"

# Kafka issues
docker compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Redis check
docker compose exec redis redis-cli ping

# Out of disk space
docker system prune -a

# Rebuild everything from scratch
docker compose down -v
docker system prune -a
docker compose up -d --build
```

---

## Optional: Custom Domain + HTTPS

1. Buy a domain (or use a free one from freenom/duckdns)
2. Point DNS A record to your VM's public IP
3. Install Certbot for free SSL:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```
