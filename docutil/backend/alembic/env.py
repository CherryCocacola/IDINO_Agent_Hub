"""
Alembic environment configuration for async SQLAlchemy migrations.

This module:

1. Imports **all** application models so that ``Base.metadata`` is fully
   populated before Alembic inspects it for autogenerate diffs.
2. Reads the database URL from the application settings (which in turn
   reads from the ``DATABASE_URL`` environment variable or ``.env`` file).
3. Runs migrations using an **async** engine (``asyncpg`` driver).
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig
from typing import TYPE_CHECKING

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from app.core.config import get_settings
from app.core.database import Base
from app.modules.api_keys.models import *  # noqa: F401, F403
from app.modules.audit.models import *  # noqa: F401, F403
from app.modules.chat.models import *  # noqa: F401, F403
from app.modules.documents.models import *  # noqa: F401, F403
from app.modules.faq.models import *  # noqa: F401, F403
from app.modules.organizations.models import *  # noqa: F401, F403
from app.modules.projects.models import *  # noqa: F401, F403
from app.modules.reports.models import *  # noqa: F401, F403
from app.modules.search_scopes.models import *  # noqa: F401, F403

# ---------------------------------------------------------------------------
# Import ALL models so that Base.metadata is aware of every table.
# Without these imports, autogenerate will not detect any tables.
# ---------------------------------------------------------------------------
from app.modules.users.models import User  # noqa: F401

if TYPE_CHECKING:
    from sqlalchemy.engine import Connection

# ---------------------------------------------------------------------------
# Alembic Config object -- provides access to values in alembic.ini
# ---------------------------------------------------------------------------
config = context.config

# Interpret the config file for Python logging if present.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The target metadata that Alembic will compare against the live database.
target_metadata = Base.metadata

# ---------------------------------------------------------------------------
# Override sqlalchemy.url from application settings
# ---------------------------------------------------------------------------
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)


# ---------------------------------------------------------------------------
# Offline migrations (SQL script generation)
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine, though
    an Engine is acceptable here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to ``context.execute()`` here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migrations (async engine)
# ---------------------------------------------------------------------------
def do_run_migrations(connection: Connection) -> None:
    """Run migrations using a synchronous connection (called inside async)."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations within a connection."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an async engine."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
