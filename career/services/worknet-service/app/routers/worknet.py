"""WorkNet Router - Diagnosis Integration API Endpoints"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query

from ..services.worknet_service import WorkNetService
from ..schemas.worknet import (
    DiagnosisType,
    DiagnosisStatus,
    DiagnosisSessionCreate,
    DiagnosisSessionResponse,
    DiagnosisSessionListResponse,
    DiagnosisResultResponse,
    DiagnosisResultListResponse,
    WorkNetCallbackData,
    DiagnosisSummary,
)

router = APIRouter(prefix="/worknet", tags=["worknet"])

# Service instance
worknet_service = WorkNetService()


# ==================== Session Management ====================

@router.post("/sessions", response_model=DiagnosisSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_diagnosis_session(data: DiagnosisSessionCreate):
    """
    Create a new WorkNet diagnosis session.

    This initiates a diagnosis test session and returns a URL to the WorkNet platform
    where the student can complete the test.

    Available diagnosis types:
    - **aptitude**: 직업적성검사 - Measures 9 aptitude factors
    - **interest**: 직업흥미검사 - Holland-based interest analysis
    - **values**: 직업가치관검사 - Work values assessment
    - **personality**: 성인용 직업성격검사 - MBTI-based personality analysis
    - **entrepreneurship**: 창업적성검사 - Entrepreneurship aptitude
    - **career_maturity**: 진로성숙도검사 - Career readiness assessment
    """
    try:
        return await worknet_service.create_session(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=DiagnosisSessionResponse)
async def get_session(session_id: str):
    """
    Get the status of a diagnosis session.
    """
    try:
        result = await worknet_service.get_session(session_id)
        if not result:
            raise HTTPException(status_code=404, detail="Session not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/student/{student_id}", response_model=DiagnosisSessionListResponse)
async def get_student_sessions(student_id: str):
    """
    Get all diagnosis sessions for a student.
    """
    try:
        return await worknet_service.get_student_sessions(student_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/sessions/{session_id}/status")
async def update_session_status(
    session_id: str,
    status: DiagnosisStatus = Query(..., description="New status")
):
    """
    Update the status of a diagnosis session.

    This is typically called internally when session state changes.
    """
    try:
        result = await worknet_service.update_session_status(session_id, status)
        if not result:
            raise HTTPException(status_code=404, detail="Session not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Callback Handler ====================

@router.post("/callback", response_model=Optional[DiagnosisResultResponse])
async def handle_worknet_callback(callback_data: WorkNetCallbackData):
    """
    Handle callback from WorkNet when a test is completed.

    This endpoint receives the test results from WorkNet and stores them
    in the system for the student.
    """
    try:
        return await worknet_service.process_callback(callback_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Results ====================

@router.get("/results/{result_id}", response_model=DiagnosisResultResponse)
async def get_result(result_id: str):
    """
    Get a specific diagnosis result by ID.
    """
    try:
        result = await worknet_service.get_result(result_id)
        if not result:
            raise HTTPException(status_code=404, detail="Result not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/student/{student_id}", response_model=DiagnosisResultListResponse)
async def get_student_results(
    student_id: str,
    diagnosis_type: Optional[DiagnosisType] = Query(None, description="Filter by diagnosis type")
):
    """
    Get all diagnosis results for a student.

    Optionally filter by diagnosis type.
    """
    try:
        return await worknet_service.get_student_results(student_id, diagnosis_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/student/{student_id}/latest")
async def get_latest_results(student_id: str):
    """
    Get the latest result for each diagnosis type for a student.

    Returns a dictionary keyed by diagnosis type.
    """
    try:
        return await worknet_service.get_latest_results(student_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Summary ====================

@router.get("/summary/{student_id}", response_model=DiagnosisSummary)
async def get_diagnosis_summary(student_id: str):
    """
    Get a comprehensive diagnosis summary for a student.

    Includes:
    - Total tests taken and completed
    - Latest results for each diagnosis type
    - Overall career profile
    - Top occupation matches across all tests
    - Top career recommendations
    """
    try:
        return await worknet_service.get_diagnosis_summary(student_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Info Endpoints ====================

@router.get("/diagnosis-types")
async def get_diagnosis_types():
    """
    Get information about all available diagnosis types.

    Returns details about each test including:
    - Name in Korean and English
    - Estimated duration
    - Description
    """
    return {
        "diagnosis_types": worknet_service.get_diagnosis_types_info(),
        "total_available": len(worknet_service.DIAGNOSIS_INFO),
    }


@router.get("/info")
async def get_worknet_info():
    """
    Get general information about WorkNet integration.
    """
    return {
        "service": "WorkNet Diagnosis Integration",
        "provider": "Korea Employment Information Service",
        "website": "https://www.work.go.kr",
        "supported_tests": len(worknet_service.DIAGNOSIS_INFO),
        "result_retention_days": 730,  # 2 years
        "features": [
            "Vocational aptitude assessment",
            "Career interest analysis",
            "Work values evaluation",
            "Personality-based career matching",
            "Entrepreneurship aptitude testing",
            "Career maturity measurement",
        ],
        "benefits": [
            "Scientifically validated assessments",
            "Government-backed career guidance",
            "Comprehensive occupation matching",
            "Personalized career recommendations",
        ],
    }
