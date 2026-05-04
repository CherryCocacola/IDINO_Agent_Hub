"""
Organization, Department, and OrganizationQuota ORM models.
"""

from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Organization(Base):
    """Top-level tenant entity.

    Inherits ``id`` and audit columns from ``Base``.
    Table name: tb_organization (auto-generated).
    """

    __tablename__ = "tb_organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # -- relationships --------------------------------------------------------
    departments: Mapped[list[Department]] = relationship(
        "Department",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Organization id={self.id!s} slug={self.slug!r}>"


class Department(Base):
    """Hierarchical department inside an organization (adjacency-list + path).

    Inherits ``id`` and audit columns from ``Base``.
    Table name: tb_department (auto-generated).
    """

    __tablename__ = "tb_departments"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    depth: Mapped[int] = mapped_column(Integer, default=0)
    path: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # -- relationships --------------------------------------------------------
    organization: Mapped[Organization] = relationship(
        "Organization",
        back_populates="departments",
    )
    parent: Mapped[Department | None] = relationship(
        "Department",
        remote_side="Department.id",
        back_populates="children",
    )
    children: Mapped[list[Department]] = relationship(
        "Department",
        back_populates="parent",
    )

    def __repr__(self) -> str:
        return f"<Department id={self.id!s} name={self.name!r}>"


class OrganizationQuota(Base):
    """조직별 월 단위 외부 이미지 생성 API 쿼터.

    한 조직은 (quota_type, year_month) 조합당 **정확히 하나**의 레코드를 갖는다.
    서비스 계층은 현재 월('YYYY-MM') 레코드를 on-demand 로 생성하며, 사용량이
    ``monthly_limit`` 을 초과하면 403(한국어 메시지) 을 반환한다.

    대응 migration: Alembic 009 (`tb_organization_quotas`).
    """

    __tablename__ = "tb_organization_quotas"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    quota_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    year_month: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
    )
    monthly_limit: Mapped[int] = mapped_column(
        Integer,
        default=100,
        nullable=False,
    )
    used_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # -- 제약조건 ----------------------------------------------------------
    # NOTE: naming_convention (app.core.database) 이 "ck_%(table_name)s_%(constraint_name)s"
    # 패턴으로 최종 이름을 합성한다. 따라서 본 ORM 에서는 접미 부분만 ``name=`` 으로
    # 지정한다. Alembic 009 migration 은 naming_convention 을 거치지 않고
    # 원본 이름을 그대로 쓰기 때문에 009 에서만 ``ck_tb_organization_quotas_*`` 풀
    # 이름을 명시한다.
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "quota_type",
            "year_month",
            name="uq_tb_organization_quotas_org_type_month",
        ),
        CheckConstraint(
            "monthly_limit >= 0",
            name="monthly_limit_positive",
        ),
        CheckConstraint(
            "used_count >= 0",
            name="used_count_positive",
        ),
        CheckConstraint(
            "quota_type IN ('dalle_monthly','unsplash_monthly')",
            name="quota_type",
        ),
        CheckConstraint(
            "year_month ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'",
            name="year_month_format",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<OrganizationQuota id={self.id!s} org={self.organization_id!s} "
            f"type={self.quota_type!r} ym={self.year_month!r} "
            f"used={self.used_count}/{self.monthly_limit}>"
        )
