from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from ..schemas import (
    BadgeCategory,
    BadgeCreate,
    BadgeResponse,
    StudentBadgeResponse,
    BadgeAwardRequest,
    SkillPassportResponse,
    PassportShareRequest,
    PassportShareResponse,
    CredentialResponse,
)
from ..services import badge_service

router = APIRouter(tags=["Badges & Passport"])


# ============================================
# Badges
# ============================================

@router.get("/badges", response_model=List[BadgeResponse])
async def list_badges(
    category: Optional[BadgeCategory] = Query(None),
    is_active: bool = Query(True),
):
    """모든 뱃지 목록"""
    badges = await badge_service.get_all_badges(category, is_active)
    return [BadgeResponse(**b) for b in badges]


@router.get("/badges/{badge_cd}", response_model=BadgeResponse)
async def get_badge(badge_cd: str):
    """뱃지 상세 조회"""
    badge = await badge_service.get_badge(badge_cd)
    if not badge:
        raise HTTPException(status_code=404, detail=f"Badge {badge_cd} not found")
    return BadgeResponse(**badge)


@router.post("/badges", response_model=BadgeResponse, status_code=201)
async def create_badge(data: BadgeCreate):
    """새 뱃지 생성"""
    result = await badge_service.create_badge(data)
    return BadgeResponse(**result)


# ============================================
# Student Badges
# ============================================

@router.post("/badges/award", response_model=StudentBadgeResponse, status_code=201)
async def award_badge(request: BadgeAwardRequest):
    """학생에게 뱃지 수여"""
    result = await badge_service.award_badge(
        student_id=request.student_id,
        badge_cd=request.badge_cd,
        issued_by=request.issued_by,
        evidence_url=request.evidence_url,
        is_public=request.is_public,
    )
    if not result:
        raise HTTPException(status_code=404, detail=f"Badge {request.badge_cd} not found")
    return StudentBadgeResponse(**result)


@router.get("/badges/student/{student_id}", response_model=List[StudentBadgeResponse])
async def get_student_badges(
    student_id: str,
    public_only: bool = Query(False),
):
    """학생의 뱃지 목록"""
    is_public = True if public_only else None
    badges = await badge_service.get_student_badges(student_id, is_public)
    return [StudentBadgeResponse(**b) for b in badges]


@router.get("/badges/student/{student_id}/stats")
async def get_student_badge_stats(student_id: str):
    """학생의 뱃지 통계"""
    return await badge_service.get_student_badge_stats(student_id)


@router.get("/badges/verify/{verification_hash}")
async def verify_badge(verification_hash: str):
    """뱃지 진위 검증"""
    result = await badge_service.verify_badge(verification_hash)
    if not result:
        raise HTTPException(status_code=404, detail="Invalid verification hash")
    return {"verified": True, "badge": result["badge_nm"], "student": result["std_nm"], "earned_at": result["earned_at"]}


# ============================================
# Student Credentials
# ============================================

@router.get("/badges/student/{student_id}/credentials", response_model=List[CredentialResponse])
async def get_student_credentials(student_id: str):
    """학생의 자격증/면허/수상 목록"""
    credentials = await badge_service.get_student_credentials(student_id)
    return [CredentialResponse(**c) for c in credentials]


# ============================================
# Skill Passport
# ============================================

@router.get("/passport/{student_id}", response_model=SkillPassportResponse)
async def get_skill_passport(student_id: str):
    """학생의 스킬 패스포트 조회"""
    passport = await badge_service.get_skill_passport(student_id)
    if not passport:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
    return passport


@router.post("/passport/share", response_model=PassportShareResponse)
async def create_passport_share(request: PassportShareRequest):
    """스킬 패스포트 공유 링크 생성"""
    return await badge_service.create_share_link(
        student_id=request.student_id,
        expiry_days=request.expiry_days,
        include_skills=request.include_skills,
        include_badges=request.include_badges,
        recipient_email=request.recipient_email,
    )
