"""
User ORM model with role / status enumerations.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserRole(str, enum.Enum):
    """Application-level roles."""

    super_admin = "super_admin"
    admin = "admin"
    member = "member"
    viewer = "viewer"


class UserStatus(str, enum.Enum):
    """Account status."""

    active = "active"
    inactive = "inactive"
    locked = "locked"


class User(Base):
    """Application user belonging to an organization.

    Inherits ``id`` and audit columns from ``Base``.
    """

    __tablename__ = "tb_users"
    __table_args__ = (
        UniqueConstraint("organization_id", "username", name="uq_tb_users_org_username"),
        UniqueConstraint("organization_id", "email", name="uq_tb_users_org_email"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    username: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="member")
    status: Mapped[str] = mapped_column(String(20), default="active")
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    language: Mapped[str] = mapped_column(String(10), default="ko")
    password_reset_token: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True,
    )
    password_reset_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    @property
    def is_active(self) -> bool:
        """Return ``True`` when the account status is *active*."""
        return self.status == "active"

    def __repr__(self) -> str:
        return f"<User id={self.id!s} username={self.username!r}>"
