---
id: 0008
title: Azure AKS Production Deployment
stage: green
date: 2026-02-26
surface: agent
model: claude-opus-4-6
feature: 005-response-delivery-egress
branch: 005-response-delivery-egress
user: FairCom
command: implement
labels: ["azure", "aks", "deployment", "kubernetes", "production", "docker"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - deploy/azure/setup-azure.sh
  - deploy/azure/build-push.sh
  - deploy/azure/deploy-to-aks.sh
  - deploy/azure/init-database.sh
  - deploy/azure/k8s/azure-configmap.yaml
  - deploy/azure/k8s/azure-secrets.yaml
  - deploy/azure/k8s/azure-ingress.yaml
  - deploy/azure/k8s/dashboard-deployment.yaml
  - deploy/azure/README.md
  - phase-3-multi-channel-ingestion/Dockerfile
  - dashboard-api/Dockerfile
tests:
  - Verification plan in README (10-step checklist)
---

## Prompt

Implement the Azure AKS Production Deployment Plan for the CRM Digital FTE Factory. The plan covers: Azure resource provisioning (AKS, ACR, PostgreSQL with pgvector, Redis, Key Vault), Dockerfiles for missing services, Azure-specific K8s manifests (configmap, secrets, ingress, dashboard deployment), build/push/deploy scripts, database initialization, and monitoring setup.

## Response snapshot

Created 11 files for full Azure AKS production deployment:

**Infrastructure scripts (4):**
- `setup-azure.sh` - Provisions Resource Group, AKS (3-node D2s_v3), ACR, PostgreSQL Flexible Server (pgvector), Redis Cache, Key Vault with secret storage
- `build-push.sh` - Builds 5 Docker images and pushes to ACR
- `deploy-to-aks.sh` - 8-step deployment orchestrator (namespace, secrets, Kafka, apps, HPA, ingress, monitoring, verification)
- `init-database.sh` - pgvector enablement, schema creation from 01-init-db.sql, knowledge base seeding, Phase 4/5 tables

**Azure K8s manifests (4):**
- `azure-configmap.yaml` - Azure PostgreSQL/Redis connection strings, rate limits
- `azure-secrets.yaml` - Secret placeholders (populate from Key Vault)
- `azure-ingress.yaml` - NGINX ingress with 4 hosts (API, app, dashboard, monitoring)
- `dashboard-deployment.yaml` - Dashboard API deployment + service + HPA

**Dockerfiles (2 new):**
- `phase-3-multi-channel-ingestion/Dockerfile` - Python 3.11-slim, uvicorn entrypoint
- `dashboard-api/Dockerfile` - Python 3.11-slim, uvicorn entrypoint

**Documentation (1):**
- `deploy/azure/README.md` - Complete deployment guide with architecture, steps, DNS, scaling, monitoring, troubleshooting

## Outcome

- Impact: Full production deployment pipeline for Azure AKS with ~$206/month estimated cost
- Tests: 10-step verification plan documented in README
- Files: 11 files created (4 scripts, 4 K8s manifests, 2 Dockerfiles, 1 README)
- Next prompts: Configure actual secrets in azure-secrets.yaml, run setup-azure.sh, set up TLS certificates
- Reflection: Leveraged existing K8s manifests and Dockerfiles as base, only adding Azure-specific configuration overlay

## Evaluation notes (flywheel)

- Failure modes observed: None - implementation followed plan directly
- Graders run and results (PASS/FAIL): N/A - infrastructure deployment scripts (manual verification required)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Add Azure Key Vault CSI driver for automatic secret injection instead of manual secrets.yaml
