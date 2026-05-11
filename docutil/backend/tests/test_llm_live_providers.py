"""Phase 4 S1 D7 Part 2 — 실 LLM API 교차 검증 (live_api 마커).

기본 skip. 명시적 실행만::

    pytest tests/test_llm_live_providers.py -m live_api -v --tb=short

실행 환경
--------
- 반드시 서버 ``docutil-api`` 컨테이너 내부에서 실행.
- DB 에 저장된 프로바이더별 API 키가 환경변수로 주입되어 있어야 한다
  (``OPENAI_API_KEY``, ``AZURE_OPENAI_API_KEY``, ``GOOGLE_API_KEY``,
  ``ANTHROPIC_API_KEY``). 누락 시 해당 프로바이더는 skip 된다.

시나리오
--------
A. slide_report — 2026 Q1 매출 20% 증가 슬라이드 3장   (4 provider × 3 호출 = 12)
B. minutes       — AI 킥오프 회의록 (3명, 안건 3, 액션 2) (4 provider × 3 호출 = 12)
C. proposal      — 클라우드 마이그레이션 5장 제안서     (4 provider × 2 호출 = 8)

총 최대 32 호출. 비용 한도 35 로 하드코딩.

수집 메트릭
-----------
각 호출마다 latency_seconds, token 사용량 (가능한 경우), estimated_cost_usd,
schema_validation_passed, component_types_used, pages_count,
total_components_count, korean_ratio, citations_included.

산출물
------
``tests/qa_reports/20260421_s1_d7_live_api_report.md`` 가 테스트 종료 시
생성된다 (pytest 종료 훅). 집계된 raw metrics 는 JSON 으로도 남긴다.
"""

from __future__ import annotations

import asyncio
import json as json_module
import os
import time
import uuid
from pathlib import Path
from typing import Any

import httpx
import pytest
from pydantic import ValidationError

# Phase 7 — R2 완전 보강 (2026-05-11): claude_client 모듈이 dead code 로 판정되어
# 삭제됨. 본 live-API 테스트는 Phase 4 S1 D7 시점의 obsolete 검증 (factory 가
# ``AgentHubLLMWrapper`` 만 반환하는 Phase 7.3 정책에서는 의미 상실).
# 모듈 로딩 자체가 실패하지 않도록 ``pytest.importorskip`` 으로 collection skip.
pytest.importorskip(
    "app.integrations.llm.claude_client",
    reason="Phase 7 (2026-05-11) claude_client.py removed — live-API tests obsolete",
)

from app.integrations.llm.claude_client import ClaudeClient  # noqa: E402
from app.integrations.llm.client import OpenAICompatibleClient  # noqa: E402
from app.integrations.llm.factory import create_llm_client  # noqa: E402
from app.integrations.llm.schema_adapter import (  # noqa: E402
    pydantic_to_gemini_schema,
    pydantic_to_openai_schema,
    validate_structured_output,
)
from app.modules.documents_v2.schemas import DocumentSchema
from app.modules.documents_v2.utils import build_system_prompt, build_user_prompt

# ---------------------------------------------------------------------------
# 전역: 모든 테스트에 live_api 마커 적용 (기본 skip).
#
# 기본은 모듈 수준에서 skip 되고, 다음 조건이 **모두** 충족돼야 실행된다.
#   1. pytest 에 ``-m live_api`` 지정 (pytestmark 마커 선택)
#   2. 환경변수 ``LIVE_API_ENABLED=1`` (실수로 도는 것 방지 가드)
# ---------------------------------------------------------------------------

pytestmark = [
    pytest.mark.live_api,
    pytest.mark.skipif(
        os.environ.get("LIVE_API_ENABLED", "").strip() not in {"1", "true", "True"},
        reason="LIVE_API_ENABLED=1 환경변수 필요 (실 API 호출 비용 보호).",
    ),
]


# ---------------------------------------------------------------------------
# 비용 한도 / 글로벌 카운터
# ---------------------------------------------------------------------------

MAX_TOTAL_CALLS = 35  # 안전 마진 (32 호출 예상 + 여유 3).
CALL_STATE: dict[str, Any] = {
    "count": 0,
    "results": [],  # list[dict] — 각 호출의 raw metrics
}


def _guard_cost() -> None:
    """호출 상한에 도달했으면 해당 테스트를 skip 시킨다."""
    if CALL_STATE["count"] >= MAX_TOTAL_CALLS:
        pytest.skip(f"호출 상한({MAX_TOTAL_CALLS}) 도달 — 비용 보호를 위해 skip")


# ---------------------------------------------------------------------------
# 토큰 단가 (USD, 2026-04 공개 가격 기준, 1K 토큰 당)
# ---------------------------------------------------------------------------

_PRICING_PER_1K = {
    "openai": {"input": 0.0025, "output": 0.01},  # gpt-4o
    "azure_openai": {"input": 0.0025, "output": 0.01},  # gpt-4o (동일)
    "gemini": {"input": 0.000075, "output": 0.0003},  # gemini-2.0-flash
    "anthropic": {"input": 0.003, "output": 0.015},  # claude-sonnet-4
}


def _estimate_cost(provider: str, input_tokens: int, output_tokens: int) -> float:
    price = _PRICING_PER_1K.get(provider, {"input": 0.0, "output": 0.0})
    return (input_tokens / 1000.0) * price["input"] + (output_tokens / 1000.0) * price["output"]


# ---------------------------------------------------------------------------
# 프로바이더별 API 키 확인 — 누락 시 개별 skip
# ---------------------------------------------------------------------------


def _require_env(var: str) -> None:
    if not os.environ.get(var):
        pytest.skip(f"{var} 미설정 — 해당 프로바이더 테스트 skip")


def _build_client(provider: str):
    """프로바이더별 클라이언트 생성. 실패 시 skip."""
    if provider == "openai":
        _require_env("OPENAI_API_KEY")
    elif provider == "azure_openai":
        _require_env("AZURE_OPENAI_API_KEY")
        _require_env("AZURE_OPENAI_ENDPOINT")
        _require_env("AZURE_OPENAI_DEPLOYMENT")
    elif provider == "gemini":
        _require_env("GOOGLE_API_KEY")
    elif provider == "anthropic":
        _require_env("ANTHROPIC_API_KEY")
    else:
        pytest.skip(f"미지원 프로바이더: {provider}")

    try:
        return create_llm_client(provider)
    except Exception as exc:  # noqa: BLE001 - skip 판정 목적
        pytest.skip(f"{provider} 클라이언트 생성 실패: {exc}")


# ---------------------------------------------------------------------------
# 시나리오 정의
# ---------------------------------------------------------------------------


SCENARIOS: dict[str, dict[str, Any]] = {
    "slide_report": {
        "document_type": "slide_report",
        "prompt": (
            "2026년 Q1 매출이 전년 동기 대비 20% 증가한 성과를 강조한 "
            "슬라이드 보고서를 정확히 3장 생성하세요. "
            "반드시 SlideTitle, KPI, BulletList 컴포넌트가 최소 1개씩 포함되어야 합니다."
        ),
        "max_tokens": 4096,
        "repeats": 3,
        "expect": {
            "min_pages": 1,
            "max_pages": 5,
            "required_component_types": {"SlideTitle", "KPI"},
        },
    },
    "minutes": {
        "document_type": "minutes",
        "prompt": (
            "AI 프로젝트 킥오프 회의록을 작성하세요. "
            "참석자 3명, 안건 3개, 액션아이템 2개를 포함합니다. "
            "AttendeeList 와 ActionItemList 컴포넌트를 반드시 사용하세요."
        ),
        "max_tokens": 3000,
        "repeats": 3,
        "expect": {
            "min_pages": 1,
            "max_pages": 3,
            "required_component_types": {"AttendeeList", "ActionItemList"},
        },
    },
    "proposal": {
        "document_type": "proposal",
        "prompt": (
            "클라우드 마이그레이션 제안서를 5장으로 작성하세요. "
            "ExecutiveSummary, KPI, RiskMatrix(또는 DataTable) 컴포넌트를 반드시 포함합니다."
        ),
        "max_tokens": 6000,
        "repeats": 2,  # 길이 제한으로 축소.
        "expect": {
            "min_pages": 3,
            "max_pages": 8,
            "required_component_types": {"ExecutiveSummary"},
            # RiskMatrix 또는 DataTable 중 하나 이상 (post-check).
            "required_any_of": {"RiskMatrix", "DataTable"},
        },
    },
}

PROVIDERS = ["openai", "azure_openai", "gemini", "anthropic"]


# ---------------------------------------------------------------------------
# 컴포넌트 순회 헬퍼 (중첩 TwoColumn/ThreeColumn 포함)
# ---------------------------------------------------------------------------


def _iter_components(schema: DocumentSchema):
    def _walk(comp):
        yield comp
        # TwoColumn
        if getattr(comp, "type", None) == "TwoColumn":
            for sub in list(comp.left) + list(comp.right):
                yield from _walk(sub)
        elif getattr(comp, "type", None) == "ThreeColumn":
            for col in comp.columns:
                for sub in col:
                    yield from _walk(sub)

    for page in schema.pages:
        for top in page.components:
            yield from _walk(top)


def _korean_ratio(text: str) -> float:
    if not text:
        return 0.0
    total = 0
    korean = 0
    for ch in text:
        if ch.isspace() or not ch.isprintable():
            continue
        total += 1
        # 한글 음절 범위
        if "\uac00" <= ch <= "\ud7a3":
            korean += 1
    return korean / total if total else 0.0


def _collect_text(schema: DocumentSchema) -> str:
    parts: list[str] = []
    for page in schema.pages:
        if page.title:
            parts.append(page.title)
    for comp in _iter_components(schema):
        for attr in ("text", "title", "label", "conclusion"):
            v = getattr(comp, attr, None)
            if isinstance(v, str):
                parts.append(v)
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 단일 호출 러너
# ---------------------------------------------------------------------------


async def _call_generate_with_schema(
    provider: str,
    client,
    *,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
) -> DocumentSchema:
    """프로바이더별 실 API 호출 래퍼.

    H11 핫픽스 (2026-04-19, D7 후속) 이후:
        ``pydantic_to_openai_schema(strict=True)`` 가 OpenAI strict 요구사항
        (required = 모든 properties 키 + additionalProperties=false +
        optional 필드 nullable 전환) 을 만족하도록 보정된다. 따라서 본 테스트에서도
        strict=True 로 호출하여 H11 해소를 실 API 로 검증한다.

    Claude 와 Gemini 는 기존 어댑터가 strict 모드를 요구하지 않으므로
    클라이언트의 ``generate_with_schema`` 를 그대로 사용한다.
    """

    raw: Any

    if provider in {"openai", "azure_openai"}:
        # H11 핫픽스 후: strict=True 로 직접 호출 — 400 이 발생하면 H11 미해소.
        json_schema = pydantic_to_openai_schema(DocumentSchema, strict=True)
        assert isinstance(client, OpenAICompatibleClient)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        raw = await client.generate_structured(
            messages=messages,
            json_schema=json_schema,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    elif provider == "gemini":
        # 평탄화 스키마로 호출. (GeminiClient.generate_with_schema 와 동일 로직)
        flat_schema = pydantic_to_gemini_schema(DocumentSchema)
        gemini_json_schema = {"name": "DocumentSchema", "schema": flat_schema}
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        raw = await OpenAICompatibleClient.generate_structured(
            client,
            messages=messages,
            json_schema=gemini_json_schema,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    elif provider == "anthropic":
        # Claude 는 Tool Use — 기존 ClaudeClient.generate_with_schema 로 위임.
        assert isinstance(client, ClaudeClient)
        # Claude 는 Pydantic 으로 직접 검증된 결과가 오므로 dict 로 역직렬화.
        schema_obj = await client.generate_with_schema(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=DocumentSchema,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return schema_obj  # 이미 DocumentSchema
    else:
        pytest.skip(f"미지원 프로바이더: {provider}")

    # ------------------------------------------------------------------
    # 서비스 파이프라인 사후 보정 (document_id, mode, template_id)
    # ------------------------------------------------------------------
    # LLM 은 document_id 를 안정적인 UUID 로 만들지 못하고 (예: 'doc-001')
    # type/mode 도 규정대로 생성하지 않는다. 실 production 플로우
    # (DocumentServiceV2._apply_metadata_overrides) 가 이를 덮어쓰므로,
    # 테스트에서도 동일 보정 후 검증한다. 원본 LLM 응답의 치명적 스키마
    # 이탈은 raw 에 기록된다 (error_type 에는 반영하지 않음).
    if isinstance(raw, dict):
        raw = dict(raw)  # shallow copy
        raw["document_id"] = str(uuid.uuid4())
        raw["mode"] = "free_generation"
        raw["template_id"] = None
        # metadata 보정
        md = dict(raw.get("metadata") or {})
        md.setdefault("created_at", "2026-04-19T10:00:00+00:00")
        md.setdefault("updated_at", "2026-04-19T10:00:00+00:00")
        md.setdefault("degraded_components", [])
        raw["metadata"] = md
    return validate_structured_output(raw, DocumentSchema)


async def _run_single_call(provider: str, scenario_name: str, repeat_idx: int) -> dict[str, Any]:
    """한 번의 generate_with_schema 호출 + 메트릭 수집."""
    _guard_cost()

    scenario = SCENARIOS[scenario_name]
    document_type = scenario["document_type"]
    prompt = scenario["prompt"]
    max_tokens = scenario["max_tokens"]

    client = _build_client(provider)

    # D6 후속 (2026-04-19): COMMON_INSTRUCTIONS 에 ISO-8601 / document_id 규정이
    # 직접 추가되었으므로, 과거의 inline 보강을 제거하여 프롬프트 개선 효과만을
    # 순수 검증한다.
    system_prompt = build_system_prompt(document_type)
    user_prompt = build_user_prompt(prompt, rag_context="")

    # TPM (30000 tok/min) 보호를 위해 프로바이더 내 연속 호출 사이에 짧게 대기.
    # 첫 호출은 대기 불필요.
    if CALL_STATE["count"] >= 1:
        await asyncio.sleep(20)

    metric: dict[str, Any] = {
        "provider": provider,
        "scenario": scenario_name,
        "repeat": repeat_idx,
        "document_type": document_type,
        "latency_seconds": None,
        "input_tokens": None,
        "output_tokens": None,
        "total_tokens": None,
        "estimated_cost_usd": None,
        "schema_validation_passed": False,
        "component_types_used": [],
        "pages_count": 0,
        "total_components_count": 0,
        "korean_ratio": None,
        "citations_included": False,
        "error_type": None,
        "error_message": None,
    }

    CALL_STATE["count"] += 1

    start = time.monotonic()
    try:
        schema = await _call_generate_with_schema(
            provider,
            client,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
            max_tokens=max_tokens,
        )
        metric["latency_seconds"] = round(time.monotonic() - start, 3)
        metric["schema_validation_passed"] = True
    except ValidationError as exc:
        metric["latency_seconds"] = round(time.monotonic() - start, 3)
        metric["error_type"] = "ValidationError"
        metric["error_message"] = str(exc)[:500]
        CALL_STATE["results"].append(metric)
        pytest.fail(
            f"[{provider}/{scenario_name} #{repeat_idx}] 스키마 검증 실패: {exc}",
            pytrace=False,
        )
    except httpx.HTTPStatusError as exc:
        # 400/500 은 응답 본문 첫 600자까지 함께 기록 (원인 파악용).
        body_snip = ""
        try:
            body_snip = exc.response.text[:600]
        except Exception:  # noqa: BLE001
            body_snip = ""
        metric["latency_seconds"] = round(time.monotonic() - start, 3)
        metric["error_type"] = "HTTPStatusError"
        metric["error_message"] = f"{exc} | body={body_snip}"
        CALL_STATE["results"].append(metric)
        pytest.fail(
            f"[{provider}/{scenario_name} #{repeat_idx}] HTTP 오류: {exc.response.status_code} body={body_snip}",
            pytrace=False,
        )
    except Exception as exc:  # noqa: BLE001 - 외부 API 실패 포괄
        metric["latency_seconds"] = round(time.monotonic() - start, 3)
        metric["error_type"] = type(exc).__name__
        metric["error_message"] = str(exc)[:500]
        CALL_STATE["results"].append(metric)
        pytest.fail(
            f"[{provider}/{scenario_name} #{repeat_idx}] API 호출 실패: {exc}",
            pytrace=False,
        )

    # 메트릭 후처리 ---------------------------------------------------------
    types_set: set[str] = set()
    total_components = 0
    for comp in _iter_components(schema):
        types_set.add(str(getattr(comp, "type", "unknown")))
        total_components += 1

    metric["component_types_used"] = sorted(types_set)
    metric["pages_count"] = len(schema.pages)
    metric["total_components_count"] = total_components
    all_text = _collect_text(schema)
    metric["korean_ratio"] = round(_korean_ratio(all_text), 3)
    metric["citations_included"] = bool(schema.metadata.citations)

    # 토큰 수집은 provider 응답에 접근 불가한 구조라 N/A (추후 client 계층 확장 시 채움)
    # 토큰 추정: 문자 수 / 2 (한국어 근사) - best effort.
    approx_output = max(1, len(json_module.dumps(schema.model_dump(mode="json"))) // 2)
    approx_input = max(1, (len(system_prompt) + len(user_prompt)) // 2)
    metric["input_tokens"] = approx_input
    metric["output_tokens"] = approx_output
    metric["total_tokens"] = approx_input + approx_output
    metric["estimated_cost_usd"] = round(_estimate_cost(provider, approx_input, approx_output), 6)

    CALL_STATE["results"].append(metric)

    # 시나리오별 품질 검증 --------------------------------------------------
    expect = scenario["expect"]
    assert expect["min_pages"] <= len(schema.pages) <= expect["max_pages"], (
        f"pages 수 {len(schema.pages)} 가 기대 범위 [{expect['min_pages']}, {expect['max_pages']}] 밖"
    )
    required = expect["required_component_types"]
    missing = required - types_set
    # 완전 누락 시 fail, 부분 누락은 경고 (Gemini 평탄화 케이스 고려).
    if missing:
        pytest.fail(
            f"[{provider}/{scenario_name} #{repeat_idx}] 필수 컴포넌트 누락: "
            f"{sorted(missing)}. 생성된 types={sorted(types_set)}",
            pytrace=False,
        )
    if "required_any_of" in expect:
        any_of = expect["required_any_of"]
        if not (any_of & types_set):
            pytest.fail(
                f"[{provider}/{scenario_name} #{repeat_idx}] "
                f"any_of={sorted(any_of)} 중 하나도 없음. generated={sorted(types_set)}",
                pytrace=False,
            )

    # 한국어 비율 50% 이상 기대 (실패는 fail 보다 경고로 남김 — 프로바이더 평가용).
    if metric["korean_ratio"] < 0.5:
        print(f"[WARN] {provider}/{scenario_name}#{repeat_idx} 한국어 비율 낮음: {metric['korean_ratio']:.2f}")

    return metric


# ---------------------------------------------------------------------------
# 파라미터화 테스트 — provider × scenario × repeat
# ---------------------------------------------------------------------------


def _build_params() -> list[tuple[str, str, int]]:
    params: list[tuple[str, str, int]] = []
    for scenario_name, cfg in SCENARIOS.items():
        for repeat in range(cfg["repeats"]):
            for provider in PROVIDERS:
                params.append((provider, scenario_name, repeat))
    return params


@pytest.mark.parametrize(
    ("provider", "scenario", "repeat"),
    _build_params(),
    ids=lambda v: str(v),
)
async def test_live_structured_generation(provider: str, scenario: str, repeat: int):
    """실 LLM API 로 DocumentSchema 생성 품질 검증 (시나리오 × 반복)."""
    await _run_single_call(provider, scenario, repeat)


# ---------------------------------------------------------------------------
# 세션 종료 시 메트릭 저장
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def _dump_metrics_on_exit():
    """세션 종료 시 raw 메트릭 JSON + 요약 MD 를 남긴다."""
    yield
    if not CALL_STATE["results"]:
        return

    base_dir = Path(__file__).resolve().parent / "qa_reports"
    base_dir.mkdir(parents=True, exist_ok=True)
    date_tag = time.strftime("%Y%m%d")

    raw_path = base_dir / f"{date_tag}_s1_d7_live_api_metrics.json"
    raw_path.write_text(
        json_module.dumps(CALL_STATE["results"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 요약 MD 생성.
    md = _render_summary_md(CALL_STATE["results"])
    md_path = base_dir / f"{date_tag}_s1_d7_live_api_report.md"
    md_path.write_text(md, encoding="utf-8")
    print(f"\n[live_api] 메트릭 저장: {raw_path}")
    print(f"[live_api] 요약 저장: {md_path}")


def _render_summary_md(results: list[dict[str, Any]]) -> str:
    """provider × scenario 집계 표를 Markdown 으로 렌더."""
    lines: list[str] = []
    lines.append("# Phase 4 S1 D7 Live API 검증 리포트")
    lines.append("")
    lines.append(f"- 총 호출 수: {len(results)}")
    total_cost = sum(r.get("estimated_cost_usd") or 0 for r in results)
    lines.append(f"- 추정 총 비용 (USD): {total_cost:.4f}")
    lines.append("")

    # provider 별 통과율
    lines.append("## 프로바이더별 요약")
    lines.append("")
    lines.append("| provider | calls | passed | pass_rate | avg_latency_s | avg_cost_usd |")
    lines.append("|----------|-------|--------|-----------|---------------|--------------|")
    providers = sorted({r["provider"] for r in results})
    for p in providers:
        subset = [r for r in results if r["provider"] == p]
        passed = [r for r in subset if r["schema_validation_passed"]]
        lat = [r["latency_seconds"] for r in subset if r["latency_seconds"] is not None]
        cost = [r["estimated_cost_usd"] for r in subset if r["estimated_cost_usd"] is not None]
        pr = (len(passed) / len(subset) * 100) if subset else 0.0
        avg_lat = (sum(lat) / len(lat)) if lat else 0.0
        avg_cost = (sum(cost) / len(cost)) if cost else 0.0
        lines.append(f"| {p} | {len(subset)} | {len(passed)} | {pr:.1f}% | {avg_lat:.2f} | {avg_cost:.6f} |")
    lines.append("")

    # 시나리오별 요약
    lines.append("## 시나리오별 요약")
    lines.append("")
    lines.append("| scenario | calls | passed | avg_pages | avg_components | avg_korean |")
    lines.append("|----------|-------|--------|-----------|----------------|------------|")
    scenarios = sorted({r["scenario"] for r in results})
    for s in scenarios:
        subset = [r for r in results if r["scenario"] == s]
        passed = [r for r in subset if r["schema_validation_passed"]]
        avg_pages = (sum(r["pages_count"] for r in passed) / len(passed)) if passed else 0
        avg_comp = (sum(r["total_components_count"] for r in passed) / len(passed)) if passed else 0
        kor = [r["korean_ratio"] for r in passed if r["korean_ratio"] is not None]
        avg_kor = (sum(kor) / len(kor)) if kor else 0.0
        lines.append(f"| {s} | {len(subset)} | {len(passed)} | {avg_pages:.1f} | {avg_comp:.1f} | {avg_kor:.2f} |")
    lines.append("")

    # 실패 케이스 목록
    failures = [r for r in results if not r["schema_validation_passed"]]
    if failures:
        lines.append("## 실패 케이스")
        lines.append("")
        for f in failures:
            lines.append(f"- [{f['provider']}/{f['scenario']} #{f['repeat']}] {f['error_type']}: {f['error_message']}")
        lines.append("")

    return "\n".join(lines)
