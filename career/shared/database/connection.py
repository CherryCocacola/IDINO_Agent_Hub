"""
Database Connection Manager
- PostgreSQL connection with schema support
- Connection pooling
- Async support
"""
import os
from dataclasses import dataclass
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool


@dataclass
class DatabaseConfig:
    """Database configuration from environment variables"""
    host: str = "localhost"
    port: int = 5432
    database: str = "postgres"
    username: str = "postgres"
    password: str = "2012"
    schema: str = "idino_career"
    pool_size: int = 5
    max_overflow: int = 10

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "postgres"),
            username=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "2012"),
            schema=os.getenv("DB_SCHEMA", "idino_career"),
            pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
        )

    @property
    def sync_url(self) -> str:
        """Synchronous database URL"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def async_url(self) -> str:
        """Asynchronous database URL"""
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


def get_db_engine(config: Optional[DatabaseConfig] = None, async_mode: bool = True):
    """
    Create database engine with schema support

    Args:
        config: DatabaseConfig instance (uses env if None)
        async_mode: Use async engine (default True)

    Returns:
        SQLAlchemy engine
    """
    if config is None:
        config = DatabaseConfig.from_env()

    connect_args = {
        "server_settings": {"search_path": config.schema}
    }

    if async_mode:
        return create_async_engine(
            config.async_url,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
    else:
        return create_engine(
            config.sync_url,
            poolclass=QueuePool,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            pool_pre_ping=True,
            connect_args=connect_args,
        )


def get_db_session(engine, async_mode: bool = True):
    """
    Create session factory

    Args:
        engine: SQLAlchemy engine
        async_mode: Use async session (default True)

    Returns:
        Session factory
    """
    if async_mode:
        return sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    else:
        return sessionmaker(
            engine,
            expire_on_commit=False,
        )
