#!/bin/bash
set -e

echo "🚀 Starting TinyVault Project"
echo "============================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok is not installed. Please install ngrok and try again."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️ .env file not found. Creating a sample .env file..."
    echo "# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
WEBHOOK_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    echo "✅ Sample .env file created. Please update it with your actual values."
fi
# activate venv
source .venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Start FastAPI in the background
echo "🌐 Starting FastAPI server..."
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
FASTAPI_PID=$!

# Give FastAPI time to start
echo "⏳ Waiting for FastAPI to start..."
sleep 5

# Start ngrok
echo "🔄 Starting ngrok tunnel..."
ngrok http 8000 > /dev/null &
NGROK_PID=$!

# Wait for ngrok to establish tunnel
echo "⏳ Waiting for ngrok tunnel to be established..."
sleep 5

# Get the ngrok public URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*' | grep -o 'https://[^"]*')

if [ -z "$NGROK_URL" ]; then
    echo "❌ Failed to get ngrok URL. Please check if ngrok is running properly."
    kill $FASTAPI_PID
    kill $NGROK_PID
    exit 1
fi

echo "✅ ngrok tunnel established at: $NGROK_URL"

# Get the bot token from .env file
BOT_TOKEN=$(grep TELEGRAM_BOT_TOKEN .env | cut -d '=' -f2)
WEBHOOK_SECRET=$(grep WEBHOOK_SECRET .env | cut -d '=' -f2)

if [ "$BOT_TOKEN" = "your_bot_token_here" ]; then
    echo "⚠️ Please update your .env file with your actual Telegram bot token."
    echo "🛑 Stopping services..."
    kill $FASTAPI_PID
    kill $NGROK_PID
    exit 1
fi

# Set up the webhook
echo "🔗 Setting up Telegram webhook..."
curl -X POST "https://api.telegram.org/bot$BOT_TOKEN/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "'"$NGROK_URL"'/telegram/webhook/'"$BOT_TOKEN"'",
    "secret_token": "'"$WEBHOOK_SECRET"'",
    "allowed_updates": ["message", "callback_query"],
    "drop_pending_updates": true
  }'

echo -e "\n\n✅ Webhook setup complete!"
echo "📝 Webhook URL: $NGROK_URL/telegram/webhook/$BOT_TOKEN"

# Verify webhook configuration
echo -e "\n🔍 Verifying webhook configuration..."
curl "https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo"

echo -e "\n\n🎉 Setup complete! Your bot should now be responding to messages."
echo "📊 You can check the application logs for more details."
echo "⚠️ Press Ctrl+C to stop the services when done."

# Wait for user to press Ctrl+C
wait $FASTAPI_PID
