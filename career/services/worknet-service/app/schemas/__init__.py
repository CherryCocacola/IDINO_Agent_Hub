"""WorkNet Schemas Package"""
from .worknet import (
    DiagnosisType,
    DiagnosisStatus,
    DiagnosisSessionCreate,
    DiagnosisSessionResponse,
    DiagnosisResultResponse,
    DiagnosisResultListResponse,
    CareerRecommendation,
    OccupationMatch,
    WorkNetCallbackData,
)

__all__ = [
    "DiagnosisType",
    "DiagnosisStatus",
    "DiagnosisSessionCreate",
    "DiagnosisSessionResponse",
    "DiagnosisResultResponse",
    "DiagnosisResultListResponse",
    "CareerRecommendation",
    "OccupationMatch",
    "WorkNetCallbackData",
]
