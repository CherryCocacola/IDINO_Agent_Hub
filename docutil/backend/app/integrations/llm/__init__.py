"""
LLM 통합 패키지.

OpenAI-호환 및 비호환 LLM 백엔드에 대한 통합 클라이언트 인터페이스,
RAG 워크플로우용 프롬프트 템플릿, A/B 테스트 라우팅을 제공한다.
"""

from app.integrations.llm.azure_client import AzureOpenAIClient
from app.integrations.llm.claude_client import ClaudeClient
from app.integrations.llm.client import (
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
