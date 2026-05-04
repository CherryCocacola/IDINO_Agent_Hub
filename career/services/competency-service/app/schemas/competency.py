"""
Competency-related Pydantic schemas.
Matches database schema: idino_career
"""
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# Competency Definition Schemas
class CompetencyResponse(BaseModel):
    """Competency definition response schema."""
    model_config = ConfigDict(from_attributes=True)

    competency_cd: str
    competency_nm: str
    competency_nm_en: Optional[str] = None
    definition: Optional[str] = None
    category: Optional[str] = None
    weight: Optional[float] = 0
    max_score: int = 100


# Student Competency Schemas
class StudentCompetencyResponse(BaseModel):
    """Student competency score response schema."""
    model_config = ConfigDict(from_attributes=True)

    student_competency_id: UUID
    student_id: str
    competency_cd: str
    current_score: float = 0
    target_score: float = 85
    gap_score: float = 0
    status: str = "improve"  # excellent, good, average, improve, focus
    last_assessment_date: Optional[date] = None
    trend: Optional[str] = None


class StudentCompetencyWithNameResponse(BaseModel):
    """Student competency with competency name."""
    model_config = ConfigDict(from_attributes=True)

    student_competency_id: UUID
    student_id: str
    competency_cd: str
    competency_nm: str
    competency_nm_en: Optional[str] = None
    definition: Optional[str] = None
    current_score: float = 0
    target_score: float = 85
    gap_score: float = 0
    status: str = "improve"
    trend: Optional[str] = None
    percentile: Optional[int] = None


class CompetencyReportResponse(BaseModel):
    """Full competency report response schema."""

    student_id: str
    report_date: datetime
    overall_score: float
    percentile_rank: Optional[int] = None
    competencies: List[StudentCompetencyWithNameResponse]
    improvement_suggestions: List[str] = Field(default_factory=list)


# Legacy compatibility
CompetencyDefinitionResponse = CompetencyResponse
