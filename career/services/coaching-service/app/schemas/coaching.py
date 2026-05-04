from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from uuid import UUID
from enum import Enum


class GoalStatus(str, Enum):
    """목표 상태"""
    DRAFT = "draft"           # 초안
    PENDING = "pending"       # 대기중 (데이터베이스 호환)
    ACTIVE = "active"         # 활성
    IN_PROGRESS = "in_progress"  # 진행중 (데이터베이스 호환)
    PAUSED = "paused"         # 일시중지
    COMPLETED = "completed"   # 완료
    ABANDONED = "abandoned"   # 포기


class GoalPriority(str, Enum):
    """목표 우선순위"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CheckinMood(str, Enum):
    """체크인 기분"""
    GREAT = "great"           # 매우 좋음
    GOOD = "good"             # 좋음
    NEUTRAL = "neutral"       # 보통
    STRUGGLING = "struggling" # 어려움
    BLOCKED = "blocked"       # 막힘


# ============================================
# Goal Schemas
# ============================================

class GoalBase(BaseModel):
    """목표 기본 스키마"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    goal_type: str = Field(default="career", description="career, skill, academic, personal")
    priority: GoalPriority = GoalPriority.MEDIUM
    target_date: Optional[date] = None
    target_role_cd: Optional[str] = None
    related_skills: Optional[List[str]] = None
    success_criteria: Optional[str] = None
    motivation: Optional[str] = None


class GoalCreate(GoalBase):
    """목표 생성"""
    student_id: str


class GoalUpdate(BaseModel):
    """목표 수정"""
    title: Optional[str] = None
    description: Optional[str] = None
    goal_type: Optional[str] = None
    priority: Optional[GoalPriority] = None
    status: Optional[GoalStatus] = None
    target_date: Optional[date] = None
    target_role_cd: Optional[str] = None
    related_skills: Optional[List[str]] = None
    success_criteria: Optional[str] = None
    motivation: Optional[str] = None
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)


class GoalResponse(BaseModel):
    """목표 응답"""
    goal_id: UUID
    student_id: str
    title: str
    description: Optional[str] = None
    goal_type: str
    priority: Any  # Can be int or string
    status: GoalStatus
    progress_percentage: float = 0
    target_date: Optional[date] = None
    target_role_cd: Optional[str] = None
    related_skills: Optional[List[str]] = None
    success_criteria: Optional[str] = None
    motivation: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Related data
    plan_items_count: int = 0
    completed_items_count: int = 0
    checkins_count: int = 0
    last_checkin_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================
# Plan Item Schemas
# ============================================

class PlanItemBase(BaseModel):
    """플랜 항목 기본 스키마"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    order_index: int = 0
    due_date: Optional[date] = None
    estimated_hours: Optional[float] = None
    related_skill_cd: Optional[str] = None


class PlanItemCreate(PlanItemBase):
    """플랜 항목 생성"""
    goal_id: UUID


class PlanItemUpdate(BaseModel):
    """플랜 항목 수정"""
    title: Optional[str] = None
    description: Optional[str] = None
    order_index: Optional[int] = None
    due_date: Optional[date] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    is_completed: Optional[bool] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None


class PlanItemResponse(PlanItemBase):
    """플랜 항목 응답"""
    plan_id: UUID
    goal_id: UUID
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    actual_hours: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================
# Check-in Schemas
# ============================================

class CheckinBase(BaseModel):
    """체크인 기본 스키마"""
    mood: CheckinMood
    progress_note: Optional[str] = None
    blockers: Optional[str] = None
    next_steps: Optional[str] = None
    reflection: Optional[str] = None


class CheckinCreate(CheckinBase):
    """체크인 생성"""
    goal_id: UUID


class CheckinResponse(CheckinBase):
    """체크인 응답"""
    checkin_id: UUID
    goal_id: UUID
    goal_title: Optional[str] = None
    ai_feedback: Optional[str] = None
    ai_suggestions: Optional[List[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# Retrospective Schemas
# ============================================

class RetrospectiveBase(BaseModel):
    """회고 기본 스키마"""
    what_went_well: Optional[str] = None
    what_could_improve: Optional[str] = None
    lessons_learned: Optional[str] = None
    next_goals: Optional[str] = None
    satisfaction_rating: int = Field(default=3, ge=1, le=5)


class RetrospectiveCreate(RetrospectiveBase):
    """회고 생성"""
    goal_id: UUID


class RetrospectiveResponse(RetrospectiveBase):
    """회고 응답"""
    retrospective_id: UUID
    goal_id: UUID
    goal_title: Optional[str] = None
    ai_analysis: Optional[str] = None
    ai_recommendations: Optional[List[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# Coaching Session Schemas
# ============================================

class CoachingSessionResponse(BaseModel):
    """코칭 세션 전체 응답"""
    goal: GoalResponse
    plan_items: List[PlanItemResponse]
    recent_checkins: List[CheckinResponse]
    retrospective: Optional[RetrospectiveResponse] = None
    ai_insights: Optional[Dict[str, Any]] = None


class AICoachRequest(BaseModel):
    """AI 코치 요청"""
    student_id: str
    goal_id: Optional[UUID] = None
    query_type: str = Field(
        default="advice",
        description="advice, plan_suggest, motivation, blockers, review"
    )
    context: Optional[str] = None
    include_history: bool = True


class AICoachResponse(BaseModel):
    """AI 코치 응답"""
    message: str
    suggestions: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    resources: List[Dict[str, str]] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    generated_at: datetime


class GoalProgressSummary(BaseModel):
    """목표 진행 요약"""
    student_id: str
    total_goals: int
    active_goals: int
    completed_goals: int
    average_progress: float
    total_checkins: int
    streak_days: int = 0
    goals: List[GoalResponse]
    recent_activity: List[Dict[str, Any]] = Field(default_factory=list)
