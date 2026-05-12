"""트랙 #75 — AgentHub 로그인 후 사이드바 / 메뉴 구조 탐색.

목적: ApiKey 메뉴 / Playground / 채팅 / DocUtil 운영 메뉴 경로 식별.
read-only — 클릭은 하지 않고 텍스트/링크만 수집.
"""
from __future__ import annotations
import json
import sys
import time

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import ADMIN_EMAIL, ADMIN_PASSWORD, AGENTHUB_BASE, chrome, now_ts, shot


def login_and_probe() -> dict:
    info = {"target": AGENTHUB_BASE, "started_at": now_ts(), "checks": []}
    with chrome(headless=True) as (_p, _b, _ctx, page):
        # 로그인
        page.goto(f"{AGENTHUB_BASE}/login")
        try:
            page.wait_for_load_state("networkidle", timeout=8_000)
        except Exception:
            pass
        page.fill("input[type='email']", ADMIN_EMAIL)
        page.fill("input[type='password']", ADMIN_PASSWORD)
        page.click("button[type='submit']")
        try:
            page.wait_for_url(lambda u: "/login" not in u, timeout=10_000)
        except Exception:
            pass
        try:
            page.wait_for_load_state("networkidle", timeout=8_000)
        except Exception:
            pass
        time.sleep(0.5)
        info["checks"].append({"step": "post_login_url", "url": page.url, "title": page.title()})
        sc = shot(page, "probe_post", "post_login_landing")
        info["checks"].append({"step": "post_login_shot", "screenshot": sc})

        # 사이드바 / 네비게이션 메뉴 텍스트 수집
        nav_selectors = [
            "aside a", "nav a", ".sidebar a", "[role='navigation'] a", ".menu a", ".nav-item",
        ]
        seen = set()
        items: list[dict] = []
        for sel in nav_selectors:
            try:
                els = page.locator(sel)
                cnt = els.count()
                for i in range(min(cnt, 80)):
                    el = els.nth(i)
                    try:
                        if not el.is_visible():
                            continue
                        txt = (el.inner_text() or "").strip()
                        href = el.get_attribute("href") or ""
                        if not txt:
                            continue
                        key = f"{txt}|{href}"
                        if key in seen:
                            continue
                        seen.add(key)
                        items.append({"text": txt, "href": href, "selector": sel})
                    except Exception:
                        continue
            except Exception:
                continue
        info["checks"].append({"step": "nav_items", "count": len(items), "items": items[:60]})

        # 추가: 모든 클릭 가능 텍스트 키워드 (API 키, 채팅, Playground, DocUtil, 평가, 대시보드, 지식베이스)
        keywords = [
            "API 키", "API Key", "키 관리",
            "채팅", "Chat",
            "Playground", "플레이그라운드",
            "에이전트", "Agent",
            "DocUtil", "지식베이스", "Knowledge",
            "평가", "Evaluation",
            "대시보드", "Dashboard",
            "사용량", "Usage", "Analytics",
            "프로필", "Profile", "로그아웃", "Logout",
        ]
        found = {}
        for kw in keywords:
            try:
                loc = page.get_by_text(kw, exact=False).first
                found[kw] = loc.count() > 0
            except Exception:
                found[kw] = False
        info["checks"].append({"step": "keyword_visibility", "found": found})

    info["finished_at"] = now_ts()
    return info


if __name__ == "__main__":
    print(json.dumps(login_and_probe(), ensure_ascii=False, indent=2, default=str))
