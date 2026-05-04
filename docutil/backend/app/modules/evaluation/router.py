"""
Evaluation API router.

Endpoints:
  GET  /evaluation/runs       — list run summaries
  GET  /evaluation/logs       — list individual evaluation logs
  GET  /evaluation/trend      — daily trend data for charts
  POST /evaluation/run        — trigger manual evaluation run
  GET  /evaluation/config     — get org metric weights
  PUT  /evaluation/config     — update org metric weights
  GET  /evaluation/questions  — get default test question set
"""

from __future__ import annotations

import uuid as uuid_mod
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import get_db_session, require_role

from .models import EvaluationConfig
from .schemas import (
    EvaluationConfigResponse,
    EvaluationConfigUpdate,
    EvaluationLogFilter,
    EvaluationLogListResponse,
    EvaluationLogResponse,
    EvaluationRunListResponse,
    EvaluationRunRequest,
    EvaluationTrendResponse,
)
from .service import EvaluationService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.security import TokenData

router = APIRouter(prefix="", tags=["evaluation"])

_require_admin = require_role(["super_admin", "admin", "org_admin"])


# ------------------------------------------------------------------
# Run summaries
# ------------------------------------------------------------------


@router.get(
    "/evaluation/runs",
    response_model=EvaluationRunListResponse,
    summary="최근 평가 실행 목록",
)
async def list_runs(
    limit: int = Query(30, ge=1, le=100),
    db: "AsyncSession" = Depends(get_db_session),
    current_user: "TokenData" = Depends(_require_admin),
) -> EvaluationRunListResponse:
    """Return aggregated summaries of recent evaluation runs."""
    items = await EvaluationService.get_run_summaries(
        db,
        org_id=current_user.organization_id,
        limit=limit,
    )
    return EvaluationRunListResponse(items=items, total=len(items))


# ------------------------------------------------------------------
# Individual logs
# ------------------------------------------------------------------


@router.get(
    "/evaluation/logs",
    response_model=EvaluationLogListResponse,
    summary="평가 로그 목록",
)
async def list_logs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    run_id: str | None = Query(None),
    run_type: str | None = Query(None),
    has_hallucination: bool | None = Query(None),
    min_score: float | None = Query(None, ge=0.0, le=1.0),
    max_score: float | None = Query(None, ge=0.0, le=1.0),
    db: "AsyncSession" = Depends(get_db_session),
    current_user: "TokenData" = Depends(_require_admin),
) -> EvaluationLogListResponse:
    """Return filtered, paginated evaluation logs."""
    filters = EvaluationLogFilter(
        run_id=run_id,
        run_type=run_type,
        has_hallucination=has_hallucination,
        min_score=min_score,
        max_score=max_score,
    )
    logs, total = await EvaluationService.get_logs(
        db,
        org_id=current_user.organization_id,
        filters=filters,
        page=page,
        size=size,
    )
    return EvaluationLogListResponse(
        items=[EvaluationLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        size=size,
    )


# ------------------------------------------------------------------
# Trend data
# ------------------------------------------------------------------


@router.get(
    "/evaluation/trend",
    response_model=EvaluationTrendResponse,
    summary="평가 점수 추이 (최근 N일)",
)
async def get_trend(
    days: int = Query(30, ge=1, le=365),
    db: "AsyncSession" = Depends(get_db_session),
    current_user: "TokenData" = Depends(_require_admin),
) -> EvaluationTrendResponse:
    """Return daily average scores for trend chart."""
    data = await EvaluationService.get_trend(
        db,
        org_id=current_user.organization_id,
        days=days,
    )
    return EvaluationTrendResponse(data=data)


# ------------------------------------------------------------------
# Manual run trigger
# ------------------------------------------------------------------


@router.post(
    "/evaluation/run",
    summary="수동 평가 실행",
    status_code=202,
)
async def trigger_run(
    body: EvaluationRunRequest | None = None,
    current_user: "TokenData" = Depends(_require_admin),
) -> dict:
    """Trigger a manual evaluation run via Celery."""
    from app.workers.evaluation_runner import run_evaluation

    run_id = uuid_mod.uuid4().hex[:16]
    questions = None
    if body and body.questions:
        questions = body.questions

    run_evaluation.delay(
        str(current_user.organization_id),
        run_id,
        "manual",
        questions,
    )
    return {"run_id": run_id, "status": "queued", "message": "평가가 시작되었습니다."}


# ------------------------------------------------------------------
# Config (metric weights)
# ------------------------------------------------------------------


@router.get(
    "/evaluation/config",
    response_model=EvaluationConfigResponse,
    summary="평가 가중치 설정 조회",
)
async def get_config(
    db: "AsyncSession" = Depends(get_db_session),
    current_user: "TokenData" = Depends(_require_admin),
) -> EvaluationConfigResponse:
    """Get current metric weights for the organization."""
    config = await EvaluationService.get_config(db, current_user.organization_id)
    if config is None:
        # Return defaults
        from .constants import DEFAULT_METRIC_WEIGHTS

        config = EvaluationConfig(
            id=uuid_mod.uuid4(),
            organization_id=current_user.organization_id,
            context_relevancy_weight=DEFAULT_METRIC_WEIGHTS["context_relevancy"],
            answer_faithfulness_weight=DEFAULT_METRIC_WEIGHTS["answer_faithfulness"],
            answer_relevancy_weight=DEFAULT_METRIC_WEIGHTS["answer_relevancy"],
            hallucination_weight=DEFAULT_METRIC_WEIGHTS["hallucination"],
        )
    return EvaluationConfigResponse.model_validate(config)


@router.put(
    "/evaluation/config",
    response_model=EvaluationConfigResponse,
    summary="평가 가중치 설정 수정",
)
async def update_config(
    body: EvaluationConfigUpdate,
    db: "AsyncSession" = Depends(get_db_session),
    current_user: "TokenData" = Depends(_require_admin),
) -> EvaluationConfigResponse:
    """Update metric weights for the organization."""
    total = (
        body.context_relevancy_weight
        + body.answer_faithfulness_weight
        + body.answer_relevancy_weight
        + body.hallucination_weight
    )
    if abs(total - 1.0) > 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"가중치 합계가 1.0이어야 합니다. (현재: {total:.2f})",
        )
    config = await EvaluationService.upsert_config(
        db,
        org_id=current_user.organization_id,
        context_relevancy_weight=body.context_relevancy_weight,
        answer_faithfulness_weight=body.answer_faithfulness_weight,
        answer_relevancy_weight=body.answer_relevancy_weight,
        hallucination_weight=body.hallucination_weight,
    )
    return EvaluationConfigResponse.model_validate(config)


# ------------------------------------------------------------------
# Default test questions
# ------------------------------------------------------------------


@router.get(
    "/evaluation/questions",
    summary="기본 테스트 질문 목록",
)
async def get_questions(
    current_user: "TokenData" = Depends(_require_admin),
) -> dict:
    """Return the default test question set."""
    questions = EvaluationService.load_test_questions()
    return {"questions": questions, "total": len(questions)}
