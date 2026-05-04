"""Pydantic v2 schemas for the agents module."""

from __future__ import annotations

import uuid
from uuid import UUID
from datetime import datetime


from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class AgentCreate(BaseModel):
    """Payload for creating a new AI agent."""

    name: str = Field(..., min_length=1, max_length=255, description="Agent name.")
    description: str | None = Field(default=None, max_length=2000, description="Agent description.")
    agent_type: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="에이전트 유형 (예: chatbot, report, proposal, minutes 등 자유 입력).",
    )
    system_prompt: str = Field(
        ...,
        min_length=1,
        description="System prompt that defines the agent's behavior.",
    )
    llm_provider: str | None = Field(
        default=None,
        max_length=50,
        description="LLM provider (openai, azure_openai, gemini, anthropic). null이면 시스템 기본값.",
    )
    llm_model: str = Field(
        default="gpt-4o",
        max_length=255,
        description="LLM model identifier.",
    )
    temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="LLM temperature (0.0–2.0).",
    )
    max_tokens: int = Field(
        default=4096,
        ge=1,
        le=128000,
        description="Maximum tokens for LLM response.",
    )


class AgentUpdate(BaseModel):
    """Payload for partially updating an AI agent."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    agent_type: str | None = Field(
        default=None,
        max_length=20,
    )
    system_prompt: str | None = Field(default=None, min_length=1)
    llm_provider: str | None = Field(default=None, max_length=50)
    llm_model: str | None = Field(default=None, max_length=255)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1, le=128000)
    is_active: bool | None = Field(default=None)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class AgentResponse(BaseModel):
    """Read-only representation of an AI agent."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    organization_id: UUID
    name: str
    description: str | None = None
    agent_type: str
    system_prompt: str
    llm_provider: str | None = None
    llm_model: str
    temperature: float
    max_tokens: int
    is_active: bool
    created_by: UUID
    created_at: datetime = Field(validation_alias="ins_dt")
    updated_at: datetime = Field(validation_alias="upd_dt")


class AgentListResponse(BaseModel):
    """Paginated list of AI agents."""

    items: list[AgentResponse]
    total: int
    page: int
    size: int
