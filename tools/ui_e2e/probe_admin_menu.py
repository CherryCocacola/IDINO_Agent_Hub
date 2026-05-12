"""트랙 #75 — AgentHub 사이드바 '운영자'/'설정'/'DOCUTIL 운영' 펼쳐서 메뉴 탐색."""
from __future__ import annotations
import io
import json
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import ADMIN_EMAIL, ADMIN_PASSWORD, AGENTHUB_BASE, chrome, now_ts, shot


def main() -> dict:
    info = {"target": AGENTHUB_BASE, "started_at": now_ts(), "checks": []}
    with chrome(headless=True) as (_p, _b, _ctx, page):
        # 로그인
        page.goto(f"{AGENTHUB_BASE}/login")
        page.wait_for_load_state("networkidle", timeout=10_000)
        page.fill("input[type='email']", ADMIN_EMAIL)
        page.fill("input[type='password']", ADMIN_PASSWORD)
        page.click("button[type='submit']")
        page.wait_for_url(lambda u: "/login" not in u, timeout=10_000)
        page.wait_for_load_state("networkidle", timeout=10_000)
        time.sleep(0.5)

        # 모든 펼침 가능 아이템 클릭
        # 사이드바: '대시보드', 'AI 서비스', 'DOCUTIL 운영', '운영자', '설정'
        # → 펼침 화살표 ▶가 있는 것은 'DOCUTIL 운영', '운영자', '설정' 등
        for menu_text in ["DOCUTIL 운영", "운영자", "설정", "AI 서비스"]:
            try:
                loc = page.get_by_text(menu_text, exact=True).first
                if loc.count() > 0:
                    loc.click()
                    time.sleep(0.4)
                    info["checks"].append({"step": "expand_menu", "menu": menu_text, "result": "clicked"})
                else:
                    info["checks"].append({"step": "expand_menu", "menu": menu_text, "result": "not_found"})
            except Exception as e:
                info["checks"].append({"step": "expand_menu", "menu": menu_text, "error": f"{type(e).__name__}:{e}"})

        time.sleep(0.6)
        sc = shot(page, "probe_admin", "all_menus_expanded")
        info["checks"].append({"step": "shot_expanded", "screenshot": sc})

        # 모든 aside 메뉴 항목 다시 수집
        try:
            els = page.locator("aside a, aside button, aside [role='button']")
            cnt = els.count()
            items = []
            for i in range(cnt):
                el = els.nth(i)
                try:
                    if not el.is_visible():
                        continue
                    txt = (el.inner_text() or "").strip()
                    href = el.get_attribute("href") or ""
                    if not txt:
                        continue
                    items.append({"text": txt[:40], "href": href})
                except Exception:
                    continue
            info["checks"].append({"step": "all_items_after_expand", "count": len(items), "items": items})
        except Exception as e:
            info["checks"].append({"step": "all_items_after_expand", "error": f"{type(e).__name__}:{e}"})

        # 특정 키워드 가시성 재확인
        keywords = ["API 키", "API Key", "키 발급", "사용자", "권한", "지식베이스", "Knowledge", "Tool", "Workflow", "분석", "사용량", "감사", "DocUtil 대시보드", "평가", "에이전트 빌더", "프로필", "프로파일"]
        found = {}
        for kw in keywords:
            try:
                loc = page.get_by_text(kw, exact=False)
                found[kw] = loc.count()
            except Exception:
                found[kw] = -1
        info["checks"].append({"step": "keywords_after_expand", "found": found})

    info["finished_at"] = now_ts()
    return info


if __name__ == "__main__":
    out = main()
    with open("probe_admin_menu_result.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=str)
    print("saved probe_admin_menu_result.json")
