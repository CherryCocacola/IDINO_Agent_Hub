"""
Student API endpoints.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas.student import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    StudentDetailResponse,
    EnrollmentWithGradeResponse,
    ActivityResponse,
    ParticipationCreate,
    ParticipationResponse,
    AchievementCreate,
    AchievementResponse,
    DashboardSummary,
)
from ..services.student_service import StudentService

logger = logging.getLogger(__name__)
router = APIRouter()


def get_student_service(db: AsyncSession = Depends(get_db)) -> StudentService:
    """Dependency for student service."""
    return StudentService(db)


# ==================== Student Endpoints ====================

@router.get("", response_model=List[StudentResponse])
async def list_students(
    department_cd: Optional[str] = None,
    current_grade: Optional[int] = None,
    skip: int = 0,
    limit: int = 20,
    service: StudentService = Depends(get_student_service),
):
    """
    List students with optional filtering.

    - **department_cd**: Filter by department code
    - **current_grade**: Filter by current grade level (1-4)
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    """
    return await service.list_students(
        department_cd=department_cd,
        current_grade=current_grade,
        skip=skip,
        limit=limit,
    )


@router.get("/{student_id}", response_model=StudentDetailResponse)
async def get_student(
    student_id: str,
    service: StudentService = Depends(get_student_service),
):
    """Get student by ID with detailed information."""
    student = await service.get_student(student_id)

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {student_id} not found",
        )

    return student


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    data: StudentCreate,
    service: StudentService = Depends(get_student_service),
):
    """Create a new student."""
    try:
        return await service.create_student(data)
    except Exception as e:
        logger.error(f"Failed to create student: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: str,
    data: StudentUpdate,
    service: StudentService = Depends(get_student_service),
):
    """Update student information."""
    student = await service.update_student(student_id, data)

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {student_id} not found",
        )

    return student


# ==================== Enrollment Endpoints ====================

@router.get("/{student_id}/courses", response_model=List[EnrollmentWithGradeResponse])
async def get_student_courses(
    student_id: str,
    service: StudentService = Depends(get_student_service),
):
    """Get all enrollments with grades for a student."""
    return await service.get_enrollments(student_id)


@router.get("/{student_id}/enrollments", response_model=List[EnrollmentWithGradeResponse])
async def get_student_enrollments(
    student_id: str,
    service: StudentService = Depends(get_student_service),
):
    """Get all enrollments with grades for a student (alias for /courses)."""
    return await service.get_enrollments(student_id)


# ==================== Activity (Program Participation) Endpoints ====================

@router.get("/{student_id}/activities", response_model=List[ActivityResponse])
async def get_student_activities(
    student_id: str,
    service: StudentService = Depends(get_student_service),
):
    """Get all program participations for a student."""
    return await service.get_activities(student_id)


@router.post(
    "/{student_id}/activities",
    response_model=ParticipationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_student_activity(
    student_id: str,
    data: ParticipationCreate,
    service: StudentService = Depends(get_student_service),
):
    """Add a program participation for a student."""
    try:
        return await service.add_activity(student_id, data)
    except Exception as e:
        logger.error(f"Failed to add activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ==================== Achievement Endpoints ====================

@router.get("/{student_id}/achievements", response_model=List[AchievementResponse])
async def get_student_achievements(
    student_id: str,
    service: StudentService = Depends(get_student_service),
):
    """Get all personal achievements for a student."""
    return await service.get_achievements(student_id)


@router.post(
    "/{student_id}/achievements",
    response_model=AchievementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_student_achievement(
    student_id: str,
    data: AchievementCreate,
    service: StudentService = Depends(get_student_service),
):
    """Add a personal achievement for a student."""
    try:
        return await service.add_achievement(student_id, data)
    except Exception as e:
        logger.error(f"Failed to add achievement: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ==================== Dashboard Endpoints ====================

@router.get("/{student_id}/dashboard", response_model=DashboardSummary)
async def get_student_dashboard(
    student_id: str,
    service: StudentService = Depends(get_student_service),
):
    """Get complete dashboard data for a student."""
    dashboard = await service.get_dashboard(student_id)

    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {student_id} not found",
        )

    return dashboard
