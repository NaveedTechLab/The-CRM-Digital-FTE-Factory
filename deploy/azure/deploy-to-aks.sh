#!/bin/bash
set -euo pipefail

###############################################################################
# Deploy CRM Digital FTE Factory to Azure AKS
# Applies all K8s manifests in correct dependency order
###############################################################################

RESOURCE_GROUP="rg-customer-success-fte"
AKS_CLUSTER="aks-fte-cluster"
NAMESPACE="customer-success-fte"
ACR_NAME="acrftecr"
ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
AZURE_K8S="${PROJECT_ROOT}/deploy/azure/k8s"
BASE_K8S="${PROJECT_ROOT}/k8s"
MONITORING="${PROJECT_ROOT}/monitoring"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ── Pre-flight ───────────────────────────────────────────────────────────────
command -v kubectl >/dev/null 2>&1 || error "kubectl not found"

info "Connecting to AKS cluster: $AKS_CLUSTER..."
az aks get-credentials \
    --resource-group "$RESOURCE_GROUP" \
    --name "$AKS_CLUSTER" \
    --overwrite-existing

kubectl cluster-info || error "Cannot connect to AKS cluster"

# ── Step 1: Namespace ────────────────────────────────────────────────────────
info "Step 1/8: Creating namespace..."
kubectl apply -f "${BASE_K8S}/namespace.yaml"

# ── Step 2: Secrets & Config ────────────────────────────────────────────────
info "Step 2/8: Applying secrets and configmap..."
kubectl apply -f "${AZURE_K8S}/azure-secrets.yaml"
kubectl apply -f "${AZURE_K8S}/azure-configmap.yaml"

# ── Step 3: Kafka (Zookeeper + Kafka) ───────────────────────────────────────
info "Step 3/8: Deploying Kafka..."
kubectl apply -f "${BASE_K8S}/kafka.yaml"

info "Waiting for Kafka pods to be ready..."
kubectl wait --for=condition=ready pod -l app=zookeeper -n "$NAMESPACE" --timeout=120s || warn "Zookeeper not ready yet"
kubectl wait --for=condition=ready pod -l app=kafka -n "$NAMESPACE" --timeout=120s || warn "Kafka not ready yet"

# ── Step 4: Application deployments (update image refs for ACR) ─────────────
info "Step 4/8: Deploying application services..."

# API (Phase 3 - Ingestion) - patch image to ACR
kubectl apply -f "${BASE_K8S}/api-deployment.yaml"
kubectl set image deployment/fte-api \
    fte-api="${ACR_LOGIN_SERVER}/fte-api:latest" \
    -n "$NAMESPACE"

# Workers (Phase 4 - Agent, Phase 5 - Dispatcher) - patch images to ACR
kubectl apply -f "${BASE_K8S}/worker-deployment.yaml"
kubectl set image deployment/fte-message-processor \
    worker="${ACR_LOGIN_SERVER}/fte-worker:latest" \
    -n "$NAMESPACE"
kubectl set image deployment/fte-response-dispatcher \
    dispatcher="${ACR_LOGIN_SERVER}/fte-dispatcher:latest" \
    -n "$NAMESPACE"

# Web Form (Next.js) - patch image to ACR
kubectl apply -f "${BASE_K8S}/web-form-deployment.yaml"
kubectl set image deployment/fte-web-form \
    web-form="${ACR_LOGIN_SERVER}/fte-web-form:latest" \
    -n "$NAMESPACE"

# Dashboard API
kubectl apply -f "${AZURE_K8S}/dashboard-deployment.yaml"

# ── Step 5: HPA (autoscaling) ───────────────────────────────────────────────
info "Step 5/8: Applying HPA autoscaling rules..."
kubectl apply -f "${BASE_K8S}/hpa.yaml"

# ── Step 6: NGINX Ingress Controller ────────────────────────────────────────
info "Step 6/8: Installing NGINX Ingress Controller..."
# Check if ingress-nginx is already installed
if ! kubectl get namespace ingress-nginx >/dev/null 2>&1; then
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.9.5/deploy/static/provider/cloud/deploy.yaml
    info "Waiting for ingress controller..."
    kubectl wait --namespace ingress-nginx \
        --for=condition=ready pod \
        --selector=app.kubernetes.io/component=controller \
        --timeout=120s || warn "Ingress controller not ready yet"
else
    info "NGINX Ingress Controller already installed"
fi

kubectl apply -f "${AZURE_K8S}/azure-ingress.yaml"

# ── Step 7: Monitoring Stack ────────────────────────────────────────────────
info "Step 7/8: Deploying monitoring stack..."

# Create monitoring ConfigMaps
kubectl create configmap prometheus-config \
    --from-file=prometheus.yml="${MONITORING}/prometheus.yml" \
    --from-file=alert_rules.yml="${MONITORING}/alert_rules.yml" \
    -n "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

kubectl create configmap grafana-dashboard \
    --from-file=fte-dashboard.json="${MONITORING}/grafana-dashboard.json" \
    -n "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Deploy Prometheus
cat <<'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: customer-success-fte
  labels:
    app: prometheus
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
        - name: prometheus
          image: prom/prometheus:v2.51.0
          args:
            - "--config.file=/etc/prometheus/prometheus.yml"
            - "--storage.tsdb.retention.time=30d"
            - "--web.enable-lifecycle"
          ports:
            - containerPort: 9090
          volumeMounts:
            - name: config
              mountPath: /etc/prometheus
          resources:
            requests:
              cpu: 100m
              memory: 256Mi
            limits:
              cpu: 500m
              memory: 512Mi
      volumes:
        - name: config
          configMap:
            name: prometheus-config
---
apiVersion: v1
kind: Service
metadata:
  name: prometheus-service
  namespace: customer-success-fte
spec:
  selector:
    app: prometheus
  ports:
    - port: 9090
      targetPort: 9090
  type: ClusterIP
EOF

# Deploy Grafana
cat <<'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: customer-success-fte
  labels:
    app: grafana
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
        - name: grafana
          image: grafana/grafana:10.4.0
          ports:
            - containerPort: 3000
          env:
            - name: GF_SECURITY_ADMIN_USER
              value: "admin"
            - name: GF_SECURITY_ADMIN_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: fte-secrets
                  key: POSTGRES_PASSWORD
            - name: GF_USERS_ALLOW_SIGN_UP
              value: "false"
          volumeMounts:
            - name: dashboards
              mountPath: /var/lib/grafana/dashboards
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 256Mi
      volumes:
        - name: dashboards
          configMap:
            name: grafana-dashboard
---
apiVersion: v1
kind: Service
metadata:
  name: grafana-service
  namespace: customer-success-fte
spec:
  selector:
    app: grafana
  ports:
    - port: 3000
      targetPort: 3000
  type: ClusterIP
EOF

# ── Step 8: Verify ──────────────────────────────────────────────────────────
info "Step 8/8: Verifying deployment..."
echo ""

info "Waiting for deployments to roll out..."
kubectl rollout status deployment/fte-api -n "$NAMESPACE" --timeout=180s || warn "fte-api not ready"
kubectl rollout status deployment/fte-web-form -n "$NAMESPACE" --timeout=180s || warn "fte-web-form not ready"
kubectl rollout status deployment/fte-dashboard -n "$NAMESPACE" --timeout=180s || warn "fte-dashboard not ready"

echo ""
echo "============================================================"
info "Deployment complete!"
echo "============================================================"
echo ""
info "Pod Status:"
kubectl get pods -n "$NAMESPACE" -o wide
echo ""
info "Services:"
kubectl get svc -n "$NAMESPACE"
echo ""
info "Ingress:"
kubectl get ingress -n "$NAMESPACE"
echo ""

# Get external IP
INGRESS_IP=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
echo "External IP: $INGRESS_IP"
echo ""
echo "Configure DNS records pointing to $INGRESS_IP:"
echo "  api.customer-success-fte.example.com       → $INGRESS_IP"
echo "  app.customer-success-fte.example.com       → $INGRESS_IP"
echo "  dashboard.customer-success-fte.example.com → $INGRESS_IP"
echo "  monitoring.customer-success-fte.example.com → $INGRESS_IP"
echo ""
echo "Quick verify:"
echo "  kubectl get pods -n $NAMESPACE"
echo "  kubectl logs -f deployment/fte-api -n $NAMESPACE"
echo "  curl http://$INGRESS_IP/health -H 'Host: api.customer-success-fte.example.com'"
