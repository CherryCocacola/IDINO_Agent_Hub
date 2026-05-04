from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from uuid import UUID
from enum import Enum


class OpportunityType(str, Enum):
    """기회 유형"""
    INTERNSHIP = "internship"           # 인턴십
    CONTEST = "contest"                 # 공모전
    LAB = "lab"                         # 연구참여
    JOB = "job"                         # 채용
    SCHOLARSHIP = "scholarship"         # 장학금
    PROJECT = "project"                 # 프로젝트
    VOLUNTEER = "volunteer"             # 봉사활동
    CERTIFICATION = "certification"     # 자격증


class ApplicationStatus(str, Enum):
    """지원 상태"""
    INTERESTED = "interested"     # 관심등록
    PREPARING = "preparing"       # 준비중
    APPLIED = "applied"           # 지원완료
    REVIEWING = "reviewing"       # 심사중
    ACCEPTED = "accepted"         # 합격
    REJECTED = "rejected"         # 불합격
    WITHDRAWN = "withdrawn"       # 철회


# ============================================
# Opportunity Schemas
# ============================================

class OpportunityBase(BaseModel):
    """기회 기본 스키마"""
    opportunity_type: OpportunityType
    title: str
    description: Optional[str] = None
    organization: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    application_deadline: Optional[date] = None
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    min_gpa: Optional[float] = None
    eligible_majors: Optional[List[str]] = None
    eligible_years: Optional[List[int]] = None
    benefits: Optional[str] = None
    url: Optional[str] = None
    is_active: bool = True


class OpportunityCreate(OpportunityBase):
    """기회 생성 스키마"""
    pass


class OpportunityUpdate(BaseModel):
    """기회 수정 스키마"""
    opportunity_type: Optional[OpportunityType] = None
    title: Optional[str] = None
    description: Optional[str] = None
    organization: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    application_deadline: Optional[date] = None
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    min_gpa: Optional[float] = None
    eligible_majors: Optional[List[str]] = None
    eligible_years: Optional[List[int]] = None
    benefits: Optional[str] = None
    url: Optional[str] = None
    is_active: Optional[bool] = None


class OpportunityResponse(OpportunityBase):
    """기회 응답 스키마"""
    opportunity_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OpportunityListResponse(BaseModel):
    """기회 목록 응답"""
    opportunities: List[OpportunityResponse]
    total_count: int
    page: int
    page_size: int


# ============================================
# Recommendation Schemas
# ============================================

class OpportunityMatchScore(BaseModel):
    """기회 매칭 점수"""
    opportunity_id: UUID
    skill_match_score: float = Field(ge=0, le=100, description="스킬 매칭 점수 (0-100)")
    eligibility_score: float = Field(ge=0, le=100, description="자격 요건 점수 (0-100)")
    preference_score: float = Field(ge=0, le=100, description="선호도 점수 (0-100)")
    overall_score: float = Field(ge=0, le=100, description="종합 점수 (0-100)")
    match_reasons: List[str] = Field(default_factory=list, description="매칭 이유")
    gap_skills: List[str] = Field(default_factory=list, description="부족 스킬")


class OpportunityRecommendationResponse(BaseModel):
    """기회 추천 응답"""
    opportunity: OpportunityResponse
    match_score: OpportunityMatchScore
    recommended_actions: List[str] = Field(default_factory=list, description="추천 행동")


class RecommendationRequest(BaseModel):
    """추천 요청"""
    student_id: str
    opportunity_types: Optional[List[OpportunityType]] = None
    min_score: float = Field(default=50.0, ge=0, le=100)
    max_results: int = Field(default=10, ge=1, le=50)
    include_expired: bool = False


class RecommendationResponse(BaseModel):
    """추천 응답"""
    student_id: str
    recommendations: List[OpportunityRecommendationResponse]
    generated_at: datetime
    filters_applied: Dict[str, Any] = Field(default_factory=dict)


# ============================================
# Application Schemas
# ============================================

class ApplicationCreate(BaseModel):
    """지원 생성"""
    student_id: str
    opportunity_id: UUID
    status: ApplicationStatus = ApplicationStatus.INTERESTED
    notes: Optional[str] = None


class ApplicationUpdate(BaseModel):
    """지원 수정"""
    status: Optional[ApplicationStatus] = None
    notes: Optional[str] = None
    applied_at: Optional[datetime] = None
    result_at: Optional[datetime] = None


class ApplicationResponse(BaseModel):
    """지원 응답"""
    application_id: UUID
    student_id: str
    opportunity_id: UUID
    opportunity_title: Optional[str] = None
    opportunity_type: Optional[OpportunityType] = None
    organization: Optional[str] = None
    status: ApplicationStatus
    notes: Optional[str] = None
    applied_at: Optional[datetime] = None
    result_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================
# Search Schemas
# ============================================

class OpportunitySearchRequest(BaseModel):
    """기회 검색 요청"""
    query: Optional[str] = None
    opportunity_types: Optional[List[OpportunityType]] = None
    skills: Optional[List[str]] = None
    location: Optional[str] = None
    min_deadline_days: Optional[int] = None
    is_active: bool = True
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: str = Field(default="deadline", description="deadline, created, title")
    sort_order: str = Field(default="asc", description="asc, desc")
