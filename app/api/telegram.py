from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from app.services.telegram_service import TelegramService
from app.utilities.dependencies import get_telegram_service
from app.utilities.config import settings
import logging
import hashlib
import hmac
import time

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/telegram", tags=["telegram"])

@router.post("/webhook/{bot_token}")
async def telegram_webhook(
    bot_token: str,
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(None),
    telegram_service: TelegramService = Depends(get_telegram_service)
):
    """
    Handle Telegram webhook updates with enhanced security.
    
    Security features:
    1. Bot token validation in URL path
    2. Webhook secret verification via header
    3. Rate limiting considerations
    4. Request validation
    """
    try:
        # 1. Validate bot token in URL path
        if bot_token != settings.telegram_bot_token:
            logger.warning(f"Invalid bot token attempt: {bot_token}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid bot token"
            )
        
        # 2. Verify webhook secret if configured
        if settings.webhook_secret and settings.webhook_secret != "not_configured":
            if not x_telegram_bot_api_secret_token:
                logger.warning("Missing webhook secret header")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing webhook secret"
                )
            
            if x_telegram_bot_api_secret_token != settings.webhook_secret:
                logger.warning("Invalid webhook secret")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook secret"
                )
        
        # 3. Parse and validate the update
        try:
            update_data = await request.json()
        except Exception as e:
            logger.error(f"Failed to parse JSON: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload"
            )
        
        # 4. Import here to avoid circular imports
        from telegram import Update
        try:
            update = Update.de_json(update_data, None)
        except Exception as e:
            logger.error(f"Failed to parse Telegram update: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Telegram update format"
            )
        
        # 5. Process the update
        result = await telegram_service.process_webhook_update(update)
        
        logger.info(f"Processed webhook update successfully: {result}")
        
        # 6. Send response back to Telegram user
        if result.get("status") == "processed":
            try:
                # Extract chat ID from the update
                chat_id = None
                if update.message:
                    chat_id = update.message.chat.id
                elif update.callback_query:
                    chat_id = update.callback_query.message.chat.id
                
                if chat_id:
                    # Get response text and keyboard
                    response_text = result.get("response_text", result.get("text", "No response"))
                    keyboard = result.get("keyboard")
                    
                    # Send the response back to Telegram
                    success = await telegram_service.send_telegram_response(
                        chat_id=chat_id,
                        text=response_text,
                        keyboard=keyboard
                    )
                    
                    if success:
                        logger.info(f"Response sent successfully to chat {chat_id}")
                    else:
                        logger.error(f"Failed to send response to chat {chat_id}")
                else:
                    logger.warning("Could not determine chat ID for response")
                    
            except Exception as e:
                logger.error(f"Error sending Telegram response: {e}")
        
        # 7. Return success response with serializable data
        # Extract only the necessary data, avoiding Telegram objects
        response_data = {
            "status": "success",
            "update_id": result.get("update_id"),
            "user_id": result.get("user_id"),
            "type": result.get("type"),
            "command": result.get("command", result.get("callback_data")),
            "message": result.get("text", result.get("response_text", "No message")),
            "has_keyboard": result.get("keyboard") is not None,
            "keyboard_info": _extract_keyboard_info(result.get("keyboard")) if result.get("keyboard") else None,
            "telegram_response_sent": chat_id is not None
        }
        
        return response_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/test-command/{bot_token}")
async def test_telegram_command(
    bot_token: str,
    command: str,
    user_id: int = 123456789,  # Default test user ID
    telegram_service: TelegramService = Depends(get_telegram_service)
):
    """
    Test endpoint to simulate Telegram commands without sending actual messages.
    Useful for development and testing.
    """
    try:
        # Validate bot token
        if bot_token != settings.telegram_bot_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid bot token"
            )
        
        # Create a mock update object
        from telegram import Update, Message, User as TelegramUser
        
        # Mock user
        mock_telegram_user = TelegramUser(
            id=user_id,
            is_bot=False,
            first_name="Test",
            last_name="User",
            username="testuser"
        )
        
        # Mock message
        mock_message = Message(
            message_id=1,
            date=time.time(),
            chat=None,  # Not needed for our use case
            from_user=mock_telegram_user,
            text=command
        )
        
        # Mock update
        mock_update = Update(
            update_id=int(time.time()),  # Use timestamp as update ID
            message=mock_message
        )
        
        # Process the mock update
        result = await telegram_service.process_webhook_update(mock_update)
        
        # Extract response data
        response_text = result.get("response_text", result.get("text", "No response text"))
        keyboard = result.get("keyboard")
        
        # Send response back to Telegram if this is a real user ID
        telegram_response_sent = False
        if user_id != 123456789:  # Default test user ID
            try:
                success = await telegram_service.send_telegram_response(
                    chat_id=user_id,
                    text=response_text,
                    keyboard=keyboard
                )
                telegram_response_sent = success
                if success:
                    logger.info(f"Test response sent successfully to user {user_id}")
                else:
                    logger.error(f"Failed to send test response to user {user_id}")
            except Exception as e:
                logger.error(f"Error sending test response: {e}")
        
        return {
            "status": "success",
            "command": command,
            "result": {
                "text": response_text,
                "has_keyboard": keyboard is not None,
                "keyboard_buttons": _extract_keyboard_info(keyboard) if keyboard else None
            },
            "user_id": user_id,
            "telegram_response_sent": telegram_response_sent
        }
        
    except Exception as e:
        logger.error(f"Error testing command: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error testing command: {str(e)}"
        )


def _extract_keyboard_info(keyboard):
    """Extract keyboard information for testing purposes."""
    if not keyboard:
        return None
    
    try:
        # Extract button information from InlineKeyboardMarkup
        buttons_info = []
        for row in keyboard.inline_keyboard:
            row_buttons = []
            for button in row:
                row_buttons.append({
                    "text": button.text,
                    "callback_data": button.callback_data
                })
            buttons_info.append(row_buttons)
        
        return {
            "type": "inline_keyboard",
            "rows": len(buttons_info),
            "buttons": buttons_info
        }
    except Exception as e:
        logger.error(f"Error extracting keyboard info: {e}")
        return {"error": "Could not extract keyboard info"}
