#!/usr/bin/env python3
"""
Telegram Bot Webhook Setup Script

This script helps you set up a secure webhook for your Telegram bot.
Run this script after starting your FastAPI application.
"""

import os
import requests
import json
from urllib.parse import urljoin

def generate_webhook_secret():
    """Generate a secure webhook secret."""
    import secrets
    return secrets.token_urlsafe(32)

def setup_webhook():
    """Set up the Telegram webhook."""
    
    # Configuration
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')
    BASE_URL = "https://51d9cd7d5b4d.ngrok-free.app"
    
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
        print("Please add it to your .env file")
        return False
    
    # Generate webhook secret if not provided
    if not WEBHOOK_SECRET:
        WEBHOOK_SECRET = generate_webhook_secret()
        print(f"🔑 Generated new webhook secret: {WEBHOOK_SECRET}")
        print("Please add this to your .env file as WEBHOOK_SECRET")
    
    # Construct webhook URL
    webhook_url = f"{BASE_URL}/telegram/webhook/{BOT_TOKEN}"
    
    print("🤖 Telegram Bot Webhook Setup")
    print("=" * 50)
    print(f"Bot Token: {BOT_TOKEN[:10]}...")
    print(f"Webhook URL: {webhook_url}")
    print(f"Webhook Secret: {WEBHOOK_SECRET[:10]}...")
    print()
    
    # Test webhook endpoint
    print("🔍 Testing webhook endpoint...")
    try:
        test_response = requests.get(f"{BASE_URL}/telegram/test-webhook")
        if test_response.status_code == 200:
            print("✅ Webhook endpoint is accessible")
        else:
            print(f"❌ Webhook endpoint test failed: {test_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot reach webhook endpoint: {e}")
        return False
    
    # Set webhook with Telegram
    print("\n📡 Setting webhook with Telegram...")
    set_webhook_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    
    webhook_data = {
        "url": webhook_url,
        "secret_token": WEBHOOK_SECRET,
        "allowed_updates": ["message", "callback_query"],
        "drop_pending_updates": True
    }
    
    try:
        response = requests.post(set_webhook_url, json=webhook_data)
        result = response.json()
        
        if result.get("ok"):
            print("✅ Webhook set successfully!")
            print(f"   URL: {result['result']['url']}")
            print(f"   Pending updates dropped: {result['result'].get('drop_pending_updates', False)}")
        else:
            print(f"❌ Failed to set webhook: {result.get('description', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error setting webhook: {e}")
        return False
    
    # Verify webhook
    print("\n🔍 Verifying webhook configuration...")
    try:
        verify_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
        response = requests.get(verify_url)
        result = response.json()
        
        if result.get("ok"):
            webhook_info = result['result']
            print("✅ Webhook verification successful!")
            print(f"   URL: {webhook_info.get('url', 'Not set')}")
            print(f"   Has custom certificate: {webhook_info.get('has_custom_certificate', False)}")
            print(f"   Pending update count: {webhook_info.get('pending_update_count', 0)}")
            print(f"   Last error: {webhook_info.get('last_error_message', 'None')}")
        else:
            print(f"❌ Failed to verify webhook: {result.get('description', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error verifying webhook: {e}")
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Add the webhook secret to your .env file")
    print("2. Send a message to your bot to test")
    print("3. Check the application logs for webhook processing")
    print("4. Monitor the /telegram/webhook-info endpoint")
    
    return True

def test_bot_commands():
    """Test basic bot functionality."""
    print("\n🧪 Testing bot commands...")
    
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not BOT_TOKEN:
        print("❌ Cannot test without bot token")
        return
    
    # Get bot info
    try:
        response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe")
        result = response.json()
        
        if result.get("ok"):
            bot_info = result['result']
            print(f"✅ Bot info retrieved:")
            print(f"   Name: {bot_info['first_name']}")
            print(f"   Username: @{bot_info['username']}")
            print(f"   ID: {bot_info['id']}")
        else:
            print(f"❌ Failed to get bot info: {result.get('description', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error getting bot info: {e}")

if __name__ == "__main__":
    print("🚀 Starting Telegram Bot Webhook Setup...")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Setup webhook
    if setup_webhook():
        # Test bot
        test_bot_commands()
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        exit(1) 