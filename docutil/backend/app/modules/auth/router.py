"""
FastAPI router for authentication endpoints.

All routes in this module are mounted under the ``/auth`` prefix by the
application factory.  The router itself uses ``prefix=""`` so that the
parent mount point has full control over the final URL namespace.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import verify_token

from .schemas import (
    LoginRequest,
    LoginResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    TokenRefreshRequest,
    TokenRefreshResponse,
    UserInfo,
)
from app.modules.audit.service import AuditService
from .service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["auth"])

# Reusable security scheme for endpoints that require a bearer token.
_bearer_scheme = HTTPBearer()


# ---------------------------------------------------------------------------
# POST /login
# ---------------------------------------------------------------------------


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate a user",
    description=(
        "Validate credentials and return an access/refresh token pair. "
        "After 5 consecutive failed attempts the account is locked for "
        "30 minutes."
    ),
    responses={
        401: {"description": "Invalid credentials or account locked."},
    },
)
async def login(
    payload: LoginRequest,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Exchange username + password for JWT tokens."""

    user = await AuthService.authenticate_user(
        db=db,
        username=payload.username,
        password=payload.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials or account is locked.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tokens = AuthService.create_tokens(user, remember_me=payload.remember_me)

    # 감사 로그: 로그인 성공 기록
    try:
        await AuditService.create_log(
            db=db,
            org_id=user.organization_id,
            user_id=user.id,
            action="auth.login",
            resource_type="auth",
            details={"username": user.username},
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
        )
    except Exception:
        pass  # 감사 로그 실패가 주 흐름을 막지 않도록 함

    user_info = UserInfo(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role.value if hasattr(user.role, "value") else user.role,
        organization_id=user.organization_id,
    )

    return LoginResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        user=user_info,
    )


# ---------------------------------------------------------------------------
# POST /logout
# ---------------------------------------------------------------------------


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Invalidate the current access token",
    description=(
        "Adds the presented token to a Redis-backed blacklist so it can no "
        "longer be used, even if it has not yet expired."
    ),
    responses={
        200: {
            "description": "Token successfully invalidated.",
            "content": {
                "application/json": {
                    "example": {"detail": "Successfully logged out."},
                },
            },
        },
        401: {"description": "Missing or invalid authorization header."},
    },
)
async def logout(
    request: Request = None,
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Blacklist the caller's access token in Redis."""

    token = credentials.credentials
    settings = get_settings()

    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Remaining TTL in seconds -- blacklist only needs to live that long.
    exp = payload.get("exp")
    if exp is not None:
        remaining = int(exp - datetime.now(timezone.utc).timestamp())
        ttl = max(remaining, 0)
    else:
        ttl = settings.jwt_access_token_expire_minutes * 60

    redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        await redis.setex(
            name=f"token_blacklist:{token}",
            time=ttl,
            value="1",
        )
    finally:
        await redis.aclose()

    # 감사 로그: 로그아웃 성공 기록
    try:
        from uuid import UUID as _UUID  # noqa: WPS433

        _user_id = payload.get("sub")
        _org_id = payload.get("organization_id")
        await AuditService.create_log(
            db=db,
            org_id=_UUID(_org_id) if _org_id else None,
            user_id=_UUID(_user_id) if _user_id else None,
            action="auth.logout",
            resource_type="auth",
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
        )
    except Exception:
        pass  # 감사 로그 실패가 주 흐름을 막지 않도록 함

    logger.info("Token blacklisted for user %s", payload.get("sub"))
    return {"detail": "Successfully logged out."}


# ---------------------------------------------------------------------------
# POST /refresh
# ---------------------------------------------------------------------------


@router.post(
    "/refresh",
    response_model=TokenRefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh an access token",
    description=(
        "Present a valid refresh token to receive a new short-lived "
        "access token without re-authenticating."
    ),
    responses={
        401: {"description": "Invalid or expired refresh token."},
    },
)
async def refresh(
    payload: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenRefreshResponse:
    """Issue a fresh access token from a valid refresh token."""

    try:
        new_access_token = await AuthService.refresh_token(
            db=db,
            refresh_token=payload.refresh_token,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return TokenRefreshResponse(access_token=new_access_token)


# ---------------------------------------------------------------------------
# POST /password/reset-request
# ---------------------------------------------------------------------------


@router.post(
    "/password/reset-request",
    status_code=status.HTTP_200_OK,
    summary="Request a password reset",
    description=(
        "Initiates the password-reset flow.  If an account with the given "
        "email exists, a reset token is generated (and would normally be "
        "sent via email).  The response is always 200 to prevent user "
        "enumeration."
    ),
    responses={
        200: {
            "description": "Request accepted (regardless of email existence).",
            "content": {
                "application/json": {
                    "example": {
                        "detail": (
                            "If an account with that email exists, a reset "
                            "link has been sent."
                        ),
                    },
                },
            },
        },
    },
)
async def password_reset_request(
    payload: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Generate a password-reset token (if the email matches a user)."""

    token = await AuthService.request_password_reset(db=db, email=payload.email)

    if token is not None:
        # In production this token would be embedded in an email link.
        # For now we simply log it at DEBUG level for local development.
        logger.debug("Password-reset token generated: %s", token)

    # Always return a uniform message to avoid leaking account existence.
    return {
        "detail": (
            "If an account with that email exists, a password reset link "
            "has been sent."
        ),
    }


# ---------------------------------------------------------------------------
# POST /password/reset
# ---------------------------------------------------------------------------


@router.post(
    "/password/reset",
    status_code=status.HTTP_200_OK,
    summary="Reset password with a token",
    description=(
        "Completes the password-reset flow.  The one-time token must be "
        "valid and not expired (1-hour window)."
    ),
    responses={
        200: {
            "description": "Password successfully reset.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Password has been reset successfully.",
                    },
                },
            },
        },
        400: {"description": "Invalid or expired reset token."},
    },
)
async def password_reset(
    payload: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Apply a new password using the one-time reset token."""

    success = await AuthService.reset_password(
        db=db,
        token=payload.token,
        new_password=payload.new_password,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password-reset token.",
        )

    return {"detail": "Password has been reset successfully."}
