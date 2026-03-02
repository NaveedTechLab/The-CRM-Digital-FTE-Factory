# Azure AKS Deployment Guide

## CRM Digital FTE Factory - Production Deployment

### Architecture

```
Azure Resource Group: rg-customer-success-fte
├── AKS Cluster (3x Standard_D2s_v3)
│   ├── Namespace: customer-success-fte
│   ├── fte-api (Phase 3 - Ingestion)         x2 pods
│   ├── fte-message-processor (Phase 4)        x3 pods
│   ├── fte-response-dispatcher (Phase 5)      x2 pods
│   ├── fte-web-form (Next.js)                 x2 pods
│   ├── fte-dashboard (Dashboard API)          x2 pods
│   ├── Kafka + Zookeeper                      x1 each
│   ├── Prometheus + Grafana                   x1 each
│   └── NGINX Ingress Controller
├── Azure Database for PostgreSQL (pgvector)
├── Azure Cache for Redis
├── Azure Container Registry (ACR)
└── Azure Key Vault
```

### Prerequisites

- Azure CLI (`az`) installed and logged in
- Docker installed and running
- `kubectl` installed
- `psql` client installed (for database init)
- Azure subscription with sufficient quota

### Estimated Monthly Cost

| Resource | SKU | Cost |
|---|---|---|
| AKS (3 nodes D2s_v3) | Standard | ~$150 |
| PostgreSQL Flexible (B1ms) | Burstable | ~$15 |
| Redis Cache (C0) | Basic | ~$16 |
| ACR | Basic | ~$5 |
| Load Balancer | Standard | ~$20 |
| **Total** | | **~$206/month** |

---

## Deployment Steps

### 1. Provision Azure Resources

```bash
chmod +x deploy/azure/*.sh
./deploy/azure/setup-azure.sh
```

This creates:
- Resource Group, AKS, ACR, PostgreSQL, Redis, Key Vault
- Stores credentials in Key Vault
- Configures AKS to pull from ACR

### 2. Update Secrets

Edit `deploy/azure/k8s/azure-secrets.yaml` with actual values:

```bash
# Get values from Key Vault
az keyvault secret show --vault-name kv-fte-secrets --name pg-password --query value -o tsv
az keyvault secret show --vault-name kv-fte-secrets --name redis-connection-string --query value -o tsv
az keyvault secret show --vault-name kv-fte-secrets --name openai-api-key --query value -o tsv
```

Replace all `<PLACEHOLDER>` values in `azure-secrets.yaml`.

### 3. Initialize Database

```bash
./deploy/azure/init-database.sh
```

This runs:
- pgvector extension enablement
- Full schema from `01-init-db.sql`
- Knowledge base seed data
- Phase 4/5 operational tables

### 4. Build & Push Docker Images

```bash
./deploy/azure/build-push.sh
```

Builds and pushes 5 images to ACR:
- `acrftecr.azurecr.io/fte-api:latest`
- `acrftecr.azurecr.io/fte-worker:latest`
- `acrftecr.azurecr.io/fte-dispatcher:latest`
- `acrftecr.azurecr.io/fte-web-form:latest`
- `acrftecr.azurecr.io/fte-dashboard:latest`

### 5. Deploy to AKS

```bash
./deploy/azure/deploy-to-aks.sh
```

Deploys in order:
1. Namespace
2. Secrets & ConfigMap
3. Kafka (Zookeeper + broker)
4. Application pods (API, workers, web form, dashboard)
5. HPA autoscaling
6. NGINX Ingress Controller
7. Monitoring (Prometheus + Grafana)

---

## Verification

```bash
# Check all pods are running
kubectl get pods -n customer-success-fte

# Check services
kubectl get svc -n customer-success-fte

# Check ingress and external IP
kubectl get ingress -n customer-success-fte

# Test API health
curl http://<EXTERNAL-IP>/health -H 'Host: api.customer-success-fte.example.com'

# View logs
kubectl logs -f deployment/fte-api -n customer-success-fte
kubectl logs -f deployment/fte-message-processor -n customer-success-fte
kubectl logs -f deployment/fte-response-dispatcher -n customer-success-fte

# Check HPA
kubectl get hpa -n customer-success-fte
```

---

## DNS Configuration

Point these records to the NGINX Ingress external IP:

| Record | Type | Target |
|---|---|---|
| `api.customer-success-fte.example.com` | A | `<INGRESS_IP>` |
| `app.customer-success-fte.example.com` | A | `<INGRESS_IP>` |
| `dashboard.customer-success-fte.example.com` | A | `<INGRESS_IP>` |
| `monitoring.customer-success-fte.example.com` | A | `<INGRESS_IP>` |

---

## Scaling

HPA is configured for automatic scaling:

| Deployment | Min | Max | CPU Target |
|---|---|---|---|
| fte-api | 2 | 10 | 70% |
| fte-message-processor | 3 | 30 | 70% |
| fte-response-dispatcher | 2 | 15 | 70% |
| fte-dashboard | 2 | 6 | 70% |

Manual scaling:
```bash
kubectl scale deployment/fte-api --replicas=5 -n customer-success-fte
```

---

## Monitoring

- **Prometheus**: `monitoring.customer-success-fte.example.com` (via ingress) or `kubectl port-forward svc/prometheus-service 9090:9090 -n customer-success-fte`
- **Grafana**: `monitoring.customer-success-fte.example.com` or `kubectl port-forward svc/grafana-service 3000:3000 -n customer-success-fte`
  - Login: admin / (uses POSTGRES_PASSWORD from secrets)

---

## Troubleshooting

```bash
# Pod not starting
kubectl describe pod <pod-name> -n customer-success-fte

# Check events
kubectl get events -n customer-success-fte --sort-by='.lastTimestamp'

# Database connectivity from a pod
kubectl exec -it deployment/fte-api -n customer-success-fte -- python -c "
import psycopg2, os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
print('DB connected:', conn.status)
conn.close()
"

# Kafka topics
kubectl exec -it deployment/kafka -n customer-success-fte -- \
    kafka-topics --list --bootstrap-server localhost:9092

# Redis connectivity
kubectl exec -it deployment/fte-api -n customer-success-fte -- python -c "
import redis, os
r = redis.from_url(os.environ['REDIS_URL'])
r.ping()
print('Redis OK')
"
```

---

## Teardown

```bash
# Delete all resources in the namespace
kubectl delete namespace customer-success-fte

# Delete all Azure resources
az group delete --name rg-customer-success-fte --yes --no-wait
```
