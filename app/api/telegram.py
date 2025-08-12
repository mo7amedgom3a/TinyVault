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
        
        # 6. Return success response
        return {"status": "success", "result": result}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
