"""
LLM 통합 패키지.

Phase 7.3 부터 본 패키지의 모든 LLM 호출은 ``AgentHubLLMWrapper`` 를 통해 AgentHub
Gateway (``/v1/chat/completions``) 로 위임된다 — R2 단일 진입점 원칙. 기존
OpenAI/Azure/Gemini/Anthropic/vLLM/SGLang SDK 직접 호출 클라이언트는 deprecate
대상이며, 호환성을 위해 export 만 유지된다 (Phase 8+ 에서 제거 예정).

신규 코드는 다음 중 하나를 사용:
    - ``create_llm_client(provider_or_task, model=AgentCode)`` — factory 경유
    - ``AgentHubLLMWrapper(agent_code=...)`` — AgentCode 직접 지정
    - ``app.integrations.agenthub_client.get_agenthub_client()`` — raw AgentHub 호출
"""

from app.integrations.llm.azure_client import AzureOpenAIClient
from app.integrations.llm.claude_client import ClaudeClient
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
from app.integrations.llm.gemini_client import GeminiClient
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
    "ClaudeClient",
    "GeminiClient",
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
