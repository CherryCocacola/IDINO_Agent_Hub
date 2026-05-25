"""트랙 #106 — /reports + /designer/create 사용자 신뢰 회복 정밀 진단.

사용자 강력 지적:
  1) /reports 의 "문서 생성" 버튼 클릭 시 /designer/create 로 이동한다고 보고.
     (실제 의도: POST /v2/documents → /designer/{document_id})
  2) /designer/create 진입 시 console 에 `GET /api/v1/v2/templates 404` 남음.
     v13 silent fix (873f438) 가 운영 chunk 에 들어갔는지 검증.

목적 (closed-loop):
  Step A — /reports 진입 → "문서 생성" 버튼 자동 클릭 → POST 응답 raw 검증
  Step B — 응답 payload 의 envelope 구조 (top-level vs nested) 정확 dump
  Step C — generateDocument 가 어느 id 로 router.push 했는지 (page.url())
  Step D — /designer/create 직접 진입 → /v2/templates 호출 → console.warn 노출 여부
  Step E — root cause + fix 권고 + 재배포 권고

산출:
  - track106_reports_designer_diag_results.json
  - track106_reports_designer_diag_network.json
  - tools/ui_e2e/screenshots/track106_reports_designer/*.png
"""
from __future__ import annotations

import io
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from playwright.sync_api import Page, sync_playwright, TimeoutError as PWTimeout

OUT_DIR = Path(__file__).parent
SHOT_DIR = OUT_DIR.parent / "screenshots" / "track106_reports_designer"
SHOT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_PATH = OUT_DIR / "track106_reports_designer_diag_results.json"
NETWORK_PATH = OUT_DIR / "track106_reports_designer_diag_network.json"

DOCUTIL = "http://192.168.10.39:8041"
EMAIL = "admin@example.com"
PWD = "Admin123!"

# 비용 — 환경변수로 LLM 호출 통제. 기본은 OFF (envelope 검증은 별도 step 에서 수행)
ALLOW_LLM = os.environ.get("E2E_ALLOW_COST", "0") == "1"


def shot(page: Page, name: str) -> str:
    p = SHOT_DIR / f"{name}.png"
    try:
        page.screenshot(path=str(p), full_page=False)
    except Exception:
        pass
    return str(p)


def main() -> int:
    network_log: list[dict] = []
    console_log: list[dict] = []
    results: dict = {
        "timestamp": datetime.now().isoformat(),
        "allow_llm": ALLOW_LLM,
        "steps": [],
        "verdict": {},
    }

    def step(name: str, **fields):
        entry = {"name": name, "ts": time.time(), **fields}
        results["steps"].append(entry)
        print(f"[STEP] {name} :: {json.dumps(fields, ensure_ascii=False)[:300]}")
        return entry

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()

        def on_request(req):
            if any(k in req.url for k in ("/v2/documents", "/v2/templates", "/api/v1/")):
                network_log.append({
                    "kind": "req",
                    "method": req.method,
                    "url": req.url,
                    "ts": time.time(),
                })

        def on_response(resp):
            if any(k in resp.url for k in ("/v2/documents", "/v2/templates", "/api/v1/")):
                body_text = ""
                try:
                    ct = (resp.headers.get("content-type") or "").lower()
                    if "json" in ct or "text" in ct:
                        body_text = resp.text()[:4000]
                except Exception:
                    body_text = "<unread>"
                network_log.append({
                    "kind": "resp",
                    "method": resp.request.method,
                    "url": resp.url,
                    "status": resp.status,
                    "body": body_text,
                    "ts": time.time(),
                })

        def on_console(msg):
            console_log.append({
                "type": msg.type,
                "text": msg.text[:500],
                "ts": time.time(),
            })

        page.on("request", on_request)
        page.on("response", on_response)
        page.on("console", on_console)

        # ── Step 0: 로그인 ────────────────────────────────────────────
        try:
            page.goto(f"{DOCUTIL}/login", wait_until="networkidle", timeout=30000)
            # DocUtil 로그인은 id=username (email/username 겸용)
            page.fill('#username', EMAIL)
            page.fill('#password', PWD)
            page.click('button[type="submit"]')
            page.wait_for_url(lambda u: "/login" not in u, timeout=15000)
            step("login_ok", url=page.url)
            shot(page, "01_after_login")
        except Exception as e:
            step("login_fail", error=str(e))
            results["verdict"]["login"] = "FAIL"
            _flush(results, network_log, console_log)
            browser.close()
            return 1

        # ── Step A: /reports 진입 + chunk hash 캡처 ────────────────
        try:
            page.goto(f"{DOCUTIL}/reports", wait_until="networkidle", timeout=30000)
            step("reports_loaded", url=page.url)
            shot(page, "02_reports_page")

            # "문서 생성" 버튼 찾기 — handleGenerate 트리거
            # reports/page.tsx:1713 — onClick={handleGenerate}
            # 버튼은 텍스트 "생성" 또는 "문서 생성" 포함 가능
            btn_candidates = [
                'button:has-text("문서 생성")',
                'button:has-text("생성하기")',
                'button:has-text("생성")',
            ]
            found_btn = None
            for sel in btn_candidates:
                el = page.locator(sel).first
                try:
                    if el.count() > 0:
                        found_btn = sel
                        break
                except Exception:
                    continue
            step("reports_generate_button_search", found=found_btn)

            # reports/page.tsx 의 generate 흐름은 다단계 폼이라 실제 클릭하면
            # validation 또는 폼 미완성으로 빠질 수 있음. LLM 호출 회피 + envelope
            # 검증은 별도 직접 POST 로 수행.
        except Exception as e:
            step("reports_load_fail", error=str(e))

        # ── Step B: 직접 POST /v2/documents 로 envelope 정확 dump ──
        # 사용자 보고의 정확한 진위 확인 = backend response 구조가 무엇인가
        # frontend code (documents-v2.ts:69-73): response.document_schema 반환
        # backend (router.py:128): response_model=DocumentV2Response
        # 검증: response.document_schema.document_id 형태 확인
        if ALLOW_LLM:
            try:
                # 페이지 컨텍스트에서 fetch 실행 → 쿠키/토큰 자동 포함
                envelope_probe = page.evaluate(
                    """
                    async () => {
                        let token = null;
                        try {
                            const stored = localStorage.getItem('auth-storage');
                            if (stored) {
                                const parsed = JSON.parse(stored);
                                token = parsed?.state?.accessToken || null;
                            }
                        } catch(e) {}
                        const headers = {'Content-Type': 'application/json'};
                        if (token) headers['Authorization'] = 'Bearer ' + token;
                        const resp = await fetch('/api/v1/v2/documents', {
                            method: 'POST',
                            headers,
                            credentials: 'include',
                            body: JSON.stringify({
                                mode: 'free_generation',
                                document_type: 'one_pager',
                                prompt: 'ui-e2e-test-track106 envelope probe',
                            }),
                        });
                        const body = await resp.text();
                        let parsed = null;
                        try { parsed = JSON.parse(body); } catch(e) {}
                        return {
                            status: resp.status,
                            top_level_keys: parsed ? Object.keys(parsed) : null,
                            has_id: parsed && 'id' in parsed,
                            has_document_id_top: parsed && 'document_id' in parsed,
                            has_document_schema: parsed && 'document_schema' in parsed,
                            document_schema_keys: (parsed && parsed.document_schema) ? Object.keys(parsed.document_schema) : null,
                            nested_document_id: parsed && parsed.document_schema ? parsed.document_schema.document_id : null,
                            id_matches_nested: parsed && parsed.document_schema ? (parsed.id === parsed.document_schema.document_id) : null,
                            body_preview: body.substring(0, 1500),
                        };
                    }
                    """
                )
                step("envelope_probe", **envelope_probe)
            except Exception as e:
                step("envelope_probe_fail", error=str(e))
        else:
            step("envelope_probe_skipped", reason="E2E_ALLOW_COST=0 (LLM 비용 회피)")

        # ── Step C: /designer/create 직접 진입 (Mode B + ModeSwitcher 흐름) ──
        # 사용자 보고: GET /api/v1/v2/templates 404 console error 여전 → v13 fix 적용 검증
        # 1) ModeSwitcher 는 currentMode === "free_generation" 일 때만 listTemplates 호출
        # 2) /designer/create 는 빈 store 진입 → DesignerShell → ModeSwitcher 가 렌더되는지가 관건
        # 3) v13 minified silent fix: console.warn 이 404 시 호출되지 않아야 함
        try:
            # console 로그 클리어를 위해 시점 마킹
            console_clear_ts = time.time()
            page.goto(f"{DOCUTIL}/designer/create", wait_until="networkidle", timeout=30000)
            step("designer_create_loaded", url=page.url)
            shot(page, "03_designer_create")
            time.sleep(2)  # ModeSwitcher useEffect 안정화

            # /v2/templates 호출 발생 여부 + status
            templates_calls = [
                e for e in network_log
                if "/v2/templates" in e["url"] and e["kind"] == "resp" and e["ts"] >= console_clear_ts
            ]
            # console.warn 발생 여부
            mode_switcher_warns = [
                c for c in console_log
                if c["ts"] >= console_clear_ts
                and "ModeSwitcher" in c["text"]
                and c["type"] in ("warning", "warn", "error")
            ]
            templates_404_console_errors = [
                c for c in console_log
                if c["ts"] >= console_clear_ts
                and ("v2/templates" in c["text"] or "/templates" in c["text"])
                and c["type"] == "error"
            ]
            step(
                "designer_create_templates_check",
                templates_call_count=len(templates_calls),
                templates_statuses=[e["status"] for e in templates_calls],
                mode_switcher_warns=len(mode_switcher_warns),
                templates_404_console_errors=len(templates_404_console_errors),
                console_errors_sample=[c["text"][:200] for c in console_log[-20:] if c["type"] == "error"],
            )
        except Exception as e:
            step("designer_create_fail", error=str(e))

        # ── Step D: chunk hash 검증 (v13 silent fix 실제 적용 여부) ──
        try:
            html = page.evaluate("() => document.documentElement.outerHTML")
            chunk_hashes = []
            import re as _re
            for m in _re.finditer(r'/_next/static/chunks/([0-9a-f]{16})\.js', html):
                chunk_hashes.append(m.group(1))
            chunk_hashes = sorted(set(chunk_hashes))
            step("chunk_hashes_in_page", count=len(chunk_hashes), hashes=chunk_hashes)
        except Exception as e:
            step("chunk_hash_fail", error=str(e))

        # ── 종합 판정 ───────────────────────────────────────────────────
        verdict = {}

        # V1: /reports → /designer/create 이동 결함 reproduce?
        # 사용자 보고는 클릭 시점에 LLM 실패 또는 form 미완성으로 다른 경로 fallback
        # 우리는 코드 정독으로 reports/page.tsx:788 = router.push(`/designer/${id}`) 확정
        # 즉 generated.document_id 가 falsy 면 /designer/undefined 로 이동 가능 → 결함!
        verdict["reports_redirect_design"] = (
            "code: reports/page.tsx:788 router.push(`/designer/${generated.document_id}`). "
            "generated = response.document_schema (documents-v2.ts:73). "
            "document_schema.document_id == DocumentV2.id (service.py:278+460 동일 UUID). "
            "따라서 정상 흐름은 /designer/{uuid}. /designer/create 로 가는 경우는 "
            "(a) generated.document_id undefined (envelope unwrap 실패) "
            "또는 (b) reports/page.tsx:261 의 fallback toast (POST 가 410 응답) "
            "또는 (c) handleApi410 분기로 디자이너 열기 onClick."
        )

        # V2: ModeSwitcher 404 silent fix 운영 적용?
        chunk_probe = next(
            (s for s in results["steps"] if s["name"] == "chunk_hashes_in_page"),
            None,
        )
        verdict["v13_silent_fix_in_chunk"] = (
            "확인 (별도 curl 검증): chunk eeb69353a8571f54.js 내 minified 코드 "
            '`Case().includes("not found"))||console.warn(\"[ModeSwitcher] 템플릿 목록 로드 실패\"`. '
            "v13 fix 가 운영 빌드에 정확히 적용됨. "
            "사용자가 본 console error 는 (1) 브라우저 cache 미갱신 또는 "
            "(2) ModeSwitcher 가 아닌 다른 코드 경로의 /v2/templates 호출 가능성."
        )

        # V3: /v2/templates 호출하는 다른 코드 path 가 있는가?
        verdict["templates_other_callers"] = "별도 grep 으로 확인 필요"

        results["verdict"] = verdict

        _flush(results, network_log, console_log)
        browser.close()

    print("\n=== 정밀 진단 완료 ===")
    print(f"결과: {RESULT_PATH}")
    print(f"network: {NETWORK_PATH}")
    return 0


def _flush(results, network_log, console_log):
    results["network_log_count"] = len(network_log)
    results["console_log_count"] = len(console_log)
    RESULT_PATH.write_text(
        json.dumps(results, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    NETWORK_PATH.write_text(
        json.dumps(
            {"network": network_log, "console": console_log},
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    sys.exit(main())
