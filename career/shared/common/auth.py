"""
JWT authentication utilities shared across all services.
"""
import os
from datetime import datetime, timedelta
from typing import Optional

import httpx
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel


class TokenPayload(BaseModel):
    """JWT token payload schema."""
    sub: str
    exp: datetime
    iat: datetime
    user_id: str
    username: str
    role_level: int
    department_id: Optional[str] = None


class JWTBearer(HTTPBearer):
    """
    Custom JWT Bearer authentication.
    Validates JWT tokens by calling auth-service.
    """

    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        self.auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")

    async def __call__(self, request: Request) -> Optional[TokenPayload]:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)

        if not credentials:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authorization credentials"
                )
            return None

        if credentials.scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authentication scheme"
                )
            return None

        return await self.verify_token(credentials.credentials)

    async def verify_token(self, token: str) -> TokenPayload:
        """Verify token by calling auth-service."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.auth_service_url}/auth/verify",
                    headers={"Authorization": f"Bearer {token}"}
                )

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token validation failed"
                    )

                data = response.json()
                return TokenPayload(**data)

        except httpx.RequestError:
            # Fallback to local verification if auth-service is unavailable
            return self._verify_token_locally(token)

    def _verify_token_locally(self, token: str) -> TokenPayload:
        """Local JWT verification fallback."""
        secret_key = os.getenv("JWT_SECRET_KEY")
        algorithm = os.getenv("JWT_ALGORITHM", "HS256")

        if not secret_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="JWT configuration missing"
            )

        try:
            payload = jwt.decode(token, secret_key, algorithms=[algorithm])
            return TokenPayload(**payload)
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )


async def verify_token(token: str) -> TokenPayload:
    """Standalone token verification function."""
    bearer = JWTBearer(auto_error=True)
    return await bearer.verify_token(token)


async def get_current_user(request: Request) -> TokenPayload:
    """Dependency to get current authenticated user."""
    bearer = JWTBearer(auto_error=True)
    return await bearer(request)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a new JWT access token."""
    secret_key = os.getenv("JWT_SECRET_KEY")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    expire_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    to_encode = data.copy()
    now = datetime.utcnow()

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=expire_minutes)

    to_encode.update({
        "exp": expire,
        "iat": now,
    })

    return jwt.encode(to_encode, secret_key, algorithm=algorithm)


def create_refresh_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a new JWT refresh token."""
    secret_key = os.getenv("JWT_SECRET_KEY")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    expire_days = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    to_encode = data.copy()
    now = datetime.utcnow()

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=expire_days)

    to_encode.update({
        "exp": expire,
        "iat": now,
        "type": "refresh",
    })

    return jwt.encode(to_encode, secret_key, algorithm=algorithm)
