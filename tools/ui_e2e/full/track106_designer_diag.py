"""트랙 #106 결함 2-1 — DocUtil /designer/[documentId] 진단 runner.

목적:
  사용자 보고 결함을 운영 UI 로 재현 + DevTools network/console 캡처.
  1) /designer/create 진입 → prompt 입력 + 생성
  2) 우측 design-token-picker 의 브랜드 프리셋 클릭 → PATCH 발송 여부
  3) 내보내기 버튼 → POST export → 폴링 → download blob

운영 데이터 영향 최소화:
  - prompt 는 "ui-e2e-test-track106-" prefix 로 시작.
  - LLM 호출 1회 (문서 생성). PATCH/EXPORT 는 LLM 무관.

산출:
  - tools/ui_e2e/full/track106_designer_diag_results.json
  - tools/ui_e2e/screenshots/track106_designer/*.png
  - tools/ui_e2e/full/track106_designer_diag_network.json
"""
from __future__ import annotations

import io
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from playwright.sync_api import Page, sync_playwright

OUT_DIR = Path(__file__).parent
SHOT_DIR = OUT_DIR.parent / "screenshots" / "track106_designer"
SHOT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_PATH = OUT_DIR / "track106_designer_diag_results.json"
NETWORK_PATH = OUT_DIR / "track106_designer_diag_network.json"

DOCUTIL = "http://192.168.10.39:8041"
EMAIL = "admin@example.com"
PWD = "Admin123!"


def shot(page: Page, name: str) -> str:
    p = SHOT_DIR / f"{name}.png"
    page.screenshot(path=str(p), full_page=False)
    return str(p)


def main() -> int:
    network_log: list[dict] = []
    console_log: list[dict] = []
    results: dict = {
        "timestamp": datetime.now().isoformat(),
        "steps": [],
        "verdict": {},
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()

        # Capture network for /v2/documents/*
        def on_request(req):
            if "/v2/documents" in req.url:
                network_log.append({
                    "kind": "req",
                    "method": req.method,
                    "url": req.url,
                    "ts": time.time(),
                })

        def on_response(resp):
            if "/v2/documents" in resp.url:
                try:
                    body_text = resp.text() if resp.request.method != "GET" or resp.headers.get("content-type", "").startswith("application/json") else ""
                except Exception:
                    body_text = "<unread>"
                network_log.append({
                    "kind": "resp",
                    "method": resp.request.method,
                    "url": resp.url,
                    "status": resp.status,
                    "body_preview": body_text[:500] if isinstance(body_text, str) else "",
                    "ts": time.time(),
                })

        def on_console(msg):
            console_log.append({"type": msg.type, "text": msg.text[:500]})

        page.on("request", on_request)
        page.on("response", on_response)
        page.on("console", on_console)

        # 1) login
        page.goto(f"{DOCUTIL}/login", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_selector("input#username", timeout=10000)
        page.fill("input#username", EMAIL)
        page.fill("input#password", PWD)
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle", timeout=20000)
        shot(page, "01_after_login")
        results["steps"].append({"name": "login", "url": page.url, "ok": "/login" not in page.url})

        # 2) /designer/create
        page.goto(f"{DOCUTIL}/designer/create", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)
        shot(page, "02_designer_create")
        results["steps"].append({"name": "designer_create_open", "url": page.url})

        # 3) prompt 입력
        # PromptInput 컴포넌트 — find textarea
        try:
            ta = page.locator("textarea").first
            ta.wait_for(state="visible", timeout=10000)
            ta.fill("ui-e2e-test-track106-diag: 3페이지 짧은 슬라이드 — 제목/요약/결론")
        except Exception as e:
            results["steps"].append({"name": "prompt_fill", "error": str(e)})
            results["verdict"]["prompt_input"] = "FAIL"

        # 4) 생성 버튼 클릭 (PromptInput 내부 submit)
        try:
            # Try multiple button selectors
            gen_btn = None
            for sel in [
                'button:has-text("생성")',
                'button:has-text("Generate")',
                '[data-testid="prompt-submit"]',
                'button[type="submit"]',
            ]:
                loc = page.locator(sel).first
                if loc.count() > 0 and loc.is_visible():
                    gen_btn = loc
                    break
            if gen_btn is None:
                results["steps"].append({"name": "find_submit", "error": "no submit button visible"})
            else:
                gen_btn.click()
                results["steps"].append({"name": "click_generate", "ok": True})
        except Exception as e:
            results["steps"].append({"name": "click_generate", "error": str(e)})

        # 5) 문서 생성 완료 대기 (URL replace → /designer/{uuid})
        doc_id = None
        started = time.time()
        while time.time() - started < 60:
            url = page.url
            if "/designer/" in url and "/create" not in url:
                parts = url.rstrip("/").split("/")
                doc_id = parts[-1]
                break
            page.wait_for_timeout(500)
        shot(page, "03_after_generate")
        results["steps"].append({"name": "wait_doc_id", "doc_id": doc_id, "url": page.url})
        results["verdict"]["doc_generation"] = "PASS" if doc_id else "FAIL"

        # 6) 브랜드 프리셋 버튼 클릭
        page.wait_for_timeout(2000)  # render
        try:
            preset_btns = page.locator('[data-preset-id]')
            preset_count = preset_btns.count()
            results["steps"].append({"name": "preset_buttons_visible", "count": preset_count})
            if preset_count > 1:
                # Click second preset (not the currently active one)
                target_preset = preset_btns.nth(1)
                preset_label = target_preset.get_attribute("data-preset-label")
                target_preset.click()
                results["steps"].append({"name": "click_preset", "label": preset_label})
                page.wait_for_timeout(1500)  # debounce 500ms + http
                shot(page, "04_after_preset_click")
        except Exception as e:
            results["steps"].append({"name": "click_preset", "error": str(e)})

        # 7) 내보내기 버튼 (PPTX)
        try:
            trigger = page.locator('[data-testid="export-menu-trigger"]').first
            trigger.wait_for(state="visible", timeout=5000)
            trigger.click()
            page.wait_for_timeout(500)
            pptx_item = page.locator('[data-testid="export-menu-item-pptx"]').first
            pptx_item.click()
            results["steps"].append({"name": "click_export_pptx", "ok": True})
            page.wait_for_timeout(8000)  # wait for build + poll
            shot(page, "05_after_export_click")
        except Exception as e:
            results["steps"].append({"name": "click_export_pptx", "error": str(e)})

        # Final state
        shot(page, "06_final_state")
        results["network_count"] = len(network_log)
        results["console_count"] = len(console_log)

        ctx.close()
        browser.close()

    # Save logs
    RESULT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    NETWORK_PATH.write_text(json.dumps({"network": network_log, "console": console_log}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] results -> {RESULT_PATH}")
    print(f"[OK] network -> {NETWORK_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
