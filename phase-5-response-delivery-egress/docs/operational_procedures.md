# Operational Procedures for Response Delivery & Egress System

## Table of Contents
1. [System Overview](#system-overview)
2. [Deployment Procedures](#deployment-procedures)
3. [Monitoring and Alerting](#monitoring-and-alerting)
4. [Troubleshooting Guide](#troubleshooting-guide)
5. [Maintenance Procedures](#maintenance-procedures)
6. [Security Procedures](#security-procedures)
7. [Backup and Recovery](#backup-and-recovery)
8. [Scaling Guidelines](#scaling-guidelines)

## System Overview

The Response Delivery & Egress system is responsible for routing agent responses to appropriate communication channels (Gmail, WhatsApp, Webhook). It consists of:

- **Response Dispatcher**: Kafka consumer that routes messages based on channel
- **Channel Services**: Individual services for each communication channel
- **Rate Limiter**: Manages API rate limits to prevent blacklisting
- **Delivery Tracker**: Tracks delivery status and manages retry queue
- **Database**: PostgreSQL for storing message status and logs

### Key Components
- **Kafka**: Message queuing for outbound responses
- **PostgreSQL**: Persistent storage for message tracking
- **Redis**: Rate limiting and caching
- **External APIs**: Gmail, Twilio WhatsApp

## Deployment Procedures

### Prerequisites
- Docker and Docker Compose
- Access to external APIs (Gmail, Twilio)
- PostgreSQL database access
- Kafka cluster access

### Environment Variables
Required environment variables in `.env`:
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Redis
REDIS_URL=redis://localhost:6379

# Gmail
GMAIL_CREDENTIALS_PATH=/path/to/credentials.json
GMAIL_TOKEN_PATH=/path/to/token.json
GMAIL_SENDER_EMAIL=user@gmail.com

# Twilio
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890

# API Limits
GMAIL_RATE_LIMIT_PER_MINUTE=250
WHATSAPP_RATE_LIMIT_PER_MINUTE=50
```

### Deployment Steps
1. **Prepare Environment**
   ```bash
   cp .env.example .env
   # Edit .env with actual values
   ```

2. **Start Infrastructure**
   ```bash
   docker-compose up -d postgresql redis kafka
   # Wait for services to be ready
   ```

3. **Initialize Database**
   ```bash
   python scripts/init_db.py
   ```

4. **Start Response Dispatcher**
   ```bash
   python scripts/start_dispatcher.py
   ```

5. **Verify Health**
   ```bash
   curl http://localhost:8000/health
   ```

## Monitoring and Alerting

### Key Metrics to Monitor
- **Message Processing Rate**: Messages per second
- **Delivery Success Rate**: Percentage of successful deliveries
- **Rate Limit Hits**: Count of rate limit events
- **Retry Queue Size**: Number of messages awaiting retry
- **API Response Times**: Time to deliver via each channel
- **System Resource Usage**: CPU, Memory, Disk

### Health Checks
- `/health`: Overall system health
- `/health/channels`: Per-channel health status
- `/health/dependencies`: External dependencies status
- `/metrics`: Prometheus-compatible metrics

### Alert Thresholds
- **Critical**: Delivery success rate < 95%
- **Warning**: Rate limit hits > 10 per minute
- **Critical**: Retry queue > 1000 messages
- **Warning**: API response time > 5 seconds

## Troubleshooting Guide

### Common Issues

#### 1. Messages Not Being Delivered
**Symptoms**: Messages stuck in 'pending' or 'in_progress' status
**Diagnosis**:
```bash
# Check dispatcher logs
tail -f logs/dispatcher.log

# Check database status
SELECT * FROM outbound_messages WHERE delivery_status = 'in_progress';
```
**Solution**: Restart dispatcher service, check external API connectivity

#### 2. Rate Limit Errors
**Symptoms**: High number of rate limit hits
**Diagnosis**:
```bash
# Check rate limit logs
SELECT * FROM rate_limit_state ORDER BY updated_at DESC;
```
**Solution**: Adjust rate limit configuration, implement backoff strategies

#### 3. Database Connection Issues
**Symptoms**: Database connection errors in logs
**Diagnosis**:
```bash
# Test connection
python -c "from app.database import test_connection; test_connection()"
```
**Solution**: Check database server, connection pool settings

#### 4. Kafka Consumer Lag
**Symptoms**: Messages delayed in processing
**Diagnosis**:
```bash
# Check Kafka consumer lag
kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group response_dispatcher_group
```
**Solution**: Scale dispatcher instances, optimize processing

### Diagnostic Commands
```bash
# Check system status
curl http://localhost:8000/health

# Get metrics
curl http://localhost:8000/metrics

# Check message counts
python scripts/dashboard_cli.py --days 1

# Run verification test
python scripts/verification_stress_test.py --messages 10
```

## Maintenance Procedures

### Daily Maintenance
- Monitor system health
- Check for failed messages
- Verify backup completion
- Review logs for errors

### Weekly Maintenance
- Review performance metrics
- Check for scaling needs
- Update rate limit configurations
- Review security logs

### Monthly Maintenance
- Database maintenance (vacuum, analyze)
- Update certificates and API keys
- Review and update rate limits
- Performance tuning

### Database Maintenance
```sql
-- Vacuum and analyze tables
VACUUM ANALYZE outbound_messages;
VACUUM ANALYZE delivery_logs;
VACUUM ANALYZE retry_queue_items;
```

## Security Procedures

### Credential Management
- Rotate API keys monthly
- Store credentials in secure vault
- Monitor access logs
- Use encrypted connections

### Rate Limiting Security
- Monitor for abuse patterns
- Implement IP-based rate limiting
- Track suspicious activity
- Automatic blocking of abusive clients

### Data Protection
- Encrypt sensitive data in transit
- Mask PII in logs
- Regular security audits
- Compliance with privacy regulations

## Backup and Recovery

### Backup Procedures
- Database dumps daily
- Configuration backups
- Log rotation and archival
- API credentials backup

### Recovery Procedures
1. **Database Recovery**
   ```bash
   # Restore from backup
   pg_restore -d database_name backup_file.dump
   ```

2. **Configuration Recovery**
   - Restore from version control
   - Reconfigure environment variables
   - Re-establish external connections

3. **Service Recovery**
   - Restart all services
   - Verify functionality
   - Monitor for issues

## Scaling Guidelines

### Horizontal Scaling
- Multiple dispatcher instances
- Load balancing between instances
- Shared database connections
- Distributed rate limiting

### Vertical Scaling
- Increase instance resources
- Optimize database queries
- Improve connection pooling
- Enhance caching strategies

### Auto-Scaling Triggers
- Message queue depth > 1000
- Processing latency > 5 seconds
- CPU utilization > 80%
- Memory usage > 85%

### Scaling Commands
```bash
# Scale dispatcher instances
docker-compose up -d --scale dispatcher=3

# Check current scaling
docker-compose ps
```

## Performance Tuning

### Database Optimization
- Index frequently queried columns
- Optimize connection pooling
- Tune query performance
- Archive old data

### API Optimization
- Implement smart retry logic
- Batch API calls when possible
- Cache API responses
- Monitor API usage patterns

### System Optimization
- Monitor resource usage
- Tune garbage collection
- Optimize serialization
- Implement efficient algorithms

---

For additional support, contact the development team or refer to the system documentation.