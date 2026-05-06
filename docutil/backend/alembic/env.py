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

import sqlalchemy as sa
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
# Phase 4.1: configparser 가 ``%`` 를 보간 문법으로 해석하므로, percent-encoded
# 비밀번호(예: ``idino%21%40%23%24``)를 가진 URL 은 ``%%`` 로 escape 해야 한다.
# 실제 DB 연결 시 SQLAlchemy 가 다시 단일 ``%`` 로 해석한다.
_safe_db_url = settings.database_url.replace("%", "%%")
config.set_main_option("sqlalchemy.url", _safe_db_url)


# ---------------------------------------------------------------------------
# Offline migrations (SQL script generation)
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Phase 4.1: AGENT_HUB DB 통합 — db_schema 격리
# ---------------------------------------------------------------------------
# Base.metadata.schema 가 설정되면 ``include_schemas=True`` 가 필요하다
# (autogenerate 가 다른 schema 의 객체와 비교할 수 있도록 활성화). 또한
# alembic_version 테이블도 동일 schema 안에 두어 4 개 schema 가 각자의
# 마이그레이션 헤드를 독립적으로 관리하게 한다.
_db_schema = settings.db_schema
_is_sqlite = settings.database_url.startswith("sqlite")


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
        # Phase 4.1: alembic_version 테이블을 db_schema 안에 두어 4 개 schema 의
        # 마이그레이션 헤드를 독립적으로 추적한다 (R3 스키마 격리).
        version_table_schema=None if _is_sqlite else _db_schema,
        include_schemas=not _is_sqlite,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migrations (async engine)
# ---------------------------------------------------------------------------
def do_run_migrations(connection: Connection) -> None:
    """Run migrations using a synchronous connection (called inside async)."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # Phase 4.1: alembic_version 테이블을 db_schema 안에 두어 4 개 schema 의
        # 마이그레이션 헤드를 독립적으로 추적한다 (R3 스키마 격리).
        version_table_schema=None if _is_sqlite else _db_schema,
        include_schemas=not _is_sqlite,
    )

    with context.begin_transaction():
        # Phase 4.1: alembic 의 transactional DDL 안에서 schema 보장 + search_path
        # 강제. AGENT_HUB DB 의 default search_path 가 ``"AIAgentManagement",
        # document_utilization, ...`` 로 잡혀 있어, ``op.create_table()`` 같은
        # alembic 명령이 잘못된 schema(AIAgentManagement) 에 객체를 만들거나
        # naming_convention 충돌로 transaction 이 abort 된다. ``SET LOCAL`` 은
        # 현재 transaction 안에서만 유효하지만, alembic 이 ``begin_transaction``
        # 으로 감싼 단일 transaction 안에서 모든 마이그레이션을 직렬 실행하므로
        # LOCAL 도 안전하다. 실수로 다른 connection 으로 새는 일도 없다.
        if not _is_sqlite:
            connection.execute(sa.text(f'CREATE SCHEMA IF NOT EXISTS "{_db_schema}"'))
            connection.execute(
                sa.text(f'SET LOCAL search_path TO "{_db_schema}", public')
            )
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations within a connection."""
    # Phase 4.1: alembic 이 만드는 별도 엔진에도 search_path 를 주입한다.
    # do_run_migrations() 내부에서 ``SET LOCAL search_path`` 도 수행하지만,
    # asyncpg 드라이버가 connect 직후부터 schema 격리를 적용하도록 이중 안전.
    connect_args: dict[str, dict[str, str]] = {}
    if not _is_sqlite:
        connect_args = {
            "server_settings": {
                "search_path": f"{_db_schema},public",
            },
        }

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
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
