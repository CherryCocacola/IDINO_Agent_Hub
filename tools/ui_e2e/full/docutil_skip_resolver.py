"""트랙 #88-4 — DocUtil 22 SKIP 시나리오 재검증.

트랙 #88 옵션 A + Part 2 동기화로 admin@example.com 자격증명이 DocUtil 에도 적용됨.
양쪽 비번 hash 동일 (BCrypt $2a/$2b 모두 검증 가능).

원칙:
- DocUtil 로그인 1회 → storage_state 재사용
- 22 라우트 진입 검증 (DOM 마운트 + 콘솔/네트워크 에러)
- live_results.json 의 기존 SKIP 22건 → 신규 결과로 머지
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

from common import (
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    DOCUTIL_NGINX,
    chrome,
    now_ts,
)
from routes_catalog import DOCUTIL_ROUTES

FULL_SCREENSHOTS = Path(__file__).resolve().parents[1] / "screenshots" / "full"
FULL_SCREENSHOTS.mkdir(parents=True, exist_ok=True)
RESULT_PATH = Path(__file__).parent / "live_results.json"
DOCUTIL_RESULT_PATH = Path(__file__).parent / "docutil_skip_resolved.json"
DU_STATE_PATH = Path(__file__).parent / "_docutil_state.json"


def shot_full(page, name: str) -> str:
    safe = name.replace("/", "_").replace("\\", "_").replace(":", "_").replace("?", "")[:80]
    path = FULL_SCREENSHOTS / f"{safe}.png"
    try:
        page.screenshot(path=str(path), full_page=False)
        return str(path).replace("\\", "/")
    except Exception as e:
        return f"(screenshot failed: {e})"


def docutil_login(page, email: str, password: str) -> tuple[bool, str]:
    """DocUtil 로그인 — 정확한 selector (id=username, id=password)."""
    page.goto(f"{DOCUTIL_NGINX}/login", timeout=30_000, wait_until="domcontentloaded")
    time.sleep(3.0)  # Next.js hydration 대기

    username_input = page.query_selector('input#username')
    password_input = page.query_selector('input#password')
    if not username_input or not password_input:
        return False, "login form inputs not found"

    username_input.fill("")
    username_input.fill(email)
    password_input.fill("")
    password_input.fill(password)
    print(f"  [fill] username={email}, password=*** (len={len(password)})")

    submit = page.query_selector('button[type="submit"]')
    if not submit:
        return False, "submit button not found"
    submit.click()

    # API 응답 + dashboard redirect 대기 (충분히 길게)
    try:
        page.wait_for_url(lambda url: "/login" not in url, timeout=15_000)
    except Exception:
        pass
    time.sleep(2.0)
    final_url = page.url
    success = "/login" not in final_url
    return success, final_url


def visit_route(
    page,
    base: str,
    path: str,
    case_prefix: str,
    *,
    role: str,
    timeout_ms: int = 20_000,
) -> dict:
    started = time.time()
    console_errors = []
    network_errors = []

    def on_console(msg):
        if msg.type == "error":
            console_errors.append(msg.text[:300])

    def on_response(resp):
        if resp.status >= 400:
            network_errors.append({
                "url": resp.url[:200],
                "status": resp.status,
                "method": resp.request.method,
            })

    page.on("console", on_console)
    page.on("response", on_response)

    url_visited = f"{base}{path}"
    redirected = False
    dom_mounted = False
    try:
        page.goto(url_visited, timeout=timeout_ms, wait_until="domcontentloaded")
        time.sleep(2.0)
        final_url = page.url
        redirected = url_visited != final_url and "/login" in final_url
        # DOM 마운트 검증 — body 가 비어있지 않으면 마운트 OK
        body_text = page.evaluate("document.body.innerText.length")
        dom_mounted = body_text > 50  # 최소 50자

        screenshot = shot_full(page, f"s88_{case_prefix}")
        status = "PASS" if dom_mounted and not redirected else ("FAIL" if redirected else "PARTIAL")
        note = ""
        if redirected:
            note = "로그인 페이지로 리디렉트 — 인증 만료 가능성"
        elif not dom_mounted:
            note = f"DOM 마운트 실패 — body innerText {body_text}자"
    except Exception as e:
        final_url = page.url
        screenshot = ""
        status = "FAIL"
        note = f"예외: {str(e)[:200]}"

    page.remove_listener("console", on_console)
    page.remove_listener("response", on_response)

    return {
        "case_prefix": case_prefix,
        "path": path,
        "role": role,
        "started_at": now_ts(),
        "url_visited": url_visited,
        "screenshot": screenshot,
        "dom_mounted": dom_mounted,
        "console_errors": console_errors[:10],
        "network_4xx_5xx": network_errors[:10],
        "final_url": final_url,
        "redirected": redirected,
        "duration_ms": int((time.time() - started) * 1000),
        "status": status,
        "note": note,
    }


def main():
    print(f"[track #88-4] start at {now_ts()}")
    out = {
        "track": "88-4 — DocUtil 22 SKIP 재검증",
        "started_at": now_ts(),
        "results": [],
        "summary": {"PASS": 0, "FAIL": 0, "PARTIAL": 0, "LOGIN_FAILED": 0},
    }

    with chrome(headless=True) as (_p, _b, ctx, page):
        # 1. DocUtil admin 로그인 — admin@example.com (super_admin 권한 동기화)
        print(f"\n[1] DocUtil admin 로그인 시도 — {ADMIN_EMAIL}")
        success, final = docutil_login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        print(f"  결과: success={success} final={final}")
        if not success:
            print("[ERROR] DocUtil admin 로그인 실패")
            for _, path, _, _ in DOCUTIL_ROUTES:
                out["results"].append({
                    "case_prefix": f"DU_{_}",
                    "status": "LOGIN_FAILED",
                    "note": f"DocUtil 로그인 실패: {final}",
                })
                out["summary"]["LOGIN_FAILED"] += 1
            DOCUTIL_RESULT_PATH.write_text(
                json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
            return

        # storage_state 저장
        ctx.storage_state(path=str(DU_STATE_PATH))
        print(f"  storage_state 저장: {DU_STATE_PATH}")

        # 2. 22 라우트 (admin role) 진입 검증
        print("\n[2] DocUtil 인증 의존 라우트 진입")
        for screen, path, _f, role in DOCUTIL_ROUTES:
            if role == "anon":
                continue
            cp = f"DU_{screen}"
            r = visit_route(page, DOCUTIL_NGINX, path, cp, role=role)
            out["results"].append(r)
            out["summary"][r["status"]] = out["summary"].get(r["status"], 0) + 1
            print(f"  [{r['status']:<8}] {path:<25} dom={r['dom_mounted']} "
                  f"console_err={len(r['console_errors'])} net_err={len(r['network_4xx_5xx'])} "
                  f"({r['duration_ms']}ms)")

    out["finished_at"] = now_ts()
    DOCUTIL_RESULT_PATH.write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[track #88-4] summary: {out['summary']}")
    print(f"[track #88-4] saved: {DOCUTIL_RESULT_PATH}")


if __name__ == "__main__":
    main()
