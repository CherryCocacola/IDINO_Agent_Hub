"""Database connection management with retry logic"""
import asyncio
import logging
import asyncpg
from typing import Optional

from .config import settings

logger = logging.getLogger(__name__)

# Connection pool
pool: Optional[asyncpg.Pool] = None


async def create_pool(max_retries: int = 3, retry_delay: float = 2.0):
    """Create database connection pool with retry logic"""
    global pool

    last_error = None
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting database connection (attempt {attempt + 1}/{max_retries})...")
            pool = await asyncpg.create_pool(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                database=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                min_size=2,
                max_size=10,
                command_timeout=60,
                timeout=30,  # Connection timeout
            )
            # Set search path
            async with pool.acquire() as conn:
                await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}")
            logger.info(f"Database pool initialized successfully (schema: {settings.DB_SCHEMA})")
            return pool
        except Exception as e:
            last_error = e
            logger.warning(f"Database connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (attempt + 1))  # Exponential backoff

    # All retries failed - log warning but allow service to start
    logger.error(f"Failed to connect to database after {max_retries} attempts: {last_error}")
    logger.warning("Service starting without database connection. Some features may be unavailable.")
    return None


async def close_pool():
    """Close database connection pool"""
    global pool
    if pool:
        await pool.close()
        pool = None
        logger.info("Database pool closed")


async def get_pool() -> Optional[asyncpg.Pool]:
    """Get connection pool"""
    global pool
    if pool is None:
        pool = await create_pool()
    return pool
