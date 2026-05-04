"""Roadmap Schemas"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import date
from enum import Enum


class ItemType(str, Enum):
    COURSE = "course"
    ACTIVITY = "activity"
    CERTIFICATE = "certificate"
    INTERNSHIP = "internship"
    PROJECT = "project"


class ItemStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class RoadmapItemResponse(BaseModel):
    item_id: str
    item_type: ItemType
    title: str
    description: Optional[str] = None
    grade_level: int = Field(ge=1, le=4)
    semester: int = Field(ge=1, le=2)
    status: ItemStatus = ItemStatus.PLANNED
    priority: int = Field(default=2, ge=1, le=3)
    competency_contributions: Optional[Dict[str, float]] = None
    skill_contributions: Optional[Dict[str, float]] = None
    prerequisites: Optional[List[str]] = None
    deadline: Optional[date] = None
    is_ai_recommended: bool = False
    recommendation_reason: Optional[str] = None


class SemesterRoadmap(BaseModel):
    semester: int = Field(ge=1, le=2)
    items: List[RoadmapItemResponse]
    total_credits: int = 0
    target_gpa: Optional[float] = None
    key_milestones: List[str] = []


class GradeRoadmapResponse(BaseModel):
    student_id: str
    grade_level: int = Field(ge=1, le=4)
    grade_name: str
    semesters: List[SemesterRoadmap]
    competency_targets: Dict[str, float] = {}
    skill_targets: Dict[str, int] = {}
    career_path: Optional[str] = None
    completion_rate: float = 0.0


class FullRoadmapResponse(BaseModel):
    """Full roadmap response with all grades and overall progress"""
    student_id: str
    roadmaps: List[GradeRoadmapResponse]
    overall_completion: float = 0.0
    current_grade: int = 1
    current_semester: int = 1


class RoadmapGenerateRequest(BaseModel):
    student_id: str
    target_role: Optional[str] = None
    career_goal: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    constraints: Optional[Dict[str, Any]] = None


class RoadmapGenerateResponse(BaseModel):
    student_id: str
    roadmaps: List[GradeRoadmapResponse]
    ai_summary: str
    key_recommendations: List[str]
    alternative_paths: List[Dict[str, Any]] = []
    confidence_score: float = Field(ge=0.0, le=1.0)


class RoadmapItemCreate(BaseModel):
    """Schema for creating a new roadmap item"""
    student_id: str
    item_type: ItemType
    title: str
    description: Optional[str] = None
    grade_level: int = Field(ge=1, le=4)
    semester: int = Field(ge=1, le=2)
    status: ItemStatus = ItemStatus.PLANNED
    priority: int = Field(default=2, ge=1, le=3)
    is_ai_recommended: bool = False
    recommendation_reason: Optional[str] = None
