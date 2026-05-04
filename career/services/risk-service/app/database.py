import asyncpg
from typing import Optional, List, Any, Dict
from contextlib import asynccontextmanager

from .config import get_settings

settings = get_settings()

_pool: Optional[asyncpg.Pool] = None


async def init_db():
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
        )
        async with _pool.acquire() as conn:
            await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}, public")
    return _pool


async def close_db():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def get_pool() -> asyncpg.Pool:
    if _pool is None:
        await init_db()
    return _pool


@asynccontextmanager
async def get_connection():
    pool = await get_pool()
    async with pool.acquire() as connection:
        await connection.execute(f"SET search_path TO {settings.DB_SCHEMA}, public")
        yield connection


async def execute_query(query: str, *args) -> List[Dict[str, Any]]:
    async with get_connection() as conn:
        rows = await conn.fetch(query, *args)
        return [dict(row) for row in rows]


async def execute_one(query: str, *args) -> Optional[Dict[str, Any]]:
    async with get_connection() as conn:
        row = await conn.fetchrow(query, *args)
        return dict(row) if row else None


async def execute_scalar(query: str, *args) -> Any:
    async with get_connection() as conn:
        return await conn.fetchval(query, *args)


async def execute_command(query: str, *args) -> str:
    async with get_connection() as conn:
        return await conn.execute(query, *args)
