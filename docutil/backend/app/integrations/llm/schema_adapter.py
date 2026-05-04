"""LLM Structured Output 을 위한 스키마 어댑터 모듈.

Phase 4 S1 D5 — Pydantic BaseModel 을 각 프로바이더별 JSON Schema/Tool 정의로
변환하는 유틸을 제공한다.

배경 (R1 리스크):
    DocumentSchema v1.0 은 Pydantic Discriminated Union 22 컴포넌트를 사용한다.
    OpenAI/Azure 는 strict json_schema 모드로 이를 원본 그대로 지원하지만,
    Gemini / Claude 는 제약이 있어 별도 변환이 필요하다.

제공 함수:
    - ``pydantic_to_openai_schema`` : OpenAI Structured Outputs 형식.
    - ``pydantic_to_gemini_schema`` : Gemini 호환 단순화 스키마.
    - ``pydantic_to_claude_tool``   : Claude Tool Use 정의.
    - ``validate_structured_output``: LLM 응답 dict 를 Pydantic model 로 검증.

본 모듈은 LLM 클라이언트 내부 헬퍼로만 사용되며, 외부에서 직접 호출하는
경우는 거의 없어야 한다 (P1 Single Implementation 원칙).
"""

from __future__ import annotations

import copy
import json as json_module
import logging
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


# ---------------------------------------------------------------------------
# 내부 헬퍼
# ---------------------------------------------------------------------------


def _resolve_refs(schema: dict[str, Any], root: dict[str, Any] | None = None) -> dict[str, Any]:
    """JSON Schema 내의 ``$ref`` 참조를 모두 inline 으로 치환한다.

    Gemini 는 ``$defs`` / ``$ref`` 를 지원하지 않으므로 참조를 전부 펼쳐야 한다.
    재귀 구조는 순환 참조 탐지를 위해 얕은 복사를 수행한다.

    Parameters
    ----------
    schema:
        변환 대상 JSON Schema 서브트리.
    root:
        ``$defs`` 조회를 위한 루트 문서. None 이면 ``schema`` 자체가 루트.

    Returns
    -------
    dict[str, Any]
        참조가 inline 된 새 스키마 (원본은 변경하지 않음).
    """
    if root is None:
        root = schema
    defs = root.get("$defs") or root.get("definitions") or {}

    def _walk(node: Any, seen: set[str]) -> Any:
        # dict 인 경우 각 키를 재귀 처리
        if isinstance(node, dict):
            # $ref 발견 시 defs 에서 정의를 찾아 inline
            if "$ref" in node and isinstance(node["$ref"], str):
                ref = node["$ref"]
                # "#/$defs/Name" 또는 "#/definitions/Name" 형식만 지원
                if ref.startswith("#/$defs/"):
                    name = ref[len("#/$defs/") :]
                elif ref.startswith("#/definitions/"):
                    name = ref[len("#/definitions/") :]
                else:
                    # 지원하지 않는 ref 형식 — 그대로 반환
                    return dict(node)
                if name in seen:
                    # 순환 참조 — 더 이상 inline 하지 않고 빈 객체로 대체
                    # Gemini 는 재귀 스키마를 지원하지 않음 (best-effort)
                    return {"type": "object"}
                if name not in defs:
                    logger.warning("[schema_adapter] $ref '%s' 를 정의 목록에서 찾지 못함", ref)
                    return dict(node)
                resolved = _walk(defs[name], seen | {name})
                # ref 와 함께 올 수 있는 추가 키 (description 등) 병합
                merged = {k: v for k, v in node.items() if k != "$ref"}
                if isinstance(resolved, dict):
                    merged = {**resolved, **merged}
                return merged
            return {k: _walk(v, seen) for k, v in node.items()}
        if isinstance(node, list):
            return [_walk(item, seen) for item in node]
        return node

    result = _walk(schema, set())
    # 최상위의 $defs 는 inline 후 제거
    if isinstance(result, dict):
        result.pop("$defs", None)
        result.pop("definitions", None)
    return result


def _strip_unsupported_keys(node: Any, remove_keys: set[str]) -> Any:
    """Gemini 등에서 무시/거부되는 JSON Schema 키를 재귀적으로 제거한다.

    Gemini 제약:
        - ``additionalProperties`` 무시
        - ``$schema`` 불필요
        - ``title`` 은 허용되지만 과도한 정보 → 본 프로젝트에서는 보존
        - ``exclusiveMinimum`` / ``exclusiveMaximum`` 는 bool 대신 숫자로 들어가야 함
          (Pydantic v2 는 숫자로 내는데 일부 도구는 bool 도 생성 → 안전 제거)
    """
    if isinstance(node, dict):
        return {k: _strip_unsupported_keys(v, remove_keys) for k, v in node.items() if k not in remove_keys}
    if isinstance(node, list):
        return [_strip_unsupported_keys(item, remove_keys) for item in node]
    return node


def _flatten_nullable(node: Any) -> Any:
    """``"type": ["string", "null"]`` 형태를 ``nullable`` 패턴으로 변환.

    Gemini 는 type 배열을 지원하지 않고, OpenAPI 의 ``nullable: true`` 를
    요구한다. 본 함수는 type 필드가 리스트인 경우 null 을 분리하고
    ``nullable=True`` 를 추가한다.
    """
    if isinstance(node, dict):
        type_val = node.get("type")
        if isinstance(type_val, list):
            non_null = [t for t in type_val if t != "null"]
            has_null = "null" in type_val
            new_node = dict(node)
            if len(non_null) == 1:
                new_node["type"] = non_null[0]
            elif len(non_null) == 0:
                new_node["type"] = "string"  # fallback
            else:
                # 여러 타입 중 첫 번째만 선택 (Gemini 제약)
                new_node["type"] = non_null[0]
                logger.warning(
                    "[schema_adapter] Gemini 호환을 위해 다중 타입 %s 중 '%s' 만 채택",
                    non_null,
                    non_null[0],
                )
            if has_null:
                new_node["nullable"] = True
            return {k: _flatten_nullable(v) for k, v in new_node.items()}
        return {k: _flatten_nullable(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_flatten_nullable(item) for item in node]
    return node


# OpenAI Structured Outputs strict 모드가 지원하지 않는 JSON Schema 키워드.
# (2024-08-01 이후 strict=true 정책 기준)
#
# 배경: D7 live API 검증에서 400 Bad Request 가 `required` 누락 외에도
# 검증 제약 키워드 (pattern / minLength / maxItems 등) 에서 재현됨.
# OpenAI 는 strict 모드에서 **JSON Schema subset** 만 받아들이며,
# 이 집합 밖 키는 schema validation 단계에서 400 으로 거부된다.
#
# 안전성:
# - 키를 제거해도 응답은 ``validate_structured_output`` 단계에서 원본
#   Pydantic 모델로 재검증되므로 제약 손실은 없다.
# - ``default`` 는 OpenAI strict 가 허용하지 않으므로 제거하고, Pydantic 이
#   정의한 default 는 응답 후 재검증 시 자동 채워진다.
_OPENAI_STRICT_UNSUPPORTED_KEYWORDS: set[str] = {
    # 문자열 제약
    "minLength",
    "maxLength",
    "pattern",
    "format",
    # 숫자 제약
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "multipleOf",
    # 배열 제약
    "minItems",
    "maxItems",
    "uniqueItems",
    "contains",
    "minContains",
    "maxContains",
    "unevaluatedItems",
    # 객체 제약
    "minProperties",
    "maxProperties",
    "patternProperties",
    "propertyNames",
    "unevaluatedProperties",
    # 기타
    "default",
    "$schema",
}


def _enforce_openai_strict(node: Any) -> Any:
    """OpenAI Structured Outputs strict 모드 호환을 위해 스키마를 in-place 보정한다.

    H11 핫픽스 (D7 후속, 2026-04-19) + D8 확장 (2026-04-22):
        OpenAI strict 모드는 **JSON Schema subset** 만 받아들인다. 구체적으로:
            1. 모든 ``type: "object"`` 노드에 다음이 필요:
               - ``required`` 배열이 ``properties`` 의 **모든 키** 를 포함
               - ``additionalProperties`` 가 **false** 로 명시
            2. 다음 키워드는 **금지** (있으면 400 Bad Request):
               - 문자열: ``minLength``, ``maxLength``, ``pattern``, ``format``
               - 숫자: ``minimum``, ``maximum``, ``exclusiveMinimum``,
                 ``exclusiveMaximum``, ``multipleOf``
               - 배열: ``minItems``, ``maxItems``, ``uniqueItems``, ``contains``,
                 ``minContains``, ``maxContains``, ``unevaluatedItems``
               - 객체: ``minProperties``, ``maxProperties``, ``patternProperties``,
                 ``propertyNames``, ``unevaluatedProperties``
               - 기타: ``default``, ``$schema``
            3. ``oneOf`` 는 지원되지 않음 → ``anyOf`` 로 치환 필요.
            4. ``discriminator`` 키워드는 Pydantic v2 Discriminated Union 에서
               발생하는데 strict 모드가 거부.

        Pydantic v2 의 ``model_json_schema()`` 는 위 제약 키워드를 전부 생성하므로
        실 API 호출 전에 필수로 제거해야 한다. D7 실 호출에서 발견된 400 은
        ``required`` 누락 + 제약 키워드 복합 원인이다.

    변환 전략:
        0. ``oneOf`` → ``anyOf`` 치환 + ``discriminator`` 제거.
        1. **object 노드** 마다:
           - ``required`` ← ``list(properties.keys())``
           - ``additionalProperties: false`` 명시
        2. 모든 노드에서 ``_OPENAI_STRICT_UNSUPPORTED_KEYWORDS`` 에 속한 키 제거.
        3. **재귀 적용 범위**:
           - ``properties.*`` (모든 프로퍼티 스키마)
           - ``items`` (배열 요소)
           - ``anyOf`` / ``oneOf`` / ``allOf`` 배열의 각 요소
           - ``$defs`` (방어적 — ``_resolve_refs`` 가 이미 인라인했어야 함)

    제약 손실에 대한 안전성:
        - 제거된 제약은 서버의 ``validate_structured_output`` 에서 원본
          Pydantic 모델로 재검증되므로 무결성은 유지된다.
        - LLM 이 제약을 어긴 응답을 내면 ValidationError 가 발생해
          ``DocumentSchemaValidationError`` 로 래핑된다 (422 응답).

    Parameters
    ----------
    node:
        보정 대상 스키마 서브트리. **in-place** 로 수정된다.

    Returns
    -------
    Any
        동일 ``node`` 참조 (체이닝 편의).
    """
    if not isinstance(node, dict):
        if isinstance(node, list):
            for item in node:
                _enforce_openai_strict(item)
        return node

    # 0) oneOf → anyOf 치환.
    #    OpenAI strict 는 ``oneOf`` 를 지원하지 않는다 (2026-04 기준). Pydantic v2
    #    Discriminated Union 은 기본적으로 ``oneOf + discriminator`` 를 사용하므로
    #    본 변환이 없으면 Discriminated Union 포함 스키마는 400 을 받는다.
    #    ``anyOf`` 는 의미상 느슨하지만, 응답은 ``validate_structured_output``
    #    단계에서 원본 Pydantic 모델로 엄격 재검증되므로 안전하다.
    if "oneOf" in node and isinstance(node["oneOf"], list):
        node["anyOf"] = node.pop("oneOf")
    # discriminator 키도 OpenAI strict 에서 금지. type enum 은 각 variant 에 이미
    # const 로 포함되어 있어 제거해도 파싱에 영향 없음.
    node.pop("discriminator", None)

    # 0.5) OpenAI strict 가 거부하는 제약 키워드 제거 (D8 확장).
    #    Pydantic v2 가 생성한 ``pattern`` / ``minLength`` / ``maxItems`` 등은
    #    strict 모드에서 400 을 유발한다. 제약 자체는 ``validate_structured_output``
    #    단계에서 원본 Pydantic 모델로 재검증되므로 제거해도 안전하다.
    for _unsupported in list(_OPENAI_STRICT_UNSUPPORTED_KEYWORDS):
        node.pop(_unsupported, None)

    # 1) object 노드 판정 — "type": "object" 단일 케이스만.
    #    (우리는 object 타입에 null 을 직접 섞지 않고 anyOf 래핑을 쓰므로
    #     "type" 이 list 가 되는 object 노드는 본 경로에 존재하지 않아야 한다.)
    if node.get("type") == "object":
        # 순환 참조 축약 노드 ({"type": "object"} 만) 포함하여 모든 object 에
        # additionalProperties=false 를 붙인다 (OpenAI strict 필수).
        if not isinstance(node.get("properties"), dict):
            node["properties"] = {}
        if not isinstance(node.get("required"), list):
            node["required"] = []

        properties: dict[str, Any] = node["properties"]
        original_required: set[str] = set(node.get("required") or [])

        all_keys = list(properties.keys())
        node["required"] = all_keys
        node["additionalProperties"] = False

        # 기존 required 에 없던 키 (= Optional 또는 default 보유) 중에서
        # **Pydantic 이 이미 null 을 허용한 필드만** nullable 표현 보정을 수행한다.
        #
        # - ``Optional[X]`` / ``X | None`` → Pydantic 이 ``anyOf: [X, {type:null}]``
        #   또는 ``type: [X, null]`` 를 생성. 본 함수는 이 표현을 그대로 살려 LLM 이
        #   null 을 반환해도 되게 한다.
        # - **default 값만** 있는 non-Optional 필드 (``numbered: bool = True`` 등) 는
        #   Pydantic 이 null 을 표현하지 않았으므로 nullable 로 승격시키면 원본 Pydantic
        #   검증이 실패한다. 이 경우 그대로 두어 LLM 이 default 값을 채우도록 한다
        #   (JSON Schema 의 ``default`` 키가 힌트).
        #
        # 따라서 _make_nullable 호출은 "이미 null 가능" 케이스에만 _ensure_null 로
        # 수렴 — 실제로는 Pydantic 이 표현한 그대로 유지하는 no-op 에 가까움.
        for key, prop in properties.items():
            if key not in original_required and isinstance(prop, dict):
                _ensure_null_variant_if_pydantic_nullable(prop)

    # 2) 재귀: properties 각 값
    if isinstance(node.get("properties"), dict):
        for prop_schema in node["properties"].values():
            _enforce_openai_strict(prop_schema)

    # 3) 재귀: items (배열 요소)
    if "items" in node:
        _enforce_openai_strict(node["items"])

    # 4) 재귀: anyOf / oneOf / allOf
    for union_key in ("anyOf", "oneOf", "allOf"):
        if union_key in node and isinstance(node[union_key], list):
            for variant in node[union_key]:
                _enforce_openai_strict(variant)

    # 5) 재귀: $defs (방어적 — _resolve_refs 가 이미 인라인했어야 함)
    for defs_key in ("$defs", "definitions"):
        if defs_key in node and isinstance(node[defs_key], dict):
            for defn in node[defs_key].values():
                _enforce_openai_strict(defn)

    return node


def _ensure_null_variant_if_pydantic_nullable(prop: dict[str, Any]) -> None:
    """Pydantic 이 이미 null 을 허용한 필드의 표현을 그대로 유지한다 (in-place).

    H11 보정 정책 (2026-04-19):
        OpenAI strict 는 **모든 키가 required** 이어야 하지만, LLM 이 실제로
        None 을 보내도 무방한지는 원본 Pydantic 타입이 결정한다. 원칙은 다음과 같다.

        - ``X | None`` (Optional) → Pydantic 이 null 표현 포함 → 그대로 유지 → LLM 이 null 가능
        - ``X = default_value`` (non-Optional, default 만 보유) → Pydantic 이 null 불가
          → null 추가 금지 (추가 시 원본 Pydantic 재검증 실패)

        본 함수는 전자의 경우에만 null variant 존재 여부를 **보장만** 하고,
        실제로는 Pydantic 이 이미 제공한 표현이 대부분 그대로 유지된다.

    케이스:
        1. ``anyOf`` / ``oneOf`` 내부에 ``{"type": "null"}`` variant 가 이미 있음
           → Pydantic 이 Optional 로 인식. 그대로 유지 (no-op).
        2. ``type`` 이 list 이고 ``"null"`` 을 포함
           → Pydantic 이 type-union 으로 null 표현. 그대로 유지 (no-op).
        3. 그 외 (단일 type, enum, const, default 만 있음)
           → Pydantic 이 null 을 허용하지 않은 경우. 아무 것도 하지 않음
             (strict 모드는 required 로만 만족시키고 LLM 이 default 나 실제값을 채움).

    즉 본 함수는 대부분의 경우 **no-op** 이며, 향후 스키마 정규화가 필요할 때
    훅으로 사용될 수 있도록 함수로 분리되어 있다.
    """
    # anyOf / oneOf 에 null variant 가 이미 있으면 그대로 둔다.
    for union_key in ("anyOf", "oneOf"):
        if union_key in prop and isinstance(prop[union_key], list):
            # 이미 표현되어 있음 — 유지 (OpenAI strict 는 anyOf 내 null variant 허용).
            return

    # type 이 list 형태로 null 을 포함 — 유지.
    prop_type = prop.get("type")
    if isinstance(prop_type, list) and "null" in prop_type:
        return

    # 그 외 — Pydantic 이 null 을 허용하지 않은 필드.
    # OpenAI strict 의 required 요구는 이미 상위에서 만족시켰고,
    # LLM 은 default 값 또는 타입 범위 내 실제 값을 채우게 된다.
    # 여기서는 아무 변형을 가하지 않는다.
    return


def _flatten_unions_for_gemini(node: Any) -> Any:
    """``oneOf`` / ``anyOf`` 를 Gemini 호환 단일 스키마로 평탄화.

    Gemini 는 ``oneOf`` / ``anyOf`` 를 지원하지 않는다 (2025-Q1 기준).
    Discriminated Union 에서 가장 일반적인 파생을 선택하여 반환하고,
    ``type`` 필드는 enum 으로 보존한다.

    변환 전략:
        1. ``oneOf`` 또는 ``anyOf`` 가 있으면 후보들을 순회.
        2. 각 후보의 properties 를 합집합으로 병합 (중복 키는 첫 정의 우선).
        3. ``required`` 는 모든 후보의 교집합 (가장 느슨한 제약).
        4. discriminator 키가 있으면 enum 으로 type 값을 모두 나열.

    주의: 이 변환은 비가역적이며 스키마의 엄밀성을 잃는다.
    반환값을 사용한 LLM 응답은 반드시 원본 Pydantic 모델로 재검증해야 한다
    (``validate_structured_output`` 사용).
    """
    if isinstance(node, dict):
        # oneOf/anyOf 를 먼저 처리
        union_key = None
        if "oneOf" in node:
            union_key = "oneOf"
        elif "anyOf" in node:
            union_key = "anyOf"

        if union_key:
            candidates = node[union_key]
            if not candidates:
                return _flatten_unions_for_gemini({"type": "object"})
            # 각 후보를 재귀적으로 먼저 평탄화
            flat_candidates = [_flatten_unions_for_gemini(c) for c in candidates]
            merged_props: dict[str, Any] = {}
            required_sets: list[set[str]] = []
            type_discriminator_values: list[str] = []

            for cand in flat_candidates:
                if not isinstance(cand, dict):
                    continue
                props = cand.get("properties", {})
                for k, v in props.items():
                    if k not in merged_props:
                        merged_props[k] = v
                required_sets.append(set(cand.get("required", [])))
                # type discriminator 탐색 (Pydantic 이 default+const 로 생성)
                type_prop = props.get("type") or {}
                if isinstance(type_prop, dict):
                    if "const" in type_prop:
                        type_discriminator_values.append(str(type_prop["const"]))
                    elif "enum" in type_prop and isinstance(type_prop["enum"], list):
                        type_discriminator_values.extend(str(v) for v in type_prop["enum"])

            # type 필드는 enum 으로 통합
            if type_discriminator_values:
                unique_types = sorted(set(type_discriminator_values))
                merged_props["type"] = {"type": "string", "enum": unique_types}

            # required 는 교집합 (모든 후보에 공통)
            common_required = sorted(set.intersection(*required_sets)) if required_sets else []

            result = {
                "type": "object",
                "properties": merged_props,
                "required": common_required,
            }
            # 원본에 description 이 있었으면 유지
            if "description" in node:
                result["description"] = node["description"]
            return result

        # 일반 dict — 재귀
        out: dict[str, Any] = {}
        for k, v in node.items():
            out[k] = _flatten_unions_for_gemini(v)
        return out

    if isinstance(node, list):
        return [_flatten_unions_for_gemini(item) for item in node]

    return node


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------


def pydantic_to_openai_schema(model: type[BaseModel], *, strict: bool = True) -> dict[str, Any]:
    """Pydantic 모델 → OpenAI Structured Outputs 형식 dict.

    반환 형태::

        {
            "name": "ModelName",
            "strict": True,
            "schema": { ... Pydantic JSON Schema ... }
        }

    OpenAI/Azure 는 Discriminated Union 과 $ref 를 strict 모드에서 공식 지원하므로
    원본 스키마를 거의 그대로 사용할 수 있다. 단, Pydantic v2 의 Optional 필드는
    ``required`` 에서 제외되어 strict 모드의 400 을 유발하므로 H11 핫픽스가 적용된다.

    H11 (D7 후속) 핫픽스:
        - ``_resolve_refs`` 로 ``$defs`` / ``$ref`` 인라인 (OpenAI 는 $ref 를
          허용하지만 ``_enforce_openai_strict`` 의 재귀 안정성 확보를 위해 선행).
        - ``_enforce_openai_strict`` 로:
            · 모든 object 노드의 ``required`` 를 ``properties`` 전체 키로 확장
            · optional 필드는 ``type`` 에 ``"null"`` 을 추가하여 nullable 표현
            · ``additionalProperties: false`` 명시
        - strict=False 로 호출된 경우 위 보정을 건너뛴다 (검증 리포트용 경로).

    Parameters
    ----------
    model:
        변환 대상 Pydantic 모델 클래스.
    strict:
        OpenAI strict 모드 활성화 여부. True 이면 스키마의 모든 객체에
        ``additionalProperties: false`` 와 완전한 ``required`` 가 자동 추가된다.

    Returns
    -------
    dict[str, Any]
        OpenAI Structured Outputs 요청 바디의 ``response_format.json_schema`` 값.
    """
    raw_schema = model.model_json_schema()

    if not strict:
        # strict=False 경로는 원본 스키마를 그대로 전달 (D7 리포트용 우회 경로).
        return {
            "name": model.__name__,
            "strict": False,
            "schema": raw_schema,
        }

    # H11 핫픽스: strict 모드용 보정.
    # 1) $ref inline — _enforce_openai_strict 가 object 를 재귀할 때 ref 참조가
    #    부재해야 일관된 보정이 가능. OpenAI 는 $ref 도 허용하지만 본 변환은
    #    안전한 상위 집합이다.
    resolved = _resolve_refs(raw_schema)
    # 2) required 확장 + nullable 전환 + additionalProperties=false
    _enforce_openai_strict(resolved)

    return {
        "name": model.__name__,
        "strict": True,
        "schema": resolved,
    }


def pydantic_to_gemini_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Pydantic 모델 → Gemini 호환 JSON Schema.

    Gemini 제약 (Google Gemini API v1beta OpenAI-compat, 2025-Q1 기준):
        - ``$ref`` / ``$defs`` 미지원 → inline expansion
        - ``oneOf`` / ``anyOf`` 미지원 → 단일 스키마로 평탄화 (정보 손실)
        - ``type`` 배열 (["string", "null"]) 미지원 → nullable 플래그로 분리
        - ``additionalProperties`` 무시 → 제거
        - ``exclusiveMinimum`` / ``exclusiveMaximum`` 는 숫자로만

    NEED_FALLBACK 케이스:
        Discriminated Union 이 포함된 스키마는 Gemini 에서 엄밀히 지원되지 않는다.
        본 함수는 union 을 평탄화하여 best-effort 로 넘기지만, 응답 검증 단계에서
        원본 Pydantic 모델로 재파싱하여 무결성을 보장해야 한다.

    Returns
    -------
    dict[str, Any]
        Gemini OpenAI-compat 엔드포인트의 ``response_format.json_schema.schema`` 에
        넣을 수 있는 형태. 일반 응답 검증은 추가로 수행할 것.
    """
    raw = model.model_json_schema()

    # 1) $ref inline 전개
    expanded = _resolve_refs(raw)

    # 2) oneOf/anyOf 평탄화
    flat = _flatten_unions_for_gemini(expanded)

    # 3) type 배열 → nullable 플래그
    nullable_fixed = _flatten_nullable(flat)

    # 4) Gemini 가 무시/거부하는 키 제거
    #    additionalProperties: 무시됨
    #    $schema: 불필요
    #    title: 보존 (Gemini 는 허용)
    cleaned = _strip_unsupported_keys(
        nullable_fixed,
        {"additionalProperties", "$schema", "discriminator"},
    )

    return cleaned


def pydantic_to_claude_tool(model: type[BaseModel]) -> dict[str, Any]:
    """Pydantic 모델 → Claude Tool Use 정의.

    Claude Tool Use 패턴:
        - tool 의 ``input_schema`` 로 JSON Schema 를 전달.
        - Claude 는 ``oneOf`` / ``anyOf`` / ``$ref`` 를 대부분 수용하지만,
          아주 깊은 중첩에서는 실패 사례가 보고된 바 있다 (Phase 1 조사 노트).
        - discriminator 키워드는 공식 미지원이지만 ``type`` enum 은 이해한다.

    반환 형태::

        {
            "name": "structured_output",
            "description": "... 한국어 설명 ...",
            "input_schema": { ... Pydantic JSON Schema ... }
        }

    Returns
    -------
    dict[str, Any]
        Claude messages API 의 ``tools[0]`` 로 전달 가능한 정의.
    """
    raw = model.model_json_schema()
    # Claude 는 $ref 는 허용하지만 일부 케이스에서 문제가 있어 inline 도 안전
    # 다만 원본이 valid JSON Schema 이므로 여기서는 그대로 전달.
    # discriminator 키워드만 제거 (Claude 가 경고를 내는 경우가 있음)
    cleaned = _strip_unsupported_keys(copy.deepcopy(raw), {"discriminator"})

    return {
        "name": "structured_output",
        "description": (
            f"{model.__name__} 스키마에 정확히 부합하는 구조화된 데이터를 출력한다. "
            "스키마에 정의되지 않은 필드는 포함하지 말 것."
        ),
        "input_schema": cleaned,
    }


def pydantic_to_vllm_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Pydantic 모델 → vLLM guided_json 용 JSON Schema.

    vLLM 은 ``guided_json`` 파라미터로 JSON Schema 를 받아 XGrammar/Outlines
    기반 강제 디코딩을 수행한다. 대부분의 JSON Schema 문법을 지원하지만,
    ``$ref`` 는 inline expansion 을 권장한다 (엔진 버전별 차이 때문).

    Pydantic v2 의 discriminated union 은 ``discriminator.mapping`` 에
    ``"#/$defs/..."`` 문자열을 남겨둔다. $defs 를 inline 으로 전개한 뒤에도
    이 문자열이 잔존하여 엔진이 참조 실패를 일으키므로, ``discriminator``
    키워드를 함께 제거한다 (oneOf 자체는 XGrammar 가 해석할 수 있음).

    Returns
    -------
    dict[str, Any]
        vLLM 요청 바디의 ``extra_body.guided_json`` 에 전달할 스키마 dict.
    """
    raw = model.model_json_schema()
    expanded = _resolve_refs(raw)
    # discriminator.mapping 내부에 "#/$defs/..." 문자열이 남아 있으므로 제거.
    # oneOf 는 유지되어 각 variant 를 독립적으로 표현한다.
    return _strip_unsupported_keys(expanded, {"discriminator"})


def validate_structured_output(raw: Any, schema: type[T]) -> T:  # noqa: UP047
    """LLM 이 반환한 원시 응답을 Pydantic 모델로 검증·파싱한다.

    입력은 dict, JSON 문자열, 또는 이미 검증된 model 인스턴스 중 하나일 수 있다.
    검증 실패 시 ``pydantic.ValidationError`` 가 그대로 전파되므로,
    호출자는 필요시 fallback/재시도 로직을 구성해야 한다.

    Parameters
    ----------
    raw:
        LLM 응답 본문. dict, str (JSON), 또는 BaseModel 인스턴스.
    schema:
        검증 대상 Pydantic 모델 클래스.

    Returns
    -------
    T
        검증 통과한 Pydantic 모델 인스턴스.

    Raises
    ------
    pydantic.ValidationError
        raw 가 schema 를 만족하지 않을 때.
    ValueError
        raw 가 JSON 문자열인데 파싱 실패.
    """
    # 이미 올바른 타입이면 그대로 통과
    if isinstance(raw, schema):
        return raw

    # 문자열 → JSON 파싱
    if isinstance(raw, str):
        try:
            raw = json_module.loads(raw)
        except json_module.JSONDecodeError as exc:
            raise ValueError(f"LLM 응답이 유효한 JSON 이 아닙니다: {exc}") from exc

    # dict → Pydantic 검증
    if isinstance(raw, dict):
        return schema.model_validate(raw)

    # 기타 타입 — 직접 validate 시도 (list 등)
    try:
        return schema.model_validate(raw)
    except ValidationError:
        raise


# ---------------------------------------------------------------------------
# 프로바이더 특성 리포트 (R1 리스크 문서화용)
# ---------------------------------------------------------------------------


def provider_capability_report() -> dict[str, dict[str, bool | str]]:
    """각 프로바이더의 Structured Output 지원 특성을 반환한다.

    R1 리스크 (Multi-provider Structured Output) 검증 결과를 프로그램적으로
    조회할 수 있는 형태로 정리한다. 값은 Phase 1~4 조사 결과 + 본 D5 구현
    검증을 기반으로 한다.
    """
    return {
        "openai": {
            "discriminated_union": True,
            "ref_support": True,
            "strict_mode": True,
            "nested_union": True,
            "note": "네이티브 strict json_schema 모드",
        },
        "azure_openai": {
            "discriminated_union": True,
            "ref_support": True,
            "strict_mode": True,
            "nested_union": True,
            "note": "OpenAI 와 동일 (api_version >= 2024-08-01-preview)",
        },
        "gemini": {
            "discriminated_union": False,
            "ref_support": False,
            "strict_mode": False,
            "nested_union": False,
            "note": "oneOf/anyOf/$ref 미지원 → 평탄화 필요 + 응답 재검증 필수",
        },
        "anthropic": {
            "discriminated_union": True,
            "ref_support": True,
            "strict_mode": False,
            "nested_union": True,
            "note": "Tool Use 패턴 — strict 는 아니지만 대부분 케이스에서 정확",
        },
        "vllm": {
            "discriminated_union": True,
            "ref_support": True,
            "strict_mode": True,
            "nested_union": True,
            "note": "guided_json (XGrammar) — JSON Schema 대부분 지원",
        },
    }
