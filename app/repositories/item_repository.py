from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.sql import func
from .base_repository import BaseRepository
from app.models import Item


class ItemRepository(BaseRepository[Item]):
    """Repository for Item entity operations."""
    
    @property
    def model(self) -> type[Item]:
        return Item
    
    async def get_by_short_code(self, short_code: str) -> Optional[Item]:
        """Get item by short code."""
        result = await self.session.execute(
            select(Item).where(
                and_(
                    Item.short_code == short_code,
                    Item.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_owner_id(self, owner_user_id: int, limit: int = 10) -> List[Item]:
        """Get items by owner user ID, excluding deleted items."""
        result = await self.session.execute(
            select(Item)
            .where(
                and_(
                    Item.owner_user_id == owner_user_id,
                    Item.deleted_at.is_(None)
                )
            )
            .order_by(Item.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def create_item(self, owner_user_id: int, short_code: str, kind: str, content: str) -> Item:
        """Create a new item."""
        item = Item(
            owner_user_id=owner_user_id,
            short_code=short_code,
            kind=kind,
            content=content
        )
        return await self.create(item)
    
    async def soft_delete(self, short_code: str, owner_user_id: int) -> bool:
        """Soft delete an item by setting deleted_at timestamp."""
        result = await self.session.execute(
            update(Item)
            .where(
                and_(
                    Item.short_code == short_code,
                    Item.owner_user_id == owner_user_id,
                    Item.deleted_at.is_(None)
                )
            )
            .values(deleted_at=func.current_timestamp())
        )
        return result.rowcount > 0
    
    async def hard_delete(self, short_code: str) -> bool:
        """Hard delete an item by short code."""
        return await self.delete_by_id(
            await self._get_id_by_short_code(short_code)
        )
    
    async def get_items_by_kind(self, owner_user_id: int, kind: str) -> List[Item]:
        """Get items by kind for a specific user."""
        result = await self.session.execute(
            select(Item)
            .where(
                and_(
                    Item.owner_user_id == owner_user_id,
                    Item.kind == kind,
                    Item.deleted_at.is_(None)
                )
            )
            .order_by(Item.created_at.desc())
        )
        return result.scalars().all()
    
    async def search_items(self, owner_user_id: int, query: str) -> List[Item]:
        """Search items by content for a specific user."""
        result = await self.session.execute(
            select(Item)
            .where(
                and_(
                    Item.owner_user_id == owner_user_id,
                    Item.content.contains(query),
                    Item.deleted_at.is_(None)
                )
            )
            .order_by(Item.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_item_stats(self, owner_user_id: int) -> dict:
        """Get item statistics for a user."""
        result = await self.session.execute(
            select(
                func.count(Item.id).label('total'),
                func.count(Item.id).filter(Item.kind == 'url').label('urls'),
                func.count(Item.id).filter(Item.kind == 'note').label('notes')
            )
            .where(
                and_(
                    Item.owner_user_id == owner_user_id,
                    Item.deleted_at.is_(None)
                )
            )
        )
        stats = result.first()
        return {
            'total': stats.total or 0,
            'urls': stats.urls or 0,
            'notes': stats.notes or 0
        }
    
    async def _get_id_by_short_code(self, short_code: str) -> int:
        """Get item ID by short code."""
        result = await self.session.execute(
            select(Item.id).where(Item.short_code == short_code)
        )
        return result.scalar_one()
    
    async def is_short_code_available(self, short_code: str) -> bool:
        """Check if a short code is available."""
        result = await self.session.execute(
            select(Item.id).where(
                and_(
                    Item.short_code == short_code,
                    Item.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none() is None 