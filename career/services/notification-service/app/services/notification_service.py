"""Notification Service - Business Logic"""
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from ..config import settings
from ..schemas.notification import (
    NotificationType,
    NotificationCreate,
    NotificationResponse,
    NotificationPreferences,
    NotificationPreferencesUpdate
)


class NotificationService:
    """알림 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.schema = settings.DB_SCHEMA

    async def send_notification(self, notification: NotificationCreate) -> NotificationResponse:
        """알림 발송"""
        # 알림 설정 확인
        preferences = await self.get_preferences(notification.student_id)
        if not self._is_notification_enabled(preferences, notification.notification_type):
            raise ValueError(f"Notification type {notification.notification_type} is disabled for this student")

        notification_id = str(uuid4())
        now = datetime.now()

        query = text(f"""
            INSERT INTO {self.schema}.tb_notification (
                notification_id, student_id, notification_type, title, message,
                reference_type, reference_id, priority, is_read, created_at
            ) VALUES (
                :notification_id, :student_id, :notification_type, :title, :message,
                :reference_type, :reference_id, :priority, false, :created_at
            )
            RETURNING notification_id, student_id, notification_type, title, message,
                      reference_type, reference_id, priority, is_read, read_at, created_at
        """)

        result = await self.db.execute(query, {
            "notification_id": notification_id,
            "student_id": notification.student_id,
            "notification_type": notification.notification_type.value,
            "title": notification.title,
            "message": notification.message,
            "reference_type": notification.reference_type,
            "reference_id": notification.reference_id,
            "priority": notification.priority,
            "created_at": now
        })

        row = result.fetchone()
        return self._row_to_response(row)

    async def get_notifications(
        self,
        student_id: str,
        unread_only: bool = False,
        notification_type: Optional[NotificationType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[NotificationResponse], int, int]:
        """알림 목록 조회"""
        where_clauses = ["student_id = :student_id"]
        params = {"student_id": student_id, "limit": limit, "offset": offset}

        if unread_only:
            where_clauses.append("is_read = false")

        if notification_type:
            where_clauses.append("notification_type = :notification_type")
            params["notification_type"] = notification_type.value

        where_sql = " AND ".join(where_clauses)

        # 알림 목록 조회
        query = text(f"""
            SELECT notification_id, student_id, notification_type, title, message,
                   reference_type, reference_id, priority, is_read, read_at, created_at
            FROM {self.schema}.tb_notification
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """)

        result = await self.db.execute(query, params)
        notifications = [self._row_to_response(row) for row in result.fetchall()]

        # 전체 개수 조회
        count_query = text(f"""
            SELECT COUNT(*) as total_count,
                   COUNT(*) FILTER (WHERE is_read = false) as unread_count
            FROM {self.schema}.tb_notification
            WHERE student_id = :student_id
        """)

        count_result = await self.db.execute(count_query, {"student_id": student_id})
        count_row = count_result.fetchone()

        return notifications, count_row.total_count, count_row.unread_count

    async def mark_as_read(self, notification_id: str) -> Optional[NotificationResponse]:
        """알림 읽음 처리"""
        now = datetime.now()

        query = text(f"""
            UPDATE {self.schema}.tb_notification
            SET is_read = true, read_at = :read_at
            WHERE notification_id = :notification_id
            RETURNING notification_id, student_id, notification_type, title, message,
                      reference_type, reference_id, priority, is_read, read_at, created_at
        """)

        result = await self.db.execute(query, {
            "notification_id": notification_id,
            "read_at": now
        })

        row = result.fetchone()
        if row:
            return self._row_to_response(row)
        return None

    async def mark_all_as_read(self, student_id: str) -> int:
        """모든 알림 읽음 처리"""
        now = datetime.now()

        query = text(f"""
            UPDATE {self.schema}.tb_notification
            SET is_read = true, read_at = :read_at
            WHERE student_id = :student_id AND is_read = false
        """)

        result = await self.db.execute(query, {
            "student_id": student_id,
            "read_at": now
        })

        return result.rowcount

    async def get_preferences(self, student_id: str) -> NotificationPreferences:
        """알림 설정 조회"""
        query = text(f"""
            SELECT student_id, risk_alert_enabled, goal_reminder_enabled,
                   opportunity_enabled, badge_earned_enabled, coaching_checkin_enabled,
                   system_enabled, email_enabled, push_enabled,
                   quiet_hours_start, quiet_hours_end
            FROM {self.schema}.tb_notification_preferences
            WHERE student_id = :student_id
        """)

        result = await self.db.execute(query, {"student_id": student_id})
        row = result.fetchone()

        if row:
            return NotificationPreferences(
                student_id=row.student_id,
                risk_alert_enabled=row.risk_alert_enabled,
                goal_reminder_enabled=row.goal_reminder_enabled,
                opportunity_enabled=row.opportunity_enabled,
                badge_earned_enabled=row.badge_earned_enabled,
                coaching_checkin_enabled=row.coaching_checkin_enabled,
                system_enabled=row.system_enabled,
                email_enabled=row.email_enabled,
                push_enabled=row.push_enabled,
                quiet_hours_start=row.quiet_hours_start,
                quiet_hours_end=row.quiet_hours_end
            )

        # 기본 설정 생성
        return await self._create_default_preferences(student_id)

    async def update_preferences(
        self,
        student_id: str,
        updates: NotificationPreferencesUpdate
    ) -> NotificationPreferences:
        """알림 설정 업데이트"""
        # 기존 설정 확인 (없으면 생성)
        await self.get_preferences(student_id)

        update_fields = []
        params = {"student_id": student_id}

        update_data = updates.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            update_fields.append(f"{field} = :{field}")
            params[field] = value

        if not update_fields:
            return await self.get_preferences(student_id)

        update_sql = ", ".join(update_fields)
        query = text(f"""
            UPDATE {self.schema}.tb_notification_preferences
            SET {update_sql}
            WHERE student_id = :student_id
        """)

        await self.db.execute(query, params)
        return await self.get_preferences(student_id)

    async def _create_default_preferences(self, student_id: str) -> NotificationPreferences:
        """기본 알림 설정 생성"""
        query = text(f"""
            INSERT INTO {self.schema}.tb_notification_preferences (
                student_id, risk_alert_enabled, goal_reminder_enabled,
                opportunity_enabled, badge_earned_enabled, coaching_checkin_enabled,
                system_enabled, email_enabled, push_enabled
            ) VALUES (
                :student_id, true, true, true, true, true, true, false, true
            )
            ON CONFLICT (student_id) DO NOTHING
            RETURNING student_id
        """)

        await self.db.execute(query, {"student_id": student_id})

        return NotificationPreferences(
            student_id=student_id,
            risk_alert_enabled=True,
            goal_reminder_enabled=True,
            opportunity_enabled=True,
            badge_earned_enabled=True,
            coaching_checkin_enabled=True,
            system_enabled=True,
            email_enabled=False,
            push_enabled=True
        )

    def _is_notification_enabled(
        self,
        preferences: NotificationPreferences,
        notification_type: NotificationType
    ) -> bool:
        """알림 유형별 활성화 여부 확인"""
        type_map = {
            NotificationType.RISK_ALERT: preferences.risk_alert_enabled,
            NotificationType.GOAL_REMINDER: preferences.goal_reminder_enabled,
            NotificationType.OPPORTUNITY: preferences.opportunity_enabled,
            NotificationType.BADGE_EARNED: preferences.badge_earned_enabled,
            NotificationType.COACHING_CHECKIN: preferences.coaching_checkin_enabled,
            NotificationType.SYSTEM: preferences.system_enabled
        }
        return type_map.get(notification_type, True)

    def _row_to_response(self, row) -> NotificationResponse:
        """DB row를 응답 객체로 변환"""
        return NotificationResponse(
            notification_id=row.notification_id,
            student_id=row.student_id,
            notification_type=NotificationType(row.notification_type),
            title=row.title,
            message=row.message,
            reference_type=row.reference_type,
            reference_id=row.reference_id,
            priority=row.priority,
            is_read=row.is_read,
            read_at=row.read_at,
            created_at=row.created_at
        )
