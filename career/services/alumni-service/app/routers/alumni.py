"""
Alumni API endpoints.
Matches database schema: idino_career
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas.alumni import (
    AlumniCohortResponse,
    AlumniBenchmarkResponse,
    SuccessPatternResponse,
    StudentComparisonResponse,
)
from ..services.alumni_service import AlumniService

logger = logging.getLogger(__name__)
router = APIRouter()


def get_alumni_service(db: AsyncSession = Depends(get_db)) -> AlumniService:
    """Dependency for alumni service."""
    return AlumniService(db)


# ==================== Cohort Endpoints ====================

@router.get("/cohorts", response_model=List[AlumniCohortResponse])
async def get_cohorts(
    department_cd: Optional[str] = None,
    service: AlumniService = Depends(get_alumni_service),
):
    """
    Get all alumni cohorts, optionally filtered.

    Returns list of k-anonymized alumni cohort statistics
    grouped by department and graduation year.
    """
    cohorts = await service.get_cohorts(
        department_cd=department_cd,
    )

    return cohorts


# ==================== Benchmark Endpoints ====================

@router.get("/benchmark/{department_cd}", response_model=AlumniBenchmarkResponse)
async def get_benchmark(
    department_cd: str,
    role_cd: Optional[str] = None,
    service: AlumniService = Depends(get_alumni_service),
):
    """
    Get alumni benchmark for a department.

    Returns aggregated statistics and top success patterns
    for alumni from the specified department.
    """
    benchmark = await service.get_benchmark(
        department_cd=department_cd,
        role_cd=role_cd,
    )

    if benchmark.total_cohorts == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No alumni data found for department {department_cd}",
        )

    return benchmark


# ==================== Pattern Endpoints ====================

@router.get("/patterns/{department_cd}", response_model=List[SuccessPatternResponse])
async def get_patterns(
    department_cd: str,
    role_cd: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
    service: AlumniService = Depends(get_alumni_service),
):
    """
    Get success patterns for a department.

    Returns ranked list of career success patterns
    identified from alumni data analysis.
    """
    patterns = await service.get_patterns(
        department_cd=department_cd,
        role_cd=role_cd,
        limit=limit,
    )

    if not patterns:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No success patterns found for department {department_cd}",
        )

    return patterns


# ==================== Comparison Endpoints ====================

@router.get("/compare/{student_id}", response_model=StudentComparisonResponse)
async def compare_with_alumni(
    student_id: str,
    target_role_cd: Optional[str] = None,
    service: AlumniService = Depends(get_alumni_service),
):
    """
    Compare student with alumni benchmark.

    Fetches student's current academic and competency status,
    compares with successful alumni profiles, and provides
    recommendations for improvement.
    """
    try:
        comparison = await service.compare_with_student(
            student_id=student_id,
            target_role_cd=target_role_cd,
        )
        return comparison
    except Exception as e:
        logger.error(f"Failed to compare student {student_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
