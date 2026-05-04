"""Pydantic v2 schemas for the FAQ module."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class FAQCreate(BaseModel):
    """Payload for creating a new FAQ entry."""

    question: str = Field(
        ..., min_length=1, max_length=2000, description="The question text."
    )
    answer: str = Field(
        ..., min_length=1, description="The answer text."
    )
    category: str | None = Field(
        default=None, max_length=128, description="Optional category label."
    )
    display_order: int = Field(
        default=0, description="Sort order within the listing."
    )
    search_scope_id: UUID | None = Field(
        default=None, description="Optionally bind this FAQ to a search scope."
    )


class FAQUpdate(BaseModel):
    """Payload for updating an existing FAQ entry (all fields optional)."""

    question: str | None = Field(
        default=None, max_length=2000, description="Updated question text."
    )
    answer: str | None = Field(default=None, description="Updated answer text.")
    category: str | None = Field(
        default=None, max_length=128, description="Updated category label."
    )
    display_order: int | None = Field(
        default=None, description="Updated sort order."
    )
    is_active: bool | None = Field(
        default=None, description="Activate or deactivate the FAQ entry."
    )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class FAQResponse(BaseModel):
    """Public representation of an FAQ entry."""

    # DB 컬럼 ins_dt/upd_dt를 created_at/updated_at으로 매핑
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    search_scope_id: UUID | None = None
    organization_id: UUID
    question: str
    answer: str
    category: str | None = None
    display_order: int
    is_active: bool
    created_at: datetime = Field(validation_alias="ins_dt")
    updated_at: datetime = Field(validation_alias="upd_dt")


class FAQListResponse(BaseModel):
    """Paginated list of FAQ entries."""

    items: list[FAQResponse]
    total: int
    page: int
    size: int
