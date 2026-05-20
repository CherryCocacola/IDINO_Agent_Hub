"""
Evaluation Pydantic schemas for request / response validation.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class EvaluationLogResponse(BaseModel):
    """Single evaluation log entry."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    organization_id: UUID
    run_id: str
    question: str
    answer: str
    contexts: dict | None = None
    context_relevancy: float
    answer_faithfulness: float
    answer_relevancy: float
    hallucination_score: float
    has_hallucination: bool
    hallucination_evidence: dict | None = None
    composite_score: float
    judge_details: dict | None = None
    run_type: str
    question_index: int
    created_at: datetime = Field(validation_alias="ins_dt")

    # 트랙 #105 Phase B.5 — DB 에 잔존한 list 형 데이터를 dict 로 정규화
    # (구버전 service.py:250 default 가 `[]` 였어서 빈 list 가 다수 저장됨)
    @field_validator("hallucination_evidence", mode="before")
    @classmethod
    def _normalize_evidence(cls, v):
        if v is None:
            return None
        if isinstance(v, list):
            # 빈 list → None, 값 있는 list → {"items": [...]} 로 dict 래핑
            return {"items": v} if v else None
        if isinstance(v, dict):
            return v
        # 그 외 타입은 pydantic 이 dict 타입 검증으로 거부
        return v


class EvaluationLogListResponse(BaseModel):
    """Paginated evaluation logs."""

    items: list[EvaluationLogResponse]
    total: int
    page: int
    size: int


class EvaluationRunSummary(BaseModel):
    """Aggregated summary for a single evaluation run."""

    run_id: str
    run_type: str
    created_at: datetime
    question_count: int
    avg_context_relevancy: float
    avg_answer_faithfulness: float
    avg_answer_relevancy: float
    avg_hallucination_score: float
    avg_composite_score: float
    hallucination_count: int


class EvaluationRunListResponse(BaseModel):
    """List of run summaries."""

    items: list[EvaluationRunSummary]
    total: int


class EvaluationTrendPoint(BaseModel):
    """Single data point for trend chart."""

    date: str
    avg_context_relevancy: float
    avg_answer_faithfulness: float
    avg_answer_relevancy: float
    avg_hallucination_score: float
    avg_composite_score: float


class EvaluationTrendResponse(BaseModel):
    """Trend data for recharts."""

    data: list[EvaluationTrendPoint]


# ---------------------------------------------------------------------------
# Config schemas
# ---------------------------------------------------------------------------


class EvaluationConfigResponse(BaseModel):
    """Current metric weights for an organization."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    organization_id: UUID
    context_relevancy_weight: float
    answer_faithfulness_weight: float
    answer_relevancy_weight: float
    hallucination_weight: float


class EvaluationConfigUpdate(BaseModel):
    """Update metric weights."""

    context_relevancy_weight: float = Field(ge=0.0, le=1.0, default=0.25)
    answer_faithfulness_weight: float = Field(ge=0.0, le=1.0, default=0.30)
    answer_relevancy_weight: float = Field(ge=0.0, le=1.0, default=0.25)
    hallucination_weight: float = Field(ge=0.0, le=1.0, default=0.20)


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class EvaluationRunRequest(BaseModel):
    """Manual evaluation run trigger."""

    questions: list[str] | None = Field(
        default=None,
        description="Custom questions. If null, uses default test set.",
    )


class EvaluationLogFilter(BaseModel):
    """Query filters for evaluation logs."""

    run_id: str | None = None
    run_type: str | None = None
    has_hallucination: bool | None = None
    min_score: float | None = Field(default=None, ge=0.0, le=1.0)
    max_score: float | None = Field(default=None, ge=0.0, le=1.0)
