"""Privacy Schemas - Data Subject Rights"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class RequestType(str, Enum):
    """Types of data subject requests"""
    ACCESS = "access"           # Right to Access
    RECTIFICATION = "rectification"  # Right to Rectification
    ERASURE = "erasure"         # Right to Erasure (Right to be Forgotten)
    PORTABILITY = "portability"  # Right to Data Portability
    RESTRICTION = "restriction"  # Right to Restriction of Processing
    OBJECTION = "objection"     # Right to Object


class RequestStatus(str, Enum):
    """Status of data subject request"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ConsentType(str, Enum):
    """Types of consent"""
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    THIRD_PARTY = "third_party"
    AI_PROCESSING = "ai_processing"
    DATA_RETENTION = "data_retention"
    RESEARCH = "research"


# Data Subject Request Schemas
class DataSubjectRequestCreate(BaseModel):
    """Schema for creating a data subject request"""
    student_id: str = Field(..., description="Student ID making the request")
    request_type: RequestType = Field(..., description="Type of request")
    description: Optional[str] = Field(None, max_length=2000, description="Additional details")
    contact_email: Optional[str] = Field(None, description="Contact email for response")


class DataSubjectRequest(BaseModel):
    """Internal data subject request model"""
    request_id: str
    student_id: str
    request_type: RequestType
    status: RequestStatus
    description: Optional[str]
    contact_email: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]
    response_data: Optional[Dict[str, Any]]
    rejection_reason: Optional[str]


class DataSubjectRequestResponse(BaseModel):
    """Response schema for a data subject request"""
    request_id: str
    student_id: str
    request_type: RequestType
    status: RequestStatus
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]
    estimated_completion: Optional[datetime]
    message: Optional[str]

    class Config:
        from_attributes = True


class DataSubjectRequestListResponse(BaseModel):
    """Response schema for list of requests"""
    student_id: str
    total_count: int
    requests: List[DataSubjectRequestResponse]


# Consent Schemas
class ConsentCreate(BaseModel):
    """Schema for recording consent"""
    student_id: str
    consent_type: ConsentType
    granted: bool = Field(..., description="Whether consent is granted")
    purpose: Optional[str] = Field(None, max_length=500)


class ConsentRecord(BaseModel):
    """Internal consent record model"""
    consent_id: str
    student_id: str
    consent_type: ConsentType
    granted: bool
    purpose: Optional[str]
    granted_at: Optional[datetime]
    revoked_at: Optional[datetime]
    ip_address: Optional[str]
    user_agent: Optional[str]


class ConsentResponse(BaseModel):
    """Response schema for consent record"""
    consent_id: str
    student_id: str
    consent_type: ConsentType
    granted: bool
    purpose: Optional[str]
    granted_at: Optional[datetime]
    revoked_at: Optional[datetime]

    class Config:
        from_attributes = True


class ConsentListResponse(BaseModel):
    """Response schema for list of consents"""
    student_id: str
    consents: List[ConsentResponse]
    all_consents_granted: bool


# Data Access/Export Schemas
class DataAccessResponse(BaseModel):
    """Response for data access request"""
    student_id: str
    request_id: str
    data_categories: List[str]
    personal_data: Dict[str, Any]
    processing_purposes: List[str]
    data_recipients: List[str]
    retention_period: str
    data_sources: List[str]
    export_available: bool
    generated_at: datetime


class DataExportResponse(BaseModel):
    """Response for data portability export"""
    student_id: str
    request_id: str
    format: str  # json, csv
    file_size_bytes: int
    download_url: Optional[str]
    expires_at: datetime
    data_categories: List[str]
    generated_at: datetime


class ErasureResponse(BaseModel):
    """Response for erasure request"""
    student_id: str
    request_id: str
    status: RequestStatus
    erased_categories: List[str]
    retained_categories: List[str]  # Data that must be retained for legal reasons
    retention_reason: Optional[str]
    completed_at: Optional[datetime]
    message: str
