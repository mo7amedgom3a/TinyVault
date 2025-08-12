from typing import List, Optional
from app.repositories.user_repository import UserRepository
from app.models import User
from app.schemas import UserCreate, UserUpdate


class UserService:
    """Service layer for user business logic."""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return await self.user_repository.get_by_id(user_id)
    
    async def get_user_by_telegram_id(self, telegram_user_id: int) -> Optional[User]:
        """Get user by Telegram user ID."""
        return await self.user_repository.get_by_telegram_id(telegram_user_id)
    
    async def create_or_update_user(self, telegram_user_id: int) -> User:
        """Create a new user or update last_seen_at if exists."""
        return await self.user_repository.create_or_update_user(telegram_user_id)
    
    async def get_all_users_with_item_count(self) -> List[tuple[User, int]]:
        """Get all users with their item count."""
        return await self.user_repository.get_users_with_item_count()
    
    async def get_active_users(self, days: int = 30) -> List[User]:
        """Get users active in the last N days."""
        return await self.user_repository.get_active_users(days)
    
    async def update_user_last_seen(self, user_id: int) -> bool:
        """Update user's last_seen_at timestamp."""
        return await self.user_repository.update_last_seen(user_id)
    
    async def get_user_stats(self, user_id: int) -> dict:
        """Get user statistics."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return {"error": "User not found"}
        
        return {
            "id": user.id,
            "telegram_user_id": user.telegram_user_id,
            "first_seen_at": user.first_seen_at,
            "last_seen_at": user.last_seen_at,
            "total_items": len(user.items)
        }
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete a user and all associated items."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        await self.user_repository.delete(user)
        return True 