"""트랙 #75 — AgentHub 로그인 폼 셀렉터 식별 + DocUtil 사용자 챗봇 라우트 탐색."""
from __future__ import annotations
import json
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


def probe_agenthub_login() -> dict:
    """AgentHub landing → "로그인" 클릭 → 로그인 폼 셀렉터 식별."""
    info = {"target": AGENTHUB_BASE, "started_at": now_ts(), "checks": []}
    with chrome(headless=True) as (_p, _b, _ctx, page):
        page.goto(AGENTHUB_BASE)
        try:
            page.wait_for_load_state("networkidle", timeout=8_000)
        except Exception:
            pass
        # 상단 우측 "로그인" 링크/버튼 클릭
        login_link = page.locator("text=로그인").first
        cnt = login_link.count()
        info["checks"].append({"step": "find_login_link", "count": cnt})
        if cnt == 0:
            info["error"] = "no 로그인 link"
            return info
        login_link.click()
        try:
            page.wait_for_load_state("networkidle", timeout=8_000)
        except Exception:
            pass
        time.sleep(0.4)
        sc = shot(page, "probe_ah_l", "agenthub_login_page")
        info["checks"].append({"step": "post_click", "url": page.url, "title": page.title(), "screenshot": sc})

        # 셀렉터 탐색
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
            ],
            "submit_button": [
                "button[type='submit']",
                "button:has-text('로그인')",
                "button:has-text('Login')",
            ],
        }
        sel_results = {}
        for k, cands in selectors.items():
            for sel in cands:
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
    info["finished_at"] = now_ts()
    return info


def probe_docutil_chat_route() -> dict:
    """DocUtil 사용자 챗봇 라우트 탐색 — /, /chat, /embed 등."""
    info = {"target": DOCUTIL_NGINX, "started_at": now_ts(), "checks": []}
    routes = ["/", "/chat", "/embed", "/chatbot", "/user", "/public"]
    with chrome(headless=True) as (_p, _b, _ctx, page):
        for r in routes:
            target_url = f"{DOCUTIL_NGINX}{r}"
            try:
                resp = page.goto(target_url, wait_until="domcontentloaded", timeout=10_000)
                try:
                    page.wait_for_load_state("networkidle", timeout=4_000)
                except Exception:
                    pass
                status = resp.status if resp else -1
                final_url = page.url
                title = page.title()
                # 페이지에 보이는 한국어 키워드
                page_text = ""
                try:
                    page_text = page.locator("body").inner_text()[:300]
                except Exception:
                    pass
                info["checks"].append({
                    "route": r,
                    "status": status,
                    "final_url": final_url,
                    "title": title,
                    "text_head": page_text,
                })
            except Exception as e:
                info["checks"].append({"route": r, "error": f"{type(e).__name__}:{e}"})
    info["finished_at"] = now_ts()
    return info


def main() -> None:
    out = {
        "agenthub_login": probe_agenthub_login(),
        "docutil_routes": probe_docutil_chat_route(),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
