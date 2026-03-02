---
id: 0009
title: Oracle Cloud Free Tier Deployment
stage: green
date: 2026-02-26
surface: agent
model: claude-opus-4-6
feature: 005-response-delivery-egress
branch: 005-response-delivery-egress
user: FairCom
command: implement
labels: ["oracle-cloud", "free-tier", "docker-compose", "deployment", "nginx"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - deploy/oracle-cloud-free/docker-compose.yml
  - deploy/oracle-cloud-free/nginx.conf
  - deploy/oracle-cloud-free/.env.example
  - deploy/oracle-cloud-free/setup-vm.sh
  - deploy/oracle-cloud-free/README.md
tests:
  - Manual verification via docker compose ps and curl /health
---

## Prompt

User requested free deployment alternative instead of Azure AKS (~$206/month). After presenting options (Oracle Cloud Free, Render+Neon+Upstash, Local Docker+ngrok), user selected Oracle Cloud Always Free Tier.

## Response snapshot

Created complete Oracle Cloud Free Tier deployment with 5 files:
- `docker-compose.yml` - Full 12-service stack (PostgreSQL+pgvector, Redis, Kafka+Zookeeper, 5 app services, Prometheus, Grafana, NGINX)
- `nginx.conf` - Reverse proxy routing all services through port 80 with rate limiting
- `.env.example` - Environment variable template for all API keys
- `setup-vm.sh` - VM bootstrap script (Docker, firewall, swap)
- `README.md` - Step-by-step guide from OCI account creation to deployment

Oracle Cloud Always Free: 4 ARM cores, 24GB RAM, 200GB disk - estimated usage ~1.4 cores / 4.2GB RAM.

## Outcome

- Impact: Full production-grade deployment at $0/month cost using Oracle Cloud Always Free Tier
- Tests: Verification steps documented in README (docker compose ps, curl health checks)
- Files: 5 files created in deploy/oracle-cloud-free/
- Next prompts: Clone repo on OCI VM, configure .env, docker compose up -d --build
- Reflection: Docker Compose is simpler than K8s for single-VM deployment and perfectly suited for hackathon demo

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A - deployment scripts
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Add Certbot/Let's Encrypt for auto-HTTPS
