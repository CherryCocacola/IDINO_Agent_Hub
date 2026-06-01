"""트랙 #148 — 운영자 콘솔 종합 smoke 자동 매트릭스.

목적: 통합 작업 완료 후 운영자 콘솔의 주요 화면들을 자동 진입하여
콘솔 에러 + 핵심 element 존재 + HTTP 응답 정합성을 회귀 차단 차원에서 검증.
Phase 5.7 라우팅 매트릭스 (tools/integration/phase5_routing_matrix.py) 와
동일 패턴.

검증 시나리오 (admin 진입):
  주요 화면 자동 load + 콘솔 에러 0건 + 핵심 element 존재 확인.

결과: user_mig/ADMIN_CONSOLE_SMOKE.json 저장 + 콘솔 PASS/FAIL.
CI exit code: 전체 PASS=0, 1건 이상 FAIL=1.
"""
from __future__ import annotations
import argparse, asyncio, io, json, sys
from datetime import datetime, timezone
from pathlib import Path
from playwright.async_api import async_playwright, Page

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "http://192.168.10.39:64005"
EMAIL = "admin@example.com"
PASSWORD = "Admin123!"


# 시나리오: (path, name, required_selector_or_text)
SCENARIOS = [
    ("/",                          "대시보드",                ".page-content-wrap, .dashboard, main"),
    ("/users",                     "사용자 관리",             "table, .users-table, .user-list"),
    ("/agents",                    "Agent 선택",              ".ag-card, .ag-grid"),
    ("/agents/marketplace",        "Agent 마켓플레이스",      ".page-content-wrap"),
    ("/analytics",                 "통계",                    ".page-content-wrap"),
    ("/usage-history",             "사용 기록",               ".page-content-wrap"),
    ("/quota",                     "할당량 관리",             ".page-content-wrap"),
    ("/api-keys",                  "API Key 관리",            ".page-content-wrap"),
    ("/reports",                   "리포트 (트랙 #147 M1)",   ".page-content-wrap"),
    ("/settings",                  "설정 (M2 프로필 사진)",   ".list-group-item"),
    ("/help",                      "도움말 (트랙 #136 FAQ)",  ".page-content-wrap"),
    ("/team",                      "팀 관리",                 ".page-content-wrap"),
    ("/admin/docutil-users",       "DocUtil 사용자 관리",     ".page-content-wrap"),
    ("/admin/docutil-departments", "DocUtil 부서 관리",       ".page-content-wrap"),
    ("/admin/faqs",                "도움말 FAQ 관리 (#136)",  ".page-content-wrap"),
    ("/admin/tutorials",           "튜토리얼 관리 (#136)",    ".page-content-wrap"),
    ("/workflows",                 "워크플로우",              ".page-content-wrap"),
    ("/tools",                     "도구",                    ".page-content-wrap"),
]


async def login(page: Page) -> None:
    await page.goto(f"{URL}/login", wait_until="networkidle")
    await page.locator("input").nth(0).fill(EMAIL)
    await page.locator("input").nth(1).fill(PASSWORD)
    await page.locator('button[type="submit"]').first.click()
    try:
        await page.wait_for_url(lambda u: "/login" not in u, timeout=15000)
    except Exception:
        pass


async def check_screen(page: Page, path: str, name: str, selector: str) -> dict:
    console_errors: list[str] = []
    page_errors: list[str] = []
    network_failures: list[str] = []
    api_errors: list[dict] = []

    def on_console(msg):
        if msg.type == "error":
            text = msg.text[:300]
            # webpack/vite HMR 메시지나 사소한 favicon 결함은 noise — 필터
            if any(x in text for x in ("favicon.ico", "HMR", "[vite]")):
                return
            console_errors.append(text)

    def on_page_error(err):
        page_errors.append(str(err)[:300])

    def on_request_failed(req):
        url = req.url
        if any(x in url for x in ("favicon.ico", ".map")):
            return
        network_failures.append(f"{url} | {req.failure}")

    def on_response(resp):
        # 5xx 응답 추적
        if resp.status >= 500 and resp.status != 503:  # 503 은 OpenAI quota 의도된 응답
            api_errors.append({"url": resp.url, "status": resp.status})

    page.on("console", on_console)
    page.on("pageerror", on_page_error)
    page.on("requestfailed", on_request_failed)
    page.on("response", on_response)

    try:
        await page.goto(f"{URL}{path}", wait_until="networkidle", timeout=20000)
        # 진입 후 잠시 대기 (lazy load chunk 등)
        await page.wait_for_timeout(1500)

        # selector 존재 확인 (CSS selector — 콤마 OR)
        selectors = [s.strip() for s in selector.split(",")]
        selector_found = False
        for sel in selectors:
            try:
                count = await page.locator(sel).count()
                if count > 0:
                    selector_found = True
                    break
            except Exception:
                continue

        ok = (
            selector_found
            and len(console_errors) == 0
            and len(page_errors) == 0
            and len(api_errors) == 0
        )
        details = {
            "selector_found": selector_found,
            "console_errors": console_errors[:5],
            "page_errors": page_errors[:5],
            "api_errors": api_errors[:5],
            "network_failures": network_failures[:5],
        }
        status = "PASS" if ok else "FAIL"
    except Exception as e:
        status = "FAIL"
        details = {"exception": str(e)[:300]}

    finally:
        page.remove_listener("console", on_console)
        page.remove_listener("pageerror", on_page_error)
        page.remove_listener("requestfailed", on_request_failed)
        page.remove_listener("response", on_response)

    return {"path": path, "name": name, "status": status, "details": details}


async def main_async(out: Path) -> int:
    started = datetime.now(timezone.utc).isoformat()
    print(f"[smoke start] {started}\n")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1600, "height": 1000})
        page = await ctx.new_page()
        await login(page)

        results = []
        for path, name, sel in SCENARIOS:
            r = await check_screen(page, path, name, sel)
            label = "[PASS]" if r["status"] == "PASS" else "[FAIL]"
            print(f"  {label} {path:35s} — {name}")
            if r["status"] == "FAIL":
                # 결함 1줄 요약
                d = r["details"]
                hints = []
                if not d.get("selector_found", True):
                    hints.append(f"selector 부재")
                if d.get("console_errors"):
                    hints.append(f"console:{d['console_errors'][0][:80]}")
                if d.get("page_errors"):
                    hints.append(f"page:{d['page_errors'][0][:80]}")
                if d.get("api_errors"):
                    hints.append(f"api:{d['api_errors'][0]['url'].split('?')[0]}={d['api_errors'][0]['status']}")
                if d.get("exception"):
                    hints.append(f"ex:{d['exception'][:80]}")
                print(f"           → {' / '.join(hints)}")
            results.append(r)

        await browser.close()

    finished = datetime.now(timezone.utc).isoformat()
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    fail_count = len(results) - pass_count
    summary = {
        "started_at": started,
        "finished_at": finished,
        "host": URL,
        "passed": pass_count,
        "failed": fail_count,
        "total": len(results),
        "results": results,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[summary] PASS={pass_count} FAIL={fail_count} / 결과: {out}")
    return 0 if fail_count == 0 else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="user_mig/ADMIN_CONSOLE_SMOKE.json")
    args = parser.parse_args()
    code = asyncio.run(main_async(Path(args.out)))
    sys.exit(code)


if __name__ == "__main__":
    main()
