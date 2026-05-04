"""FastAPI router for LLM API-key management endpoints.

All routes in this module are mounted under the ``/api-keys`` prefix by the
application factory.  The router itself uses ``prefix=""`` so that the
parent mount point has full control over the final URL namespace.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_role

from .schemas import (
    ApiKeyCreate,
    ApiKeyListResponse,
    ApiKeyResponse,
    ApiKeyVerifyResponse,
)
from .service import ApiKeyService

router = APIRouter(prefix="", tags=["api-keys"])


# ---------------------------------------------------------------------------
# GET /api-keys
# ---------------------------------------------------------------------------


@router.get(
    "/api-keys",
    response_model=ApiKeyListResponse,
    summary="List API keys",
    description="Return a paginated list of stored LLM API keys (masked).",
)
async def list_api_keys(
    page: int = Query(1, ge=1, description="Page number."),
    size: int = Query(20, ge=1, le=100, description="Items per page."),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["super_admin", "admin", "org_admin"])),
) -> ApiKeyListResponse:
    """List all API keys for the current organisation."""
    items, total = await ApiKeyService.get_api_keys(
        db, org_id=current_user.organization_id, page=page, size=size
    )
    return ApiKeyListResponse(
        items=[ApiKeyResponse.model_validate(k) for k in items],
        total=total,
        page=page,
        size=size,
    )


# ---------------------------------------------------------------------------
# POST /api-keys
# ---------------------------------------------------------------------------


@router.post(
    "/api-keys",
    response_model=ApiKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new API key",
    description="Encrypt and store a new LLM provider API key.",
)
async def create_api_key(
    data: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["super_admin", "admin", "org_admin"])),
) -> ApiKeyResponse:
    """Create a new API key entry."""
    api_key = await ApiKeyService.create_api_key(
        db,
        org_id=current_user.organization_id,
        user_id=current_user.user_id,
        data=data,
    )
    return ApiKeyResponse.model_validate(api_key)


# ---------------------------------------------------------------------------
# DELETE /api-keys/{id}
# ---------------------------------------------------------------------------


@router.delete(
    "/api-keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete an API key",
    description="Permanently remove an API key from the system.",
)
async def delete_api_key(
    key_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["super_admin", "admin", "org_admin"])),
) -> None:
    """Delete a stored API key."""
    await ApiKeyService.delete_api_key(
        db, key_id=key_id, org_id=current_user.organization_id
    )


# ---------------------------------------------------------------------------
# POST /api-keys/{id}/verify
# ---------------------------------------------------------------------------


@router.post(
    "/api-keys/{key_id}/verify",
    response_model=ApiKeyVerifyResponse,
    summary="Verify an API key",
    description=(
        "Decrypt the stored key and test the connection to the LLM provider."
    ),
)
async def verify_api_key(
    key_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["super_admin", "admin", "org_admin"])),
) -> ApiKeyVerifyResponse:
    """Verify that a stored API key is valid."""
    return await ApiKeyService.verify_api_key(
        db, key_id=key_id, org_id=current_user.organization_id
    )
