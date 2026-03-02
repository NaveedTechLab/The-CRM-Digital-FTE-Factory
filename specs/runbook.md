# Incident Response Runbook - Customer Success Digital FTE

## Table of Contents
1. [Incident Classification](#incident-classification)
2. [Response Procedures](#response-procedures)
3. [Common Incidents](#common-incidents)
4. [Diagnostic Commands](#diagnostic-commands)
5. [Recovery Procedures](#recovery-procedures)
6. [Post-Incident Review](#post-incident-review)

---

## Incident Classification

| Severity | Description | Response Time | Examples |
|----------|-------------|---------------|---------|
| **SEV-1 (Critical)** | Complete system outage, all channels down | 15 minutes | All pods crashed, database unreachable |
| **SEV-2 (Major)** | One channel completely down, or >50% message failure | 30 minutes | Gmail delivery 100% failing, Kafka down |
| **SEV-3 (Minor)** | Degraded performance, partial failures | 2 hours | High latency, rate limit issues |
| **SEV-4 (Low)** | Cosmetic issues, non-blocking bugs | Next business day | Dashboard display errors |

---

## Response Procedures

### SEV-1: Critical Incident Response

1. **Acknowledge** (0-5 min)
   - Confirm incident in monitoring alerts
   - Notify on-call team
   - Create incident channel/thread

2. **Assess** (5-15 min)
   ```bash
   # Check all pod statuses
   kubectl get pods -n customer-success-fte

   # Check recent events
   kubectl get events -n customer-success-fte --sort-by='.lastTimestamp'

   # Check node health
   kubectl get nodes

   # Check service endpoints
   kubectl get endpoints -n customer-success-fte
   ```

3. **Mitigate** (15-30 min)
   - Restart failed pods: `kubectl rollout restart deployment/<name> -n customer-success-fte`
   - Scale up if under load: `kubectl scale deployment/fte-api --replicas=5 -n customer-success-fte`
   - If database issue: check PostgreSQL pod and connections
   - If Kafka issue: check broker pods and consumer lag

4. **Resolve** (30-60 min)
   - Apply fix or workaround
   - Verify all channels operational
   - Monitor for 30 min stability

5. **Communicate**
   - Update status page
   - Notify affected customers if message loss occurred

### SEV-2: Major Incident Response

1. Check specific channel health
2. Identify failing component
3. Apply targeted fix (see Common Incidents below)
4. Monitor recovery

### SEV-3/SEV-4: Standard Response

1. Log issue in tracking system
2. Investigate root cause
3. Schedule fix in next maintenance window

---

## Common Incidents

### INC-01: Pods in CrashLoopBackOff

**Symptoms:** Pod repeatedly crashing, container restart count increasing

**Diagnosis:**
```bash
# Check pod status and restart count
kubectl get pods -n customer-success-fte

# Check pod logs for crash reason
kubectl logs <pod-name> -n customer-success-fte --previous

# Check pod events
kubectl describe pod <pod-name> -n customer-success-fte
```

**Resolution:**
1. Check logs for the crash reason (OOM, exception, missing config)
2. If OOM: increase memory limits in deployment manifest
3. If config error: check ConfigMap and Secrets
4. If code error: rollback to previous version
   ```bash
   kubectl rollout undo deployment/<name> -n customer-success-fte
   ```

---

### INC-02: Database Connection Failures

**Symptoms:** Services logging "connection refused" or "too many connections"

**Diagnosis:**
```bash
# Check PostgreSQL pod
kubectl get pods -l app=postgres -n customer-success-fte

# Check PostgreSQL logs
kubectl logs -l app=postgres -n customer-success-fte --tail=100

# Check connection count (exec into postgres pod)
kubectl exec -it <postgres-pod> -n customer-success-fte -- psql -U fte_user -d fte_db -c "SELECT count(*) FROM pg_stat_activity;"
```

**Resolution:**
1. If pod down: restart PostgreSQL StatefulSet
2. If connection exhaustion: restart application pods (releases connections)
3. If disk full: expand PVC or clean old data
   ```sql
   -- Archive old messages (>90 days)
   DELETE FROM messages WHERE created_at < NOW() - INTERVAL '90 days';
   VACUUM ANALYZE messages;
   ```

---

### INC-03: Kafka Consumer Lag

**Symptoms:** Messages delayed, queue building up, responses slow

**Diagnosis:**
```bash
# Check Kafka pods
kubectl get pods -l app=kafka -n customer-success-fte

# Check consumer lag (exec into kafka pod)
kubectl exec -it <kafka-pod> -n customer-success-fte -- \
  kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
  --describe --group response_dispatcher_group

# Check dispatcher pod logs
kubectl logs -l app=fte-dispatcher -n customer-success-fte --tail=50
```

**Resolution:**
1. If consumer crashed: restart dispatcher deployment
2. If lag growing: scale dispatcher replicas
   ```bash
   kubectl scale deployment/fte-dispatcher --replicas=5 -n customer-success-fte
   ```
3. If Kafka broker issue: restart Kafka pods
4. Check topic partition count matches consumer count

---

### INC-04: Gmail API Failures

**Symptoms:** Email delivery failing, rate limit errors in logs

**Diagnosis:**
```bash
# Check Phase 5 dispatcher logs
kubectl logs -l app=fte-dispatcher -n customer-success-fte | grep -i "gmail"

# Check rate limit status
kubectl exec -it <redis-pod> -n customer-success-fte -- redis-cli GET "rate_limit:gmail"
```

**Resolution:**
1. If rate limited (HTTP 429): wait for quota reset (resets per minute/day)
2. If OAuth token expired: trigger token refresh
3. If API disabled: re-enable Gmail API in Google Cloud Console
4. If quota exceeded (daily): wait for daily reset, scale down sending rate
5. Check `GMAIL_RATE_LIMIT_PER_MINUTE` config (default: 250)

---

### INC-05: WhatsApp/Twilio Failures

**Symptoms:** WhatsApp messages not delivered, Twilio errors

**Diagnosis:**
```bash
# Check dispatcher logs for Twilio errors
kubectl logs -l app=fte-dispatcher -n customer-success-fte | grep -i "twilio\|whatsapp"

# Check Twilio account status
# Visit: https://www.twilio.com/console
```

**Resolution:**
1. If authentication error: verify `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` in secrets
2. If rate limited: reduce sending rate, check `WHATSAPP_RATE_LIMIT_PER_MINUTE` (default: 50)
3. If 24-hour session expired: use approved template messages
4. If account suspended: contact Twilio support
5. If webhook validation failing: verify webhook URL and auth token

---

### INC-06: Redis Unavailable

**Symptoms:** Rate limiting not working, potential API overuse

**Diagnosis:**
```bash
# Check Redis pod
kubectl get pods -l app=redis -n customer-success-fte

# Check Redis logs
kubectl logs -l app=redis -n customer-success-fte --tail=50

# Test Redis connectivity
kubectl exec -it <redis-pod> -n customer-success-fte -- redis-cli ping
```

**Resolution:**
1. If pod crashed: Redis will restart (data loss acceptable for rate limits)
2. If memory full: flush rate limit keys
   ```bash
   kubectl exec -it <redis-pod> -- redis-cli FLUSHDB
   ```
3. Rate limiter degrades gracefully (allows all requests if Redis unavailable)

---

### INC-07: High Latency (P95 > 3 seconds)

**Symptoms:** Slow responses across channels, HPA not scaling fast enough

**Diagnosis:**
```bash
# Check HPA status
kubectl get hpa -n customer-success-fte

# Check resource usage
kubectl top pods -n customer-success-fte

# Check Prometheus metrics
curl http://<prometheus-url>/api/v1/query?query=http_request_duration_seconds
```

**Resolution:**
1. Manual scale up:
   ```bash
   kubectl scale deployment/fte-api --replicas=10 -n customer-success-fte
   kubectl scale deployment/fte-worker --replicas=10 -n customer-success-fte
   ```
2. Check database query performance (slow queries)
3. Check Kafka consumer lag (processing bottleneck)
4. Review pgvector query performance (RAG retrieval)
5. If sustained: lower HPA CPU threshold from 70% to 60%

---

### INC-08: Message Loss Detected

**Symptoms:** Messages received but no response delivered, missing tickets

**Diagnosis:**
```bash
# Check Kafka topics for unprocessed messages
kubectl exec -it <kafka-pod> -n customer-success-fte -- \
  kafka-console-consumer.sh --bootstrap-server localhost:9092 \
  --topic dlq --from-beginning --max-messages 10

# Check database for orphaned tickets
kubectl exec -it <postgres-pod> -n customer-success-fte -- \
  psql -U fte_user -d fte_db -c \
  "SELECT * FROM tickets WHERE status = 'open' AND created_at < NOW() - INTERVAL '1 hour';"
```

**Resolution:**
1. Check DLQ (Dead Letter Queue) for failed messages
2. Reprocess DLQ messages manually if needed
3. Check all service logs for errors in the processing chain
4. Verify Kafka consumer offsets are advancing
5. If data corruption: restore from last known good backup

---

### INC-09: Web Form Not Loading

**Symptoms:** Next.js frontend returning errors or blank page

**Diagnosis:**
```bash
# Check web form pods
kubectl get pods -l app=web-support-form -n customer-success-fte

# Check pod logs
kubectl logs -l app=web-support-form -n customer-success-fte --tail=50

# Check ingress
kubectl get ingress -n customer-success-fte
```

**Resolution:**
1. If pod crashed: restart deployment
2. If build error: check Next.js build logs
3. If API unreachable from form: check CORS configuration and API endpoint config
4. If ingress issue: verify ingress controller and TLS cert

---

### INC-10: HPA Not Scaling

**Symptoms:** High load but replica count not increasing

**Diagnosis:**
```bash
# Check HPA status and events
kubectl describe hpa -n customer-success-fte

# Check metrics server
kubectl get pods -n kube-system | grep metrics-server
```

**Resolution:**
1. If metrics server down: restart metrics-server
2. If HPA max reached: increase maxReplicas in HPA manifest
3. If resource limits preventing scaling: check node capacity
4. Manual override:
   ```bash
   kubectl scale deployment/<name> --replicas=<count> -n customer-success-fte
   ```

---

## Diagnostic Commands Quick Reference

```bash
# === System Overview ===
kubectl get all -n customer-success-fte
kubectl get events -n customer-success-fte --sort-by='.lastTimestamp' | tail -20

# === Pod Health ===
kubectl get pods -n customer-success-fte -o wide
kubectl top pods -n customer-success-fte
kubectl describe pod <pod-name> -n customer-success-fte

# === Logs ===
kubectl logs <pod-name> -n customer-success-fte --tail=100
kubectl logs <pod-name> -n customer-success-fte --previous  # crashed container

# === Database ===
kubectl exec -it <postgres-pod> -n customer-success-fte -- \
  psql -U fte_user -d fte_db -c "SELECT count(*) FROM tickets WHERE status='open';"

# === Kafka ===
kubectl exec -it <kafka-pod> -n customer-success-fte -- \
  kafka-topics.sh --bootstrap-server localhost:9092 --list

# === Redis ===
kubectl exec -it <redis-pod> -n customer-success-fte -- redis-cli INFO memory

# === Networking ===
kubectl get svc -n customer-success-fte
kubectl get ingress -n customer-success-fte

# === Scaling ===
kubectl get hpa -n customer-success-fte
kubectl top nodes
```

---

## Recovery Procedures

### Full System Recovery (from scratch)

1. Verify infrastructure (nodes, storage)
2. Apply namespace: `kubectl apply -f k8s/namespace.yaml`
3. Apply config: `kubectl apply -f k8s/configmap.yaml -f k8s/secrets.yaml`
4. Start data layer: `kubectl apply -f k8s/postgres.yaml -f k8s/kafka.yaml -f k8s/redis.yaml`
5. Wait for data layer ready (2-5 min)
6. Start application layer: `kubectl apply -f k8s/api-deployment.yaml -f k8s/worker-deployment.yaml`
7. Start web form: `kubectl apply -f k8s/web-form-deployment.yaml`
8. Apply networking: `kubectl apply -f k8s/ingress.yaml`
9. Apply autoscaling: `kubectl apply -f k8s/hpa.yaml`
10. Verify all pods running: `kubectl get pods -n customer-success-fte`
11. Test health endpoints across all services

### Database Recovery

```bash
# Restore from backup
kubectl exec -it <postgres-pod> -n customer-success-fte -- \
  pg_restore -U fte_user -d fte_db /backups/latest.dump

# Verify data integrity
kubectl exec -it <postgres-pod> -n customer-success-fte -- \
  psql -U fte_user -d fte_db -c "SELECT count(*) FROM customers; SELECT count(*) FROM tickets;"
```

### Kafka Topic Recovery

```bash
# Recreate topics if lost
kubectl exec -it <kafka-pod> -n customer-success-fte -- \
  kafka-topics.sh --bootstrap-server localhost:9092 \
  --create --topic inbound_events --partitions 6 --replication-factor 1

kubectl exec -it <kafka-pod> -n customer-success-fte -- \
  kafka-topics.sh --bootstrap-server localhost:9092 \
  --create --topic outbound_responses --partitions 6 --replication-factor 1
```

---

## Post-Incident Review

After every SEV-1 or SEV-2 incident, conduct a post-incident review within 48 hours:

### Review Template
1. **Incident Summary:** What happened, when, duration
2. **Timeline:** Chronological sequence of events and actions
3. **Impact:** Messages lost, customers affected, SLA breaches
4. **Root Cause:** Technical root cause analysis
5. **Resolution:** What fixed the issue
6. **Action Items:** Preventive measures with owners and deadlines
7. **Lessons Learned:** What went well, what to improve

### SLA Tracking
| Metric | Target | Measurement |
|--------|--------|-------------|
| Uptime | >99.9% | Monthly calculation |
| P95 Latency | <3 seconds | Prometheus percentile |
| Message Loss | 0% | DLQ + delivery tracking |
| Escalation Rate | <25% | Agent metrics |
| Cross-Channel ID | >95% | Identity resolver logs |
