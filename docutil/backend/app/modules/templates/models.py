"""
DocumentTemplate ORM model for organization-scoped document generation templates.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DocumentTemplate(Base):
    """Organization-level document template definition.

    Inherits ``id`` and audit columns from ``Base``.
    """

    __tablename__ = "tb_document_templates"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="'report' or 'proposal' 등 템플릿 유형",
    )
    tone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="formal",
    )
    output_format: Mapped[str] = mapped_column(String(20), nullable=False)
    schema_: Mapped[dict | None] = mapped_column(
        "schema",
        JSONB,
        nullable=True,
    )
    sample_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
    )

    # -- Jinja2 템플릿 렌더링 관련 컬럼 (Phase 1) ---------------------------

    # MinIO에 업로드된 DOCX 템플릿 파일의 스토리지 경로
    template_storage_path: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )
    # 사용자가 업로드한 원본 파일 경로 (원본 보존용)
    original_file_path: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )
    # Jinja2 템플릿 안에서 사용 가능한 변수 정의 (JSON)
    # 예: {"title": "string", "author": "string", "items": "list"}
    jinja2_variables: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # 렌더링 방식 — 'jinja2'(DOCX 템플릿) 또는 'structured'(LLM 생성) 등
    rendering_mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="jinja2",
    )
    # 이미지 자동 생성 설정 (DALL-E 등 이미지 생성 AI 연동 시 사용)
    image_generation_config: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<DocumentTemplate id={self.id!s} name={self.name!r} type={self.template_type!r}>"
