"""FastAPI router for user management endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.core.security import TokenData
from app.modules.audit.service import AuditService

from .schemas import UserCreate, UserListResponse, UserResponse, UserUpdate
from .service import UserService

router = APIRouter(prefix="", tags=["users"])


# ---------------------------------------------------------------------------
# 트랙 A1 Phase C (2026-05-26): DocUtil 사용자 mutation 차단
# ---------------------------------------------------------------------------
# 운영자 콘솔이 AgentHub `/admin/docutil-users` 로 단일화됨 (Phase A~E).
# 본 router 의 POST/PUT/DELETE 는 410 Gone 으로 응답하여 외부에서 직접 호출
# 시에도 AgentHub 콘솔로 안내한다. 일반 사용자 화면(/profile 등)에서 호출
# 하는 GET 은 영향 없음.
#
# 참고: 트랙 #98 phase 3 이후 tb_users 가 VIEW + INSTEAD OF TRIGGER 로
# AgentHub.Users 에 자동 위임되므로, 운영자가 본 endpoint 우회로 호출해도
# 데이터는 AgentHub 마스터로 가지만 UX 일관성을 위해 명시 차단.

_GONE_DETAIL_KO = (
    "DocUtil 사용자/부서 mutation 은 AgentHub 운영자 콘솔로 통합되었습니다. "
    "AgentHub `/admin/docutil-users` 또는 `/admin/docutil-departments` 를 사용해 주세요."
)


def _raise_gone() -> None:
    raise HTTPException(status_code=status.HTTP_410_GONE, detail=_GONE_DETAIL_KO)


# ---------------------------------------------------------------------------
# Small helper schema for the status-update endpoint
# ---------------------------------------------------------------------------

class _StatusBody(BaseModel):
    status: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=UserListResponse,
    summary="List users",
)
@router.get(
    "/",
    response_model=UserListResponse,
    summary="List users (trailing slash alias — 트랙 #88-7)",
    include_in_schema=False,
)
async def list_users(
    org_id: UUID = Query(..., description="Organisation to list users for"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    role: str | None = Query(None, description="Filter by role"),
    user_status: str | None = Query(None, alias="status", description="Filter by status"),
    search: str | None = Query(None, description="username/email LIKE 검색"),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role(["admin", "super_admin"])),
):
    """Return a paginated, filterable list of users for a given organisation.

    ``search`` 파라미터는 username/email 에 대한 ILIKE 부분 일치 검색을 수행한다.
    """
    users, total = await UserService.get_users(
        db,
        org_id=org_id,
        page=page,
        size=size,
        role_filter=role,
        status_filter=user_status,
        search_filter=search,
    )
    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        size=size,
    )


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user",
)
@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user (trailing slash alias — 트랙 #88-7)",
    include_in_schema=False,
)
async def create_user(
    user_data: UserCreate,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    _current_user: TokenData = Depends(require_role(["admin", "super_admin"])),
):
    """[Deprecated 트랙 A1 Phase C] AgentHub 운영자 콘솔로 이전."""
    _raise_gone()
    user = await UserService.create_user(db, user_data)

    # 감사 로그: 사용자 생성 성공 기록
    try:
        await AuditService.create_log(
            db=db,
            org_id=user.organization_id,
            user_id=_current_user.user_id,
            action="user.create",
            resource_type="user",
            resource_id=str(user.id),
            details={"username": user.username, "role": user.role if isinstance(user.role, str) else user.role.value},
            ip_address=request.client.host if request and request.client else None,
        )
    except Exception:
        pass  # 감사 로그 실패가 주 흐름을 막지 않도록 함

    return UserResponse.model_validate(user)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get a user",
)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role(["admin", "super_admin"])),
):
    """Retrieve a single user by ID."""
    user = await UserService.get_user(db, user_id)
    return UserResponse.model_validate(user)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update a user",
)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role(["admin", "super_admin"])),
):
    """[Deprecated 트랙 A1 Phase C] AgentHub 운영자 콘솔로 이전."""
    _raise_gone()
    user = await UserService.update_user(db, user_id, user_data)
    return UserResponse.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete a user",
)
async def delete_user(
    user_id: UUID,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    _current_user: TokenData = Depends(require_role(["admin", "super_admin"])),
):
    """[Deprecated 트랙 A1 Phase C] AgentHub 운영자 콘솔로 이전."""
    _raise_gone()
    await UserService.delete_user(db, user_id)

    # 감사 로그: 사용자 삭제 성공 기록
    try:
        await AuditService.create_log(
            db=db,
            org_id=_current_user.organization_id,
            user_id=_current_user.user_id,
            action="user.delete",
            resource_type="user",
            resource_id=str(user_id),
            ip_address=request.client.host if request and request.client else None,
        )
    except Exception:
        pass  # 감사 로그 실패가 주 흐름을 막지 않도록 함


@router.put(
    "/{user_id}/status",
    response_model=UserResponse,
    summary="Toggle user status",
)
async def update_user_status(
    user_id: UUID,
    body: _StatusBody,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    _current_user: TokenData = Depends(require_role(["admin", "super_admin"])),
):
    """[Deprecated 트랙 A1 Phase C] AgentHub 운영자 콘솔로 이전."""
    _raise_gone()
    user = await UserService.update_status(db, user_id, body.status)

    # 감사 로그: 사용자 상태 변경 성공 기록
    try:
        await AuditService.create_log(
            db=db,
            org_id=_current_user.organization_id,
            user_id=_current_user.user_id,
            action="user.status_change",
            resource_type="user",
            resource_id=str(user_id),
            details={"new_status": body.status},
            ip_address=request.client.host if request and request.client else None,
        )
    except Exception:
        pass  # 감사 로그 실패가 주 흐름을 막지 않도록 함

    return UserResponse.model_validate(user)
