"""FastAPI router for LLM API-key management endpoints.

DEPRECATED — Phase 7 R2 이후 신규 사용 금지 (트랙 #69, 2026-05-12).

All routes in this module are mounted under the ``/api-keys`` prefix by the
application factory.  The router itself uses ``prefix=""`` so that the
parent mount point has full control over the final URL namespace.

본 라우터의 모든 endpoint 는 응답 헤더 ``Deprecation: true`` 와
``Link: <AgentHub /admin/api-keys>; rel="successor-version"`` 을 포함하여
표준 deprecation 신호 (RFC 8594 + Deprecation HTTP Header draft) 를 발신한다.

운영자 키 발급/검증/회전은 AgentHub 운영자 콘솔(`/admin/api-keys`)로 이전.
본 라우터는 운영 데이터 보존을 위해 유지된다.

참조:
- ``user_mig/TECHSPEC.md`` §16 (Phase 7.3 단일 진입점 정책)
- 트랙 #69 분석 (progress.md)
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
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

router = APIRouter(prefix="", tags=["api-keys (deprecated)"])

# 트랙 #69: deprecation 표준 헤더 (RFC 8594 / IETF draft-ietf-httpapi-deprecation-header)
# 주의: HTTP 헤더 값은 ISO-8859-1 (latin-1) 으로 제한되므로 ASCII 문자만 사용한다.
# 한국어 안내는 응답 body 의 description 필드와 프론트엔드 WarningBanner 에서 처리.
_DEPRECATION_HEADERS: dict[str, str] = {
    "Deprecation": "true",
    "Link": '<https://agenthub.idino.local/admin/api-keys>; rel="successor-version"',
    "X-Deprecation-Track": "track-69-phase-7-r2",
    "X-Deprecation-Reason": (
        "DocUtil LLM calls are delegated to AgentHub single entry point "
        "since Phase 7.3+. Use AgentHub admin console for key management."
    ),
}


def _apply_deprecation_headers(response: Response) -> None:
    """모든 api-keys endpoint 응답에 deprecation 표준 헤더 부착.

    HTTP 클라이언트가 deprecation 신호를 감지하고 자동으로
    successor-version 으로 이전할 수 있도록 한다.
    """
    for key, value in _DEPRECATION_HEADERS.items():
        response.headers[key] = value


# ---------------------------------------------------------------------------
# GET /api-keys
# ---------------------------------------------------------------------------


@router.get(
    "/api-keys",
    response_model=ApiKeyListResponse,
    summary="[DEPRECATED] List API keys",
    description=(
        "**DEPRECATED — Phase 7 R2 (트랙 #69)**\n\n"
        "운영자 키 관리는 AgentHub 운영자 콘솔(`/admin/api-keys`)로 이전. "
        "본 endpoint 는 운영 데이터 보존 목적으로만 유지되며 신규 적재 대상이 아닙니다.\n\n"
        '응답 헤더 `Deprecation: true` + `Link: <...>; rel="successor-version"` 발신.'
    ),
)
async def list_api_keys(
    response: Response,
    page: int = Query(1, ge=1, description="Page number."),
    size: int = Query(20, ge=1, le=100, description="Items per page."),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["super_admin", "admin", "org_admin"])),
) -> ApiKeyListResponse:
    """List all API keys for the current organisation.

    .. deprecated:: Phase 7 R2 (트랙 #69)
    """
    _apply_deprecation_headers(response)
    items, total = await ApiKeyService.get_api_keys(db, org_id=current_user.organization_id, page=page, size=size)
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
    summary="[DEPRECATED] Register a new API key",
    description=(
        "**DEPRECATED — Phase 7 R2 (트랙 #69)**\n\n"
        "신규 키 등록은 AgentHub 운영자 콘솔(`/admin/api-keys`)에서 수행하세요. "
        "본 endpoint 는 호환성 유지 목적으로만 존재합니다."
    ),
)
async def create_api_key(
    data: ApiKeyCreate,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["super_admin", "admin", "org_admin"])),
) -> ApiKeyResponse:
    """Create a new API key entry.

    .. deprecated:: Phase 7 R2 (트랙 #69)
    """
    _apply_deprecation_headers(response)
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
    summary="[DEPRECATED] Delete an API key",
    description=(
        "**DEPRECATED — Phase 7 R2 (트랙 #69)**\n\n"
        "운영 정리 목적의 삭제만 허용. 신규 키 관리는 AgentHub 운영자 콘솔로 이전."
    ),
)
async def delete_api_key(
    key_id: UUID,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["super_admin", "admin", "org_admin"])),
) -> None:
    """Delete a stored API key.

    .. deprecated:: Phase 7 R2 (트랙 #69)
    """
    _apply_deprecation_headers(response)
    await ApiKeyService.delete_api_key(db, key_id=key_id, org_id=current_user.organization_id)


# ---------------------------------------------------------------------------
# POST /api-keys/{id}/verify
# ---------------------------------------------------------------------------


@router.post(
    "/api-keys/{key_id}/verify",
    response_model=ApiKeyVerifyResponse,
    summary="[DEPRECATED] Verify an API key",
    description=(
        "**DEPRECATED — Phase 7 R2 (트랙 #69)**\n\n"
        "Decrypt the stored key and test the connection to the LLM provider. "
        "신규 키 검증은 AgentHub 운영자 콘솔로 이전."
    ),
)
async def verify_api_key(
    key_id: UUID,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["super_admin", "admin", "org_admin"])),
) -> ApiKeyVerifyResponse:
    """Verify that a stored API key is valid.

    .. deprecated:: Phase 7 R2 (트랙 #69)
    """
    _apply_deprecation_headers(response)
    return await ApiKeyService.verify_api_key(db, key_id=key_id, org_id=current_user.organization_id)
