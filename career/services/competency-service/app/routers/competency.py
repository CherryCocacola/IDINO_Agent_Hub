"""
Competency API endpoints.
Matches database schema: idino_career
"""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas.competency import (
    CompetencyResponse,
    StudentCompetencyWithNameResponse,
    CompetencyReportResponse,
)
from ..services.competency_service import CompetencyService

logger = logging.getLogger(__name__)
router = APIRouter()


def get_competency_service(db: AsyncSession = Depends(get_db)) -> CompetencyService:
    """Dependency for competency service."""
    return CompetencyService(db)


# ==================== Definition Endpoints ====================

@router.get("/definitions", response_model=List[CompetencyResponse])
async def get_competencies(
    service: CompetencyService = Depends(get_competency_service),
):
    """Get all competency definitions."""
    return await service.get_competencies()


# ==================== Student Competency Endpoints ====================

@router.get("/{student_id}/scores", response_model=List[StudentCompetencyWithNameResponse])
async def get_student_scores(
    student_id: str,
    service: CompetencyService = Depends(get_competency_service),
):
    """Get competency scores for a student."""
    scores = await service.get_student_competencies(student_id)
    if not scores:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No competency data found for student {student_id}",
        )
    return scores


# ==================== Report Endpoints ====================

@router.get("/{student_id}/report", response_model=CompetencyReportResponse)
async def get_report(
    student_id: str,
    service: CompetencyService = Depends(get_competency_service),
):
    """Get comprehensive competency report for a student."""
    report = await service.get_report(student_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No competency data found for student {student_id}",
        )

    return report
