"""
Authentication API endpoints.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas.auth import (
    EmailOtpRequest,
    EmailOtpResponse,
    LoginRequest,
    LoginResponse,
    MfaVerifyRequest,
    MfaVerifyResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    VerifyTokenResponse,
)
from ..services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


async def get_auth_service(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AuthService:
    """Dependency to get auth service instance."""
    return AuthService(request.app.state.redis, db)


@router.post("/login", response_model=LoginResponse)
async def login(
    login_request: LoginRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Authenticate user and return tokens.

    - **username**: User's username (login_id)
    - **password**: User's password

    Returns access token, refresh token, and user info.
    If MFA is enabled, mfa_required will be true.
    """
    # Get client info
    ip_address = request.client.host if request.client else "0.0.0.0"
    user_agent = request.headers.get("user-agent", "")
    device_type = "mobile" if "Mobile" in user_agent else "web"

    result = await auth_service.login(
        login_request,
        ip_address=ip_address,
        user_agent=user_agent,
        device_type=device_type,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return result


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    request: TokenRefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Refresh access token using refresh token.

    - **refresh_token**: Valid refresh token

    Returns new access token.
    """
    result = await auth_service.refresh_token(request.refresh_token)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return result


@router.get("/verify", response_model=VerifyTokenResponse)
async def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Verify access token validity.

    Requires Bearer token in Authorization header.
    Used by other services to validate tokens.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await auth_service.verify_token(credentials.credentials)

    if not result.valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return result


@router.post("/logout")
async def logout(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Logout user and invalidate tokens.

    Requires Bearer token in Authorization header.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token first
    verify_result = await auth_service.verify_token(credentials.credentials)

    if not verify_result.valid or not verify_result.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    success = await auth_service.logout(verify_result.user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout",
        )

    return {"message": "Successfully logged out"}


@router.post("/mfa/verify", response_model=MfaVerifyResponse)
async def verify_mfa(
    request: MfaVerifyRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Verify MFA code (TOTP or Email OTP).

    - **user_id**: User ID from login response
    - **code**: 6-digit verification code
    - **method**: 'totp' or 'email'

    Returns access token and refresh token on success.
    """
    result = await auth_service.verify_mfa(
        user_id=request.user_id,
        code=request.code,
        method=request.method,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.message or "MFA verification failed",
        )

    return result


@router.post("/mfa/send-email", response_model=EmailOtpResponse)
async def send_email_otp(
    request: EmailOtpRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Send email OTP for 2FA.

    - **user_id**: User ID from login response

    Sends a 6-digit code to the user's registered email.
    Code expires in 5 minutes.
    """
    result = await auth_service.send_email_otp(request.user_id)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message or "Failed to send email OTP",
        )

    return result
