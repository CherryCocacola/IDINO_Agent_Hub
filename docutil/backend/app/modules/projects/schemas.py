"""
Pydantic v2 schemas for projects, boards, and folders.

Provides request / response models for the hierarchical
project -> board -> folder structure.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Project schemas
# ---------------------------------------------------------------------------


class ProjectCreate(BaseModel):
    """Payload for creating a new project."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    allow_original_download: bool = Field(default=True)


class ProjectUpdate(BaseModel):
    """Payload for partially updating a project."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class ProjectResponse(BaseModel):
    """프로젝트 조회 응답 스키마.

    DB 컬럼 ins_dt/upd_dt를 created_at/updated_at으로 매핑한다.
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    name: str
    description: str | None
    allow_original_download: bool
    organization_id: UUID
    created_by: UUID
    created_at: datetime = Field(validation_alias="ins_dt")
    updated_at: datetime = Field(validation_alias="upd_dt")


class ProjectListResponse(BaseModel):
    """Paginated list of projects."""

    items: list[ProjectResponse]
    total: int
    page: int
    size: int


# ---------------------------------------------------------------------------
# Board schemas
# ---------------------------------------------------------------------------


class BoardCreate(BaseModel):
    """Payload for creating a new board inside a project."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class BoardUpdate(BaseModel):
    """Payload for partially updating a board."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class BoardResponse(BaseModel):
    """보드 조회 응답 스키마.

    DB 컬럼 ins_dt/upd_dt를 created_at/updated_at으로 매핑한다.
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    project_id: UUID
    name: str
    description: str | None
    created_by: UUID
    created_at: datetime = Field(validation_alias="ins_dt")
    updated_at: datetime = Field(validation_alias="upd_dt")


class BoardListResponse(BaseModel):
    """Paginated list of boards."""

    items: list[BoardResponse]
    total: int
    page: int
    size: int


# ---------------------------------------------------------------------------
# Folder schemas
# ---------------------------------------------------------------------------


class FolderCreate(BaseModel):
    """Payload for creating a new folder inside a board."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class FolderUpdate(BaseModel):
    """Payload for partially updating a folder."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class FolderResponse(BaseModel):
    """폴더 조회 응답 스키마.

    DB 컬럼 ins_dt/upd_dt를 created_at/updated_at으로 매핑한다.
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    board_id: UUID
    name: str
    description: str | None
    created_by: UUID
    created_at: datetime = Field(validation_alias="ins_dt")
    updated_at: datetime = Field(validation_alias="upd_dt")


class FolderListResponse(BaseModel):
    """Paginated list of folders."""

    items: list[FolderResponse]
    total: int
    page: int
    size: int


# ---------------------------------------------------------------------------
# ProjectMember schemas (트랙 #101 F8)
# ---------------------------------------------------------------------------


class ProjectMemberCreate(BaseModel):
    """프로젝트 멤버 추가 요청 (트랙 #101 F8).

    role: 'member' | 'manager' (DB 컬럼 코멘트 기준).
    """

    user_id: UUID
    role: str = Field(default="member", max_length=20)


class ProjectMemberResponse(BaseModel):
    """프로젝트 멤버 조회/추가 응답 (트랙 #101 F8).

    GET /projects/{id}/members 의 평탄 응답과 호환되도록
    username/email 를 조인 결과로 함께 반환한다.
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    project_id: UUID
    user_id: UUID
    username: str
    email: str
    role: str
