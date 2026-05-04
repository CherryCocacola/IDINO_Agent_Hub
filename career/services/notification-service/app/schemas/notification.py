"""Notification Schemas"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class NotificationType(str, Enum):
    """알림 유형"""
    RISK_ALERT = "RISK_ALERT"           # 위험 알림
    GOAL_REMINDER = "GOAL_REMINDER"     # 목표 리마인더
    OPPORTUNITY = "OPPORTUNITY"          # 기회 추천
    BADGE_EARNED = "BADGE_EARNED"       # 뱃지 획득
    COACHING_CHECKIN = "COACHING_CHECKIN"  # 코칭 체크인
    SYSTEM = "SYSTEM"                   # 시스템 알림


class NotificationCreate(BaseModel):
    """알림 생성 요청"""
    student_id: str = Field(..., description="학생 ID")
    notification_type: NotificationType = Field(..., description="알림 유형")
    title: str = Field(..., max_length=200, description="알림 제목")
    message: str = Field(..., description="알림 내용")
    reference_type: Optional[str] = Field(None, description="참조 엔티티 타입 (goal, risk, opportunity 등)")
    reference_id: Optional[str] = Field(None, description="참조 엔티티 ID")
    priority: int = Field(default=3, ge=1, le=5, description="우선순위 (1: 최고, 5: 최저)")


class NotificationResponse(BaseModel):
    """알림 응답"""
    notification_id: str
    student_id: str
    notification_type: NotificationType
    title: str
    message: str
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    priority: int
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """알림 목록 응답"""
    notifications: List[NotificationResponse]
    total_count: int
    unread_count: int


class NotificationPreferences(BaseModel):
    """알림 설정"""
    student_id: str
    risk_alert_enabled: bool = True
    goal_reminder_enabled: bool = True
    opportunity_enabled: bool = True
    badge_earned_enabled: bool = True
    coaching_checkin_enabled: bool = True
    system_enabled: bool = True
    email_enabled: bool = False
    push_enabled: bool = True
    quiet_hours_start: Optional[str] = None  # "22:00" 형식
    quiet_hours_end: Optional[str] = None    # "08:00" 형식

    class Config:
        from_attributes = True


class NotificationPreferencesUpdate(BaseModel):
    """알림 설정 업데이트"""
    risk_alert_enabled: Optional[bool] = None
    goal_reminder_enabled: Optional[bool] = None
    opportunity_enabled: Optional[bool] = None
    badge_earned_enabled: Optional[bool] = None
    coaching_checkin_enabled: Optional[bool] = None
    system_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
