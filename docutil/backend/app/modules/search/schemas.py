"""
Pydantic v2 schemas for the search module.

Covers hybrid, keyword, semantic, chatbot, and QA search flows as well as
search history and administrative test endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Shared / embedded schemas
# ---------------------------------------------------------------------------


class Citation(BaseModel):
    """A single source citation referencing a specific document passage."""

    document_id: UUID
    document_name: str
    page_number: int | None = None
    snippet: str = Field(
        ...,
        description="Verbatim or lightly trimmed excerpt from the source.",
    )
    relevance_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How relevant this citation is to the query (0-1).",
    )


class SearchResult(BaseModel):
    """A single ranked result returned by the search pipeline."""

    model_config = ConfigDict(from_attributes=True)

    document_id: UUID
    document_name: str
    chunk_id: UUID
    chunk_index: int
    content: str
    score: float = Field(
        ...,
        description="Fused relevance score (higher is better).",
    )
    page_number: int | None = None
    section_title: str | None = None
    chunk_type: str = Field(
        default="text",
        description="Type of chunk (text, table, image_caption, etc.).",
    )
    highlights: list[str] | None = Field(
        default=None,
        description="Highlighted snippets containing query-term matches.",
    )


# ---------------------------------------------------------------------------
# Generic search
# ---------------------------------------------------------------------------


class SearchRequest(BaseModel):
    """Payload for the primary hybrid-search endpoint."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Natural-language search query.",
    )
    search_scope_id: UUID | None = Field(
        default=None,
        description="Optional search-scope to restrict the search.",
    )
    document_ids: list[UUID] | None = Field(
        default=None,
        description="Restrict search to these specific documents.",
    )
    search_type: Literal["hybrid", "keyword", "semantic"] = Field(
        default="hybrid",
        description="Strategy used for retrieval.",
    )
    max_results: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of results to return.",
    )
    include_citations: bool = Field(
        default=True,
        description="Whether to include citation metadata in results.",
    )
    filters: dict | None = Field(
        default=None,
        description="Optional filters: date_from, date_to, formats, tags.",
    )
    agentic: bool = Field(
        default=False,
        description="Enable agentic search mode with LLM-driven query refinement.",
    )


class SearchResponse(BaseModel):
    """Envelope returned by the generic search endpoints."""

    query: str
    results: list[SearchResult]
    total_results: int
    search_type: str
    latency_ms: int = Field(
        ...,
        description="Server-side processing time in milliseconds.",
    )


# ---------------------------------------------------------------------------
# Chatbot search
# ---------------------------------------------------------------------------


class ChatbotSearchRequest(BaseModel):
    """Payload for the chatbot-oriented search endpoint."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User question posed to the chatbot.",
    )
    search_scope_id: UUID = Field(
        ...,
        description="Search scope that defines the chatbot's knowledge base.",
    )
    include_faq: bool = Field(
        default=True,
        description="Whether to check the FAQ store before searching.",
    )


class ChatbotSearchResponse(BaseModel):
    """Response from the chatbot search endpoint."""

    answer: str = Field(
        ...,
        description="LLM-generated answer grounded in retrieved context.",
    )
    citations: list[Citation] = Field(default_factory=list)
    faq_matches: list[dict] | None = Field(
        default=None,
        description="Matching FAQ entries (if include_faq was True).",
    )


# ---------------------------------------------------------------------------
# QA search
# ---------------------------------------------------------------------------


class QASearchRequest(BaseModel):
    """Payload for the QA-with-citations search endpoint."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Question to answer using retrieved documents.",
    )
    search_scope_id: UUID | None = Field(
        default=None,
        description="Optional scope restriction.",
    )
    document_ids: list[UUID] | None = Field(
        default=None,
        description="Restrict to specific documents.",
    )


class QASearchResponse(BaseModel):
    """Response from the QA search endpoint."""

    answer: str = Field(
        ...,
        description="LLM-generated answer with enforced citations.",
    )
    citations: list[Citation] = Field(default_factory=list)
    hallucination_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Estimated probability of hallucination (0 = faithful).",
    )
    model_used: str = Field(
        ...,
        description="Identifier of the LLM model used for generation.",
    )


# ---------------------------------------------------------------------------
# Keyword search
# ---------------------------------------------------------------------------


class KeywordSearchRequest(BaseModel):
    """Payload for the keyword-only (BM25) search endpoint."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Keyword query string.",
    )
    search_scope_id: UUID | None = Field(
        default=None,
        description="Optional scope restriction.",
    )
    filters: dict | None = Field(
        default=None,
        description="Additional metadata filters (key-value pairs).",
    )


# ---------------------------------------------------------------------------
# Search history
# ---------------------------------------------------------------------------


class SearchHistoryItem(BaseModel):
    """A single entry in the user's search history."""

    # DB 컬럼 ins_dt를 created_at으로 매핑
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    query: str
    search_type: str
    result_count: int
    created_at: datetime = Field(validation_alias="ins_dt")


# ---------------------------------------------------------------------------
# Admin / testing
# ---------------------------------------------------------------------------


class SearchTestRequest(BaseModel):
    """Admin-only payload for testing search quality against a scope."""

    search_scope_id: UUID = Field(
        ...,
        description="Scope to test search against.",
    )
    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Test query.",
    )
    search_type: Literal["hybrid", "keyword", "semantic"] = Field(
        default="hybrid",
        description="Search strategy to evaluate.",
    )
