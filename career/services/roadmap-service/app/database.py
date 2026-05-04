"""
Database configuration for Roadmap Service.
Uses asyncpg for async database operations.
"""
import asyncpg
import logging
import yaml
from pathlib import Path
from typing import Optional, List, Dict, Any

from .config import settings

logger = logging.getLogger(__name__)


class DatabasePool:
    """Database connection pool manager"""

    _pool: Optional[asyncpg.Pool] = None
    _queries: Dict[str, Dict[str, Any]] = {}

    @classmethod
    async def get_pool(cls) -> asyncpg.Pool:
        """Get or create database connection pool"""
        if cls._pool is None:
            cls._pool = await asyncpg.create_pool(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                database=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                min_size=2,
                max_size=10,
                command_timeout=60,
                server_settings={"search_path": settings.DB_SCHEMA}
            )
            logger.info(f"Database pool created for {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
        return cls._pool

    @classmethod
    async def close_pool(cls):
        """Close database connection pool"""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            logger.info("Database pool closed")

    @classmethod
    def load_queries(cls, yaml_file: str = "roadmap.yaml") -> Dict[str, Dict[str, Any]]:
        """Load SQL queries from YAML file"""
        if not cls._queries:
            # Try multiple paths
            paths_to_try = [
                Path(__file__).parent.parent.parent.parent / "shared" / "database" / "queries" / yaml_file,
                Path("shared/database/queries") / yaml_file,
            ]

            for query_path in paths_to_try:
                if query_path.exists():
                    with open(query_path, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                        cls._queries = data.get('queries', {})
                        logger.info(f"Loaded {len(cls._queries)} queries from {query_path}")
                        break
            else:
                logger.warning(f"Query file not found: {yaml_file}")
                cls._queries = {}

        return cls._queries

    @classmethod
    def get_query(cls, query_name: str) -> Optional[str]:
        """Get SQL query by name"""
        if not cls._queries:
            cls.load_queries()

        query_info = cls._queries.get(query_name, {})
        return query_info.get('sql')


async def get_db_pool() -> asyncpg.Pool:
    """Dependency for getting database pool"""
    return await DatabasePool.get_pool()


async def execute_query(
    query_name: str,
    params: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """Execute a named query and return results as list of dicts"""
    sql = DatabasePool.get_query(query_name)
    if not sql:
        logger.error(f"Query not found: {query_name}")
        return []

    pool = await DatabasePool.get_pool()

    try:
        # Convert named parameters to positional
        if params:
            for key, value in params.items():
                sql = sql.replace(f":{key}", f"${list(params.keys()).index(key) + 1}")
            param_values = list(params.values())
        else:
            param_values = []

        async with pool.acquire() as conn:
            rows = await conn.fetch(sql, *param_values)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Query execution failed ({query_name}): {e}")
        return []


async def execute_raw_query(
    sql: str,
    params: List[Any] = None
) -> List[Dict[str, Any]]:
    """Execute raw SQL query"""
    pool = await DatabasePool.get_pool()

    try:
        async with pool.acquire() as conn:
            if params:
                rows = await conn.fetch(sql, *params)
            else:
                rows = await conn.fetch(sql)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Raw query execution failed: {e}")
        return []
