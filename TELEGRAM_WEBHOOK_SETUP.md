# Telegram Bot Webhook Setup Guide

## Overview
This guide will help you set up a secure Telegram bot webhook for your TinyVault application using FastAPI and ngrok.

## Prerequisites
- ✅ Telegram Bot Token (already in your env.example)
- ✅ ngrok tunnel running at `https://51d9cd7d5b4d.ngrok-free.app`
- ✅ FastAPI application running with Docker
- ✅ Environment variables configured

## Step 1: Environment Configuration

### 1.1 Create/Update .env file
Create a `.env` file in your project root with the following content:

```bash
# Database Configuration
DB_URL=sqlite+aiosqlite:///./data/tinyvault.db

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=8367963568:AAEMCMEc48q6GcFNc-XGUFd3mMliYoRM8xo

# Admin API Configuration
ADMIN_API_KEY=your_secure_admin_api_key_here

# Webhook Security (Required for production)
WEBHOOK_SECRET=your_secure_webhook_secret_here

# Application Configuration
DEBUG=false
```

### 1.2 Generate Webhook Secret
Generate a secure webhook secret using Python:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output and add it to your `.env` file as `WEBHOOK_SECRET`.

## Step 2: Restart Application

After updating the `.env` file, restart your Docker container:

```bash
docker-compose down
docker-compose up -d
```

## Step 3: Verify Webhook Endpoints

### 3.1 Check webhook info
```bash
curl http://127.0.0.1:8000/telegram/webhook-info
```

### 3.2 Test webhook endpoint
```bash
curl http://127.0.0.1:8000/telegram/test-webhook
```

## Step 4: Set Webhook with Telegram

### 4.1 Using BotFather (Recommended)
1. Open Telegram and search for `@BotFather`
2. Send the command: `/setwebhook https://51d9cd7d5b4d.ngrok-free.app/telegram/webhook/8367963568:AAEMCMEc48q6GcFNc-XGUFd3mMliYoRM8xo`

### 4.2 Using Direct API Call
```bash
curl -X POST "https://api.telegram.org/bot8367963568:AAEMCMEc48q6GcFNc-XGUFd3mMliYoRM8xo/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://51d9cd7d5b4d.ngrok-free.app/telegram/webhook/8367963568:AAEMCMEc48q6GcFNc-XGUFd3mMliYoRM8xo",
    "secret_token": "YOUR_WEBHOOK_SECRET_HERE",
    "allowed_updates": ["message", "callback_query"],
    "drop_pending_updates": true
  }'
```

## Step 5: Verify Webhook Configuration

### 5.1 Check webhook status
```bash
curl "https://api.telegram.org/bot8367963568:AAEMCMEc48q6GcFNc-XGUFd3mMliYoRM8xo/getWebhookInfo"
```

### 5.2 Expected response
```json
{
  "ok": true,
  "result": {
    "url": "https://51d9cd7d5b4d.ngrok-free.app/telegram/webhook/8367963568:AAEMCMEc48q6GcFNc-XGUFd3mMliYoRM8xo",
    "has_custom_certificate": false,
    "pending_update_count": 0,
    "last_error_date": 0,
    "last_error_message": "",
    "max_connections": 40,
    "allowed_updates": ["message", "callback_query"]
  }
}
```

## Step 6: Test the Bot

### 6.1 Send a message to your bot
1. Find your bot in Telegram (using the username from BotFather)
2. Send `/start` command
3. Check the application logs for webhook processing

### 6.2 Check application logs
```bash
docker-compose logs -f app
```

## Security Features

### 1. Bot Token Validation
- Bot token is validated in the URL path
- Prevents unauthorized access to webhook endpoint

### 2. Webhook Secret Verification
- Optional webhook secret for additional security
- Validates `X-Telegram-Bot-Api-Secret-Token` header

### 3. Request Validation
- JSON payload validation
- Telegram update format validation
- Comprehensive error logging

### 4. Rate Limiting Considerations
- Built-in request validation
- Error handling for malformed requests

## Troubleshooting

### Common Issues

#### 1. Webhook not receiving updates
- Check ngrok tunnel is active
- Verify webhook URL is correct
- Check application logs for errors

#### 2. 401 Unauthorized errors
- Verify bot token in URL
- Check webhook secret configuration
- Ensure environment variables are loaded

#### 3. 400 Bad Request errors
- Check JSON payload format
- Verify Telegram update structure
- Review application logs

### Debug Commands

#### Check webhook status
```bash
curl "https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo"
```

#### Test webhook endpoint
```bash
curl http://127.0.0.1:8000/telegram/test-webhook
```

#### Check application health
```bash
curl http://127.0.0.1:8000/health
```

## Next Steps

1. **Monitor webhook processing** - Check logs for successful message handling
2. **Test bot commands** - Try `/help`, `/save`, `/list` commands
3. **Set up monitoring** - Monitor webhook health and performance
4. **Production considerations** - Use HTTPS, implement rate limiting, add monitoring

## API Endpoints

- `GET /telegram/webhook-info` - Get webhook configuration information
- `GET /telegram/set-webhook` - Get setup instructions
- `POST /telegram/test-webhook` - Test webhook endpoint
- `POST /telegram/webhook/{bot_token}` - Main webhook endpoint

## Support

If you encounter issues:
1. Check the application logs
2. Verify environment variables
3. Test webhook endpoints
4. Check Telegram Bot API documentation 