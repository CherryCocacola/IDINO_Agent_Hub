"""
LLM 클라이언트 구현 모듈.

제공하는 클래스:
  - ``LLMClient`` -- 모든 LLM 클라이언트의 추상 베이스 클래스.
  - ``AgentHubLLMWrapper`` -- **(Phase 7.3 신규)** AgentHub `/v1/chat/completions` 위임 클라이언트.
    R2 단일 진입점 원칙에 따라 본 monorepo 의 모든 DocUtil LLM 호출이 본 래퍼를 거친다.
  - ``OpenAICompatibleClient`` -- (Phase 7.3 deprecate 진행) OpenAI-호환 API 직접 호출 베이스.
  - ``OpenAIClient`` -- (Phase 7.3 deprecate) OpenAI API (GPT-4o 등) 직접 호출 클라이언트.
  - ``VLLMClient`` -- (Phase 7.3 deprecate) 자체 호스팅 vLLM (OpenAI-호환) 직접 호출 클라이언트.
  - ``SGLangClient`` -- (Phase 7.3 deprecate) SGLang (RadixAttention) 직접 호출 클라이언트.
  - ``ModelRouter`` -- 조직/태스크 기반 A/B 테스트 라우팅.

Phase 7.3 마이그레이션 노트:
    `factory.create_llm_client()` 는 본 모듈의 ``AgentHubLLMWrapper`` 를 반환하도록
    변경되었다. 외부 시그니처(``generate`` / ``generate_stream`` / ``generate_structured``
    / ``generate_with_schema`` 및 _sync 동기 변종)는 유지되며, 호출처(documents_v2,
    templates, workers/report_generator, workers/jinja2_engine, workers/evaluation_runner)
    는 변경 없이 그대로 동작한다. 직접 SDK import (anti-patterns.md §1) 위반은 본 Phase 에서
    제거되거나 별도 트랙(이미지/임베딩)으로 분리된다.
"""

from __future__ import annotations

import hashlib
import json as json_module
import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, TypeVar

import httpx
from pydantic import BaseModel

from app.core.config import get_settings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


# Structured Output 통일 인터페이스용 제네릭 타입 파라미터.
# BaseModel 서브클래스만 허용하여 응답을 해당 모델로 강타입 검증한다.
T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# 추상 베이스 클래스
# ---------------------------------------------------------------------------


class LLMClient(ABC):
    """모든 LLM 클라이언트의 추상 베이스 클래스.

    하위 클래스는 generate, generate_stream, generate_structured 메서드를
    구현해야 한다. 동기 메서드(generate_sync, generate_structured_sync)는
    Celery worker처럼 async를 사용할 수 없는 환경에서 사용한다.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o",
        base_url: str | None = None,
    ) -> None:
        # Phase 7 — R2 완전 보강 (2026-05-11): base_url default 를 ``https://api.openai.com/v1``
        # 에서 ``None`` 으로 변경. ``AgentHubLLMWrapper`` 가 ``"agenthub://"`` 로 override 하고,
        # 서브클래스(OpenAIClient/VLLMClient/SGLangClient/AzureOpenAIClient)는 명시 지정한다.
        # base_url 미지정 상태로 ``OpenAICompatibleClient`` 가 instantiate 되면 ``RuntimeError``
        # 를 던져 OpenAI 직접 호출(anti-patterns.md §1 위반)을 사전 차단.
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/") if base_url else ""

    # -- 비동기 메서드 (FastAPI 등에서 사용) --

    @abstractmethod
    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> str | AsyncGenerator[str, None]:
        """메시지 목록으로부터 응답을 생성한다.

        stream=False이면 전체 텍스트(str)를 반환하고,
        stream=True이면 토큰을 하나씩 yield하는 AsyncGenerator를 반환한다.
        """
        ...

    @abstractmethod
    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        """토큰 단위로 스트리밍 응답을 생성한다."""
        ...

    @abstractmethod
    async def generate_structured(
        self,
        messages: list[dict[str, str]],
        json_schema: dict,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> dict:
        """JSON 스키마에 맞는 구조화된 응답을 반환한다.

        OpenAI의 Structured Outputs, Claude의 Tool Use 등
        프로바이더별로 다른 방식으로 구현된다.
        """
        ...

    # -- Structured Output 통일 인터페이스 (Phase 4 S1 D5) --
    #
    # Pydantic BaseModel 기반 단일 진입점. 기존 ``generate_structured(dict)`` 는
    # 하위 호환을 위해 유지되며, documents_v2 등 신규 코드는 본 메서드를 사용한다.
    # 기본 구현은 각 프로바이더의 ``generate_structured(dict)`` 로 위임하고
    # 결과를 ``response_schema`` 로 재검증한다. 프로바이더별 최적화가 필요할 때만
    # 하위 클래스에서 오버라이드한다 (예: Gemini 스키마 평탄화, Claude Tool Use).

    async def generate_with_schema(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[T],
        *,
        temperature: float = 0.3,
        max_tokens: int | None = None,
    ) -> T:
        """Pydantic Structured Output 통일 인터페이스 (비동기).

        Parameters
        ----------
        system_prompt:
            시스템 역할 프롬프트.
        user_prompt:
            사용자 역할 프롬프트.
        response_schema:
            기대하는 응답의 Pydantic 모델 클래스.
        temperature:
            생성 온도 (기본 0.3, Structured Output 은 일반적으로 저온).
        max_tokens:
            최대 토큰. None 이면 클라이언트 기본값(4096).

        Returns
        -------
        response_schema
            검증 통과한 Pydantic 모델 인스턴스.

        Notes
        -----
        - 기본 구현은 ``generate_structured(dict)`` 호출 후 Pydantic 재검증.
        - Gemini 등 Discriminated Union 미지원 프로바이더는 하위 클래스에서
          스키마 평탄화 후 호출하도록 오버라이드할 것.
        """
        # 지연 import 로 순환 참조 회피
        from app.integrations.llm.schema_adapter import (
            pydantic_to_openai_schema,
            validate_structured_output,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        json_schema = pydantic_to_openai_schema(response_schema)
        raw = await self.generate_structured(
            messages=messages,
            json_schema=json_schema,
            temperature=temperature,
            max_tokens=max_tokens or 4096,
        )
        return validate_structured_output(raw, response_schema)

    def generate_with_schema_sync(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[T],
        *,
        temperature: float = 0.3,
        max_tokens: int | None = None,
    ) -> T:
        """Pydantic Structured Output 통일 인터페이스 (동기, Celery worker 용).

        비동기 버전과 동일한 의미. 기본 구현은
        ``generate_structured_sync(dict)`` 호출 후 Pydantic 재검증.
        """
        from app.integrations.llm.schema_adapter import (
            pydantic_to_openai_schema,
            validate_structured_output,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        json_schema = pydantic_to_openai_schema(response_schema)
        raw = self.generate_structured_sync(
            messages=messages,
            json_schema=json_schema,
            temperature=temperature,
            max_tokens=max_tokens or 4096,
        )
        return validate_structured_output(raw, response_schema)

    # -- 동기 메서드 (Celery worker 등에서 사용) --

    def generate_sync(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> str:
        """동기 컨텍스트에서 응답을 생성한다. (Celery worker용)"""
        raise NotImplementedError(f"{self.__class__.__name__}은 동기 호출을 지원하지 않습니다.")

    def generate_structured_sync(
        self,
        messages: list[dict[str, str]],
        json_schema: dict,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> dict:
        """동기 컨텍스트에서 구조화된 응답을 생성한다. (Celery worker용)"""
        raise NotImplementedError(f"{self.__class__.__name__}은 동기 Structured Outputs를 지원하지 않습니다.")


# ---------------------------------------------------------------------------
# AgentHub 위임 LLM 래퍼 (Phase 7.3 — R2 단일 진입점)
# ---------------------------------------------------------------------------


class AgentHubLLMWrapper(LLMClient):
    """AgentHub `/v1/chat/completions` 위임 LLM 클라이언트.

    Phase 7.3 부터 DocUtil 의 모든 LLM 호출은 본 래퍼를 통해 AgentHub Gateway 로
    위임된다. 외부 시그니처(``generate`` / ``generate_stream`` / ``generate_structured``
    / ``generate_with_schema`` 및 _sync 동기 변종)는 기존 ``OpenAICompatibleClient``
    와 동일하므로, 호출처(documents_v2, templates, workers 등)는 변경 없이 그대로
    동작한다.

    설계 원칙:
        - **R2 단일 진입점**: 외부 LLM SDK / OpenAI 호환 엔드포인트 직접 호출 금지.
          모든 호출은 ``AgentHubClient`` 를 거쳐 AgentHub 의 라우팅(External/Internal/
          Hybrid) / 사용량 / PII / 캐싱 정책을 적용받는다.
        - **AgentCode 매핑**: ``provider`` (호출처가 전달하는 프로바이더 문자열) 또는
          ``model`` 을 기반으로 적절한 AgentCode 를 결정한다. ``factory.create_llm_client``
          가 매핑을 수행하므로 본 래퍼는 결정된 ``agent_code`` 를 그대로 사용한다.
        - **동기 호출**: Celery worker 등에서 ``generate_sync`` / ``generate_structured_sync``
          가 호출되므로, 내부적으로 동기 ``httpx.Client`` 를 별도로 운용한다 (asyncio
          이벤트 루프 부재 환경 호환).

    Notes
    -----
    - Structured Outputs (``response_format={"type": "json_schema", ...}``) 는
      AgentHub 가 OpenAI 호환 모드로 그대로 forward 하므로 ``extra`` 파라미터로
      전달한다.
    - 임베딩 (``/v1/embeddings``) 은 AgentHub 미구현 — Phase 7.5 또는 별도 트랙으로
      분리. 본 래퍼는 chat/completions 만 처리한다.
    """

    # 동기 호출 타임아웃 (초). 보고서 생성 등 긴 호출 대비.
    _SYNC_TIMEOUT = 180.0

    def __init__(
        self,
        agent_code: str,
        *,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        """AgentHubLLMWrapper 를 초기화한다.

        Parameters
        ----------
        agent_code:
            AgentHub 에 등록된 AgentCode (예: ``"docutil-rag-chat"``,
            ``"docutil-report-generator"``, ``"docutil-evaluator"``).
            AgentHub 의 OpenAI 호환 엔드포인트는 ``model`` 필드로 Agent 를 식별한다.
        api_key:
            (호환용 인자, 사용하지 않음). AgentHub 인증은 환경변수
            ``AGENTHUB_API_KEY`` 를 통해 ``AgentHubClient`` 가 직접 처리한다.
        model:
            (호환용 인자, 사용하지 않음). 실제 LLM 모델 결정은 AgentHub 가 수행한다.
            본 인자는 ``LLMClient.model`` 속성으로만 보존되어 로깅/디버깅에 사용된다.
        """
        # LLMClient 베이스의 model 속성은 보존 — 일부 호출처가 ``client.model`` 로 참조.
        super().__init__(api_key=api_key, model=model or agent_code, base_url="agenthub://")
        self.agent_code = agent_code

    # ── 비동기 메서드 ───────────────────────────────────────────────────────

    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> str | AsyncGenerator[str, None]:
        """비동기 chat 호출. ``stream=True`` 면 토큰 스트리밍 generator 반환."""
        if stream:
            return self.generate_stream(messages, temperature, max_tokens)

        # 지연 import — 모듈 로드 시점의 환경변수 검증 회피 + 순환 참조 방지.
        from app.integrations.agenthub_client import get_agenthub_client

        client = get_agenthub_client()
        resp = await client.chat(
            agent_code=self.agent_code,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp["choices"][0]["message"]["content"]

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        """SSE 스트리밍. AgentHub chunk 의 ``delta.content`` 만 추출하여 yield."""
        from app.integrations.agenthub_client import get_agenthub_client

        client = get_agenthub_client()
        async for chunk in client.chat_stream(
            agent_code=self.agent_code,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            try:
                delta = chunk["choices"][0].get("delta", {})
            except (KeyError, IndexError, TypeError):
                continue
            content = delta.get("content")
            if content:
                yield content

    async def generate_structured(
        self,
        messages: list[dict[str, str]],
        json_schema: dict,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> dict:
        """OpenAI Structured Outputs (``response_format=json_schema``) 위임.

        AgentHub 는 OpenAI 호환 ``response_format`` 을 그대로 forward 하므로
        ``extra`` 파라미터로 전달한다.
        """
        from app.integrations.agenthub_client import get_agenthub_client

        client = get_agenthub_client()
        resp = await client.chat(
            agent_code=self.agent_code,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            extra={
                "response_format": {
                    "type": "json_schema",
                    "json_schema": json_schema,
                }
            },
        )
        content = resp["choices"][0]["message"]["content"]
        return json_module.loads(content)

    # ── 동기 메서드 (Celery worker 용) ─────────────────────────────────────
    #
    # Celery worker 는 prefork 모델로 asyncio 이벤트 루프가 없는 환경에서 실행되므로,
    # ``httpx.Client`` 동기 호출을 별도로 운용한다. AgentHubClient 의 비동기 인터페이스
    # 와 동일한 엔드포인트(`POST /v1/chat/completions`) + 동일한 인증 헤더(`X-API-Key`)
    # 를 사용한다. 환경변수 로드는 호출 시점에 수행 (lazy).

    def _sync_post(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """동기 httpx 로 AgentHub `/v1/chat/completions` 호출."""
        import os

        base_url = os.environ.get("AGENTHUB_URL", "").strip()
        api_key = os.environ.get("AGENTHUB_API_KEY", "").strip()
        if not base_url:
            raise RuntimeError("AgentHub base_url 미설정 — 환경변수 AGENTHUB_URL 확인 (Phase 7.3)")
        if not api_key:
            raise RuntimeError("AgentHub api_key 미설정 — 환경변수 AGENTHUB_API_KEY 확인 (Phase 7.3)")

        with httpx.Client(timeout=self._SYNC_TIMEOUT) as client:
            response = client.post(
                f"{base_url.rstrip('/')}/v1/chat/completions",
                headers={
                    "X-API-Key": api_key,
                    "Content-Type": "application/json",
                    "User-Agent": "AgentHubLLMWrapper/1.0 (docutil-sync)",
                },
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    def generate_sync(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> str:
        """동기 chat 호출 (Celery worker 용). AgentHub 위임."""
        payload: dict[str, Any] = {
            "model": self.agent_code,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        data = self._sync_post(payload)
        return data["choices"][0]["message"]["content"]

    def generate_structured_sync(
        self,
        messages: list[dict[str, str]],
        json_schema: dict,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> dict:
        """동기 Structured Outputs 호출 (Celery worker 용). AgentHub 위임."""
        payload: dict[str, Any] = {
            "model": self.agent_code,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
            "response_format": {
                "type": "json_schema",
                "json_schema": json_schema,
            },
        }
        data = self._sync_post(payload)
        content = data["choices"][0]["message"]["content"]
        return json_module.loads(content)


# ---------------------------------------------------------------------------
# OpenAI-호환 API 공통 베이스
# ---------------------------------------------------------------------------


class OpenAICompatibleClient(LLMClient):
    """OpenAI-호환 API를 사용하는 클라이언트의 공통 구현.

    OpenAI, vLLM, SGLang 등 /chat/completions 엔드포인트를 제공하는
    서비스에서 공통으로 사용되는 로직을 집약한다.
    하위 클래스는 생성자에서 api_key, model, base_url만 설정하면 된다.
    """

    # httpx 타임아웃 (초) — 보고서 생성 등 긴 작업에 대비하여 넉넉히 설정
    _TIMEOUT = 180.0

    def _headers(self) -> dict[str, str]:
        """HTTP 요청 헤더를 구성한다."""
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _build_payload(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        stream: bool = False,
        **extra: Any,
    ) -> dict[str, Any]:
        """chat/completions API 요청 페이로드를 구성한다."""
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        # Structured Outputs 등 추가 파라미터 병합
        payload.update(extra)
        return payload

    def _completions_url(self) -> str:
        """chat/completions 엔드포인트 URL을 반환한다."""
        return f"{self.base_url}/chat/completions"

    # -- 비동기 생성 --

    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> str | AsyncGenerator[str, None]:
        """비동기로 응답을 생성한다. stream=True이면 스트리밍 제너레이터를 반환."""
        if stream:
            return self.generate_stream(messages, temperature, max_tokens)

        async with httpx.AsyncClient(timeout=self._TIMEOUT) as client:
            response = await client.post(
                self._completions_url(),
                headers=self._headers(),
                json=self._build_payload(messages, temperature, max_tokens),
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        """SSE 스트리밍으로 토큰을 하나씩 yield한다."""
        async with (
            httpx.AsyncClient(timeout=self._TIMEOUT) as client,
            client.stream(
                "POST",
                self._completions_url(),
                headers=self._headers(),
                json=self._build_payload(messages, temperature, max_tokens, stream=True),
            ) as response,
        ):
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[len("data: ") :]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    data = json_module.loads(data_str)
                    delta = data["choices"][0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        yield content
                except (json_module.JSONDecodeError, KeyError, IndexError):
                    continue

    async def generate_structured(
        self,
        messages: list[dict[str, str]],
        json_schema: dict,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> dict:
        """Structured Outputs (response_format: json_schema)로 JSON 응답을 받는다.

        OpenAI/Azure에서 지원하는 json_schema strict 모드를 사용한다.
        vLLM/SGLang에서도 모델에 따라 지원될 수 있다.
        """
        async with httpx.AsyncClient(timeout=self._TIMEOUT) as client:
            response = await client.post(
                self._completions_url(),
                headers=self._headers(),
                json=self._build_payload(
                    messages,
                    temperature,
                    max_tokens,
                    response_format={
                        "type": "json_schema",
                        "json_schema": json_schema,
                    },
                ),
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return json_module.loads(content)

    # -- 동기 생성 (Celery worker용) --

    def generate_sync(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> str:
        """동기 컨텍스트에서 응답을 생성한다."""
        with httpx.Client(timeout=self._TIMEOUT) as client:
            response = client.post(
                self._completions_url(),
                headers=self._headers(),
                json=self._build_payload(messages, temperature, max_tokens),
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    def generate_structured_sync(
        self,
        messages: list[dict[str, str]],
        json_schema: dict,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> dict:
        """동기 컨텍스트에서 Structured Outputs JSON 응답을 받는다."""
        with httpx.Client(timeout=self._TIMEOUT) as client:
            response = client.post(
                self._completions_url(),
                headers=self._headers(),
                json=self._build_payload(
                    messages,
                    temperature,
                    max_tokens,
                    response_format={
                        "type": "json_schema",
                        "json_schema": json_schema,
                    },
                ),
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return json_module.loads(content)


# ---------------------------------------------------------------------------
# OpenAI 클라이언트 (GPT-4o)
# ---------------------------------------------------------------------------


class OpenAIClient(OpenAICompatibleClient):
    """OpenAI API (GPT-4o 등) 클라이언트.

    .. deprecated:: Phase 7.3 (2026-05-06)
        Phase 7.3 부터 ``factory.create_llm_client`` 는 본 클래스를 직접 instantiate 하지
        않고 ``AgentHubLLMWrapper`` 를 반환한다 — R2 단일 진입점 원칙. 본 클래스는
        ``ModelRouter`` 의 의존성으로만 잔존하며 (``ModelRouter`` 자체도 app 내 사용처 0건),
        ``__init__`` 호출 시 ``RuntimeError`` 를 던져 OpenAI 직접 호출(anti-patterns.md §1)
        을 사전 차단한다. 신규 호출은 ``AgentHubLLMWrapper`` 또는 ``create_llm_client``
        을 사용한다.

    기본 설정은 config.py의 openai_api_key, llm_model을 사용한다.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        # Phase 7 — R2 완전 보강: OpenAI 직접 호출 차단. 호출자에게 마이그레이션 경로 안내.
        raise RuntimeError(
            "OpenAIClient 직접 instantiate 는 더 이상 지원되지 않습니다 "
            "(Phase 7 R2 보강, anti-patterns.md §1). "
            "AgentHubLLMWrapper 또는 create_llm_client('chat') 을 사용하세요."
        )


# ---------------------------------------------------------------------------
# vLLM 클라이언트 (자체 호스팅, OpenAI-호환)
# ---------------------------------------------------------------------------


class VLLMClient(OpenAICompatibleClient):
    """자체 호스팅 vLLM (OpenAI-호환 API) 클라이언트.

    .. deprecated:: Phase 7.3 (2026-05-06)
        ``factory.create_llm_client`` 가 본 클래스를 instantiate 하지 않는다.
        Phase 7 (2026-05-11) 부터 ``__init__`` 호출 시 ``RuntimeError`` — vLLM 직접
        호출은 AgentHub 의 ``LlmRouting=Internal`` 정책으로 라우팅된다.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        raise RuntimeError(
            "VLLMClient 직접 instantiate 는 더 이상 지원되지 않습니다 "
            "(Phase 7 R2 보강, anti-patterns.md §1). "
            "AgentHub Agent 의 LlmRouting='Internal' 정책 또는 "
            "create_llm_client('chat') 을 사용하세요."
        )


# ---------------------------------------------------------------------------
# SGLang 클라이언트 (RadixAttention 기반, OpenAI-호환)
# ---------------------------------------------------------------------------


class SGLangClient(OpenAICompatibleClient):
    """SGLang 서빙 엔진 클라이언트.

    .. deprecated:: Phase 7.3 (2026-05-06)
        ``factory.create_llm_client`` 가 본 클래스를 instantiate 하지 않는다.
        Phase 7 (2026-05-11) 부터 ``__init__`` 호출 시 ``RuntimeError``.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str = "EMPTY",
    ) -> None:
        raise RuntimeError(
            "SGLangClient 직접 instantiate 는 더 이상 지원되지 않습니다 "
            "(Phase 7 R2 보강, anti-patterns.md §1). "
            "AgentHub Agent 의 LlmRouting='Internal' 정책 또는 "
            "create_llm_client('chat') 을 사용하세요."
        )


# ---------------------------------------------------------------------------
# 모델 라우터 (A/B 테스트 지원)
# ---------------------------------------------------------------------------


class ModelRouter:
    """조직/태스크 기반으로 LLM 클라이언트를 선택하는 라우터.

    .. deprecated:: Phase 7.3 (2026-05-06)
        본 라우터는 OpenAIClient/VLLMClient/SGLangClient 를 instantiate 하나, 세 클래스
        모두 Phase 7 (2026-05-11) 부터 ``RuntimeError`` 를 던진다 — A/B 라우팅 책임은
        AgentHub 의 ``LlmRouting`` (External/Internal/Hybrid) 으로 이관되었다. app 내
        사용처 0건. 신규 호출은 ``AgentHubLLMWrapper`` 또는 ``create_llm_client`` 사용.

    결정적 해시 기반 A/B 테스트를 지원하여, 동일한 (org_id, task_type) 조합은
    항상 같은 프로바이더로 라우팅된다. 다중 턴 채팅에는 SGLang을 우선 선택한다.
    """

    # 라우터가 인식하는 태스크 유형
    TASK_TYPES = {
        "qa",
        "chatbot",
        "summarisation",
        "report",
        "tagging",
        "hallucination_check",
        "query_decomposition",
    }

    def __init__(
        self,
        ab_test_ratio: float = 0.0,
        sglang_ratio: float = 0.0,
    ) -> None:
        """라우터를 초기화한다.

        Parameters
        ----------
        ab_test_ratio:
            vLLM으로 라우팅할 트래픽 비율 (0~100). 나머지는 OpenAI로.
        sglang_ratio:
            향후 SGLang 비율 설정용 (현재 미사용).
        """
        self.ab_test_ratio = ab_test_ratio
        self.sglang_ratio = sglang_ratio
        self._openai_client = OpenAIClient()
        self._vllm_client = VLLMClient()
        self._sglang_client = SGLangClient() if get_settings().sglang_enabled else None

    def route(self, org_id: str, task_type: str = "qa") -> LLMClient:
        """조직과 태스크 유형에 따라 적절한 LLM 클라이언트를 반환한다.

        Parameters
        ----------
        org_id:
            요청 조직의 UUID 문자열.
        task_type:
            태스크 유형 (qa, chatbot, report 등).

        Returns
        -------
        LLMClient
            선택된 클라이언트 인스턴스.
        """
        # 다중 턴 채팅은 SGLang 우선 (RadixAttention 이점)
        if task_type == "chatbot" and self._sglang_client:
            return self._sglang_client
        # 해시 기반 A/B 라우팅
        hash_val = (
            int(
                hashlib.sha256(f"{org_id}:{task_type}".encode()).hexdigest(),
                16,
            )
            % 100
        )
        if hash_val < self.ab_test_ratio:
            return self._vllm_client
        return self._openai_client
