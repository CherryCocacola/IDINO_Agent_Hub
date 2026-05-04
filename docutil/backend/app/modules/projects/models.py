"""
Project, Board, and Folder ORM models.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, Text
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
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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
