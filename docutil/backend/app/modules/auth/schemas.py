"""
Pydantic v2 schemas for authentication requests and responses.

These schemas handle validation and serialization for login, token refresh,
password reset, and related auth flows.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------------------------
# Shared / embedded schemas
# ---------------------------------------------------------------------------


class UserInfo(BaseModel):
    """Public-facing user information embedded in auth responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: str
    role: str
    organization_id: UUID


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    """Credentials submitted by the user to obtain tokens."""

    username: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Username or email used to authenticate.",
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Plain-text password (transmitted over TLS).",
    )
    remember_me: bool = Field(
        default=False,
        description=(
            "When True the refresh token is issued with a longer lifetime."
        ),
    )


class LoginResponse(BaseModel):
    """Tokens and basic user info returned after successful authentication."""

    model_config = ConfigDict(from_attributes=True)

    access_token: str = Field(
        ..., description="Short-lived JWT access token."
    )
    refresh_token: str = Field(
        ..., description="Long-lived JWT refresh token."
    )
    token_type: str = Field(
        default="bearer", description="OAuth2-compatible token type."
    )
    user: UserInfo


# ---------------------------------------------------------------------------
# Token refresh
# ---------------------------------------------------------------------------


class TokenRefreshRequest(BaseModel):
    """Payload sent when the client needs a fresh access token."""

    refresh_token: str = Field(
        ..., description="The refresh token obtained during login."
    )


class TokenRefreshResponse(BaseModel):
    """Response containing only the new access token."""

    access_token: str = Field(
        ..., description="Newly issued short-lived JWT access token."
    )
    token_type: str = Field(
        default="bearer", description="OAuth2-compatible token type."
    )


# ---------------------------------------------------------------------------
# Password reset
# ---------------------------------------------------------------------------


class PasswordResetRequest(BaseModel):
    """Initiates the password-reset flow by providing the account email."""

    email: EmailStr = Field(
        ..., description="Email address associated with the account."
    )


class PasswordResetConfirm(BaseModel):
    """Completes the password-reset flow with a one-time token."""

    token: str = Field(
        ...,
        min_length=1,
        description="One-time password-reset token received via email.",
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="The new password to set (min 8 characters).",
    )


# ---------------------------------------------------------------------------
# Change password (authenticated)
# ---------------------------------------------------------------------------


class ChangePasswordRequest(BaseModel):
    """Allows an authenticated user to change their own password."""

    current_password: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="The user's current password for verification.",
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="The new password to set (min 8 characters).",
    )
