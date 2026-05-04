"""
Pydantic v2 schemas for the reports module.

Covers report template CRUD, report generation requests, and generated
report responses (status, download, listing).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Report template schemas
# ---------------------------------------------------------------------------


class ReportTemplateCreate(BaseModel):
    """Payload for creating a new report template (metadata only).

    The actual template file is uploaded as a multipart form field alongside
    this JSON body.
    """

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    format: str = Field(
        ...,
        description="Template document format.",
        pattern=r"^(hwp|hwpx|docx|pdf|html)$",
    )


class ReportTemplateUpdate(BaseModel):
    """Payload for partially updating a report template's metadata."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class ReportTemplateResponse(BaseModel):
    """Read-only representation of a report template."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    organization_id: UUID
    name: str
    description: str | None = None
    format: str
    template_storage_path: str | None = None
    schema_: dict[str, Any] | None = Field(default=None, alias="schema")
    created_by: UUID
    created_at: datetime = Field(validation_alias="ins_dt")  # DB 컬럼 ins_dt 매핑
    updated_at: datetime = Field(validation_alias="upd_dt")  # DB 컬럼 upd_dt 매핑


class ReportTemplateListResponse(BaseModel):
    """Paginated list of report templates."""

    items: list[ReportTemplateResponse]
    total: int
    page: int
    size: int


# ---------------------------------------------------------------------------
# Report generation schemas
# ---------------------------------------------------------------------------


class ReportGenerateRequest(BaseModel):
    """Payload for requesting asynchronous report generation."""

    template_id: UUID | None = Field(
        default=None,
        description="Template to use for generation (optional for free-form).",
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Human-readable title for the generated report.",
    )
    output_format: str = Field(
        default="docx",
        description="Desired output format (docx, pdf, html, hwp, hwpx).",
    )
    source_document_ids: list[UUID] | None = Field(
        default=None,
        description="Documents whose content feeds into the report.",
    )
    source_chat_session_id: UUID | None = Field(
        default=None,
        description="Chat session whose conversation is used as source material.",
    )
    generation_params: dict[str, Any] | None = Field(
        default=None,
        description="Arbitrary key-value parameters for the generation engine.",
    )


class GeneratedReportResponse(BaseModel):
    """Read-only representation of a generated (or in-progress) report."""

    # DB 컬럼 ins_dt를 created_at으로 매핑
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    template_id: UUID | None = None
    organization_id: UUID
    title: str
    status: str
    output_format: str
    output_storage_path: str | None = None
    source_document_ids: list[UUID] | None = None
    source_chat_session_id: UUID | None = None
    generation_params: dict[str, Any] | None = None
    # Alembic 004에서 추가된 렌더링 기록 필드. 프론트가 보고서 방식/변수를 재확인할 수 있다.
    rendering_mode: str | None = None
    jinja2_context: dict[str, Any] | None = None
    error_message: str | None = None
    generated_by: UUID
    created_at: datetime = Field(validation_alias="ins_dt")
    completed_at: datetime | None = None


class GeneratedReportListResponse(BaseModel):
    """Paginated list of generated reports."""

    items: list[GeneratedReportResponse]
    total: int
    page: int
    size: int
