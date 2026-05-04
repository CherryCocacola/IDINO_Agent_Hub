"""
User repository for database operations.
"""
import hashlib
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import AuthSession, LoginHistory, User

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user-related database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_login_id(self, login_id: str) -> Optional[User]:
        """Get user by login ID."""
        query = select(User).where(
            User.login_id == login_id,
            User.status != "inactive"
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        query = select(User).where(User.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_login_success(
        self,
        user_id: UUID,
        ip_address: str,
    ) -> None:
        """Update user record on successful login."""
        query = (
            update(User)
            .where(User.user_id == user_id)
            .values(
                login_fail_count=0,
                locked_until=None,
                last_login=datetime.utcnow(),
                upd_dt=datetime.utcnow(),
            )
        )
        await self.session.execute(query)
        await self.session.commit()

    async def update_login_failure(
        self,
        user_id: UUID,
    ) -> tuple[int, Optional[datetime]]:
        """Increment failed login count and potentially lock account."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return 0, None

        new_count = (user.login_fail_count or 0) + 1
        locked_until = None

        # Lock account after 5 failures for 30 minutes
        if new_count >= 5:
            from datetime import timedelta
            locked_until = datetime.utcnow() + timedelta(minutes=30)

        query = (
            update(User)
            .where(User.user_id == user_id)
            .values(
                login_fail_count=new_count,
                locked_until=locked_until,
                upd_dt=datetime.utcnow(),
            )
        )
        await self.session.execute(query)
        await self.session.commit()

        return new_count, locked_until

    async def create_session(
        self,
        user_id: UUID,
        access_token: str,
        refresh_token: str,
        device_type: str,
        device_name: str,
        user_agent: str,
        ip_address: str,
        expires_at: datetime,
        mfa_verified: bool = False,
    ) -> AuthSession:
        """Create a new authentication session."""
        session = AuthSession(
            session_id=uuid4(),
            user_id=user_id,
            access_token_hash=hashlib.sha256(access_token.encode()).hexdigest(),
            refresh_token_hash=hashlib.sha256(refresh_token.encode()).hexdigest(),
            device_type=device_type,
            device_name=device_name,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=expires_at,
            mfa_verified=mfa_verified,
            is_active=True,
            issued_at=datetime.utcnow(),
            last_activity_at=datetime.utcnow(),
            ins_user_id=str(user_id),
            ins_dt=datetime.utcnow(),
        )
        self.session.add(session)
        await self.session.commit()
        await self.session.refresh(session)
        return session

    async def get_session_by_refresh_token(
        self,
        refresh_token: str,
    ) -> Optional[AuthSession]:
        """Get active session by refresh token hash."""
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        query = select(AuthSession).where(
            AuthSession.refresh_token_hash == token_hash,
            AuthSession.is_active == True,
            AuthSession.expires_at > datetime.utcnow(),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_session_activity(self, session_id: UUID) -> None:
        """Update session last activity timestamp."""
        query = (
            update(AuthSession)
            .where(AuthSession.session_id == session_id)
            .values(last_activity_at=datetime.utcnow())
        )
        await self.session.execute(query)
        await self.session.commit()

    async def revoke_session(
        self,
        session_id: UUID,
        reason: str = "logout",
    ) -> None:
        """Revoke a session."""
        query = (
            update(AuthSession)
            .where(AuthSession.session_id == session_id)
            .values(
                is_active=False,
                revoked_at=datetime.utcnow(),
                revoked_reason=reason,
            )
        )
        await self.session.execute(query)
        await self.session.commit()

    async def revoke_all_user_sessions(
        self,
        user_id: UUID,
        reason: str = "logout_all",
    ) -> int:
        """Revoke all sessions for a user."""
        query = (
            update(AuthSession)
            .where(
                AuthSession.user_id == user_id,
                AuthSession.is_active == True,
            )
            .values(
                is_active=False,
                revoked_at=datetime.utcnow(),
                revoked_reason=reason,
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount

    async def log_login_attempt(
        self,
        login_id: str,
        user_id: Optional[UUID],
        result: str,
        failure_reason: Optional[str],  # kept for API compatibility, not stored
        ip_address: str,
        user_agent: str,
        device_type: str,
        is_suspicious: bool = False,
        risk_score: int = 0,
    ) -> LoginHistory:
        """Log a login attempt."""
        history = LoginHistory(
            history_id=uuid4(),
            user_id=user_id,
            login_id=login_id,
            login_result=result,
            # failure_reason not in DB schema
            ip_address=ip_address,
            user_agent=user_agent,
            device_type=device_type,
            is_suspicious=is_suspicious,
            risk_score=risk_score,
            attempted_at=datetime.utcnow(),
        )
        self.session.add(history)
        await self.session.commit()
        return history

    async def update_mfa_verified(self, session_id: UUID) -> None:
        """Mark session as MFA verified."""
        query = (
            update(AuthSession)
            .where(AuthSession.session_id == session_id)
            .values(
                mfa_verified=True,
                last_activity_at=datetime.utcnow(),
            )
        )
        await self.session.execute(query)
        await self.session.commit()

    async def mark_session_mfa_verified(self, user_id: UUID) -> None:
        """Mark the latest active session for a user as MFA verified."""
        query = (
            update(AuthSession)
            .where(
                AuthSession.user_id == user_id,
                AuthSession.is_active == True,
                AuthSession.mfa_verified == False,
            )
            .values(
                mfa_verified=True,
                last_activity_at=datetime.utcnow(),
            )
        )
        await self.session.execute(query)
        await self.session.commit()
