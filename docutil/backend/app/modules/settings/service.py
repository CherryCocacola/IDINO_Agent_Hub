"""트랙 #88-7 — Settings 서비스.

현 시점은 기본값 + MinIO/스토리지 라이브 정보만 반환. 영구 저장은 다음 트랙.
"""
from __future__ import annotations

from app.core.config import get_settings
from app.modules.settings.schemas import (
    GeneralSettings,
    SecuritySettings,
    SettingsData,
    StorageSettings,
)


class SettingsService:
    """운영자 콘솔 /settings 페이지 데이터 제공."""

    @staticmethod
    async def get_all() -> SettingsData:
        cfg = get_settings()

        general = GeneralSettings(
            default_language=getattr(cfg, "default_language", "ko"),
            maintenance_mode=getattr(cfg, "maintenance_mode", False),
        )

        security = SecuritySettings(
            password_min_length=getattr(cfg, "password_min_length", 8),
            password_require_uppercase=getattr(cfg, "password_require_uppercase", True),
            password_require_number=getattr(cfg, "password_require_number", True),
            password_require_special=getattr(cfg, "password_require_special", True),
            session_timeout_minutes=int(getattr(cfg, "jwt_access_token_expire_minutes", 30)),
        )

        storage = StorageSettings(
            minio_connected=bool(getattr(cfg, "minio_endpoint", "")),
            minio_endpoint=getattr(cfg, "minio_endpoint", "") or "",
            total_storage_bytes=0,
            used_storage_bytes=0,
        )

        return SettingsData(general=general, security=security, storage=storage)
