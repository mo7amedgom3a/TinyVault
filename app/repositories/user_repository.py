from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.sql import func
from .base_repository import BaseRepository
from app.models import User


class UserRepository(BaseRepository[User]):
    """Repository for User entity operations."""
    
    @property
    def model(self) -> type[User]:
        return User
    
    async def get_by_telegram_id(self, telegram_user_id: int) -> Optional[User]:
        """Get user by Telegram user ID."""
        result = await self.session.execute(
            select(User).where(User.telegram_user_id == telegram_user_id)
        )
        return result.scalar_one_or_none()
    
    async def create_or_update_user(self, telegram_user_id: int) -> User:
        """Create a new user or update last_seen_at if exists."""
        user = await self.get_by_telegram_id(telegram_user_id)
        
        if user is None:
            # Create new user
            user = User(telegram_user_id=telegram_user_id)
            await self.create(user)
        else:
            # Update last_seen_at
            user.last_seen_at = func.current_timestamp()
            await self.update(user)
        
        return user
    
    async def get_users_with_item_count(self) -> List[tuple[User, int]]:
        """Get all users with their item count."""
        from app.models import Item
        
        result = await self.session.execute(
            select(User, func.count(Item.id).label('item_count'))
            .outerjoin(Item, User.id == Item.owner_user_id)
            .group_by(User.id)
        )
        return result.all()
    
    async def get_active_users(self, days: int = 30) -> List[User]:
        """Get users active in the last N days."""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(User).where(User.last_seen_at >= cutoff_date)
        )
        return result.scalars().all()
    
    async def update_last_seen(self, user_id: int) -> bool:
        """Update user's last_seen_at timestamp."""
        result = await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_seen_at=func.current_timestamp())
        )
        return result.rowcount > 0 