"""
ChatSession and ChatMessage ORM models.
"""

from __future__ import annotations

import enum
import uuid
from typing import Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MessageRole(str, enum.Enum):
    """Role of the message author."""

    user = "user"
    assistant = "assistant"
    system = "system"


class ChatSession(Base):
    """A conversation session between a user and the assistant.

    Inherits ``id`` and audit columns from ``Base``.
    """

    __tablename__ = "tb_chat_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    search_scope_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_search_scopes.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    scoped_document_ids: Mapped[Optional[list[uuid.UUID]]] = mapped_column(
        ARRAY(PG_UUID(as_uuid=True)), nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # -- relationships --------------------------------------------------------
    messages: Mapped[list[ChatMessage]] = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.ins_dt",
    )

    def __repr__(self) -> str:
        return f"<ChatSession id={self.id!s} title={self.title!r}>"


class ChatMessage(Base):
    """Individual message within a chat session.

    Inherits ``id`` and audit columns from ``Base``.
    """

    __tablename__ = "tb_chat_messages"

    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    retrieved_chunks: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    model_used: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    token_count_input: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    token_count_output: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    hallucination_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # -- relationships --------------------------------------------------------
    session: Mapped[ChatSession] = relationship(
        "ChatSession",
        back_populates="messages",
    )

    def __repr__(self) -> str:
        return f"<ChatMessage id={self.id!s} role={self.role.value!r}>"
