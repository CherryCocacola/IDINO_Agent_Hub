"""트랙 #75 — UI 탐색 probe (login 페이지 + 라우팅 구조).

목적:
- AgentHub Vue SPA: 로그인 화면 진입 + 폼 셀렉터 식별 + 라우팅 구조 파악
- DocUtil Next.js: 로그인 화면 진입 + 셀렉터 식별

읽기 전용. 폼에 값을 입력하기만 하고 submit 은 호출하지 않음 (probe 단계).
"""
from __future__ import annotations
import sys
import time

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import (
    AGENTHUB_BASE,
    DOCUTIL_NGINX,
    chrome,
    now_ts,
    shot,
)


def probe_agenthub() -> dict:
    """AgentHub UI 진입 — 첫 페이지 구조 캡처."""
    info = {"target": AGENTHUB_BASE, "started_at": now_ts(), "checks": []}
    with chrome(headless=True) as (_p, _b, _ctx, page):
        t0 = time.time()
        page.goto(AGENTHUB_BASE, wait_until="domcontentloaded")
        # Vue SPA 렌더링 대기 — 로그인 폼 입력란 등장까지
        try:
            page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:
            pass
        elapsed = int((time.time() - t0) * 1000)

        title = page.title()
        url = page.url
        sc = shot(page, "probe_ah", "agenthub_landing")
        info["checks"].append({
            "step": "landing",
            "title": title,
            "url": url,
            "duration_ms": elapsed,
            "screenshot": sc,
        })

        # 폼 셀렉터 탐색
        # email/password input 후보
        selectors = {
            "email_input": [
                "input[type='email']",
                "input[name='email']",
                "input[placeholder*='이메일']",
                "input[placeholder*='Email']",
                "input[autocomplete='username']",
            ],
            "password_input": [
                "input[type='password']",
                "input[name='password']",
                "input[autocomplete='current-password']",
            ],
            "login_button": [
                "button[type='submit']",
                "button:has-text('로그인')",
                "button:has-text('Login')",
                "button:has-text('Sign in')",
            ],
        }
        sel_results = {}
        for k, candidates in selectors.items():
            for sel in candidates:
                try:
                    loc = page.locator(sel).first
                    if loc.count() > 0 and loc.is_visible():
                        sel_results[k] = sel
                        break
                except Exception:
                    continue
            else:
                sel_results[k] = None
        info["checks"].append({"step": "selectors", "selectors": sel_results})

        # 페이지 전체 HTML 일부 캡처 (디버그)
        try:
            html_snippet = page.content()[:3000]
        except Exception:
            html_snippet = ""
        info["checks"].append({"step": "html_snippet", "snippet_chars": len(html_snippet), "head_100": html_snippet[:200]})

    info["finished_at"] = now_ts()
    return info


def probe_docutil() -> dict:
    """DocUtil nginx → Next.js 진입."""
    info = {"target": DOCUTIL_NGINX, "started_at": now_ts(), "checks": []}
    with chrome(headless=True) as (_p, _b, _ctx, page):
        t0 = time.time()
        try:
            page.goto(DOCUTIL_NGINX, wait_until="domcontentloaded", timeout=20_000)
            try:
                page.wait_for_load_state("networkidle", timeout=10_000)
            except Exception:
                pass
            elapsed = int((time.time() - t0) * 1000)
            title = page.title()
            url = page.url
            sc = shot(page, "probe_du", "docutil_landing")
            info["checks"].append({
                "step": "landing",
                "title": title,
                "url": url,
                "duration_ms": elapsed,
                "screenshot": sc,
            })

            # 로그인/회원가입 링크 탐색
            link_texts = ["로그인", "회원가입", "Sign in", "Sign up", "Login"]
            found = {}
            for t in link_texts:
                try:
                    loc = page.get_by_text(t, exact=False).first
                    if loc.count() > 0 and loc.is_visible():
                        found[t] = True
                except Exception:
                    pass
            info["checks"].append({"step": "link_texts", "found": found})
        except Exception as e:
            info["checks"].append({"step": "landing", "error": f"{type(e).__name__}:{e}"})

    info["finished_at"] = now_ts()
    return info


def main() -> None:
    import json
    out = {"agenthub": probe_agenthub(), "docutil": probe_docutil()}
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
