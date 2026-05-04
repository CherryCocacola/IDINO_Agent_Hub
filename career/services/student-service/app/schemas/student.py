"""
Student-related Pydantic schemas.
Matches database schema: idino_career
"""
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict


# College Schemas (matches actual DB schema)
class CollegeResponse(BaseModel):
    """College response schema."""
    model_config = ConfigDict(from_attributes=True)

    college_cd: str
    college_nm: str
    college_nm_en: Optional[str] = None


# Department Schemas (matches actual DB schema)
class DepartmentResponse(BaseModel):
    """Department response schema."""
    model_config = ConfigDict(from_attributes=True)

    department_cd: str
    department_nm: str
    department_nm_en: Optional[str] = None
    college: Optional[CollegeResponse] = None


# Student Schemas (matches actual DB schema)
class StudentBase(BaseModel):
    """Base student schema."""

    student_nm: str = Field(..., min_length=1, max_length=50)
    department_cd: Optional[str] = None
    current_grade: Optional[int] = Field(None, ge=1, le=4)
    current_semester: Optional[int] = Field(None, ge=1, le=8)
    career_goal: Optional[str] = None


class StudentCreate(StudentBase):
    """Student creation schema."""

    student_id: str = Field(..., min_length=5, max_length=20)
    university_cd: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    admission_year: int
    birth_date: Optional[date] = None
    gender: Optional[str] = None


class StudentUpdate(BaseModel):
    """Student update schema."""

    student_nm: Optional[str] = Field(None, min_length=1, max_length=50)
    current_grade: Optional[int] = Field(None, ge=1, le=4)
    current_semester: Optional[int] = Field(None, ge=1, le=8)
    career_goal: Optional[str] = None
    status: Optional[str] = None


class StudentResponse(BaseModel):
    """Student response schema."""
    model_config = ConfigDict(from_attributes=True)

    student_id: str
    student_nm: str
    department_cd: Optional[str] = None
    current_grade: Optional[int] = None
    current_semester: Optional[int] = None
    career_goal: Optional[str] = None
    status: str = "enrolled"
    ins_dt: Optional[datetime] = None


class StudentDetailResponse(StudentResponse):
    """Detailed student response with related data."""

    university_cd: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    admission_year: Optional[int] = None
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    department: Optional[DepartmentResponse] = None
    enrollment_count: int = 0
    activity_count: int = 0
    achievement_count: int = 0
    # Calculated fields for dashboard
    gpa: Optional[float] = None  # Calculated from tb_grade
    completed_credits: int = 0   # Sum of earned credits
    summary: Optional["StudentSummaryResponse"] = None


class StudentSummaryResponse(BaseModel):
    """Student summary response schema."""
    model_config = ConfigDict(from_attributes=True)

    completed_credits: int = 0
    remaining_credits: Optional[int] = None
    major_credits: int = 0
    liberal_credits: int = 0
    elective_credits: int = 0
    graduation_readiness_pct: Optional[float] = None


# Course & Enrollment Schemas
class CourseResponse(BaseModel):
    """Course response schema."""
    model_config = ConfigDict(from_attributes=True)

    course_id: str
    course_cd: str
    course_nm: str
    course_nm_en: Optional[str] = None
    credits: int
    course_type: Optional[str] = None
    target_grade: Optional[int] = None
    description: Optional[str] = None


class EnrollmentResponse(BaseModel):
    """Enrollment response schema."""
    model_config = ConfigDict(from_attributes=True)

    enrollment_id: UUID
    student_id: str
    course_offering_id: UUID
    status_cd: str = "ENROLLED"
    ins_dt: Optional[datetime] = None


class GradeResponse(BaseModel):
    """Grade response schema."""
    model_config = ConfigDict(from_attributes=True)

    grade_id: UUID
    enrollment_id: UUID
    attendance_score: Optional[float] = None
    assignment_score: Optional[float] = None
    midterm_score: Optional[float] = None
    final_score: Optional[float] = None
    total_score: Optional[float] = None
    letter_grade: Optional[str] = None
    grade_point: Optional[float] = None


class EnrollmentWithGradeResponse(BaseModel):
    """Enrollment with grade and course info."""
    model_config = ConfigDict(from_attributes=True)

    enrollment_id: UUID  # DDL uses UUID
    course_nm: str
    course_cd: str
    credits: int
    course_type: Optional[str] = None  # e.g. '1'=전공필수, '2'=전공선택, '3'=교양필수, '4'=교양선택
    term_nm: Optional[str] = None  # Updated: DB uses term_nm
    letter_grade: Optional[str] = None
    grade_point: Optional[float] = None
    status_cd: Optional[str] = None  # Can be NULL in database


# Activity Schemas
class ProgramResponse(BaseModel):
    """Program response schema."""
    model_config = ConfigDict(from_attributes=True)

    program_id: str
    program_nm: str
    program_nm_en: Optional[str] = None
    program_type: Optional[str] = None
    host_organization: Optional[str] = None
    description: Optional[str] = None


class ActivityResponse(BaseModel):
    """Activity response schema - matches tb_activity table."""
    model_config = ConfigDict(from_attributes=True)

    activity_id: UUID
    student_id: str
    program_cd: Optional[str] = None
    activity_type: str
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    hours: Optional[float] = None
    achievement: Optional[str] = None
    status: str = "completed"
    verified: str = "N"
    ins_dt: Optional[datetime] = None


class ParticipationResponse(BaseModel):
    """Program participation response schema (legacy - use ActivityResponse)."""
    model_config = ConfigDict(from_attributes=True)

    participation_id: UUID
    student_id: str
    program_id: str
    program: Optional[ProgramResponse] = None
    participation_date: Optional[date] = None
    hours_completed: int = 0
    score: Optional[float] = None
    certificate_url: Optional[str] = None
    feedback: Optional[str] = None
    ins_dt: Optional[datetime] = None


class ParticipationCreate(BaseModel):
    """Participation creation schema."""

    program_id: str
    participation_date: Optional[date] = None
    hours_completed: int = 0
    score: Optional[float] = None
    certificate_url: Optional[str] = None
    feedback: Optional[str] = None


# Achievement Schemas
class AchievementResponse(BaseModel):
    """Achievement response schema."""
    model_config = ConfigDict(from_attributes=True)

    achievement_id: UUID  # DDL uses UUID
    student_id: str
    achievement_type: str
    achievement_nm: str  # Mapped from DB 'title'
    issuing_org: Optional[str] = None  # Mapped from DB 'issuer'
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None  # Mapped from DB 'expire_date'
    level: Optional[str] = None
    score: Optional[str] = None
    certificate_url: Optional[str] = None  # Not in DB
    verified_fg: Optional[str] = "N"  # Mapped from DB 'verified'
    ins_dt: Optional[datetime] = None


class AchievementCreate(BaseModel):
    """Achievement creation schema."""

    achievement_type: str = Field(..., max_length=50)
    achievement_nm: str = Field(..., max_length=200)
    issuing_org: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    level: Optional[str] = None
    score: Optional[str] = None
    certificate_url: Optional[str] = None


# Dashboard Schemas
class DashboardSummary(BaseModel):
    """Dashboard summary for a student."""

    student: StudentDetailResponse
    enrollments: List[EnrollmentWithGradeResponse] = Field(default_factory=list)
    activities: List[ActivityResponse] = Field(default_factory=list)
    achievements: List[AchievementResponse] = Field(default_factory=list)


# Legacy compatibility aliases
CourseRecordCreate = ParticipationCreate  # Alias for backward compatibility
CourseRecordResponse = EnrollmentWithGradeResponse
ActivityCreate = ParticipationCreate
# ActivityResponse is defined above (line 180) - do NOT alias to ParticipationResponse
CurriculumResponse = CourseResponse
