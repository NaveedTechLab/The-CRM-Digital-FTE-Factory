###############################################################################
# CRM Digital FTE Factory - HuggingFace Spaces Docker
# Runs: Dashboard API (FastAPI) + Web Form (Next.js) + NGINX
# Port: 7860 (HuggingFace default)
###############################################################################

FROM node:18-slim AS frontend-builder

WORKDIR /frontend
COPY web-support-form/package.json ./
RUN npm install
COPY web-support-form/ ./

# Update Next.js config to proxy to internal dashboard API
RUN echo '/** @type {import("next").NextConfig} */ \n\
const nextConfig = { \n\
  async rewrites() { \n\
    return [ \n\
      { source: "/support/:path*", destination: "http://127.0.0.1:8002/support/:path*" }, \n\
      { source: "/api/:path*", destination: "http://127.0.0.1:8002/api/:path*" }, \n\
    ]; \n\
  }, \n\
}; \n\
module.exports = nextConfig;' > next.config.js

RUN npm run build

# ── Final image ──────────────────────────────────────────────────────────────
FROM python:3.11-slim

# Install Node.js, NGINX, supervisor
RUN apt-get update && apt-get install -y \
    curl \
    nginx \
    supervisor \
    gcc \
    postgresql-server-dev-all \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Dashboard API (Python) ───────────────────────────────────────────────────
COPY dashboard-api/requirements.txt /app/dashboard-api/requirements.txt
RUN pip install --no-cache-dir -r /app/dashboard-api/requirements.txt

COPY dashboard-api/ /app/dashboard-api/

# ── Web Form (Next.js - pre-built) ──────────────────────────────────────────
COPY --from=frontend-builder /frontend/.next /app/web-form/.next
COPY --from=frontend-builder /frontend/node_modules /app/web-form/node_modules
COPY --from=frontend-builder /frontend/package.json /app/web-form/package.json
COPY --from=frontend-builder /frontend/public /app/web-form/public
COPY --from=frontend-builder /frontend/next.config.js /app/web-form/next.config.js

# ── NGINX config ─────────────────────────────────────────────────────────────
COPY deploy/huggingface/nginx.conf /etc/nginx/nginx.conf

# ── Supervisor config ────────────────────────────────────────────────────────
COPY deploy/huggingface/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# ── Startup script ───────────────────────────────────────────────────────────
COPY deploy/huggingface/start.sh /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 7860

CMD ["/app/start.sh"]
