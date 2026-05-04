from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from enum import Enum


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ActionRecommendation(BaseModel):
    id: int
    title: str
    description: str
    priority: Priority
    deadline: str
    competency: str
    reasoning: str
    icon_type: str = "default"


class ActionRecommendationResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    student_id: str
    recommendations: List[ActionRecommendation]
    generated_at: datetime = Field(default_factory=datetime.now)
    model_used: str = "gpt-4o-mini"


class CompetencyScore(BaseModel):
    name: str
    score: float
    status: str
    gap: float = 0.0


class CompetencyAnalysisRequest(BaseModel):
    student_id: str
    competencies: List[CompetencyScore]
    career_goal: Optional[str] = None


class CompetencyAnalysisResponse(BaseModel):
    student_id: str
    analysis: str
    strengths: List[str]
    weaknesses: List[str]
    improvement_suggestions: List[str]
    generated_at: datetime = Field(default_factory=datetime.now)


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    student_id: str
    message: str
    history: List[ChatMessage] = []
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    student_id: str
    response: str
    suggestions: List[str] = []
    generated_at: datetime = Field(default_factory=datetime.now)


class MonthlyScore(BaseModel):
    month: int
    score: float


class HeatStripData(BaseModel):
    name: str
    monthly_scores: List[float]
    color: str
    trend: str = "stable"  # "up", "down", "stable"


class HeatStripResponse(BaseModel):
    student_id: str
    competencies: List[HeatStripData]
    period: str = "12개월"
    generated_at: datetime = Field(default_factory=datetime.now)


class SemesterGoal(BaseModel):
    label: str
    completed: bool
    priority: Priority = Priority.MEDIUM


class SemesterSprintResponse(BaseModel):
    student_id: str
    semester: str
    goals: List[SemesterGoal]
    completion_rate: float
    ai_suggestions: List[str]
    generated_at: datetime = Field(default_factory=datetime.now)
