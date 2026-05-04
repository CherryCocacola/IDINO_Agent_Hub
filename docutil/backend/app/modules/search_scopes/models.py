"""
SearchScope ORM model -- defines retrieval and chatbot configuration scopes.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SearchScope(Base):
    """Defines a configured search scope with retrieval and chatbot settings.

    Inherits ``id`` and audit columns from ``Base``.
    """

    __tablename__ = "tb_search_scopes"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # -- optional location narrowing ------------------------------------------
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_projects.id", ondelete="SET NULL"),
        nullable=True,
    )
    board_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_boards.id", ondelete="SET NULL"),
        nullable=True,
    )
    folder_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_folders.id", ondelete="SET NULL"),
        nullable=True,
    )
    location_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # -- feature toggles ------------------------------------------------------
    chatbot_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    chatbot_faq_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    qa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    qa_prompt_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    qa_llm_model: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    keyword_search_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    agent_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    # -- chunking / retrieval tuning ------------------------------------------
    chunk_size: Mapped[int] = mapped_column(Integer, default=512)
    chunk_overlap: Mapped[int] = mapped_column(Integer, default=64)
    title_weight: Mapped[float] = mapped_column(Float, default=0.3)
    keyword_weight: Mapped[float] = mapped_column(Float, default=0.3)
    content_weight: Mapped[float] = mapped_column(Float, default=0.4)
    max_results: Mapped[int] = mapped_column(Integer, default=10)
    similarity_threshold: Mapped[float] = mapped_column(Float, default=0.5)

    # -- ownership ------------------------------------------------------------
    created_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_users.id", ondelete="SET NULL"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<SearchScope id={self.id!s} name={self.name!r}>"
