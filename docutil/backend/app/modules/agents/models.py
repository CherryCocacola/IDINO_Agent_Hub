"""
Agent ORM model for organization-scoped AI agent configurations.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Agent(Base):
    """Organization-level AI agent configuration.

    Inherits ``id`` and audit columns from ``Base``.
    """

    __tablename__ = "tb_agents"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="'chatbot', 'report', or 'proposal'",
    )
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    # 에이전트가 사용할 LLM 프로바이더 (None이면 시스템 기본값 사용)
    llm_provider: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="openai, azure_openai, gemini, anthropic 등",
    )
    llm_model: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        server_default="gpt-4o",
    )
    temperature: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        server_default="0.1",
    )
    max_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="4096",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Agent id={self.id!s} name={self.name!r} type={self.agent_type!r}>"
