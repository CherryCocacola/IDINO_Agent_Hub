"""Privacy Router - Data Subject Rights API Endpoints"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query

from ..services.privacy_service import PrivacyService
from ..schemas.privacy import (
    RequestType,
    ConsentType,
    DataSubjectRequestCreate,
    DataSubjectRequestResponse,
    DataSubjectRequestListResponse,
    ConsentCreate,
    ConsentResponse,
    ConsentListResponse,
    DataAccessResponse,
    DataExportResponse,
    ErasureResponse,
)

router = APIRouter(prefix="/privacy", tags=["privacy"])

# Service instance
privacy_service = PrivacyService()


# ==================== Data Subject Requests ====================

@router.post("/requests", response_model=DataSubjectRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_data_subject_request(data: DataSubjectRequestCreate):
    """
    Create a new data subject request.

    Supported request types:
    - **access**: Right to Access - Get all your personal data
    - **rectification**: Right to Rectification - Correct your data
    - **erasure**: Right to Erasure - Delete your data (Right to be Forgotten)
    - **portability**: Right to Data Portability - Export your data
    - **restriction**: Right to Restriction - Limit processing
    - **objection**: Right to Object - Object to processing
    """
    try:
        return await privacy_service.create_request(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/requests/student/{student_id}", response_model=DataSubjectRequestListResponse)
async def get_student_requests(student_id: str):
    """
    Get all data subject requests for a student.
    """
    try:
        return await privacy_service.get_requests(student_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/requests/{request_id}", response_model=DataSubjectRequestResponse)
async def get_request_status(request_id: str):
    """
    Get the status of a specific data subject request.
    """
    try:
        result = await privacy_service.get_request_status(request_id)
        if not result:
            raise HTTPException(status_code=404, detail="Request not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Right to Access ====================

@router.post("/access/{student_id}", response_model=DataAccessResponse)
async def request_data_access(
    student_id: str,
    request_id: Optional[str] = Query(None, description="Existing request ID to link")
):
    """
    Process a data access request (GDPR Article 15).

    Returns all personal data held about the student, including:
    - Personal information
    - Academic records
    - Competency assessments
    - Activity history
    - Portfolio items
    """
    try:
        # Create a new request if not provided
        if not request_id:
            req = await privacy_service.create_request(
                DataSubjectRequestCreate(
                    student_id=student_id,
                    request_type=RequestType.ACCESS,
                    description="Automated access request via API"
                )
            )
            request_id = req.request_id

        return await privacy_service.process_access_request(student_id, request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Right to Data Portability ====================

@router.post("/export/{student_id}", response_model=DataExportResponse)
async def export_personal_data(
    student_id: str,
    format: str = Query("json", description="Export format: json or csv"),
    request_id: Optional[str] = Query(None, description="Existing request ID to link")
):
    """
    Export personal data in portable format (GDPR Article 20).

    Provides data in a structured, commonly used, machine-readable format.
    """
    try:
        if format not in ["json", "csv"]:
            raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")

        # Create a new request if not provided
        if not request_id:
            req = await privacy_service.create_request(
                DataSubjectRequestCreate(
                    student_id=student_id,
                    request_type=RequestType.PORTABILITY,
                    description=f"Data export request in {format} format"
                )
            )
            request_id = req.request_id

        return await privacy_service.export_data(student_id, request_id, format)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Right to Erasure ====================

@router.post("/erasure/{student_id}", response_model=ErasureResponse)
async def request_data_erasure(
    student_id: str,
    request_id: Optional[str] = Query(None, description="Existing request ID to link")
):
    """
    Process a data erasure request (GDPR Article 17 - Right to be Forgotten).

    Note: Some data may be retained for legal/regulatory compliance.
    Academic records are anonymized but retained per Higher Education Act.
    """
    try:
        # Create a new request if not provided
        if not request_id:
            req = await privacy_service.create_request(
                DataSubjectRequestCreate(
                    student_id=student_id,
                    request_type=RequestType.ERASURE,
                    description="Data erasure request via API"
                )
            )
            request_id = req.request_id

        return await privacy_service.process_erasure_request(student_id, request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Consent Management ====================

@router.post("/consent", response_model=ConsentResponse, status_code=status.HTTP_201_CREATED)
async def record_consent(data: ConsentCreate):
    """
    Record a consent decision.

    Consent types:
    - **marketing**: Consent for marketing communications
    - **analytics**: Consent for analytics and tracking
    - **third_party**: Consent for third-party data sharing
    - **ai_processing**: Consent for AI-based processing
    - **data_retention**: Consent for extended data retention
    - **research**: Consent for research purposes
    """
    try:
        return await privacy_service.record_consent(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/consent/student/{student_id}", response_model=ConsentListResponse)
async def get_student_consents(student_id: str):
    """
    Get all consent records for a student.
    """
    try:
        return await privacy_service.get_consents(student_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/consent/{student_id}/{consent_type}", response_model=ConsentResponse)
async def revoke_consent(student_id: str, consent_type: ConsentType):
    """
    Revoke a specific consent.
    """
    try:
        result = await privacy_service.revoke_consent(student_id, consent_type)
        if not result:
            raise HTTPException(status_code=404, detail="Consent record not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Info Endpoints ====================

@router.get("/rights")
async def get_data_subject_rights():
    """
    Get information about available data subject rights.
    """
    return {
        "rights": [
            {
                "type": "access",
                "name": "Right to Access",
                "article": "GDPR Article 15",
                "description": "You have the right to obtain confirmation of whether personal data concerning you is being processed and access to that data."
            },
            {
                "type": "rectification",
                "name": "Right to Rectification",
                "article": "GDPR Article 16",
                "description": "You have the right to obtain rectification of inaccurate personal data concerning you."
            },
            {
                "type": "erasure",
                "name": "Right to Erasure",
                "article": "GDPR Article 17",
                "description": "You have the right to obtain erasure of personal data concerning you (Right to be Forgotten)."
            },
            {
                "type": "portability",
                "name": "Right to Data Portability",
                "article": "GDPR Article 20",
                "description": "You have the right to receive your personal data in a structured, commonly used, machine-readable format."
            },
            {
                "type": "restriction",
                "name": "Right to Restriction",
                "article": "GDPR Article 18",
                "description": "You have the right to obtain restriction of processing of your personal data."
            },
            {
                "type": "objection",
                "name": "Right to Object",
                "article": "GDPR Article 21",
                "description": "You have the right to object to processing of your personal data."
            }
        ],
        "processing_time": "30 days maximum (GDPR requirement)",
        "contact": "privacy@idino.edu"
    }


@router.get("/consent-types")
async def get_consent_types():
    """
    Get information about available consent types.
    """
    return {
        "consent_types": [
            {"type": "marketing", "name": "Marketing Communications", "required": False},
            {"type": "analytics", "name": "Analytics and Tracking", "required": False},
            {"type": "third_party", "name": "Third-Party Data Sharing", "required": False},
            {"type": "ai_processing", "name": "AI-Based Processing", "required": False},
            {"type": "data_retention", "name": "Extended Data Retention", "required": False},
            {"type": "research", "name": "Research Purposes", "required": False}
        ]
    }
