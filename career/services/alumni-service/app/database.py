"""
Alumni Service Database Configuration.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text

from .config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    pool_size=5,
    max_overflow=10,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db():
    """Dependency for database sessions."""
    async with AsyncSessionLocal() as session:
        # Set schema search path
        await session.execute(
            text(f"SET search_path TO {settings.DB_SCHEMA}, public")
        )
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
