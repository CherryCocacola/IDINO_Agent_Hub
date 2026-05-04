"""
Pydantic v2 schemas for document management.

Covers document responses, upload responses, chunk responses,
and bulk-upload result payloads.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# 문서 공개 범위 6단계 리터럴 타입 (Pydantic 검증용).
# models.py 의 DocumentVisibility enum 과 동기화되어야 함.
VISIBILITY_VALUES = Literal[
    "public",
    "all_departments",
    "department_only",
    "project_only",
    "confidential",
    "hidden",
]


# ---------------------------------------------------------------------------
# Document schemas
# ---------------------------------------------------------------------------


class DocumentResponse(BaseModel):
    """Full read-only representation of a stored document."""

    # DB 컬럼 ins_dt/upd_dt를 created_at/updated_at으로 매핑
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    folder_id: UUID | None = None
    organization_id: UUID
    name: str
    original_filename: str
    format: str
    file_size_bytes: int
    status: str
    processing_error: str | None
    page_count: int | None
    chunk_count: int | None
    tags: list[str] | None
    language: str | None
    uploaded_by: UUID
    # 부서/프로젝트 권한 필드 (Alembic 002 에서 도입)
    visibility: str = "department_only"
    department_id: UUID | None = None
    project_id: UUID | None = None
    processing_started_at: datetime | None
    processing_completed_at: datetime | None
    created_at: datetime = Field(validation_alias="ins_dt")
    updated_at: datetime = Field(validation_alias="upd_dt")


class DocumentListResponse(BaseModel):
    """Paginated list of documents."""

    items: list[DocumentResponse]
    total: int
    page: int
    size: int


# ---------------------------------------------------------------------------
# Detail response — 상세 다이얼로그용 표시 정보 포함
# ---------------------------------------------------------------------------
#
# 일반 DocumentResponse 는 ORM 그대로의 ID 기반이라 화면에서 보여줄 때 UUID 가
# 그대로 노출된다 ("업로드자: 00000000-..."). 상세 다이얼로그에서는 사람이
# 읽을 수 있는 이름과 공개 가능한 대상 목록을 함께 내려준다.
#
# - uploaded_by_name        : 업로더의 username (한글 이름이 들어감)
# - department_name         : department_only 일 때 대상 부서 이름
# - visible_department_names: 가시성에 따라 실제로 볼 수 있는 부서 이름 목록
#                             (department_only 는 부서 + 하위, all_departments 는 조직 전체)
# - project_name            : project_only 일 때 프로젝트 이름
# - project_member_names    : project_only 일 때 볼 수 있는 사용자명 목록
#                             (직접 멤버 + 참여 부서의 사용자)
# - visibility_summary      : 한 줄 요약 (UI 라벨로 사용)


class DocumentDetailResponse(DocumentResponse):
    """단건 조회용 확장 응답 — 화면 표시용 부가 정보를 포함한다."""

    uploaded_by_name: str | None = None
    department_name: str | None = None
    project_name: str | None = None
    visible_department_names: list[str] = Field(default_factory=list)
    project_member_names: list[str] = Field(default_factory=list)
    visibility_summary: str | None = None


# ---------------------------------------------------------------------------
# Upload schemas
# ---------------------------------------------------------------------------


class DocumentUploadResponse(BaseModel):
    """Immediate response returned after a single document upload."""

    id: UUID
    name: str
    status: str
    job_id: str


class BulkUploadItemError(BaseModel):
    """Details for a single file that failed during bulk upload."""

    filename: str
    error: str


class BulkUploadResponse(BaseModel):
    """Aggregated result of a bulk upload operation."""

    uploaded: list[DocumentUploadResponse]
    failed: list[BulkUploadItemError]


# ---------------------------------------------------------------------------
# Chunk schemas
# ---------------------------------------------------------------------------


class DocumentChunkResponse(BaseModel):
    """A single content chunk extracted from a document."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    chunk_index: int
    chunk_type: str
    content: str
    content_length: int
    page_number: int | None
    section_title: str | None
