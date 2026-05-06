"""
Async SQLAlchemy engine, session factory, and declarative base classes.

Usage
-----
In any FastAPI route or service, depend on ``get_db``::

    async def my_route(db: AsyncSession = Depends(get_db)):
        ...
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, MetaData, String, event, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    declared_attr,
    mapped_column,
)

from .config import get_settings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

# ---------------------------------------------------------------------------
# Naming convention (Alembic-friendly) - idx_ prefix for indexes
# ---------------------------------------------------------------------------
NAMING_CONVENTION: dict[str, str] = {
    "ix": "idx_%(table_name)s_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# ---------------------------------------------------------------------------
# Settings (module-level singleton, used by both metadata and engine)
# ---------------------------------------------------------------------------
_settings = get_settings()

# SQLite doesn't support pool_size/max_overflow/pool_timeout arguments,
# nor does it support PostgreSQL-style schemas. Detect by URL prefix so
# pytest InMemory configurations keep working without db_schema.
_is_sqlite = _settings.database_url.startswith("sqlite")

# Phase 4.1: 모든 테이블을 AGENT_HUB.document_utilization schema 에 격리한다.
# Base.metadata.schema 가 설정되면 ForeignKey("tb_xxx.id") 같은 단순 참조도
# 자동으로 동일 schema 안에서 해석된다. cross-schema FK 가 필요할 때만
# 모델에 명시적으로 __table_args__ = {"schema": "...other..."} 를 부여한다.
# (현재 DocUtil 18 모듈은 모두 자기 schema 내부 참조만 사용 — 검증 완료)
metadata = MetaData(
    naming_convention=NAMING_CONVENTION,
    schema=None if _is_sqlite else _settings.db_schema,
)

# ---------------------------------------------------------------------------
# Audit context (per-request storage for user/IP)
# ---------------------------------------------------------------------------
audit_context: ContextVar[dict[str, Any] | None] = ContextVar("audit_context", default=None)

if _is_sqlite:
    # SQLite configuration (for testing)
    engine = create_async_engine(
        _settings.database_url,
        echo=_settings.db_echo,
    )
else:
    # PostgreSQL/production configuration
    #
    # Phase 4.1: AGENT_HUB DB 진입 시 search_path 를 db_schema 로 강제한다.
    # 이는 두 가지 효과를 갖는다:
    #   1. SQLAlchemy 모델 / alembic 마이그레이션의 단순 테이블 참조
    #      (`tb_xxx`, `ForeignKey("tb_yyy.id")`) 가 자동으로 db_schema 에서
    #      해석된다. 따라서 18 개 모듈에 `__table_args__ = {"schema": ...}`
    #      를 일일이 추가할 필요가 없다.
    #   2. 다른 schema (예: AIAgentManagement, idino_career) 의 객체에 우연히
    #      접근하지 못하도록 1 차 방어선을 친다 (R3 스키마 격리).
    #
    # asyncpg 는 PostgreSQL ``options=-c search_path=...`` 를
    # ``server_settings`` 딕셔너리로 전달해야 한다 (psycopg2 의 ``options``
    # 키와 다름). public 을 두 번째에 두는 이유는 pgcrypto / uuid-ossp 같은
    # 확장 함수가 public 에 위치하기 때문.
    engine = create_async_engine(
        _settings.database_url,
        echo=_settings.db_echo,
        pool_size=_settings.db_pool_size,
        max_overflow=_settings.db_max_overflow,
        pool_timeout=_settings.db_pool_timeout,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={
            "server_settings": {
                "search_path": f"{_settings.db_schema},public",
            },
        },
    )

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ---------------------------------------------------------------------------
# Mixins
# ---------------------------------------------------------------------------
class UUIDMixin:
    """Provides a UUID v4 primary key column named ``id``."""

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        index=True,
    )


class AuditMixin:
    """Audit columns: ins_dt, ins_user, ins_ip, upd_dt, upd_user, upd_ip.

    Replaces the previous TimestampMixin (created_at, updated_at).
    """

    ins_dt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=text("now()"),
        nullable=False,
    )
    ins_user: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )
    ins_ip: Mapped[str | None] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True,
    )
    upd_dt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=text("now()"),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    upd_user: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )
    upd_ip: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )


# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------
class Base(AsyncAttrs, DeclarativeBase, UUIDMixin, AuditMixin):
    """Application-wide declarative base.

    Every model inheriting from ``Base`` automatically receives:

    * ``id``       -- UUID v4 primary key
    * ``ins_dt``   -- insert timestamp (UTC)
    * ``ins_user`` -- insert user UUID
    * ``ins_ip``   -- insert client IP
    * ``upd_dt``   -- update timestamp (UTC)
    * ``upd_user`` -- update user UUID
    * ``upd_ip``   -- update client IP
    """

    metadata = metadata
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:  # noqa: N805
        """Derive table name from the class name (snake_case) with tb_ prefix."""
        name = cls.__name__
        result: list[str] = []
        for i, ch in enumerate(name):
            if ch.isupper() and i > 0:
                result.append("_")
            result.append(ch.lower())
        return "tb_" + "".join(result)

    def to_dict(self) -> dict[str, Any]:
        """Serialise the model instance to a plain dict."""
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}


# ---------------------------------------------------------------------------
# SQLAlchemy event listener for audit field injection
# ---------------------------------------------------------------------------
@event.listens_for(Session, "before_flush")
def inject_audit_fields(
    session: Session,
    flush_context: Any,
    instances: Any,
) -> None:
    """Automatically inject audit fields on INSERT/UPDATE operations."""
    ctx = audit_context.get() or {}
    user_id = ctx.get("user_id")
    client_ip = ctx.get("client_ip")
    now = datetime.now(UTC)

    # Handle INSERT (new objects)
    for obj in session.new:
        if hasattr(obj, "ins_user") and obj.ins_user is None:
            obj.ins_user = user_id
        if hasattr(obj, "ins_ip") and obj.ins_ip is None:
            obj.ins_ip = client_ip
        if hasattr(obj, "ins_dt"):
            obj.ins_dt = now
        # Also set update fields on insert
        if hasattr(obj, "upd_user"):
            obj.upd_user = user_id
        if hasattr(obj, "upd_ip"):
            obj.upd_ip = client_ip
        if hasattr(obj, "upd_dt"):
            obj.upd_dt = now

    # Handle UPDATE (dirty objects)
    for obj in session.dirty:
        if hasattr(obj, "upd_user"):
            obj.upd_user = user_id
        if hasattr(obj, "upd_ip"):
            obj.upd_ip = client_ip
        if hasattr(obj, "upd_dt"):
            obj.upd_dt = now


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an ``AsyncSession`` and ensures cleanup.

    Usage::

        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
