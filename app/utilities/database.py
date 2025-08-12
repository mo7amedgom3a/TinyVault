from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import StaticPool
from contextlib import asynccontextmanager
from .config import settings
import sqlalchemy as sa

# Create the engine with proper configuration
engine = create_async_engine(
    settings.db_url,
    poolclass=StaticPool,
    connect_args={
        "check_same_thread": False,
        "timeout": 20,
        "isolation_level": None  # Enable autocommit mode for SQLite
    } if "sqlite" in settings.db_url else {},
    # Enable foreign key support for SQLite
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()


@asynccontextmanager
async def get_db_session():
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


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        # Enable foreign key support for SQLite
        if "sqlite" in settings.db_url:
            await conn.execute(sa.text("PRAGMA foreign_keys = ON"))
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections."""
    await engine.dispose()


# Import models to ensure they are registered with Base.metadata
from app.models import User, Item  # noqa: E402

# This ensures all models are imported and registered
__all__ = ["Base", "engine", "AsyncSessionLocal", "get_db_session", "init_db", "close_db"] 