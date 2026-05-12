"""
Authentication business logic.

Handles credential verification, token lifecycle, account lockout policy,
and password-reset flows.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
)
from app.modules.users.models import User

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_FAILED_ATTEMPTS: int = 5
LOCKOUT_DURATION_MINUTES: int = 30


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class AuthService:
    """Stateless helper that encapsulates all authentication operations.

    Every public method receives a database session explicitly so callers
    (typically FastAPI route handlers) can control the transaction boundary.
    """

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        username: str,
        password: str,
        org_id: UUID | None = None,
    ) -> User | None:
        """Verify credentials and return the ``User`` on success, or ``None``.

        Behaviour
        ---------
        * If the user does not exist, return ``None`` immediately.
        * If the account is currently locked and the lock window has **not**
          expired, return ``None``.
        * On a wrong password the ``failed_login_count`` is incremented.
          After ``MAX_FAILED_ATTEMPTS`` consecutive failures the account is
          locked for ``LOCKOUT_DURATION_MINUTES`` minutes.
        * On a correct password the failure counter is reset and
          ``last_login_at`` is updated.
        """

        # -- look up user -------------------------------------------------
        # username, 전체 email, 또는 email 로컬파트(@ 앞부분)로 검색
        # 트랙 #88 — 통합 후 tb_users.username 은 진짜 운영 데이터의 한국어 이름.
        # 사용자는 보통 email 로 로그인하므로 User.email 매칭도 함께 검사.
        from sqlalchemy import or_, func

        stmt = select(User).where(
            or_(
                User.username == username,
                User.email == username,
                func.split_part(User.email, '@', 1) == username,
            )
        )
        if org_id is not None:
            stmt = stmt.where(User.organization_id == org_id)

        result = await db.execute(stmt)
        user: User | None = result.scalar_one_or_none()

        if user is None:
            return None

        # -- check active status ------------------------------------------
        if hasattr(user, "is_active") and not user.is_active:
            return None

        # -- check lockout ------------------------------------------------
        if await AuthService._is_locked(user):
            return None

        # -- verify password ----------------------------------------------
        if not verify_password(password, user.password_hash):
            await AuthService._record_failed_attempt(db, user)
            return None

        # -- success: reset counters --------------------------------------
        user.failed_login_count = 0
        user.locked_until = None
        user.last_login_at = datetime.now(timezone.utc)
        await db.flush()

        return user

    # ------------------------------------------------------------------
    # Token creation
    # ------------------------------------------------------------------

    @staticmethod
    def create_tokens(user: User, remember_me: bool = False) -> dict:
        """Issue an access / refresh token pair for an authenticated user.

        Parameters
        ----------
        user:
            The authenticated ``User`` ORM instance.
        remember_me:
            If ``True`` the refresh token receives a longer TTL (30 days
            instead of the default configured value).

        Returns
        -------
        dict
            ``{"access_token": ..., "refresh_token": ..., "token_type": "bearer"}``
        """

        settings = get_settings()

        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value if hasattr(user.role, "value") else user.role,
            "org": str(user.organization_id),
        }

        access_token = create_access_token(
            data=token_data,
            expires_delta=timedelta(
                minutes=settings.jwt_access_token_expire_minutes,
            ),
        )

        refresh_expires = timedelta(
            days=30 if remember_me else settings.jwt_refresh_token_expire_days,
        )
        refresh_token = create_refresh_token(
            data=token_data,
            expires_delta=refresh_expires,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    # ------------------------------------------------------------------
    # Token refresh
    # ------------------------------------------------------------------

    @staticmethod
    async def refresh_token(
        db: AsyncSession,
        refresh_token: str,
    ) -> str:
        """Validate a refresh token and issue a new access token.

        Parameters
        ----------
        db:
            Active database session.
        refresh_token:
            The JWT refresh token to verify.

        Returns
        -------
        str
            A freshly signed access token.

        Raises
        ------
        ValueError
            If the refresh token is invalid, expired, or refers to a user
            that no longer exists / is inactive.
        """

        payload = verify_token(refresh_token)
        if payload is None:
            raise ValueError("Invalid or expired refresh token.")

        user_id = payload.get("sub")
        if user_id is None:
            raise ValueError("Refresh token payload missing subject claim.")

        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user: User | None = result.scalar_one_or_none()

        if user is None:
            raise ValueError("User associated with token no longer exists.")

        if hasattr(user, "is_active") and not user.is_active:
            raise ValueError("User account is deactivated.")

        settings = get_settings()
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value if hasattr(user.role, "value") else user.role,
            "org": str(user.organization_id),
        }
        new_access_token = create_access_token(
            data=token_data,
            expires_delta=timedelta(
                minutes=settings.jwt_access_token_expire_minutes,
            ),
        )
        return new_access_token

    # ------------------------------------------------------------------
    # Password reset -- request
    # ------------------------------------------------------------------

    @staticmethod
    async def request_password_reset(
        db: AsyncSession,
        email: str,
    ) -> str | None:
        """Generate a one-time password-reset token for *email*.

        Returns the token string when a matching user is found, or ``None``
        when no account is associated with the address.  The caller should
        **never** reveal whether the email exists -- always return a
        success-like message to the end user.
        """

        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user: User | None = result.scalar_one_or_none()

        if user is None:
            return None

        # Generate a URL-safe token and persist it on the user row.
        token = secrets.token_urlsafe(32)
        user.password_reset_token = token
        user.password_reset_expires_at = datetime.now(timezone.utc) + timedelta(
            hours=1,
        )
        await db.flush()

        return token

    # ------------------------------------------------------------------
    # Password reset -- confirm
    # ------------------------------------------------------------------

    @staticmethod
    async def reset_password(
        db: AsyncSession,
        token: str,
        new_password: str,
    ) -> bool:
        """Apply a new password using a valid reset token.

        Returns ``True`` when the password was changed and ``False`` if the
        token is invalid or expired.
        """

        stmt = select(User).where(User.password_reset_token == token)
        result = await db.execute(stmt)
        user: User | None = result.scalar_one_or_none()

        if user is None:
            return False

        # Check expiry
        if (
            user.password_reset_expires_at is None
            or user.password_reset_expires_at < datetime.now(timezone.utc)
        ):
            # Expired -- clear the token so it cannot be reused.
            user.password_reset_token = None
            user.password_reset_expires_at = None
            await db.flush()
            return False

        # Apply new password
        user.password_hash = get_password_hash(new_password)
        user.password_reset_token = None
        user.password_reset_expires_at = None
        # Unlock the account in case it was locked
        user.failed_login_count = 0
        user.locked_until = None
        await db.flush()

        return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _is_locked(user: User) -> bool:
        """Return ``True`` if the user account is currently locked out."""
        if not hasattr(user, "locked_until") or user.locked_until is None:
            return False

        if user.locked_until > datetime.now(timezone.utc):
            return True

        # Lock window has expired -- clear it.
        user.locked_until = None
        user.failed_login_count = 0
        return False

    @staticmethod
    async def _record_failed_attempt(
        db: AsyncSession,
        user: User,
    ) -> None:
        """Increment the failure counter and lock the account if needed."""
        current_count = getattr(user, "failed_login_count", 0) or 0
        user.failed_login_count = current_count + 1

        if user.failed_login_count >= MAX_FAILED_ATTEMPTS:
            user.locked_until = datetime.now(timezone.utc) + timedelta(
                minutes=LOCKOUT_DURATION_MINUTES,
            )

        await db.flush()
