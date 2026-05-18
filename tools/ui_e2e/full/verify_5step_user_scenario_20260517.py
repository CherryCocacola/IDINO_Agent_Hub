"""2026-05-17 사용자 측 5단 검증 자동 시뮬레이션 — 결함 1+2 재현 시도 (Playwright + HAR).

5단 + 변형:
  [S1] storage 청소 (새 컨텍스트 = 자동 깨끗)
  [S2] fresh 로그인 — rememberMe 체크 + sessionStorage→localStorage 강제 복사
  [S3] AgentChat 정상 send 검증 — 응답 status / Console / URL / 응답 표시
  [S4] AgentMultiChat (ChatGPT/Nexus) send 검증 — 동일 4가지
  [S5] HAR 자동 저장 (Network/Response 전구간)
  ─── 추가 결함 재현 변형 ────────────────────────────
  [V1] 만료된 JWT 주입 후 AgentChat send — 결함 1 (Send→Dashboard) 재현 시도
  [V2] alert 차단 시뮬레이션 (dialog handler) + 만료 토큰 — race 시나리오
  [V3] /landing 경로에서 send 직후 라우팅 검사 — router 가드 동작 검증

산출:
  tools/ui_e2e/full/verify_5step_result_20260517.json   — 8단계 결과 + 캡처
  tools/ui_e2e/full/verify_5step_har/*.har              — 단계별 HAR
  tools/ui_e2e/screenshots/verify_5step_20260517/*.png  — 단계별 스크린샷
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
    DEFAULT_TIMEOUT_MS,
    VIEWPORT,
    now_ts,
)
from playwright.sync_api import sync_playwright

OUT_DIR = Path(__file__).parent
SHOT_DIR = OUT_DIR.parent / "screenshots" / "verify_5step_20260517"
HAR_DIR = OUT_DIR / "verify_5step_har"
RESULT_PATH = OUT_DIR / "verify_5step_result_20260517.json"

SHOT_DIR.mkdir(parents=True, exist_ok=True)
HAR_DIR.mkdir(parents=True, exist_ok=True)

DASHBOARD_PATHS = {"/", "/dashboard", "/home"}


def shot(page, step: str) -> str:
    p = SHOT_DIR / f"{step}.png"
    try:
        page.screenshot(path=str(p), full_page=False)
        return str(p).replace("\\", "/")
    except Exception as e:
        return f"(shot fail: {e})"


def setup_listeners(page) -> tuple[list, list, list]:
    console_msgs: list[dict] = []
    network: list[dict] = []
    dialogs: list[dict] = []

    def on_console(msg):
        try:
            console_msgs.append({
                "type": msg.type,
                "text": msg.text[:300],
                "ts": now_ts(),
            })
        except Exception:
            pass

    def on_response(resp):
        try:
            url = resp.url
            if any(x in url for x in [".ico", "hot-update", "/sockjs", "_vue-devtools"]):
                return
            # 응답 body 캡처 — chat/send 만 (다른 건 metadata 만)
            body_preview = ""
            try:
                if "/api/chat/" in url or "/api/auth/" in url:
                    body = resp.body()
                    body_preview = body[:800].decode("utf-8", errors="replace") if body else ""
            except Exception:
                pass
            network.append({
                "status": resp.status,
                "method": resp.request.method,
                "url": url[:200],
                "body_preview": body_preview,
                "ts": now_ts(),
            })
        except Exception:
            pass

    def on_dialog(dialog):
        try:
            dialogs.append({
                "type": dialog.type,
                "message": dialog.message[:300],
                "ts": now_ts(),
            })
            # 기본은 accept (정상 사용자 동작)
            dialog.accept()
        except Exception:
            pass

    page.on("console", on_console)
    page.on("response", on_response)
    page.on("dialog", on_dialog)
    return console_msgs, network, dialogs


def login_with_remember(page) -> dict:
    """fresh 로그인 + rememberMe + sessionStorage→localStorage 복사."""
    result = {"step": "S2-login", "status": "FAIL", "note": ""}
    page.goto(f"{AGENTHUB_BASE}/login", timeout=20_000)
    page.wait_for_load_state("domcontentloaded")
    time.sleep(0.5)
    try:
        page.fill('#lgEmail', ADMIN_EMAIL)
        page.fill('#lgPassword', ADMIN_PASSWORD)
        # rememberMe 체크 (label click — invisible checkbox 우회)
        try:
            page.click('label[for="lgRemember"]', timeout=3000)
        except Exception:
            try:
                page.evaluate("() => document.querySelector('#lgRemember').click()")
            except Exception:
                pass
        page.click('button.lg-submit-btn[type="submit"]')
        page.wait_for_load_state("networkidle", timeout=15_000)
        time.sleep(1.5)
        if "/login" in page.url:
            result["note"] = f"로그인 실패 — url={page.url}"
            return result
        # sessionStorage → localStorage 복사
        ss = page.evaluate("() => sessionStorage.getItem('token')")
        ls = page.evaluate("() => localStorage.getItem('token')")
        if ss and not ls:
            page.evaluate(f"() => localStorage.setItem('token', {json.dumps(ss)})")
            ss_r = page.evaluate("() => sessionStorage.getItem('refreshToken')")
            if ss_r:
                page.evaluate(f"() => localStorage.setItem('refreshToken', {json.dumps(ss_r)})")
            result["note"] = "sessionStorage → localStorage 복사 완료"
        else:
            result["note"] = f"localStorage 직접 저장 (ls={'OK' if ls else 'EMPTY'})"
        result["status"] = "PASS"
        result["final_url"] = page.url
        return result
    except Exception as e:
        result["note"] = f"예외: {e}"
        return result


def agentchat_send(page, msg: str = "ping 5step") -> dict:
    """AgentChat 단일 send 후 URL + 응답 검증 (결함 1+2)."""
    r = {"step": "S3-agentchat", "status": "FAIL", "note": "", "url_before": "", "url_after": ""}
    page.goto(f"{AGENTHUB_BASE}/agents", timeout=20_000)
    page.wait_for_load_state("networkidle", timeout=15_000)
    time.sleep(1.5)
    try:
        # 첫 Agent 카드 클릭
        card = page.query_selector('.ag-card:first-child') or page.query_selector('.ag-card')
        if not card:
            r["note"] = "Agent 카드(.ag-card) 미발견 — /agents 비어있음"
            return r
        card.click()
        page.wait_for_load_state("networkidle", timeout=15_000)
        time.sleep(2.0)
        r["url_before"] = page.url
        # 입력 + Send
        ta = page.query_selector('textarea.cd-textarea')
        if not ta:
            r["note"] = "input(textarea.cd-textarea) 미발견"
            return r
        ta.click()
        ta.fill(msg)
        page.click('button.cd-send-btn')
        time.sleep(3.0)
        r["url_after"] = page.url
        from urllib.parse import urlparse
        p_after = urlparse(page.url).path or "/"
        if p_after in DASHBOARD_PATHS:
            r["note"] = f"DEFECT1_REPRO__Send→{p_after} (chat={r['url_before']})"
            r["status"] = "FAIL"
            return r
        # 응답 대기 5초 + 검증
        time.sleep(5.0)
        body = page.evaluate("() => document.body.innerText || ''")
        kw = ["응답", "안녕", "Hello", "도와", "I'm", "ping", "I am"]
        has_resp = any(k in body for k in kw)
        r["status"] = "PASS" if has_resp else "FAIL"
        r["note"] = "응답 표시 OK" if has_resp else "DEFECT2_REPRO__응답_미표시"
        return r
    except Exception as e:
        r["note"] = f"예외: {e}"
        return r


def multichat_send(page, provider: str, wait_sec: float) -> dict:
    r = {"step": f"S4-multi-{provider}", "status": "FAIL", "note": "", "url_before": "", "url_after": ""}
    page.goto(f"{AGENTHUB_BASE}/agents/multi-chat", timeout=20_000)
    page.wait_for_load_state("networkidle", timeout=15_000)
    time.sleep(2.0)
    try:
        # 새 채팅 (있으면 클릭)
        for sel in ['button:has-text("새 채팅")', 'button:has-text("새 대화")', 'button.new-chat']:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    el.click()
                    break
            except Exception:
                continue
        time.sleep(1.0)
        # provider 선택
        try:
            for sel in ['select.service-select', 'select.cd-select', 'select']:
                el = page.query_selector(sel)
                if el:
                    try:
                        el.select_option(label=provider)
                        break
                    except Exception:
                        continue
        except Exception:
            pass
        # 입력 — AgentMultiChat 은 mc- prefix (cd- 아님)
        ta = (page.query_selector('textarea.mc-textarea')
              or page.query_selector('textarea.cd-textarea')
              or page.query_selector('textarea:not(.form-control)'))
        if not ta:
            r["note"] = "멀티채팅 input 미발견 (mc-textarea/cd-textarea/textarea 모두)"
            return r
        ta.click()
        ta.fill(f"ping multi {provider}")
        r["url_before"] = page.url
        # send 버튼 — mc-send-btn 우선
        try:
            page.click('button.mc-send-btn', timeout=3000)
        except Exception:
            try:
                page.click('button.cd-send-btn', timeout=3000)
            except Exception:
                page.keyboard.press("Enter")
        time.sleep(wait_sec)
        r["url_after"] = page.url
        from urllib.parse import urlparse
        p_after = urlparse(page.url).path or "/"
        if p_after in DASHBOARD_PATHS:
            r["note"] = f"DEFECT1_REPRO__Send→{p_after} (멀티채팅)"
            r["status"] = "FAIL"
            return r
        body = page.evaluate("() => document.body.innerText || ''")
        kw = ["안녕", "도와", "Hello", "I'm", "응답이 없습니다", "오류가 발생"]
        has_resp = any(k in body for k in kw)
        err = "오류가 발생" in body or "응답이 없습니다" in body
        r["status"] = "PASS" if (has_resp and not err) else "FAIL"
        r["note"] = "응답 OK" if (has_resp and not err) else (
            f"DEFECT2_REPRO__응답_미표시" if not has_resp
            else f"오류 표시: {body[body.find('오류'):body.find('오류')+150]}"
        )
        return r
    except Exception as e:
        r["note"] = f"예외: {e}"
        return r


def inject_expired_both_and_send(page) -> dict:
    """V3 (신규): 만료 access + 만료 refresh token 둘 다 주입 → SSE 401 → refresh 실패 →
    fix-A 분기 (notifyAndRedirectToLogin) 트리거 검증.

    기대: alert 1건 발생 + 양쪽 storage 청소 + /login redirect (대시보드 이탈 X).
    fix-A 미적용 시: dialog 0건 + /agents/chat 유지 (사용자 모름).
    """
    r = {"step": "V3-both-expired-fix-a-trigger", "status": "FAIL", "note": "", "url_after": ""}
    try:
        page.goto(f"{AGENTHUB_BASE}/agents", timeout=20_000)
        page.wait_for_load_state("networkidle", timeout=10_000)
        time.sleep(1.5)
        card = page.query_selector('.ag-card:first-child') or page.query_selector('.ag-card')
        if not card:
            r["note"] = "Agent 카드 미발견"
            return r
        card.click()
        page.wait_for_load_state("networkidle", timeout=10_000)
        time.sleep(2.0)
        ta = page.query_selector('textarea.cd-textarea')
        if not ta:
            r["note"] = "input 미발견"
            return r
        ta.click()
        ta.fill("ping V3 both expired")
        expired = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiJhZG1pbiIsImV4cCI6MTAwMDAwMDAwMH0."
            "dummy"
        )
        # access + refresh 둘 다 만료 (백엔드가 둘 다 거부 → refreshAccessToken catch 진입)
        page.evaluate(f"() => localStorage.setItem('token', '{expired}')")
        page.evaluate(f"() => localStorage.setItem('refreshToken', '{expired}')")
        page.evaluate(f"() => sessionStorage.setItem('token', '{expired}')")
        page.evaluate(f"() => sessionStorage.setItem('refreshToken', '{expired}')")
        page.click('button.cd-send-btn')
        time.sleep(5.0)
        r["url_after"] = page.url
        from urllib.parse import urlparse
        p_after = urlparse(page.url).path or "/"
        # fix-A 적용 시 → /login (alert + redirect)
        # 미적용 시 → /agents/chat 유지 (사용자가 모름)
        if "/login" in p_after:
            r["status"] = "PASS"
            r["note"] = f"fix-A OK — refresh 실패 → notifyAndRedirectToLogin → /login redirect"
        elif p_after in DASHBOARD_PATHS:
            r["status"] = "FAIL"
            r["note"] = f"DEFECT1_REPRO__V3 → {p_after} (router 가드 storage 잔존 race)"
        else:
            r["status"] = "FAIL"
            r["note"] = f"fix-A 미동작 의심 — /login 으로 안 감, {p_after} 유지"
        # storage 청소 확인
        ls_t = page.evaluate("() => localStorage.getItem('token')")
        ss_t = page.evaluate("() => sessionStorage.getItem('token')")
        r["storage_after"] = {
            "localStorage_token": "OK" if ls_t else "EMPTY",
            "sessionStorage_token": "OK" if ss_t else "EMPTY",
        }
        return r
    except Exception as e:
        r["note"] = f"예외: {e}"
        return r


def inject_expired_token_and_send(page) -> dict:
    """V1: 만료된 access JWT 만 주입 (refresh 토큰 유효 — refresh 성공해야 정상)."""
    r = {"step": "V1-expired-access-only", "status": "FAIL", "note": "", "url_after": ""}
    try:
        # 정상 로그인된 상태에서 출발 → /agents → 채팅방 → 입력 후 send 직전 JWT 만료된 값으로 교체
        page.goto(f"{AGENTHUB_BASE}/agents", timeout=20_000)
        page.wait_for_load_state("networkidle", timeout=10_000)
        time.sleep(1.5)
        card = page.query_selector('.ag-card:first-child') or page.query_selector('.ag-card')
        if not card:
            r["note"] = "Agent 카드 미발견"
            return r
        card.click()
        page.wait_for_load_state("networkidle", timeout=10_000)
        time.sleep(2.0)
        ta = page.query_selector('textarea.cd-textarea')
        if not ta:
            r["note"] = "input 미발견"
            return r
        ta.click()
        ta.fill("ping with expired token")
        # JWT 를 만료된 더미로 교체 (header.payload.signature 형태지만 exp 가 과거)
        expired_jwt = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiJhZG1pbiIsImV4cCI6MTAwMDAwMDAwMH0."  # exp = 2001-09-09 (만료)
            "dummy"
        )
        page.evaluate(f"() => localStorage.setItem('token', '{expired_jwt}')")
        page.evaluate(f"() => sessionStorage.setItem('token', '{expired_jwt}')")
        # send 클릭 — 401 발생 → 인터셉터 → /login → 가드
        page.click('button.cd-send-btn')
        time.sleep(4.0)
        r["url_after"] = page.url
        from urllib.parse import urlparse
        p_after = urlparse(page.url).path or "/"
        if p_after in DASHBOARD_PATHS:
            r["status"] = "FAIL"
            r["note"] = f"DEFECT1_REPRO__만료토큰 Send → {p_after} (router 가드 race)"
        elif "/login" in p_after:
            r["status"] = "PASS"
            r["note"] = "만료 토큰 → /login 정상 redirect (의도된 동작)"
        else:
            r["status"] = "PASS"
            r["note"] = f"만료 토큰 → {p_after} (예상 외 라우팅)"
        return r
    except Exception as e:
        r["note"] = f"예외: {e}"
        return r


def alert_blocked_send(page) -> dict:
    """V2: alert dismiss 시뮬레이션 (사용자가 alert 닫음) + 만료 토큰 + send → race 검증."""
    r = {"step": "V2-alert-dismiss-expired", "status": "FAIL", "note": "", "url_after": ""}
    try:
        page.goto(f"{AGENTHUB_BASE}/agents", timeout=20_000)
        page.wait_for_load_state("networkidle", timeout=10_000)
        time.sleep(1.5)
        card = page.query_selector('.ag-card:first-child') or page.query_selector('.ag-card')
        if not card:
            r["note"] = "Agent 카드 미발견"
            return r
        card.click()
        page.wait_for_load_state("networkidle", timeout=10_000)
        time.sleep(2.0)
        ta = page.query_selector('textarea.cd-textarea')
        if not ta:
            r["note"] = "input 미발견"
            return r
        ta.click()
        ta.fill("ping alert dismiss")
        # alert dismiss handler 별도 등록 (accept 대신 dismiss = 사용자가 "취소" 누름)
        dismiss_count = [0]

        def on_dlg(d):
            try:
                dismiss_count[0] += 1
                d.dismiss()
            except Exception:
                pass

        page.on("dialog", on_dlg)
        expired_jwt = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiJhZG1pbiIsImV4cCI6MTAwMDAwMDAwMH0."
            "dummy"
        )
        page.evaluate(f"() => localStorage.setItem('token', '{expired_jwt}')")
        page.evaluate(f"() => sessionStorage.setItem('token', '{expired_jwt}')")
        page.click('button.cd-send-btn')
        time.sleep(4.0)
        r["url_after"] = page.url
        r["dismiss_count"] = dismiss_count[0]
        from urllib.parse import urlparse
        p_after = urlparse(page.url).path or "/"
        if p_after in DASHBOARD_PATHS:
            r["status"] = "FAIL"
            r["note"] = f"DEFECT1_REPRO__alert dismiss → {p_after} (dialog={dismiss_count[0]})"
        elif "/login" in p_after:
            r["status"] = "PASS"
            r["note"] = f"alert dismiss → /login (dialog={dismiss_count[0]})"
        else:
            r["status"] = "PASS"
            r["note"] = f"alert dismiss → {p_after} (dialog={dismiss_count[0]})"
        return r
    except Exception as e:
        r["note"] = f"예외: {e}"
        return r


def main():
    print(f"[start] 5단 검증 자동화 — {now_ts()}")
    results = []
    all_console: list[dict] = []
    all_network: list[dict] = []
    all_dialogs: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # ── 컨텍스트 (HAR 기록 활성) ──
        ctx = browser.new_context(
            viewport=VIEWPORT,
            locale="ko-KR",
            ignore_https_errors=True,
            record_har_path=str(HAR_DIR / "session.har"),
            record_har_content="embed",
        )
        ctx.set_default_timeout(DEFAULT_TIMEOUT_MS)
        page = ctx.new_page()
        console_msgs, network, dialogs = setup_listeners(page)
        all_console = console_msgs
        all_network = network
        all_dialogs = dialogs

        # ─── S1: storage 청소 (새 컨텍스트 = 자동) ───
        results.append({
            "step": "S1-storage-cleanup",
            "status": "PASS",
            "note": "새 컨텍스트 = cookies/storage 자동 청소",
        })
        print("[S1] storage cleanup OK (new context)")

        # ─── S2: fresh 로그인 ───
        r_login = login_with_remember(page)
        r_login["screenshot"] = shot(page, "S2_login")
        results.append(r_login)
        print(f"[S2] {r_login['status']} — {r_login['note']}")
        if r_login["status"] != "PASS":
            ctx.close()
            browser.close()
            _save(results, all_console, all_network, all_dialogs)
            return

        # ─── S3: AgentChat 정상 send ───
        before_console_len = len(console_msgs)
        before_net_len = len(network)
        r_chat = agentchat_send(page, "ping 5step S3")
        r_chat["screenshot"] = shot(page, "S3_agentchat")
        r_chat["new_console_errors"] = [
            c for c in console_msgs[before_console_len:] if c["type"] == "error"
        ]
        r_chat["new_4xx_5xx"] = [
            n for n in network[before_net_len:] if 400 <= n.get("status", 0) < 600
        ]
        results.append(r_chat)
        print(f"[S3] {r_chat['status']} — {r_chat['note']}")
        print(f"     new console errors: {len(r_chat['new_console_errors'])}")
        print(f"     new 4xx/5xx: {len(r_chat['new_4xx_5xx'])}")

        # ─── S4: Multi ChatGPT ───
        before_console_len = len(console_msgs)
        before_net_len = len(network)
        r_gpt = multichat_send(page, "ChatGPT", 25.0)
        r_gpt["screenshot"] = shot(page, "S4_multi_chatgpt")
        r_gpt["new_console_errors"] = [
            c for c in console_msgs[before_console_len:] if c["type"] == "error"
        ]
        r_gpt["new_4xx_5xx"] = [
            n for n in network[before_net_len:] if 400 <= n.get("status", 0) < 600
        ]
        results.append(r_gpt)
        print(f"[S4a] {r_gpt['status']} — {r_gpt['note']}")

        # ─── S4: Multi Nexus ───
        before_console_len = len(console_msgs)
        before_net_len = len(network)
        r_nexus = multichat_send(page, "Project Nexus", 80.0)
        r_nexus["screenshot"] = shot(page, "S4_multi_nexus")
        r_nexus["new_console_errors"] = [
            c for c in console_msgs[before_console_len:] if c["type"] == "error"
        ]
        r_nexus["new_4xx_5xx"] = [
            n for n in network[before_net_len:] if 400 <= n.get("status", 0) < 600
        ]
        results.append(r_nexus)
        print(f"[S4b] {r_nexus['status']} — {r_nexus['note']}")

        # ─── V3 (신규, fix-A 트리거 핵심): access + refresh 둘 다 만료 ───
        before_console_len = len(console_msgs)
        before_net_len = len(network)
        r_v3 = inject_expired_both_and_send(page)
        r_v3["screenshot"] = shot(page, "V3_both_expired_fix_a")
        r_v3["new_console_errors"] = [
            c for c in console_msgs[before_console_len:] if c["type"] == "error"
        ]
        r_v3["new_4xx_5xx"] = [
            n for n in network[before_net_len:] if 400 <= n.get("status", 0) < 600
        ]
        results.append(r_v3)
        print(f"[V3] {r_v3['status']} — {r_v3['note']}")

        # 다음 변형을 위해 다시 로그인 (V3 가 storage 청소했을 수 있음)
        if "/login" in page.url:
            login_again = login_with_remember(page)
            print(f"  [re-login for V1] {login_again['status']}")

        # ─── V1: 만료 토큰 + send → 결함 1 재현 ───
        before_console_len = len(console_msgs)
        before_net_len = len(network)
        r_v1 = inject_expired_token_and_send(page)
        r_v1["screenshot"] = shot(page, "V1_expired_token")
        r_v1["new_console_errors"] = [
            c for c in console_msgs[before_console_len:] if c["type"] == "error"
        ]
        r_v1["new_4xx_5xx"] = [
            n for n in network[before_net_len:] if 400 <= n.get("status", 0) < 600
        ]
        results.append(r_v1)
        print(f"[V1] {r_v1['status']} — {r_v1['note']}")

        # ─── V2: alert dismiss + 만료 토큰 ───
        # 새 컨텍스트로 진행 — 이전 상태 격리
        ctx.close()
        ctx2 = browser.new_context(
            viewport=VIEWPORT,
            locale="ko-KR",
            ignore_https_errors=True,
            record_har_path=str(HAR_DIR / "session_v2.har"),
            record_har_content="embed",
        )
        ctx2.set_default_timeout(DEFAULT_TIMEOUT_MS)
        page2 = ctx2.new_page()
        c2, n2, d2 = setup_listeners(page2)
        # 로그인 먼저
        r_v2_login = login_with_remember(page2)
        if r_v2_login["status"] == "PASS":
            before_c = len(c2)
            before_n = len(n2)
            r_v2 = alert_blocked_send(page2)
            r_v2["screenshot"] = shot(page2, "V2_alert_dismiss")
            r_v2["new_console_errors"] = [c for c in c2[before_c:] if c["type"] == "error"]
            r_v2["new_4xx_5xx"] = [n for n in n2[before_n:] if 400 <= n.get("status", 0) < 600]
        else:
            r_v2 = {
                "step": "V2-alert-dismiss-expired",
                "status": "SKIP",
                "note": "v2 컨텍스트 로그인 실패 — V2 skip",
            }
        results.append(r_v2)
        print(f"[V2] {r_v2['status']} — {r_v2['note']}")
        all_console.extend(c2)
        all_network.extend(n2)
        all_dialogs.extend(d2)

        ctx2.close()
        browser.close()

    _save(results, all_console, all_network, all_dialogs)


def _save(results, console, network, dialogs):
    summary = {
        "track": "사용자 측 5단 검증 자동 시뮬레이션 — 2026-05-17",
        "ts": now_ts(),
        "results": results,
        "totals": {
            "console_errors": len([c for c in console if c.get("type") == "error"]),
            "network_4xx_5xx": len([n for n in network if 400 <= n.get("status", 0) < 600]),
            "dialogs": len(dialogs),
        },
        "all_dialogs": dialogs,
        "har_dir": str(HAR_DIR).replace("\\", "/"),
    }
    counters = {"PASS": 0, "FAIL": 0, "SKIP": 0}
    for r in results:
        s = r.get("status", "?")
        counters[s] = counters.get(s, 0) + 1
    summary["counters"] = counters

    with open(RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n[done] counters={counters}")
    print(f"[result] {RESULT_PATH}")
    print(f"[har] {HAR_DIR}")


if __name__ == "__main__":
    main()
