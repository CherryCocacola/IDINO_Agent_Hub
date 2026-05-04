import asyncpg
import json
from typing import Optional, List, Any, Dict
from contextlib import asynccontextmanager

from .config import get_settings

settings = get_settings()

# Connection pool
_pool: Optional[asyncpg.Pool] = None


async def _init_connection(conn):
    """Initialize connection with JSONB codec"""
    await conn.set_type_codec(
        'jsonb',
        encoder=json.dumps,
        decoder=json.loads,
        schema='pg_catalog'
    )
    await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}, public")


async def init_db():
    """Initialize database connection pool"""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            min_size=settings.DB_POOL_MIN,
            max_size=settings.DB_POOL_MAX,
            command_timeout=60,
            init=_init_connection,
        )
    return _pool


async def close_db():
    """Close database connection pool"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def get_pool() -> asyncpg.Pool:
    """Get database connection pool"""
    if _pool is None:
        await init_db()
    return _pool


@asynccontextmanager
async def get_connection():
    """Get a database connection from the pool"""
    pool = await get_pool()
    async with pool.acquire() as connection:
        # Ensure search_path is set for this connection
        await connection.execute(f"SET search_path TO {settings.DB_SCHEMA}, public")
        yield connection


async def execute_query(query: str, *args) -> List[Dict[str, Any]]:
    """Execute a query and return all results as dictionaries"""
    async with get_connection() as conn:
        rows = await conn.fetch(query, *args)
        return [dict(row) for row in rows]


async def execute_one(query: str, *args) -> Optional[Dict[str, Any]]:
    """Execute a query and return single result as dictionary"""
    async with get_connection() as conn:
        row = await conn.fetchrow(query, *args)
        return dict(row) if row else None


async def execute_scalar(query: str, *args) -> Any:
    """Execute a query and return scalar value"""
    async with get_connection() as conn:
        return await conn.fetchval(query, *args)


async def execute_many(query: str, args_list: List[tuple]) -> None:
    """Execute a query multiple times with different arguments"""
    async with get_connection() as conn:
        await conn.executemany(query, args_list)


async def execute_command(query: str, *args) -> str:
    """Execute a command (INSERT, UPDATE, DELETE) and return status"""
    async with get_connection() as conn:
        return await conn.execute(query, *args)
