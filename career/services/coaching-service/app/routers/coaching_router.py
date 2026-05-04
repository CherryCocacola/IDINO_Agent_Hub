from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from uuid import UUID

from ..schemas import (
    GoalStatus,
    GoalCreate,
    GoalUpdate,
    GoalResponse,
    PlanItemCreate,
    PlanItemUpdate,
    PlanItemResponse,
    CheckinCreate,
    CheckinResponse,
    RetrospectiveCreate,
    RetrospectiveResponse,
    CoachingSessionResponse,
    AICoachRequest,
    AICoachResponse,
    GoalProgressSummary,
)
from ..services import coaching_service

router = APIRouter(prefix="/coaching", tags=["AI Coaching"])


# ============================================
# Goals
# ============================================

@router.post("/goals", response_model=GoalResponse, status_code=201)
async def create_goal(data: GoalCreate):
    """
    새로운 목표 생성

    - **title**: 목표 제목
    - **goal_type**: career, skill, academic, personal
    - **priority**: high, medium, low
    - **target_date**: 목표 완료 예정일
    """
    result = await coaching_service.create_goal(data)
    return GoalResponse(**result)


@router.get("/goals/{goal_id}", response_model=GoalResponse)
async def get_goal(goal_id: UUID):
    """목표 상세 조회"""
    goal = await coaching_service.get_goal(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail=f"Goal {goal_id} not found")
    return GoalResponse(**goal)


@router.get("/goals/student/{student_id}", response_model=List[GoalResponse])
async def get_student_goals(
    student_id: str,
    status: Optional[GoalStatus] = Query(None, description="Filter by status"),
    goal_type: Optional[str] = Query(None, description="Filter by goal type"),
):
    """학생의 모든 목표 조회"""
    goals = await coaching_service.get_student_goals(
        student_id=student_id,
        status=status,
        goal_type=goal_type,
    )
    return [GoalResponse(**g) for g in goals]


@router.put("/goals/{goal_id}", response_model=GoalResponse)
async def update_goal(goal_id: UUID, data: GoalUpdate):
    """목표 수정"""
    result = await coaching_service.update_goal(goal_id, data)
    if not result:
        raise HTTPException(status_code=404, detail=f"Goal {goal_id} not found")
    return GoalResponse(**result)


@router.delete("/goals/{goal_id}", status_code=204)
async def delete_goal(goal_id: UUID):
    """목표 삭제"""
    success = await coaching_service.delete_goal(goal_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Goal {goal_id} not found")


# ============================================
# Plan Items
# ============================================

@router.post("/plans", response_model=PlanItemResponse, status_code=201)
async def create_plan_item(data: PlanItemCreate):
    """
    플랜 항목 생성

    목표를 달성하기 위한 구체적인 액션 아이템을 추가합니다.
    """
    # Verify goal exists
    goal = await coaching_service.get_goal(data.goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail=f"Goal {data.goal_id} not found")

    result = await coaching_service.create_plan_item(data)
    return PlanItemResponse(**result)


@router.get("/plans/{goal_id}", response_model=List[PlanItemResponse])
async def get_plan_items(goal_id: UUID):
    """목표의 플랜 항목 목록"""
    items = await coaching_service.get_plan_items(goal_id)
    return [PlanItemResponse(**item) for item in items]


@router.put("/plans/{plan_id}", response_model=PlanItemResponse)
async def update_plan_item(plan_id: UUID, data: PlanItemUpdate):
    """
    플랜 항목 수정

    - **is_completed**: 완료 여부
    - **actual_hours**: 실제 소요 시간
    """
    result = await coaching_service.update_plan_item(plan_id, data)
    if not result:
        raise HTTPException(status_code=404, detail=f"Plan item {plan_id} not found")
    return PlanItemResponse(**result)


@router.delete("/plans/{plan_id}", status_code=204)
async def delete_plan_item(plan_id: UUID):
    """플랜 항목 삭제"""
    success = await coaching_service.delete_plan_item(plan_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Plan item {plan_id} not found")


# ============================================
# Check-ins
# ============================================

@router.post("/checkins", response_model=CheckinResponse, status_code=201)
async def create_checkin(data: CheckinCreate):
    """
    체크인 생성

    목표 진행 상황을 기록합니다. AI가 피드백과 제안을 제공합니다.

    - **mood**: great, good, neutral, struggling, blocked
    - **progress_note**: 진행 상황 메모
    - **blockers**: 방해 요소
    """
    # Verify goal exists
    goal = await coaching_service.get_goal(data.goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail=f"Goal {data.goal_id} not found")

    result = await coaching_service.create_checkin(data)
    return CheckinResponse(**result)


@router.get("/checkins/{goal_id}", response_model=List[CheckinResponse])
async def get_checkins(
    goal_id: UUID,
    limit: int = Query(10, ge=1, le=50, description="Maximum number of checkins"),
):
    """목표의 체크인 기록"""
    checkins = await coaching_service.get_checkins(goal_id, limit)
    return [CheckinResponse(**c) for c in checkins]


@router.get("/checkins/student/{student_id}/recent", response_model=List[CheckinResponse])
async def get_student_recent_checkins(
    student_id: str,
    days: int = Query(7, ge=1, le=30, description="Number of days"),
):
    """학생의 최근 체크인"""
    checkins = await coaching_service.get_student_recent_checkins(student_id, days)
    return [CheckinResponse(**c) for c in checkins]


# ============================================
# Retrospectives
# ============================================

@router.post("/retrospectives", response_model=RetrospectiveResponse, status_code=201)
async def create_retrospective(data: RetrospectiveCreate):
    """
    회고 생성

    목표 완료 후 또는 중간 점검 시 회고를 작성합니다.

    - **what_went_well**: 잘된 점
    - **what_could_improve**: 개선할 점
    - **lessons_learned**: 배운 점
    """
    result = await coaching_service.create_retrospective(data)
    return RetrospectiveResponse(**result)


@router.get("/retrospectives/{goal_id}", response_model=RetrospectiveResponse)
async def get_retrospective(goal_id: UUID):
    """목표의 최근 회고"""
    retro = await coaching_service.get_retrospective(goal_id)
    if not retro:
        raise HTTPException(status_code=404, detail=f"No retrospective found for goal {goal_id}")
    return RetrospectiveResponse(**retro)


# ============================================
# Coaching Session (Full View)
# ============================================

@router.get("/session/{goal_id}", response_model=CoachingSessionResponse)
async def get_coaching_session(goal_id: UUID):
    """
    코칭 세션 전체 조회

    목표, 플랜, 체크인, 회고를 한 번에 조회합니다.
    """
    goal = await coaching_service.get_goal(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail=f"Goal {goal_id} not found")

    plan_items = await coaching_service.get_plan_items(goal_id)
    checkins = await coaching_service.get_checkins(goal_id, limit=5)
    retro = await coaching_service.get_retrospective(goal_id)

    return CoachingSessionResponse(
        goal=GoalResponse(**goal),
        plan_items=[PlanItemResponse(**p) for p in plan_items],
        recent_checkins=[CheckinResponse(**c) for c in checkins],
        retrospective=RetrospectiveResponse(**retro) if retro else None,
    )


# ============================================
# AI Coach
# ============================================

@router.post("/ai-coach", response_model=AICoachResponse)
async def get_ai_coaching(request: AICoachRequest):
    """
    AI 코치 조언 받기

    - **query_type**: advice, plan_suggest, motivation, blockers, review
    - **context**: 추가 맥락 정보
    """
    return await coaching_service.get_ai_coaching(
        student_id=request.student_id,
        goal_id=request.goal_id,
        query_type=request.query_type,
        context=request.context,
    )


@router.get("/ai-coach/{student_id}", response_model=AICoachResponse)
async def get_ai_coaching_simple(
    student_id: str,
    query_type: str = Query("advice", description="advice, motivation, blockers, review"),
):
    """AI 코치 조언 (GET 버전)"""
    return await coaching_service.get_ai_coaching(
        student_id=student_id,
        query_type=query_type,
    )


# ============================================
# Progress Summary
# ============================================

@router.get("/progress/{student_id}", response_model=GoalProgressSummary)
async def get_progress_summary(student_id: str):
    """
    학생 진행 요약

    전체 목표 현황, 평균 진행률, 체크인 수, 연속 체크인 일수 등을 제공합니다.
    """
    return await coaching_service.get_progress_summary(student_id)
