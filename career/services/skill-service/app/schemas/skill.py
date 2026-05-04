from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID


# ============================================
# Skill Schemas
# ============================================

class SkillBase(BaseModel):
    skill_cd: str
    skill_nm: str
    skill_nm_en: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[int] = Field(None, ge=1, le=5)


class SkillResponse(SkillBase):
    synonyms: Optional[List[str]] = None

    class Config:
        from_attributes = True


class StudentSkillBase(BaseModel):
    skill_cd: str
    current_level: int = Field(1, ge=1, le=5)
    target_level: int = Field(3, ge=1, le=5)


class StudentSkillResponse(StudentSkillBase):
    student_skill_id: UUID
    skill_nm: Optional[str] = None
    evidence_count: int = 0
    last_verified_date: Optional[date] = None
    verification_source: Optional[str] = None
    trend: str = "stable"
    gap: int = 0  # target_level - current_level

    class Config:
        from_attributes = True


class StudentSkillUpdate(BaseModel):
    current_level: Optional[int] = Field(None, ge=1, le=5)
    target_level: Optional[int] = Field(None, ge=1, le=5)
    verification_source: Optional[str] = None


# ============================================
# Role-Skill Mapping Schemas
# ============================================

class RoleSkillMapResponse(BaseModel):
    role_cd: str
    role_nm: Optional[str] = None
    skill_cd: str
    skill_nm: Optional[str] = None
    required_level: int
    importance: str
    market_demand_score: Optional[float] = None
    growth_trend: str = "stable"

    class Config:
        from_attributes = True


# ============================================
# Skill Graph Schemas
# ============================================

class SkillNode(BaseModel):
    """Graph node representing a skill"""
    id: str  # skill_cd
    name: str
    category: Optional[str] = None
    difficulty: Optional[int] = None
    student_level: Optional[int] = None  # 학생 현재 레벨
    required_level: Optional[int] = None  # 목표 역할 요구 레벨
    gap: Optional[int] = None
    importance: Optional[str] = None


class SkillEdge(BaseModel):
    """Graph edge representing skill relationship"""
    source: str  # skill_cd_from
    target: str  # skill_cd_to
    relation_type: str  # prerequisite, complementary, alternative, builds_on
    strength: float = 1.0


class SkillGraphResponse(BaseModel):
    """Complete skill graph for visualization"""
    nodes: List[SkillNode]
    edges: List[SkillEdge]
    role_cd: Optional[str] = None
    role_nm: Optional[str] = None


# ============================================
# Gap Analysis Schemas
# ============================================

class SkillGapItem(BaseModel):
    skill_cd: str
    skill_nm: str
    current_level: int
    required_level: int
    gap: int
    importance: str
    priority_rank: int
    recommended_actions: Optional[List[str]] = None


class GapAnalysisRequest(BaseModel):
    student_id: str
    target_role_cd: str
    include_recommendations: bool = True


class GapAnalysisResponse(BaseModel):
    analysis_id: Optional[UUID] = None
    student_id: str
    target_role_cd: str
    target_role_nm: Optional[str] = None
    analysis_date: datetime
    overall_gap_score: float  # 0-100, 낮을수록 좋음
    readiness_percentage: float  # 0-100, 높을수록 좋음
    skill_gaps: List[SkillGapItem]
    top_priority_skills: List[str]
    strengths: List[str]  # 이미 충족된 스킬
    summary: str

    class Config:
        from_attributes = True


# ============================================
# Skill Relation Schemas
# ============================================

class SkillRelationResponse(BaseModel):
    skill_cd_from: str
    skill_nm_from: Optional[str] = None
    skill_cd_to: str
    skill_nm_to: Optional[str] = None
    relation_type: str
    strength: float

    class Config:
        from_attributes = True


# ============================================
# Role Requirement Schemas
# ============================================

class RoleRequirementResponse(BaseModel):
    role_cd: str
    role_nm: str
    role_nm_en: Optional[str] = None
    industry: Optional[str] = None
    required_skills: List[RoleSkillMapResponse]
    total_skills: int
    critical_skills: int
    average_required_level: float

    class Config:
        from_attributes = True
