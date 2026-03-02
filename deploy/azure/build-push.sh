#!/bin/bash
set -euo pipefail

###############################################################################
# Build & Push Docker Images to Azure Container Registry
###############################################################################

ACR_NAME="acrftecr"
ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"
TAG="${1:-latest}"
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ── Pre-flight ───────────────────────────────────────────────────────────────
command -v az >/dev/null 2>&1 || error "Azure CLI not found"
command -v docker >/dev/null 2>&1 || error "Docker not found"

info "Logging into ACR: $ACR_LOGIN_SERVER..."
az acr login --name "$ACR_NAME"

# ── Image definitions ────────────────────────────────────────────────────────
# Format: IMAGE_NAME|BUILD_CONTEXT|DOCKERFILE_PATH
IMAGES=(
    "fte-api|${PROJECT_ROOT}/phase-3-multi-channel-ingestion|${PROJECT_ROOT}/phase-3-multi-channel-ingestion/Dockerfile"
    "fte-worker|${PROJECT_ROOT}/phase-4-agent-intelligence-logic|${PROJECT_ROOT}/phase-4-agent-intelligence-logic/Dockerfile"
    "fte-dispatcher|${PROJECT_ROOT}/phase-5-response-delivery-egress|${PROJECT_ROOT}/phase-5-response-delivery-egress/Dockerfile"
    "fte-web-form|${PROJECT_ROOT}/web-support-form|${PROJECT_ROOT}/web-support-form/Dockerfile"
    "fte-dashboard|${PROJECT_ROOT}/dashboard-api|${PROJECT_ROOT}/dashboard-api/Dockerfile"
)

FAILED=0

for entry in "${IMAGES[@]}"; do
    IFS='|' read -r IMAGE_NAME BUILD_CONTEXT DOCKERFILE <<< "$entry"
    FULL_TAG="${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${TAG}"

    info "Building ${IMAGE_NAME}..."
    if docker build -t "$FULL_TAG" -f "$DOCKERFILE" "$BUILD_CONTEXT"; then
        info "Pushing ${FULL_TAG}..."
        if docker push "$FULL_TAG"; then
            info "${IMAGE_NAME}:${TAG} pushed successfully"
        else
            warn "Failed to push ${IMAGE_NAME}"
            FAILED=$((FAILED + 1))
        fi
    else
        warn "Failed to build ${IMAGE_NAME}"
        FAILED=$((FAILED + 1))
    fi
    echo ""
done

# ── Summary ──────────────────────────────────────────────────────────────────
echo "============================================================"
if [ "$FAILED" -eq 0 ]; then
    info "All images built and pushed successfully!"
else
    warn "${FAILED} image(s) failed. Check output above."
fi
echo "============================================================"
echo ""
echo "Images in ACR:"
az acr repository list --name "$ACR_NAME" --output table
echo ""
echo "Next step: ./deploy-to-aks.sh"
