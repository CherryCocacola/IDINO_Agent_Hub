"""
LLM API 키 해석 모듈.

DB에 저장된 검증된 키를 우선 사용하고, 없으면 환경변수(.env)로 fallback한다.

사용법::

    from app.core.llm_keys import resolve_api_key
    key = await resolve_api_key(db, org_id, "openai")
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.core.config import get_settings

if TYPE_CHECKING:
    from uuid import UUID

logger = logging.getLogger(__name__)

# 프로바이더 이름 → settings 속성명 매핑
# DB에서 키를 찾지 못했을 때 환경변수(.env)에서 가져올 속성명을 정의한다.
_PROVIDER_SETTINGS_MAP: dict[str, str] = {
    "openai": "openai_api_key",
    "anthropic": "anthropic_api_key",
    "azure": "azure_openai_api_key",
    "azure_openai": "azure_openai_api_key",
    "gemini": "google_api_key",
    "google": "google_api_key",
}


async def resolve_api_key(
    db=None,
    org_id: UUID | None = None,
    provider: str = "openai",
) -> str:
    """LLM API 키를 해석한다: DB 검증된 키 우선, .env fallback.

    Parameters
    ----------
    db:
        SQLAlchemy 비동기 세션. None이면 DB 조회를 건너뛴다.
    org_id:
        조직 UUID. None이면 DB 조회를 건너뛴다.
    provider:
        프로바이더 이름 ("openai", "anthropic", "azure_openai", "gemini" 등).

    Returns
    -------
    str
        해석된 API 키. 찾지 못하면 빈 문자열.
    """
    # 1단계: DB에서 조직별 검증된 키 조회 시도
    if db is not None and org_id is not None:
        try:
            from app.modules.api_keys.service import ApiKeyService

            key = await ApiKeyService.get_active_api_key(db, org_id, provider)
            if key:
                logger.debug("DB API 키 사용: org=%s, provider=%s", org_id, provider)
                return key
        except Exception:
            logger.debug(
                "DB API 키 조회 실패, 환경변수 fallback 사용",
                exc_info=True,
            )

    # 2단계: 환경변수(.env)에서 fallback
    settings = get_settings()
    settings_attr = _PROVIDER_SETTINGS_MAP.get(provider)

    if settings_attr:
        return getattr(settings, settings_attr, "") or ""

    # 알 수 없는 프로바이더 → OpenAI 키로 fallback
    logger.warning(
        "알 수 없는 프로바이더 '%s', openai_api_key로 fallback합니다.",
        provider,
    )
    return settings.openai_api_key or ""
