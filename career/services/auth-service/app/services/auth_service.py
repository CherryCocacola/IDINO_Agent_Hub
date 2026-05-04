"""
Authentication service business logic.
"""
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4, UUID

import pyotp
import redis.asyncio as redis
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..repositories.user_repository import UserRepository
from ..schemas.auth import (
    LoginRequest,
    LoginResponse,
    MfaVerifyResponse,
    EmailOtpResponse,
    TokenRefreshResponse,
    UserInfo,
    VerifyTokenResponse,
)

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication service."""

    def __init__(self, redis_client: redis.Redis, db_session: AsyncSession):
        self.redis = redis_client
        self.db = db_session
        self.user_repo = UserRepository(db_session)
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_expire = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_expire = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def hash_password(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    def create_access_token(
        self,
        user_id: str,
        username: str,
        role_level: int,
        department_id: Optional[str] = None,
    ) -> tuple[str, int]:
        """Create a new access token."""
        now = datetime.utcnow()
        expire = now + timedelta(minutes=self.access_expire)

        payload = {
            "sub": user_id,
            "user_id": user_id,
            "username": username,
            "role_level": role_level,
            "department_id": department_id,
            "exp": expire,
            "iat": now,
            "type": "access",
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        expires_in = int((expire - now).total_seconds())

        return token, expires_in

    def create_refresh_token(self, user_id: str) -> str:
        """Create a new refresh token."""
        now = datetime.utcnow()
        expire = now + timedelta(days=self.refresh_expire)

        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": now,
            "type": "refresh",
            "jti": str(uuid4()),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def _get_role_level(self, user_type: str) -> int:
        """Map user type to role level."""
        role_map = {
            "admin": 1,
            "career_admin": 2,
            "advisor": 3,
            "professor": 4,
            "student": 5,
        }
        return role_map.get(user_type, 5)

    async def login(
        self,
        request: LoginRequest,
        ip_address: str = "0.0.0.0",
        user_agent: str = "",
        device_type: str = "web",
    ) -> Optional[LoginResponse]:
        """Authenticate user and return tokens."""
        # Get user from database
        user = await self.user_repo.get_user_by_login_id(request.username)

        if not user:
            # Log failed attempt
            await self.user_repo.log_login_attempt(
                login_id=request.username,
                user_id=None,
                result="failed",
                failure_reason="user_not_found",
                ip_address=ip_address,
                user_agent=user_agent,
                device_type=device_type,
            )
            logger.warning(f"Login failed: user not found - {request.username}")
            return None

        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            await self.user_repo.log_login_attempt(
                login_id=request.username,
                user_id=user.user_id,
                result="failed",
                failure_reason="account_locked",
                ip_address=ip_address,
                user_agent=user_agent,
                device_type=device_type,
            )
            logger.warning(f"Login failed: account locked - {request.username}")
            return None

        # Verify password
        if not self.verify_password(request.password, user.password_hash):
            # Update failed login count
            failed_count, locked_until = await self.user_repo.update_login_failure(user.user_id)

            await self.user_repo.log_login_attempt(
                login_id=request.username,
                user_id=user.user_id,
                result="failed",
                failure_reason="invalid_password",
                ip_address=ip_address,
                user_agent=user_agent,
                device_type=device_type,
            )
            logger.warning(f"Login failed: invalid password - {request.username}")
            return None

        # Check if MFA is required (MFA enabled AND secret is configured)
        mfa_required = user.mfa_enabled and user.mfa_secret is not None

        # Create tokens
        role_level = self._get_role_level(user.user_type)
        department_id = None  # Will be fetched from student/professor table if needed

        access_token, expires_in = self.create_access_token(
            user_id=str(user.user_id),
            username=user.login_id,
            role_level=role_level,
            department_id=department_id,
        )

        refresh_token = self.create_refresh_token(str(user.user_id))

        # Calculate token expiry
        token_expires_at = datetime.utcnow() + timedelta(days=self.refresh_expire)

        # Create session in database
        await self.user_repo.create_session(
            user_id=user.user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            device_type=device_type,
            device_name=user_agent[:100] if user_agent else "Unknown",
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=token_expires_at,
            mfa_verified=not mfa_required,  # If MFA not required, mark as verified
        )

        # Update login success
        await self.user_repo.update_login_success(user.user_id, ip_address)

        # Log successful login
        await self.user_repo.log_login_attempt(
            login_id=request.username,
            user_id=user.user_id,
            result="success",
            failure_reason=None,
            ip_address=ip_address,
            user_agent=user_agent,
            device_type=device_type,
        )

        # Store session in Redis for quick access (if Redis is available)
        if self.redis:
            try:
                await self.redis.setex(
                    f"session:{user.user_id}",
                    timedelta(minutes=self.access_expire),
                    user.login_id,
                )
            except Exception as e:
                logger.warning(f"Redis session storage failed: {e}")

        logger.info(f"Login successful: {request.username}")

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            mfa_required=mfa_required,
            user=UserInfo(
                user_id=str(user.user_id),
                username=user.login_id,
                email=user.email,
                role_level=role_level,
                department_id=department_id,
                name=user.user_nm,  # 사용자 이름 (한글)
                student_id=user.student_id,
            ),
        )

    async def refresh_token(self, refresh_token: str) -> Optional[TokenRefreshResponse]:
        """Refresh access token using refresh token."""
        try:
            payload = jwt.decode(
                refresh_token, self.secret_key, algorithms=[self.algorithm]
            )

            if payload.get("type") != "refresh":
                logger.warning("Invalid token type for refresh")
                return None

            user_id = payload.get("sub")

            # Verify session exists in database
            session = await self.user_repo.get_session_by_refresh_token(refresh_token)
            if not session:
                logger.warning(f"Session not found for refresh token: {user_id}")
                return None

            # Get user info
            user = await self.user_repo.get_user_by_id(UUID(user_id))
            if not user or user.status != "active":
                logger.warning(f"User not active or not found: {user_id}")
                return None

            # Update session activity
            await self.user_repo.update_session_activity(session.session_id)

            # Create new access token
            role_level = self._get_role_level(user.user_type)
            access_token, expires_in = self.create_access_token(
                user_id=str(user.user_id),
                username=user.login_id,
                role_level=role_level,
                department_id=None,
            )

            logger.info(f"Token refreshed for user: {user_id}")

            return TokenRefreshResponse(
                access_token=access_token,
                expires_in=expires_in,
            )

        except JWTError as e:
            logger.error(f"JWT error during refresh: {e}")
            return None

    async def verify_token(self, token: str) -> VerifyTokenResponse:
        """Verify an access token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            return VerifyTokenResponse(
                valid=True,
                user_id=payload.get("user_id"),
                username=payload.get("username"),
                role_level=payload.get("role_level"),
                department_id=payload.get("department_id"),
                exp=datetime.fromtimestamp(payload.get("exp")),
                iat=datetime.fromtimestamp(payload.get("iat")),
            )

        except JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            return VerifyTokenResponse(valid=False)

    async def logout(self, user_id: str, session_id: Optional[str] = None) -> bool:
        """Logout user by revoking session."""
        try:
            if session_id:
                # Revoke specific session
                await self.user_repo.revoke_session(UUID(session_id), "logout")
            else:
                # Revoke all sessions
                await self.user_repo.revoke_all_user_sessions(UUID(user_id), "logout")

            # Remove from Redis (if Redis is available)
            if self.redis:
                try:
                    await self.redis.delete(f"session:{user_id}")
                except Exception as e:
                    logger.warning(f"Redis session deletion failed: {e}")

            logger.info(f"User logged out: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Logout failed: {e}")
            return False

    async def verify_mfa(
        self,
        user_id: str,
        code: str,
        method: str = "totp",
    ) -> MfaVerifyResponse:
        """Verify MFA code and return tokens if successful."""
        try:
            user = await self.user_repo.get_user_by_id(UUID(user_id))
            if not user:
                logger.warning(f"MFA verification failed: user not found - {user_id}")
                return MfaVerifyResponse(success=False, message="User not found")

            # Verify based on method
            if method == "totp":
                # Verify TOTP code
                if not user.mfa_secret:
                    logger.warning(f"MFA verification failed: TOTP not configured - {user_id}")
                    return MfaVerifyResponse(success=False, message="TOTP not configured")

                totp = pyotp.TOTP(user.mfa_secret)
                # Allow 2 window tolerance (±60 seconds for 30-sec TOTP) to handle time drift
                if not totp.verify(code, valid_window=2):
                    logger.warning(f"MFA verification failed: invalid TOTP code - {user_id}")
                    return MfaVerifyResponse(success=False, message="Invalid verification code")

            elif method == "email":
                # Verify email OTP from Redis
                if not self.redis:
                    logger.error("Redis not available for email OTP verification")
                    return MfaVerifyResponse(success=False, message="Email OTP service unavailable")

                stored_otp = await self.redis.get(f"email_otp:{user_id}")
                if not stored_otp:
                    logger.warning(f"MFA verification failed: OTP expired or not found - {user_id}")
                    return MfaVerifyResponse(success=False, message="OTP expired or not found")

                if stored_otp.decode() != code:
                    logger.warning(f"MFA verification failed: invalid email OTP - {user_id}")
                    return MfaVerifyResponse(success=False, message="Invalid verification code")

                # Delete used OTP
                await self.redis.delete(f"email_otp:{user_id}")
            else:
                return MfaVerifyResponse(success=False, message="Invalid MFA method")

            # MFA verified - create new tokens
            role_level = self._get_role_level(user.user_type)
            access_token, expires_in = self.create_access_token(
                user_id=str(user.user_id),
                username=user.login_id,
                role_level=role_level,
                department_id=None,
            )
            refresh_token = self.create_refresh_token(str(user.user_id))

            # Update session to mark MFA as verified
            await self.user_repo.mark_session_mfa_verified(UUID(user_id))

            logger.info(f"MFA verification successful: {user_id}")

            return MfaVerifyResponse(
                success=True,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=expires_in,
            )

        except Exception as e:
            logger.error(f"MFA verification error: {e}")
            return MfaVerifyResponse(success=False, message="Verification failed")

    async def send_email_otp(self, user_id: str) -> EmailOtpResponse:
        """Generate and send email OTP."""
        try:
            user = await self.user_repo.get_user_by_id(UUID(user_id))
            if not user:
                logger.warning(f"Email OTP failed: user not found - {user_id}")
                return EmailOtpResponse(success=False, message="User not found")

            if not user.email:
                logger.warning(f"Email OTP failed: email not configured - {user_id}")
                return EmailOtpResponse(success=False, message="Email not configured")

            # Generate 6-digit OTP
            otp = "".join([str(secrets.randbelow(10)) for _ in range(6)])

            # Store OTP in Redis with 5-minute expiry
            if not self.redis:
                logger.error("Redis not available for email OTP storage")
                return EmailOtpResponse(success=False, message="OTP service unavailable")

            await self.redis.setex(
                f"email_otp:{user_id}",
                300,  # 5 minutes
                otp,
            )

            # TODO: Implement actual email sending
            # For now, log the OTP (in production, this should send an email)
            logger.info(f"Email OTP generated for {user.email}: {otp}")

            # In development, we can also store in a way that frontend can display
            # This is only for testing - remove in production
            if settings.DEBUG:
                logger.debug(f"[DEV] Email OTP for {user_id}: {otp}")

            return EmailOtpResponse(
                success=True,
                message="Verification code sent to your email",
            )

        except Exception as e:
            logger.error(f"Email OTP error: {e}")
            return EmailOtpResponse(success=False, message="Failed to send OTP")
