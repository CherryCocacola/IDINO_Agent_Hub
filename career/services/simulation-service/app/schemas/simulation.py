from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from uuid import UUID
from enum import Enum


class ScenarioType(str, Enum):
    CAREER_PATH = "career_path"           # 진로 경로 시뮬레이션
    SKILL_DEVELOPMENT = "skill_development"  # 스킬 개발 시나리오
    COURSE_SELECTION = "course_selection"  # 수강 신청 시나리오
    OPPORTUNITY = "opportunity"           # 기회 선택 시나리오
    TIMELINE = "timeline"                 # 타임라인 시뮬레이션
    ACTIVITY = "activity"                 # 활동 시나리오
    # Legacy values for backward compatibility
    CAREER = "career"                     # Legacy: 진로 시뮬레이션
    SKILL = "skill"                       # Legacy: 스킬 시뮬레이션
    COURSE = "course"                     # Legacy: 수강 시뮬레이션


class ScenarioVariable(BaseModel):
    name: str
    current_value: Any
    simulated_value: Any
    impact_description: Optional[str] = None


class ScenarioCreate(BaseModel):
    student_id: str
    scenario_type: ScenarioType
    name: str
    description: Optional[str] = None
    variables: List[ScenarioVariable]
    target_date: Optional[date] = None


class SimulationResult(BaseModel):
    metric_name: str
    current_value: float
    simulated_value: float
    change_percent: float
    impact_level: str = Field(description="positive, negative, neutral")
    explanation: Optional[str] = None


class ScenarioResponse(BaseModel):
    scenario_id: UUID
    student_id: str
    scenario_type: ScenarioType
    name: str
    description: Optional[str] = None
    variables: List[ScenarioVariable]
    results: List[SimulationResult] = Field(default_factory=list)
    overall_impact_score: float = 0
    recommendation: Optional[str] = None
    ai_analysis: Optional[Dict[str, Any]] = None  # AI 분석 결과
    created_at: datetime
    is_saved: bool = False

    class Config:
        from_attributes = True


class ComparisonRequest(BaseModel):
    student_id: str
    scenario_ids: List[UUID] = Field(min_length=2, max_length=5)


class ComparisonResponse(BaseModel):
    comparison_id: UUID
    student_id: str
    scenarios: List[ScenarioResponse]
    comparison_matrix: Dict[str, Dict[str, float]]
    best_scenario_id: UUID
    recommendation: str
    created_at: datetime


class CareerPathSimulation(BaseModel):
    student_id: str
    target_role_cd: str
    current_skills: Dict[str, int] = Field(default_factory=dict)
    planned_courses: List[str] = Field(default_factory=list)
    planned_opportunities: List[str] = Field(default_factory=list)
    timeline_months: int = 24


class SkillDevelopmentSimulation(BaseModel):
    student_id: str
    target_skills: Dict[str, int]  # skill_cd -> target_level
    available_hours_per_week: int = 10
    learning_resources: List[str] = Field(default_factory=list)


class CourseSelectionSimulation(BaseModel):
    student_id: str
    course_codes: List[str]  # 수강할 과목 코드들
    expected_grades: Dict[str, str] = Field(default_factory=dict)  # course_cd -> expected grade (A, B, C, ...)
    semester: Optional[str] = None  # 학기 (예: "2026-1")


class TimelineSimulation(BaseModel):
    student_id: str
    target_date: date  # 목표 날짜
    milestones: List[Dict[str, Any]] = Field(default_factory=list)  # 중간 목표들
    timeline_type: str = "graduation"  # graduation, job_ready, skill_complete


class ScenarioTypeInfo(BaseModel):
    value: str
    label: str
    description: str


class VariableGuide(BaseModel):
    """시나리오 변수 설정 가이드"""
    name: str
    label: str
    description: str
    input_type: str = "text"  # text, number, select, multi-select
    options: Optional[List[Dict[str, Any]]] = None  # select/multi-select용 옵션
    default_value: Optional[Any] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    required: bool = True


class MetricExplanation(BaseModel):
    """시뮬레이션 결과 메트릭 설명"""
    metric_name: str
    description: str
    unit: str  # %, 점, 시간, 개월 등
    interpretation: str  # 수치 해석 방법
    good_threshold: Optional[float] = None  # 좋은 결과 기준값
    warning_threshold: Optional[float] = None  # 주의 필요 기준값


class ScenarioGuide(BaseModel):
    """시나리오 유형별 전체 가이드"""
    scenario_type: str
    title: str
    description: str
    how_it_works: str  # 시뮬레이션 작동 방식 설명
    steps: List[str]  # 진행 단계
    variables: List[VariableGuide]  # 설정 가능한 변수들
    expected_metrics: List[MetricExplanation]  # 예상되는 결과 메트릭들
    tips: List[str]  # 사용 팁


class AIAnalysis(BaseModel):
    """AI 기반 분석 결과"""
    summary: str  # 핵심 요약
    strengths: List[str]  # 이 시나리오의 장점
    risks: List[str]  # 주의해야 할 위험요소
    recommendations: List[str]  # AI 추천 행동
    next_steps: List[str]  # 다음 단계 제안
    confidence_reason: str  # 종합점수 산정 이유


class SuggestedScenario(BaseModel):
    scenario_type: ScenarioType
    title: str
    description: str
    reason: str  # 추천 이유
    variables: List[ScenarioVariable] = Field(default_factory=list)
