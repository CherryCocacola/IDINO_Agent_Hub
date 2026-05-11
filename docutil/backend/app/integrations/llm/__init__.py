"""
LLM 통합 패키지.

Phase 7.3 부터 본 패키지의 모든 LLM 호출은 ``AgentHubLLMWrapper`` 를 통해 AgentHub
Gateway (``/v1/chat/completions``) 로 위임된다 — R2 단일 진입점 원칙. 기존
OpenAI/Azure/Anthropic/Gemini/vLLM/SGLang SDK 직접 호출 클라이언트는 deprecate
대상이다.

Phase 7 (2026-05-11) — R2 완전 보강:
    Anthropic SDK 를 직접 import 하던 ``ClaudeClient`` 와 OpenAI-호환 URL
    (``https://generativelanguage.googleapis.com/v1beta/openai``) 을 직접 사용하던
    ``GeminiClient`` 모듈을 dead code 로 판정하여 삭제했다. factory 가 ``provider``
    값에 관계없이 ``AgentHubLLMWrapper`` 만 반환하므로 app 코드에서 두 클래스의
    instantiate 경로는 0건이었다 (tests 만 잔존 — 별도 트랙으로 정리).

신규 코드는 다음 중 하나를 사용:
    - ``create_llm_client(provider_or_task, model=AgentCode)`` — factory 경유
    - ``AgentHubLLMWrapper(agent_code=...)`` — AgentCode 직접 지정
    - ``app.integrations.agenthub_client.get_agenthub_client()`` — raw AgentHub 호출
"""

from app.integrations.llm.azure_client import AzureOpenAIClient
from app.integrations.llm.client import (
    AgentHubLLMWrapper,
    LLMClient,
    ModelRouter,
    OpenAIClient,
    OpenAICompatibleClient,
    SGLangClient,
    VLLMClient,
)
from app.integrations.llm.factory import create_llm_client, get_provider_for_task
from app.integrations.llm.schema_adapter import (
    provider_capability_report,
    pydantic_to_claude_tool,
    pydantic_to_gemini_schema,
    pydantic_to_openai_schema,
    pydantic_to_vllm_schema,
    validate_structured_output,
)

__all__ = [
    "AgentHubLLMWrapper",
    "AzureOpenAIClient",
    "LLMClient",
    "ModelRouter",
    "OpenAIClient",
    "OpenAICompatibleClient",
    "SGLangClient",
    "VLLMClient",
    "create_llm_client",
    "get_provider_for_task",
    "provider_capability_report",
    "pydantic_to_claude_tool",
    "pydantic_to_gemini_schema",
    "pydantic_to_openai_schema",
    "pydantic_to_vllm_schema",
    "validate_structured_output",
]
