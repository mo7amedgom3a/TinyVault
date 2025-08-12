from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.utilities.database import Base

T = TypeVar('T', bound=Base)


class BaseRepository(ABC, Generic[T]):
    """Base repository interface for all data access operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    @property
    @abstractmethod
    def model(self) -> type[T]:
        """Return the model class this repository handles."""
        pass
    
    async def get_by_id(self, id: int) -> Optional[T]:
        """Get entity by ID."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self) -> List[T]:
        """Get all entities."""
        result = await self.session.execute(select(self.model))
        return result.scalars().all()
    
    async def create(self, entity: T) -> T:
        """Create a new entity."""
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
    
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
    
    async def delete(self, entity: T) -> None:
        """Delete an entity."""
        await self.session.delete(entity)
        await self.session.flush()
    
    async def delete_by_id(self, id: int) -> bool:
        """Delete entity by ID. Returns True if deleted, False if not found."""
        result = await self.session.execute(
            delete(self.model).where(self.model.id == id)
        )
        return result.rowcount > 0
    
    async def exists(self, id: int) -> bool:
        """Check if entity exists by ID."""
        result = await self.session.execute(
            select(self.model.id).where(self.model.id == id)
        )
        return result.scalar_one_or_none() is not None
    
    async def count(self) -> int:
        """Get total count of entities."""
        result = await self.session.execute(select(self.model.id))
        return len(result.scalars().all()) 