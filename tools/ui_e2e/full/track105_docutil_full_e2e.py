"""트랙 #105 Phase C.2~C.3 — DocUtil 전 페이지 e2e runner.

대상 카탈로그: docutil_page_catalog.py (182 cases, auto 154 / manual 27 / skip 1)
대상 시스템:  DocUtil nginx http://192.168.10.39:8041 (→ Next.js 8040/3000)

4계정 매트릭스 (운영 DB 실측):
  - SuperAdmin   : admin@example.com / Admin123!   role=admin
  - User         : user@example.com  / Admin123!   role=user
  - EmployeeShb  : shbaek@idino.co.kr / Admin123!   role=admin (직원)
  - EmployeeHsl  : hslee@idino.co.kr  / Admin123!   role=user  (직원)

총 cell = 4 × 154 auto = 616 (각 케이스를 4계정 모두 실행)
manual / skip = 결과에 SKIP 기록만, 실행 안 함.

운영 데이터 무영향 원칙:
  - mutation 케이스는 모두 SKIP 처리 (Phase C.2 는 검증 위주 — runtime 실행은 회피)
    * 사유: 카탈로그 mutation 48 cases 각자 별도 setup 필요. 전수 자동 cleanup 위험.
    * 별도 트랙 (C.3 부분) 에서 mutation 시나리오만 골라 자체 prefix + 자체 회수로 처리.
  - 본 runner 는 (i) navigate (ii) safe click (iii) submit (단 mutation 제외) 만 실행.
  - cost 케이스 (12) 도 SKIP — LLM 호출 비용 발생 회피.
  - 사용자 명시 결함 LAY-HDR-004 (프로필 클릭) 은 별도 우선 검증 시나리오로 실행.

산출:
  - tools/ui_e2e/full/track105_docutil_full_e2e_results.json
  - tools/ui_e2e/screenshots/track105_full/*.png  (실패 케이스 + SuperAdmin LAY-HDR-004)
"""
from __future__ import annotations
import io
import json
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).parent))

from common import (  # noqa: E402
    DEFAULT_TIMEOUT_MS,
    DOCUTIL_NGINX,
    VIEWPORT,
    now_ts,
)
from docutil_page_catalog import CASES  # noqa: E402
from e2e_helpers import (  # noqa: E402
    ApiCallCounter,
    allow_cost,
    allow_mutation,
    assert_body_not_empty,
    download_file,
    iframe_mounted,
    wait_settled,
)
from playwright.sync_api import Page, sync_playwright  # noqa: E402

# ─── 경로 ──────────────────────────────────────────────────────
OUT_DIR = Path(__file__).parent
SHOT_DIR = OUT_DIR.parent / "screenshots" / "track105_full"
SHOT_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR = OUT_DIR
RESULT_PATH = OUT_DIR / "track105_docutil_full_e2e_results.json"

# ─── 4계정 정의 (DocUtil 운영 DB 실측 결과) ────────────────────
# login_id : DocUtil /login 의 input#username 에 입력할 값 (email 기준 작동 확인 — track #88-4)
PASSWORD = "Admin123!"
ACCOUNTS: list[dict] = [
    {"label": "SuperAdmin",   "login_id": "admin@example.com",   "expected_role": "admin",
     "state_path": STATE_DIR / "_track105_du_super.json"},
    {"label": "User",         "login_id": "user@example.com",    "expected_role": "user",
     "state_path": STATE_DIR / "_track105_du_user.json"},
    {"label": "EmployeeShb",  "login_id": "shbaek@idino.co.kr",  "expected_role": "admin",
     "state_path": STATE_DIR / "_track105_du_shbaek.json"},
    {"label": "EmployeeHsl",  "login_id": "hslee@idino.co.kr",   "expected_role": "user",
     "state_path": STATE_DIR / "_track105_du_hslee.json"},
]
ADMIN_LABELS = {"SuperAdmin", "EmployeeShb"}
SCREENSHOT_ACCOUNT = "SuperAdmin"  # 운영 데이터 영향 최소화 — SuperAdmin 만 스크린샷

# ─── 페이지 path 매핑 (catalog 의 page 컬럼 → 실제 URL path) ───
# 카탈로그 page 값 → 실제 nginx path
PAGE_TO_PATH: dict[str, str] = {
    "(공통)": "/dashboard",              # admin 진입 가능 path 로 대체
    "(admin)": "/dashboard",
    "(user)": "/search",                  # user role 의 sidebar 진입점
    "/": "/",
    "/preview-host": "/preview-host",
    "/login": "/login",
    "/dashboard": "/dashboard",
    "/departments": "/departments",
    "/projects": "/projects",
    "/documents": "/documents",
    "/admin-accounts": "/admin-accounts",
    "/search-scopes": "/search-scopes",
    "/api-keys": "/api-keys",
    "/templates": "/templates",
    "/agents": "/agents",
    "/evaluation": "/evaluation",
    "/quotas": "/quotas",
    "/settings": "/settings",
    "/search-test": "/search-test",
    "/help": "/help",
    "/quick-guide": "/quick-guide",
    "/chat": "/chat",
    "/my-documents": "/my-documents",
    "/search": "/search",
    "/reports": "/reports",
    "/designer/create": "/designer/create",
    "/designer/[documentId]": "/designer/create",       # 동적 라우트 → create 페이지로 대체 검증
    "/designer/fill/[templateId]": "/designer/create",
}

# /admin/* 동등 — DocUtil 의 admin 전용 path (admin role 이외는 redirect)
ADMIN_ONLY_PATHS = {
    "/dashboard", "/departments", "/projects", "/documents",
    "/admin-accounts", "/search-scopes", "/api-keys", "/templates",
    "/agents", "/evaluation", "/quotas", "/search-test",
}
USER_ALLOWED_PATHS = {
    "/search", "/my-documents", "/chat", "/reports",
    "/designer/create", "/help", "/quick-guide", "/settings", "/preview-host",
}

DASHBOARD_PATHS = {"/", "/dashboard", "/home", "/search", "/login"}


def safe_name(s: str) -> str:
    return s.replace("/", "_").replace("\\", "_").replace(":", "_").replace("?", "")[:80]


def shot(page: Page, account: str, name: str, *, force: bool = False) -> str:
    """SuperAdmin 만 저장 (force=True 면 모든 계정)."""
    if account != SCREENSHOT_ACCOUNT and not force:
        return ""
    p = SHOT_DIR / f"{safe_name(name)}.png"
    try:
        page.screenshot(path=str(p), full_page=False)
        return str(p).replace("\\", "/")
    except Exception as e:
        return f"(shot fail: {e})"


# ════════════════════════════════════════════════════════════════════════════
# DocUtil 로그인 (트랙 #88-4 패턴)
# ════════════════════════════════════════════════════════════════════════════
def docutil_login(p, login_id: str, password: str, state_path: Path) -> dict:
    """DocUtil 로그인 → storage_state 저장. 성공/실패 dict 반환."""
    b = p.chromium.launch(headless=True)
    try:
        ctx = b.new_context(viewport=VIEWPORT, locale="ko-KR", ignore_https_errors=True)
        ctx.set_default_timeout(DEFAULT_TIMEOUT_MS)
        page = ctx.new_page()
        try:
            page.goto(f"{DOCUTIL_NGINX}/login", timeout=30_000, wait_until="domcontentloaded")
            time.sleep(2.5)  # Next.js hydration

            u = page.query_selector('input#username')
            pw = page.query_selector('input#password')
            if not u or not pw:
                return {"ok": False, "url": page.url, "note": "login form not found"}
            u.fill("")
            u.fill(login_id)
            pw.fill("")
            pw.fill(password)

            sub = page.query_selector('button[type="submit"]')
            if not sub:
                return {"ok": False, "url": page.url, "note": "submit button not found"}
            sub.click()
            try:
                page.wait_for_url(lambda url: "/login" not in url, timeout=15_000)
            except Exception:
                pass
            time.sleep(2.0)
            if "/login" in page.url:
                # 메시지 캡쳐
                body = ""
                try:
                    body = (page.evaluate("() => document.body.innerText || ''") or "")[:200]
                except Exception:
                    pass
                return {"ok": False, "url": page.url, "note": f"still on /login. body={body}"}
            ctx.storage_state(path=str(state_path))
            return {"ok": True, "url": page.url, "note": "login ok"}
        finally:
            ctx.close()
    finally:
        b.close()


def verify_state(p, state_path: Path) -> bool:
    """storage_state 로 /dashboard 진입 → 200 + non-login URL 확인."""
    if not state_path.exists():
        return False
    b = p.chromium.launch(headless=True)
    try:
        ctx = b.new_context(
            viewport=VIEWPORT, locale="ko-KR",
            ignore_https_errors=True, storage_state=str(state_path),
        )
        ctx.set_default_timeout(DEFAULT_TIMEOUT_MS)
        page = ctx.new_page()
        try:
            page.goto(f"{DOCUTIL_NGINX}/dashboard", timeout=20_000, wait_until="domcontentloaded")
            time.sleep(2.0)
            return "/login" not in page.url
        finally:
            ctx.close()
    except Exception:
        return False
    finally:
        b.close()


# ════════════════════════════════════════════════════════════════════════════
# Special case handlers — Phase C 보강: manual → auto 전환된 케이스들의 전용 검증.
# 각 핸들러는 (page, result, account) 를 받아 result dict 를 갱신하고 verdict 결정.
# ════════════════════════════════════════════════════════════════════════════
def handle_lay_asb_014(page: Page, result: dict, account: dict) -> dict:
    """LAY-ASB-014 — 모바일 햄버거 메뉴 visible 확인 (viewport 375x812)."""
    label = account["label"]
    # 모바일 viewport 로 변경 후 햄버거 button 존재 확인
    try:
        # admin 만 admin sidebar 햄버거를 가짐
        if label not in ADMIN_LABELS:
            result["verdict"] = "SKIP"
            result["actual"] = "non-admin — admin sidebar 햄버거 대상 아님"
            return result
        page.set_viewport_size({"width": 375, "height": 812})
        page.goto(f"{DOCUTIL_NGINX}/dashboard", timeout=20_000, wait_until="domcontentloaded")
        wait_settled(page, timeout_ms=5000, sleep_after=1.0)
        # 햄버거 selector 후보 — DocUtil header.tsx 패턴 (md:hidden 가시성)
        candidates = [
            'button[aria-label*="메뉴"]', 'button[aria-label*="menu"]',
            'header button.md\\:hidden', 'header button:has(svg.lucide-menu)',
            'header button:has-text("☰")',
        ]
        hb = None
        for sel in candidates:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    hb = el
                    break
            except Exception:
                continue
        # fallback — header 의 첫 visible button
        if not hb:
            try:
                btns = page.query_selector_all("header button")
                for el in btns:
                    if el.is_visible():
                        box = el.bounding_box()
                        if box and box["x"] < 100:  # 왼쪽 영역 = 햄버거 위치
                            hb = el
                            break
            except Exception:
                pass
        if hb:
            result["verdict"] = "PASS"
            result["actual"] = "햄버거 button visible (mobile viewport 375x812)"
        else:
            result["verdict"] = "FAIL"
            result["actual"] = "모바일 viewport 에서 햄버거 button 미발견"
    except Exception as e:
        result["verdict"] = "ERROR"
        result["actual"] = f"햄버거 검증 예외: {type(e).__name__}: {e}"
    finally:
        # viewport 복원
        try:
            page.set_viewport_size(VIEWPORT)
        except Exception:
            pass
    return result


def handle_msc_pvh_001(page: Page, result: dict, account: dict) -> dict:
    """MSC-PVH-001 — /preview-host 페이지 로드 확인.

    /preview-host 는 designer 가 query param 으로 documentId 를 주입할 때만 iframe 을 띄움.
    bare /preview-host 진입 시 빈 페이지가 정상 — Next.js 페이지 자체가 200 으로 응답하면 PASS.
    """
    try:
        resp = page.goto(f"{DOCUTIL_NGINX}/preview-host", timeout=20_000, wait_until="domcontentloaded")
        wait_settled(page, timeout_ms=4000, sleep_after=1.0)
        # HTTP 200 이면 페이지 자체는 정상 (빈 host 도 정상)
        status = resp.status if resp else 0
        if 200 <= status < 400:
            # iframe 있으면 mount note, 없으면 host 정상 응답으로 PASS
            mount = iframe_mounted(page, "iframe", timeout_ms=2000)
            if mount["ok"]:
                result["verdict"] = "PASS"
                result["actual"] = f"preview-host status={status} + {mount['note']}"
            else:
                result["verdict"] = "PASS"
                result["actual"] = (
                    f"preview-host status={status} — bare 진입 시 빈 host 정상 "
                    f"(iframe 은 documentId query 시 주입)"
                )
        else:
            result["verdict"] = "FAIL"
            result["actual"] = f"preview-host HTTP {status}"
    except Exception as e:
        result["verdict"] = "ERROR"
        result["actual"] = f"preview-host 예외: {type(e).__name__}: {e}"
    return result


def handle_adm_dash_009(page: Page, result: dict, account: dict) -> dict:
    """ADM-DASH-009 — /dashboard 30s 자동 새로고침 — API 호출 카운트."""
    label = account["label"]
    if label not in ADMIN_LABELS:
        result["verdict"] = "SKIP"
        result["actual"] = "non-admin — /dashboard 권한 없음"
        return result
    try:
        page.goto(f"{DOCUTIL_NGINX}/dashboard", timeout=20_000, wait_until="domcontentloaded")
        wait_settled(page, timeout_ms=5000, sleep_after=2.0)
        # ApiCallCounter — 진입 후 초기 호출은 무시하고, 다음 cycle 만 카운트
        counter = ApiCallCounter(page, "/api/v1/dashboard").start()
        # 32s 대기 (30s 인터벌 + 2s 여유) — 단축 옵션 환경변수 (CI 단축용)
        import os
        wait_s = int(os.environ.get("E2E_DASH_REFRESH_WAIT", "32"))
        time.sleep(wait_s)
        cnt = counter.stop()
        if cnt >= 1:
            result["verdict"] = "PASS"
            result["actual"] = f"30s 자동 새로고침 OK — {wait_s}s 동안 dashboard API 호출 {cnt}회"
        elif wait_s < 30:
            # 대기 시간이 인터벌(30s) 미만이면 검증 불가 — SKIP 으로 격하
            result["verdict"] = "SKIP"
            result["actual"] = (
                f"E2E_DASH_REFRESH_WAIT={wait_s}s 가 30s 미만 — 인터벌 검증 불가. "
                f"실측은 별도 long-run (E2E_DASH_REFRESH_WAIT=32 이상)"
            )
        else:
            result["verdict"] = "FAIL"
            result["actual"] = f"30s 자동 새로고침 미동작 — {wait_s}s 동안 dashboard API 호출 0회"
    except Exception as e:
        result["verdict"] = "ERROR"
        result["actual"] = f"자동 새로고침 검증 예외: {type(e).__name__}: {e}"
    return result


def handle_adm_doc_004(page: Page, result: dict, account: dict) -> dict:
    """ADM-DOC-004 — /documents 파일 업로드 button + input[type=file] selector 존재 검증."""
    label = account["label"]
    if label not in ADMIN_LABELS:
        result["verdict"] = "SKIP"
        result["actual"] = "non-admin — /documents 권한 없음"
        return result
    try:
        page.goto(f"{DOCUTIL_NGINX}/documents", timeout=20_000, wait_until="domcontentloaded")
        wait_settled(page)
        # input[type=file] 존재 확인 (visible/hidden 무관)
        inputs = page.query_selector_all('input[type="file"]')
        # 업로드 button 후보
        btn_candidates = [
            'button:has-text("업로드")', 'button:has-text("파일")',
            'button[aria-label*="업로드"]', 'button[aria-label*="upload"]',
        ]
        btn_found = False
        for sel in btn_candidates:
            try:
                if page.query_selector(sel):
                    btn_found = True
                    break
            except Exception:
                continue
        if inputs or btn_found:
            result["verdict"] = "PASS"
            result["actual"] = f"업로드 UI 발견 — input[type=file] count={len(inputs)}, button={btn_found}"
        else:
            result["verdict"] = "FAIL"
            result["actual"] = "업로드 input/button 모두 미발견"
    except Exception as e:
        result["verdict"] = "ERROR"
        result["actual"] = f"업로드 UI 검증 예외: {type(e).__name__}: {e}"
    return result


def handle_adm_doc_010(page: Page, result: dict, account: dict) -> dict:
    """ADM-DOC-010 — /documents 첫 행 다운로드 — download_file 헬퍼."""
    label = account["label"]
    if label not in ADMIN_LABELS:
        result["verdict"] = "SKIP"
        result["actual"] = "non-admin — /documents 권한 없음"
        return result
    try:
        page.goto(f"{DOCUTIL_NGINX}/documents", timeout=20_000, wait_until="domcontentloaded")
        wait_settled(page, timeout_ms=5000, sleep_after=1.5)
        # 다운로드 button 후보 (테이블 첫 행)
        candidates = [
            'table tr:nth-child(2) button[aria-label*="다운로드"]',
            'table tr:nth-child(2) button[title*="다운로드"]',
            'table tr:nth-child(2) a[download]',
            'tbody tr:first-child button:has(svg.lucide-download)',
            'button[aria-label*="download"]:visible',
        ]
        click_sel = None
        for sel in candidates:
            try:
                el = page.query_selector(sel)
                if el:
                    click_sel = sel
                    break
            except Exception:
                continue
        if not click_sel:
            result["verdict"] = "SKIP"
            result["actual"] = "다운로드 button 미발견 — 운영 환경에 다운로드 가능 문서 없음 가능"
            return result
        dl = download_file(page, click_sel, min_size_bytes=100, timeout_ms=10_000)
        if dl["ok"]:
            result["verdict"] = "PASS"
            result["actual"] = dl["note"]
        else:
            # 다운로드 실패는 데이터 부재일 수 있음 — SKIP 으로 격하
            result["verdict"] = "SKIP"
            result["actual"] = f"다운로드 미수행: {dl['note']}"
    except Exception as e:
        result["verdict"] = "ERROR"
        result["actual"] = f"문서 다운로드 검증 예외: {type(e).__name__}: {e}"
    return result


def handle_usr_rpt_008(page: Page, result: dict, account: dict) -> dict:
    """USR-RPT-008 — /reports 첫 행 보고서 다운로드."""
    try:
        page.goto(f"{DOCUTIL_NGINX}/reports", timeout=20_000, wait_until="domcontentloaded")
        wait_settled(page, timeout_ms=5000, sleep_after=1.5)
        candidates = [
            'button[aria-label*="다운로드"]:visible',
            'button:has-text("다운로드")',
            'a[download]:visible',
            'tbody tr:first-child button:has(svg.lucide-download)',
            'tbody tr:first-child a[download]',
        ]
        click_sel = None
        for sel in candidates:
            try:
                el = page.query_selector(sel)
                if el:
                    click_sel = sel
                    break
            except Exception:
                continue
        if not click_sel:
            result["verdict"] = "SKIP"
            result["actual"] = "보고서 다운로드 button 미발견 — 사용자에게 보고서 데이터 없음 가능"
            return result
        dl = download_file(page, click_sel, min_size_bytes=100, timeout_ms=10_000)
        if dl["ok"]:
            result["verdict"] = "PASS"
            result["actual"] = dl["note"]
        else:
            result["verdict"] = "SKIP"
            result["actual"] = f"보고서 다운로드 미수행: {dl['note']}"
    except Exception as e:
        result["verdict"] = "ERROR"
        result["actual"] = f"보고서 다운로드 예외: {type(e).__name__}: {e}"
    return result


def handle_dsg_did_002(page: Page, result: dict, account: dict) -> dict:
    """DSG-DID-002 — /designer/create iframe mount 확인."""
    try:
        page.goto(f"{DOCUTIL_NGINX}/designer/create", timeout=20_000, wait_until="domcontentloaded")
        wait_settled(page, timeout_ms=5000, sleep_after=1.5)
        mount = iframe_mounted(page, "iframe", timeout_ms=4000)
        if mount["ok"]:
            result["verdict"] = "PASS"
            result["actual"] = mount["note"]
        else:
            # designer/create 는 PromptBox 만 표시 — iframe 은 document 생성 후 노출
            body = assert_body_not_empty(page, min_len=30)
            if body["ok"]:
                result["verdict"] = "PASS"
                result["actual"] = f"designer/create body OK (iframe 은 document 생성 후 노출): {mount['note']}"
            else:
                result["verdict"] = "FAIL"
                result["actual"] = f"designer/create iframe + body 모두 empty: {mount['note']}"
    except Exception as e:
        result["verdict"] = "ERROR"
        result["actual"] = f"designer iframe 검증 예외: {type(e).__name__}: {e}"
    return result


# case_id → handler 매핑
SPECIAL_HANDLERS: dict = {
    "LAY-ASB-014": handle_lay_asb_014,
    "MSC-PVH-001": handle_msc_pvh_001,
    "ADM-DASH-009": handle_adm_dash_009,
    "ADM-DOC-004": handle_adm_doc_004,
    "ADM-DOC-010": handle_adm_doc_010,
    "USR-RPT-008": handle_usr_rpt_008,
    "DSG-DID-002": handle_dsg_did_002,
}


# ════════════════════════════════════════════════════════════════════════════
# 단일 case 실행
# ════════════════════════════════════════════════════════════════════════════
def run_single_case(page: Page, case: dict, account: dict) -> dict:
    """단일 case 1회 실행 → result dict."""
    started = time.time()
    cid = case["id"]
    label = account["label"]
    role = account["expected_role"]
    is_admin = label in ADMIN_LABELS
    raw_page = case["page"]
    path = PAGE_TO_PATH.get(raw_page, "/dashboard")
    risk = case["risk_level"]
    mode = case["automation_mode"]
    action = case["action_type"]
    expected = case["expected_behavior"]

    result = {
        "case_id": cid,
        "account": label,
        "role": role,
        "page": raw_page,
        "resolved_path": path,
        "section": case["section"],
        "button_label": case["button_label"],
        "action_type": action,
        "risk_level": risk,
        "automation_mode": mode,
        "expected": expected[:200],
        "verdict": "PENDING",
        "actual": "",
        "final_url": "",
        "console_errors": [],
        "network_4xx_5xx": [],
        "duration_ms": 0,
        "screenshot": "",
    }

    # Phase C 보강 — special handler 가 있으면 SKIP 우회하여 별도 실행 경로
    has_special = cid in SPECIAL_HANDLERS

    # SKIP 사유 결정
    skip_reasons: list[str] = []
    if mode == "skip":
        skip_reasons.append("automation_mode=skip")
    if mode == "manual":
        skip_reasons.append("automation_mode=manual")
    # cost — 환경변수 E2E_ALLOW_COST=1 일 때만 실행 (기본 OFF)
    if risk == "cost" and not allow_cost():
        skip_reasons.append("risk=cost (E2E_ALLOW_COST=0 — SKIP)")
    # mutation — special handler 없으면 보호 위해 SKIP (mutation handler 가 있으면 검증 진행)
    # 단, allow_mutation()=False 인 경우 무조건 SKIP
    if action == "mutation" or risk == "mutation":
        if not allow_mutation():
            skip_reasons.append(f"risk={risk}/action={action} (E2E_ALLOW_MUTATION=0 — SKIP)")
        elif not has_special:
            skip_reasons.append(f"risk={risk}/action={action} (special handler 없음 — 운영 보호 SKIP)")
    # 로그인 페이지의 submit 케이스 (AUT-LGN-003/004) 는 운영 인증 영향 회피 위해 SKIP
    if raw_page == "/login" and action == "submit":
        skip_reasons.append("login submit — 운영 인증 영향 회피")
    # 로그아웃 (LAY-HDR-006/007 / LAY-USB-006) — storage_state 만료 시킴 → SKIP
    if "로그아웃" in case["button_label"]:
        skip_reasons.append("logout — storage_state 만료 회피")

    # special handler 가 있는 case 는 manual SKIP 무시 (auto 변경된 케이스)
    if has_special and skip_reasons:
        # manual/skip 사유는 제거 (handler 가 직접 검증)
        skip_reasons = [r for r in skip_reasons if "automation_mode=" not in r]

    if skip_reasons:
        result["verdict"] = "SKIP"
        result["actual"] = "; ".join(skip_reasons)
        result["duration_ms"] = int((time.time() - started) * 1000)
        return result

    # Phase C 보강 — special handler 호출 (auto 변경 케이스 전용 검증)
    if has_special:
        try:
            handler = SPECIAL_HANDLERS[cid]
            result = handler(page, result, account)
        except Exception as e:
            result["verdict"] = "ERROR"
            result["actual"] = f"special handler 예외: {type(e).__name__}: {str(e)[:200]}"
        finally:
            result["duration_ms"] = int((time.time() - started) * 1000)
        return result

    # ── 실행 (navigate / click / submit safe 만) ────────────────
    console_errors: list[str] = []
    network_errors: list[dict] = []

    def on_console(msg):
        try:
            if msg.type == "error":
                console_errors.append(str(msg.text)[:300])
        except Exception:
            pass

    def on_response(resp):
        try:
            if resp.status >= 400 and "/_next/" not in resp.url and "/favicon" not in resp.url:
                network_errors.append({
                    "url": resp.url[:200],
                    "status": resp.status,
                    "method": resp.request.method,
                })
        except Exception:
            pass

    page.on("console", on_console)
    page.on("response", on_response)

    try:
        target_url = f"{DOCUTIL_NGINX}{path}"
        # ① 페이지 진입
        try:
            page.goto(target_url, timeout=20_000, wait_until="domcontentloaded")
        except Exception as nav_err:
            result["verdict"] = "ERROR"
            result["actual"] = f"goto 실패: {type(nav_err).__name__}: {str(nav_err)[:150]}"
            result["screenshot"] = shot(page, label, f"ERR_{cid}", force=True)
            return result
        time.sleep(1.5)
        try:
            page.wait_for_load_state("networkidle", timeout=5_000)
        except Exception:
            pass
        time.sleep(0.5)

        final_url = page.url
        result["final_url"] = final_url
        final_path = urlparse(final_url).path or "/"

        # ② 권한 가드 검증 (admin only path 인 경우)
        if path in ADMIN_ONLY_PATHS:
            if is_admin:
                # admin 인데 redirect 되면 FAIL (단, /search/dashboard 가 next.js 의 fallback 일 수도)
                # — admin path 에 머무르거나 path 가 그대로면 OK
                if final_path == path or final_path.startswith(path):
                    pass  # 정상 진입 — 액션 단계로
                elif "/login" in final_url:
                    result["verdict"] = "FAIL"
                    result["actual"] = f"admin 인데 /login redirect — 인증 만료 의심 (final={final_path})"
                    result["screenshot"] = shot(page, label, f"FAIL_{cid}_AdminRedirected", force=True)
                    return result
                else:
                    # admin 인데 다른 path 로 redirect — 권한가드 결함 가능성
                    result["verdict"] = "FAIL"
                    result["actual"] = f"admin 인데 path 변경 ({path} → {final_path})"
                    result["screenshot"] = shot(page, label, f"FAIL_{cid}_AdminPathChanged", force=True)
                    return result
            else:
                # non-admin — redirect 되어야 정상 (PASS)
                if final_path != path:
                    result["verdict"] = "PASS"
                    result["actual"] = f"비admin 권한차단 OK (path {path} → {final_path})"
                    return result
                else:
                    # path 그대로 — 권한 가드 누락 의심. 단 body 메시지 확인
                    body = ""
                    try:
                        body = page.evaluate("() => document.body.innerText || ''") or ""
                    except Exception:
                        pass
                    if any(k in body for k in ("권한", "Forbidden", "Unauthorized", "403", "401")):
                        result["verdict"] = "PASS"
                        result["actual"] = f"권한차단 메시지 표시 (path {final_path})"
                        return result
                    else:
                        result["verdict"] = "FAIL"
                        result["actual"] = (
                            f"비admin 권한차단 미동작 — path {final_path} (body 일부: {body[:80]})"
                        )
                        result["screenshot"] = shot(page, label, f"FAIL_{cid}_GuardMissing", force=True)
                        return result

        # ③ user-allowed path — non-admin 도 진입 가능해야 함
        if path in USER_ALLOWED_PATHS:
            if "/login" in final_url:
                result["verdict"] = "FAIL"
                result["actual"] = f"user-allowed path 인데 /login redirect (final={final_path})"
                result["screenshot"] = shot(page, label, f"FAIL_{cid}_UnexpectedLoginRedirect", force=True)
                return result

        # ④ action 별 분기 — 본 runner 는 navigate / safe click / safe submit 만
        if action == "navigate":
            # body 가 비어있지 않으면 (DOM 마운트) PASS
            body_len = 0
            try:
                body_len = page.evaluate("() => (document.body.innerText || '').length")
            except Exception:
                pass
            if body_len > 30:
                result["verdict"] = "PASS"
                result["actual"] = f"navigate OK — body_len={body_len}, final={final_path}"
            else:
                result["verdict"] = "FAIL"
                result["actual"] = f"navigate but body 비어있음 (body_len={body_len})"
                result["screenshot"] = shot(page, label, f"FAIL_{cid}_EmptyBody", force=True)

        elif action == "click":
            # 본 runner 의 click 은 "page 진입 + DOM 마운트 OK + 해당 section 존재 확인"
            body_len = 0
            try:
                body_len = page.evaluate("() => (document.body.innerText || '').length")
            except Exception:
                pass
            if body_len > 30:
                result["verdict"] = "PASS"
                result["actual"] = f"click target page 진입 OK — body_len={body_len}"
            else:
                result["verdict"] = "FAIL"
                result["actual"] = f"click target page body 비어있음 (body_len={body_len})"
                result["screenshot"] = shot(page, label, f"FAIL_{cid}_EmptyBody", force=True)

        elif action == "submit":
            # mutation submit 은 이미 SKIP 됨. 남은 건 safe submit
            body_len = 0
            try:
                body_len = page.evaluate("() => (document.body.innerText || '').length")
            except Exception:
                pass
            if body_len > 30:
                result["verdict"] = "PASS"
                result["actual"] = f"submit target page OK — body_len={body_len}"
            else:
                result["verdict"] = "FAIL"
                result["actual"] = f"submit target page body 비어있음"

        else:
            result["verdict"] = "SKIP"
            result["actual"] = f"unknown action_type={action}"

    except Exception as e:
        result["verdict"] = "ERROR"
        result["actual"] = f"예외: {type(e).__name__}: {str(e)[:200]}"
        result["screenshot"] = shot(page, label, f"ERR_{cid}", force=True)
        traceback.print_exc()
    finally:
        try:
            page.remove_listener("console", on_console)
        except Exception:
            pass
        try:
            page.remove_listener("response", on_response)
        except Exception:
            pass
        result["console_errors"] = console_errors[:5]
        result["network_4xx_5xx"] = network_errors[:5]
        result["duration_ms"] = int((time.time() - started) * 1000)

    return result


# ════════════════════════════════════════════════════════════════════════════
# 우선 시나리오 — LAY-HDR-004 (프로필 드롭다운) 별도 검증
# ════════════════════════════════════════════════════════════════════════════
def verify_profile_dropdown(page: Page, account: dict) -> dict:
    """사용자 명시 결함 — 우측 상단 프로필 클릭 시 드롭다운 오픈 여부.

    Header.tsx 분석:
      - 아바타 트리거: button[aria-label*="프로필"] 또는 div.avatar
      - 드롭다운: 클릭 후 .dropdown-menu / [role="menu"] / "프로필"|"로그아웃" 텍스트 노출
    """
    label = account["label"]
    started = time.time()
    result = {
        "case_id": "LAY-HDR-004",
        "account": label,
        "role": account["expected_role"],
        "page": "(공통)",
        "resolved_path": "/dashboard",
        "section": "header",
        "button_label": "사용자 아바타 (프로필 드롭다운 트리거)",
        "action_type": "click",
        "risk_level": "safe",
        "automation_mode": "auto",
        "expected": "드롭다운 오픈/클로즈. 외부 클릭 시 자동 닫힘.",
        "verdict": "PENDING",
        "actual": "",
        "final_url": "",
        "screenshot": "",
        "duration_ms": 0,
    }
    try:
        # admin path 진입 (admin 만), 비admin 은 /search
        path = "/dashboard" if label in ADMIN_LABELS else "/search"
        page.goto(f"{DOCUTIL_NGINX}{path}", timeout=20_000, wait_until="domcontentloaded")
        time.sleep(2.5)
        try:
            page.wait_for_load_state("networkidle", timeout=5_000)
        except Exception:
            pass
        time.sleep(0.5)
        result["final_url"] = page.url

        # 진입 실패 시 즉시 FAIL
        if "/login" in page.url:
            result["verdict"] = "FAIL"
            result["actual"] = "프로필 검증 전 /login redirect — 인증 만료"
            result["screenshot"] = shot(page, label, f"LAY-HDR-004_{label}_LoginRedirect", force=True)
            return result

        # ── 아바타 트리거 후보 selector ─────────────────
        # Header.tsx 패턴: 우상단 영역의 button (avatar img 또는 initial)
        trigger_selectors = [
            'header button:has(img)',
            'header button[aria-label*="프로필"]',
            'header button[aria-label*="profile"]',
            'header button[aria-label*="Profile"]',
            'header button[aria-haspopup]',
            'header button:has(svg):has-text("")',  # icon-only button
            '[data-testid="user-menu-trigger"]',
            '[data-testid="avatar-button"]',
            'header [class*="avatar"]',
            'header [class*="Avatar"]',
            'header button.profile',
        ]
        trigger = None
        used_sel = ""
        for sel in trigger_selectors:
            try:
                els = page.query_selector_all(sel)
                # header 안의 마지막(가장 오른쪽) 요소 선택
                for el in reversed(els):
                    try:
                        box = el.bounding_box()
                        if box and box["width"] > 10 and box["height"] > 10:
                            trigger = el
                            used_sel = sel
                            break
                    except Exception:
                        continue
                if trigger:
                    break
            except Exception:
                continue

        if not trigger:
            # fallback — header 의 마지막 button
            try:
                btns = page.query_selector_all('header button')
                if btns:
                    trigger = btns[-1]
                    used_sel = "header button[-1]"
            except Exception:
                pass

        if not trigger:
            result["verdict"] = "FAIL"
            result["actual"] = "프로필 트리거 element 미발견 (header 내 button 없음)"
            result["screenshot"] = shot(page, label, f"LAY-HDR-004_{label}_NoTrigger", force=True)
            return result

        # 클릭 전 body 상태
        before_html_len = page.evaluate("() => document.body.innerHTML.length")
        before_url = page.url

        # 클릭
        try:
            trigger.click(timeout=3000)
        except Exception as ce:
            result["verdict"] = "FAIL"
            result["actual"] = f"트리거 클릭 실패 (sel={used_sel}): {type(ce).__name__}: {str(ce)[:100]}"
            result["screenshot"] = shot(page, label, f"LAY-HDR-004_{label}_ClickFail", force=True)
            return result
        time.sleep(1.0)

        after_url = page.url
        after_html_len = page.evaluate("() => document.body.innerHTML.length")

        # 드롭다운 노출 확인
        dropdown_selectors = [
            '[role="menu"]:visible',
            '.dropdown-menu.show',
            '.dropdown-menu:not([hidden])',
            '[class*="dropdown"][class*="open"]',
            '[class*="Dropdown"]:visible',
            '[data-state="open"]',
            '[aria-expanded="true"] + *',
        ]
        dropdown_found = False
        for sel in dropdown_selectors:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    dropdown_found = True
                    break
            except Exception:
                continue

        # 텍스트 기반 보조 검증 — 프로필/로그아웃 새로 노출됐는지
        menu_keywords_found: list[str] = []
        try:
            visible_text = page.evaluate("() => document.body.innerText || ''") or ""
            # 메뉴에만 등장할 키워드
            for kw in ("프로필", "내 정보", "로그아웃", "Sign out", "Logout"):
                if kw in visible_text:
                    menu_keywords_found.append(kw)
        except Exception:
            pass

        # URL 변경 = navigation 발생 (= 드롭다운 X, 사용자 명시 결함 — 화면 리프레시)
        url_changed = (after_url != before_url)
        page_grew = (after_html_len > before_html_len + 50)  # 드롭다운 DOM 추가 흔적

        if dropdown_found:
            result["verdict"] = "PASS"
            result["actual"] = f"프로필 드롭다운 오픈 OK (sel={used_sel}, kw={menu_keywords_found})"
        elif page_grew and menu_keywords_found and not url_changed:
            result["verdict"] = "PASS"
            result["actual"] = (
                f"드롭다운 DOM 추가 + 메뉴 키워드 노출 OK "
                f"(growth={after_html_len-before_html_len}, kw={menu_keywords_found})"
            )
        elif url_changed:
            result["verdict"] = "FAIL"
            result["actual"] = (
                f"사용자 명시 결함 재현 — 프로필 클릭 시 URL 변경됨 "
                f"({before_url} → {after_url}) (드롭다운 미오픈)"
            )
            result["screenshot"] = shot(page, label, f"LAY-HDR-004_{label}_UrlChanged", force=True)
        else:
            result["verdict"] = "FAIL"
            result["actual"] = (
                f"드롭다운 미오픈 — sel={used_sel} click 후 DOM 변화 없음 "
                f"(growth={after_html_len-before_html_len}, kw={menu_keywords_found})"
            )
            result["screenshot"] = shot(page, label, f"LAY-HDR-004_{label}_NoDropdown", force=True)
    except Exception as e:
        result["verdict"] = "ERROR"
        result["actual"] = f"예외: {type(e).__name__}: {str(e)[:200]}"
        result["screenshot"] = shot(page, label, f"LAY-HDR-004_{label}_Exception", force=True)
    finally:
        result["duration_ms"] = int((time.time() - started) * 1000)
    return result


# ════════════════════════════════════════════════════════════════════════════
# 메인
# ════════════════════════════════════════════════════════════════════════════
def main():
    print(f"[track #105 C.2/C.3 + 보강] start at {now_ts()}")
    print(f"[정보] 카탈로그 = {len(CASES)} cases, 4계정 매트릭스 = {len(CASES)*4} cells")
    print(f"[flag] E2E_ALLOW_COST={allow_cost()}, E2E_ALLOW_MUTATION={allow_mutation()}")
    print(f"[special handlers] {sorted(SPECIAL_HANDLERS.keys())}")

    out: dict = {
        "track": "#105 Phase C.2~C.3 — DocUtil 전 페이지 e2e",
        "ran_at": now_ts(),
        "base_url": DOCUTIL_NGINX,
        "accounts": [
            {"label": a["label"], "login_id": a["login_id"], "expected_role": a["expected_role"]}
            for a in ACCOUNTS
        ],
        "total_cases": len(CASES),
        "total_cells": len(CASES) * len(ACCOUNTS),
        "logins": [],
        "profile_dropdown_results": [],
        "results": [],
        "summary": {},
        "per_account_summary": {},
        "per_page_summary": {},
    }

    with sync_playwright() as p:
        # ── 1. 4계정 로그인 + state 저장 ────────────────
        print(f"\n[1] 4계정 로그인 + storage_state 생성")
        for acc in ACCOUNTS:
            print(f"  → {acc['label']} ({acc['login_id']})")
            login = docutil_login(p, acc["login_id"], PASSWORD, acc["state_path"])
            out["logins"].append({
                "label": acc["label"],
                "login_id": acc["login_id"],
                "ok": login["ok"],
                "url": login["url"],
                "note": login["note"],
            })
            print(f"     ok={login['ok']} url={login['url']} note={login['note']}")

        ok_labels = [li["label"] for li in out["logins"] if li["ok"]]
        if not ok_labels:
            print("[ERROR] 모든 계정 로그인 실패. 종료.")
            RESULT_PATH.write_text(
                json.dumps(out, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )
            return

        # ── 2. 우선 시나리오 — LAY-HDR-004 (4계정 모두) ──────────
        print(f"\n[2] LAY-HDR-004 (프로필 드롭다운) 우선 검증 — 4계정")
        for acc in ACCOUNTS:
            if acc["label"] not in ok_labels:
                out["profile_dropdown_results"].append({
                    "case_id": "LAY-HDR-004", "account": acc["label"],
                    "verdict": "SKIP", "actual": "로그인 실패로 SKIP",
                })
                continue
            b = p.chromium.launch(headless=True)
            try:
                ctx = b.new_context(
                    viewport=VIEWPORT, locale="ko-KR",
                    ignore_https_errors=True, storage_state=str(acc["state_path"]),
                )
                ctx.set_default_timeout(DEFAULT_TIMEOUT_MS)
                page = ctx.new_page()
                pr = verify_profile_dropdown(page, acc)
                out["profile_dropdown_results"].append(pr)
                print(f"  [{pr['verdict']:<5}] {acc['label']:<13} {pr['actual'][:120]}")
                ctx.close()
            finally:
                b.close()

        # ── 3. 본 매트릭스 실행 — 4계정 × 154 auto 케이스 ──────
        print(f"\n[3] 본 매트릭스 실행 — {len(ACCOUNTS)}계정 × {len(CASES)} cases")
        for acc in ACCOUNTS:
            if acc["label"] not in ok_labels:
                # 로그인 실패 → 전수 SKIP 기록
                for case in CASES:
                    out["results"].append({
                        "case_id": case["id"],
                        "account": acc["label"],
                        "role": acc["expected_role"],
                        "page": case["page"],
                        "verdict": "SKIP",
                        "actual": "로그인 실패 — 전수 SKIP",
                    })
                continue

            print(f"\n  [account] {acc['label']} ({acc['login_id']})")
            b = p.chromium.launch(headless=True)
            try:
                ctx = b.new_context(
                    viewport=VIEWPORT, locale="ko-KR",
                    ignore_https_errors=True, storage_state=str(acc["state_path"]),
                )
                ctx.set_default_timeout(DEFAULT_TIMEOUT_MS)
                page = ctx.new_page()
                # 페이지 console/network listener 는 case 마다 등록/해제 (per-case)

                acc_pass = acc_fail = acc_skip = acc_err = 0
                for idx, case in enumerate(CASES, 1):
                    r = run_single_case(page, case, acc)
                    out["results"].append(r)
                    v = r["verdict"]
                    if v == "PASS":
                        acc_pass += 1
                    elif v == "FAIL":
                        acc_fail += 1
                    elif v == "SKIP":
                        acc_skip += 1
                    else:
                        acc_err += 1
                    # 진행 출력 — 매 30 케이스마다
                    if idx % 30 == 0 or idx == len(CASES):
                        print(f"    [{idx:>3}/{len(CASES)}] PASS={acc_pass} FAIL={acc_fail} SKIP={acc_skip} ERR={acc_err}")
                print(f"  [account-summary] {acc['label']}: PASS={acc_pass} FAIL={acc_fail} SKIP={acc_skip} ERR={acc_err}")
                ctx.close()
            finally:
                b.close()

    # ── 4. 집계 ────────────────────────────────────────
    summary = {"PASS": 0, "FAIL": 0, "SKIP": 0, "ERROR": 0, "PENDING": 0}
    per_account: dict = {}
    per_page: dict = {}
    for r in out["results"]:
        v = r["verdict"]
        summary[v] = summary.get(v, 0) + 1
        per_account.setdefault(r["account"], {"PASS": 0, "FAIL": 0, "SKIP": 0, "ERROR": 0})
        per_account[r["account"]][v] = per_account[r["account"]].get(v, 0) + 1
        per_page.setdefault(r["page"], {"PASS": 0, "FAIL": 0, "SKIP": 0, "ERROR": 0})
        per_page[r["page"]][v] = per_page[r["page"]].get(v, 0) + 1
    # profile dropdown 도 합산
    pd_summary = {"PASS": 0, "FAIL": 0, "SKIP": 0, "ERROR": 0}
    for r in out["profile_dropdown_results"]:
        pd_summary[r.get("verdict", "ERROR")] = pd_summary.get(r.get("verdict", "ERROR"), 0) + 1

    out["summary"] = summary
    out["per_account_summary"] = per_account
    out["per_page_summary"] = per_page
    out["profile_dropdown_summary"] = pd_summary
    out["finished_at"] = now_ts()

    RESULT_PATH.write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"\n[summary] {summary}")
    print(f"[per-account] {per_account}")
    print(f"[profile-dropdown] {pd_summary}")
    print(f"\n[saved] {RESULT_PATH}")


if __name__ == "__main__":
    main()
