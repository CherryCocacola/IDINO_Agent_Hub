"""
Pydantic v2 schemas for search scopes and their environment settings.

A *search scope* defines a configurable search context over projects,
boards, or folders, together with tuning knobs for LLM, retrieval,
and UI features.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Environment configuration (embedded in SearchScope)
# ---------------------------------------------------------------------------


class SearchScopeEnvironment(BaseModel):
    """Tunable environment settings for a search scope."""

    # Feature toggles
    chatbot_enabled: bool = Field(default=False)
    chatbot_faq_template: str | None = Field(default=None, max_length=5000)
    qa_enabled: bool = Field(default=False)
    qa_prompt_template: str | None = Field(default=None, max_length=5000)
    qa_llm_model: str | None = Field(default=None, max_length=255)
    keyword_search_enabled: bool = Field(default=False)
    agent_enabled: bool = Field(default=False)

    # Chunking parameters
    chunk_size: int = Field(default=512, ge=64, le=8192)
    chunk_overlap: int = Field(default=64, ge=0, le=1024)

    # Retrieval weights (should sum to 1.0 ideally)
    title_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    keyword_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    content_weight: float = Field(default=0.4, ge=0.0, le=1.0)

    # Retrieval limits
    max_results: int = Field(default=10, ge=1, le=100)
    similarity_threshold: float = Field(default=0.5, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Create / Update
# ---------------------------------------------------------------------------


class SearchScopeCreate(BaseModel):
    """Payload for creating a new search scope."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    project_id: UUID | None = Field(default=None)
    board_id: UUID | None = Field(default=None)
    folder_id: UUID | None = Field(default=None)

    # Optional environment fields (set at creation time)
    chatbot_enabled: bool | None = Field(default=None)
    qa_enabled: bool | None = Field(default=None)
    keyword_search_enabled: bool | None = Field(default=None)
    agent_enabled: bool | None = Field(default=None)
    chunk_size: int | None = Field(default=None, ge=64, le=8192)
    chunk_overlap: int | None = Field(default=None, ge=0, le=1024)
    title_weight: float | None = Field(default=None, ge=0.0, le=1.0)
    keyword_weight: float | None = Field(default=None, ge=0.0, le=1.0)
    content_weight: float | None = Field(default=None, ge=0.0, le=1.0)
    max_results: int | None = Field(default=None, ge=1, le=100)
    similarity_threshold: float | None = Field(default=None, ge=0.0, le=1.0)


class SearchScopeUpdate(BaseModel):
    """Payload for partially updating a search scope (metadata + environment)."""

    # Metadata
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    project_id: UUID | None = Field(default=None)
    board_id: UUID | None = Field(default=None)
    folder_id: UUID | None = Field(default=None)

    # Environment / feature toggles
    chatbot_enabled: bool | None = Field(default=None)
    qa_enabled: bool | None = Field(default=None)
    keyword_search_enabled: bool | None = Field(default=None)
    agent_enabled: bool | None = Field(default=None)

    # Chunking
    chunk_size: int | None = Field(default=None, ge=64, le=8192)
    chunk_overlap: int | None = Field(default=None, ge=0, le=1024)

    # Retrieval weights
    title_weight: float | None = Field(default=None, ge=0.0, le=1.0)
    keyword_weight: float | None = Field(default=None, ge=0.0, le=1.0)
    content_weight: float | None = Field(default=None, ge=0.0, le=1.0)

    # Retrieval limits
    max_results: int | None = Field(default=None, ge=1, le=100)
    similarity_threshold: float | None = Field(default=None, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------


class SearchScopeResponse(BaseModel):
    """Full read-only representation of a search scope."""

    # DB 컬럼 ins_dt/upd_dt를 created_at/updated_at으로 매핑
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    name: str
    description: str | None
    organization_id: UUID
    created_by: UUID
    project_id: UUID | None
    board_id: UUID | None
    folder_id: UUID | None
    location_path: str | None = None

    # Environment / configuration fields
    chatbot_enabled: bool
    chatbot_faq_template: str | None
    qa_enabled: bool
    qa_prompt_template: str | None
    qa_llm_model: str | None
    keyword_search_enabled: bool
    agent_enabled: bool
    chunk_size: int
    chunk_overlap: int
    title_weight: float
    keyword_weight: float
    content_weight: float
    max_results: int
    similarity_threshold: float

    created_at: datetime = Field(validation_alias="ins_dt")
    updated_at: datetime = Field(validation_alias="upd_dt")


class SearchScopeListResponse(BaseModel):
    """Paginated list of search scopes."""

    items: list[SearchScopeResponse]
    total: int
    page: int
    size: int


# ---------------------------------------------------------------------------
# Lightweight option schemas (for dropdowns / selectors)
# ---------------------------------------------------------------------------


class SearchScopeOption(BaseModel):
    """Simplified search scope for dropdown selectors."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    location_path: str | None = None


class LocationOption(BaseModel):
    """A project, board, or folder available as a search scope location."""

    id: UUID
    name: str
    type: str
    path: str | None = None
