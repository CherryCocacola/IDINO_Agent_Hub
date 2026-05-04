"""Business logic for LLM API-key management."""

from __future__ import annotations

import logging
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_api_key_hex, encrypt_api_key_hex

from .models import LLMApiKey
from .schemas import ApiKeyCreate, ApiKeyVerifyResponse

logger = logging.getLogger(__name__)

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
        """
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
        """
        base_query = select(LLMApiKey).where(
            LLMApiKey.organization_id == org_id
        )

        # Total count
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await db.execute(count_query)).scalar_one()

        # Paginated items
        offset = (page - 1) * size
        items_query = (
            base_query
            .order_by(LLMApiKey.ins_dt.desc())
            .offset(offset)
            .limit(size)
        )
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
        """Delete an API key by ID. Raises 404 if not found."""
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
        """
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
                    message=(
                        f"Provider returned HTTP {response.status_code}. "
                        "The API key may be invalid or expired."
                    ),
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
        """
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
