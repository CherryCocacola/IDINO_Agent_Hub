"""
Project, Board, and Folder ORM models.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Project(Base):
    """Logical project container within an organization.

    Inherits ``id`` and audit columns from ``Base``.
    """

    __tablename__ = "tb_projects"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    allow_original_download: Mapped[bool] = mapped_column(
        Boolean, default=False,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_users.id", ondelete="SET NULL"),
        nullable=False,
    )

    # -- relationships --------------------------------------------------------
    boards: Mapped[list[Board]] = relationship(
        "Board",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id!s} name={self.name!r}>"


class Board(Base):
    """Board grouping inside a project.

    Inherits ``id`` and audit columns from ``Base``.
    """

    __tablename__ = "tb_boards"

    project_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_users.id", ondelete="SET NULL"),
        nullable=False,
    )

    # -- relationships --------------------------------------------------------
    project: Mapped[Project] = relationship(
        "Project",
        back_populates="boards",
    )
    folders: Mapped[list[Folder]] = relationship(
        "Folder",
        back_populates="board",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Board id={self.id!s} name={self.name!r}>"


class Folder(Base):
    """Folder inside a board for organizing documents.

    Inherits ``id`` and audit columns from ``Base``.
    """

    __tablename__ = "tb_folders"

    board_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_boards.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_users.id", ondelete="SET NULL"),
        nullable=False,
    )

    # -- relationships --------------------------------------------------------
    board: Mapped[Board] = relationship(
        "Board",
        back_populates="folders",
    )

    def __repr__(self) -> str:
        return f"<Folder id={self.id!s} name={self.name!r}>"


# ---------------------------------------------------------------------------
# ProjectMember (트랙 #101 F8) — 프로젝트 ↔ 사용자 매핑
# ---------------------------------------------------------------------------
#
# 운영 메모:
#   - DB 테이블은 이미 존재(트랙 #88-6 마이그레이션) — 본 ORM 클래스는 mapping 만 추가.
#   - tb_users 는 트랙 #98 phase 3 이후 VIEW 이다(AgentHub User 마스터 → DocUtil VIEW 투영).
#     PostgreSQL 은 VIEW 를 가리키는 FK 를 만들 수 없으므로 user_id 에는
#     `ForeignKey("tb_users.id", ...)` 를 부착하지 않는다. user_id 유효성은
#     application 레벨(ProjectService.add_member 가 tb_users 존재 검증)에서 보장한다.
#   - project_id 에만 FK 가 살아 있다(`fk_tb_project_members_project_id_tb_projects`).
# ---------------------------------------------------------------------------


class ProjectMember(Base):
    """프로젝트 ↔ 사용자 N:M 매핑 (트랙 #101 F8).

    Inherits ``id`` and audit columns from ``Base``.
    """

    __tablename__ = "tb_project_members"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "user_id",
            name="uq_tb_project_members_proj_user",
        ),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    # tb_users 는 VIEW (트랙 #98) — PG 가 VIEW 를 가리키는 FK 를 허용하지 않으므로
    # ForeignKey 미부착. 유효성은 ProjectService.add_member 가 책임진다.
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
    )
    # 'member' | 'manager' (DB 컬럼 코멘트 기준)
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="member",
    )

    def __repr__(self) -> str:
        return (
            f"<ProjectMember id={self.id!s} "
            f"project_id={self.project_id!s} user_id={self.user_id!s} role={self.role!r}>"
        )
