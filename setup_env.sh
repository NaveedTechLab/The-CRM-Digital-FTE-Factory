#!/bin/bash
# setup_env.sh - Quick setup script for environment configuration

echo "==========================================="
echo "Response Delivery & Egress System Setup"
echo "==========================================="

# Check if .env file exists
if [ -f ".env" ]; then
    echo "⚠️  Warning: .env file already exists!"
    echo "Do you want to overwrite it? (y/N): "
    read -r response
    if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
fi

# Copy the example file
cp .env.example .env
echo "✅ Copied .env.example to .env"

# Check for required tools
echo ""
echo "🔍 Checking for required tools..."

if command -v python3 &> /dev/null; then
    echo "✅ Python3 found"
else
    echo "❌ Python3 not found. Please install Python3."
    exit 1
fi

if command -v pip &> /dev/null; then
    echo "✅ Pip found"
else
    echo "❌ Pip not found. Please install Pip."
    exit 1
fi

# Install required packages
echo ""
echo "📦 Installing required packages..."
pip install python-dotenv psycopg2-binary redis kafka-python aiokafka

# Check if credentials directory exists
if [ ! -d "./credentials" ]; then
    mkdir -p ./credentials
    echo "📁 Created credentials directory"
fi

echo ""
echo "==========================================="
echo "Setup Complete! Now configure your .env file:"
echo "==========================================="
echo ""
echo "1. Edit the .env file with your actual credentials:"
echo "   nano .env    # or use your preferred editor"
echo ""
echo "2. Add your database connection string:"
echo "   DATABASE_URL=postgresql://username:password@localhost:5432/database_name"
echo ""
echo "3. Add your Gmail credentials:"
echo "   - Download Gmail credentials JSON from Google Cloud Console"
echo "   - Place it at ./credentials/gmail_credentials.json"
echo "   - Set GMAIL_SENDER_EMAIL=your-email@gmail.com"
echo ""
echo "4. Add your Twilio credentials:"
echo "   - Get from Twilio Console"
echo "   - Set TWILIO_ACCOUNT_SID=your_sid"
echo "   - Set TWILIO_AUTH_TOKEN=your_token"
echo "   - Set TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890"
echo ""
echo "5. Run the application:"
echo "   cd phase-5-response-delivery-egress"
echo "   python scripts/start_dispatcher.py"
echo ""
echo "For detailed instructions, see SETUP_INSTRUCTIONS.md"
echo "==========================================="