# Response Delivery & Egress System - Environment Setup

## Overview
This document explains how to set up the environment variables for the Response Delivery & Egress system that handles multi-channel communications (Gmail, WhatsApp, Webhook).

## Quick Setup

### Option 1: Using the Setup Script
```bash
# Navigate to the project root directory
cd /path/to/The-CRM-Digital-FTE-Factory

# Run the setup script
./setup_env.sh
```

### Option 2: Manual Setup
1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your actual credentials (see detailed instructions below)

## Required Environment Variables

### Database Configuration
```env
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
```

### Gmail API Configuration
```env
GMAIL_CREDENTIALS_PATH=./credentials/gmail_credentials.json
GMAIL_TOKEN_PATH=./credentials/gmail_token.json
GMAIL_SENDER_EMAIL=your-email@gmail.com
```

### Twilio WhatsApp Configuration
```env
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890
```

### Rate Limiting Configuration
```env
GMAIL_RATE_LIMIT_PER_MINUTE=250
WHATSAPP_RATE_LIMIT_PER_MINUTE=50
WEBFORM_RATE_LIMIT_PER_MINUTE=1000
```

## Detailed Setup Instructions

### 1. Database Setup
- Install PostgreSQL
- Create a database for the CRM system
- Update `DATABASE_URL` with your connection details

### 2. Gmail API Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API
4. Create credentials (OAuth 2.0 Client ID)
5. Download the credentials JSON file
6. Place it at `./credentials/gmail_credentials.json`
7. Update `GMAIL_SENDER_EMAIL` with your Gmail address

### 3. Twilio WhatsApp Setup
1. Sign up at [Twilio Console](https://console.twilio.com/)
2. Get your Account SID and Auth Token
3. Set up WhatsApp Business API
4. Update the Twilio environment variables

### 4. Rate Limits
Adjust rate limits based on your API quotas:
- Gmail: Typically 250 requests per minute
- WhatsApp: Depends on your Twilio plan
- Webhooks: Based on your receiving server capacity

## Security Best Practices
- Never commit `.env` file to version control
- Store credentials securely
- Rotate credentials periodically
- Use different credentials for dev/prod environments

## Verification
After setup, verify your configuration by running:
```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

required = ['DATABASE_URL', 'GMAIL_SENDER_EMAIL', 'TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN']
missing = [var for var in required if not os.getenv(var)]

if missing:
    print('❌ Missing required environment variables:', missing)
else:
    print('✅ All required environment variables are set')
"
```

## Running the System
```bash
cd phase-5-response-delivery-egress
python scripts/start_dispatcher.py
```

## Troubleshooting
- Check that all required environment variables are set
- Verify API credentials are valid
- Ensure database is accessible
- Check rate limits are appropriate for your use case

For complete setup instructions, see `SETUP_INSTRUCTIONS.md`.