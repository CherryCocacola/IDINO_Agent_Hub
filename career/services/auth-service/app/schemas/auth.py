"""
Authentication request/response schemas.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login request schema."""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=4)  # Changed from 6 to 4 for demo


class LoginResponse(BaseModel):
    """Login response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    mfa_required: bool = False  # 2FA 필요 여부
    user: "UserInfo"


class TokenRefreshRequest(BaseModel):
    """Token refresh request schema."""

    refresh_token: str


class TokenRefreshResponse(BaseModel):
    """Token refresh response schema."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """JWT token payload schema."""

    sub: str
    exp: datetime
    iat: datetime
    user_id: str
    username: str
    role_level: int
    department_id: Optional[str] = None


class UserInfo(BaseModel):
    """User information schema."""

    user_id: str
    username: str
    email: str
    role_level: int
    department_id: Optional[str] = None
    name: Optional[str] = None
    student_id: Optional[str] = None


class VerifyTokenResponse(BaseModel):
    """Token verification response."""

    valid: bool
    user_id: Optional[str] = None
    username: Optional[str] = None
    role_level: Optional[int] = None
    department_id: Optional[str] = None
    exp: Optional[datetime] = None
    iat: Optional[datetime] = None


# MFA Schemas
class MfaVerifyRequest(BaseModel):
    """MFA verification request schema."""

    user_id: str
    code: str = Field(..., min_length=6, max_length=6)
    method: str = Field(default="totp", pattern="^(totp|email)$")


class MfaVerifyResponse(BaseModel):
    """MFA verification response schema."""

    success: bool
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    message: Optional[str] = None


class EmailOtpRequest(BaseModel):
    """Email OTP request schema."""

    user_id: str


class EmailOtpResponse(BaseModel):
    """Email OTP response schema."""

    success: bool
    message: Optional[str] = None


# Update forward references
LoginResponse.model_rebuild()
