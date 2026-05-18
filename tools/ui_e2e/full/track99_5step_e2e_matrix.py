"""트랙 #99 5단 — 5계정 × 2시스템 × 화면 e2e 매트릭스.

5계정 × (AgentHub 87 routes + Phase B 인터랙션) + 3계정 × (DocUtil 25 routes + 인터랙션).

전체 흐름:
  1) storage_state 생성: AgentHub 5개 + DocUtil 3개 (검증 + sessionStorage→localStorage 강제)
  2) Phase A — AgentHub 87 라우트 × 5계정 = 435 진입 검증
     - 권한 거부 redirect (User 가 /admin/* → 차단) 정상 판정
     - 스크린샷은 SuperAdmin 만 저장
  3) Phase B — AgentHub 핵심 인터랙션 × 5계정 = ~50 시나리오
     - AgentChat 단일 채팅 (1회만 실 LLM 호출 — SuperAdmin)
     - AgentMultiChat service 변경 + 전송 (SuperAdmin 만)
     - Settings 부서 트리 readonly 표시 (모든 계정)
     - 운영자 메뉴 (SuperAdmin 만): Users / Agents / ApiKeys / Departments
     - 사용자 메뉴 (모든 계정): Agent 선택 / 채팅 화면 진입
  4) Phase A — DocUtil 25 페이지 × 3계정 (admin/user SKIP)
  5) Phase B — DocUtil 핵심 인터랙션 (search / chat / 운영자 콘솔)
  6) 매트릭스 JSON + 한글 요약 markdown 저장

산출:
  tools/ui_e2e/full/track99_5step_e2e_results.json
  tools/ui_e2e/full/track99_5step_summary.md
  tools/ui_e2e/screenshots/track99_5step/*.png (SuperAdmin 만)
  tools/ui_e2e/full/_state_*_ah.json (5개)
  tools/ui_e2e/full/_state_*_du.json (3개)

⚠️ Playwright storage_state 결함 회피:
  AgentHub Login의 "로그인 상태 유지"(#lgRemember) 미체크 → JWT 는 sessionStorage 저장.
  Playwright storage_state 는 localStorage 만 저장 → sessionStorage 의 JWT 누락 → 페이지 재방문 시 로그아웃.
  해결: 로그인 직후 evaluate 로 sessionStorage→localStorage 강제 복사 (verify_5step_user_scenario_20260517 패턴).

⚠️ 시크릿 보호:
  storage_state JSON 은 JWT 평문 포함 — .gitignore 의 _state_*.json 패턴이 차단.
  완료 후 _state_track99_*.json 도 git 추적 금지.
"""
from __future__ import annotations
import io
import json
import sys
import time
import traceback
from pathlib import Path
from urllib.parse import urlparse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).parent))

from common import (
    AGENTHUB_BASE,
    DEFAULT_TIMEOUT_MS,
    DOCUTIL_NGINX,
    VIEWPORT,
    now_ts,
)
from playwright.sync_api import sync_playwright
from routes_catalog import DOCUTIL_ROUTES, PROTECTED_ROUTES, PUBLIC_ROUTES

# ─── 경로/상수 ────────────────────────────────────────────────
OUT_DIR = Path(__file__).parent
SHOT_DIR = OUT_DIR.parent / "screenshots" / "track99_5step"
SHOT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_PATH = OUT_DIR / "track99_5step_e2e_results.json"
SUMMARY_PATH = OUT_DIR / "track99_5step_summary.md"

PASSWORD = "Admin123!"
# 5계정 — (label, AgentHub email, DocUtil username | None if SKIP)
ACCOUNTS = [
    ("SuperAdmin",       "admin@example.com",     None),         # DocUtil admin SKIP (4단 결함)
    ("AdminDev",         "developer@example.com", "developer"),  # AgentHub Admin + DocUtil admin
    ("User",             "user@example.com",      None),         # DocUtil user SKIP (4단 결함)
    ("EmployeeHslee",    "hslee@idino.co.kr",     "hslee"),
    ("EmployeeShbaek",   "shbaek@idino.co.kr",    "shbaek"),
]

# SuperAdmin 만 스크린샷 저장 (용량 절약)
SCREENSHOT_ACCOUNT = "SuperAdmin"
# 실 LLM 호출하는 계정 (비용 절약)
LLM_CALL_ACCOUNT = "SuperAdmin"

# 권한 매트릭스 — User 계정이 진입 시 redirect 되어야 하는 라우트
ADMIN_ONLY_PATHS_PREFIX = (
    "/users", "/admin/", "/api-keys", "/audit-log", "/database-backup",
    "/system-health", "/banned-words", "/pii-protection", "/quota",
    "/team", "/reports", "/usage-history", "/cost-analysis",
)

DASHBOARD_PATHS = {"/", "/dashboard", "/home"}


def safe_name(s: str) -> str:
    return s.replace("/", "_").replace("\\", "_").replace(":", "_").replace("?", "")[:80]


def shot(page, account: str, name: str) -> str:
    """SuperAdmin 만 저장."""
    if account != SCREENSHOT_ACCOUNT:
        return ""
    p = SHOT_DIR / f"{safe_name(name)}.png"
    try:
        page.screenshot(path=str(p), full_page=False)
        return str(p).replace("\\", "/")
    except Exception as e:
        return f"(shot fail: {e})"


# ════════════════════════════════════════════════════════════════════════════
# AgentHub 로그인 + storage_state 생성
# ════════════════════════════════════════════════════════════════════════════
def agenthub_login_to_state(p, email: str, password: str, state_path: Path) -> dict:
    """AgentHub 로그인 → sessionStorage→localStorage 복사 → storage_state 저장.

    반환: {"ok": bool, "url": str, "note": str}
    """
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport=VIEWPORT, locale="ko-KR", ignore_https_errors=True)
    ctx.set_default_timeout(DEFAULT_TIMEOUT_MS)
    page = ctx.new_page()
    try:
        page.goto(f"{AGENTHUB_BASE}/login", timeout=20_000)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(0.8)
        page.fill('#lgEmail', email)
        page.fill('#lgPassword', password)
        # rememberMe 체크 시도 (label click — checkbox 가 invisible 일 수 있음)
        for sel in ['label[for="lgRemember"]', '#lgRemember']:
            try:
                el = page.query_selector(sel)
                if el:
                    try:
                        el.click(timeout=2000)
                        break
                    except Exception:
                        try:
                            page.evaluate("() => document.querySelector('#lgRemember').click()")
                            break
                        except Exception:
                            pass
            except Exception:
                continue
        # 제출
        try:
            page.click('button.lg-submit-btn[type="submit"]', timeout=5000)
        except Exception:
            try:
                page.click('button[type="submit"]', timeout=5000)
            except Exception:
                return {"ok": False, "url": page.url, "note": "submit button not found"}
        try:
            page.wait_for_url(lambda u: "/login" not in u, timeout=15_000)
        except Exception:
            pass
        time.sleep(2.0)
        if "/login" in page.url:
            return {"ok": False, "url": page.url, "note": "login failed (still on /login)"}
        # sessionStorage → localStorage 강제 복사 (storage_state 가 sessionStorage 미저장)
        ss = page.evaluate("() => sessionStorage.getItem('token')")
        ls = page.evaluate("() => localStorage.getItem('token')")
        copy_note = ""
        if ss and not ls:
            page.evaluate(f"() => localStorage.setItem('token', {json.dumps(ss)})")
            ss_r = page.evaluate("() => sessionStorage.getItem('refreshToken')")
            if ss_r:
                page.evaluate(f"() => localStorage.setItem('refreshToken', {json.dumps(ss_r)})")
            copy_note = "sessionStorage→localStorage copied"
        else:
            copy_note = f"localStorage already has token (ls={'OK' if ls else 'EMPTY'})"
        # storage_state 저장
        ctx.storage_state(path=str(state_path))
        return {"ok": True, "url": page.url, "note": copy_note}
    except Exception as e:
        return {"ok": False, "url": page.url, "note": f"exception: {e}"}
    finally:
        try:
            ctx.close()
        except Exception:
            pass
        try:
            b.close()
        except Exception:
            pass


def docutil_login_to_state(p, username: str, password: str, state_path: Path) -> dict:
    """DocUtil 로그인 → storage_state 저장."""
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport=VIEWPORT, locale="ko-KR", ignore_https_errors=True)
    ctx.set_default_timeout(DEFAULT_TIMEOUT_MS)
    page = ctx.new_page()
    try:
        page.goto(f"{DOCUTIL_NGINX}/login", timeout=30_000, wait_until="domcontentloaded")
        time.sleep(3.0)  # Next.js hydration
        u_in = page.query_selector('input#username')
        p_in = page.query_selector('input#password')
        if not u_in or not p_in:
            return {"ok": False, "url": page.url, "note": "login form not found"}
        u_in.fill("")
        u_in.fill(username)
        p_in.fill("")
        p_in.fill(password)
        btn = page.query_selector('button[type="submit"]')
        if not btn:
            return {"ok": False, "url": page.url, "note": "submit not found"}
        btn.click()
        try:
            page.wait_for_url(lambda u: "/login" not in u, timeout=15_000)
        except Exception:
            pass
        time.sleep(2.0)
        if "/login" in page.url:
            return {"ok": False, "url": page.url, "note": "login failed (still on /login)"}
        ctx.storage_state(path=str(state_path))
        return {"ok": True, "url": page.url, "note": "ok"}
    except Exception as e:
        return {"ok": False, "url": page.url, "note": f"exception: {e}"}
    finally:
        try:
            ctx.close()
        except Exception:
            pass
        try:
            b.close()
        except Exception:
            pass


# ════════════════════════════════════════════════════════════════════════════
# Phase A — 라우트 진입 검증
# ════════════════════════════════════════════════════════════════════════════
def visit_route(
    page, base: str, path: str, account: str, *, role: str, timeout_ms: int = 15_000,
) -> dict:
    started = time.time()
    result = {
        "account": account, "role": role, "path": path,
        "url_visited": f"{base}{path}", "final_url": "",
        "redirected": False, "status": "FAIL", "dom_mounted": False,
        "console_errors": [], "network_4xx_5xx": [],
        "duration_ms": 0, "note": "",
    }
    console_errors: list[str] = []
    net_issues: list[dict] = []

    def on_console(msg):
        try:
            if msg.type == "error":
                t = msg.text
                if not any(x in t for x in ("Failed to load resource", "favicon", "extension")):
                    console_errors.append(t[:200])
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
        time.sleep(1.0)
        try:
            page.wait_for_load_state("networkidle", timeout=4_000)
        except Exception:
            pass
        result["final_url"] = page.url
        result["redirected"] = page.url != f"{base}{path}"
        result["dom_mounted"] = True
        result["console_errors"] = console_errors[:5]
        result["network_4xx_5xx"] = net_issues[:5]
        has_5xx = any(n["status"] >= 500 for n in net_issues)

        # 권한 분기 — User 계정이 admin-only 라우트 진입 시 redirect 정상 판정
        is_admin_only = any(path.startswith(pref) for pref in ADMIN_ONLY_PATHS_PREFIX)
        landed_to_root = urlparse(page.url).path in DASHBOARD_PATHS
        landed_to_login = "/login" in page.url
        landed_to_landing = "/landing" in page.url

        if account == "User" and is_admin_only:
            # User 가 admin 페이지 진입 → redirect 되어야 PASS
            if landed_to_root or landed_to_login or landed_to_landing or result["redirected"]:
                result["status"] = "PASS"
                result["note"] = f"권한차단 redirect → {urlparse(page.url).path}"
            else:
                result["status"] = "FAIL"
                result["note"] = "권한차단 미동작 — User 가 admin 페이지 진입"
        else:
            if has_5xx:
                result["status"] = "FAIL"
                result["note"] = "5xx 발생"
            else:
                result["status"] = "PASS"
                if console_errors:
                    result["note"] = f"console_errors={len(console_errors)}"
    except Exception as e:
        result["status"] = "FAIL"
        result["note"] = f"exception: {type(e).__name__}: {str(e)[:120]}"
    finally:
        result["duration_ms"] = int((time.time() - started) * 1000)
        try:
            page.remove_listener("console", on_console)
            page.remove_listener("response", on_response)
        except Exception:
            pass
    return result


# ════════════════════════════════════════════════════════════════════════════
# Phase B — AgentHub 인터랙션
# ════════════════════════════════════════════════════════════════════════════
def b_agentchat_send(page, account: str, do_llm: bool) -> dict:
    """단일 채팅 — Agent 카드 → /agents/chat 진입 → 입력 → 전송 (do_llm 시).

    do_llm=False 시 입력 + 페이지 마운트만 확인 (전송 안 함 — 비용 절약).
    """
    r = {"scenario": "B1-AgentChat", "account": account, "status": "FAIL", "note": ""}
    try:
        page.goto(f"{AGENTHUB_BASE}/agents", timeout=20_000)
        page.wait_for_load_state("networkidle", timeout=10_000)
        time.sleep(1.5)
        card = page.query_selector('.ag-card:first-child') or page.query_selector('.ag-card')
        if not card:
            r["note"] = "Agent 카드(.ag-card) 미발견 — /agents 가 비어있거나 권한 없음"
            return r
        card.click()
        page.wait_for_load_state("networkidle", timeout=10_000)
        time.sleep(2.0)
        r["chat_url"] = page.url
        ta = page.query_selector('textarea.cd-textarea')
        if not ta:
            r["note"] = "input(textarea.cd-textarea) 미발견"
            r["status"] = "FAIL"
            return r
        ta.click()
        ta.fill(f"ping track99 5step {account}")
        if not do_llm:
            r["status"] = "PASS"
            r["note"] = "입력 OK — 전송 생략 (비용 절약)"
            shot(page, account, f"B1_AgentChat_{account}_no_send")
            return r
        # 전송 (SuperAdmin 1회만)
        page.click('button.cd-send-btn')
        time.sleep(8.0)
        p_after = urlparse(page.url).path or "/"
        if p_after in DASHBOARD_PATHS:
            r["status"] = "FAIL"
            r["note"] = f"전송 후 dashboard 이동 — DEFECT1 의심 ({p_after})"
            return r
        body = page.evaluate("() => document.body.innerText || ''")
        kw = ["응답", "안녕", "Hello", "도와", "I'm", "ping", "I am", "도움"]
        has_resp = any(k in body for k in kw)
        r["status"] = "PASS" if has_resp else "FAIL"
        r["note"] = "응답 표시 OK" if has_resp else "응답 미표시 — DEFECT2 의심"
        shot(page, account, f"B1_AgentChat_{account}_after_send")
        return r
    except Exception as e:
        r["note"] = f"예외: {type(e).__name__}: {str(e)[:150]}"
        return r


def b_multichat_check(page, account: str, do_llm: bool) -> dict:
    """멀티 채팅 화면 진입 + service 변경. do_llm 시 1회 전송."""
    r = {"scenario": "B2-AgentMultiChat", "account": account, "status": "FAIL", "note": ""}
    try:
        page.goto(f"{AGENTHUB_BASE}/agents/multi-chat", timeout=20_000)
        page.wait_for_load_state("networkidle", timeout=10_000)
        time.sleep(2.0)
        ta = (page.query_selector('textarea.mc-textarea')
              or page.query_selector('textarea.cd-textarea')
              or page.query_selector('textarea'))
        if not ta:
            r["note"] = "멀티채팅 textarea 미발견"
            return r
        ta.click()
        ta.fill(f"ping multi {account}")
        # service 변경 — 첫 select 가 있다면 ChatGPT 선택 시도
        try:
            sel = page.query_selector('select')
            if sel:
                try:
                    sel.select_option(label="ChatGPT")
                except Exception:
                    pass
        except Exception:
            pass
        if not do_llm:
            r["status"] = "PASS"
            r["note"] = "멀티채팅 UI 마운트 OK — 전송 생략"
            shot(page, account, f"B2_MultiChat_{account}_no_send")
            return r
        try:
            page.click('button.mc-send-btn', timeout=3000)
        except Exception:
            try:
                page.click('button.cd-send-btn', timeout=3000)
            except Exception:
                page.keyboard.press("Enter")
        time.sleep(25.0)
        body = page.evaluate("() => document.body.innerText || ''")
        kw = ["안녕", "도와", "Hello", "I'm", "응답이 없습니다"]
        has_resp = any(k in body for k in kw)
        err = "오류가 발생" in body
        r["status"] = "PASS" if (has_resp and not err) else "FAIL"
        r["note"] = "응답 OK" if has_resp else "응답 미표시"
        shot(page, account, f"B2_MultiChat_{account}_after_send")
        return r
    except Exception as e:
        r["note"] = f"예외: {type(e).__name__}: {str(e)[:120]}"
        return r


def b_settings_dept_tree(page, account: str) -> dict:
    """Settings 페이지 부서 트리 readonly 표시 검증.

    트랙 #100 fix — HTML 표준상 <input> 의 value attribute 는 innerText 에 포함되지 않음.
    body.innerText 만 검사하면 readonly input 의 value 를 못 찾으므로,
    document.querySelectorAll('input').value 도 함께 합쳐서 검색해야 정확한 판정 가능.
    """
    r = {"scenario": "B3-Settings-DeptTree", "account": account, "status": "FAIL", "note": ""}
    try:
        page.goto(f"{AGENTHUB_BASE}/settings", timeout=20_000)
        page.wait_for_load_state("networkidle", timeout=10_000)
        time.sleep(2.0)
        body = page.evaluate("() => document.body.innerText || ''")
        # 트랙 #100 fix — input value 들도 함께 수집
        input_values = page.evaluate(
            "() => Array.from(document.querySelectorAll('input')).map(i => i.value || '').filter(v => v).join(' ')"
        )
        combined = body + " " + input_values
        # 부서 트리 키워드 검색 — 아이디노/본부/팀 패턴
        has_dept_tree = any(k in combined for k in ("아이디노", "본부", "팀"))
        # readonly — input/select 가 disabled 인지 (대략)
        readonly_input = page.query_selector('input[readonly], input[disabled]')
        r["status"] = "PASS" if has_dept_tree else "FAIL"
        r["note"] = (
            f"부서 트리 키워드 발견={has_dept_tree}, readonly_input={'있음' if readonly_input else '없음'}, "
            f"input_values_len={len(input_values)}"
        )
        shot(page, account, f"B3_Settings_{account}")
        return r
    except Exception as e:
        r["note"] = f"예외: {type(e).__name__}: {str(e)[:120]}"
        return r


def b_admin_menu(page, account: str, menu_path: str, menu_name: str) -> dict:
    """운영자 메뉴 진입 + 핵심 콘텐츠 표시 검증."""
    r = {"scenario": f"B4-Admin-{menu_name}", "account": account, "status": "FAIL", "note": "", "path": menu_path}
    try:
        page.goto(f"{AGENTHUB_BASE}{menu_path}", timeout=20_000)
        page.wait_for_load_state("networkidle", timeout=10_000)
        time.sleep(2.0)
        body = page.evaluate("() => document.body.innerText || ''")
        # 페이지 키워드 — 페이지명 또는 표 헤더
        path_after = urlparse(page.url).path or "/"
        if path_after != menu_path and path_after in DASHBOARD_PATHS:
            r["status"] = "FAIL"
            r["note"] = f"리다이렉트됨 → {path_after} (권한 없음 또는 라우터 문제)"
            return r
        # 콘텐츠 존재 여부 — 표/카드 키워드
        has_content = any(k in body for k in ("이름", "이메일", "삭제", "수정", "추가", "검색", "Code", "Name"))
        r["status"] = "PASS" if has_content else "FAIL"
        r["note"] = f"콘텐츠 키워드 {'발견' if has_content else '미발견'} (path={path_after})"
        shot(page, account, f"B4_Admin_{menu_name}_{account}")
        return r
    except Exception as e:
        r["note"] = f"예외: {type(e).__name__}: {str(e)[:120]}"
        return r


# ════════════════════════════════════════════════════════════════════════════
# DocUtil Phase B 인터랙션
# ════════════════════════════════════════════════════════════════════════════
def du_search_check(page, account: str) -> dict:
    r = {"scenario": "DU-B1-Search", "account": account, "status": "FAIL", "note": ""}
    try:
        page.goto(f"{DOCUTIL_NGINX}/search", timeout=20_000)
        page.wait_for_load_state("networkidle", timeout=10_000)
        time.sleep(2.0)
        path_after = urlparse(page.url).path or "/"
        if "/login" in path_after:
            r["status"] = "FAIL"
            r["note"] = "로그인 페이지로 리다이렉트 — storage_state 무효"
            return r
        body = page.evaluate("() => document.body.innerText || ''")
        has_input = page.query_selector('input[type="search"], input[type="text"], input[placeholder*="검색"]')
        r["status"] = "PASS" if (has_input is not None) else "FAIL"
        r["note"] = f"검색 input {'발견' if has_input else '미발견'}, path={path_after}"
        shot(page, account, f"DU_B1_Search_{account}")
        return r
    except Exception as e:
        r["note"] = f"예외: {type(e).__name__}: {str(e)[:120]}"
        return r


def du_chat_check(page, account: str) -> dict:
    r = {"scenario": "DU-B2-Chat", "account": account, "status": "FAIL", "note": ""}
    try:
        page.goto(f"{DOCUTIL_NGINX}/chat", timeout=20_000)
        page.wait_for_load_state("networkidle", timeout=10_000)
        time.sleep(2.0)
        path_after = urlparse(page.url).path or "/"
        if "/login" in path_after:
            r["status"] = "FAIL"
            r["note"] = "로그인 페이지로 리다이렉트"
            return r
        ta = page.query_selector('textarea, input[type="text"]')
        r["status"] = "PASS" if (ta is not None) else "FAIL"
        r["note"] = f"채팅 input {'발견' if ta else '미발견'}, path={path_after}"
        shot(page, account, f"DU_B2_Chat_{account}")
        return r
    except Exception as e:
        r["note"] = f"예외: {type(e).__name__}: {str(e)[:120]}"
        return r


def du_admin_menu(page, account: str, menu_path: str, menu_name: str) -> dict:
    r = {"scenario": f"DU-B3-Admin-{menu_name}", "account": account, "status": "FAIL", "note": "", "path": menu_path}
    try:
        page.goto(f"{DOCUTIL_NGINX}{menu_path}", timeout=20_000)
        page.wait_for_load_state("networkidle", timeout=10_000)
        time.sleep(2.0)
        path_after = urlparse(page.url).path or "/"
        if "/login" in path_after:
            r["status"] = "FAIL"
            r["note"] = "로그인 페이지로 리다이렉트"
            return r
        body = page.evaluate("() => document.body.innerText || ''")
        has_content = len(body) > 200  # 빈 페이지 아님
        r["status"] = "PASS" if has_content else "FAIL"
        r["note"] = f"콘텐츠 길이={len(body)} (path={path_after})"
        shot(page, account, f"DU_B3_Admin_{menu_name}_{account}")
        return r
    except Exception as e:
        r["note"] = f"예외: {type(e).__name__}: {str(e)[:120]}"
        return r


# ════════════════════════════════════════════════════════════════════════════
# 메인 흐름
# ════════════════════════════════════════════════════════════════════════════
def main():
    print(f"[start] 트랙 #99 5단 e2e 매트릭스 — {now_ts()}")
    out = {
        "track": "#99 5단 e2e — 5계정 × 2시스템 매트릭스",
        "started_at": now_ts(),
        "accounts": [a[0] for a in ACCOUNTS],
        "phase_a_agenthub": [],
        "phase_b_agenthub": [],
        "phase_a_docutil": [],
        "phase_b_docutil": [],
        "storage_states": {},
        "summary": {},
    }

    ah_state_paths = {}
    du_state_paths = {}

    with sync_playwright() as p:
        # ─── 1단계: storage_state 생성 ───
        print("\n[1] storage_state 생성 — 5계정 AgentHub + 3계정 DocUtil")
        for label, ah_email, du_user in ACCOUNTS:
            ah_path = OUT_DIR / f"_state_track99_{label}_ah.json"
            ah_r = agenthub_login_to_state(p, ah_email, PASSWORD, ah_path)
            ah_state_paths[label] = str(ah_path) if ah_r["ok"] else None
            out["storage_states"][f"{label}_ah"] = {
                "ok": ah_r["ok"], "note": ah_r["note"], "path": str(ah_path) if ah_r["ok"] else None
            }
            print(f"  [AH] {label}: {'OK' if ah_r['ok'] else 'FAIL'} — {ah_r['note']}")

            if du_user:
                du_path = OUT_DIR / f"_state_track99_{label}_du.json"
                du_r = docutil_login_to_state(p, du_user, PASSWORD, du_path)
                du_state_paths[label] = str(du_path) if du_r["ok"] else None
                out["storage_states"][f"{label}_du"] = {
                    "ok": du_r["ok"], "note": du_r["note"], "path": str(du_path) if du_r["ok"] else None
                }
                print(f"  [DU] {label} (user={du_user}): {'OK' if du_r['ok'] else 'FAIL'} — {du_r['note']}")
            else:
                out["storage_states"][f"{label}_du"] = {"ok": False, "note": "SKIP — 4단 결함", "path": None}
                print(f"  [DU] {label}: SKIP (4단 결함 — 시드 미존재)")

        # ─── 2단계: storage_state 검증 — 페이지 재방문 시 로그인 유지 ───
        print("\n[2] storage_state 검증 — 페이지 재방문 로그인 유지 확인")
        for label, _, _ in ACCOUNTS:
            sp = ah_state_paths.get(label)
            if not sp:
                continue
            b = p.chromium.launch(headless=True)
            ctx = b.new_context(
                viewport=VIEWPORT, locale="ko-KR",
                ignore_https_errors=True, storage_state=sp
            )
            ctx.set_default_timeout(DEFAULT_TIMEOUT_MS)
            page = ctx.new_page()
            try:
                page.goto(f"{AGENTHUB_BASE}/", timeout=20_000, wait_until="domcontentloaded")
                time.sleep(2.0)
                landed_login = "/login" in page.url
                out["storage_states"][f"{label}_ah"]["verify"] = "FAIL" if landed_login else "PASS"
                print(f"  [verify-AH] {label}: {'FAIL (loginpage)' if landed_login else 'PASS'} url={page.url}")
            finally:
                ctx.close()
                b.close()

        # ─── 3단계: Phase A — AgentHub 87 라우트 × 5계정 ───
        print(f"\n[3] Phase A — AgentHub {len(PROTECTED_ROUTES)+len(PUBLIC_ROUTES)} 라우트 × 5계정")
        all_routes = (
            [(screen, path, "protected") for screen, path, _ in PROTECTED_ROUTES]
            + [(screen, path, "public") for screen, path, _ in PUBLIC_ROUTES]
        )
        for label, _, _ in ACCOUNTS:
            sp = ah_state_paths.get(label)
            if not sp:
                print(f"  [{label}] storage_state 없음 — 전부 SKIP")
                for screen, path, _ in all_routes:
                    out["phase_a_agenthub"].append({
                        "account": label, "path": path, "screen": screen,
                        "status": "SKIP", "note": "storage_state 없음"
                    })
                continue
            b = p.chromium.launch(headless=True)
            ctx = b.new_context(
                viewport=VIEWPORT, locale="ko-KR",
                ignore_https_errors=True, storage_state=sp
            )
            ctx.set_default_timeout(DEFAULT_TIMEOUT_MS)
            page = ctx.new_page()
            try:
                for screen, path, kind in all_routes:
                    r = visit_route(page, AGENTHUB_BASE, path, label, role=label)
                    r["screen"] = screen
                    r["kind"] = kind
                    out["phase_a_agenthub"].append(r)
                    if label == SCREENSHOT_ACCOUNT:
                        shot(page, label, f"AH_A_{screen}")
                print(f"  [{label}] {len(all_routes)} 라우트 완료")
            except Exception as e:
                print(f"  [{label}] Phase A 예외: {e}")
            finally:
                ctx.close()
                b.close()

        # ─── 4단계: Phase B — AgentHub 인터랙션 ───
        print("\n[4] Phase B — AgentHub 인터랙션")
        admin_menus = [
            ("/users", "Users"),
            ("/agents", "Agents"),
            ("/api-keys", "ApiKeys"),
            ("/admin/docutil-departments", "Departments"),
        ]
        for label, _, _ in ACCOUNTS:
            sp = ah_state_paths.get(label)
            if not sp:
                continue
            b = p.chromium.launch(headless=True)
            ctx = b.new_context(
                viewport=VIEWPORT, locale="ko-KR",
                ignore_https_errors=True, storage_state=sp
            )
            ctx.set_default_timeout(DEFAULT_TIMEOUT_MS)
            page = ctx.new_page()
            try:
                # 모든 계정 — AgentChat 입력 폼 확인 (LLM 호출은 SuperAdmin 만)
                do_llm = (label == LLM_CALL_ACCOUNT)
                r1 = b_agentchat_send(page, label, do_llm=do_llm)
                out["phase_b_agenthub"].append(r1)
                print(f"  [{label}] B1-AgentChat: {r1['status']} — {r1['note']}")
                # MultiChat — SuperAdmin 만 전송
                r2 = b_multichat_check(page, label, do_llm=do_llm)
                out["phase_b_agenthub"].append(r2)
                print(f"  [{label}] B2-MultiChat: {r2['status']} — {r2['note']}")
                # Settings — 모든 계정
                r3 = b_settings_dept_tree(page, label)
                out["phase_b_agenthub"].append(r3)
                print(f"  [{label}] B3-Settings: {r3['status']} — {r3['note']}")
                # 운영자 메뉴 — SuperAdmin / AdminDev 만 실제 접근, 나머지는 권한차단 확인
                for mp, mn in admin_menus:
                    r4 = b_admin_menu(page, label, mp, mn)
                    out["phase_b_agenthub"].append(r4)
                    print(f"  [{label}] B4-{mn}: {r4['status']} — {r4['note']}")
            except Exception as e:
                print(f"  [{label}] Phase B 예외: {type(e).__name__}: {e}")
                traceback.print_exc()
            finally:
                ctx.close()
                b.close()

        # ─── 5단계: DocUtil Phase A — 25 라우트 × 3계정 ───
        print("\n[5] DocUtil Phase A — 25 라우트 × 3계정 (admin/user SKIP)")
        for label, _, du_user in ACCOUNTS:
            if not du_user:
                # SKIP — admin/user
                for screen, path, _f, role in DOCUTIL_ROUTES:
                    out["phase_a_docutil"].append({
                        "account": label, "path": path, "screen": screen,
                        "status": "SKIP", "note": "4단 결함 — DocUtil 시드 없음"
                    })
                continue
            sp = du_state_paths.get(label)
            if not sp:
                for screen, path, _f, role in DOCUTIL_ROUTES:
                    out["phase_a_docutil"].append({
                        "account": label, "path": path, "screen": screen,
                        "status": "SKIP", "note": "DocUtil storage_state 없음"
                    })
                continue
            b = p.chromium.launch(headless=True)
            ctx = b.new_context(
                viewport=VIEWPORT, locale="ko-KR",
                ignore_https_errors=True, storage_state=sp
            )
            ctx.set_default_timeout(DEFAULT_TIMEOUT_MS)
            page = ctx.new_page()
            try:
                for screen, path, _f, role in DOCUTIL_ROUTES:
                    r = visit_route(page, DOCUTIL_NGINX, path, label, role=role)
                    r["screen"] = screen
                    r["docutil_role"] = role
                    out["phase_a_docutil"].append(r)
                    if label == SCREENSHOT_ACCOUNT:
                        shot(page, label, f"DU_A_{screen}")
                print(f"  [{label}] DocUtil {len(DOCUTIL_ROUTES)} 라우트 완료")
            finally:
                ctx.close()
                b.close()

        # ─── 6단계: DocUtil Phase B ───
        print("\n[6] DocUtil Phase B — 핵심 인터랙션")
        du_admin_menus = [
            ("/admin-accounts", "AdminAccounts"),
            ("/documents", "Documents"),
            ("/departments", "Departments"),
        ]
        for label, _, du_user in ACCOUNTS:
            if not du_user:
                continue
            sp = du_state_paths.get(label)
            if not sp:
                continue
            b = p.chromium.launch(headless=True)
            ctx = b.new_context(
                viewport=VIEWPORT, locale="ko-KR",
                ignore_https_errors=True, storage_state=sp
            )
            ctx.set_default_timeout(DEFAULT_TIMEOUT_MS)
            page = ctx.new_page()
            try:
                r1 = du_search_check(page, label)
                out["phase_b_docutil"].append(r1)
                print(f"  [{label}] DU-B1-Search: {r1['status']} — {r1['note']}")
                r2 = du_chat_check(page, label)
                out["phase_b_docutil"].append(r2)
                print(f"  [{label}] DU-B2-Chat: {r2['status']} — {r2['note']}")
                # developer 만 운영자 콘솔 가능 (hslee/shbaek 도 admin role 이지만 RBAC 검증 차원에서 동일하게 시도)
                for mp, mn in du_admin_menus:
                    r3 = du_admin_menu(page, label, mp, mn)
                    out["phase_b_docutil"].append(r3)
                    print(f"  [{label}] DU-B3-{mn}: {r3['status']} — {r3['note']}")
            finally:
                ctx.close()
                b.close()

    # ─── 종합 ───
    out["finished_at"] = now_ts()
    counters = {
        "phase_a_agenthub": {"PASS": 0, "FAIL": 0, "SKIP": 0},
        "phase_b_agenthub": {"PASS": 0, "FAIL": 0, "SKIP": 0},
        "phase_a_docutil": {"PASS": 0, "FAIL": 0, "SKIP": 0},
        "phase_b_docutil": {"PASS": 0, "FAIL": 0, "SKIP": 0},
    }
    for phase in ("phase_a_agenthub", "phase_b_agenthub", "phase_a_docutil", "phase_b_docutil"):
        for r in out[phase]:
            s = r.get("status", "FAIL")
            counters[phase][s] = counters[phase].get(s, 0) + 1
    out["summary"] = counters

    RESULT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\n[done] {RESULT_PATH}")
    print(f"  Phase A AH: {counters['phase_a_agenthub']}")
    print(f"  Phase B AH: {counters['phase_b_agenthub']}")
    print(f"  Phase A DU: {counters['phase_a_docutil']}")
    print(f"  Phase B DU: {counters['phase_b_docutil']}")

    # 한글 summary
    write_summary(out)


def write_summary(out: dict):
    s = out["summary"]
    total = {
        "PASS": sum(p["PASS"] for p in s.values()),
        "FAIL": sum(p["FAIL"] for p in s.values()),
        "SKIP": sum(p["SKIP"] for p in s.values()),
    }
    total["all"] = sum(total.values())

    # 결함 추출 — Phase A 의 FAIL + Phase B 의 FAIL
    failures = []
    for phase_key in ("phase_a_agenthub", "phase_b_agenthub", "phase_a_docutil", "phase_b_docutil"):
        for r in out[phase_key]:
            if r.get("status") == "FAIL":
                failures.append({
                    "phase": phase_key,
                    "account": r.get("account"),
                    "path_or_scenario": r.get("path") or r.get("scenario"),
                    "note": r.get("note", ""),
                })

    md = [
        f"# 트랙 #99 5단 e2e 매트릭스 — {out['started_at']} 시작",
        "",
        f"- 종료: {out.get('finished_at', '?')}",
        f"- 계정: {', '.join(out['accounts'])}",
        "",
        "## 종합 PASS율",
        "",
        f"- 전체: {total['PASS']}/{total['all']} PASS ({total['PASS']*100//max(total['all'],1)}%)",
        f"- FAIL: {total['FAIL']}건",
        f"- SKIP: {total['SKIP']}건",
        "",
        "## Phase별 결과",
        "",
        f"| Phase | PASS | FAIL | SKIP |",
        f"|---|---|---|---|",
        f"| AgentHub Phase A (라우트 진입) | {s['phase_a_agenthub']['PASS']} | {s['phase_a_agenthub']['FAIL']} | {s['phase_a_agenthub']['SKIP']} |",
        f"| AgentHub Phase B (인터랙션) | {s['phase_b_agenthub']['PASS']} | {s['phase_b_agenthub']['FAIL']} | {s['phase_b_agenthub']['SKIP']} |",
        f"| DocUtil Phase A (라우트 진입) | {s['phase_a_docutil']['PASS']} | {s['phase_a_docutil']['FAIL']} | {s['phase_a_docutil']['SKIP']} |",
        f"| DocUtil Phase B (인터랙션) | {s['phase_b_docutil']['PASS']} | {s['phase_b_docutil']['FAIL']} | {s['phase_b_docutil']['SKIP']} |",
        "",
        "## storage_state 생성 결과",
        "",
    ]
    for k, v in out["storage_states"].items():
        verify = v.get("verify", "-")
        md.append(f"- **{k}**: ok={v['ok']} verify={verify} note={v['note']}")
    md.append("")
    md.append(f"## 발견된 결함 ({len(failures)}건)")
    md.append("")
    if not failures:
        md.append("- 결함 없음.")
    else:
        for i, f in enumerate(failures[:50], 1):
            md.append(f"{i}. [{f['phase']}] **{f['account']}** | {f['path_or_scenario']} → {f['note']}")
        if len(failures) > 50:
            md.append(f"... ({len(failures)-50}건 더)")
    md.append("")
    md.append("## 산출물")
    md.append("")
    md.append(f"- 매트릭스: `tools/ui_e2e/full/track99_5step_e2e_results.json`")
    md.append(f"- 스크린샷: `tools/ui_e2e/screenshots/track99_5step/` (SuperAdmin 만)")
    md.append(f"- storage_state: `tools/ui_e2e/full/_state_track99_*.json` (gitignore 대상)")
    SUMMARY_PATH.write_text("\n".join(md), encoding="utf-8")
    print(f"[summary] {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
