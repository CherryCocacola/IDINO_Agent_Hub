"""
LLM 클라이언트 구현 모듈.

제공하는 클래스:
  - ``LLMClient`` -- 모든 LLM 클라이언트의 추상 베이스 클래스.
  - ``OpenAICompatibleClient`` -- OpenAI-호환 API를 사용하는 클라이언트 공통 구현.
  - ``OpenAIClient`` -- OpenAI API (GPT-4o 등) 클라이언트.
  - ``VLLMClient`` -- 자체 호스팅 vLLM (OpenAI-호환) 클라이언트.
  - ``SGLangClient`` -- SGLang (RadixAttention) 클라이언트.
  - ``ModelRouter`` -- 조직/태스크 기반 A/B 테스트 라우팅.
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
        base_url: str = "https://api.openai.com/v1",
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

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

    기본 설정은 config.py의 openai_api_key, llm_model을 사용한다.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str = "https://api.openai.com/v1",
    ) -> None:
        super().__init__(
            api_key=api_key or settings.openai_api_key,
            model=model or settings.llm_model,
            base_url=base_url,
        )


# ---------------------------------------------------------------------------
# vLLM 클라이언트 (자체 호스팅, OpenAI-호환)
# ---------------------------------------------------------------------------


class VLLMClient(OpenAICompatibleClient):
    """자체 호스팅 vLLM (OpenAI-호환 API) 클라이언트.

    GPU 서버에서 실행되는 vLLM 엔진에 연결한다.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model or settings.llm_model,
            base_url=base_url or settings.vllm_url,
        )


# ---------------------------------------------------------------------------
# SGLang 클라이언트 (RadixAttention 기반, OpenAI-호환)
# ---------------------------------------------------------------------------


class SGLangClient(OpenAICompatibleClient):
    """SGLang 서빙 엔진 클라이언트.

    RadixAttention으로 다중 턴 대화의 KV 캐시를 효율적으로 재활용한다.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str = "EMPTY",
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model or settings.llm_model,
            base_url=base_url or settings.sglang_url,
        )


# ---------------------------------------------------------------------------
# 모델 라우터 (A/B 테스트 지원)
# ---------------------------------------------------------------------------


class ModelRouter:
    """조직/태스크 기반으로 LLM 클라이언트를 선택하는 라우터.

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
