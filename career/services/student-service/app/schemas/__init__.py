"""
Student Service Schemas.
"""
from .student import (
    StudentBase,
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    StudentDetailResponse,
    CourseRecordCreate,
    CourseRecordResponse,
    ActivityCreate,
    ActivityResponse,
    AchievementCreate,
    AchievementResponse,
    DepartmentResponse,
    CurriculumResponse,
)

__all__ = [
    "StudentBase",
    "StudentCreate",
    "StudentUpdate",
    "StudentResponse",
    "StudentDetailResponse",
    "CourseRecordCreate",
    "CourseRecordResponse",
    "ActivityCreate",
    "ActivityResponse",
    "AchievementCreate",
    "AchievementResponse",
    "DepartmentResponse",
    "CurriculumResponse",
]
