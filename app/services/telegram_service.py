import json
import logging
import time
import httpx
from typing import List, Optional, Set, Dict, Any
from telegram import Update, Message, User as TelegramUser, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from app.repositories.user_repository import UserRepository
from app.repositories.item_repository import ItemRepository
from app.services.user_service import UserService
from app.services.item_service import ItemService
from app.models import User, Item
from app.utilities.config import settings


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
        # Track processed updates to ensure idempotency
        self._processed_updates: Set[int] = set()
        # Cleanup old updates every 1000 updates to prevent memory leaks
        self._cleanup_threshold = 1000
        self._last_cleanup = 0
        # Track user conversation states
        self._user_states: Dict[int, Dict[str, Any]] = {}
    
    async def send_telegram_response(self, chat_id: int, text: str, keyboard=None, parse_mode="HTML") -> bool:
        """
        Send response back to Telegram user.
        
        Args:
            chat_id: Telegram chat ID
            text: Message text to send
            keyboard: InlineKeyboardMarkup object (optional)
            parse_mode: Text parsing mode (HTML, Markdown, etc.)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not settings.telegram_bot_token:
                logger.error("Telegram bot token not configured")
                return False
            
            # Prepare the message data
            message_data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            
            # Add keyboard if provided
            if keyboard:
                # Convert keyboard to serializable format
                keyboard_data = self._keyboard_to_dict(keyboard)
                message_data["reply_markup"] = keyboard_data
            
            # Send message via Telegram Bot API
            url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=message_data, timeout=10.0)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        logger.info(f"Message sent successfully to chat {chat_id}")
                        return True
                    else:
                        logger.error(f"Telegram API error: {result.get('description')}")
                        return False
                else:
                    logger.error(f"Failed to send message: HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending Telegram response: {e}")
            return False
    
    def _keyboard_to_dict(self, keyboard) -> dict:
        """Convert InlineKeyboardMarkup to serializable dictionary."""
        try:
            if not keyboard or not hasattr(keyboard, 'inline_keyboard'):
                return {}
            
            keyboard_data = {
                "inline_keyboard": []
            }
            
            for row in keyboard.inline_keyboard:
                row_data = []
                for button in row:
                    button_data = {
                        "text": button.text
                    }
                    if hasattr(button, 'callback_data') and button.callback_data:
                        button_data["callback_data"] = button.callback_data
                    if hasattr(button, 'url') and button.url:
                        button_data["url"] = button.url
                    
                    row_data.append(button_data)
                
                keyboard_data["inline_keyboard"].append(row_data)
            
            return keyboard_data
            
        except Exception as e:
            logger.error(f"Error converting keyboard to dict: {e}")
            return {}
    
    def _cleanup_old_updates(self):
        """Clean up old processed updates to prevent memory leaks."""
        if len(self._processed_updates) > self._cleanup_threshold:
            # Keep only the last 500 updates
            updates_list = list(self._processed_updates)
            self._processed_updates = set(updates_list[-500:])
            logger.info(f"Cleaned up processed updates, kept last 500")
    
    def _is_update_processed(self, update_id: int) -> bool:
        """Check if update has been processed and cleanup if needed."""
        if update_id in self._processed_updates:
            return True
        
        # Cleanup old updates periodically
        if len(self._processed_updates) > self._cleanup_threshold:
            self._cleanup_old_updates()
        
        return False
    
    def _get_user_state(self, user_id: int) -> Dict[str, Any]:
        """Get user's conversation state."""
        if user_id not in self._user_states:
            self._user_states[user_id] = {"state": "idle", "data": {}}
        return self._user_states[user_id]
    
    def _set_user_state(self, user_id: int, state: str, data: Dict[str, Any] = None):
        """Set user's conversation state."""
        if user_id not in self._user_states:
            self._user_states[user_id] = {}
        
        self._user_states[user_id]["state"] = state
        if data:
            self._user_states[user_id]["data"] = data
        else:
            self._user_states[user_id]["data"] = {}
    
    def _clear_user_state(self, user_id: int):
        """Clear user's conversation state."""
        if user_id in self._user_states:
            del self._user_states[user_id]
    
    def _create_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        """Create the main menu keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("📝 Save Item", callback_data="save_item"),
                InlineKeyboardButton("📋 My Items", callback_data="list_items")
            ],
            [
                InlineKeyboardButton("🔍 Get Item", callback_data="get_item"),
                InlineKeyboardButton("🗑️ Delete Item", callback_data="delete_item")
            ],
            [
                InlineKeyboardButton("📊 Statistics", callback_data="stats"),
                InlineKeyboardButton("❓ Help", callback_data="help")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def _create_item_type_keyboard(self) -> InlineKeyboardMarkup:
        """Create keyboard for item type selection."""
        keyboard = [
            [
                InlineKeyboardButton("🔗 URL", callback_data="item_type_url"),
                InlineKeyboardButton("📝 Note", callback_data="item_type_note")
            ],
            [
                InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def _create_confirm_keyboard(self, action: str, item_id: str = None) -> InlineKeyboardMarkup:
        """Create confirmation keyboard."""
        callback_data = f"confirm_{action}"
        if item_id:
            callback_data += f"_{item_id}"
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Yes", callback_data=callback_data),
                InlineKeyboardButton("❌ No", callback_data="cancel_action")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def _create_item_list_keyboard(self, items: List[Item], page: int = 0, items_per_page: int = 5) -> InlineKeyboardMarkup:
        """Create keyboard for item list navigation."""
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        page_items = items[start_idx:end_idx]
        
        keyboard = []
        
        # Add item buttons
        for item in page_items:
            content_preview = item.content[:30] + "..." if len(item.content) > 30 else item.content
            keyboard.append([
                InlineKeyboardButton(
                    f"🔗 {item.short_code} - {content_preview}",
                    callback_data=f"view_item_{item.short_code}"
                )
            ])
        
        # Add navigation buttons
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"page_{page-1}"))
        if end_idx < len(items):
            nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"page_{page+1}"))
        
        if nav_row:
            keyboard.append(nav_row)
        
        # Add back button
        keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")])
        
        return InlineKeyboardMarkup(keyboard)
    
    async def handle_start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> dict:
        """Handle /start command with interactive menu."""
        user_id = update.effective_user.id
        user = await self.user_service.create_or_update_user(user_id)
        
        # Clear any existing state
        self._clear_user_state(user_id)
        
        welcome_text = (
            f"👋 Welcome to TinyVault!\n\n"
            f"Your user ID: {user.id}\n\n"
            "Choose an action from the menu below:"
        )
        
        return {
            "text": welcome_text,
            "keyboard": self._create_main_menu_keyboard()
        }
    
    async def handle_help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> dict:
        """Handle /help command with interactive menu."""
        help_text = (
            "📚 TinyVault Help\n\n"
            "Available commands:\n"
            "• /start - Show main menu\n"
            "• /help - Show this help message\n"
            "• /menu - Show main menu\n"
            "• /cancel - Cancel current operation\n\n"
            "Use the interactive menu below to navigate easily!"
        )
        
        return {
            "text": help_text,
            "keyboard": self._create_main_menu_keyboard()
        }
    
    async def handle_menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> dict:
        """Handle /menu command to show main menu."""
        user_id = update.effective_user.id
        user = await self.user_service.get_user_by_telegram_id(user_id)
        
        if not user:
            return {
                "text": "❌ Please use /start first to initialize your account.",
                "keyboard": None
            }
        
        # Clear any existing state
        self._clear_user_state(user_id)
        
        return {
            "text": "🏠 Main Menu\n\nChoose an action:",
            "keyboard": self._create_main_menu_keyboard()
        }
    
    async def handle_cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> dict:
        """Handle /cancel command to cancel current operation."""
        user_id = update.effective_user.id
        user = await self.user_service.get_user_by_telegram_id(user_id)
        
        if not user:
            return {
                "text": "❌ Please use /start first to initialize your account.",
                "keyboard": None
            }
        
        # Clear user state
        self._clear_user_state(user_id)
        
        return {
            "text": "❌ Operation cancelled. Back to main menu:",
            "keyboard": self._create_main_menu_keyboard()
        }
    
    async def handle_save_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> dict:
        """Handle /save command with interactive flow."""
        # Validate arguments
        is_valid, error_msg = await self._validate_command_args(context, min_args=1)
        if not is_valid:
            return {
                "text": error_msg,
                "keyboard": self._create_main_menu_keyboard()
            }
        
        content = ' '.join(context.args)
        user_id = update.effective_user.id
        
        # Get or create user
        user = await self.user_service.create_or_update_user(user_id)
        
        # Validate content
        validation = await self.item_service.validate_item_content(content, None)
        if not validation["valid"]:
            return {
                "text": f"❌ Validation failed: {', '.join(validation['errors'])}",
                "keyboard": self._create_main_menu_keyboard()
            }
        
        try:
            # Create item
            item = await self.item_service.create_item(
                owner_user_id=user.id,
                content=content
            )
            
            success_text = (
                f"✅ Item saved successfully!\n\n"
                f"📝 Content: {content[:100]}{'...' if len(content) > 100 else ''}\n"
                f"🔗 Short Code: `{item.short_code}`\n"
                f"📂 Type: {item.kind.title()}\n\n"
                f"Use `/get {item.short_code}` to retrieve it later!"
            )
            
            return {
                "text": success_text,
                "keyboard": self._create_main_menu_keyboard()
            }
                
        except Exception as e:
            logger.error(f"Failed to save item: {e}")
            return {
                "text": f"❌ Failed to save item: {str(e)}",
                "keyboard": self._create_main_menu_keyboard()
            }
    
    async def handle_list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> dict:
        """Handle /list command with interactive pagination."""
        # Get user with validation
        is_valid, error_msg, user = await self._get_user_from_update(update)
        if not is_valid:
            return {
                "text": error_msg,
                "keyboard": self._create_main_menu_keyboard()
            }
        
        try:
            items = await self.item_service.get_user_items(user.id, limit=50)  # Get more items for pagination
            
            if not items:
                return {
                    "text": "📭 You don't have any saved items yet.\nUse /save <content> to save your first item!",
                    "keyboard": self._create_main_menu_keyboard()
                }
            
            # Set user state for pagination
            self._set_user_state(user.id, "viewing_items", {"items": [item.short_code for item in items], "page": 0})
            
            response_text = f"📋 Your Items ({len(items)} total)\n\nPage 1 of {(len(items) + 4) // 5}"
            
            return {
                "text": response_text,
                "keyboard": self._create_item_list_keyboard(items, page=0)
            }
            
        except Exception as e:
            logger.error(f"Failed to list items: {e}")
            return {
                "text": "❌ Failed to retrieve your items. Please try again.",
                "keyboard": self._create_main_menu_keyboard()
            }
    
    async def handle_get_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> dict:
        """Handle /get command with interactive confirmation."""
        # Validate arguments
        is_valid, error_msg = await self._validate_command_args(context, min_args=1, max_args=1)
        if not is_valid:
            return {
                "text": error_msg,
                "keyboard": self._create_main_menu_keyboard()
            }
        
        short_code = context.args[0].strip()
        
        # Get user with validation
        is_valid, error_msg, user = await self._get_user_from_update(update)
        if not is_valid:
            return {
                "text": error_msg,
                "keyboard": self._create_main_menu_keyboard()
            }
        
        try:
            # Get item
            item = await self.item_service.get_item_by_short_code(short_code)
            if not item:
                return {
                    "text": f"❌ Item with code `{short_code}` not found.",
                    "keyboard": self._create_main_menu_keyboard()
                }
                
            # Check ownership (optional - could be made public)
            if item.owner_user_id != user.id:
                return {
                    "text": f"❌ You don't have permission to access this item.",
                    "keyboard": self._create_main_menu_keyboard()
                }
            
            item_text = (
                f"📋 Item Details\n\n"
                f"🔗 Short Code: `{item.short_code}`\n"
                f"📂 Type: {item.kind.title()}\n"
                f"📅 Created: {item.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                f"📝 Content:\n{item.content}"
            )
            
            # Add action buttons
            action_keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_item_{item.short_code}"),
                    InlineKeyboardButton("📋 Copy Code", callback_data=f"copy_code_{item.short_code}")
                ],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
            ])
            
            return {
                "text": item_text,
                "keyboard": action_keyboard
            }
            
        except Exception as e:
            logger.error(f"Failed to get item: {e}")
            return {
                "text": "❌ Failed to retrieve item. Please try again.",
                "keyboard": self._create_main_menu_keyboard()
            }
    
    async def handle_delete_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> dict:
        """Handle /del command with interactive confirmation."""
        # Validate arguments
        is_valid, error_msg = await self._validate_command_args(context, min_args=1, max_args=1)
        if not is_valid:
            return {
                "text": error_msg,
                "keyboard": self._create_main_menu_keyboard()
            }
        
        short_code = context.args[0].strip()
        
        # Get user with validation
        is_valid, error_msg, user = await self._get_user_from_update(update)
        if not is_valid:
            return {
                "text": error_msg,
                "keyboard": self._create_main_menu_keyboard()
            }
        
        try:
            # Check if item exists and user owns it
            item = await self.item_service.get_item_by_short_code(short_code)
            if not item:
                return {
                    "text": f"❌ Item with code `{short_code}` not found.",
                    "keyboard": self._create_main_menu_keyboard()
                }
            
            if item.owner_user_id != user.id:
                return {
                    "text": f"❌ You don't have permission to delete this item.",
                    "keyboard": self._create_main_menu_keyboard()
                }
            
            # Set user state for confirmation
            self._set_user_state(user.id, "confirming_delete", {"item_code": short_code})
            
            confirm_text = (
                f"⚠️ Delete Confirmation\n\n"
                f"Are you sure you want to delete item `{short_code}`?\n\n"
                f"📝 Content: {item.content[:100]}{'...' if len(item.content) > 100 else ''}\n\n"
                f"This action cannot be undone."
            )
            
            return {
                "text": confirm_text,
                "keyboard": self._create_confirm_keyboard("delete", short_code)
            }
                
        except Exception as e:
            logger.error(f"Failed to prepare delete: {e}")
            return {
                "text": "❌ Failed to prepare delete operation. Please try again.",
                "keyboard": self._create_main_menu_keyboard()
            }
    
    async def handle_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> dict:
        """Handle /stats command with interactive options."""
        # Get user with validation
        is_valid, error_msg, user = await self._get_user_from_update(update)
        if not is_valid:
            return {
                "text": error_msg,
                "keyboard": self._create_main_menu_keyboard()
            }
        
        try:
            item_stats = await self.item_service.get_item_stats(user.id)
            
            stats_text = (
                f"📊 Your Statistics\n\n"
                f"👤 User ID: {user.id}\n"
                f"📅 Member since: {user.first_seen_at.strftime('%Y-%m-%d')}\n"
                f"🕒 Last seen: {user.last_seen_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                f"📦 Items:\n"
                f"• Total: {item_stats.get('total', 0)}\n"
                f"• URLs: {item_stats.get('urls', 0)}\n"
                f"• Notes: {item_stats.get('notes', 0)}"
            )
            
            # Add action buttons
            stats_keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📋 View All Items", callback_data="list_items"),
                    InlineKeyboardButton("📝 Save New Item", callback_data="save_item")
                ],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
            ])
            
            return {
                "text": stats_text,
                "keyboard": stats_keyboard
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                "text": "❌ Failed to retrieve statistics. Please try again.",
                "keyboard": self._create_main_menu_keyboard()
            }
    
    async def handle_unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> dict:
        """Handle unknown commands with helpful suggestions."""
        return {
            "text": (
                "❓ Unknown command. Here are some helpful options:\n\n"
                "Available commands:\n"
                "• /start - Initialize your account\n"
                "• /help - Show help message\n"
                "• /menu - Show main menu\n"
                "• /cancel - Cancel current operation"
            ),
            "keyboard": self._create_main_menu_keyboard()
        }
    
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
        """Process incoming webhook update with idempotent handling."""
        if not update.message and not update.callback_query:
            return {"status": "ignored", "reason": "No message or callback query in update"}
        
        # Check if this update has already been processed (idempotency)
        update_id = update.update_id
        if self._is_update_processed(update_id):
            logger.info(f"Update {update_id} already processed, skipping")
            return {"status": "ignored", "reason": "Already processed", "update_id": update_id}
        
        try:
            # Handle callback queries (inline keyboard buttons)
            if update.callback_query:
                return await self._process_callback_query(update)
            
            # Handle regular messages
            if update.message:
                return await self._process_message(update)
            
            return {"status": "ignored", "reason": "Unsupported update type", "update_id": update_id}
            
        except Exception as e:
            logger.error(f"Error processing update {update_id}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "update_id": update_id
            }
    
    async def _process_callback_query(self, update: Update) -> dict:
        """Process callback query from inline keyboard."""
        callback_query = update.callback_query
        user_id = callback_query.from_user.id
        callback_data = callback_query.data
        
        logger.info(f"Processing callback query from user {user_id}: {callback_data}")
        
        try:
            # Update user's last seen
            user = await self.user_service.create_or_update_user(user_id)
            
            # Handle the callback query
            result = await self.handle_callback_query(update, callback_data)
            
            # Mark update as processed
            self._processed_updates.add(update.update_id)
            
            logger.info(f"Callback query processed successfully for user {user.id}")
            
            return {
                "status": "processed",
                "type": "callback_query",
                "callback_data": callback_data,
                "text": result.get("text", ""),
                "keyboard": result.get("keyboard"),
                "user_id": user.id,
                "update_id": update.update_id
            }
            
        except Exception as e:
            logger.error(f"Error processing callback query: {e}")
            return {
                "status": "error",
                "error": str(e),
                "update_id": update.update_id
            }
    
    async def _process_message(self, update: Update) -> dict:
        """Process regular message."""
        message = update.message
        user_id = message.from_user.id
        text = message.text or ""
        
        logger.info(f"Processing message from user {user_id}: {text[:50]}{'...' if len(text) > 50 else ''}")
        
        try:
            # Update user's last seen
            user = await self.user_service.create_or_update_user(user_id)
            logger.info(f"User {user.id} (Telegram: {user_id}) processed")
            
            # Process commands
            if text.startswith('/'):
                result = await self._process_command(update, text)
            else:
                # Handle text messages (for interactive flows)
                result = await self.handle_text_message(update, text)
            
            # Mark update as processed
            self._processed_updates.add(update.update_id)
            
            logger.info(f"Message processed successfully for user {user.id}")
            
            return {
                "status": "processed",
                "type": "message",
                "text": text,
                "command": text.split()[0] if text.startswith('/') else None,
                "response_text": result.get("text", ""),
                "keyboard": result.get("keyboard"),
                "user_id": user.id,
                "update_id": update.update_id
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "status": "error",
                "error": str(e),
                "update_id": update.update_id
            }
    
    async def _process_command(self, update: Update, text: str) -> dict:
        """Process command messages."""
        command = text.split()[0].lower()
        context = type('Context', (), {'args': text.split()[1:]})()
        
        logger.info(f"Processing command: {command} with args: {context.args}")
        
        if command == '/start':
            response = await self.handle_start_command(update, context)
        elif command == '/help':
            response = await self.handle_help_command(update, context)
        elif command == '/menu':
            response = await self.handle_menu_command(update, context)
        elif command == '/cancel':
            response = await self.handle_cancel_command(update, context)
        elif command == '/save':
            response = await self.handle_save_command(update, context)
        elif command == '/list':
            response = await self.handle_list_command(update, context)
        elif command == '/get':
            response = await self.handle_get_command(update, context)
        elif command == '/del':
            response = await self.handle_delete_command(update, context)
        elif command == '/stats':
            response = await self.handle_stats_command(update, context)
        else:
            response = await self.handle_unknown_command(update, context)
        
        return response
    
    async def _validate_command_args(self, context: ContextTypes.DEFAULT_TYPE, min_args: int = 0, max_args: int = None) -> tuple[bool, str]:
        """Validate command arguments."""
        args = context.args or []
        
        if len(args) < min_args:
            return False, f"❌ Too few arguments. Expected at least {min_args}."
        
        if max_args is not None and len(args) > max_args:
            return False, f"❌ Too many arguments. Expected at most {max_args}."
        
        return True, ""
    
    async def _get_user_from_update(self, update: Update) -> tuple[bool, str, Optional[User]]:
        """Get user from update with error handling."""
        try:
            user_id = update.effective_user.id
            user = await self.user_service.get_user_by_telegram_id(user_id)
            
            if not user:
                return False, "❌ Please use /start first to initialize your account.", None
            
            return True, "", user
            
        except Exception as e:
            logger.error(f"Error getting user from update: {e}")
            return False, "❌ Error retrieving user information.", None
    
    async def handle_callback_query(self, update: Update, callback_data: str) -> dict:
        """Handle callback query from inline keyboards."""
        user_id = update.effective_user.id
        user = await self.user_service.get_user_by_telegram_id(user_id)
        
        if not user:
            return {
                "text": "❌ Please use /start first to initialize your account.",
                "keyboard": None
            }
        
        try:
            if callback_data == "main_menu":
                self._clear_user_state(user_id)
                return {
                    "text": "🏠 Main Menu\n\nChoose an action:",
                    "keyboard": self._create_main_menu_keyboard()
                }
            
            elif callback_data == "save_item":
                self._set_user_state(user_id, "waiting_for_content", {"action": "save"})
                return {
                    "text": (
                        "📝 Save Item\n\n"
                        "Please send me the content you want to save:\n\n"
                        "• For URLs: Just paste the URL\n"
                        "• For notes: Type your note\n\n"
                        "Use /cancel to go back to menu"
                    ),
                    "keyboard": InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Cancel", callback_data="main_menu")]
                    ])
                }
            
            elif callback_data == "list_items":
                return await self.handle_list_command(update, type('Context', (), {'args': []})())
            
            elif callback_data == "get_item":
                self._set_user_state(user_id, "waiting_for_code", {"action": "get"})
                return {
                    "text": (
                        "🔍 Get Item\n\n"
                        "Please send me the short code of the item you want to retrieve.\n\n"
                        "Use /cancel to go back to menu"
                    ),
                    "keyboard": InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Cancel", callback_data="main_menu")]
                    ])
                }
            
            elif callback_data == "delete_item":
                self._set_user_state(user_id, "waiting_for_delete_code", {"action": "delete"})
                return {
                    "text": (
                        "🗑️ Delete Item\n\n"
                        "Please send me the short code of the item you want to delete.\n\n"
                        "⚠️ This action cannot be undone!\n\n"
                        "Use /cancel to go back to menu"
                    ),
                    "keyboard": InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Cancel", callback_data="main_menu")]
                    ])
                }
            
            elif callback_data == "stats":
                return await self.handle_stats_command(update, type('Context', (), {'args': []})())
            
            elif callback_data == "help":
                return await self.handle_help_command(update, type('Context', (), {'args': []})())
            
            elif callback_data.startswith("view_item_"):
                short_code = callback_data.replace("view_item_", "")
                return await self.handle_get_command(update, type('Context', (), {'args': [short_code]})())
            
            elif callback_data.startswith("delete_item_"):
                short_code = callback_data.replace("delete_item_", "")
                return await self.handle_delete_command(update, type('Context', (), {'args': [short_code]})())
            
            elif callback_data.startswith("confirm_delete_"):
                short_code = callback_data.replace("confirm_delete_", "")
                return await self._confirm_delete_item(user, short_code)
            
            elif callback_data.startswith("copy_code_"):
                short_code = callback_data.replace("copy_code_", "")
                return {
                    "text": f"📋 Copy this code: `{short_code}`",
                    "keyboard": InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
                    ])
                }
            
            elif callback_data.startswith("page_"):
                page = int(callback_data.replace("page_", ""))
                return await self._show_items_page(user, page)
            
            elif callback_data == "cancel_action":
                self._clear_user_state(user_id)
                return {
                    "text": "❌ Action cancelled. Back to main menu:",
                    "keyboard": self._create_main_menu_keyboard()
                }
            
            else:
                return {
                    "text": "❓ Unknown action. Back to main menu:",
                    "keyboard": self._create_main_menu_keyboard()
                }
                
        except Exception as e:
            logger.error(f"Error handling callback query: {e}")
            return {
                "text": "❌ An error occurred. Back to main menu:",
                "keyboard": self._create_main_menu_keyboard()
            }
    
    async def _confirm_delete_item(self, user: User, short_code: str) -> dict:
        """Confirm and execute item deletion."""
        try:
            # Delete item
            success = await self.item_service.delete_item(short_code, user.id)
            
            if success:
                self._clear_user_state(user.telegram_user_id)
                return {
                    "text": f"✅ Item `{short_code}` has been deleted successfully.",
                    "keyboard": self._create_main_menu_keyboard()
                }
            else:
                return {
                    "text": f"❌ Failed to delete item `{short_code}`. It may not exist or you don't have permission.",
                    "keyboard": self._create_main_menu_keyboard()
                }
                
        except Exception as e:
            logger.error(f"Failed to delete item: {e}")
            return {
                "text": "❌ Failed to delete item. Please try again.",
                "keyboard": self._create_main_menu_keyboard()
            }
    
    async def _show_items_page(self, user: User, page: int) -> dict:
        """Show a specific page of items."""
        try:
            items = await self.item_service.get_user_items(user.id, limit=50)
            
            if not items:
                return {
                    "text": "📭 You don't have any saved items yet.",
                    "keyboard": self._create_main_menu_keyboard()
                }
            
            total_pages = (len(items) + 4) // 5
            if page < 0 or page >= total_pages:
                page = 0
            
            # Update user state
            self._set_user_state(user.telegram_user_id, "viewing_items", {"items": [item.short_code for item in items], "page": page})
            
            response_text = f"📋 Your Items ({len(items)} total)\n\nPage {page + 1} of {total_pages}"
            
            return {
                "text": response_text,
                "keyboard": self._create_item_list_keyboard(items, page=page)
            }
            
        except Exception as e:
            logger.error(f"Failed to show items page: {e}")
            return {
                "text": "❌ Failed to retrieve items. Please try again.",
                "keyboard": self._create_main_menu_keyboard()
            }
    
    async def handle_text_message(self, update: Update, text: str) -> dict:
        """Handle text messages based on user state."""
        user_id = update.effective_user.id
        user_state = self._get_user_state(user_id)
        
        # Get the user from the service
        user = await self.user_service.get_user_by_telegram_id(user_id)
        if not user:
            return {
                "text": "❌ Please use /start first to initialize your account.",
                "keyboard": self._create_main_menu_keyboard()
            }
        
        if user_state["state"] == "waiting_for_content":
            # User is trying to save an item
            return await self._handle_save_content(user, text)
        
        elif user_state["state"] == "waiting_for_code":
            # User is trying to get an item
            return await self._handle_get_by_code(user, text)
        
        elif user_state["state"] == "waiting_for_delete_code":
            # User is trying to delete an item
            return await self._handle_delete_by_code(user, text)
        
        else:
            # Default response for text messages
            return {
                "text": (
                    "💬 I received your message, but I'm not sure what you'd like me to do.\n\n"
                    "Use /start to see the main menu or /help for available commands."
                ),
                "keyboard": self._create_main_menu_keyboard()
            }
    
    async def _handle_save_content(self, user: User, content: str) -> dict:
        """Handle saving content from text message."""
        try:
            # Validate content
            validation = await self.item_service.validate_item_content(content, None)
            if not validation["valid"]:
                return {
                    "text": f"❌ Validation failed: {', '.join(validation['errors'])}",
                    "keyboard": self._create_main_menu_keyboard()
                }
            
            # Create item
            item = await self.item_service.create_item(
                owner_user_id=user.id,
                content=content
            )
            
            # Clear user state
            self._clear_user_state(user.telegram_user_id)
            
            success_text = (
                f"✅ Item saved successfully!\n\n"
                f"📝 Content: {content[:100]}{'...' if len(content) > 100 else ''}\n"
                f"🔗 Short Code: `{item.short_code}`\n"
                f"📂 Type: {item.kind.title()}\n\n"
                f"Use `/get {item.short_code}` to retrieve it later!"
            )
            
            return {
                "text": success_text,
                "keyboard": self._create_main_menu_keyboard()
            }
                
        except Exception as e:
            logger.error(f"Failed to save item: {e}")
            return {
                "text": f"❌ Failed to save item: {str(e)}",
                "keyboard": self._create_main_menu_keyboard()
            }
    
    async def _handle_get_by_code(self, user: User, short_code: str) -> dict:
        """Handle getting item by code from text message."""
        try:
            # Get item
            item = await self.item_service.get_item_by_short_code(short_code.strip())
            if not item:
                return {
                    "text": f"❌ Item with code `{short_code}` not found.",
                    "keyboard": self._create_main_menu_keyboard()
                }
                
            # Check ownership
            if item.owner_user_id != user.id:
                return {
                    "text": f"❌ You don't have permission to access this item.",
                    "keyboard": self._create_main_menu_keyboard()
                }
            
            # Clear user state
            self._clear_user_state(user.telegram_user_id)
            
            item_text = (
                f"📋 Item Details\n\n"
                f"🔗 Short Code: `{item.short_code}`\n"
                f"📂 Type: {item.kind.title()}\n"
                f"📅 Created: {item.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                f"📝 Content:\n{item.content}"
            )
            
            # Add action buttons
            action_keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_item_{item.short_code}"),
                    InlineKeyboardButton("📋 Copy Code", callback_data=f"copy_code_{item.short_code}")
                ],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
            ])
            
            return {
                "text": item_text,
                "keyboard": action_keyboard
            }
            
        except Exception as e:
            logger.error(f"Failed to get item: {e}")
            return {
                "text": "❌ Failed to retrieve item. Please try again.",
                "keyboard": self._create_main_menu_keyboard()
            }
    
    async def _handle_delete_by_code(self, user: User, short_code: str) -> dict:
        """Handle deleting item by code from text message."""
        try:
            # Check if item exists and user owns it
            item = await self.item_service.get_item_by_short_code(short_code.strip())
            if not item:
                return {
                    "text": f"❌ Item with code `{short_code}` not found.",
                    "keyboard": self._create_main_menu_keyboard()
                }
            
            if item.owner_user_id != user.id:
                return {
                    "text": f"❌ You don't have permission to delete this item.",
                    "keyboard": self._create_main_menu_keyboard()
                }
            
            # Set user state for confirmation
            self._set_user_state(user.telegram_user_id, "confirming_delete", {"item_code": short_code.strip()})
            
            confirm_text = (
                f"⚠️ Delete Confirmation\n\n"
                f"Are you sure you want to delete item `{short_code}`?\n\n"
                f"📝 Content: {item.content[:100]}{'...' if len(item.content) > 100 else ''}\n\n"
                f"This action cannot be undone."
            )
            
            return {
                "text": confirm_text,
                "keyboard": self._create_confirm_keyboard("delete", short_code.strip())
            }
                
        except Exception as e:
            logger.error(f"Failed to prepare delete: {e}")
            return {
                "text": "❌ Failed to prepare delete operation. Please try again.",
                "keyboard": self._create_main_menu_keyboard()
            } 