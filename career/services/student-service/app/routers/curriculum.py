"""
Curriculum API endpoints.
"""
import logging
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas.student import CurriculumResponse, DepartmentResponse
from ..services.student_service import StudentService

logger = logging.getLogger(__name__)
router = APIRouter()


def get_student_service(db: AsyncSession = Depends(get_db)) -> StudentService:
    """Dependency for student service."""
    return StudentService(db)


@router.get("/departments", response_model=List[DepartmentResponse])
async def list_departments(
    service: StudentService = Depends(get_student_service),
):
    """Get all active departments."""
    return await service.get_departments()


@router.get("/{department_id}", response_model=List[CurriculumResponse])
async def get_department_curriculum(
    department_id: str,
    service: StudentService = Depends(get_student_service),
):
    """Get curriculum for a specific department."""
    return await service.get_curriculum(department_id)
