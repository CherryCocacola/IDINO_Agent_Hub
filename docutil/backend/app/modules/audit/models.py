"""
AuditLog ORM model for immutable activity tracking.

Note: table partitioning (e.g. by ins_dt range) is handled at the
Alembic migration level, not in the ORM model definition.
"""

from __future__ import annotations

import enum
import uuid
from typing import Optional

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditAction(str, enum.Enum):
    """Enumeration of auditable actions."""

    login = "login"
    logout = "logout"
    create = "create"
    read = "read"
    update = "update"
    delete = "delete"
    upload = "upload"
    download = "download"
    search = "search"
    generate = "generate"


class AuditLog(Base):
    """Append-only audit log entry.

    Inherits ``id`` and audit columns from ``Base``.
    Partitioning by ``ins_dt`` is configured in the database migration,
    not here -- SQLAlchemy's ORM does not natively manage partitioned tables.
    """

    __tablename__ = "tb_audit_logs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )
    # 감사 로그 액션은 String으로 저장하여 유연성을 확보한다.
    # "auth.login", "document.upload" 등 도메인별 접두사를 사용한다.
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )
    details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id!s} action={self.action!r} "
            f"resource={self.resource_type!r}>"
        )
