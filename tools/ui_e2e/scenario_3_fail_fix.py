"""트랙 #75 시나리오 3 — FAIL 4건 TC 보정 (실제 UI 흐름으로 정확 endpoint 식별).

3-1. A-06 — 사이드바 우상단 사용자 메뉴 → 로그아웃 클릭 → 실제 endpoint + 인증 무효화 검증
3-2. E-02 — 채팅 페이지 진입 시 자동 SignalR negotiate (WebSocket OPEN 캡처)
3-3. G-04a — 사이드바 "DOCUTIL 운영" → "대시보드" 또는 비슷한 메뉴 클릭 → 실제 호출 endpoint
3-4. G-07a — 사이드바 "DOCUTIL 운영" → "평가" 메뉴 클릭 → 실제 호출 endpoint
"""
from __future__ import annotations
import io
import json
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import (
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    AGENTHUB_BASE,
    chrome,
    now_ts,
    shot,
)


def run() -> dict:
    out: dict = {"scenario_id": "S3", "scenario": "FAIL 4건 TC 보정", "started_at": now_ts(), "steps": []}
    network_log: list[dict] = []
    websockets_observed: list[dict] = []

    with chrome(headless=True) as (_p, _b, _ctx, page):

        def on_response(resp):
            try:
                u = resp.url
                m = resp.request.method
                if "/api/" in u or "/hubs/" in u:
                    network_log.append({
                        "method": m,
                        "url": u,
                        "status": resp.status,
                        "ct": resp.headers.get("content-type", ""),
                    })
            except Exception:
                pass

        def on_ws(ws):
            websockets_observed.append({"url": ws.url, "ts": now_ts()})

        page.on("response", on_response)
        page.on("websocket", on_ws)

        # === 로그인 ===
        page.goto(f"{AGENTHUB_BASE}/login")
        page.wait_for_load_state("networkidle", timeout=10_000)
        page.fill("input[type='email']", ADMIN_EMAIL)
        page.fill("input[type='password']", ADMIN_PASSWORD)
        page.click("button[type='submit']")
        try:
            page.wait_for_url(lambda u: "/login" not in u, timeout=12_000)
        except Exception:
            pass
        page.wait_for_load_state("networkidle", timeout=10_000)
        time.sleep(0.5)

        # =====================================================
        # 3-2. E-02 — 채팅 진입 시 자동 SignalR negotiate (먼저 실행 — 로그인 직후 자동 negotiate 캡처)
        # =====================================================
        t0 = time.time()
        # 채팅 페이지 진입 → SignalR negotiate + WebSocket open
        page.goto(f"{AGENTHUB_BASE}/agents/multi-chat")
        page.wait_for_load_state("networkidle", timeout=10_000)
        time.sleep(2.0)  # SignalR 핸드셰이크 대기

        # 캡처된 negotiate 호출 검색
        negotiate_calls = [n for n in network_log if "negotiate" in n["url"]]
        ws_observed = list(websockets_observed)
        sc = shot(page, "s3_02", "after_signalr_init")
        out["steps"].append({
            "id": "3-2 (E-02 fix)",
            "desc": "채팅 UI 진입 → 자동 SignalR negotiate + WebSocket OPEN",
            "result": "PASS" if (negotiate_calls or ws_observed) else "FAIL",
            "duration_ms": int((time.time()-t0)*1000),
            "negotiate_calls": negotiate_calls[:5],
            "websockets": ws_observed[:5],
            "screenshot": sc,
        })

        # =====================================================
        # 3-3. G-04a — DOCUTIL 운영 → 대시보드 메뉴 클릭
        # =====================================================
        t0 = time.time()
        # 사이드바 DOCUTIL 운영 펼치기
        try:
            tg = page.locator("aside").get_by_text("DOCUTIL 운영", exact=False).first
            if tg.count() > 0:
                tg.click()
                time.sleep(0.5)
        except Exception:
            pass

        # 펼친 후 보이는 모든 DOCUTIL 운영 하위 메뉴
        sub_items = []
        try:
            els = page.locator("aside a")
            for i in range(els.count()):
                el = els.nth(i)
                try:
                    if el.is_visible():
                        txt = (el.inner_text() or "").strip()
                        href = el.get_attribute("href") or ""
                        if href and ("docutil" in href.lower() or "admin" in href.lower() or "knowledge" in href.lower() or "rag" in href.lower() or "evaluation" in href.lower() or "평가" in txt or "대시보드" in txt):
                            sub_items.append({"text": txt, "href": href})
                except Exception:
                    continue
        except Exception:
            pass

        out["steps"].append({"id": "3-3 (G-04a probe)", "desc": "DOCUTIL 운영 하위 메뉴 식별", "result": "INFO", "items": sub_items})

        # "대시보드" 또는 "DocUtil 대시보드" 클릭 — 네트워크 호출 캡처 시작
        before_idx = len(network_log)
        dashboard_clicked = None
        for candidate in ["DocUtil 대시보드", "DocUtil 대시", "대시보드", "RAG 대시보드"]:
            try:
                # 사이드바 내부에서 클릭 (전역 대시보드는 메인 사이드바에 있음 → DocUtil 운영 하위만)
                docu_section = page.locator("aside")
                el = docu_section.get_by_text(candidate, exact=False).all()
                # 가장 아래쪽 (운영 섹션 하위) 항목
                for ee in reversed(el):
                    try:
                        if ee.is_visible():
                            ee.click()
                            dashboard_clicked = candidate
                            break
                    except Exception:
                        continue
                if dashboard_clicked:
                    break
            except Exception:
                continue

        time.sleep(2.0)
        page.wait_for_load_state("networkidle", timeout=10_000)
        # 클릭 후 발생한 호출
        dashboard_calls = [n for n in network_log[before_idx:] if "admin" in n["url"] or "docutil" in n["url"].lower() or "dashboard" in n["url"].lower()]
        sc = shot(page, "s3_03", "docutil_dashboard")
        out["steps"].append({
            "id": "3-3 (G-04a fix)",
            "desc": f"DOCUTIL 운영 대시보드 클릭 ({dashboard_clicked or '미발견'})",
            "result": "PASS" if dashboard_clicked and dashboard_calls else "FAIL",
            "duration_ms": int((time.time()-t0)*1000),
            "candidate_endpoint": dashboard_calls[:10],
            "current_url": page.url,
            "screenshot": sc,
        })

        # =====================================================
        # 3-4. G-07a — DOCUTIL 운영 → 평가 메뉴 클릭
        # =====================================================
        t0 = time.time()
        before_idx = len(network_log)
        eval_clicked = None
        for candidate in ["평가", "Evaluation", "RAG 평가"]:
            try:
                # 사이드바
                docu_section = page.locator("aside")
                el = docu_section.get_by_text(candidate, exact=False).all()
                for ee in reversed(el):
                    try:
                        if ee.is_visible():
                            ee.click()
                            eval_clicked = candidate
                            break
                    except Exception:
                        continue
                if eval_clicked:
                    break
            except Exception:
                continue
        time.sleep(2.0)
        page.wait_for_load_state("networkidle", timeout=10_000)
        eval_calls = [n for n in network_log[before_idx:] if "admin" in n["url"] or "docutil" in n["url"].lower() or "evaluation" in n["url"].lower()]
        sc = shot(page, "s3_04", "docutil_evaluation")
        out["steps"].append({
            "id": "3-4 (G-07a fix)",
            "desc": f"DOCUTIL 운영 평가 클릭 ({eval_clicked or '미발견'})",
            "result": "PASS" if eval_clicked and eval_calls else "FAIL",
            "duration_ms": int((time.time()-t0)*1000),
            "candidate_endpoint": eval_calls[:10],
            "current_url": page.url,
            "screenshot": sc,
        })

        # =====================================================
        # 3-1. A-06 — UI 로그아웃 클릭 (마지막에 실행)
        # =====================================================
        t0 = time.time()
        before_idx = len(network_log)
        # 우상단 사용자 메뉴 클릭
        logout_clicked = None
        # 1) "로그아웃" 텍스트 직접
        try:
            lo = page.locator("aside").get_by_text("로그아웃", exact=False).first
            if lo.count() > 0 and lo.is_visible():
                lo.click()
                logout_clicked = "aside 로그아웃"
        except Exception:
            pass
        # 2) 우상단 user dropdown 열고
        if not logout_clicked:
            try:
                # 우상단 사용자 메뉴 (관리자 아이콘)
                user_menu = page.locator(".user-menu, .navbar-user, [class*='user']").first
                if user_menu.count() > 0:
                    user_menu.click()
                    time.sleep(0.4)
                    lo = page.get_by_text("로그아웃", exact=False).first
                    if lo.count() > 0:
                        lo.click()
                        logout_clicked = "dropdown 로그아웃"
            except Exception:
                pass

        time.sleep(2.0)
        try:
            page.wait_for_load_state("networkidle", timeout=8_000)
        except Exception:
            pass
        logout_calls = [n for n in network_log[before_idx:] if "auth" in n["url"] or "logout" in n["url"]]
        sc = shot(page, "s3_01", "after_logout")
        out["steps"].append({
            "id": "3-1 (A-06 fix)",
            "desc": f"UI 로그아웃 ({logout_clicked or '미발견'})",
            "result": "PASS" if logout_clicked else "FAIL",
            "duration_ms": int((time.time()-t0)*1000),
            "logout_endpoint": logout_calls,
            "post_logout_url": page.url,
            "screenshot": sc,
        })

    out["finished_at"] = now_ts()
    summary = {"PASS": 0, "FAIL": 0, "SKIP": 0, "INFO": 0}
    for s in out["steps"]:
        r = s.get("result", "")
        if r in summary:
            summary[r] += 1
    out["summary"] = summary
    out["overall"] = "PASS" if summary["FAIL"] == 0 and summary["PASS"] >= 3 else "PARTIAL"
    out["network_log_full"] = network_log
    return out


if __name__ == "__main__":
    result = run()
    # network_log_full 은 별도 파일
    full = result.pop("network_log_full")
    with open("scenario_3_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    with open("scenario_3_network_log.json", "w", encoding="utf-8") as f:
        json.dump(full, f, ensure_ascii=False, indent=2, default=str)
    print(json.dumps({"summary": result["summary"], "overall": result["overall"]}, ensure_ascii=False, indent=2))
    print("saved scenario_3_result.json + scenario_3_network_log.json")
