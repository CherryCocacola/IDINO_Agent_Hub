"""
Google Gemini LLM 클라이언트 모듈.

Gemini는 OpenAI-호환 엔드포인트를 제공하므로 ``OpenAICompatibleClient`` 를
상속하여 대부분의 기능(일반 생성, 스트리밍)을 그대로 사용한다.

Structured Outputs(JSON 스키마 응답)의 경우, Gemini는 ``response_format:
{"type": "json_schema"}`` 형식을 지원하지만 OpenAI처럼 strict 모드가 없어
스키마를 벗어난 응답이 올 수 있다. 따라서 부모 클래스의 결과를 받은 뒤
필수 키 존재 여부를 검증하고, 실패 시 경고 로그를 남기되 best-effort로
그대로 반환한다.
"""

from __future__ import annotations

import logging
from typing import TypeVar

from pydantic import BaseModel

from app.core.config import get_settings
from app.integrations.llm.client import OpenAICompatibleClient

logger = logging.getLogger(__name__)
settings = get_settings()

T = TypeVar("T", bound=BaseModel)

# Gemini OpenAI-호환 엔드포인트 기본 URL
_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"


def _extract_required_keys(json_schema: dict) -> set[str]:
    """JSON 스키마에서 최상위 필수 키 목록을 추출한다.

    OpenAI Structured Outputs 형식의 스키마 구조를 따른다:
    ``{"name": "...", "schema": {"type": "object", "properties": {...}, "required": [...]}}``

    일반적인 JSON Schema 형식(``{"type": "object", "required": [...]}`` )도 지원한다.

    Parameters
    ----------
    json_schema:
        Structured Outputs 요청에 전달되는 JSON 스키마 딕셔너리.

    Returns
    -------
    set[str]
        최상위 필수 키 이름의 집합. 스키마에 required 필드가 없으면 빈 집합.
    """
    # OpenAI 형식: {"name": "...", "schema": {"type": "object", "required": [...]}}
    inner = json_schema.get("schema", json_schema)
    required = inner.get("required", [])
    return set(required)


def _validate_structured_response(result: dict, json_schema: dict) -> None:
    """Structured Outputs 응답이 스키마의 필수 키를 모두 포함하는지 검증한다.

    검증 실패 시 예외를 발생시키지 않고 경고 로그만 남긴다 (best-effort).
    Gemini는 strict 모드가 없으므로 응답이 스키마를 일부 벗어날 수 있기 때문이다.

    Parameters
    ----------
    result:
        Gemini가 반환한 파싱된 JSON 딕셔너리.
    json_schema:
        요청 시 전달한 JSON 스키마.
    """
    required_keys = _extract_required_keys(json_schema)
    if not required_keys:
        return

    # 결과가 dict가 아닌 경우 (예: 리스트) 키 검증 불가
    if not isinstance(result, dict):
        logger.warning(
            "[GeminiClient] Structured 응답이 dict가 아님 (type=%s). 스키마 필수 키 검증을 건너뜁니다.",
            type(result).__name__,
        )
        return

    missing = required_keys - set(result.keys())
    if missing:
        logger.warning(
            "[GeminiClient] Structured 응답에 필수 키 누락: %s. "
            "Gemini는 strict 모드를 지원하지 않으므로 best-effort로 반환합니다.",
            sorted(missing),
        )


class GeminiClient(OpenAICompatibleClient):
    """Google Gemini OpenAI-호환 API 클라이언트.

    Gemini의 OpenAI-호환 엔드포인트를 사용하여 일반 생성, 스트리밍,
    Structured Outputs를 모두 지원한다.

    일반 생성 / 스트리밍은 ``OpenAICompatibleClient`` 의 구현을 그대로 사용하고,
    Structured Outputs만 응답 검증 로직을 추가로 오버라이드한다.

    Examples
    --------
    >>> from app.integrations.llm.gemini_client import GeminiClient
    >>> client = GeminiClient()
    >>> # 일반 텍스트 생성
    >>> text = await client.generate([{"role": "user", "content": "안녕하세요"}])
    >>> # 구조화된 JSON 응답
    >>> data = await client.generate_structured(messages, schema)
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str = _GEMINI_BASE_URL,
    ) -> None:
        """GeminiClient를 초기화한다.

        Parameters
        ----------
        api_key:
            Google API 키. 미지정 시 ``settings.google_api_key`` 사용.
        model:
            사용할 Gemini 모델 이름. 미지정 시 ``settings.google_model`` 사용.
            기본값: ``gemini-2.0-flash``.
        base_url:
            Gemini OpenAI-호환 엔드포인트 URL.
        """
        super().__init__(
            api_key=api_key or settings.google_api_key,
            model=model or settings.google_model,
            base_url=base_url,
        )
        logger.info(
            "[GeminiClient] 초기화 완료 (model=%s, base_url=%s)",
            self.model,
            self.base_url,
        )

    # ------------------------------------------------------------------
    # Structured Outputs 오버라이드 (비동기)
    # ------------------------------------------------------------------

    async def generate_structured(
        self,
        messages: list[dict[str, str]],
        json_schema: dict,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> dict:
        """JSON 스키마에 맞는 구조화된 응답을 생성한다.

        부모 클래스(OpenAICompatibleClient)의 Structured Outputs 로직을
        그대로 호출한 뒤, 응답의 필수 키 존재 여부를 추가 검증한다.

        Gemini는 OpenAI와 달리 strict 모드가 없으므로 스키마를 완벽히
        준수하지 않을 수 있다. 검증 실패 시 경고 로그를 남기고
        best-effort로 결과를 그대로 반환한다.

        Parameters
        ----------
        messages:
            대화 메시지 목록 (role, content 딕셔너리).
        json_schema:
            OpenAI Structured Outputs 형식의 JSON 스키마.
        temperature:
            생성 온도 (0.0~2.0). 낮을수록 결정적.
        max_tokens:
            최대 생성 토큰 수.

        Returns
        -------
        dict
            파싱된 JSON 응답 딕셔너리.
        """
        result = await super().generate_structured(messages, json_schema, temperature, max_tokens)

        # 필수 키 검증 (best-effort)
        _validate_structured_response(result, json_schema)

        return result

    # ------------------------------------------------------------------
    # Structured Outputs 오버라이드 (동기 — Celery worker용)
    # ------------------------------------------------------------------

    def generate_structured_sync(
        self,
        messages: list[dict[str, str]],
        json_schema: dict,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> dict:
        """동기 컨텍스트에서 구조화된 JSON 응답을 생성한다. (Celery worker용)

        부모 클래스의 동기 Structured Outputs를 호출한 뒤
        비동기 버전과 동일하게 필수 키 검증을 수행한다.

        Parameters
        ----------
        messages:
            대화 메시지 목록.
        json_schema:
            JSON 스키마.
        temperature:
            생성 온도.
        max_tokens:
            최대 생성 토큰 수.

        Returns
        -------
        dict
            파싱된 JSON 응답 딕셔너리.
        """
        result = super().generate_structured_sync(messages, json_schema, temperature, max_tokens)

        # 필수 키 검증 (best-effort)
        _validate_structured_response(result, json_schema)

        return result

    # ------------------------------------------------------------------
    # Structured Output 통일 인터페이스 (Phase 4 S1 D5)
    # ------------------------------------------------------------------
    #
    # Gemini 는 Discriminated Union (oneOf/anyOf) 와 $ref 를 지원하지 않는다.
    # 기본 구현은 원본 Pydantic JSON Schema 를 그대로 보내므로, Gemini 에서는
    # 400 에러 또는 스키마 무시 응답이 반환될 수 있다. 따라서 오버라이드하여
    # schema_adapter.pydantic_to_gemini_schema 로 사전 평탄화 후 전송한다.
    # 응답은 원본 Pydantic 모델로 재검증하여 정보 손실을 방지한다.

    async def generate_with_schema(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[T],
        *,
        temperature: float = 0.3,
        max_tokens: int | None = None,
    ) -> T:
        """Gemini 평탄화 스키마 기반 Structured Output (비동기).

        Gemini 는 Discriminated Union 을 네이티브로 지원하지 않으므로,
        스키마를 단일 object 로 평탄화한 뒤 전송하고 응답은 원본 모델로
        재검증한다. 이로 인해 Gemini 가 union 의 특정 variant 를 정확히
        반영하지 못할 때 ValidationError 가 발생할 수 있다.
        """
        from app.integrations.llm.schema_adapter import (
            pydantic_to_gemini_schema,
            validate_structured_output,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        flat_schema = pydantic_to_gemini_schema(response_schema)
        gemini_json_schema = {
            "name": response_schema.__name__,
            "schema": flat_schema,
        }

        # 부모의 generate_structured(dict) 를 호출해서 HTTP 왕복 실행.
        # Gemini 는 strict 키를 무시하므로 설정해도 무해하다.
        raw = await super().generate_structured(
            messages=messages,
            json_schema=gemini_json_schema,
            temperature=temperature,
            max_tokens=max_tokens or 4096,
        )
        # 원본 Pydantic 모델로 재검증 — 평탄화로 잃어버린 엄밀성 복원.
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
        """Gemini 평탄화 스키마 기반 Structured Output (동기, Celery worker 용)."""
        from app.integrations.llm.schema_adapter import (
            pydantic_to_gemini_schema,
            validate_structured_output,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        flat_schema = pydantic_to_gemini_schema(response_schema)
        gemini_json_schema = {
            "name": response_schema.__name__,
            "schema": flat_schema,
        }

        raw = super().generate_structured_sync(
            messages=messages,
            json_schema=gemini_json_schema,
            temperature=temperature,
            max_tokens=max_tokens or 4096,
        )
        return validate_structured_output(raw, response_schema)
