"""트랙 #105 Phase C 보강 — 자동화 전환 7건 + manual 잔존 20건 분류 검증 (단축 runner).

목적: 본 매트릭스(644 cells) 전수 실행 없이, Phase C 보강에서 새로 추가한 7건 SPECIAL_HANDLERS
       만 4계정으로 검증 (28 cells, ~3-5분 예상). manual 잔존 케이스는 분류만 검증.

산출:
  - tools/ui_e2e/full/track105_phase_c_boost_verify_results.json
"""
from __future__ import annotations

import io
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).parent))

# track105 import 가 sys.stdout 을 갈아끼우면서 기존 buffer 가 close 될 수 있음.
# fileno() 기반 fresh wrapper 를 강제로 박아넣어 안전 확보.
_real_stdout_fd = sys.__stdout__.fileno() if sys.__stdout__ else 1

from common import DEFAULT_TIMEOUT_MS, DOCUTIL_NGINX, VIEWPORT, now_ts  # noqa: E402
from docutil_page_catalog import CASES  # noqa: E402
from e2e_helpers import allow_cost, allow_mutation  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

# 본 runner 의 단일 case 실행 함수 + special handlers 재사용 (이 import 가 sys.stdout 을 갈아끼움)
from track105_docutil_full_e2e import (  # noqa: E402
    ACCOUNTS,
    ADMIN_LABELS,
    PASSWORD,
    SPECIAL_HANDLERS,
    docutil_login,
    run_single_case,
)

# stdout 재확인 — 닫혀 있으면 fresh wrapper 로 교체
def _safe_print(*args, **kwargs):
    """sys.stdout 이 닫혀 있을 때도 작동하는 print fallback."""
    msg = " ".join(str(a) for a in args) + "\n"
    try:
        os.write(_real_stdout_fd, msg.encode("utf-8", errors="replace"))
    except Exception:
        pass

OUT = Path(__file__).parent / "track105_phase_c_boost_verify_results.json"

# 검증 대상 case_id — Phase C 보강 7건 + manual 잔존 분류 확인용 일부
TARGET_CASE_IDS = sorted(SPECIAL_HANDLERS.keys())  # 7건

# manual 잔존 분류 — 카탈로그에서 자동 추출
MANUAL_REMAINING = [c for c in CASES if c["automation_mode"] == "manual"]


def main() -> None:
    _safe_print(f"[track105 Phase C 보강 verify] start at {now_ts()}")
    _safe_print(f"[flag] E2E_ALLOW_COST={allow_cost()}, E2E_ALLOW_MUTATION={allow_mutation()}")
    _safe_print(f"[targets] auto-converted {len(TARGET_CASE_IDS)} cases × 4 accounts = {len(TARGET_CASE_IDS)*4} cells")
    _safe_print(f"[manual remaining] {len(MANUAL_REMAINING)} cases (classification only, no runtime)")

    out = {
        "track": "#105 Phase C 보강 verify",
        "ran_at": now_ts(),
        "base_url": DOCUTIL_NGINX,
        "flags": {
            "E2E_ALLOW_COST": allow_cost(),
            "E2E_ALLOW_MUTATION": allow_mutation(),
        },
        "target_case_ids": TARGET_CASE_IDS,
        "manual_remaining_classification": [
            {
                "case_id": c["id"],
                "page": c["page"],
                "risk_level": c["risk_level"],
                "reason": _classify_manual(c),
            }
            for c in MANUAL_REMAINING
        ],
        "logins": [],
        "results": [],
        "summary": {},
    }

    # 대상 case 객체 조회
    target_cases = [c for c in CASES if c["id"] in set(TARGET_CASE_IDS)]
    if len(target_cases) != len(TARGET_CASE_IDS):
        missing = set(TARGET_CASE_IDS) - {c["id"] for c in target_cases}
        _safe_print(f"[ERROR] 카탈로그에 미존재 case_id: {missing}")
        return

    with sync_playwright() as p:
        # 1) 4계정 로그인
        _safe_print("\n[1] 4계정 로그인")
        for acc in ACCOUNTS:
            _safe_print(f"  → {acc['label']}")
            login = docutil_login(p, acc["login_id"], PASSWORD, acc["state_path"])
            out["logins"].append({
                "label": acc["label"], "ok": login["ok"], "url": login["url"], "note": login["note"],
            })
            _safe_print(f"     ok={login['ok']} note={login['note']}")
        ok_labels = {li["label"] for li in out["logins"] if li["ok"]}
        if not ok_labels:
            _safe_print("[ERROR] 모든 계정 로그인 실패. 종료.")
            OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
            return

        # 2) 7건 × 4계정 실행
        _safe_print(f"\n[2] target {len(target_cases)} cases × {len(ACCOUNTS)} accounts 실행")
        for acc in ACCOUNTS:
            if acc["label"] not in ok_labels:
                continue
            _safe_print(f"\n  [account] {acc['label']}")
            b = p.chromium.launch(headless=True)
            try:
                ctx = b.new_context(
                    viewport=VIEWPORT, locale="ko-KR",
                    ignore_https_errors=True, storage_state=str(acc["state_path"]),
                )
                ctx.set_default_timeout(DEFAULT_TIMEOUT_MS)
                page = ctx.new_page()
                for c in target_cases:
                    r = run_single_case(page, c, acc)
                    out["results"].append(r)
                    _safe_print(f"    [{r['verdict']:<5}] {c['id']:<14} {r['actual'][:130]}")
                ctx.close()
            finally:
                b.close()

    # 3) 집계
    summary = {"PASS": 0, "FAIL": 0, "SKIP": 0, "ERROR": 0}
    for r in out["results"]:
        v = r["verdict"]
        summary[v] = summary.get(v, 0) + 1
    out["summary"] = summary
    out["finished_at"] = now_ts()

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    _safe_print(f"\n[summary] {summary}")
    _safe_print(f"[saved] {OUT}")


def _classify_manual(case: dict) -> str:
    """manual 잔존 사유 분류."""
    risk = case["risk_level"]
    bl = case["button_label"]
    if risk == "cost":
        return "LLM cost (E2E_ALLOW_COST=1 시 별도 cost runner 에서 실행)"
    if "고아 벡터" in bl:
        return "운영 Qdrant 영향 큼 (벡터 영구 삭제) — 자동화 비권장"
    if "템플릿 파일 교체" in bl:
        return "MinIO 운영 template 덮어쓰기 위험 — 자동화 비권장"
    if "EditSidebar 속성" in bl:
        return "vue-flow 동적 selector 안정성 낮음 (자동화 비효율)"
    if "내보내기" in bl:
        return "선행 designer document 필요 (시나리오 의존도 高)"
    if "API Key 검증" in bl:
        return "외부 LLM ping cost — E2E_ALLOW_COST=1 시 별도 runner"
    if "스트리밍 중지" in bl:
        return "AbortController — SSE 진행 중에만 의미 — 시나리오 의존 (cost runner 일부)"
    if risk == "mutation" and "업로드" in bl:
        return "운영 Celery 임베딩 큐 트리거 — manual cleanup 의무"
    return "분류 미정"


if __name__ == "__main__":
    main()
