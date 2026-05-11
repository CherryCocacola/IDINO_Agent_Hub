"""Phase 4 S1 D5 — LLMClient.generate_with_schema 교차 프로바이더 테스트.

4 프로바이더 × 3 시나리오 = 12 정상 케이스 + 실패 케이스 (잘못된 JSON,
schema 위반) 최소 1 건씩.

**실 API 호출 금지** — 모든 외부 호출을 monkeypatch 로 대체한다.
검증 대상:
    1. 각 클라이언트가 프로바이더별로 올바른 스키마 표현을 구성하는가?
       (OpenAI strict, Gemini flattened, Claude tool_use, vLLM 원본).
    2. mock 응답이 Pydantic 모델로 정확히 파싱되는가?
    3. Discriminated Union (DocumentSchema 일부) 이 프로바이더별로 올바르게
       처리되는가? — R1 리스크 검증.

참조:
- backend/app/integrations/llm/client.py — LLMClient ABC.
- backend/app/integrations/llm/{openai,azure,gemini,claude,vllm}_client.py
- backend/app/integrations/llm/schema_adapter.py
- docs/phase3_execution_roadmap.md §2.1 S1 D5
"""

from __future__ import annotations

import json as json_module
from typing import Annotated, Literal
from uuid import UUID  # noqa: TC003  # Pydantic 모델 필드에서 런타임 참조됨

import httpx
import pytest
from pydantic import BaseModel, Field, ValidationError

# Phase 7 — R2 완전 보강 (2026-05-11): claude_client / gemini_client 모듈이 dead code
# 로 판정되어 삭제됨. 본 테스트는 Phase 4 S1 D5 cross-provider 시점의 obsolete 검증으로,
# Phase 7.3 이후 factory 가 ``AgentHubLLMWrapper`` 만 반환하므로 의미를 상실했다.
# 모듈 로딩 자체가 실패하지 않도록 ``pytest.importorskip`` 으로 collection 단계에서 skip.
pytest.importorskip(
    "app.integrations.llm.claude_client",
    reason="Phase 7 (2026-05-11) claude_client.py removed — cross-provider tests obsolete",
)
pytest.importorskip(
    "app.integrations.llm.gemini_client",
    reason="Phase 7 (2026-05-11) gemini_client.py removed — cross-provider tests obsolete",
)

from app.integrations.llm.azure_client import AzureOpenAIClient
from app.integrations.llm.claude_client import ClaudeClient  # noqa: E402  # importorskip 후
from app.integrations.llm.client import OpenAIClient  # noqa: E402
from app.integrations.llm.gemini_client import GeminiClient  # noqa: E402
from app.integrations.llm.schema_adapter import (  # noqa: E402
    provider_capability_report,
    pydantic_to_claude_tool,
    pydantic_to_gemini_schema,
    pydantic_to_openai_schema,
    pydantic_to_vllm_schema,
    validate_structured_output,
)

# pytest-asyncio Mode.AUTO 로 구성되어 있어 async def 는 자동으로 asyncio
# 실행된다 (pyproject.toml 설정). 전역 pytestmark 를 두면 동기 테스트에까지
# asyncio 마크가 적용되어 경고가 발생하므로 개별 async 메서드는 @pytest.mark.asyncio
# 를 명시하거나 pyproject.toml 의 AUTO 설정에 의존한다.


# ---------------------------------------------------------------------------
# 시나리오 스키마 정의
# ---------------------------------------------------------------------------
#
# 세 시나리오는 각각 다음 JSON Schema 특성을 노출한다:
#   1. SimpleSchema         — flat object (baseline)
#   2. DiscriminatedUnion   — oneOf + discriminator ("type")
#   3. NestedSchema         — list[Inner] (단순 중첩)


class SimpleSchema(BaseModel):
    """시나리오 1: 단순 flat 스키마."""

    name: str = Field(..., min_length=1)
    age: int = Field(..., ge=0, le=150)


class TextBlock(BaseModel):
    """Discriminated union variant 1 — Paragraph 유사."""

    type: Literal["text"] = "text"
    text: str = Field(..., min_length=1)


class NumberBlock(BaseModel):
    """Discriminated union variant 2 — KPI 유사."""

    type: Literal["number"] = "number"
    label: str
    value: float


class ListBlock(BaseModel):
    """Discriminated union variant 3 — BulletList 유사."""

    type: Literal["list"] = "list"
    items: list[str] = Field(..., min_length=1)


Block = Annotated[
    TextBlock | NumberBlock | ListBlock,
    Field(discriminator="type"),
]


class DiscriminatedSchema(BaseModel):
    """시나리오 2: Pydantic v2 Discriminated Union (R1 검증 대상)."""

    document_id: UUID
    blocks: list[Block] = Field(..., min_length=1, max_length=5)


class InnerItem(BaseModel):
    """중첩 스키마의 내부 모델."""

    id: str
    weight: float


class NestedSchema(BaseModel):
    """시나리오 3: 단순 list[Inner] 중첩."""

    title: str
    items: list[InnerItem] = Field(..., min_length=1)


# ---------------------------------------------------------------------------
# 각 시나리오의 예상 정답 dict — mock 응답으로 사용.
# ---------------------------------------------------------------------------

SIMPLE_VALID = {"name": "Alice", "age": 30}

DISCRIMINATED_VALID = {
    "document_id": "11111111-2222-3333-4444-555555555555",
    "blocks": [
        {"type": "text", "text": "소개 문장"},
        {"type": "number", "label": "매출", "value": 12.5},
        {"type": "list", "items": ["A", "B", "C"]},
    ],
}

NESTED_VALID = {
    "title": "지표 요약",
    "items": [
        {"id": "k1", "weight": 0.25},
        {"id": "k2", "weight": 0.75},
    ],
}


SCENARIOS: list[tuple[str, type[BaseModel], dict]] = [
    ("simple", SimpleSchema, SIMPLE_VALID),
    ("discriminated", DiscriminatedSchema, DISCRIMINATED_VALID),
    ("nested", NestedSchema, NESTED_VALID),
]


# ---------------------------------------------------------------------------
# 공통 httpx mock 헬퍼
# ---------------------------------------------------------------------------
#
# OpenAICompatibleClient 계열 (OpenAI / Azure / Gemini / vLLM) 은 httpx.AsyncClient
# 로 POST 한다. mock 은 httpx.AsyncClient.post 를 monkeypatch 하여 기록된 페이로드를
# 검증하고, mock 응답을 반환한다.


class _MockResponse:
    """httpx.Response 최소 대체."""

    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"status {self.status_code}",
                request=httpx.Request("POST", "http://mock"),
                response=httpx.Response(self.status_code),
            )

    def json(self) -> dict:
        return self._payload


def _wrap_chat_completion(structured_dict: dict) -> dict:
    """OpenAI /chat/completions 응답 envelope 로 감싼다.

    Structured Outputs 는 message.content 에 JSON string 을 넣는다.
    """
    return {
        "id": "mock-id",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": json_module.dumps(structured_dict),
                },
                "finish_reason": "stop",
            }
        ],
    }


@pytest.fixture
def httpx_recorder(monkeypatch):
    """httpx.AsyncClient.post 를 가로채 요청 페이로드를 기록하고 mock 응답을 반환.

    Yields
    ------
    dict
        {
          "calls": [ {url, json, headers}, ... ],
          "set_response": callable(dict) -> None  # mock 응답 JSON 설정,
          "set_status": callable(int) -> None,
          "set_content": callable(str) -> None    # message.content 를 raw 로 override,
        }
    """
    state: dict = {
        "calls": [],
        "response_payload": None,
        "status": 200,
        "raw_content": None,  # None 이면 response_payload 사용, str 이면 content 에 주입
    }

    async def fake_post(self, url, *, json=None, headers=None, **kwargs):  # noqa: A002
        state["calls"].append({"url": url, "json": json, "headers": headers})
        if state["raw_content"] is not None:
            envelope = {"choices": [{"message": {"role": "assistant", "content": state["raw_content"]}}]}
            return _MockResponse(envelope, state["status"])
        return _MockResponse(
            _wrap_chat_completion(state["response_payload"] or {}),
            state["status"],
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    def set_response(payload: dict) -> None:
        state["response_payload"] = payload
        state["raw_content"] = None

    def set_status(code: int) -> None:
        state["status"] = code

    def set_content(raw: str) -> None:
        state["raw_content"] = raw

    return {
        "calls": state["calls"],
        "set_response": set_response,
        "set_status": set_status,
        "set_content": set_content,
    }


# ---------------------------------------------------------------------------
# Claude mock — anthropic SDK 의 AsyncAnthropic 을 MagicMock 으로 교체
# ---------------------------------------------------------------------------


class _ClaudeToolUseBlock:
    """Claude messages.content[i] 의 tool_use 블록 최소 stub."""

    def __init__(self, payload: dict) -> None:
        self.type = "tool_use"
        self.input = payload
        self.name = "structured_output"


class _ClaudeMessagesResponse:
    """Claude messages.create 반환값 stub."""

    def __init__(self, payload: dict) -> None:
        self.content = [_ClaudeToolUseBlock(payload)]


@pytest.fixture
def claude_recorder(monkeypatch):
    """ClaudeClient._create_async_client 를 monkeypatch.

    반환된 dict 는 최근 호출의 kwargs 를 보관한다.
    ``set_response(dict)`` 로 tool_use.input 에 들어갈 값을 설정한다.
    """
    state: dict = {"calls": [], "response_payload": None, "raise_exc": None}

    class _FakeMessages:
        async def create(self_inner, **kwargs):  # noqa: N805
            state["calls"].append(kwargs)
            if state["raise_exc"] is not None:
                raise state["raise_exc"]
            return _ClaudeMessagesResponse(state["response_payload"] or {})

    class _FakeAsyncClient:
        def __init__(self) -> None:
            self.messages = _FakeMessages()

    def fake_create_async(self) -> _FakeAsyncClient:
        return _FakeAsyncClient()

    monkeypatch.setattr(ClaudeClient, "_create_async_client", fake_create_async)

    def set_response(payload: dict) -> None:
        state["response_payload"] = payload

    def set_exception(exc: Exception | None) -> None:
        state["raise_exc"] = exc

    return {
        "calls": state["calls"],
        "set_response": set_response,
        "set_exception": set_exception,
    }


# ---------------------------------------------------------------------------
# 클라이언트 인스턴스 fixture (환경변수 없이 dummy 로 초기화)
# ---------------------------------------------------------------------------


@pytest.fixture
def openai_client():
    return OpenAIClient(api_key="sk-test", model="gpt-4o")


@pytest.fixture
def azure_client():
    # Azure 는 settings 에서 endpoint/deployment 를 가져오려 하므로
    # 명시적으로 전달하여 settings 의존성 제거.
    return AzureOpenAIClient(
        api_key="az-test",
        deployment="gpt-4o",
        endpoint="https://mockazure.openai.azure.com",
        api_version="2024-08-01-preview",
    )


@pytest.fixture
def gemini_client():
    return GeminiClient(api_key="google-test", model="gemini-2.0-flash")


@pytest.fixture
def claude_client():
    # anthropic SDK 가 설치되지 않은 환경에서도 테스트가 돌 수 있도록
    # ClaudeClient 초기화 시 _ensure_anthropic_installed 를 우회.
    pytest.importorskip("anthropic")
    return ClaudeClient(api_key="ant-test", model="claude-sonnet-4-20250514")


# ---------------------------------------------------------------------------
# schema_adapter 단위 검증
# ---------------------------------------------------------------------------


class TestSchemaAdapter:
    """schema_adapter 의 프로바이더별 변환 결과를 검증한다."""

    def test_openai_schema_preserves_strict_and_refs(self):
        result = pydantic_to_openai_schema(DiscriminatedSchema)
        assert result["strict"] is True
        assert result["name"] == "DiscriminatedSchema"
        # Pydantic v2 는 union 을 $defs + $ref 로 표현 — OpenAI strict 는 이를 허용
        schema = result["schema"]
        as_json = json_module.dumps(schema)
        assert "$defs" in as_json or "oneOf" in as_json or "anyOf" in as_json

    def test_gemini_schema_removes_unions_and_refs(self):
        """Gemini 어댑터가 oneOf/anyOf/$ref 를 모두 제거해야 한다."""
        flat = pydantic_to_gemini_schema(DiscriminatedSchema)
        as_json = json_module.dumps(flat)
        assert "$ref" not in as_json, "Gemini 스키마에 $ref 가 남아있음"
        assert "$defs" not in as_json, "Gemini 스키마에 $defs 가 남아있음"
        assert "oneOf" not in as_json, "Gemini 스키마에 oneOf 가 남아있음"
        assert "anyOf" not in as_json, "Gemini 스키마에 anyOf 가 남아있음"
        # discriminator 값들은 type enum 으로 통합되어야 함
        blocks = flat["properties"]["blocks"]
        item_schema = blocks["items"]
        assert "type" in item_schema["properties"]
        type_prop = item_schema["properties"]["type"]
        # flattened 후에는 enum 형태로 존재
        assert type_prop.get("enum") == sorted(["text", "number", "list"])

    def test_claude_tool_has_input_schema(self):
        tool = pydantic_to_claude_tool(SimpleSchema)
        assert tool["name"] == "structured_output"
        assert "input_schema" in tool
        assert tool["input_schema"]["type"] == "object"
        assert set(tool["input_schema"]["required"]) == {"name", "age"}

    def test_vllm_schema_is_inlined(self):
        flat = pydantic_to_vllm_schema(DiscriminatedSchema)
        as_json = json_module.dumps(flat)
        # vLLM 은 $ref 를 inline 한다 (guided_json 엔진 호환성)
        assert "$ref" not in as_json
        assert "$defs" not in as_json
        # 하지만 oneOf/anyOf 는 보존되어야 함 (XGrammar 가 지원)
        assert "oneOf" in as_json or "anyOf" in as_json

    def test_validate_accepts_dict(self):
        result = validate_structured_output({"name": "Bob", "age": 25}, SimpleSchema)
        assert isinstance(result, SimpleSchema)
        assert result.name == "Bob"

    def test_validate_accepts_json_string(self):
        result = validate_structured_output('{"name":"Bob","age":25}', SimpleSchema)
        assert isinstance(result, SimpleSchema)

    def test_validate_rejects_schema_violation(self):
        """실패 케이스 1: schema 를 위반한 응답은 ValidationError 를 낸다."""
        with pytest.raises(ValidationError):
            validate_structured_output({"name": "Bob"}, SimpleSchema)  # age 누락

    def test_validate_rejects_invalid_json(self):
        """실패 케이스 2: 잘못된 JSON 문자열은 ValueError."""
        with pytest.raises(ValueError, match="유효한 JSON"):
            validate_structured_output("{not json", SimpleSchema)

    def test_provider_capability_report_shape(self):
        report = provider_capability_report()
        assert set(report.keys()) == {"openai", "azure_openai", "gemini", "anthropic", "vllm"}
        for _name, caps in report.items():
            assert "discriminated_union" in caps
            assert "note" in caps

    # ------------------------------------------------------------------
    # H11 핫픽스 검증 — OpenAI strict 모드 Optional 필드 처리
    # ------------------------------------------------------------------
    #
    # D7 실 API 검증에서 발견된 400 Bad Request:
    #   "required is required to include every key in properties. Missing 'status'."
    # Pydantic v2 의 Optional 필드가 required 에서 제외되어 발생. H11 은
    # pydantic_to_openai_schema(strict=True) 에 후처리를 추가하여 해결한다.

    def test_openai_strict_includes_optional_fields_in_required(self):
        """H11-1: Optional 필드도 required 배열에 포함되고 anyOf 로 null 허용되어야 한다.

        OpenAI strict 는 ``type`` 배열에 null 을 섞는 방식보다 ``anyOf`` 래핑을
        안전하게 지원하므로 본 구현은 anyOf 경로로 통일한다.
        """

        class ModelWithOptional(BaseModel):
            """필수 name + optional age/nickname 을 갖는 모델."""

            name: str
            age: int | None = None
            nickname: str | None = None

        result = pydantic_to_openai_schema(ModelWithOptional, strict=True)
        schema = result["schema"]
        assert set(schema["required"]) == {"name", "age", "nickname"}, (
            "OpenAI strict 모드는 Optional 필드도 required 에 포함되어야 함"
        )
        assert schema["additionalProperties"] is False, "strict 모드는 additionalProperties=false 필수"

        # Optional 필드는 anyOf 에 {"type": "null"} variant 가 있어야 한다.
        age_prop = schema["properties"]["age"]
        age_variants = age_prop.get("anyOf") or age_prop.get("oneOf") or []
        age_has_null = any(isinstance(v, dict) and v.get("type") == "null" for v in age_variants)
        assert age_has_null, f"Optional int 필드는 anyOf 에 null variant 필요. age={age_prop}"

        # required 필드 (name) 는 null 허용을 강제로 추가하지 않음.
        name_prop = schema["properties"]["name"]
        name_variants = name_prop.get("anyOf") or name_prop.get("oneOf") or []
        name_has_null = any(isinstance(v, dict) and v.get("type") == "null" for v in name_variants)
        assert not name_has_null, "required 필드 name 에 null variant 가 자동 추가되면 안 됨"
        assert name_prop.get("type") == "string", (
            f"required string 필드의 type 은 단일 문자열이어야 함. name={name_prop}"
        )

    def test_openai_strict_discriminated_union_variants_enforced(self):
        """H11-2: Discriminated Union 내부 variant 의 Optional 필드도 strict 보정을 받아야 한다."""

        class StatusBlock(BaseModel):
            """Union variant — assignee 가 optional."""

            type: Literal["status"] = "status"
            label: str
            assignee: str | None = None  # optional — H11 대상

        class NoteBlock(BaseModel):
            """Union variant — comment 가 optional."""

            type: Literal["note"] = "note"
            body: str
            comment: str | None = None  # optional — H11 대상

        UnionBlock = Annotated[
            StatusBlock | NoteBlock,
            Field(discriminator="type"),
        ]

        class ContainerModel(BaseModel):
            """Discriminated Union 을 포함한 래퍼."""

            blocks: list[UnionBlock] = Field(..., min_length=1)

        result = pydantic_to_openai_schema(ContainerModel, strict=True)
        schema = result["schema"]
        # 최상위 object 는 blocks 만 required 로 보유.
        assert schema["required"] == ["blocks"]
        assert schema["additionalProperties"] is False

        # blocks.items 는 oneOf / anyOf 둘 중 하나로 표현됨 — 각 variant 를 확인.
        items = schema["properties"]["blocks"]["items"]
        variants = items.get("oneOf") or items.get("anyOf") or []
        assert variants, f"Discriminated Union 의 items 에 oneOf/anyOf 가 있어야 함: {items}"

        # 각 variant 의 required 는 properties 전체 키여야 하며
        # additionalProperties=false 가 적용되어야 한다.
        for variant in variants:
            assert isinstance(variant, dict)
            assert variant.get("additionalProperties") is False, (
                f"variant 에 additionalProperties=false 필요: {variant}"
            )
            if "properties" in variant:
                props_keys = set(variant["properties"].keys())
                required_keys = set(variant.get("required") or [])
                assert props_keys == required_keys, (
                    f"variant 의 required 가 properties 와 일치하지 않음. props={props_keys}, required={required_keys}"
                )

    def test_openai_strict_inlines_defs_and_applies_recursively(self):
        """H11-3: $defs 는 인라인되고, 중첩 object 에도 strict 보정이 재귀 적용되어야 한다."""

        class InnerDetail(BaseModel):
            """중첩 객체 — status 가 optional."""

            key: str
            status: str | None = None  # optional

        class OuterModel(BaseModel):
            """Outer — detail 은 required, note 는 optional."""

            title: str
            detail: InnerDetail
            note: str | None = None

        result = pydantic_to_openai_schema(OuterModel, strict=True)
        schema = result["schema"]
        as_json = json_module.dumps(schema)

        # $defs 는 인라인되어 사라져야 함 (H11 의 _resolve_refs 선행 호출)
        assert "$defs" not in as_json, "H11 strict 변환 후 $defs 가 남아있으면 안 됨 (인라인 보장)"
        assert "$ref" not in as_json, "$ref 도 모두 인라인되어야 함"

        # 최상위 required = [title, detail, note]
        assert set(schema["required"]) == {"title", "detail", "note"}
        assert schema["additionalProperties"] is False

        # 중첩 object (detail) 에도 strict 보정이 적용되어야 한다.
        detail_schema = schema["properties"]["detail"]
        # Pydantic 이 inner 를 anyOf/단일 object 로 표현할 수 있음 — object 노드를 찾는다.
        object_node = detail_schema
        if "anyOf" in detail_schema:
            # Optional 이 아닌 required 라서 일반적으로 단일 object 지만,
            # Pydantic 버전에 따라 anyOf 가 쓰일 수도 있음. 첫 object 를 추출.
            for v in detail_schema["anyOf"]:
                if isinstance(v, dict) and v.get("type") == "object":
                    object_node = v
                    break
        assert object_node.get("type") == "object"
        assert set(object_node["required"]) == {"key", "status"}, "중첩 object 의 optional 필드도 strict 보정 대상"
        assert object_node["additionalProperties"] is False

    # ------------------------------------------------------------------
    # H12 핫픽스 — OpenAI strict 미지원 키워드 제거 (D8, 2026-04-22)
    # ------------------------------------------------------------------
    #
    # D7 실 API 호출에서 ``required`` 누락 외에도 ``pattern`` / ``minLength`` /
    # ``maxItems`` 같은 JSON Schema 제약 키워드가 strict 모드에서 400 을
    # 유발함이 관측됨. OpenAI strict 는 JSON Schema subset 만 허용하며,
    # 다음 키워드는 **모두 제거**해야 한다:
    #
    # - 문자열: ``minLength`` / ``maxLength`` / ``pattern`` / ``format``
    # - 숫자 : ``minimum`` / ``maximum`` / ``multipleOf`` 등
    # - 배열 : ``minItems`` / ``maxItems`` / ``uniqueItems`` 등
    # - 객체 : ``patternProperties`` / ``propertyNames`` 등
    # - 기타 : ``default``, ``$schema``
    #
    # 제약 손실에 대한 안전성: 응답은 ``validate_structured_output`` 에서
    # 원본 Pydantic 모델로 재검증되므로 무결성은 유지된다.

    def test_openai_strict_strips_unsupported_constraint_keywords(self):
        """H12-1: strict 모드 스키마에서 pattern/min*/max* 등 제약 키워드가 제거되어야 한다.

        Pydantic v2 는 Field 제약 (min_length, max_length, pattern, ge, le 등)
        을 JSON Schema 로 직렬화하는데, OpenAI strict 는 이들을 거부하므로
        호출 전에 제거해야 한다.
        """

        class StrictlyConstrained(BaseModel):
            """다양한 제약 키워드가 들어가도록 구성."""

            name: str = Field(..., min_length=1, max_length=80, pattern=r"^[A-Z][a-z]+$")
            age: int = Field(..., ge=0, le=150)
            tags: list[str] = Field(..., min_length=1, max_length=5)
            email: str = Field(..., max_length=200)

        result = pydantic_to_openai_schema(StrictlyConstrained, strict=True)
        as_json = json_module.dumps(result["schema"])

        # 문자열 제약
        assert "minLength" not in as_json, "minLength 가 strict 스키마에 남아있음"
        assert "maxLength" not in as_json, "maxLength 가 strict 스키마에 남아있음"
        assert "pattern" not in as_json, "pattern 이 strict 스키마에 남아있음"
        # 숫자 제약
        assert "minimum" not in as_json, "minimum 이 strict 스키마에 남아있음"
        assert "maximum" not in as_json, "maximum 이 strict 스키마에 남아있음"
        # 배열 제약
        assert "minItems" not in as_json, "minItems 가 strict 스키마에 남아있음"
        assert "maxItems" not in as_json, "maxItems 가 strict 스키마에 남아있음"

    def test_openai_strict_strips_default_keyword(self):
        """H12-2: Pydantic 기본값으로 생성되는 ``default`` 키가 제거되어야 한다.

        OpenAI strict 는 ``default`` 를 허용하지 않는다. 서버는 응답 후
        Pydantic 재검증 단계에서 기본값을 자동 주입하므로 정보 손실은 없다.
        """

        class WithDefaults(BaseModel):
            """기본값이 풍부한 모델."""

            title: str
            numbered: bool = False
            emphasis: Literal["normal", "bold"] = "normal"
            rank: int = 10

        result = pydantic_to_openai_schema(WithDefaults, strict=True)
        as_json = json_module.dumps(result["schema"])
        assert '"default"' not in as_json, "default 키워드가 strict 스키마에 남아있음"

    def test_openai_strict_document_schema_passes_api_rules(self):
        """H12-3: 실제 DocumentSchema 가 OpenAI strict 규정을 완전히 만족해야 한다.

        D7 live API 에서 400 을 유발한 실 케이스를 회귀 테스트로 고정한다.
        규정:
            - 모든 object 는 required=모든 키 + additionalProperties=false.
            - 미지원 키워드 (pattern/min*/max*/default 등) 가 스키마에 없어야 함.
            - oneOf / discriminator 가 없어야 함.
        """

        from app.modules.documents_v2.schemas import DocumentSchema as _DocSchema

        result = pydantic_to_openai_schema(_DocSchema, strict=True)
        schema = result["schema"]
        as_json = json_module.dumps(schema)

        # 미지원 키워드 0건
        unsupported = {
            "minLength",
            "maxLength",
            "pattern",
            "format",
            "minimum",
            "maximum",
            "exclusiveMinimum",
            "exclusiveMaximum",
            "multipleOf",
            "minItems",
            "maxItems",
            "uniqueItems",
            "minProperties",
            "maxProperties",
            "default",
            "$schema",
            "oneOf",
            "discriminator",
        }
        for kw in unsupported:
            assert f'"{kw}"' not in as_json, f"DocumentSchema strict 출력에 '{kw}' 가 남아있음"

        # 모든 object 노드의 required == properties 키 전체
        def _check_object(node: object, path: str = "root") -> None:
            if isinstance(node, dict):
                if node.get("type") == "object":
                    props = set((node.get("properties") or {}).keys())
                    req = set(node.get("required") or [])
                    assert props == req, f"{path}: required({sorted(req)}) != properties({sorted(props)})"
                    assert node.get("additionalProperties") is False, f"{path}: additionalProperties 가 false 가 아님"
                for k, v in node.items():
                    _check_object(v, f"{path}.{k}")
            elif isinstance(node, list):
                for i, v in enumerate(node):
                    _check_object(v, f"{path}[{i}]")

        _check_object(schema)


# ---------------------------------------------------------------------------
# 12 케이스 교차 테스트 — OpenAI
# ---------------------------------------------------------------------------


class TestOpenAIStructured:
    """OpenAI 는 strict json_schema 모드로 원본 스키마를 그대로 사용."""

    @pytest.mark.parametrize(
        ("scenario_name", "schema", "valid_payload"),
        SCENARIOS,
        ids=[s[0] for s in SCENARIOS],
    )
    async def test_generate_with_schema_happy_path(
        self,
        openai_client,
        httpx_recorder,
        scenario_name,
        schema,
        valid_payload,
    ):
        httpx_recorder["set_response"](valid_payload)
        result = await openai_client.generate_with_schema(
            system_prompt="너는 JSON 생성기.",
            user_prompt=f"{scenario_name} 케이스를 생성해줘.",
            response_schema=schema,
            temperature=0.0,
        )
        assert isinstance(result, schema)
        # 요청 페이로드 검증: response_format 에 strict json_schema 가 있는지
        calls = httpx_recorder["calls"]
        assert len(calls) == 1
        req = calls[0]["json"]
        assert req["model"] == "gpt-4o"
        assert req["temperature"] == 0.0
        rf = req["response_format"]
        assert rf["type"] == "json_schema"
        assert rf["json_schema"]["strict"] is True
        assert rf["json_schema"]["name"] == schema.__name__

    async def test_schema_violation_raises(self, openai_client, httpx_recorder):
        """OpenAI 가 schema 를 위반한 응답을 (가상으로) 반환하면 ValidationError."""
        httpx_recorder["set_response"]({"name": "only_name"})  # age 누락
        with pytest.raises(ValidationError):
            await openai_client.generate_with_schema(
                system_prompt="s",
                user_prompt="u",
                response_schema=SimpleSchema,
            )

    async def test_invalid_json_raises(self, openai_client, httpx_recorder):
        """message.content 가 JSON 이 아닐 때 ValueError 혹은 JSONDecodeError."""
        httpx_recorder["set_content"]("not json at all {{{")
        with pytest.raises((ValueError, json_module.JSONDecodeError)):
            await openai_client.generate_with_schema(
                system_prompt="s",
                user_prompt="u",
                response_schema=SimpleSchema,
            )


# ---------------------------------------------------------------------------
# 12 케이스 교차 테스트 — Azure OpenAI
# ---------------------------------------------------------------------------


class TestAzureStructured:
    """Azure 는 OpenAI 와 동일 response_format 이지만 URL/headers 가 다름."""

    @pytest.mark.parametrize(
        ("scenario_name", "schema", "valid_payload"),
        SCENARIOS,
        ids=[s[0] for s in SCENARIOS],
    )
    async def test_generate_with_schema_happy_path(
        self,
        azure_client,
        httpx_recorder,
        scenario_name,
        schema,
        valid_payload,
    ):
        httpx_recorder["set_response"](valid_payload)
        result = await azure_client.generate_with_schema(
            system_prompt="s",
            user_prompt=f"{scenario_name}",
            response_schema=schema,
        )
        assert isinstance(result, schema)
        calls = httpx_recorder["calls"]
        assert len(calls) == 1
        call = calls[0]
        # Azure: URL 에 api-version 쿼리 + api-key 헤더
        assert "?api-version=2024-08-01-preview" in call["url"]
        assert "mockazure.openai.azure.com" in call["url"]
        assert call["headers"].get("api-key") == "az-test"
        # Authorization 헤더는 Azure 에서 사용되지 않아야 함
        assert "Authorization" not in call["headers"]


# ---------------------------------------------------------------------------
# 12 케이스 교차 테스트 — Gemini
# ---------------------------------------------------------------------------


class TestGeminiStructured:
    """Gemini 는 schema 평탄화 후 전송 + Pydantic 재검증."""

    @pytest.mark.parametrize(
        ("scenario_name", "schema", "valid_payload"),
        SCENARIOS,
        ids=[s[0] for s in SCENARIOS],
    )
    async def test_generate_with_schema_happy_path(
        self,
        gemini_client,
        httpx_recorder,
        scenario_name,
        schema,
        valid_payload,
    ):
        httpx_recorder["set_response"](valid_payload)
        result = await gemini_client.generate_with_schema(
            system_prompt="s",
            user_prompt=f"{scenario_name}",
            response_schema=schema,
        )
        assert isinstance(result, schema)
        calls = httpx_recorder["calls"]
        assert len(calls) == 1
        sent_schema = calls[0]["json"]["response_format"]["json_schema"]["schema"]
        sent_json = json_module.dumps(sent_schema)
        # Gemini 전용 평탄화 확인: oneOf/anyOf/$ref 없음
        assert "$ref" not in sent_json
        assert "oneOf" not in sent_json
        assert "anyOf" not in sent_json

    async def test_discriminated_union_flattens_but_still_validates(self, gemini_client, httpx_recorder):
        """Gemini 는 union 을 평탄화하지만, 응답이 원본 스키마를 만족하면 검증 통과.

        이 테스트가 R1 리스크의 핵심 성공 경로를 확증한다:
        Gemini 가 평탄화된 스키마를 받고도 올바른 variant 의 응답을 반환하면
        Pydantic 재검증이 원래의 Discriminated Union 을 성공적으로 파싱한다.
        """
        httpx_recorder["set_response"](DISCRIMINATED_VALID)
        result = await gemini_client.generate_with_schema(
            system_prompt="s",
            user_prompt="u",
            response_schema=DiscriminatedSchema,
        )
        assert len(result.blocks) == 3
        assert result.blocks[0].type == "text"
        assert result.blocks[1].type == "number"
        assert result.blocks[2].type == "list"

    async def test_discriminated_union_bad_variant_raises(self, gemini_client, httpx_recorder):
        """Gemini 가 평탄화로 인해 type 필드 없이 응답하면 ValidationError.

        R1 리스크 시나리오: Gemini 가 union 을 완전히 준수하지 못할 때
        우리는 ValidationError 로 감지하고 상위 레이어에서 재시도해야 한다.
        """
        bad_payload = {
            "document_id": "11111111-2222-3333-4444-555555555555",
            "blocks": [{"text": "type 필드가 빠진 variant"}],  # type 누락
        }
        httpx_recorder["set_response"](bad_payload)
        with pytest.raises(ValidationError):
            await gemini_client.generate_with_schema(
                system_prompt="s",
                user_prompt="u",
                response_schema=DiscriminatedSchema,
            )


# ---------------------------------------------------------------------------
# 12 케이스 교차 테스트 — Claude
# ---------------------------------------------------------------------------


class TestClaudeStructured:
    """Claude 는 Tool Use 패턴 — anthropic SDK 의 messages.create 를 mock."""

    @pytest.mark.parametrize(
        ("scenario_name", "schema", "valid_payload"),
        SCENARIOS,
        ids=[s[0] for s in SCENARIOS],
    )
    async def test_generate_with_schema_happy_path(
        self,
        claude_client,
        claude_recorder,
        scenario_name,
        schema,
        valid_payload,
    ):
        claude_recorder["set_response"](valid_payload)
        result = await claude_client.generate_with_schema(
            system_prompt="너는 JSON 생성기",
            user_prompt=f"{scenario_name}",
            response_schema=schema,
        )
        assert isinstance(result, schema)
        calls = claude_recorder["calls"]
        assert len(calls) == 1
        kwargs = calls[0]
        # Tool Use 검증
        assert "tools" in kwargs
        assert len(kwargs["tools"]) == 1
        assert kwargs["tools"][0]["name"] == "structured_output"
        assert kwargs["tool_choice"] == {"type": "tool", "name": "structured_output"}
        # system prompt 는 별도 파라미터로 분리되어야 함
        assert kwargs["system"] == "너는 JSON 생성기"
        # messages 에는 user 만
        assert kwargs["messages"] == [{"role": "user", "content": f"{scenario_name}"}]

    async def test_schema_violation_raises(self, claude_client, claude_recorder):
        """Claude 의 tool_use.input 이 schema 를 위반하면 ValidationError."""
        claude_recorder["set_response"]({"name": "only_name"})
        with pytest.raises(ValidationError):
            await claude_client.generate_with_schema(
                system_prompt="s",
                user_prompt="u",
                response_schema=SimpleSchema,
            )

    async def test_missing_tool_use_block_raises(self, claude_client, claude_recorder):
        """실패 케이스: Claude 가 tool_use 블록 없이 텍스트만 반환하면 ValueError."""
        # _ClaudeMessagesResponse.content 를 비우도록 exception 주입 대신
        # response 를 빈 payload 로 두면 tool_use.input 이 빈 dict → Pydantic 검증 실패.
        # 명확히 "tool_use 없음" 경로를 검증하려면 커스텀 응답이 필요하다.

        class _EmptyResponse:
            content = []  # tool_use 블록 없음

        async def fake_create(**kwargs):
            return _EmptyResponse()

        class _FakeMessages:
            create = staticmethod(fake_create)

        class _FakeClient:
            messages = _FakeMessages()

        claude_client._create_async_client = lambda: _FakeClient()  # type: ignore[method-assign]

        with pytest.raises(ValueError, match="tool_use"):
            await claude_client.generate_with_schema(
                system_prompt="s",
                user_prompt="u",
                response_schema=SimpleSchema,
            )


# ---------------------------------------------------------------------------
# 추가 — R1 판정 요약 테스트 (capability_report 기반)
# ---------------------------------------------------------------------------


class TestR1Verdict:
    """R1 리스크 (Multi-provider Structured Output) 판정을 자동 검증."""

    def test_openai_azure_vllm_native_support(self):
        report = provider_capability_report()
        for name in ("openai", "azure_openai", "vllm"):
            caps = report[name]
            assert caps["discriminated_union"] is True, f"{name} 가 union 미지원으로 보고됨"

    def test_gemini_flagged_as_need_fallback(self):
        """Gemini 는 NEED_FALLBACK — 평탄화 스키마 필요."""
        caps = provider_capability_report()["gemini"]
        assert caps["discriminated_union"] is False
        assert caps["strict_mode"] is False

    def test_claude_via_tool_use(self):
        """Claude 는 Tool Use 로 PASS (strict 모드는 없음)."""
        caps = provider_capability_report()["anthropic"]
        assert caps["discriminated_union"] is True
        assert caps["strict_mode"] is False
