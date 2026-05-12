"""트랙 #88-7 — Settings 모듈 schemas.

운영자 콘솔 /settings 페이지에 필요한 3개 영역 (general/security/storage) 정의.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class GeneralSettings(BaseModel):
    default_language: str = Field("ko", description="기본 언어 코드")
    maintenance_mode: bool = Field(False, description="시스템 점검 모드")


class SecuritySettings(BaseModel):
    password_min_length: int = Field(8, ge=4, le=128)
    password_require_uppercase: bool = True
    password_require_number: bool = True
    password_require_special: bool = True
    session_timeout_minutes: int = Field(30, ge=5, le=1440)


class StorageSettings(BaseModel):
    minio_connected: bool = False
    minio_endpoint: str = ""
    total_storage_bytes: int = 0
    used_storage_bytes: int = 0


class SettingsData(BaseModel):
    general: GeneralSettings
    security: SecuritySettings
    storage: StorageSettings
