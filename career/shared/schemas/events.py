"""
Event schemas for Kafka message payloads.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    """Base schema for all events."""

    event_id: str
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_service: str
    payload: Dict[str, Any]

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StudentCreatedEvent(BaseModel):
    """Event payload when a new student is created."""

    student_id: str
    name: str
    department_id: str
    major: str
    grade: int
    career_goal: Optional[str] = None


class StudentUpdatedEvent(BaseModel):
    """Event payload when student info is updated."""

    student_id: str
    updated_fields: List[str]
    gpa: Optional[float] = None
    total_credits: Optional[int] = None
    career_goal: Optional[str] = None
    target_job_codes: Optional[List[str]] = None


class CourseCompletedEvent(BaseModel):
    """Event payload when a course is completed."""

    student_id: str
    course_code: str
    course_name: str
    semester: str
    credits: int
    grade: str
    grade_point: float
    competency_mappings: Dict[str, float]  # competency_id -> weight


class ActivityCompletedEvent(BaseModel):
    """Event payload when an activity is completed."""

    student_id: str
    activity_id: str
    activity_type: str
    activity_name: str
    hours_completed: int
    competency_gains: Dict[str, float]  # competency_id -> points


class CompetencyCalculatedEvent(BaseModel):
    """Event payload when competencies are recalculated."""

    student_id: str
    calculation_date: datetime
    scores: Dict[str, float]  # competency_name -> score
    percentile_ranks: Dict[str, int]  # competency_name -> percentile
    trigger: str  # What triggered the calculation


class RoadmapGeneratedEvent(BaseModel):
    """Event payload when a new roadmap is generated."""

    roadmap_id: str
    student_id: str
    target_job_code: str
    target_job_name: str
    semester_count: int
    confidence_score: float
    generation_method: str  # "ai" or "rule_based"


class AIRecommendationEvent(BaseModel):
    """Event payload for AI recommendation results."""

    student_id: str
    recommendation_type: str  # "action", "course", "activity", "job"
    recommendations: List[Dict[str, Any]]
    reasoning: Optional[str] = None
    confidence_score: float
    model_version: str
