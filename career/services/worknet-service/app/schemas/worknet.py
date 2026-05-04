"""WorkNet Diagnosis Schemas"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class DiagnosisType(str, Enum):
    """Types of vocational diagnosis tests"""
    APTITUDE = "aptitude"                    # 직업적성검사
    INTEREST = "interest"                    # 직업흥미검사
    VALUES = "values"                        # 직업가치관검사
    PERSONALITY = "personality"              # 성인용 직업성격검사
    ENTREPRENEURSHIP = "entrepreneurship"    # 창업적성검사
    CAREER_MATURITY = "career_maturity"      # 진로성숙도검사


class DiagnosisStatus(str, Enum):
    """Status of diagnosis session"""
    INITIATED = "initiated"          # Session created, not started
    IN_PROGRESS = "in_progress"      # User is taking the test
    COMPLETED = "completed"          # Test completed, results available
    EXPIRED = "expired"              # Session expired
    CANCELLED = "cancelled"          # User cancelled
    ERROR = "error"                  # Error occurred


# ==================== Session Schemas ====================

class DiagnosisSessionCreate(BaseModel):
    """Schema for creating a diagnosis session"""
    student_id: str = Field(..., description="Student ID")
    diagnosis_type: DiagnosisType = Field(..., description="Type of diagnosis test")
    callback_url: Optional[str] = Field(None, description="Callback URL for results")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class DiagnosisSessionResponse(BaseModel):
    """Response schema for diagnosis session"""
    session_id: str
    student_id: str
    diagnosis_type: DiagnosisType
    status: DiagnosisStatus
    worknet_url: Optional[str] = Field(None, description="URL to WorkNet diagnosis page")
    expires_at: datetime
    created_at: datetime
    updated_at: Optional[datetime]
    message: Optional[str]

    class Config:
        from_attributes = True


class DiagnosisSessionListResponse(BaseModel):
    """Response for list of sessions"""
    student_id: str
    total_count: int
    sessions: List[DiagnosisSessionResponse]


# ==================== Result Schemas ====================

class OccupationMatch(BaseModel):
    """Matched occupation from diagnosis"""
    occupation_code: str = Field(..., description="WorkNet occupation code")
    occupation_name: str = Field(..., description="Occupation name in Korean")
    occupation_name_en: Optional[str] = Field(None, description="Occupation name in English")
    match_score: float = Field(..., ge=0, le=100, description="Match percentage")
    match_rank: int = Field(..., description="Ranking among matches")
    description: Optional[str] = Field(None, description="Brief description")
    required_education: Optional[str] = Field(None, description="Required education level")
    salary_range: Optional[str] = Field(None, description="Expected salary range")
    employment_outlook: Optional[str] = Field(None, description="Employment outlook")


class CareerRecommendation(BaseModel):
    """Career recommendation based on diagnosis"""
    recommendation_id: str
    category: str = Field(..., description="Recommendation category")
    title: str
    description: str
    priority: int = Field(..., ge=1, le=5, description="Priority level 1-5")
    action_items: List[str] = Field(default_factory=list)
    related_occupations: List[str] = Field(default_factory=list)
    related_competencies: List[str] = Field(default_factory=list)


class DiagnosisScoreCategory(BaseModel):
    """Score for a specific category in diagnosis"""
    category_code: str
    category_name: str
    score: float
    percentile: Optional[float] = None
    interpretation: Optional[str] = None


class DiagnosisResultResponse(BaseModel):
    """Response schema for diagnosis result"""
    result_id: str
    session_id: str
    student_id: str
    diagnosis_type: DiagnosisType

    # Overall Results
    overall_score: Optional[float] = Field(None, description="Overall score if applicable")
    overall_percentile: Optional[float] = Field(None, description="Percentile ranking")
    overall_interpretation: Optional[str] = Field(None, description="Overall interpretation")

    # Detailed Scores
    category_scores: List[DiagnosisScoreCategory] = Field(
        default_factory=list,
        description="Scores by category"
    )

    # Occupation Matches
    occupation_matches: List[OccupationMatch] = Field(
        default_factory=list,
        description="Matched occupations"
    )

    # Recommendations
    recommendations: List[CareerRecommendation] = Field(
        default_factory=list,
        description="Career recommendations"
    )

    # Metadata
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw data from WorkNet")
    completed_at: datetime
    valid_until: datetime
    worknet_result_url: Optional[str] = Field(None, description="URL to view results on WorkNet")

    class Config:
        from_attributes = True


class DiagnosisResultListResponse(BaseModel):
    """Response for list of results"""
    student_id: str
    total_count: int
    results: List[DiagnosisResultResponse]


# ==================== Callback Schemas ====================

class WorkNetCallbackData(BaseModel):
    """Data received from WorkNet callback"""
    session_id: str = Field(..., description="Our session ID")
    worknet_session_id: Optional[str] = Field(None, description="WorkNet's session ID")
    status: str = Field(..., description="Completion status")
    result_data: Optional[Dict[str, Any]] = Field(None, description="Result data")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")


# ==================== Integration Schemas ====================

class WorkNetAuthRequest(BaseModel):
    """Request for WorkNet authentication"""
    student_id: str
    diagnosis_type: DiagnosisType
    redirect_url: Optional[str] = None


class WorkNetAuthResponse(BaseModel):
    """Response with WorkNet authentication URL"""
    session_id: str
    auth_url: str
    expires_in: int = Field(..., description="Seconds until expiration")
    message: str


# ==================== Summary Schemas ====================

class DiagnosisSummary(BaseModel):
    """Summary of all diagnosis results for a student"""
    student_id: str
    total_tests_taken: int
    completed_tests: int
    latest_results: Dict[str, DiagnosisResultResponse]  # keyed by diagnosis_type
    overall_career_profile: Optional[Dict[str, Any]]
    top_occupation_matches: List[OccupationMatch]
    top_recommendations: List[CareerRecommendation]
    last_updated: datetime


class DiagnosisComparisonResponse(BaseModel):
    """Compare diagnosis results over time"""
    student_id: str
    diagnosis_type: DiagnosisType
    comparisons: List[Dict[str, Any]]  # Historical comparison data
    trend_analysis: Optional[str]
    improvement_areas: List[str]
