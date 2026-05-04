"""
LLM 클라이언트 팩토리 모듈.

프로바이더 이름 문자열로부터 적절한 LLMClient 인스턴스를 생성하는 중앙 팩토리.
모든 LLM 호출 지점에서 이 팩토리를 통해 클라이언트를 얻어야 한다.

사용법::

    from app.integrations.llm.factory import create_llm_client, get_provider_for_task

    # 기본 프로바이더로 클라이언트 생성
    client = create_llm_client("openai", api_key="sk-...")

    # 기능별 프로바이더 자동 해석
    provider = get_provider_for_task("chat")   # chat_llm_provider 또는 llm_provider
    client = create_llm_client(provider)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.core.config import get_settings

if TYPE_CHECKING:
    from app.integrations.llm.client import LLMClient

logger = logging.getLogger(__name__)


def create_llm_client(
    provider: str,
    api_key: str | None = None,
    model: str | None = None,
) -> LLMClient:
    """프로바이더 이름으로 적절한 LLMClient 인스턴스를 생성한다.

    Parameters
    ----------
    provider:
        프로바이더 이름. "openai", "azure_openai", "gemini", "anthropic",
        "vllm", "sglang" 중 하나.
    api_key:
        API 키. None이면 각 클라이언트가 settings에서 자동으로 가져온다.
    model:
        모델 이름. None이면 각 클라이언트의 기본값을 사용한다.

    Returns
    -------
    LLMClient
        생성된 클라이언트 인스턴스.

    Raises
    ------
    ValueError
        알 수 없는 프로바이더 이름일 때.
    """
    get_settings()

    match provider:
        case "openai":
            from app.integrations.llm.client import OpenAIClient

            return OpenAIClient(api_key=api_key, model=model)

        case "azure_openai":
            from app.integrations.llm.azure_client import AzureOpenAIClient

            return AzureOpenAIClient(api_key=api_key)

        case "gemini":
            from app.integrations.llm.gemini_client import GeminiClient

            return GeminiClient(api_key=api_key, model=model)

        case "anthropic":
            from app.integrations.llm.claude_client import ClaudeClient

            return ClaudeClient(api_key=api_key, model=model)

        case "vllm":
            from app.integrations.llm.client import VLLMClient

            return VLLMClient(api_key=api_key, model=model)

        case "sglang":
            from app.integrations.llm.client import SGLangClient

            return SGLangClient(model=model, api_key=api_key or "EMPTY")

        case _:
            raise ValueError(
                f"알 수 없는 LLM 프로바이더: '{provider}'. 지원: openai, azure_openai, gemini, anthropic, vllm, sglang"
            )


def get_provider_for_task(task_type: str) -> str:
    """기능(태스크) 유형에 맞는 프로바이더 이름을 반환한다.

    config.py의 기능별 오버라이드 설정을 확인하고,
    설정되지 않았으면 기본 llm_provider를 반환한다.

    Parameters
    ----------
    task_type:
        기능 유형. "chat", "report", "template" 등.

    Returns
    -------
    str
        프로바이더 이름 (예: "openai", "anthropic" 등).
    """
    settings = get_settings()

    # 기능별 오버라이드 매핑
    overrides: dict[str, str | None] = {
        "chat": settings.chat_llm_provider,
        "chatbot": settings.chat_llm_provider,
        "report": settings.report_llm_provider,
        "template": settings.template_llm_provider,
    }

    override = overrides.get(task_type)
    if override:
        return override

    # 오버라이드 없으면 기본 프로바이더 사용
    return settings.llm_provider
