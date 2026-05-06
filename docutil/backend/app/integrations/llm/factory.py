"""
LLM 클라이언트 팩토리 모듈 (Phase 7.3 — R2 단일 진입점).

Phase 7.3 부터 본 팩토리는 더 이상 OpenAI/Azure/Gemini/Anthropic/vLLM/SGLang SDK 의
직접 호출 클라이언트를 반환하지 않는다. 대신 ``AgentHubLLMWrapper`` 를 반환하며,
모든 LLM 호출은 AgentHub 의 OpenAI 호환 엔드포인트(``/v1/chat/completions``)로
위임된다 — 외부 시그니처는 보존되므로 호출처 코드 변경은 불필요.

마이그레이션 매핑 (provider 문자열 → AgentCode):
    "openai" / "azure_openai" / "vllm" / "sglang"  → 호출 task 에 따라 결정
    "anthropic"                                    → 호출 task 에 따라 결정
    "gemini"                                       → 호출 task 에 따라 결정

호출 task 별 기본 AgentCode:
    "chat" / "chatbot"                             → "docutil-rag-chat"
    "report"                                       → "docutil-report-generator"
    "evaluation"                                   → "docutil-evaluator"
    "agentic_search"                               → "agentic-search"
    "template"                                     → "docutil-rag-chat" (S7 폐기 예정)

호출처가 명시적 AgentCode 가 필요하면 ``model`` 파라미터에 AgentCode 를 전달한다
(예: ``create_llm_client("openai", model="docutil-evaluator")``).

사용법::

    from app.integrations.llm.factory import create_llm_client, get_provider_for_task

    # 기존 호출 패턴 — 호출처 변경 불필요
    provider = get_provider_for_task("chat")   # "openai" 등
    client = create_llm_client(provider)        # AgentHubLLMWrapper 반환

    # 호출
    text = await client.generate(messages=[...], temperature=0.5)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.core.config import get_settings

if TYPE_CHECKING:
    from app.integrations.llm.client import LLMClient

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# AgentCode 매핑 정책 (Phase 7.1 시드 기반)
# ----------------------------------------------------------------------
#
# 호출 task 별 기본 AgentCode. AI_INVENTORY.md §6 카탈로그와 1:1 매핑.
# 호출처가 ``model`` 인자에 AgentCode 를 직접 전달하면 본 매핑을 우회한다.

_DEFAULT_AGENT_CODE = "docutil-rag-chat"

_TASK_TO_AGENT_CODE: dict[str, str] = {
    # 채팅/RAG — 사용자 챗봇 메인 흐름
    "chat": "docutil-rag-chat",
    "chatbot": "docutil-rag-chat",
    # 보고서/문서 생성 — Structured Outputs 기반
    "report": "docutil-report-generator",
    # 평가/judge — RAGAS daily-evaluation Celery beat
    "evaluation": "docutil-evaluator",
    # Agentic Search — 쿼리 분석 + 결과 품질 판정
    "agentic_search": "agentic-search",
    "agentic_query_analysis": "agentic-search",
    "agentic_quality_judgment": "agentic-search",
    # 템플릿 (S7 에서 폐기 예정 — 임시 매핑)
    "template": "docutil-rag-chat",
    # 학습 데이터 생성 (data_generator) — judge 도 동일 Agent 로 위임
    "training_qa": "docutil-evaluator",
    "training_judge": "docutil-evaluator",
}


def _resolve_agent_code(provider: str | None, model: str | None) -> str:
    """provider/model 인자로부터 최종 AgentCode 를 결정한다.

    우선순위:
        1. ``model`` 이 AgentCode 형태(``docutil-*`` / ``agentic-*`` / ``career-*``
           / ``embedding-*``)이면 그대로 사용 — 호출처가 명시적으로 AgentCode 를
           지정한 경우.
        2. ``provider`` 가 task 키(``chat``/``report`` 등)면 매핑 테이블 사용.
        3. 그 외(``openai`` / ``anthropic`` 등 레거시 provider) → 기본값
           ``docutil-rag-chat``.
    """
    # 1. model 이 AgentCode 형태이면 그대로 사용
    if model and isinstance(model, str):
        prefix = model.split("-", 1)[0] if "-" in model else ""
        if prefix in {"docutil", "agentic", "career", "embedding"} or model.startswith(
            ("docutil-", "agentic-", "career-", "embedding-")
        ):
            return model

    # 2. provider 가 task 키 매핑에 있으면 사용
    if provider and provider in _TASK_TO_AGENT_CODE:
        return _TASK_TO_AGENT_CODE[provider]

    # 3. 레거시 provider (openai/anthropic/gemini/azure_openai/vllm/sglang)
    #    → 기본 chat Agent. 호출처가 더 구체적인 매핑을 원하면 model 에 AgentCode 명시.
    if provider in {"openai", "azure_openai", "anthropic", "gemini", "vllm", "sglang"}:
        logger.debug(
            "Phase 7.3: legacy provider '%s' → default AgentCode '%s' (호출처가 model 인자로 AgentCode 명시 가능)",
            provider,
            _DEFAULT_AGENT_CODE,
        )
        return _DEFAULT_AGENT_CODE

    return _DEFAULT_AGENT_CODE


def create_llm_client(
    provider: str,
    api_key: str | None = None,
    model: str | None = None,
) -> LLMClient:
    """프로바이더 이름(또는 task 키)으로 ``AgentHubLLMWrapper`` 를 생성한다.

    Phase 7.3 부터 본 함수는 항상 ``AgentHubLLMWrapper`` 를 반환한다 — 외부 LLM SDK
    직접 호출 경로는 모두 폐기되었다. 외부 시그니처는 기존 OpenAIClient/VLLMClient
    등과 호환되므로, 호출처(documents_v2/templates/workers/* 등)는 코드 변경
    불필요.

    Parameters
    ----------
    provider:
        프로바이더 이름 또는 task 키. 다음 중 하나:
            - 레거시 provider: "openai", "azure_openai", "gemini", "anthropic",
              "vllm", "sglang" (모두 ``docutil-rag-chat`` 으로 매핑)
            - task 키: "chat", "chatbot", "report", "evaluation", "agentic_search",
              "template", "training_qa", "training_judge"
    api_key:
        호환용 인자. AgentHub 인증은 환경변수 ``AGENTHUB_API_KEY`` 로 처리되므로
        본 인자는 무시된다.
    model:
        AgentCode 직접 지정용 인자 (선택). ``"docutil-*"`` / ``"agentic-*"`` 형태로
        전달하면 매핑 우회. 그 외 값은 ``LLMClient.model`` 속성에만 보존된다.

    Returns
    -------
    LLMClient (실제 타입은 ``AgentHubLLMWrapper``)
        AgentHub 위임 클라이언트.
    """
    # settings 의존성은 호출 시점에만 검증 (lazy import 와 동일 의도).
    get_settings()

    # 지연 import — 순환 참조 회피.
    from app.integrations.llm.client import AgentHubLLMWrapper

    agent_code = _resolve_agent_code(provider, model)
    return AgentHubLLMWrapper(agent_code=agent_code, api_key=api_key, model=model)


def get_provider_for_task(task_type: str) -> str:
    """기능(태스크) 유형에 맞는 프로바이더 이름을 반환한다.

    Phase 7.3 부터 본 함수의 반환값은 ``create_llm_client`` 의 AgentCode 매핑 키로
    사용된다. 기존 ``settings.chat_llm_provider`` 등의 오버라이드는 그대로 적용되며,
    매핑 결과가 ``"openai"`` / ``"anthropic"`` 등 레거시 provider 이면 ``create_llm_client``
    가 ``docutil-rag-chat`` 으로 변환한다. 호출처가 더 구체적인 Agent 를 원하면
    ``create_llm_client(provider, model="docutil-report-generator")`` 처럼 명시.

    Parameters
    ----------
    task_type:
        기능 유형. "chat", "chatbot", "report", "template", "evaluation",
        "agentic_search" 등.

    Returns
    -------
    str
        프로바이더 이름 (또는 task 키).
    """
    settings = get_settings()

    # 기능별 오버라이드 매핑 (settings 기반)
    overrides: dict[str, str | None] = {
        "chat": settings.chat_llm_provider,
        "chatbot": settings.chat_llm_provider,
        "report": settings.report_llm_provider,
        "template": settings.template_llm_provider,
    }

    override = overrides.get(task_type)
    if override:
        return override

    # 오버라이드 없으면 task_type 자체를 반환 (예: "evaluation", "agentic_search")
    # — ``create_llm_client`` 의 ``_TASK_TO_AGENT_CODE`` 매핑에서 처리됨.
    if task_type in _TASK_TO_AGENT_CODE:
        return task_type

    # 그 외(미등록 task) 는 기본 프로바이더 — 결과적으로 docutil-rag-chat 매핑.
    return settings.llm_provider
