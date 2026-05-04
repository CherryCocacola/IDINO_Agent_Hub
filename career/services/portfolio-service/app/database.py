"""Database connection module for Portfolio Service"""
import logging
from typing import Optional
import asyncpg

from .config import settings

logger = logging.getLogger(__name__)

# Global database pool
_db_pool: Optional[asyncpg.Pool] = None


async def init_db_pool():
    """Initialize the database connection pool"""
    global _db_pool
    try:
        # Use 127.0.0.1 instead of localhost on Windows to avoid asyncpg issues
        host = settings.DB_HOST if settings.DB_HOST != 'localhost' else '127.0.0.1'
        _db_pool = await asyncpg.create_pool(
            host=host,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            min_size=2,
            max_size=10,
            command_timeout=60,
        )
        # Set search path for the pool
        async with _db_pool.acquire() as conn:
            await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}")
        logger.info(f"Database pool initialized successfully (schema: {settings.DB_SCHEMA})")
    except Exception as e:
        logger.error(f"Failed to initialize database pool: {e}")
        raise


async def close_db_pool():
    """Close the database connection pool"""
    global _db_pool
    if _db_pool:
        await _db_pool.close()
        logger.info("Database pool closed")


async def get_db_pool() -> asyncpg.Pool:
    """Get the database connection pool"""
    global _db_pool
    if _db_pool is None:
        await init_db_pool()
    return _db_pool
