# Environment Setup Instructions

## Step 1: Copy the Example Environment File

First, copy the example environment file to create your actual `.env` file:

```bash
cp .env.example .env
```

## Step 2: Configure Database Settings

Edit the `.env` file and update the database configuration:

```env
DATABASE_URL=postgresql://your_username:your_password@localhost:5432/your_database_name
```

Replace `your_username`, `your_password`, and `your_database_name` with your actual PostgreSQL credentials.

## Step 3: Configure Gmail API

### 3.1 Create Gmail Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API
4. Create credentials (OAuth 2.0 Client ID)
5. Download the credentials JSON file
6. Place it in `./credentials/gmail_credentials.json`

### 3.2 Set Up Gmail Authentication
```env
GMAIL_CREDENTIALS_PATH=./credentials/gmail_credentials.json
GMAIL_TOKEN_PATH=./credentials/gmail_token.json  # This will be created automatically
GMAIL_SENDER_EMAIL=your_actual_gmail_address@gmail.com
```

## Step 4: Configure Twilio WhatsApp

### 4.1 Get Twilio Credentials
1. Sign up at [Twilio Console](https://console.twilio.com/)
2. Get your Account SID and Auth Token
3. Get your WhatsApp number (starts with `whatsapp:`)

### 4.2 Update Environment Variables
```env
TWILIO_ACCOUNT_SID=your_actual_account_sid
TWILIO_AUTH_TOKEN=your_actual_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890  # Replace with your actual WhatsApp number
```

## Step 5: Configure Kafka (if not using local defaults)

If you're using a different Kafka setup:
```env
KAFKA_BOOTSTRAP_SERVERS=your_kafka_server:9092
```

## Step 6: Configure Redis (if not using local defaults)

If you're using a different Redis setup:
```env
REDIS_URL=redis://your_redis_server:6379
```

## Step 7: Adjust Rate Limits (Optional)

You can adjust the rate limits based on your API quotas:
```env
GMAIL_RATE_LIMIT_PER_MINUTE=250  # Gmail API limit
WHATSAPP_RATE_LIMIT_PER_MINUTE=50  # Twilio WhatsApp limit
WEBFORM_RATE_LIMIT_PER_MINUTE=1000  # Webhook delivery limit
```

## Step 8: Final Environment File

Your final `.env` file should look something like this:

```env
# Database Configuration
DATABASE_URL=postgresql://myuser:mypassword@localhost:5432/mycrm_db

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_CONSUMER_GROUP_ID=response_dispatcher_group

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Gmail API Configuration
GMAIL_CREDENTIALS_PATH=./credentials/gmail_credentials.json
GMAIL_TOKEN_PATH=./credentials/gmail_token.json
GMAIL_SENDER_EMAIL=user@gmail.com

# Twilio WhatsApp Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890

# Rate Limiting Configuration
GMAIL_RATE_LIMIT_PER_MINUTE=250
WHATSAPP_RATE_LIMIT_PER_MINUTE=50
WEBFORM_RATE_LIMIT_PER_MINUTE=1000

# Application Settings
APP_NAME=response-delivery-service
LOG_LEVEL=INFO
DEBUG=false

# Delivery Configuration
DELIVERY_TIMEOUT_SECONDS=30
MAX_RETRY_ATTEMPTS=3
```

## Step 9: Security Best Practices

1. **Never commit the `.env` file** to version control
2. Add `.env` to your `.gitignore` file
3. Store credentials securely in a password manager
4. Rotate credentials periodically
5. Use different credentials for development and production

## Step 10: Verification

After setting up your `.env` file, you can verify the configuration by running:

```bash
# Check if environment variables are loaded correctly
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

print('DATABASE_URL loaded:', bool(os.getenv('DATABASE_URL')))
print('GMAIL_SENDER_EMAIL:', os.getenv('GMAIL_SENDER_EMAIL'))
print('TWILIO_ACCOUNT_SID length:', len(os.getenv('TWILIO_ACCOUNT_SID', '')))
print('All required env vars present:', all([
    os.getenv('DATABASE_URL'),
    os.getenv('GMAIL_SENDER_EMAIL'),
    os.getenv('TWILIO_ACCOUNT_SID'),
    os.getenv('TWILIO_AUTH_TOKEN')
]))
"
```

## Common Issues and Solutions

### Issue: Gmail API authentication fails
**Solution:** Make sure you've properly set up OAuth 2.0 credentials and granted the necessary scopes

### Issue: Twilio authentication fails
**Solution:** Verify your Account SID and Auth Token are correct and your WhatsApp number is properly configured

### Issue: Database connection fails
**Solution:** Check your PostgreSQL server is running and credentials are correct

### Issue: Rate limiting too restrictive
**Solution:** Adjust the rate limit values based on your actual API quotas