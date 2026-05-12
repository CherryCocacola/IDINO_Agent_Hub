"""Business logic for LLM API-key management.

DEPRECATED — Phase 7 R2 이후 신규 사용 금지 (트랙 #69, 2026-05-12).

DocUtil 의 모든 LLM 호출은 AgentHub `/v1/chat/completions` 단일 진입점으로
위임되므로, 본 서비스의 CRUD/verify 기능은 신규 적재 대상이 아니다.
운영자 키 발급/회전은 AgentHub 운영자 콘솔(`/admin/api-keys`)로 일원화.

본 모듈은 데이터 보존 + legacy fallback (`app/core/llm_keys.py`) 호환을
위해 코드만 유지된다. 신규 호출은 ``DeprecationWarning`` 발생.

참조:
- ``user_mig/TECHSPEC.md`` §16 (Phase 7.3 단일 진입점 정책)
- 트랙 #69 분석 (progress.md)
"""

from __future__ import annotations

import logging
import warnings
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_api_key_hex, encrypt_api_key_hex

from .models import LLMApiKey
from .schemas import ApiKeyCreate, ApiKeyVerifyResponse

logger = logging.getLogger(__name__)

# 트랙 #69: deprecate 경고 메시지 (Phase 7 R2 정책)
_DEPRECATION_MESSAGE = (
    "DocUtil tb_llm_api_keys 모듈은 Phase 7 R2 이후 deprecate 되었습니다. "
    "운영자 키 관리는 AgentHub 운영자 콘솔(/admin/api-keys)로 이전하세요. "
    "본 endpoint 는 데이터 보존을 위해 유지되지만 신규 적재 대상이 아닙니다."
)


def _emit_deprecation_warning(operation: str) -> None:
    """trace-friendly deprecate 신호: logger + DeprecationWarning.

    운영 로그에 1회 기록되고 pytest -W error 환경에서 fail-loud 동작.
    트랙 #69 / Phase 7 R2 단일 진입점 정책 강제용.
    """
    logger.warning(
        "[DEPRECATED tb_llm_api_keys] %s — %s",
        operation,
        _DEPRECATION_MESSAGE,
    )
    warnings.warn(
        f"[tb_llm_api_keys.{operation}] {_DEPRECATION_MESSAGE}",
        DeprecationWarning,
        stacklevel=3,
    )


# ---------------------------------------------------------------------------
# Provider verification endpoints
# ---------------------------------------------------------------------------
_PROVIDER_VERIFY_URLS: dict[str, str] = {
    "openai": "https://api.openai.com/v1/models",
    "anthropic": "https://api.anthropic.com/v1/messages",
    "google": "https://generativelanguage.googleapis.com/v1/models",
}


class ApiKeyService:
    """Stateless service methods for LLM API-key CRUD and verification."""

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    @staticmethod
    async def create_api_key(
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID,
        data: ApiKeyCreate,
    ) -> LLMApiKey:
        """Encrypt and store a new LLM API key.

        The raw key is encrypted with AES-256-GCM and only a masked prefix
        is stored in plain text for display purposes.

        .. deprecated:: Phase 7 R2 (트랙 #69)
            신규 키 등록은 AgentHub 운영자 콘솔에서 수행하세요.
        """
        _emit_deprecation_warning("create_api_key")
        encrypted = encrypt_api_key_hex(data.api_key)

        # Build a masked prefix: show first 8 characters then mask the rest
        raw = data.api_key
        if len(raw) > 8:
            prefix = raw[:8] + "****"
        else:
            prefix = raw[:4] + "****"

        api_key = LLMApiKey(
            organization_id=org_id,
            llm_name=data.llm_name,
            api_key_encrypted=bytes.fromhex(encrypted),
            api_key_prefix=prefix,
            is_verified=False,
            registered_by=str(user_id),
        )
        db.add(api_key)
        await db.flush()
        await db.refresh(api_key)
        return api_key

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    @staticmethod
    async def get_api_keys(
        db: AsyncSession,
        org_id: UUID,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[LLMApiKey], int]:
        """Return a paginated list of API keys for an organisation.

        The encrypted key is **never** included in the response; only the
        masked ``api_key_prefix`` is visible.

        .. deprecated:: Phase 7 R2 (트랙 #69)
            조회는 운영 데이터 보존 목적으로만 유지됩니다.
        """
        _emit_deprecation_warning("get_api_keys")
        base_query = select(LLMApiKey).where(LLMApiKey.organization_id == org_id)

        # Total count
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await db.execute(count_query)).scalar_one()

        # Paginated items
        offset = (page - 1) * size
        items_query = base_query.order_by(LLMApiKey.ins_dt.desc()).offset(offset).limit(size)
        result = await db.execute(items_query)
        items = list(result.scalars().all())

        return items, total

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    @staticmethod
    async def delete_api_key(
        db: AsyncSession,
        key_id: UUID,
        org_id: UUID,
    ) -> None:
        """Delete an API key by ID. Raises 404 if not found.

        .. deprecated:: Phase 7 R2 (트랙 #69)
            삭제는 운영 정리 목적으로만 유지됩니다.
        """
        _emit_deprecation_warning("delete_api_key")
        result = await db.execute(
            select(LLMApiKey).where(
                LLMApiKey.id == key_id,
                LLMApiKey.organization_id == org_id,
            )
        )
        api_key = result.scalar_one_or_none()
        if api_key is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key '{key_id}' not found.",
            )
        await db.delete(api_key)
        await db.flush()

    # ------------------------------------------------------------------
    # Verify
    # ------------------------------------------------------------------

    @staticmethod
    async def verify_api_key(
        db: AsyncSession,
        key_id: UUID,
        org_id: UUID,
    ) -> ApiKeyVerifyResponse:
        """Decrypt the stored key and attempt a test call to the LLM provider.

        Updates the ``is_verified`` flag on the stored record accordingly.

        .. deprecated:: Phase 7 R2 (트랙 #69)
            검증은 운영 데이터 보존 목적으로만 유지됩니다.
            신규 키 검증은 AgentHub 운영자 콘솔에서 수행하세요.
        """
        _emit_deprecation_warning("verify_api_key")
        result = await db.execute(
            select(LLMApiKey).where(
                LLMApiKey.id == key_id,
                LLMApiKey.organization_id == org_id,
            )
        )
        api_key = result.scalar_one_or_none()
        if api_key is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key '{key_id}' not found.",
            )

        # Decrypt
        try:
            decrypted = decrypt_api_key_hex(api_key.api_key_encrypted.hex())
        except Exception:
            api_key.is_verified = False
            await db.flush()
            return ApiKeyVerifyResponse(
                is_valid=False,
                message="Failed to decrypt the stored API key.",
            )

        # Attempt verification against known provider
        provider = api_key.llm_name.lower()
        verify_url = _PROVIDER_VERIFY_URLS.get(provider)

        if verify_url is None:
            # Unknown provider -- mark as verified on successful decrypt only
            api_key.is_verified = True
            await db.flush()
            return ApiKeyVerifyResponse(
                is_valid=True,
                message=(
                    f"Provider '{api_key.llm_name}' is not directly testable. "
                    "Key decrypted successfully and marked as verified."
                ),
            )

        # Build provider-appropriate headers
        headers: dict[str, str] = {}
        if provider == "openai":
            headers["Authorization"] = f"Bearer {decrypted}"
        elif provider == "anthropic":
            headers["x-api-key"] = decrypted
            headers["anthropic-version"] = "2023-06-01"
        elif provider == "google":
            verify_url = f"{verify_url}?key={decrypted}"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(verify_url, headers=headers)

            if response.status_code in (200, 201):
                api_key.is_verified = True
                await db.flush()
                return ApiKeyVerifyResponse(
                    is_valid=True,
                    message=f"API key for '{api_key.llm_name}' is valid.",
                )
            else:
                api_key.is_verified = False
                await db.flush()
                return ApiKeyVerifyResponse(
                    is_valid=False,
                    message=(f"Provider returned HTTP {response.status_code}. The API key may be invalid or expired."),
                )
        except httpx.HTTPError as exc:
            logger.warning("API key verification failed for %s: %s", key_id, exc)
            api_key.is_verified = False
            await db.flush()
            return ApiKeyVerifyResponse(
                is_valid=False,
                message=f"Connection error during verification: {exc}",
            )

    # ------------------------------------------------------------------
    # Internal: decrypt key for runtime LLM calls
    # ------------------------------------------------------------------

    @staticmethod
    async def _get_decrypted_key(
        db: AsyncSession,
        key_id: UUID,
        org_id: UUID,
    ) -> str:
        """Return the decrypted API key for internal LLM call usage.

        This method is intended for internal service-to-service calls only
        and should **never** be exposed via an HTTP endpoint.

        .. deprecated:: Phase 7 R2 (트랙 #69)
            DocUtil 의 LLM 호출은 AgentHub 위임이 표준이므로 본 메서드는
            legacy fallback (``app/core/llm_keys.py``) 에서만 참조됩니다.
            ``report_generator.py`` 의 잔여 호출은 별도 트랙에서 정리.
        """
        _emit_deprecation_warning("_get_decrypted_key")
        result = await db.execute(
            select(LLMApiKey).where(
                LLMApiKey.id == key_id,
                LLMApiKey.organization_id == org_id,
            )
        )
        api_key = result.scalar_one_or_none()
        if api_key is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key '{key_id}' not found.",
            )
        return decrypt_api_key_hex(api_key.api_key_encrypted.hex())
