from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from uuid import UUID
from enum import Enum


class InterventionType(str, Enum):
    MEETING = "meeting"           # 상담
    EMAIL = "email"               # 이메일
    REFERRAL = "referral"         # 의뢰/연계
    RESOURCE = "resource"         # 자료 제공
    FOLLOWUP = "followup"         # 후속 조치


class InterventionStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AdvisorAssignmentResponse(BaseModel):
    assignment_id: UUID
    advisor_id: UUID
    advisor_name: Optional[str] = None
    student_id: str
    student_name: Optional[str] = None
    assigned_at: datetime
    is_primary: bool = True
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class InterventionCreate(BaseModel):
    advisor_id: str
    student_id: str
    intervention_type: InterventionType
    title: str
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    priority: int = Field(default=2, ge=1, le=5)


class InterventionUpdate(BaseModel):
    status: Optional[InterventionStatus] = None
    outcome: Optional[str] = None
    completed_at: Optional[datetime] = None
    follow_up_needed: Optional[bool] = None
    next_action: Optional[str] = None


class InterventionResponse(BaseModel):
    intervention_id: UUID
    advisor_id: str
    student_id: str
    student_name: Optional[str] = None
    intervention_type: InterventionType
    title: str
    description: Optional[str] = None
    status: InterventionStatus
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    outcome: Optional[str] = None
    follow_up_needed: bool = False
    next_action: Optional[str] = None
    priority: int
    created_at: datetime

    class Config:
        from_attributes = True


class CohortSnapshotResponse(BaseModel):
    snapshot_id: UUID
    advisor_id: str
    snapshot_date: date
    total_students: int
    at_risk_count: int
    on_track_count: int
    excelling_count: int
    avg_gpa: float
    avg_progress: float
    key_metrics: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True


class AdvisorNoteCreate(BaseModel):
    advisor_id: str
    student_id: str
    note_type: str = "general"
    content: str
    is_private: bool = False
    tags: Optional[List[str]] = None


class AdvisorNoteResponse(BaseModel):
    note_id: UUID
    advisor_id: str
    student_id: str
    student_name: Optional[str] = None
    note_type: str
    content: str
    is_private: bool
    tags: Optional[List[str]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StudentSummary(BaseModel):
    student_id: str
    student_name: str
    major: Optional[str] = None
    grade: int
    gpa: float
    risk_level: str  # low, medium, high, critical
    active_alerts: int = 0
    last_interaction: Optional[datetime] = None
    progress_percentage: float = 0
    needs_attention: bool = False


class CohortAnalytics(BaseModel):
    total_students: int
    by_risk_level: Dict[str, int]
    by_grade: Dict[int, int]
    avg_gpa: float
    avg_progress: float
    interventions_this_month: int
    pending_followups: int


class CohortDashboard(BaseModel):
    advisor_id: str
    advisor_name: Optional[str] = None
    analytics: CohortAnalytics
    students_needing_attention: List[StudentSummary]
    recent_interventions: List[InterventionResponse]
    upcoming_interventions: List[InterventionResponse]
    recent_notes: List[AdvisorNoteResponse]
    generated_at: datetime


# Meeting Types
class MeetingStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MeetingType(str, Enum):
    IN_PERSON = "in_person"
    VIDEO = "video"
    PHONE = "phone"


class MeetingCreate(BaseModel):
    advisor_id: str
    student_id: str
    title: str
    description: Optional[str] = None
    scheduled_at: datetime
    duration_minutes: int = Field(default=30, ge=15, le=180)
    location: Optional[str] = None
    meeting_type: MeetingType = MeetingType.IN_PERSON


class MeetingResponse(BaseModel):
    meeting_id: UUID
    advisor_id: str
    student_id: str
    student_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    scheduled_at: datetime
    duration_minutes: int
    location: Optional[str] = None
    meeting_type: MeetingType
    status: MeetingStatus
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
