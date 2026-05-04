"""
Alumni Service Pydantic Schemas.
Matches database schema: idino_career
"""
from datetime import datetime
from typing import List, Dict, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class AlumniCohortResponse(BaseModel):
    """Alumni cohort statistics response."""
    model_config = ConfigDict(from_attributes=True)

    cohort_id: UUID
    department_cd: str
    graduation_year: int
    cohort_size: int = 0
    avg_gpa: Optional[float] = None
    employment_rate: Optional[float] = None
    avg_salary: Optional[float] = None
    top_employers: Optional[List[str]] = None
    top_roles: Optional[List[str]] = None
    avg_competency_scores: Dict[str, Any] = Field(default_factory=dict)


class SuccessPatternResponse(BaseModel):
    """Success pattern response."""
    model_config = ConfigDict(from_attributes=True)

    pattern_id: UUID
    pattern_nm: str
    pattern_type: Optional[str] = None
    department_cd: Optional[str] = None
    role_cd: Optional[str] = None
    description: Optional[str] = None
    typical_gpa_range: Optional[str] = None
    key_courses: Optional[List[str]] = None
    key_activities: Optional[List[str]] = None
    key_skills: Optional[List[str]] = None
    timeline: Optional[Dict[str, Any]] = None
    success_rate: Optional[float] = None
    sample_size: int = 0


class AlumniBenchmarkResponse(BaseModel):
    """Alumni benchmark summary for a department."""
    department_cd: str

    # Overall Statistics
    total_cohorts: int = 0
    avg_employment_rate: Optional[float] = None

    # Cohort data
    cohorts: List[AlumniCohortResponse] = Field(default_factory=list)

    # Top Success Patterns
    success_patterns: List[SuccessPatternResponse] = Field(default_factory=list)


class CompetencyComparison(BaseModel):
    """Competency comparison between student and alumni cohort."""
    competency_cd: str
    competency_nm: str
    student_score: float
    alumni_avg_score: float
    gap: float
    status: str  # above, below, at


class StudentComparisonResponse(BaseModel):
    """Student vs alumni comparison response."""
    student_id: str
    department_cd: str
    target_role_cd: Optional[str] = None

    # Student Current State
    student_gpa: Optional[float] = None
    student_competencies: Dict[str, float] = Field(default_factory=dict)

    # Alumni Benchmark
    alumni_avg_gpa_range: Optional[str] = None
    alumni_competencies: Dict[str, float] = Field(default_factory=dict)

    # Comparison
    competency_comparisons: List[CompetencyComparison] = Field(default_factory=list)

    # Gap Analysis
    overall_readiness_score: float = 0.0
    improvement_areas: List[str] = Field(default_factory=list)

    # Student extras (credits, certifications, activities)
    student_credits: Optional[int] = None
    student_certifications: Optional[int] = None
    student_activities: Optional[int] = None

    # Alumni average extras
    alumni_avg_credits: Optional[int] = None
    alumni_avg_certifications: Optional[int] = None
    alumni_avg_activities: Optional[int] = None

    # Best Matching Pattern
    best_matching_pattern: Optional[SuccessPatternResponse] = None
