"""
Document and DocumentChunk ORM models with format / status / chunk-type enums.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class DocumentStatus(str, enum.Enum):
    """Pipeline processing status."""

    waiting = "waiting"
    processing = "processing"
    completed = "completed"
    error = "error"


class DocumentVisibility(str, enum.Enum):
    """문서 공개 범위(visibility) 6단계.

    - public: 조직 전체 공개 (최상위 레벨)
    - all_departments: 모든 부서 공개
    - department_only: 작성 부서와 하위 부서만 공개 (기본값)
    - project_only: 프로젝트 구성원만 공개
    - confidential: tb_document_access 테이블로 명시 허용된 사용자 + 업로더
    - hidden: 업로더 + 운영자(admin)만 보이는 극비 문서
    """

    public = "public"
    all_departments = "all_departments"
    department_only = "department_only"
    project_only = "project_only"
    confidential = "confidential"
    hidden = "hidden"


class DocumentFormat(str, enum.Enum):
    """Supported source-file formats."""

    hwp = "hwp"
    hwpx = "hwpx"
    pdf = "pdf"
    docx = "docx"
    pptx = "pptx"
    xlsx = "xlsx"
    csv = "csv"
    html = "html"
    txt = "txt"
    md = "md"
    png = "png"
    jpg = "jpg"
    jpeg = "jpeg"
    tiff = "tiff"
    bmp = "bmp"


class ChunkType(str, enum.Enum):
    """Semantic type of a document chunk."""

    text = "text"
    table = "table"
    image_caption = "image_caption"
    header = "header"
    list = "list"
    code = "code"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Document(Base):
    """Uploaded document and its processing metadata.

    Inherits ``id`` and audit columns from ``Base``.
    """

    __tablename__ = "tb_documents"

    # Alembic 002에서 folder_id 를 nullable=True 로 변경했으므로 ORM 도 맞춘다
    folder_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_folders.id", ondelete="CASCADE"),
        nullable=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 문서 공개 범위 (6단계). Alembic 002 server_default="department_only"
    visibility: Mapped[str] = mapped_column(
        String(20), default="department_only", nullable=False,
    )
    # 문서가 소속된 부서 (SET NULL on 부서 삭제)
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    # 문서가 소속된 프로젝트 (project_only 가시성일 때 필수)
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_projects.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    # DB에서는 String(20)으로 저장하므로, ORM에서도 String으로 매핑한다
    format: Mapped[str] = mapped_column(String(20), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="waiting")
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, nullable=True,
    )
    tags: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(String), nullable=True,
    )
    language: Mapped[str] = mapped_column(String(10), default="ko")
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_users.id", ondelete="SET NULL"),
        nullable=False,
    )
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    processing_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # -- relationships --------------------------------------------------------
    chunks: Mapped[list[DocumentChunk]] = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id!s} name={self.name!r} status={self.status!r}>"


class DocumentChunk(Base):
    """Individual chunk produced by the document-processing pipeline.

    Inherits ``id`` and audit columns from ``Base``.
    """

    __tablename__ = "tb_document_chunks"
    __table_args__ = (
        UniqueConstraint(
            "document_id", "chunk_index", name="uq_tb_document_chunks_doc_idx",
        ),
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_length: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    section_title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, nullable=True,
    )
    qdrant_point_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True,
    )

    # -- relationships --------------------------------------------------------
    document: Mapped[Document] = relationship(
        "Document",
        back_populates="chunks",
    )

    def __repr__(self) -> str:
        return (
            f"<DocumentChunk id={self.id!s} document_id={self.document_id!s} "
            f"index={self.chunk_index}>"
        )
