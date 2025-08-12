import json
import logging
from typing import List, Optional
from telegram import Update
from telegram.ext import ContextTypes
from app.repositories.user_repository import UserRepository
from app.repositories.item_repository import ItemRepository
from app.services.user_service import UserService
from app.services.item_service import ItemService
from app.models import User, Item


logger = logging.getLogger(__name__)


class TelegramService:
    """Service layer for Telegram bot business logic."""
    
    def __init__(
        self,
        user_service: UserService,
        item_service: ItemService,
        user_repository: UserRepository,
        item_repository: ItemRepository
    ):
        self.user_service = user_service
        self.item_service = item_service
        self.user_repository = user_repository
        self.item_repository = item_repository
    
    async def handle_start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle /start command."""
        user_id = update.effective_user.id
        user = await self.user_service.create_or_update_user(user_id)
        
        return (
            f"👋 Welcome to TinyVault!\n\n"
            f"Your user ID: {user.id}\n\n"
            "Available commands:\n"
            "/help - Show this help message\n"
            "/save <content> - Save URL or note\n"
            "/list - Show your recent items\n"
            "/get <code> - Retrieve item by code\n"
            "/del <code> - Delete item by code"
        )
    
    async def handle_help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle /help command."""
        return (
            "📚 TinyVault Help\n\n"
            "Commands:\n"
            "• /start - Initialize your account\n"
            "• /help - Show this help message\n"
            "• /save <content> - Save URL or note\n"
            "• /list - Show your 5 most recent items\n"
            "• /get <code> - Retrieve item by short code\n"
            "• /del <code> - Delete item by short code\n\n"
            "Examples:\n"
            "• /save https://example.com\n"
            "• /save My important note\n"
            "• /get abc123\n"
            "• /del abc123"
        )
    
    async def handle_save_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle /save command."""
        if not context.args:
            return "❌ Please provide content to save.\nUsage: /save <content>"
        
        content = ' '.join(context.args)
        user_id = update.effective_user.id
            
            # Get or create user
        user = await self.user_service.create_or_update_user(user_id)
        
        # Validate content
        validation = await self.item_service.validate_item_content(content, None)
        if not validation["valid"]:
            return f"❌ Validation failed: {', '.join(validation['errors'])}"
        
        try:
            # Create item
            item = await self.item_service.create_item(
                owner_user_id=user.id,
                content=content
            )
            
            return (
                f"✅ Item saved successfully!\n\n"
                f"📝 Content: {content[:100]}{'...' if len(content) > 100 else ''}\n"
                f"🔗 Short Code: `{item.short_code}`\n"
                f"📂 Type: {item.kind.title()}\n\n"
                f"Use `/get {item.short_code}` to retrieve it later!"
            )
                
        except Exception as e:
            return f"❌ Failed to save item: {str(e)}"
    
    async def handle_list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle /list command."""
        user_id = update.effective_user.id
        user = await self.user_service.get_user_by_telegram_id(user_id)
        
        if not user:
            return "❌ Please use /start first to initialize your account."
        
        items = await self.item_service.get_user_items(user.id, limit=5)
        
        if not items:
            return "📭 You don't have any saved items yet.\nUse /save <content> to save your first item!"
        
        response = "📋 Your recent items:\n\n"
        for item in items:
            content_preview = item.content[:50] + "..." if len(item.content) > 50 else item.content
            response += (
                f"🔗 `{item.short_code}` ({item.kind.title()})\n"
                f"📝 {content_preview}\n"
                f"📅 {item.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
            )
        
        response += "Use `/get <code>` to retrieve any item."
        return response
    
    async def handle_get_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle /get command."""
        if not context.args:
            return "❌ Please provide a short code.\nUsage: /get <code>"
        
        short_code = context.args[0].strip()
        user_id = update.effective_user.id
        
        # Get user
        user = await self.user_service.get_user_by_telegram_id(user_id)
        if not user:
            return "❌ Please use /start first to initialize your account."
        
        # Get item
        item = await self.item_service.get_item_by_short_code(short_code)
        if not item:
            return f"❌ Item with code `{short_code}` not found."
            
        # Check ownership (optional - could be made public)
        if item.owner_user_id != user.id:
            return f"❌ You don't have permission to access this item."
        
        return (
            f"📋 Item Details\n\n"
            f"🔗 Short Code: `{item.short_code}`\n"
            f"📂 Type: {item.kind.title()}\n"
            f"📅 Created: {item.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"📝 Content:\n{item.content}"
        )
    
    async def handle_delete_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle /del command."""
        if not context.args:
            return "❌ Please provide a short code.\nUsage: /del <code>"
        
        short_code = context.args[0].strip()
        user_id = update.effective_user.id
        
        # Get user
        user = await self.user_service.get_user_by_telegram_id(user_id)
        if not user:
            return "❌ Please use /start first to initialize your account."
        
        # Delete item
        success = await self.item_service.delete_item(short_code, user.id)
        
        if success:
            return f"✅ Item `{short_code}` has been deleted successfully."
        else:
            return f"❌ Failed to delete item `{short_code}`. It may not exist or you don't have permission."
    
    async def handle_unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle unknown commands."""
        return (
            "❓ Unknown command. Use /help to see available commands.\n\n"
            "Available commands:\n"
            "/start - Initialize your account\n"
            "/help - Show help message\n"
            "/save - Save URL or note\n"
            "/list - Show your items\n"
            "/get - Retrieve item\n"
            "/del - Delete item"
        )
    
    async def get_user_statistics(self, telegram_user_id: int) -> dict:
        """Get user statistics for Telegram user."""
        user = await self.user_service.get_user_by_telegram_id(telegram_user_id)
        if not user:
            return {"error": "User not found"}
        
        item_stats = await self.item_service.get_item_stats(user.id)
        user_stats = await self.user_service.get_user_stats(user.id)
        
        return {
            **user_stats,
            **item_stats
        }
    
    async def process_webhook_update(self, update: Update) -> dict:
        """Process incoming webhook update."""
        if not update.message:
            return {"status": "ignored", "reason": "No message in update"}
        
        message = update.message
        user_id = message.from_user.id
        text = message.text or ""
        
        # Update user's last seen
        user = await self.user_service.create_or_update_user(user_id)
        
        # Process commands
        if text.startswith('/'):
            command = text.split()[0].lower()
            context = type('Context', (), {'args': text.split()[1:]})()
            
            if command == '/start':
                response = await self.handle_start_command(update, context)
            elif command == '/help':
                response = await self.handle_help_command(update, context)
            elif command == '/save':
                response = await self.handle_save_command(update, context)
            elif command == '/list':
                response = await self.handle_list_command(update, context)
            elif command == '/get':
                response = await self.handle_get_command(update, context)
            elif command == '/del':
                response = await self.handle_delete_command(update, context)
            else:
                response = await self.handle_unknown_command(update, context)
            
            return {
                "status": "processed",
                "command": command,
                "response": response,
                "user_id": user.id
            }
        
        return {
            "status": "ignored",
            "reason": "Not a command",
            "user_id": user.id
        } 