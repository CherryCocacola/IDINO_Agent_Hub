"""
AgentHubClient — DocUtil 측 공용 AI Gateway 클라이언트
=========================================================

목적 (Phase 7.2 — R2 단일 진입점 인프라 사전 준비):
    DocUtil 의 모든 LLM 호출을 *AgentHub* 의 OpenAI 호환 엔드포인트
    (`POST /v1/chat/completions`) 로 위임하기 위한 비동기 httpx 래퍼.

설계 원칙:
    - **Single Implementation (P1)**: 본 모듈이 DocUtil 의 유일한 AgentHub 진입점.
      직접 OpenAI/Anthropic SDK import 는 anti-patterns.md §1 위반 — 본 클라이언트로 교체.
    - **R3 스키마 격리**: 본 클라이언트는 HTTP 호출만 수행 — DB/스키마 직접 접근 금지.
    - **R5 한국어**: 사용자에게 노출되는 예외 메시지는 한국어. 내부 로그는 영문/한글 병기.
    - **에러 폴백**: AgentHub 비가용 시 OpenAI SDK 직접 호출 폴백을 *지원하지 않는다* —
      Phase 7.3 에서 R2 단일 진입점을 강제. 폴백이 필요하면 AgentHub 측에서 라우팅 정책으로 결정.

인증:
    - 헤더 `X-API-Key: ak-...` (Phase 7.2 발급된 master 키)
    - AgentHub 가 ApiKeyAuthService 로 KeyHash UNIQUE 단건 조회 후 통과 — Scopes 검증.

스트리밍 (SSE):
    - AgentHub `/v1/chat/completions` 의 `stream=true` 응답은 `data: {json}\\n\\n` 형식.
    - 본 클라이언트의 `chat_stream` 은 이를 줄단위로 파싱하여 dict 비동기 generator 로 반환.
    - 종료 마커 `data: [DONE]\\n\\n` 시 generator 종료.

사용 예:
    from app.integrations.agenthub_client import get_agenthub_client

    async def echo():
        client = get_agenthub_client()
        resp = await client.chat(
            agent_code="docutil-rag-chat",
            messages=[{"role": "user", "content": "회사 휴가 정책 알려줘"}],
            temperature=0.5,
        )
        return resp["choices"][0]["message"]["content"]

    async def stream_demo():
        client = get_agenthub_client()
        async for chunk in client.chat_stream(
            agent_code="docutil-rag-chat",
            messages=[{"role": "user", "content": "최근 보고서 요약"}],
        ):
            delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
            print(delta, end="", flush=True)

설정:
    환경변수 `AGENTHUB_URL` (예: http://localhost:5000), `AGENTHUB_API_KEY` 필수.
    본 클라이언트는 `app.core.config.settings` 와 분리되어 환경변수 직접 로드한다 —
    DocUtil S6/S7 진행 중인 환경에서 settings 의존성 충돌 회피.
"""
from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from typing import Any, AsyncIterator, Optional

import httpx

logger = logging.getLogger(__name__)


class AgentHubError(Exception):
    """AgentHub 호출 실패 시 발생. status_code / error_body 첨부."""

    def __init__(self, message: str, *, status_code: Optional[int] = None,
                 error_body: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_body = error_body


class AgentHubClient:
    """
    AgentHub OpenAI 호환 엔드포인트 비동기 클라이언트.

    - `chat()` : 비스트리밍 호출. 단일 dict 응답 (OpenAI ChatCompletion 형식).
    - `chat_stream()` : SSE 스트리밍. dict 비동기 generator (각 chunk 는 ChatCompletionChunk).
    - `aclose()` : 내부 httpx.AsyncClient 종료. FastAPI lifespan 의 shutdown 에서 호출.

    멀티 인스턴스가 필요하면 직접 ``AgentHubClient(...)`` 인스턴스화. 단일 사용은
    `get_agenthub_client()` 싱글턴 사용 권장.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        default_timeout: float = 60.0,
        connect_timeout: float = 10.0,
    ) -> None:
        if not base_url:
            raise ValueError("AgentHub base_url 미설정 — 환경변수 AGENTHUB_URL 확인")
        if not api_key:
            raise ValueError("AgentHub api_key 미설정 — 환경변수 AGENTHUB_API_KEY 확인")

        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        # httpx.AsyncClient 는 connection pool 을 내부 보유 — 인스턴스 재사용이 핵심.
        # FastAPI lifespan(startup) 에서 1회 생성, shutdown 에서 aclose 호출 권장.
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(default_timeout, connect=connect_timeout),
            headers={
                "X-API-Key": self._api_key,
                "Content-Type": "application/json",
                # 호출자(DocUtil/career) 식별 — AgentHub 의 사용량/감사 로그에 기록.
                "User-Agent": "AgentHubClient/1.0 (docutil)",
            },
        )

    # ── public API ──────────────────────────────────────────────────────────

    async def chat(
        self,
        agent_code: str,
        messages: list[dict[str, str]],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        비스트리밍 호출. AgentHub 가 라우팅 정책을 평가한 후 단일 응답을 반환한다.

        :param agent_code: AgentCode UNIQUE 식별자 (예: "docutil-rag-chat").
                           AgentHub 의 OpenAI 호환 엔드포인트는 `model` 필드를 통해
                           Agent 를 식별한다 (R2: AgentHub 내부에서 LLM 모델로 변환).
        :param messages: ChatMessage 리스트. role 은 "user"/"assistant"/"system"/"tool".
        :param temperature / max_tokens: 호출 단위 override. 미지정 시 Agent 정의값 사용.
        :param extra: AgentHub 가 인식하는 추가 파라미터 (예: {"top_p": 0.9}).
        :raises AgentHubError: HTTP 4xx/5xx 또는 네트워크/타임아웃 실패.
        """
        payload: dict[str, Any] = {
            "model": agent_code,
            "messages": messages,
            "stream": False,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if extra:
            payload.update(extra)

        try:
            resp = await self._client.post("/v1/chat/completions", json=payload)
        except httpx.TimeoutException as ex:
            logger.error("AgentHub chat 호출 타임아웃: agent=%s", agent_code)
            raise AgentHubError("AgentHub 응답 시간 초과 — 네트워크 또는 LLM 지연 확인 필요") from ex
        except httpx.RequestError as ex:
            logger.error("AgentHub chat 호출 네트워크 오류: agent=%s err=%s", agent_code, ex)
            raise AgentHubError("AgentHub 서버에 연결할 수 없습니다") from ex

        if resp.status_code >= 400:
            self._raise_for_status(resp)

        try:
            return resp.json()
        except json.JSONDecodeError as ex:
            logger.error("AgentHub chat 응답 JSON 파싱 실패: agent=%s body=%s",
                         agent_code, resp.text[:500])
            raise AgentHubError("AgentHub 응답 형식이 올바르지 않습니다") from ex

    async def chat_stream(
        self,
        agent_code: str,
        messages: list[dict[str, str]],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        SSE 스트리밍 호출. AgentHub 가 chunk 단위로 send 하는 응답을 dict 로 yield 한다.

        SSE 프레임 형식 (AgentHub Phase 3.5/3.5b 진짜 SSE):
            data: {"id":"...","choices":[{"delta":{"content":"안녕"}}]}\\n\\n
            data: [DONE]\\n\\n

        :raises AgentHubError: 스트림 시작 전 HTTP 오류 또는 네트워크 실패.
        """
        payload: dict[str, Any] = {
            "model": agent_code,
            "messages": messages,
            "stream": True,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if extra:
            payload.update(extra)

        try:
            async with self._client.stream(
                "POST", "/v1/chat/completions", json=payload
            ) as response:
                if response.status_code >= 400:
                    # 스트리밍 응답이라도 시작 직후 4xx/5xx 면 본문을 읽어 한국어 에러로 변환.
                    body_bytes = await response.aread()
                    raise self._build_error(response.status_code, body_bytes.decode("utf-8", errors="replace"))

                async for line in response.aiter_lines():
                    # SSE 는 빈 줄(`\\n\\n`)이 chunk 구분자 — aiter_lines 는 빈 줄을 빈 문자열로 yield.
                    if not line:
                        continue
                    if not line.startswith("data: "):
                        # 주석(`: ping`) 또는 비표준 라인 — 무시.
                        continue
                    payload_str = line[len("data: "):].strip()
                    if payload_str == "[DONE]":
                        return
                    try:
                        chunk = json.loads(payload_str)
                    except json.JSONDecodeError:
                        logger.warning("AgentHub SSE chunk JSON 파싱 실패: %r", payload_str[:200])
                        continue
                    yield chunk
        except httpx.TimeoutException as ex:
            logger.error("AgentHub chat_stream 타임아웃: agent=%s", agent_code)
            raise AgentHubError("AgentHub 스트리밍 응답 시간 초과") from ex
        except httpx.RequestError as ex:
            logger.error("AgentHub chat_stream 네트워크 오류: agent=%s err=%s", agent_code, ex)
            raise AgentHubError("AgentHub 스트리밍 서버에 연결할 수 없습니다") from ex

    async def aclose(self) -> None:
        """내부 httpx.AsyncClient 의 connection pool 을 종료한다 (lifespan shutdown)."""
        await self._client.aclose()

    # ── 내부 ────────────────────────────────────────────────────────────────

    @staticmethod
    def _raise_for_status(resp: httpx.Response) -> None:
        """4xx/5xx 응답을 한국어 메시지의 AgentHubError 로 변환."""
        try:
            body = resp.json()
        except json.JSONDecodeError:
            body = None
        raise AgentHubClient._build_error_from_response(resp.status_code, resp.text, body)

    @staticmethod
    def _build_error(status_code: int, raw_body: str) -> "AgentHubError":
        try:
            body = json.loads(raw_body)
        except json.JSONDecodeError:
            body = None
        return AgentHubClient._build_error_from_response(status_code, raw_body, body)

    @staticmethod
    def _build_error_from_response(
        status_code: int, raw_body: str, body: Optional[dict[str, Any]]
    ) -> "AgentHubError":
        # AgentHub 의 ErrorResponseDto 형식 (한국어 message + errorCode) 우선 사용.
        if isinstance(body, dict) and isinstance(body.get("message"), str):
            msg = body["message"]
        else:
            # 폴백: 상태 코드별 한국어 메시지.
            mapping = {
                401: "AgentHub 인증 실패 — API Key 확인 필요",
                403: "AgentHub 권한 부족 — Agent 호출 스코프/ConsumerSystems 화이트리스트 확인",
                404: "AgentHub 자원 미존재 — AgentCode 또는 엔드포인트 확인",
                429: "AgentHub Rate Limit 초과 — 잠시 후 재시도하세요",
                502: "AgentHub 가 외부 LLM 호출에 실패했습니다",
                503: "AgentHub 일시적 사용 불가 — 잠시 후 재시도",
                504: "AgentHub Gateway Timeout — LLM 응답 지연",
            }
            msg = mapping.get(
                status_code,
                f"AgentHub 호출 실패 (HTTP {status_code}). body 일부: {raw_body[:200]}",
            )
        logger.error("AgentHub 호출 실패: status=%s body=%s", status_code, raw_body[:500])
        return AgentHubError(msg, status_code=status_code, error_body=body)


# ── 싱글턴 헬퍼 ─────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_agenthub_client() -> AgentHubClient:
    """
    프로세스 단위 AgentHubClient 싱글턴.

    httpx.AsyncClient 는 connection pool 을 내부 보유하므로 인스턴스 재사용이 권장된다.
    FastAPI lifespan(startup) 에서 본 함수를 1회 호출하여 워밍업하고, shutdown 에서
    `await get_agenthub_client().aclose()` 로 정리.

    환경변수:
        AGENTHUB_URL     : AgentHub 베이스 URL (예: http://localhost:5000)
        AGENTHUB_API_KEY : ApiKeyAuthService 로 발급된 평문 키 (`ak-...`)
    """
    base_url = os.environ.get("AGENTHUB_URL", "").strip()
    api_key = os.environ.get("AGENTHUB_API_KEY", "").strip()
    return AgentHubClient(base_url=base_url, api_key=api_key)
