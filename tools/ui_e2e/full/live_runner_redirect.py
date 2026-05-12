"""트랙 #83 — 추가 라이브: 모든 protected 라우트의 anonymous redirect 검증.

live_runner.py 의 4단계는 샘플 5개만 진행 → 나머지 41개 protected 라우트도 전부 검증.
"""
from __future__ import annotations
import io
import json
import sys
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).parent))

from common import AGENTHUB_BASE, chrome, now_ts
from routes_catalog import PROTECTED_ROUTES

RESULT_PATH = Path(__file__).parent / "live_results_redirect.json"


def main() -> None:
    print(f"[redirect_runner] start at {now_ts()}")
    results = []
    with chrome(headless=True) as (_p, _b, _ctx, page):
        for screen, path, _vue in PROTECTED_ROUTES:
            started = time.time()
            try:
                page.goto(f"{AGENTHUB_BASE}{path}", timeout=12_000, wait_until="domcontentloaded")
                # SPA router beforeEach 실행 대기 (live_runner.py 와 동일하게 1.2초 + networkidle)
                time.sleep(1.2)
                try:
                    page.wait_for_load_state("networkidle", timeout=4_000)
                except Exception:
                    pass
                # 라우터 가드가 다시 한 번 동작할 시간 보장
                time.sleep(0.3)
                final = page.url
                redirected_to_login = ("/login" in final) or ("/landing" in final)
                status = "PASS" if redirected_to_login else "FAIL"
                note = f"final={final[:120]}"
                if not redirected_to_login:
                    note += " — anonymous 진입이 차단되지 않음 (보안 우려)"
            except Exception as e:
                status = "FAIL"
                final = ""
                note = f"exception: {type(e).__name__}: {e}"[:120]
            duration = int((time.time() - started) * 1000)
            results.append({
                "screen": screen,
                "path": path,
                "status": status,
                "final_url": final,
                "note": note,
                "duration_ms": duration,
            })
            print(f"  [{status}] {path} -> {final[:60]}")
    out = {
        "started_at": now_ts(),
        "results": results,
        "summary": {
            "PASS": sum(1 for r in results if r["status"] == "PASS"),
            "FAIL": sum(1 for r in results if r["status"] == "FAIL"),
        },
    }
    RESULT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[redirect_runner] summary: {out['summary']}")
    print(f"[redirect_runner] saved: {RESULT_PATH}")


if __name__ == "__main__":
    main()
