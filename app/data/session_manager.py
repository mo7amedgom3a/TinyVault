from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.utilities.database import AsyncSessionLocal


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session with automatic cleanup."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class DatabaseSessionManager:
    """Database session manager for dependency injection."""
    
    def __init__(self):
        self.session: AsyncSession | None = None
    
    async def get_session(self) -> AsyncSession:
        """Get the current database session."""
        if self.session is None:
            raise RuntimeError("Database session not initialized")
        return self.session
    
    async def set_session(self, session: AsyncSession):
        """Set the current database session."""
        self.session = session
    
    async def close_session(self):
        """Close the current database session."""
        if self.session:
            await self.session.close()
            self.session = None 