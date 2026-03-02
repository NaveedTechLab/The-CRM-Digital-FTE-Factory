# Quickstart Guide: Phase 1: Incubation & Prototyping

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL client (for local development)

## Setup Instructions

### 1. Clone and Navigate to Project
```bash
cd /phase-1-incubation-prototype
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables
Copy the example environment file and configure your settings:
```bash
cp .env.example .env
# Edit .env with your specific configuration
```

### 4. Initialize Local PostgreSQL Database
Start the database using Docker Compose:
```bash
docker-compose up -d
```

### 5. Run Database Migrations
```bash
python -m app.database.migrate
```

### 6. Start the FastAPI Application
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Running Tests
```bash
pytest tests/
```

## Mock Channel Testing

### Gmail Mock Interface
Send a POST request to:
```
POST http://localhost:8000/api/v1/channels/gmail/webhook
```

### WhatsApp Mock Interface
Send a POST request to:
```
POST http://localhost:8000/api/v1/channels/whatsapp/webhook
```

### Web Form Mock Interface
Send a POST request to:
```
POST http://localhost:8000/api/v1/channels/webform/webhook
```

## Sample Request Format
```json
{
  "customer_email": "customer@example.com",
  "customer_name": "John Doe",
  "message": "I have a question about your product...",
  "channel": "gmail"
}
```

## Development Commands

### Running with Auto-reload
```bash
uvicorn app.main:app --reload
```

### Running Specific Test Suite
```bash
pytest tests/unit/
pytest tests/integration/
```

### Checking Code Quality
```bash
flake8 app/
black --check app/
```