from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from uuid import UUID
from enum import Enum


class RiskSeverity(str, Enum):
    """위험 심각도"""
    LOW = "low"           # 낮음 - 모니터링 필요
    MEDIUM = "medium"     # 중간 - 주의 필요
    HIGH = "high"         # 높음 - 즉시 조치 필요
    CRITICAL = "critical" # 심각 - 긴급 개입 필요


class RiskCategory(str, Enum):
    """위험 카테고리"""
    GPA = "gpa"                     # 학점 관련
    CREDITS = "credits"             # 학점 이수 관련
    ATTENDANCE = "attendance"       # 출석 관련
    PREREQUISITE = "prerequisite"   # 선수과목 관련
    GRADUATION = "graduation"       # 졸업요건 관련
    CAREER = "career"               # 진로 관련
    SKILL_GAP = "skill_gap"         # 스킬 갭 관련


class AlertStatus(str, Enum):
    """알림 상태"""
    ACTIVE = "active"       # 활성
    ACKNOWLEDGED = "acknowledged"  # 확인됨
    RESOLVED = "resolved"   # 해결됨
    DISMISSED = "dismissed" # 무시됨


# ============================================
# Risk Alert Schemas
# ============================================

class RiskAlertBase(BaseModel):
    """위험 알림 기본 스키마"""
    category: RiskCategory
    severity: RiskSeverity
    title: str
    description: str
    recommendation: Optional[str] = None
    related_entity_type: Optional[str] = None  # course, skill, goal, etc.
    related_entity_id: Optional[str] = None
    due_date: Optional[date] = None


class RiskAlertCreate(RiskAlertBase):
    """위험 알림 생성"""
    student_id: str


class RiskAlertUpdate(BaseModel):
    """위험 알림 수정"""
    status: Optional[AlertStatus] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_note: Optional[str] = None


class RiskAlertResponse(RiskAlertBase):
    """위험 알림 응답"""
    alert_id: UUID
    student_id: str
    status: AlertStatus = AlertStatus.ACTIVE
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_note: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================
# Constraint Check Schemas
# ============================================

class ConstraintCheckResponse(BaseModel):
    """제약조건 체크 응답"""
    check_id: UUID
    student_id: str
    constraint_type: str
    constraint_name: str
    is_satisfied: bool
    current_value: Optional[str] = None
    required_value: Optional[str] = None
    gap_description: Optional[str] = None
    checked_at: datetime

    class Config:
        from_attributes = True


# ============================================
# Prerequisite Rule Schemas
# ============================================

class PrerequisiteRuleResponse(BaseModel):
    """선수과목 규칙 응답"""
    rule_id: UUID
    course_cd: str
    course_nm: Optional[str] = None
    prerequisite_cd: str
    prerequisite_nm: Optional[str] = None
    rule_type: str = Field(description="required, recommended, corequisite")
    min_grade: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================
# Student Risk Profile
# ============================================

class RiskRecommendation(BaseModel):
    """위험 해결 권장사항"""
    priority: int
    category: RiskCategory
    action: str
    description: str
    deadline: Optional[date] = None
    resources: List[str] = Field(default_factory=list)


class StudentRiskProfile(BaseModel):
    """학생 위험 프로필"""
    student_id: str
    student_name: Optional[str] = None
    overall_risk_score: float = Field(ge=0, le=100, description="0=안전, 100=매우 위험")
    risk_level: RiskSeverity

    # Category scores
    gpa_risk_score: float = 0
    credits_risk_score: float = 0
    prerequisite_risk_score: float = 0
    graduation_risk_score: float = 0
    career_risk_score: float = 0

    # Active alerts
    active_alerts: List[RiskAlertResponse] = Field(default_factory=list)
    total_active_alerts: int = 0
    critical_alerts: int = 0
    high_alerts: int = 0

    # Constraints
    unsatisfied_constraints: List[ConstraintCheckResponse] = Field(default_factory=list)

    # Recommendations
    recommendations: List[RiskRecommendation] = Field(default_factory=list)

    # Meta
    last_analyzed_at: datetime
    next_review_date: Optional[date] = None


# ============================================
# Risk Analysis Request/Response
# ============================================

class RiskAnalysisRequest(BaseModel):
    """위험 분석 요청"""
    student_id: str
    categories: Optional[List[RiskCategory]] = None
    include_recommendations: bool = True
    force_refresh: bool = False


class RiskAnalysisResponse(BaseModel):
    """위험 분석 응답"""
    profile: StudentRiskProfile
    analysis_summary: str
    key_risks: List[str]
    immediate_actions: List[str]
    generated_at: datetime
