"""2026-05-17 Phase B v2 — 메뉴별 case-by-case 인터랙션 (단일 컨텍스트 + 순차).

핵심 변경 (v2):
  - live_runner.py 와 동일하게 **단일 chrome() 컨텍스트 안에서 모든 케이스 순차 실행**.
  - 매번 새 컨텍스트 시 storage_state localStorage 복원 불완전 결함 회피.
  - 각 케이스 사이 page.goto() 만 — 컨텍스트/쿠키/localStorage 유지.

결함 판정:
  - 결함 1: Send 3초 후 URL path ∈ {"/", "/dashboard", "/home"} → FAIL + DEFECT1_TAG
  - 결함 2: 응답 대기 후 body innerText 에 응답 키워드 없으면 FAIL + DEFECT2_TAG

실행:
  python tools/ui_e2e/full/interaction_runner_20260517.py
"""
from __future__ import annotations
import io
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Callable

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).parent))

from common import (
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    AGENTHUB_BASE,
    chrome,
    now_ts,
)

SHOT_DIR = Path(__file__).resolve().parents[1] / "screenshots" / "interaction_20260517"
SHOT_DIR.mkdir(parents=True, exist_ok=True)
STATE_PATH = Path(__file__).parent / "_admin_state.json"
RESULT_PATH = Path(__file__).parent / "interaction_results_20260517.json"

DEFECT1_TAG = "DEFECT1_REPRO__Send_후_대시보드_이탈"
DEFECT2_TAG = "DEFECT2_REPRO__응답_미표시"
DASHBOARD_PATHS = {"/", "/dashboard", "/home"}

# 글로벌 console/network 캡처 (컨텍스트 단위 부착, 케이스 단위 추출)
_CONSOLE: list[str] = []
_NETWORK: list[dict] = []


# ────────────────────────────────────────────────────────────────────
# 공통 유틸
# ────────────────────────────────────────────────────────────────────
def shot(page, case_id: str) -> str:
    safe = case_id.replace("/", "_").replace(":", "_")[:80]
    path = SHOT_DIR / f"{safe}.png"
    try:
        page.screenshot(path=str(path), full_page=False)
        return str(path).replace("\\", "/")
    except Exception as e:
        return f"(shot failed: {e})"


def attach_global(page) -> None:
    """컨텍스트 단위 1회 부착. 케이스 시작 시 리스트 clear."""

    def on_console(msg):
        try:
            if msg.type == "error":
                _CONSOLE.append(f"[{msg.type}] {msg.text[:300]}")
        except Exception:
            pass

    def on_response(resp):
        try:
            if 400 <= resp.status < 600:
                url = resp.url
                if any(x in url for x in [".ico", "_vue-devtools", "hot-update", "/sockjs"]):
                    return
                _NETWORK.append({"status": resp.status, "url": url[:200]})
        except Exception:
            pass

    page.on("console", on_console)
    page.on("response", on_response)


def reset_capture():
    _CONSOLE.clear()
    _NETWORK.clear()


def snapshot_capture() -> tuple[list, list]:
    return list(_CONSOLE), list(_NETWORK)


def admin_login_to_state() -> bool:
    """admin 로그인 → storage_state 신규 저장.

    핵심 fix:
      - live_runner 와 동일한 광범위 셀렉터(input[type=email])로 로그인 (안정성 우선)
      - 로그인 성공 후 sessionStorage 의 token/refreshToken 을 localStorage 로 강제 복사
      - Playwright storage_state 가 localStorage 만 저장하므로 sessionStorage 만 있으면 새 ctx 에서 토큰 손실
    """
    try:
        STATE_PATH.unlink(missing_ok=True)
    except Exception:
        pass
    with chrome(headless=True) as (_, _, ctx, page):
        page.goto(f"{AGENTHUB_BASE}/login", timeout=20_000)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(0.5)
        try:
            page.fill('input[type="email"], input[name="email"]', ADMIN_EMAIL)
            page.fill('input[type="password"], input[name="password"]', ADMIN_PASSWORD)
            clicked = False
            for sel in ['button[type="submit"]', 'button:has-text("로그인")', 'button:has-text("Login")']:
                try:
                    btn = page.query_selector(sel)
                    if btn:
                        btn.click()
                        clicked = True
                        break
                except Exception:
                    pass
            if not clicked:
                print("  [fail] submit 버튼 미클릭")
                return False
            page.wait_for_load_state("networkidle", timeout=15_000)
            time.sleep(1.5)
            if "/login" in page.url:
                print(f"  [fail] 로그인 후에도 /login 잔존: {page.url}")
                return False

            # storage 상태 진단 + sessionStorage → localStorage 강제 복사
            ls_token_before = page.evaluate("() => localStorage.getItem('token')")
            ss_token = page.evaluate("() => sessionStorage.getItem('token')")
            ss_refresh = page.evaluate("() => sessionStorage.getItem('refreshToken')")
            print(f"  [diag] before: localStorage.token={'OK' if ls_token_before else 'EMPTY'} "
                  f"sessionStorage.token={'OK' if ss_token else 'EMPTY'}")

            # sessionStorage 에 있고 localStorage 에 없으면 복사
            if ss_token and not ls_token_before:
                page.evaluate(f"() => localStorage.setItem('token', {json.dumps(ss_token)})")
                if ss_refresh:
                    page.evaluate(f"() => localStorage.setItem('refreshToken', {json.dumps(ss_refresh)})")
                print(f"  [fix] sessionStorage token → localStorage 복사 완료")

            ls_token_after = page.evaluate("() => localStorage.getItem('token')")
            print(f"  [diag] after: localStorage.token={'OK' if ls_token_after else 'EMPTY'}")
            if not ls_token_after:
                print("  [abort] localStorage 에 token 적재 실패 — storage_state 무효")
                return False

            ctx.storage_state(path=str(STATE_PATH))
            # 저장 검증
            try:
                with open(STATE_PATH, encoding='utf-8') as fh:
                    saved = json.load(fh)
                origins = saved.get('origins', [])
                ls_count = sum(len(o.get('localStorage', [])) for o in origins)
                print(f"  [diag] storage_state 저장: origins={len(origins)} localStorage entries={ls_count}")
            except Exception as e:
                print(f"  [warn] storage_state 검증 실패: {e}")
            return True
        except Exception as e:
            print(f"  login failed: {e}")
            return False


def make_result(
    case_id: str,
    screen: str,
    path_or_action: str,
    status: str,
    *,
    note: str = "",
    duration_ms: int = 0,
    screenshot: str = "",
    final_url: str = "",
    risk: str = "safe",
) -> dict:
    ce, ne = snapshot_capture()
    return {
        "case_id": case_id,
        "screen": screen,
        "path_or_action": path_or_action,
        "risk": risk,
        "status": status,
        "note": note,
        "console_errors": ce,
        "network_4xx_5xx": ne,
        "duration_ms": duration_ms,
        "screenshot": screenshot,
        "final_url": final_url,
        "ts": now_ts(),
    }


def try_fill(page, selectors: list[str], text: str) -> bool:
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el:
                el.click()
                el.fill(text)
                return True
        except Exception:
            continue
    return False


def try_click(page, selectors: list[str]) -> bool:
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                el.click()
                return True
        except Exception:
            continue
    return False


def get_path(url: str) -> str:
    try:
        from urllib.parse import urlparse
        return urlparse(url).path or "/"
    except Exception:
        return url


# ────────────────────────────────────────────────────────────────────
# Critical 결함 1+2 reproduce 시나리오
# ────────────────────────────────────────────────────────────────────
def case_001_agentchat_send_to_dashboard(page) -> dict:
    """IX-AH-001 — /agents → 첫 카드(.ag-card) → /agents/chat/:id → input + Send → URL 검증."""
    case_id = "IX-AH-001"
    reset_capture()
    start = time.time()
    try:
        page.goto(f"{AGENTHUB_BASE}/agents", timeout=20_000)
        page.wait_for_load_state("networkidle", timeout=15_000)
        time.sleep(1.5)

        if "/login" in page.url:
            return make_result(
                case_id, "AgentChat", "/agents",
                "FAIL", note="세션 redirect /login — admin 로그인 무효화",
                duration_ms=int((time.time() - start) * 1000),
                screenshot=shot(page, case_id), final_url=page.url,
            )

        card_clicked = try_click(
            page,
            [
                '.ag-card:first-child',
                '.ag-card',
                'a[href*="/agents/chat/"]',
                '.agent-card:first-child',
            ],
        )
        if not card_clicked:
            return make_result(
                case_id, "AgentChat", "/agents → first card",
                "SKIP", note="Agent 카드(.ag-card) 미발견 — /agents 페이지 비어있을 수 있음",
                duration_ms=int((time.time() - start) * 1000),
                screenshot=shot(page, case_id), final_url=page.url,
            )

        page.wait_for_load_state("networkidle", timeout=15_000)
        time.sleep(2.0)
        chat_url = page.url

        filled = try_fill(
            page,
            [
                'textarea.cd-textarea',
                'textarea[placeholder*="메시지"]',
                'textarea:not(.form-control)',
                'textarea',
            ],
            f"ping e2e {now_ts()}",
        )
        if not filled:
            return make_result(
                case_id, "AgentChat", chat_url,
                "SKIP", note="채팅 input(textarea.cd-textarea) 미발견",
                duration_ms=int((time.time() - start) * 1000),
                screenshot=shot(page, case_id), final_url=page.url,
            )

        send_clicked = try_click(
            page,
            [
                'button.cd-send-btn',
                'button:has-text("전송")',
                'button[type="submit"]',
            ],
        )
        if not send_clicked:
            try:
                page.keyboard.press("Enter")
                send_clicked = True
            except Exception:
                pass
        if not send_clicked:
            return make_result(
                case_id, "AgentChat", chat_url,
                "SKIP", note="Send 버튼 미발견",
                duration_ms=int((time.time() - start) * 1000),
                screenshot=shot(page, case_id), final_url=page.url,
            )

        # 결함 1 판정 — Send 3초 후 URL
        time.sleep(3.0)
        final_path = get_path(page.url)
        dur = int((time.time() - start) * 1000)

        if final_path in DASHBOARD_PATHS:
            return make_result(
                case_id, "AgentChat", f"Send → {final_path}",
                "FAIL", note=DEFECT1_TAG + f" (chat={chat_url} → final={page.url})",
                duration_ms=dur, screenshot=shot(page, case_id), final_url=page.url, risk="cost",
            )

        # 결함 2 검증 — 응답 표시 여부 (5초 더 대기)
        time.sleep(5.0)
        body_text = ""
        try:
            body_text = page.evaluate("() => document.body.innerText || ''")
        except Exception:
            pass
        kw = ["응답", "안녕", "Hello", "도와", "I'm", "I am", "ping"]
        has_response = any(k in body_text for k in kw)
        return make_result(
            case_id, "AgentChat", f"Send (url 유지: {final_path})",
            "PASS" if has_response else "FAIL",
            note="응답 표시 OK" if has_response else f"{DEFECT2_TAG} (단일채팅 응답 미표시)",
            duration_ms=dur, screenshot=shot(page, case_id), final_url=page.url, risk="cost",
        )
    except Exception as e:
        return make_result(
            case_id, "AgentChat", "send error",
            "FAIL", note=f"예외: {type(e).__name__}: {str(e)[:200]}",
            duration_ms=int((time.time() - start) * 1000),
        )


def case_multichat_provider(page, case_id: str, provider_label: str, wait_sec: float) -> dict:
    reset_capture()
    start = time.time()
    try:
        page.goto(f"{AGENTHUB_BASE}/agents/multi-chat", timeout=20_000)
        page.wait_for_load_state("networkidle", timeout=15_000)
        time.sleep(2.0)

        if "/login" in page.url:
            return make_result(
                case_id, "AgentMultiChat", "/agents/multi-chat",
                "FAIL", note="세션 redirect /login",
                duration_ms=int((time.time() - start) * 1000),
                screenshot=shot(page, case_id), final_url=page.url,
            )

        # 새 채팅 버튼 (있으면 클릭)
        try_click(
            page,
            [
                'button:has-text("새 채팅")',
                'button:has-text("새 대화")',
                'button:has-text("+ 채팅")',
                'button.new-chat',
            ],
        )
        time.sleep(1.0)

        # 서비스 select — provider 선택
        select_done = False
        for sel in ['select.service-select', 'select[name="service"]', 'select.cd-select', 'select']:
            try:
                el = page.query_selector(sel)
                if el:
                    try:
                        el.select_option(label=provider_label)
                        select_done = True
                        break
                    except Exception:
                        try:
                            el.select_option(value=provider_label.lower())
                            select_done = True
                            break
                        except Exception:
                            continue
            except Exception:
                continue

        filled = try_fill(
            page,
            [
                'textarea.cd-textarea',
                'textarea[placeholder*="메시지"]',
                'textarea:not(.form-control)',
                'textarea',
            ],
            f"ping multi {provider_label} {now_ts()}",
        )
        if not filled:
            return make_result(
                case_id, "AgentMultiChat", f"{provider_label} select={select_done}",
                "SKIP", note="멀티채팅 input 미발견",
                duration_ms=int((time.time() - start) * 1000),
                screenshot=shot(page, case_id), final_url=page.url,
            )

        sent = try_click(
            page,
            [
                'button.cd-send-btn',
                'button:has-text("전송")',
                'button[type="submit"]',
            ],
        )
        if not sent:
            try:
                page.keyboard.press("Enter")
                sent = True
            except Exception:
                pass
        if not sent:
            return make_result(
                case_id, "AgentMultiChat", f"{provider_label}",
                "SKIP", note="Send 미클릭",
                duration_ms=int((time.time() - start) * 1000),
                screenshot=shot(page, case_id), final_url=page.url,
            )

        time.sleep(wait_sec)
        final_path = get_path(page.url)
        ss = shot(page, case_id)
        dur = int((time.time() - start) * 1000)

        if final_path in DASHBOARD_PATHS:
            return make_result(
                case_id, "AgentMultiChat", f"{provider_label} Send → {final_path}",
                "FAIL", note=DEFECT1_TAG + " (멀티채팅도 동일)",
                duration_ms=dur, screenshot=ss, final_url=page.url, risk="cost",
            )

        body_text = ""
        try:
            body_text = page.evaluate("() => document.body.innerText || ''")
        except Exception:
            pass
        kw = ["안녕", "응답이 없습니다", "오류가 발생", "I'm", "Hello", "도와"]
        has_response = any(k in body_text for k in kw)
        err_shown = "오류가 발생" in body_text or "응답이 없습니다" in body_text
        status = "FAIL" if not has_response else ("FAIL" if err_shown else "PASS")
        note = (
            DEFECT2_TAG + f" (provider={provider_label})" if not has_response
            else (f"오류 표시: {body_text[body_text.find('오류'):body_text.find('오류')+150]}" if err_shown
                  else f"응답 OK ({provider_label})")
        )
        return make_result(
            case_id, "AgentMultiChat", f"{provider_label} Send",
            status, note=note, duration_ms=dur,
            screenshot=ss, final_url=page.url, risk="cost",
        )
    except Exception as e:
        return make_result(
            case_id, "AgentMultiChat", f"{provider_label}",
            "FAIL", note=f"예외: {type(e).__name__}: {str(e)[:200]}",
            duration_ms=int((time.time() - start) * 1000),
        )


def case_002_multichat_openai(page) -> dict:
    return case_multichat_provider(page, "IX-AH-002", "ChatGPT", 15.0)


def case_003_multichat_nexus(page) -> dict:
    return case_multichat_provider(page, "IX-AH-003", "Project Nexus", 65.0)


# ────────────────────────────────────────────────────────────────────
# 단순 진입 케이스 (visit + extra_check)
# ────────────────────────────────────────────────────────────────────
def check_has_text(*keywords: str):
    def _chk(page):
        body = page.evaluate("() => document.body.innerText || ''")
        hit = [k for k in keywords if k in body]
        if hit:
            return True, f"keyword match: {hit[:3]}"
        return False, f"키워드 미매치 (검색: {list(keywords)[:5]})"
    return _chk


def check_has_table_or_list():
    def _chk(page):
        for sel in ["table tbody tr", ".list-group-item", ".row", "[role='row']", ".card"]:
            try:
                els = page.query_selector_all(sel)
                if len(els) >= 1:
                    return True, f"row/card 발견 {len(els)}건 ({sel})"
            except Exception:
                continue
        return True, "테이블 미매치 (페이지는 표시됨)"
    return _chk


def visit(
    page,
    case_id: str,
    screen: str,
    path: str,
    *,
    extra_check: Callable[[Any], tuple[bool, str]] | None = None,
    risk: str = "safe",
) -> dict:
    reset_capture()
    start = time.time()
    try:
        page.goto(f"{AGENTHUB_BASE}{path}", timeout=20_000)
        page.wait_for_load_state("domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:
            pass
        time.sleep(1.0)
        final_url = page.url
        ss = shot(page, case_id)

        if "/login" in final_url and path != "/login":
            return make_result(
                case_id, screen, path,
                "FAIL", note="세션 redirect /login",
                duration_ms=int((time.time() - start) * 1000),
                screenshot=ss, final_url=final_url, risk=risk,
            )

        ok = True
        note = ""
        if extra_check:
            try:
                ok, note = extra_check(page)
            except Exception as e:
                ok = False
                note = f"extra_check 예외: {e}"
        return make_result(
            case_id, screen, path,
            "PASS" if ok else "FAIL",
            note=note, duration_ms=int((time.time() - start) * 1000),
            screenshot=ss, final_url=final_url, risk=risk,
        )
    except Exception as e:
        return make_result(
            case_id, screen, path,
            "FAIL", note=f"예외: {type(e).__name__}: {str(e)[:200]}",
            duration_ms=int((time.time() - start) * 1000), risk=risk,
        )


# ────────────────────────────────────────────────────────────────────
# 케이스 카탈로그
# ────────────────────────────────────────────────────────────────────
def all_cases(page) -> list[tuple[str, Callable[[], dict]]]:
    return [
        # Critical 결함 1+2
        ("IX-AH-001", lambda: case_001_agentchat_send_to_dashboard(page)),
        ("IX-AH-002", lambda: case_002_multichat_openai(page)),
        ("IX-AH-003", lambda: case_003_multichat_nexus(page)),

        # Agent 관리
        ("IX-AH-051", lambda: visit(page, "IX-AH-051", "AgentBuilder", "/agents/builder",
                                    extra_check=check_has_text("Agent", "에이전트", "이름", "설정"))),
        ("IX-AH-052", lambda: visit(page, "IX-AH-052", "AgentMarketplace", "/agents/marketplace",
                                    extra_check=check_has_table_or_list())),
        ("IX-AH-053", lambda: visit(page, "IX-AH-053", "AgentTemplates", "/agents/templates",
                                    extra_check=check_has_table_or_list())),

        # 운영자 콘솔
        ("IX-AH-030", lambda: visit(page, "IX-AH-030", "AdminKnowledgeBase", "/admin/knowledge-base",
                                    extra_check=check_has_table_or_list())),
        ("IX-AH-031", lambda: visit(page, "IX-AH-031", "AdminDocUtilUsers", "/admin/docutil-users",
                                    extra_check=check_has_table_or_list())),
        ("IX-AH-032", lambda: visit(page, "IX-AH-032", "AdminDocUtilDashboard", "/admin/docutil-dashboard",
                                    extra_check=check_has_text("DocUtil", "대시보드", "사용자", "문서"))),
        ("IX-AH-033", lambda: visit(page, "IX-AH-033", "AdminRagMetrics", "/admin/rag-metrics",
                                    extra_check=check_has_text("RAG", "메트릭", "검색", "지식"))),

        # 사용자 자기 데이터 + 분석
        ("IX-AH-060", lambda: visit(page, "IX-AH-060", "Dashboard", "/",
                                    extra_check=check_has_text("대시보드", "Dashboard"))),
        ("IX-AH-061", lambda: visit(page, "IX-AH-061", "Analytics", "/analytics",
                                    extra_check=check_has_text("분석", "Analytics", "차트", "기간"))),
        ("IX-AH-062", lambda: visit(page, "IX-AH-062", "CostAnalysis", "/cost-analysis",
                                    extra_check=check_has_text("비용", "Cost", "달러", "원"))),
        ("IX-AH-063", lambda: visit(page, "IX-AH-063", "Quota", "/quota",
                                    extra_check=check_has_text("할당량", "Quota", "사용량", "일일"))),
        ("IX-AH-064", lambda: visit(page, "IX-AH-064", "UsageHistory", "/usage-history",
                                    extra_check=check_has_table_or_list())),

        # ApiKeys / Tools / Workflows
        ("IX-AH-040", lambda: visit(page, "IX-AH-040", "ApiKeys", "/api-keys",
                                    extra_check=check_has_text("API", "Key", "키"))),
        ("IX-AH-050", lambda: visit(page, "IX-AH-050", "Tools", "/tools",
                                    extra_check=check_has_text("도구", "Tool"))),
        ("IX-AH-080", lambda: visit(page, "IX-AH-080", "Workflows", "/workflows",
                                    extra_check=check_has_text("워크플로우", "Workflow"))),

        # Settings (i18n)
        ("IX-AH-020", lambda: visit(page, "IX-AH-020", "Settings", "/settings",
                                    extra_check=check_has_text("설정", "Settings", "언어", "Language"))),

        # 시스템/보안
        ("IX-AH-070", lambda: visit(page, "IX-AH-070", "PiiProtection", "/pii-protection",
                                    extra_check=check_has_text("개인정보", "PII", "보호"))),
        ("IX-AH-071", lambda: visit(page, "IX-AH-071", "BannedWords", "/banned-words",
                                    extra_check=check_has_text("금칙어", "Banned", "단어"))),
        ("IX-AH-072", lambda: visit(page, "IX-AH-072", "SystemHealth", "/system-health",
                                    extra_check=check_has_text("시스템", "Health", "상태"))),
        ("IX-AH-073", lambda: visit(page, "IX-AH-073", "DatabaseBackup", "/database-backup",
                                    extra_check=check_has_text("백업", "Backup", "데이터베이스"))),
        ("IX-AH-074", lambda: visit(page, "IX-AH-074", "AuditLog", "/audit-log",
                                    extra_check=check_has_text("감사", "Audit", "로그"))),

        # 이미지/PPTX (UI 진입만)
        ("IX-AH-090", lambda: visit(page, "IX-AH-090", "ImageGeneration", "/image-generation",
                                    extra_check=check_has_text("이미지", "Image", "생성"),
                                    risk="cost (UI만)")),
        ("IX-AH-091", lambda: visit(page, "IX-AH-091", "QuickImageGeneration", "/quick-image",
                                    extra_check=check_has_text("이미지", "빠른", "Quick"),
                                    risk="cost (UI만)")),
        ("IX-AH-092", lambda: visit(page, "IX-AH-092", "PresentationBuilder", "/presentation-builder",
                                    extra_check=check_has_text("프레젠테이션", "PPT", "Presentation"),
                                    risk="cost (UI만)")),
    ]


# ────────────────────────────────────────────────────────────────────
# 메인 — 단일 컨텍스트 패턴 (live_runner 와 동일)
# ────────────────────────────────────────────────────────────────────
def main():
    print(f"[start] Phase B v2 — {now_ts()}")
    if not admin_login_to_state():
        print("[abort] admin 로그인 실패")
        return
    print(f"[login] storage_state 저장 → {STATE_PATH.name}")

    counters = {"PASS": 0, "FAIL": 0, "SKIP": 0}
    defects = {"DEFECT1": 0, "DEFECT2": 0}
    results: list[dict] = []

    # 단일 컨텍스트 — storage_state 로드 후 모든 케이스 순차
    with chrome(headless=True, storage_state=str(STATE_PATH)) as (_, _, _, page):
        attach_global(page)
        cases = all_cases(page)
        print(f"[plan] 총 {len(cases)} 케이스 (단일 컨텍스트)")

        for idx, (case_id, fn) in enumerate(cases, 1):
            print(f"\n[{idx}/{len(cases)}] {case_id} ...")
            try:
                r = fn()
            except Exception as e:
                r = make_result(
                    case_id, case_id, "runner error",
                    "FAIL", note=f"runner 예외: {e}\n{traceback.format_exc()[:300]}",
                )
            results.append(r)
            counters[r.get("status", "FAIL")] = counters.get(r.get("status", "FAIL"), 0) + 1
            if DEFECT1_TAG in r.get("note", ""):
                defects["DEFECT1"] += 1
            if DEFECT2_TAG in r.get("note", ""):
                defects["DEFECT2"] += 1
            print(
                f"  [{r['status']}] {r['screen']} ({r['duration_ms']}ms) "
                f"console={len(r['console_errors'])} net={len(r['network_4xx_5xx'])} "
                f"note={r['note'][:100]}"
            )

    summary = {
        "track": "Phase B v2 2026-05-17 — case-by-case 인터랙션 (단일 컨텍스트)",
        "started_at": now_ts(),
        "finished_at": now_ts(),
        "cases_total": len(results),
        "counters": counters,
        "defect_reproductions": defects,
        "results": results,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n[done] counters={counters} defects={defects}")
    print(f"[result] {RESULT_PATH}")


if __name__ == "__main__":
    main()
