"""
FastAPI dependencies for authentication, authorisation, DB sessions,
and rate limiting.
"""

from __future__ import annotations

import time
import uuid
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import Depends, Header, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from .database import async_session_factory, audit_context
from .security import TokenData, TokenType, decode_token

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable

# ---------------------------------------------------------------------------
# Database session dependency
# ---------------------------------------------------------------------------


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an ``AsyncSession`` suitable for request-scoped work.

    The session is committed on success and rolled back on any exception.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Annotated shortcut for convenience in route signatures
DBSession = Annotated[AsyncSession, Depends(get_db_session)]

# ---------------------------------------------------------------------------
# JWT / current-user dependency
# ---------------------------------------------------------------------------


async def get_current_user(
    request: Request,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> TokenData:
    """Extract and validate the Bearer JWT from the *Authorization* header.

    Returns the decoded ``TokenData`` or raises *401 Unauthorized*.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if authorization is None:
        raise credentials_exception

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise credentials_exception

    token = parts[1]

    try:
        token_data = decode_token(token)
    except JWTError as err:
        raise credentials_exception from err

    if token_data.token_type != TokenType.ACCESS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Access token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token_data


CurrentUser = Annotated[TokenData, Depends(get_current_user)]

# ---------------------------------------------------------------------------
# Role-based access control (RBAC) dependency
# ---------------------------------------------------------------------------


def require_role(allowed_roles: list[str]) -> Callable[..., Any]:
    """Return a FastAPI dependency that enforces RBAC.

    Usage::

        @router.get("/admin/users", dependencies=[Depends(require_role(["admin"]))])
        async def list_users(...):
            ...

    Or inject it to receive the user data directly::

        @router.get("/org/settings")
        async def org_settings(
            user: TokenData = Depends(require_role(["admin", "org_admin"])),
        ):
            ...
    """

    async def _check_role(
        current_user: TokenData = Depends(get_current_user),
    ) -> TokenData:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(f"Role '{current_user.role}' is not authorised. Required: {allowed_roles}."),
            )
        return current_user

    return _check_role


# Convenience aliases - super_admin has access to everything
RequireAdmin = Depends(require_role(["super_admin", "admin"]))
RequireOrgAdmin = Depends(require_role(["super_admin", "admin", "org_admin"]))
RequireEditor = Depends(require_role(["super_admin", "admin", "org_admin", "editor", "member"]))
RequireViewer = Depends(require_role(["super_admin", "admin", "org_admin", "editor", "member", "viewer"]))

# ---------------------------------------------------------------------------
# In-memory rate limiter (per-endpoint, per-user)
# ---------------------------------------------------------------------------


class RateLimiter:
    """Simple sliding-window rate limiter backed by an in-memory dict.

    For production deployments behind multiple workers, swap the store for
    Redis (see ``RateLimitMiddleware`` in ``middleware.py``).

    Usage as a **dependency**::

        rate_limit = RateLimiter(max_requests=30, window_seconds=60)

        @router.post("/ask", dependencies=[Depends(rate_limit)])
        async def ask_question(...):
            ...
    """

    def __init__(self, max_requests: int = 60, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # key -> list of timestamps
        self._store: dict[str, list[float]] = {}

    def _key(self, request: Request, user: TokenData | None) -> str:
        if user is not None:
            return f"rl:{user.user_id}"
        forwarded = request.headers.get("X-Forwarded-For")
        client_ip = (
            forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
        )
        return f"rl:{client_ip}"

    def _prune(self, key: str, now: float) -> list[float]:
        timestamps = self._store.get(key, [])
        cutoff = now - self.window_seconds
        pruned = [t for t in timestamps if t > cutoff]
        self._store[key] = pruned
        return pruned

    async def __call__(
        self,
        request: Request,
        current_user: TokenData | None = Depends(get_current_user),
    ) -> None:
        now = time.monotonic()
        key = self._key(request, current_user)
        recent = self._prune(key, now)

        if len(recent) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={
                    "Retry-After": str(self.window_seconds),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                },
            )

        recent.append(now)
        self._store[key] = recent

        # Attach headers so downstream can inspect limits
        request.state.rate_limit_limit = self.max_requests
        request.state.rate_limit_remaining = self.max_requests - len(recent)


# ---------------------------------------------------------------------------
# Optional: organisation-scoped dependency
# ---------------------------------------------------------------------------


async def get_current_organization_id(
    current_user: CurrentUser,
) -> uuid.UUID:
    """Return the organisation ID from the token or raise 403."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )
    return current_user.organization_id


CurrentOrganizationId = Annotated[uuid.UUID, Depends(get_current_organization_id)]


# ---------------------------------------------------------------------------
# Audit context dependency
# ---------------------------------------------------------------------------


async def get_current_user_optional(
    request: Request,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> TokenData | None:
    """Extract and validate JWT, returning None if not present or invalid."""
    if authorization is None:
        return None

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    token = parts[1]

    try:
        token_data = decode_token(token)
        if token_data.token_type != TokenType.ACCESS:
            return None
        return token_data
    except Exception:
        return None


async def set_audit_context(
    request: Request,
    current_user: TokenData | None = Depends(get_current_user_optional),
) -> None:
    """Set per-request audit context with user_id and client_ip."""
    ctx = {
        "user_id": current_user.user_id if current_user else None,
        "client_ip": getattr(request.state, "client_ip", None),
    }
    audit_context.set(ctx)


# Dependency alias for router use
AuditContext = Depends(set_audit_context)
