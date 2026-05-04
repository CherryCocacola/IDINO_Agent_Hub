"""
University API endpoints.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status

from ..connectors import UniversityConnector
from ..schemas.integration import (
    UniversityStudentResponse,
    UniversityCourseResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Create connector instance
connector = UniversityConnector()


@router.get("/student/{student_id}", response_model=UniversityStudentResponse)
async def get_student(student_id: str):
    """
    Get student academic information from university system.

    Returns student profile, GPA, and course records.
    """
    student = await connector.get_student(student_id)

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {student_id} not found"
        )

    return student


@router.get("/student/{student_id}/courses", response_model=List[UniversityCourseResponse])
async def get_student_courses(
    student_id: str,
    semester: Optional[str] = None,
):
    """
    Get student course records.

    Can be filtered by semester (e.g., '2023-1', '2023-2').
    """
    courses = await connector.get_student_courses(
        student_id=student_id,
        semester=semester,
    )

    if not courses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No courses found for student {student_id}"
        )

    return courses


@router.get("/departments")
async def get_departments():
    """
    Get list of departments.

    Returns department IDs and names.
    """
    departments = await connector.get_departments()
    return {"departments": departments}
