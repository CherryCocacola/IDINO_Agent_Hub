"""
Pydantic v2 schemas for the chat module.

Covers session management, message history, and WebSocket message framing
for the streaming chat interface.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Chat sessions
# ---------------------------------------------------------------------------


class ChatSessionCreate(BaseModel):
    """Payload for creating a new chat session."""

    title: str | None = Field(
        default=None,
        max_length=255,
        description=(
            "Human-readable title for the session. When omitted the system "
            "generates one from the first message."
        ),
    )
    search_scope_id: UUID | None = Field(
        default=None,
        description="Search scope that restricts which documents are queried.",
    )
    scoped_document_ids: list[UUID] | None = Field(
        default=None,
        description="Restrict the session to these specific documents.",
    )


class ChatSessionResponse(BaseModel):
    """Read-only representation of a chat session."""

    # DB 컬럼 ins_dt/upd_dt를 created_at/updated_at으로 매핑
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    user_id: UUID
    organization_id: UUID
    search_scope_id: UUID | None = None
    title: str | None = None
    scoped_document_ids: list[UUID] | None = None
    is_active: bool = True
    created_at: datetime = Field(validation_alias="ins_dt")
    updated_at: datetime = Field(validation_alias="upd_dt")


class ChatSessionListResponse(BaseModel):
    """Paginated list of chat sessions."""

    items: list[ChatSessionResponse]
    total: int
    page: int
    size: int


# ---------------------------------------------------------------------------
# Chat messages
# ---------------------------------------------------------------------------


class ChatMessageResponse(BaseModel):
    """Read-only representation of a single chat message."""

    # DB 컬럼 ins_dt를 created_at으로 매핑
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    session_id: UUID
    role: str = Field(
        ...,
        description="Message role: 'user', 'assistant', or 'system'.",
    )
    content: str
    citations: list[dict] | None = Field(
        default=None,
        description="Source citations attached to assistant messages.",
    )
    model_used: str | None = Field(
        default=None,
        description="LLM model identifier used for this response.",
    )
    token_count_input: int | None = Field(
        default=None,
        description="Number of input tokens consumed.",
    )
    token_count_output: int | None = Field(
        default=None,
        description="Number of output tokens generated.",
    )
    latency_ms: int | None = Field(
        default=None,
        description="Server-side processing time in milliseconds.",
    )
    hallucination_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Estimated hallucination probability (0 = faithful).",
    )
    created_at: datetime = Field(validation_alias="ins_dt")  # DB 컬럼 ins_dt 매핑


class ChatMessageListResponse(BaseModel):
    """Paginated list of chat messages within a session."""

    items: list[ChatMessageResponse]
    total: int
    page: int
    size: int


# ---------------------------------------------------------------------------
# WebSocket message framing
# ---------------------------------------------------------------------------


class ChatMessageCreate(BaseModel):
    """Payload for sending a message via REST (WebSocket fallback)."""

    content: str = Field(..., min_length=1, max_length=10000)


class ChatMessageSendResponse(BaseModel):
    """Response wrapper for the REST send-message endpoint."""

    message: ChatMessageResponse


# ---------------------------------------------------------------------------
# WebSocket message framing
# ---------------------------------------------------------------------------


class WebSocketMessage(BaseModel):
    """Inbound message from the client over the WebSocket connection."""

    type: str = Field(
        ...,
        description=(
            "Message type.  Currently supported: 'message' (send a chat "
            "message), 'ping' (keep-alive)."
        ),
    )
    content: str | None = Field(
        default=None,
        description="The user message text (required when type='message').",
    )
    options: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Optional per-message settings (e.g. temperature, max_tokens)."
        ),
    )


class WebSocketResponse(BaseModel):
    """Outbound message sent to the client over the WebSocket connection."""

    type: Literal["status", "chunk", "citations", "metadata", "done"] = Field(
        ...,
        description=(
            "Payload type:\n"
            "  - status   : connection / processing status update\n"
            "  - chunk    : a streamed text fragment of the answer\n"
            "  - citations: citation data for the completed answer\n"
            "  - metadata : token counts, latency, hallucination score\n"
            "  - done     : signals the response is complete"
        ),
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Type-specific payload.",
    )
