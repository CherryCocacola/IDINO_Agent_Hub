from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from ..schemas import (
    OpportunityType,
    ApplicationStatus,
    OpportunityCreate,
    OpportunityUpdate,
    OpportunityResponse,
    OpportunityListResponse,
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse,
    RecommendationRequest,
    RecommendationResponse,
    OpportunitySearchRequest,
)
from ..services import opportunity_service

router = APIRouter(prefix="/opportunities", tags=["Opportunities"])


# ============================================
# Opportunity CRUD
# ============================================

@router.get("", response_model=OpportunityListResponse)
async def list_opportunities(
    opportunity_type: Optional[OpportunityType] = Query(None, description="Filter by type"),
    is_active: bool = Query(True, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """
    모든 기회 목록 조회

    - **opportunity_type**: 인턴십, 공모전, 연구참여 등 필터
    - **is_active**: 활성 상태 필터
    """
    opportunities, total = await opportunity_service.get_all_opportunities(
        opportunity_type=opportunity_type,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )
    return OpportunityListResponse(
        opportunities=[OpportunityResponse(**o) for o in opportunities],
        total_count=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(opportunity_id: UUID):
    """특정 기회 상세 조회"""
    opp = await opportunity_service.get_opportunity(opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail=f"Opportunity {opportunity_id} not found")
    return OpportunityResponse(**opp)


@router.post("", response_model=OpportunityResponse, status_code=201)
async def create_opportunity(data: OpportunityCreate):
    """새로운 기회 등록"""
    result = await opportunity_service.create_opportunity(data)
    return OpportunityResponse(**result)


@router.put("/{opportunity_id}", response_model=OpportunityResponse)
async def update_opportunity(opportunity_id: UUID, data: OpportunityUpdate):
    """기회 정보 수정"""
    result = await opportunity_service.update_opportunity(opportunity_id, data)
    if not result:
        raise HTTPException(status_code=404, detail=f"Opportunity {opportunity_id} not found")
    return OpportunityResponse(**result)


@router.delete("/{opportunity_id}", status_code=204)
async def delete_opportunity(opportunity_id: UUID):
    """기회 삭제 (비활성화)"""
    success = await opportunity_service.delete_opportunity(opportunity_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Opportunity {opportunity_id} not found")


# ============================================
# Recommendations
# ============================================

@router.post("/recommend", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """
    학생 맞춤 기회 추천

    학생의 스킬, 전공, 학년 등을 기반으로 최적의 기회를 추천합니다.

    - **student_id**: 학생 ID
    - **opportunity_types**: 추천받을 기회 유형 (선택)
    - **min_score**: 최소 매칭 점수 (기본 50)
    - **max_results**: 최대 결과 수 (기본 10)
    """
    recommendations = await opportunity_service.get_recommendations(
        student_id=request.student_id,
        opportunity_types=request.opportunity_types,
        min_score=request.min_score,
        max_results=request.max_results,
        include_expired=request.include_expired,
    )

    return RecommendationResponse(
        student_id=request.student_id,
        recommendations=recommendations,
        generated_at=datetime.now(),
        filters_applied={
            "opportunity_types": [t.value for t in request.opportunity_types] if request.opportunity_types else None,
            "min_score": request.min_score,
            "max_results": request.max_results,
            "include_expired": request.include_expired,
        },
    )


@router.get("/recommend/{student_id}", response_model=RecommendationResponse)
async def get_recommendations_for_student(
    student_id: str,
    opportunity_type: Optional[OpportunityType] = Query(None, description="Filter by type"),
    min_score: float = Query(50.0, ge=0, le=100, description="Minimum match score"),
    max_results: int = Query(10, ge=1, le=50, description="Maximum results"),
):
    """학생 ID로 기회 추천 (GET 버전)"""
    opportunity_types = [opportunity_type] if opportunity_type else None

    recommendations = await opportunity_service.get_recommendations(
        student_id=student_id,
        opportunity_types=opportunity_types,
        min_score=min_score,
        max_results=max_results,
        include_expired=False,
    )

    return RecommendationResponse(
        student_id=student_id,
        recommendations=recommendations,
        generated_at=datetime.now(),
        filters_applied={
            "opportunity_type": opportunity_type.value if opportunity_type else None,
            "min_score": min_score,
            "max_results": max_results,
        },
    )


# ============================================
# Applications
# ============================================

@router.get("/applications/{student_id}", response_model=List[ApplicationResponse])
async def get_student_applications(
    student_id: str,
    status: Optional[ApplicationStatus] = Query(None, description="Filter by status"),
):
    """
    학생의 지원 목록 조회

    - **student_id**: 학생 ID
    - **status**: 지원 상태 필터 (interested, preparing, applied, etc.)
    """
    applications = await opportunity_service.get_student_applications(
        student_id=student_id,
        status=status,
    )
    return [ApplicationResponse(**a) for a in applications]


@router.get("/applications/{student_id}/{opportunity_id}", response_model=ApplicationResponse)
async def get_application(student_id: str, opportunity_id: UUID):
    """특정 지원 상세 조회"""
    application = await opportunity_service.get_application(student_id, opportunity_id)
    if not application:
        raise HTTPException(
            status_code=404,
            detail=f"Application not found for student {student_id} and opportunity {opportunity_id}",
        )
    return ApplicationResponse(**application)


@router.post("/applications", response_model=ApplicationResponse, status_code=201)
async def create_application(data: ApplicationCreate):
    """
    기회 지원 등록

    학생이 특정 기회에 관심을 표시하거나 지원합니다.
    """
    # Check if opportunity exists
    opp = await opportunity_service.get_opportunity(data.opportunity_id)
    if not opp:
        raise HTTPException(
            status_code=404,
            detail=f"Opportunity {data.opportunity_id} not found",
        )

    # Check if already applied
    existing = await opportunity_service.get_application(data.student_id, data.opportunity_id)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Application already exists for this opportunity",
        )

    result = await opportunity_service.create_application(data)
    return ApplicationResponse(**result)


@router.put("/applications/{application_id}", response_model=ApplicationResponse)
async def update_application(application_id: UUID, data: ApplicationUpdate):
    """
    지원 상태 업데이트

    - **status**: interested → preparing → applied → reviewing → accepted/rejected
    """
    result = await opportunity_service.update_application(application_id, data)
    if not result:
        raise HTTPException(status_code=404, detail=f"Application {application_id} not found")
    return ApplicationResponse(**result)


@router.delete("/applications/{application_id}", status_code=204)
async def delete_application(application_id: UUID):
    """지원 철회/삭제"""
    success = await opportunity_service.delete_application(application_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Application {application_id} not found")


# ============================================
# Search
# ============================================

@router.post("/search", response_model=OpportunityListResponse)
async def search_opportunities(request: OpportunitySearchRequest):
    """
    기회 검색

    다양한 조건으로 기회를 검색합니다.

    - **query**: 텍스트 검색 (제목, 설명, 기관명)
    - **opportunity_types**: 기회 유형 필터
    - **skills**: 필요 스킬 필터
    - **location**: 위치 필터
    """
    opportunities, total = await opportunity_service.search_opportunities(
        query_text=request.query,
        opportunity_types=request.opportunity_types,
        skills=request.skills,
        location=request.location,
        min_deadline_days=request.min_deadline_days,
        is_active=request.is_active,
        page=request.page,
        page_size=request.page_size,
        sort_by=request.sort_by,
        sort_order=request.sort_order,
    )

    return OpportunityListResponse(
        opportunities=[OpportunityResponse(**o) for o in opportunities],
        total_count=total,
        page=request.page,
        page_size=request.page_size,
    )
