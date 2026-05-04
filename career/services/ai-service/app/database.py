"""
Database Connection Module for AI Service
Provides async SQLAlchemy session for RAG and Eval operations
"""

from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from .config import get_settings


settings = get_settings()

# Create async engine with connection pooling
# Use NullPool for serverless or development environments
engine = create_async_engine(
    settings.database_url,
    poolclass=NullPool,
    echo=False,
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.

    Usage:
        @router.get("/example")
        async def example(db: AsyncSession = Depends(get_db)):
            result = await db.execute(text("SELECT 1"))
            return result.scalar()
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database connection (called on startup)."""
    # Set search path for the schema
    async with engine.begin() as conn:
        await conn.execute(text(f"SET search_path TO {settings.DB_SCHEMA}, public"))


async def close_db():
    """Close database connections (called on shutdown)."""
    await engine.dispose()
