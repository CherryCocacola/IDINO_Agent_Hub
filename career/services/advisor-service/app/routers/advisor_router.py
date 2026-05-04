from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from uuid import UUID

from ..schemas import (
    InterventionStatus,
    AdvisorAssignmentResponse,
    InterventionCreate,
    InterventionUpdate,
    InterventionResponse,
    CohortSnapshotResponse,
    AdvisorNoteCreate,
    AdvisorNoteResponse,
    CohortDashboard,
    StudentSummary,
    MeetingCreate,
    MeetingResponse,
)
from ..services import advisor_service

router = APIRouter(prefix="/advisor", tags=["Advisor Workspace"])


# ============================================
# Dashboard
# ============================================

@router.get("/dashboard/{advisor_id}", response_model=CohortDashboard)
async def get_advisor_dashboard(advisor_id: str):
    """
    어드바이저 대시보드

    담당 학생 코호트의 전체 현황, 주의 필요 학생, 최근/예정 개입 등을 제공합니다.
    """
    return await advisor_service.get_dashboard(advisor_id)


# ============================================
# Assignments
# ============================================

@router.get("/students/{advisor_id}", response_model=List[AdvisorAssignmentResponse])
async def get_advisor_students(advisor_id: str):
    """어드바이저 담당 학생 목록"""
    students = await advisor_service.get_advisor_students(advisor_id)
    return [AdvisorAssignmentResponse(**s) for s in students]


@router.post("/students/assign", response_model=AdvisorAssignmentResponse)
async def assign_student(advisor_id: str, student_id: str, is_primary: bool = True, notes: Optional[str] = None):
    """학생을 어드바이저에게 배정"""
    result = await advisor_service.assign_student(advisor_id, student_id, is_primary, notes)
    return AdvisorAssignmentResponse(**result)


@router.get("/attention/{advisor_id}", response_model=List[StudentSummary])
async def get_students_needing_attention(advisor_id: str, limit: int = Query(10, ge=1, le=50)):
    """주의가 필요한 학생 목록 (위험도순)"""
    return await advisor_service.get_students_needing_attention(advisor_id, limit)


# ============================================
# Interventions
# ============================================

@router.post("/interventions", response_model=InterventionResponse, status_code=201)
async def create_intervention(data: InterventionCreate):
    """
    새 개입 기록 생성

    상담, 이메일, 연계 등 학생 지원 활동을 기록합니다.
    """
    result = await advisor_service.create_intervention(data)
    return InterventionResponse(**result)


@router.get("/interventions/{intervention_id}", response_model=InterventionResponse)
async def get_intervention(intervention_id: UUID):
    """개입 상세 조회"""
    result = await advisor_service.get_intervention(intervention_id)
    if not result:
        raise HTTPException(status_code=404, detail="Intervention not found")
    return InterventionResponse(**result)


@router.get("/interventions/advisor/{advisor_id}", response_model=List[InterventionResponse])
async def get_advisor_interventions(
    advisor_id: str,
    status: Optional[InterventionStatus] = None,
    limit: int = Query(50, ge=1, le=200),
):
    """어드바이저의 개입 목록"""
    results = await advisor_service.get_advisor_interventions(advisor_id, status, limit)
    return [InterventionResponse(**r) for r in results]


@router.put("/interventions/{intervention_id}", response_model=InterventionResponse)
async def update_intervention(intervention_id: UUID, data: InterventionUpdate):
    """개입 상태 업데이트"""
    result = await advisor_service.update_intervention(intervention_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Intervention not found")
    return InterventionResponse(**result)


# ============================================
# Notes
# ============================================

@router.post("/notes", response_model=AdvisorNoteResponse, status_code=201)
async def create_note(data: AdvisorNoteCreate):
    """학생 노트 작성"""
    result = await advisor_service.create_note(data)
    return AdvisorNoteResponse(**result)


@router.get("/notes/student/{student_id}", response_model=List[AdvisorNoteResponse])
async def get_student_notes(student_id: str, advisor_id: Optional[str] = None):
    """학생 노트 조회"""
    results = await advisor_service.get_student_notes(student_id, advisor_id)
    return [AdvisorNoteResponse(**r) for r in results]


# ============================================
# Snapshots
# ============================================

@router.post("/snapshots/{advisor_id}", response_model=CohortSnapshotResponse, status_code=201)
async def create_snapshot(advisor_id: str):
    """코호트 스냅샷 생성"""
    return await advisor_service.create_snapshot(advisor_id)


@router.get("/snapshots/{advisor_id}", response_model=List[CohortSnapshotResponse])
async def get_snapshots(advisor_id: str, limit: int = Query(30, ge=1, le=365)):
    """코호트 스냅샷 기록"""
    return await advisor_service.get_snapshots(advisor_id, limit)


# ============================================
# Meetings
# ============================================

@router.get("/meetings/{advisor_id}", response_model=List[MeetingResponse])
async def get_advisor_meetings(advisor_id: str, limit: int = Query(50, ge=1, le=200)):
    """어드바이저의 미팅 목록"""
    results = await advisor_service.get_advisor_meetings(advisor_id, limit)
    return [MeetingResponse(**r) for r in results]


@router.post("/meetings", response_model=MeetingResponse, status_code=201)
async def create_meeting(data: MeetingCreate):
    """새 미팅 예약"""
    result = await advisor_service.create_meeting(data)
    return MeetingResponse(**result)


@router.patch("/meetings/{meeting_id}/complete", response_model=MeetingResponse)
async def complete_meeting(meeting_id: UUID, notes: Optional[str] = None):
    """미팅 완료 처리"""
    result = await advisor_service.complete_meeting(meeting_id, notes)
    if not result:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return MeetingResponse(**result)


@router.post("/meetings/{meeting_id}/cancel", response_model=MeetingResponse)
async def cancel_meeting(meeting_id: UUID):
    """미팅 취소"""
    result = await advisor_service.cancel_meeting(meeting_id)
    if not result:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return MeetingResponse(**result)
