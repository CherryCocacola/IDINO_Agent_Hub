"""트랙 #88-7 — Settings 라우터.

엔드포인트:
- GET  /settings            — 전체 (general/security/storage) 반환
- PUT  /settings/general    — general 저장 (현재 stub, 영구화는 다음 트랙)
- PUT  /settings/security   — security 저장 (stub)
- PUT  /settings/storage    — storage 저장 (stub)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.core.dependencies import require_role
from app.modules.settings.schemas import (
    GeneralSettings,
    SecuritySettings,
    SettingsData,
    StorageSettings,
)
from app.modules.settings.service import SettingsService

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get(
    "",
    response_model=SettingsData,
    summary="시스템 설정 전체 조회",
)
async def get_settings(
    _current_user=Depends(require_role(["admin", "super_admin"])),
) -> SettingsData:
    """운영자 콘솔 /settings 페이지의 초기 데이터."""
    return await SettingsService.get_all()


@router.put(
    "/general",
    status_code=status.HTTP_200_OK,
    summary="일반 설정 저장 (stub)",
)
async def update_general(
    payload: GeneralSettings,
    _current_user=Depends(require_role(["admin", "super_admin"])),
) -> dict:
    """현재는 stub — 영구 저장은 다음 트랙."""
    return {"status": "ok", "saved": payload.model_dump()}


@router.put(
    "/security",
    status_code=status.HTTP_200_OK,
    summary="보안 설정 저장 (stub)",
)
async def update_security(
    payload: SecuritySettings,
    _current_user=Depends(require_role(["admin", "super_admin"])),
) -> dict:
    return {"status": "ok", "saved": payload.model_dump()}


@router.put(
    "/storage",
    status_code=status.HTTP_200_OK,
    summary="스토리지 설정 저장 (stub)",
)
async def update_storage(
    payload: StorageSettings,
    _current_user=Depends(require_role(["admin", "super_admin"])),
) -> dict:
    return {"status": "ok", "saved": payload.model_dump()}
