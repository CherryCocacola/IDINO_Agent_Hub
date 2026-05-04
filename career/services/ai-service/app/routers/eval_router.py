"""
Evaluation Router for AI Recommendation Quality Assessment
Phase 4: Eval System API Endpoints

Provides endpoints for:
- Submitting user feedback on recommendations
- Retrieving evaluation metrics
- Managing evaluation test cases
- Running quality assessments
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..services.eval_service import EvalService

router = APIRouter(prefix="/eval", tags=["evaluation"])


# ==========================================
# Request/Response Models
# ==========================================

class FeedbackRequest(BaseModel):
    """Request model for submitting feedback."""
    student_id: str = Field(..., description="Student ID providing feedback")
    item_id: int = Field(..., description="Recommendation item ID")
    feedback_type: str = Field(
        ...,
        description="Type of feedback: accepted, rejected, viewed, clicked, rated"
    )
    rating: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="Rating from 1-5 (required for 'rated' feedback_type)"
    )
    comment: Optional[str] = Field(None, description="Optional comment text")
    context_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional context data"
    )


class FeedbackResponse(BaseModel):
    """Response model for feedback submission."""
    status: str
    feedback_id: Optional[int]
    message: str


class MetricsResponse(BaseModel):
    """Response model for evaluation metrics."""
    period_days: int
    run_metrics: Dict[str, Any]
    feedback_metrics: Dict[str, Any]
    quality_indicators: Dict[str, Any]
    generated_at: str


class FeedbackStatsResponse(BaseModel):
    """Response model for feedback statistics."""
    period_days: int
    stats_by_action_type: Dict[str, Dict[str, Any]]
    generated_at: str


class RunDetailsResponse(BaseModel):
    """Response model for run details."""
    run_id: int
    student_id: str
    run_type: str
    model_version: str
    latency_ms: int
    created_at: Optional[str]
    items: List[Dict[str, Any]]


class EvalCaseResponse(BaseModel):
    """Response model for evaluation case."""
    case_id: int
    case_name: str
    case_type: str
    input_data: Dict[str, Any]
    expected_output: Dict[str, Any]
    quality_criteria: Dict[str, Any]


class EvalResultRequest(BaseModel):
    """Request model for saving evaluation result."""
    case_id: int = Field(..., description="Test case ID")
    run_id: int = Field(..., description="Recommendation run ID")
    actual_output: Dict[str, Any] = Field(..., description="Actual output from run")
    passed: bool = Field(..., description="Whether the test passed")
    score: float = Field(..., ge=0, le=100, description="Quality score (0-100)")
    details: Dict[str, Any] = Field(default={}, description="Detailed results")


class EvalResultResponse(BaseModel):
    """Response model for evaluation result."""
    status: str
    result_id: Optional[int]
    message: str


# ==========================================
# API Endpoints
# ==========================================

@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit user feedback on a recommendation.

    Feedback types:
    - accepted: User accepted/acted on the recommendation
    - rejected: User dismissed the recommendation
    - viewed: User viewed the recommendation details
    - clicked: User clicked on the recommendation
    - rated: User provided a rating (requires rating field)
    """
    # Validate rating requirement
    if request.feedback_type == "rated" and request.rating is None:
        raise HTTPException(
            status_code=400,
            detail="Rating is required for 'rated' feedback type"
        )

    eval_service = EvalService(db)
    feedback_id = await eval_service.record_feedback(
        student_id=request.student_id,
        item_id=request.item_id,
        feedback_type=request.feedback_type,
        rating=request.rating,
        comment=request.comment,
        context_data=request.context_data,
    )

    if feedback_id:
        return FeedbackResponse(
            status="success",
            feedback_id=feedback_id,
            message="Feedback recorded successfully"
        )
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to record feedback"
        )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get comprehensive evaluation metrics.

    Returns metrics including:
    - Run statistics (count, latency, tokens)
    - Feedback metrics (ratings, acceptance rate)
    - Quality indicators (engagement rate)
    """
    eval_service = EvalService(db)
    metrics = await eval_service.calculate_metrics(days=days)

    if "error" in metrics:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate metrics: {metrics['error']}"
        )

    return MetricsResponse(
        period_days=metrics["period_days"],
        run_metrics=metrics["run_metrics"],
        feedback_metrics=metrics["feedback_metrics"],
        quality_indicators=metrics["quality_indicators"],
        generated_at=metrics["generated_at"],
    )


@router.get("/feedback-stats", response_model=FeedbackStatsResponse)
async def get_feedback_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get feedback statistics grouped by action type.

    Returns statistics including:
    - Average rating per action type
    - Acceptance/rejection counts
    - Click and view counts
    """
    eval_service = EvalService(db)
    stats = await eval_service.get_feedback_stats(days=days)

    return FeedbackStatsResponse(
        period_days=days,
        stats_by_action_type=stats,
        generated_at=datetime.utcnow().isoformat(),
    )


@router.get("/runs/{run_id}", response_model=RunDetailsResponse)
async def get_run_details(
    run_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed information about a specific recommendation run.

    Returns:
    - Run metadata (model, latency, timestamps)
    - Associated recommendation items
    """
    eval_service = EvalService(db)
    run_details = await eval_service.get_run_details(run_id)

    if not run_details:
        raise HTTPException(
            status_code=404,
            detail=f"Run {run_id} not found"
        )

    return RunDetailsResponse(
        run_id=run_details["run_id"],
        student_id=run_details["student_id"],
        run_type=run_details["run_type"],
        model_version=run_details["model_version"],
        latency_ms=run_details["latency_ms"],
        created_at=run_details["created_at"],
        items=run_details["items"],
    )


@router.get("/cases", response_model=List[EvalCaseResponse])
async def get_eval_cases(
    case_type: Optional[str] = Query(None, description="Filter by case type"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get evaluation test cases.

    Optional filtering by case_type (e.g., 'competency', 'career', 'constraint').
    """
    eval_service = EvalService(db)
    cases = await eval_service.get_eval_cases(case_type=case_type)

    return [
        EvalCaseResponse(
            case_id=case["case_id"],
            case_name=case["case_name"],
            case_type=case["case_type"],
            input_data=case["input_data"],
            expected_output=case["expected_output"],
            quality_criteria=case["quality_criteria"],
        )
        for case in cases
    ]


@router.post("/results", response_model=EvalResultResponse)
async def save_eval_result(
    request: EvalResultRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Save an evaluation result for a test case run.

    Used to track quality test results over time.
    """
    eval_service = EvalService(db)
    result_id = await eval_service.save_eval_result(
        case_id=request.case_id,
        run_id=request.run_id,
        actual_output=request.actual_output,
        passed=request.passed,
        score=request.score,
        details=request.details,
    )

    if result_id:
        return EvalResultResponse(
            status="success",
            result_id=result_id,
            message="Evaluation result saved successfully"
        )
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to save evaluation result"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for eval service."""
    return {
        "status": "healthy",
        "service": "eval",
        "timestamp": datetime.utcnow().isoformat(),
    }
