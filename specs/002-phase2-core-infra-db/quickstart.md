# Quickstart Guide: Phase 2: Core Infrastructure & Database

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- PostgreSQL client (for manual database operations)
- Kafka client tools (for topic inspection)

## Setup Instructions

### 1. Clone and Navigate to Project
```bash
cd /phase-2-core-infrastructure-database
```

### 2. Initialize the Infrastructure
Run the initialization script to start services in the correct order:
```bash
./scripts/init_infrastructure.sh
```

This script performs the following sequence:
1. Starts Docker Compose services (PostgreSQL and Kafka/Zookeeper)
2. Runs database migrations to set up tables and extensions
3. Creates Kafka topics with proper configurations

### 3. Manual Setup (Alternative to init script)
If you prefer to set up manually:

#### Start Docker Services
```bash
docker-compose up -d
```

#### Wait for Services to be Ready
```bash
# Wait for PostgreSQL
docker-compose exec postgres pg_isready

# Wait for Kafka
docker-compose exec kafka kafka-topics.sh --bootstrap-server localhost:9092 --list
```

#### Run Database Migrations
```bash
cd postgresql/migrations
alembic upgrade head
```

#### Create Kafka Topics
```bash
# Create inbound events topic
docker-compose exec kafka kafka-topics.sh --create --topic inbound_events --bootstrap-server localhost:9092 --partitions 6 --replication-factor 1

# Create outbound responses topic
docker-compose exec kafka kafka-topics.sh --create --topic outbound_responses --bootstrap-server localhost:9092 --partitions 6 --replication-factor 1

# Create escalations topic
docker-compose exec kafka kafka-topics.sh --create --topic escalations --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
```

### 4. Verify Installation
Check that all services are running properly:

#### Check PostgreSQL Connection
```bash
docker-compose exec postgres psql -U postgres -c "SELECT version();"
```

#### Check Kafka Topics
```bash
docker-compose exec kafka kafka-topics.sh --bootstrap-server localhost:9092 --describe
```

#### Test Database Utility Module
```bash
cd app
python -c "from database_utility import DatabaseUtility; db = DatabaseUtility(); print('Database utility loaded successfully')"
```

## Running Tests
```bash
# Unit tests for database utility
pytest tests/unit/

# Integration tests for Kafka
pytest tests/integration/

# Stress tests (24-hour simulation)
pytest tests/stress/
```

## Development Commands

### Starting Individual Services
```bash
# Start only PostgreSQL
docker-compose up -d postgres

# Start only Kafka
docker-compose up -d kafka zookeeper
```

### Accessing Services
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres

# Access Kafka CLI
docker-compose exec kafka bash

# Check service logs
docker-compose logs -f postgres
docker-compose logs -f kafka
```

### Database Management
```bash
# Create a new migration
cd postgresql/migrations
alembic revision --autogenerate -m "description of changes"

# Run specific migration
alembic upgrade head

# Downgrade to previous version
alembic downgrade -1
```

## Troubleshooting

### If Docker Containers Fail to Start
- Check available disk space
- Verify Docker is running
- Check port availability (5432 for PostgreSQL, 9092 for Kafka)

### If Database Migrations Fail
- Ensure PostgreSQL is fully started before running migrations
- Check database connection parameters in environment files

### If Kafka Topics Don't Create
- Ensure Zookeeper and Kafka are running
- Check Kafka bootstrap server configuration