from typing import AsyncGenerator
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.data.session_manager import get_db_session
from app.repositories.user_repository import UserRepository
from app.repositories.item_repository import ItemRepository
from app.services.user_service import UserService
from app.services.item_service import ItemService
from app.services.telegram_service import TelegramService


# Database session dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with get_db_session() as session:
        yield session


# Repository dependencies
async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """Get user repository instance."""
    return UserRepository(db)


async def get_item_repository(db: AsyncSession = Depends(get_db)) -> ItemRepository:
    """Get item repository instance."""
    return ItemRepository(db)


# Service dependencies
async def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository)
) -> UserService:
    """Get user service instance."""
    return UserService(user_repo)


async def get_item_service(
    item_repo: ItemRepository = Depends(get_item_repository),
    user_repo: UserRepository = Depends(get_user_repository)
) -> ItemService:
    """Get item service instance."""
    return ItemService(item_repo, user_repo)


async def get_telegram_service(
    user_service: UserService = Depends(get_user_service),
    item_service: ItemService = Depends(get_item_service),
    user_repo: UserRepository = Depends(get_user_repository),
    item_repo: ItemRepository = Depends(get_item_repository)
) -> TelegramService:
    """Get telegram service instance."""
    return TelegramService(user_service, item_service, user_repo, item_repo)


# Admin API key dependency
async def verify_admin_api_key(
    x_api_key: str = Header(None, alias="X-API-Key")
) -> str:
    """Verify admin API key."""
    from app.utilities.config import settings
    
    if not x_api_key or x_api_key != settings.admin_api_key:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return x_api_key 