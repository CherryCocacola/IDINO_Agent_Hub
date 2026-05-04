import asyncpg
from typing import Optional
from .config import get_settings

_pool: Optional[asyncpg.Pool] = None


async def init_db():
    global _pool
    settings = get_settings()
    _pool = await asyncpg.create_pool(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        min_size=2,
        max_size=10,
        command_timeout=60
    )
    # Set search path
    async with _pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}, public")
    return _pool


async def close_db():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        await init_db()
    return _pool


async def execute_query(query: str, *args):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {get_settings().DB_SCHEMA}, public")
        return await conn.fetch(query, *args)


async def execute_one(query: str, *args):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {get_settings().DB_SCHEMA}, public")
        return await conn.fetchrow(query, *args)


async def execute_scalar(query: str, *args):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {get_settings().DB_SCHEMA}, public")
        return await conn.fetchval(query, *args)
