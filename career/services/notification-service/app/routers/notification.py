"""Notification API Router"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas.notification import (
    NotificationType,
    NotificationCreate,
    NotificationResponse,
    NotificationListResponse,
    NotificationPreferences,
    NotificationPreferencesUpdate
)
from ..services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/send", response_model=NotificationResponse)
async def send_notification(
    notification: NotificationCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    알림 발송

    - **student_id**: 학생 ID
    - **notification_type**: 알림 유형 (RISK_ALERT, GOAL_REMINDER, OPPORTUNITY, BADGE_EARNED, COACHING_CHECKIN, SYSTEM)
    - **title**: 알림 제목
    - **message**: 알림 내용
    - **reference_type**: 참조 엔티티 타입 (optional)
    - **reference_id**: 참조 엔티티 ID (optional)
    - **priority**: 우선순위 1-5 (1이 가장 높음)
    """
    service = NotificationService(db)
    try:
        return await service.send_notification(notification)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{student_id}", response_model=NotificationListResponse)
async def get_notifications(
    student_id: str,
    unread_only: bool = Query(False, description="읽지 않은 알림만 조회"),
    notification_type: Optional[NotificationType] = Query(None, description="알림 유형 필터"),
    limit: int = Query(50, ge=1, le=100, description="조회 개수"),
    offset: int = Query(0, ge=0, description="오프셋"),
    db: AsyncSession = Depends(get_db)
):
    """
    학생의 알림 목록 조회
    """
    service = NotificationService(db)
    notifications, total_count, unread_count = await service.get_notifications(
        student_id=student_id,
        unread_only=unread_only,
        notification_type=notification_type,
        limit=limit,
        offset=offset
    )

    return NotificationListResponse(
        notifications=notifications,
        total_count=total_count,
        unread_count=unread_count
    )


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_as_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    알림 읽음 처리
    """
    service = NotificationService(db)
    result = await service.mark_as_read(notification_id)

    if not result:
        raise HTTPException(status_code=404, detail="Notification not found")

    return result


@router.put("/{student_id}/read-all")
async def mark_all_as_read(
    student_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    모든 알림 읽음 처리
    """
    service = NotificationService(db)
    count = await service.mark_all_as_read(student_id)

    return {"message": f"Marked {count} notifications as read"}


@router.get("/preferences/{student_id}", response_model=NotificationPreferences)
async def get_preferences(
    student_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    알림 설정 조회
    """
    service = NotificationService(db)
    return await service.get_preferences(student_id)


@router.put("/preferences/{student_id}", response_model=NotificationPreferences)
async def update_preferences(
    student_id: str,
    updates: NotificationPreferencesUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    알림 설정 업데이트

    - **risk_alert_enabled**: 위험 알림 활성화
    - **goal_reminder_enabled**: 목표 리마인더 활성화
    - **opportunity_enabled**: 기회 추천 활성화
    - **badge_earned_enabled**: 뱃지 획득 알림 활성화
    - **coaching_checkin_enabled**: 코칭 체크인 알림 활성화
    - **system_enabled**: 시스템 알림 활성화
    - **email_enabled**: 이메일 알림 활성화
    - **push_enabled**: 푸시 알림 활성화
    - **quiet_hours_start**: 방해금지 시작 시간 (예: "22:00")
    - **quiet_hours_end**: 방해금지 종료 시간 (예: "08:00")
    """
    service = NotificationService(db)
    return await service.update_preferences(student_id, updates)
