"""
Anthropic Claude LLM 클라이언트 구현 모듈.

Claude는 OpenAI-호환 API가 아니므로 ``LLMClient`` ABC를 직접 상속하여 구현한다.
공식 ``anthropic`` SDK (AsyncAnthropic / Anthropic)를 사용한다.

제공하는 클래스:
  - ``ClaudeClient`` -- Anthropic Claude API 클라이언트.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, TypeVar

from pydantic import BaseModel

from app.core.config import get_settings
from app.integrations.llm.client import LLMClient

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# anthropic SDK lazy import
# SDK가 설치되지 않은 환경에서도 모듈 로딩은 실패하지 않도록
# 클래스 메서드 내부에서 import하되, 여기서 미리 체크도 수행한다.
# ---------------------------------------------------------------------------
try:
    import anthropic
    from anthropic import Anthropic, AsyncAnthropic
except ImportError:
    anthropic = None  # type: ignore[assignment]
    Anthropic = None  # type: ignore[assignment,misc]
    AsyncAnthropic = None  # type: ignore[assignment,misc]


def _ensure_anthropic_installed() -> None:
    """anthropic 패키지가 설치되어 있는지 확인한다.

    설치되지 않았으면 설치 안내와 함께 ImportError를 발생시킨다.
    """
    if anthropic is None:
        raise ImportError("anthropic 패키지가 설치되지 않았습니다. 다음 명령으로 설치하세요: pip install anthropic")


# ---------------------------------------------------------------------------
# 메시지 변환 헬퍼
# ---------------------------------------------------------------------------


def _convert_messages(
    messages: list[dict[str, str]],
) -> tuple[str | None, list[dict[str, str]]]:
    """OpenAI 형식 메시지 목록을 Claude 형식으로 변환한다.

    OpenAI 포맷에서는 system 역할의 메시지가 messages 배열 안에 포함되지만,
    Claude API에서는 ``system`` 파라미터로 분리해서 전달해야 한다.

    Parameters
    ----------
    messages:
        OpenAI 형식의 메시지 목록.
        예: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]

    Returns
    -------
    tuple[str | None, list[dict[str, str]]]
        (system_text, claude_messages) 튜플.
        - system_text: system 역할 메시지들을 합친 텍스트 (없으면 None).
        - claude_messages: user/assistant 역할 메시지만 포함한 목록.
    """
    system_parts: list[str] = []
    claude_messages: list[dict[str, str]] = []

    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")

        if role == "system":
            # system 메시지는 별도로 모아서 system 파라미터에 전달
            if content:
                system_parts.append(content)
        elif role in ("user", "assistant"):
            # user와 assistant만 Claude messages 배열에 포함
            claude_messages.append({"role": role, "content": content})
        else:
            # 알 수 없는 role은 user로 변환 (function, tool 등)
            logger.warning("알 수 없는 메시지 role '%s'을(를) 'user'로 변환합니다.", role)
            claude_messages.append({"role": "user", "content": content})

    system_text = "\n\n".join(system_parts) if system_parts else None
    return system_text, claude_messages


# ---------------------------------------------------------------------------
# Claude 클라이언트
# ---------------------------------------------------------------------------


class ClaudeClient(LLMClient):
    """Anthropic Claude API 클라이언트.

    OpenAI-호환 API가 아니므로 LLMClient ABC를 직접 상속하여
    anthropic SDK를 사용해 구현한다.

    기본 설정은 config.py의 anthropic_api_key, anthropic_model을 사용한다.
    """

    # API 호출 타임아웃 (초) — 보고서 생성 등 장시간 작업 대비
    _TIMEOUT = 180.0

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        """ClaudeClient를 초기화한다.

        Parameters
        ----------
        api_key:
            Anthropic API 키. 생략 시 settings에서 가져온다.
        model:
            사용할 Claude 모델 이름. 생략 시 settings에서 가져온다.
        base_url:
            커스텀 Anthropic API 엔드포인트. (프록시 등 사용 시)
        """
        _ensure_anthropic_installed()

        resolved_api_key = api_key or settings.anthropic_api_key
        resolved_model = model or settings.anthropic_model

        # LLMClient.__init__은 api_key, model, base_url을 속성으로 설정
        super().__init__(
            api_key=resolved_api_key,
            model=resolved_model,
            base_url=base_url or "https://api.anthropic.com",
        )

    # ── 내부 헬퍼: 클라이언트 생성 ───────────────────────────────────────

    def _create_async_client(self) -> AsyncAnthropic:
        """비동기 Anthropic 클라이언트 인스턴스를 생성한다."""
        kwargs: dict = {
            "api_key": self.api_key,
            "timeout": self._TIMEOUT,
        }
        # 기본 Anthropic URL이 아닌 경우에만 base_url 전달 (프록시 지원)
        if self.base_url != "https://api.anthropic.com":
            kwargs["base_url"] = self.base_url
        return AsyncAnthropic(**kwargs)

    def _create_sync_client(self) -> Anthropic:
        """동기 Anthropic 클라이언트 인스턴스를 생성한다. (Celery worker용)"""
        kwargs: dict = {
            "api_key": self.api_key,
            "timeout": self._TIMEOUT,
        }
        if self.base_url != "https://api.anthropic.com":
            kwargs["base_url"] = self.base_url
        return Anthropic(**kwargs)

    # ── 비동기 메서드 ────────────────────────────────────────────────────

    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> str | AsyncGenerator[str, None]:
        """비동기로 Claude 응답을 생성한다.

        stream=False이면 전체 텍스트(str)를 반환하고,
        stream=True이면 토큰을 하나씩 yield하는 AsyncGenerator를 반환한다.
        """
        if stream:
            return self.generate_stream(messages, temperature, max_tokens)

        system_text, claude_messages = _convert_messages(messages)
        client = self._create_async_client()

        try:
            # Claude API 호출
            kwargs: dict = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": claude_messages,
                "temperature": temperature,
            }
            # system 파라미터는 값이 있을 때만 전달
            if system_text:
                kwargs["system"] = system_text

            response = await client.messages.create(**kwargs)

            # 응답의 첫 번째 content 블록에서 텍스트 추출
            return response.content[0].text

        except Exception:
            logger.exception("Claude generate() 호출 중 에러 발생")
            raise

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        """토큰 단위로 Claude 스트리밍 응답을 생성한다.

        anthropic SDK의 ``messages.stream()`` 컨텍스트 매니저를 사용하여
        서버에서 토큰이 생성될 때마다 즉시 yield한다.
        챗봇 실시간 응답 표시 등에 사용된다.
        """
        system_text, claude_messages = _convert_messages(messages)
        client = self._create_async_client()

        try:
            kwargs: dict = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": claude_messages,
                "temperature": temperature,
            }
            if system_text:
                kwargs["system"] = system_text

            # stream() 컨텍스트 매니저로 스트리밍 세션 열기
            async with client.messages.stream(**kwargs) as stream:
                # text_stream은 텍스트 토큰만 yield하는 편의 이터레이터
                async for text in stream.text_stream:
                    yield text

        except Exception:
            logger.exception("Claude generate_stream() 호출 중 에러 발생")
            raise

    async def generate_structured(
        self,
        messages: list[dict[str, str]],
        json_schema: dict,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> dict:
        """JSON 스키마에 맞는 구조화된 응답을 반환한다. (Tool Use 패턴)

        Claude는 OpenAI의 Structured Outputs를 직접 지원하지 않으므로,
        JSON 스키마를 Tool의 input_schema로 변환하고 해당 tool을 강제 호출하여
        구조화된 JSON 응답을 얻는다.

        동작 원리:
        1. json_schema를 "structured_output" 이름의 tool로 정의
        2. tool_choice로 해당 tool을 강제 선택
        3. 응답의 tool_use content 블록에서 input (dict)을 추출
        """
        system_text, claude_messages = _convert_messages(messages)
        client = self._create_async_client()

        # JSON 스키마에서 tool input_schema 구성
        # OpenAI Structured Outputs 형식: {"name": "...", "strict": true, "schema": {...}}
        # Claude Tool 형식: {"name": "...", "description": "...", "input_schema": {...}}
        input_schema = json_schema.get("schema", json_schema)

        tool_definition = {
            "name": "structured_output",
            "description": "요청된 JSON 스키마에 맞춰 구조화된 데이터를 출력한다.",
            "input_schema": input_schema,
        }

        try:
            kwargs: dict = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": claude_messages,
                "temperature": temperature,
                "tools": [tool_definition],
                # 반드시 structured_output tool을 사용하도록 강제
                "tool_choice": {"type": "tool", "name": "structured_output"},
            }
            if system_text:
                kwargs["system"] = system_text

            response = await client.messages.create(**kwargs)

            # 응답 content 블록 중 tool_use 타입을 찾아 input 추출
            for block in response.content:
                if block.type == "tool_use":
                    return block.input  # type: ignore[return-value]

            # tool_use 블록이 없는 경우 (발생하면 안 됨)
            logger.error(
                "Claude structured 응답에 tool_use 블록이 없습니다: %s",
                response.content,
            )
            raise ValueError("Claude 응답에서 tool_use 블록을 찾을 수 없습니다.")

        except Exception:
            logger.exception("Claude generate_structured() 호출 중 에러 발생")
            raise

    # ── Structured Output 통일 인터페이스 (Phase 4 S1 D5) ──────────────
    #
    # Claude 는 native JSON Schema 모드가 없어 Tool Use 패턴을 사용한다.
    # 기본 구현(generate_structured dict) 을 거치지 않고 Pydantic 모델을
    # 직접 Claude Tool 로 변환하여 왕복 횟수를 최소화한다.

    async def generate_with_schema(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[T],
        *,
        temperature: float = 0.3,
        max_tokens: int | None = None,
    ) -> T:
        """Claude Tool Use 기반 Structured Output (비동기).

        동작:
            1. Pydantic model → Claude Tool 정의 (schema_adapter).
            2. tool_choice 로 해당 tool 강제 호출.
            3. 응답의 tool_use block.input 을 Pydantic 으로 재검증.

        Discriminated Union 지원:
            Claude 는 oneOf/anyOf 를 대부분 수용한다. DocumentSchema 의 22
            컴포넌트 union 도 정상 동작하는 것으로 Phase 4 R1 검증에서 확인.
        """
        from app.integrations.llm.schema_adapter import (
            pydantic_to_claude_tool,
            validate_structured_output,
        )

        claude_messages = [{"role": "user", "content": user_prompt}]
        tool_definition = pydantic_to_claude_tool(response_schema)
        resolved_max_tokens = max_tokens or 4096

        client = self._create_async_client()
        try:
            kwargs: dict = {
                "model": self.model,
                "max_tokens": resolved_max_tokens,
                "messages": claude_messages,
                "temperature": temperature,
                "tools": [tool_definition],
                "tool_choice": {"type": "tool", "name": tool_definition["name"]},
            }
            if system_prompt:
                kwargs["system"] = system_prompt

            response = await client.messages.create(**kwargs)

            for block in response.content:
                if getattr(block, "type", None) == "tool_use":
                    return validate_structured_output(block.input, response_schema)

            logger.error(
                "[ClaudeClient.generate_with_schema] tool_use 블록 없음: %s",
                response.content,
            )
            raise ValueError("Claude 응답에서 tool_use 블록을 찾을 수 없습니다.")
        except Exception:
            logger.exception("Claude generate_with_schema() 호출 중 에러 발생")
            raise

    def generate_with_schema_sync(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[T],
        *,
        temperature: float = 0.3,
        max_tokens: int | None = None,
    ) -> T:
        """Claude Tool Use 기반 Structured Output (동기, Celery worker 용)."""
        from app.integrations.llm.schema_adapter import (
            pydantic_to_claude_tool,
            validate_structured_output,
        )

        claude_messages = [{"role": "user", "content": user_prompt}]
        tool_definition = pydantic_to_claude_tool(response_schema)
        resolved_max_tokens = max_tokens or 4096

        client = self._create_sync_client()
        try:
            kwargs: dict = {
                "model": self.model,
                "max_tokens": resolved_max_tokens,
                "messages": claude_messages,
                "temperature": temperature,
                "tools": [tool_definition],
                "tool_choice": {"type": "tool", "name": tool_definition["name"]},
            }
            if system_prompt:
                kwargs["system"] = system_prompt

            response = client.messages.create(**kwargs)

            for block in response.content:
                if getattr(block, "type", None) == "tool_use":
                    return validate_structured_output(block.input, response_schema)

            logger.error(
                "[ClaudeClient.generate_with_schema_sync] tool_use 블록 없음: %s",
                response.content,
            )
            raise ValueError("Claude 응답에서 tool_use 블록을 찾을 수 없습니다.")
        except Exception:
            logger.exception("Claude generate_with_schema_sync() 호출 중 에러 발생")
            raise

    # ── 동기 메서드 (Celery worker용) ────────────────────────────────────

    def generate_sync(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> str:
        """동기 컨텍스트에서 Claude 응답을 생성한다.

        Celery worker처럼 async를 사용할 수 없는 환경에서 사용한다.
        동기 Anthropic 클라이언트를 사용한다.
        """
        system_text, claude_messages = _convert_messages(messages)
        client = self._create_sync_client()

        try:
            kwargs: dict = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": claude_messages,
                "temperature": temperature,
            }
            if system_text:
                kwargs["system"] = system_text

            response = client.messages.create(**kwargs)
            return response.content[0].text

        except Exception:
            logger.exception("Claude generate_sync() 호출 중 에러 발생")
            raise

    def generate_structured_sync(
        self,
        messages: list[dict[str, str]],
        json_schema: dict,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> dict:
        """동기 컨텍스트에서 구조화된 Claude 응답을 반환한다. (Tool Use 패턴)

        generate_structured()의 동기 버전으로,
        Celery worker에서 보고서/제안서 생성 시 사용된다.
        """
        system_text, claude_messages = _convert_messages(messages)
        client = self._create_sync_client()

        input_schema = json_schema.get("schema", json_schema)

        tool_definition = {
            "name": "structured_output",
            "description": "요청된 JSON 스키마에 맞춰 구조화된 데이터를 출력한다.",
            "input_schema": input_schema,
        }

        try:
            kwargs: dict = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": claude_messages,
                "temperature": temperature,
                "tools": [tool_definition],
                "tool_choice": {"type": "tool", "name": "structured_output"},
            }
            if system_text:
                kwargs["system"] = system_text

            response = client.messages.create(**kwargs)

            for block in response.content:
                if block.type == "tool_use":
                    return block.input  # type: ignore[return-value]

            logger.error(
                "Claude structured_sync 응답에 tool_use 블록이 없습니다: %s",
                response.content,
            )
            raise ValueError("Claude 응답에서 tool_use 블록을 찾을 수 없습니다.")

        except Exception:
            logger.exception("Claude generate_structured_sync() 호출 중 에러 발생")
            raise
