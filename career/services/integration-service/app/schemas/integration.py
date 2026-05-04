"""
Integration Service Pydantic Schemas.
"""
from datetime import datetime
from typing import List, Dict, Optional, Any

from pydantic import BaseModel, Field


# ==================== Worknet (직업정보) Schemas ====================

class WorknetJobResponse(BaseModel):
    """Worknet job information response."""

    job_code: str
    job_name: str
    job_name_en: Optional[str] = None
    category: str
    description: str

    # Requirements
    required_education: Optional[str] = None
    required_certifications: List[str] = Field(default_factory=list)
    required_skills: List[str] = Field(default_factory=list)
    required_competencies: Dict[str, float] = Field(default_factory=dict)

    # Employment Information
    avg_salary: Optional[int] = None
    employment_outlook: Optional[str] = None
    job_growth_rate: Optional[float] = None

    # Related Information
    related_majors: List[str] = Field(default_factory=list)
    related_jobs: List[str] = Field(default_factory=list)

    # Metadata
    last_updated: Optional[datetime] = None


class WorknetSearchRequest(BaseModel):
    """Worknet job search request."""

    query: str
    category: Optional[str] = None
    education_level: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=50)


class WorknetSearchResponse(BaseModel):
    """Worknet job search response."""

    query: str
    total_count: int
    results: List[WorknetJobResponse] = Field(default_factory=list)


# ==================== University (학사정보) Schemas ====================

class UniversityCourseResponse(BaseModel):
    """University course information."""

    course_code: str
    course_name: str
    department_id: str
    credits: int
    course_type: str  # 전필, 전선, 교양
    semester: str
    grade: Optional[str] = None
    grade_point: Optional[float] = None
    competency_mappings: Dict[str, float] = Field(default_factory=dict)


class UniversityStudentResponse(BaseModel):
    """University student academic information."""

    student_id: str
    name: str
    department_id: str
    department_name: str
    major: Optional[str] = None
    grade: int
    status: str  # 재학, 휴학, 졸업

    # Academic Summary
    total_credits: int
    gpa: float
    semester_gpa: Optional[float] = None

    # Course Records
    courses: List[UniversityCourseResponse] = Field(default_factory=list)

    # Registration Info
    admission_year: int
    expected_graduation: Optional[str] = None


# ==================== HRD-Net (졸업생/취업정보) Schemas ====================

class HRDAlumniResponse(BaseModel):
    """HRD-Net alumni employment information."""

    alumni_id: str
    department_id: str
    graduation_year: int

    # Employment Status
    is_employed: bool
    employment_date: Optional[datetime] = None
    company_name: Optional[str] = None
    job_category: Optional[str] = None
    job_title: Optional[str] = None

    # Academic Background
    final_gpa: Optional[float] = None
    total_credits: Optional[int] = None

    # Certifications and Activities
    certifications: List[str] = Field(default_factory=list)
    activities: List[str] = Field(default_factory=list)

    # Competency Profile
    final_competency_scores: Dict[str, float] = Field(default_factory=dict)


# ==================== Sync Schemas ====================

class SyncRequest(BaseModel):
    """Data synchronization request."""

    source: str  # worknet, university, hrd
    target_ids: Optional[List[str]] = None
    full_sync: bool = False


class SyncResponse(BaseModel):
    """Data synchronization response."""

    source: str
    status: str  # success, partial, failed
    records_synced: int
    records_failed: int
    errors: List[str] = Field(default_factory=list)
    sync_timestamp: datetime = Field(default_factory=datetime.utcnow)
