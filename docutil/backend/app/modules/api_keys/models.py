"""
LLMApiKey ORM model for storing encrypted LLM provider API keys.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, LargeBinary, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LLMApiKey(Base):
    """Encrypted API key for an LLM provider, scoped to an organization.

    Inherits ``id`` and audit columns from ``Base``.
    """

    __tablename__ = "tb_llm_api_keys"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    llm_name: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    api_key_prefix: Mapped[str] = mapped_column(String(20), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    registered_by: Mapped[str] = mapped_column(String(255), nullable=False)

    def __repr__(self) -> str:
        return (
            f"<LLMApiKey id={self.id!s} llm={self.llm_name!r} "
            f"prefix={self.api_key_prefix!r}>"
        )
