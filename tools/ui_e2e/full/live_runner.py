"""트랙 #83 — 라이브 e2e 러너 (Playwright sync).

전수 라우트 진입 + DOM 마운트 검증 + 스크린샷 저장 + JSON 결과 기록.

원칙:
- AgentHub admin 1회 로그인 → storage_state 재사용 (모든 protected 라우트)
- anonymous 분기는 별도 컨텍스트
- DocUtil 인증 의존 라우트는 SKIP (자격증명 미확보)
- mutation/cost 라우트는 SKIP — 시나리오 1~3 결과 인용

실행:
  python tools/ui_e2e/full/live_runner.py

출력:
  tools/ui_e2e/full/live_results.json     — 케이스별 결과
  tools/ui_e2e/screenshots/full/*.png     — 라우트별 스크린샷
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
    AGENTHUB_BASE,
    DOCUTIL_NGINX,
    chrome,
    now_ts,
)
from routes_catalog import (
    DOCUTIL_ROUTES,
    PROTECTED_ROUTES,
    PUBLIC_ROUTES,
)

FULL_SCREENSHOTS = Path(__file__).resolve().parents[1] / "screenshots" / "full"
FULL_SCREENSHOTS.mkdir(parents=True, exist_ok=True)
STATE_PATH = Path(__file__).parent / "_admin_state.json"
RESULT_PATH = Path(__file__).parent / "live_results.json"


def shot_full(page, name: str) -> str:
    """full/ 디렉토리에 스크린샷 저장."""
    safe = name.replace("/", "_").replace("\\", "_").replace(":", "_").replace("?", "")[:80]
    path = FULL_SCREENSHOTS / f"{safe}.png"
    try:
        page.screenshot(path=str(path), full_page=False)
        return str(path).replace("\\", "/")
    except Exception as e:
        return f"(screenshot failed: {e})"


def admin_login(page) -> bool:
    """admin 로그인 → storage_state 저장."""
    page.goto(f"{AGENTHUB_BASE}/login", timeout=20_000)
    page.wait_for_load_state("domcontentloaded")
    try:
        page.fill('input[type="email"], input[name="email"]', ADMIN_EMAIL)
        page.fill('input[type="password"], input[name="password"]', ADMIN_PASSWORD)
        # 다양한 셀렉터 시도
        clicked = False
        for sel in ['button[type="submit"]', 'button:has-text("로그인")', 'button:has-text("Login")']:
            try:
                btn = page.query_selector(sel)
                if btn:
                    btn.click()
                    clicked = True
                    break
            except Exception:
                pass
        if not clicked:
            return False
        page.wait_for_load_state("networkidle", timeout=15_000)
        # 로그인 성공 여부 — / 또는 /dashboard 등으로 이동했는지
        time.sleep(1.0)
        url = page.url
        return "/login" not in url
    except Exception as e:
        print(f"  login error: {e}")
        return False


def visit_route(
    page,
    base: str,
    path: str,
    case_prefix: str,
    *,
    role: str,
    timeout_ms: int = 15_000,
) -> dict:
    """단일 라우트 진입 검증."""
    started = time.time()
    result: dict = {
        "case_prefix": case_prefix,
        "path": path,
        "role": role,
        "started_at": now_ts(),
        "url_visited": f"{base}{path}",
        "screenshot": None,
        "dom_mounted": False,
        "console_errors": [],
        "network_4xx_5xx": [],
        "final_url": "",
        "redirected": False,
        "duration_ms": 0,
        "status": "FAIL",  # 기본 FAIL, 성공 시 PASS
        "note": "",
    }
    console_errors: list[str] = []
    net_issues: list[dict] = []

    def on_console(msg):
        try:
            if msg.type == "error":
                # 외부 라이브러리 noise 일부 제외
                text = msg.text
                ignore = ("Failed to load resource", "favicon", "extension")
                if not any(x in text for x in ignore):
                    console_errors.append(text[:200])
        except Exception:
            pass

    def on_response(resp):
        try:
            if resp.status >= 400 and "/_next/" not in resp.url and "favicon" not in resp.url:
                net_issues.append({"url": resp.url[:120], "status": resp.status})
        except Exception:
            pass

    page.on("console", on_console)
    page.on("response", on_response)

    try:
        page.goto(f"{base}{path}", timeout=timeout_ms, wait_until="domcontentloaded")
        # DOM 안정화 1.2초
        time.sleep(1.2)
        try:
            page.wait_for_load_state("networkidle", timeout=5_000)
        except Exception:
            pass
        result["final_url"] = page.url
        result["redirected"] = page.url != f"{base}{path}"
        result["dom_mounted"] = True

        # 스크린샷
        ss = shot_full(page, case_prefix)
        result["screenshot"] = ss

        # 결과 판정
        result["console_errors"] = console_errors[:5]
        result["network_4xx_5xx"] = net_issues[:5]
        # PASS 조건: DOM 마운트 + 5xx 0건
        has_5xx = any(n["status"] >= 500 for n in net_issues)
        result["status"] = "FAIL" if has_5xx else "PASS"
        if console_errors:
            result["note"] = f"console_errors={len(console_errors)}"
    except Exception as e:
        result["status"] = "FAIL"
        result["note"] = f"exception: {type(e).__name__}: {e}"[:200]
    finally:
        result["duration_ms"] = int((time.time() - started) * 1000)
        # 핸들러 분리
        try:
            page.remove_listener("console", on_console)
            page.remove_listener("response", on_response)
        except Exception:
            pass

    return result


def run() -> dict:
    out: dict = {
        "track": "#83 전수 라이브 e2e",
        "started_at": now_ts(),
        "routes_total": 0,
        "results": [],
        "summary": {"PASS": 0, "FAIL": 0, "SKIP": 0},
        "notes": [],
    }

    # ── 1단계: AgentHub admin 로그인 → storage_state 저장 ──
    print("[1] AgentHub admin 로그인 시도...")
    with chrome(headless=True) as (_p, _b, ctx, page):
        ok = admin_login(page)
        if not ok:
            out["notes"].append("admin 로그인 실패 — protected 라우트 전부 SKIP")
            print("  admin 로그인 실패")
        else:
            ctx.storage_state(path=str(STATE_PATH))
            print(f"  admin 로그인 성공 → {STATE_PATH.name}")

    if not STATE_PATH.exists():
        # 로그인 실패 시 protected/admin 라우트 전부 SKIP
        for screen, path, _vue in PROTECTED_ROUTES:
            out["results"].append({
                "case_prefix": f"AH_PROT_{screen}",
                "path": path,
                "role": "admin",
                "status": "SKIP",
                "note": "admin 로그인 실패",
            })
            out["summary"]["SKIP"] += 1
        # public 라우트도 admin 세션 없이 anonymous 만 진행
        for screen, path, _vue in PUBLIC_ROUTES:
            with chrome(headless=True) as (_p, _b, _ctx, page):
                r = visit_route(page, AGENTHUB_BASE, path, f"AH_PUB_{screen}", role="anon")
                out["results"].append(r)
                out["summary"][r["status"]] += 1
        # DocUtil
        for screen, path, _f, role in DOCUTIL_ROUTES:
            if role != "anon":
                out["results"].append({
                    "case_prefix": f"DU_{screen}",
                    "path": path,
                    "role": role,
                    "status": "SKIP",
                    "note": "DocUtil 자격증명 미확보",
                })
                out["summary"]["SKIP"] += 1
            else:
                with chrome(headless=True) as (_p, _b, _ctx, page):
                    r = visit_route(page, DOCUTIL_NGINX, path, f"DU_{screen}", role="anon")
                    out["results"].append(r)
                    out["summary"][r["status"]] += 1
        return out

    # ── 2단계: AgentHub public 라우트 (anonymous) ──
    print("[2] AgentHub public 라우트 진입 (anonymous)...")
    with chrome(headless=True) as (_p, _b, _ctx, page):
        for screen, path, _vue in PUBLIC_ROUTES:
            cp = f"AH_PUB_{screen}"
            r = visit_route(page, AGENTHUB_BASE, path, cp, role="anon")
            out["results"].append(r)
            out["summary"][r["status"]] += 1
            print(f"  [{r['status']}] {path} ({r['duration_ms']}ms)")

    # ── 3단계: AgentHub protected 라우트 (admin) ──
    print("[3] AgentHub protected 라우트 진입 (admin)...")
    with chrome(headless=True, storage_state=str(STATE_PATH)) as (_p, _b, _ctx, page):
        for screen, path, _vue in PROTECTED_ROUTES:
            cp = f"AH_PROT_{screen}"
            r = visit_route(page, AGENTHUB_BASE, path, cp, role="admin")
            out["results"].append(r)
            out["summary"][r["status"]] += 1
            print(f"  [{r['status']}] {path} ({r['duration_ms']}ms)")

    # ── 4단계: AgentHub protected 라우트 anonymous 차단 검증 (샘플) ──
    print("[4] AgentHub admin-only anonymous redirect 검증 (샘플 5개)...")
    sample_paths = ["/", "/users", "/agents", "/api-keys", "/admin/knowledge-base"]
    with chrome(headless=True) as (_p, _b, _ctx, page):
        for path in sample_paths:
            cp = f"AH_AUTH_REDIR_{path.replace('/', '_')}"
            r = visit_route(page, AGENTHUB_BASE, path, cp, role="anon")
            # 추가 판정: /login 또는 /landing 으로 리다이렉트 되었는지
            final = r.get("final_url", "")
            if "/login" in final or "/landing" in final:
                r["status"] = "PASS"
                r["note"] = f"redirected to {final}"
            else:
                # 보호되지 않은 경우 FAIL
                if r["status"] == "PASS":
                    r["status"] = "FAIL"
                    r["note"] = "anonymous 진입이 차단되지 않음 — 보안 우려"
            out["results"].append(r)
            out["summary"][r["status"]] = out["summary"].get(r["status"], 0) + 1
            print(f"  [{r['status']}] {path} -> {final[:60]}")

    # ── 5단계: DocUtil 공개 라우트 (anonymous) ──
    print("[5] DocUtil 공개 라우트 진입 (anonymous)...")
    with chrome(headless=True) as (_p, _b, _ctx, page):
        for screen, path, _f, role in DOCUTIL_ROUTES:
            if role != "anon":
                continue
            cp = f"DU_{screen}"
            r = visit_route(page, DOCUTIL_NGINX, path, cp, role="anon")
            out["results"].append(r)
            out["summary"][r["status"]] += 1
            print(f"  [{r['status']}] {path} ({r['duration_ms']}ms)")

    # ── 6단계: DocUtil 인증 의존 라우트 SKIP 처리 ──
    print("[6] DocUtil 인증 의존 라우트 SKIP (자격증명 미확보)...")
    for screen, path, _f, role in DOCUTIL_ROUTES:
        if role == "anon":
            continue
        out["results"].append({
            "case_prefix": f"DU_{screen}",
            "path": path,
            "role": role,
            "status": "SKIP",
            "note": "DocUtil 자격증명 미확보 — 트랙 #75 시나리오 4 인용",
        })
        out["summary"]["SKIP"] += 1

    out["routes_total"] = len(out["results"])
    out["finished_at"] = now_ts()
    return out


def main() -> None:
    print(f"[live_runner] start at {now_ts()}")
    out = run()
    print(f"\n[live_runner] summary: {out['summary']}")
    print(f"[live_runner] total: {out['routes_total']}")
    RESULT_PATH.write_text(
        json.dumps(out, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[live_runner] saved: {RESULT_PATH}")


if __name__ == "__main__":
    main()
