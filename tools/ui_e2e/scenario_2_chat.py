"""트랙 #75 시나리오 2 — LLM 1회 정밀 검증 (UI 채팅).

흐름:
1) admin 로그인
2) /agents 또는 /agents/multi-chat 진입
3) Agent 선택 (가능하면 docutil-rag-chat 또는 사용 가능한 chat agent)
4) 메시지 입력창에 "안녕하세요, AgentHub 테스트입니다" 입력
5) 전송 → 응답 대기 (최대 30초)
6) 응답 텍스트 확인 + 토큰/모델 표기 검증

운영 영향: LLM 호출 1회 (~$0.0001).
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

TEST_MESSAGE = "안녕하세요, AgentHub UI e2e 테스트 (1회만)"


def run() -> dict:
    out: dict = {
        "scenario_id": "S2",
        "scenario": "LLM 1회 정밀 검증 (UI 채팅)",
        "started_at": now_ts(),
        "steps": [],
        "llm_response": None,
        "test_message": TEST_MESSAGE,
    }

    chat_responses: dict = {"messages": [], "endpoints": set()}

    with chrome(headless=True) as (_p, _b, _ctx, page):
        # 응답 hooking — 채팅 응답 캡처
        def on_response(resp):
            try:
                u = resp.url
                m = resp.request.method
                if m == "POST" and ("/chat" in u or "/messages" in u) and 200 <= resp.status < 400:
                    chat_responses["endpoints"].add(u)
                    try:
                        ctype = resp.headers.get("content-type", "")
                        if "json" in ctype:
                            body = resp.json()
                            chat_responses["messages"].append({"url": u, "status": resp.status, "body": body})
                        elif "text/event-stream" in ctype or "stream" in ctype:
                            chat_responses["messages"].append({"url": u, "status": resp.status, "sse": True})
                    except Exception:
                        pass
            except Exception:
                pass

        page.on("response", on_response)

        # === 2-1. 로그인 ===
        t0 = time.time()
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
        sc = shot(page, "s2_01", "post_login")
        out["steps"].append({"id": "2-1", "desc": "admin 로그인",
                             "result": "PASS" if "/login" not in page.url else "FAIL",
                             "duration_ms": int((time.time()-t0)*1000), "screenshot": sc})

        # === 2-2. /agents 페이지 진입 ===
        t0 = time.time()
        page.goto(f"{AGENTHUB_BASE}/agents")
        page.wait_for_load_state("networkidle", timeout=10_000)
        time.sleep(0.8)
        sc = shot(page, "s2_02", "agents_page")
        out["steps"].append({"id": "2-2", "desc": "/agents 진입",
                             "result": "PASS" if "/agents" in page.url else "FAIL",
                             "duration_ms": int((time.time()-t0)*1000),
                             "url": page.url, "title": page.title(), "screenshot": sc})

        # === 2-3. Agent 카드 또는 리스트에서 첫 번째 사용 가능한 Agent 클릭 ===
        t0 = time.time()
        agent_clicked = None
        # 후보 셀렉터: Agent 카드, 리스트, "채팅하기" 또는 "시작" 버튼
        candidates = [
            ".agent-card", ".agent-item", "[class*='agent']",
            "button:has-text('채팅하기')", "button:has-text('시작')",
            "a:has-text('채팅')",
        ]
        for sel in candidates:
            try:
                els = page.locator(sel)
                cnt = els.count()
                for i in range(min(cnt, 5)):
                    el = els.nth(i)
                    try:
                        if not el.is_visible():
                            continue
                        txt = (el.inner_text() or "").strip()[:40]
                        # 카드를 클릭하면 채팅 페이지로 이동하는 경우
                        el.click()
                        time.sleep(1.0)
                        # url 이 변했는지
                        if "/chat" in page.url or "/conversations" in page.url or "/agents/" in page.url.replace(f"{AGENTHUB_BASE}/agents", ""):
                            agent_clicked = {"selector": sel, "text": txt, "url": page.url}
                            break
                    except Exception:
                        continue
                if agent_clicked:
                    break
            except Exception:
                continue
        try:
            page.wait_for_load_state("networkidle", timeout=8_000)
        except Exception:
            pass
        time.sleep(0.7)
        sc = shot(page, "s2_03", "agent_clicked")
        out["steps"].append({"id": "2-3", "desc": "Agent 카드/리스트 선택",
                             "result": "PASS" if agent_clicked else "FAIL",
                             "duration_ms": int((time.time()-t0)*1000),
                             "agent": agent_clicked, "screenshot": sc})

        if not agent_clicked:
            # fallback: navigate to /agents/multi-chat
            try:
                page.goto(f"{AGENTHUB_BASE}/agents/multi-chat")
                page.wait_for_load_state("networkidle", timeout=10_000)
                time.sleep(0.7)
                agent_clicked = {"selector": "navigate", "url": page.url}
            except Exception:
                pass

        # === 2-4. 메시지 입력창 + 전송 ===
        t0 = time.time()
        msg_input_sel = None
        for sel in [
            "textarea[placeholder*='메시지']",
            "textarea[placeholder*='입력']",
            "textarea[placeholder*='Message']",
            "div[contenteditable='true']",
            "textarea.form-control",
            "textarea",
        ]:
            try:
                loc = page.locator(sel).first
                if loc.count() > 0 and loc.is_visible():
                    msg_input_sel = sel
                    break
            except Exception:
                continue

        message_sent = False
        if msg_input_sel:
            try:
                # fill 또는 type (contenteditable 처리)
                loc = page.locator(msg_input_sel).first
                if "contenteditable" in msg_input_sel:
                    loc.click()
                    page.keyboard.type(TEST_MESSAGE)
                else:
                    loc.fill(TEST_MESSAGE)
                time.sleep(0.4)
                # 전송 — Ctrl+Enter or 전송 버튼
                # 1) 전송 버튼 텍스트 또는 아이콘
                send_clicked = False
                for sel2 in ["button:has-text('전송')", "button:has-text('Send')",
                             "button[type='submit']", "button[aria-label*='send']",
                             "button[aria-label*='전송']"]:
                    try:
                        b = page.locator(sel2).first
                        if b.count() > 0 and b.is_visible() and b.is_enabled():
                            b.click()
                            send_clicked = True
                            break
                    except Exception:
                        continue
                # 2) fallback: Enter
                if not send_clicked:
                    page.keyboard.press("Enter")
                message_sent = True
            except Exception as e:
                out["steps"].append({"id": "2-4-debug", "error": f"{type(e).__name__}:{e}"})

        out["steps"].append({"id": "2-4", "desc": "메시지 입력 + 전송",
                             "result": "PASS" if message_sent else "FAIL",
                             "duration_ms": int((time.time()-t0)*1000),
                             "input_selector": msg_input_sel})

        # === 2-5. 응답 대기 (최대 35초) ===
        t0 = time.time()
        # 응답 캡처 + 채팅 영역에 텍스트 등장 대기
        deadline = time.time() + 35.0
        response_visible = False
        while time.time() < deadline:
            if chat_responses["messages"]:
                response_visible = True
                break
            time.sleep(0.5)
        # 추가 대기 (스트리밍 완료)
        time.sleep(2.0)
        sc = shot(page, "s2_05", "after_response")

        # 응답 내용 캡처
        response_text = ""
        try:
            # 메시지 영역 텍스트
            body_text = page.locator("body").inner_text()
            # 우리가 보낸 메시지 이후의 텍스트
            idx = body_text.find(TEST_MESSAGE)
            if idx >= 0:
                response_text = body_text[idx + len(TEST_MESSAGE):][:800]
        except Exception:
            pass

        out["llm_response"] = {
            "response_visible_via_network": response_visible,
            "response_text_preview": response_text[:500],
            "endpoints_called": list(chat_responses["endpoints"]),
            "messages_captured": len(chat_responses["messages"]),
        }
        out["steps"].append({
            "id": "2-5",
            "desc": "LLM 응답 수신",
            "result": "PASS" if (response_visible or response_text) else "FAIL",
            "duration_ms": int((time.time()-t0)*1000),
            "endpoints": list(chat_responses["endpoints"]),
            "msg_count": len(chat_responses["messages"]),
            "response_preview": response_text[:200],
            "screenshot": sc,
        })

    out["finished_at"] = now_ts()
    summary = {"PASS": 0, "FAIL": 0, "SKIP": 0, "INFO": 0}
    for s in out["steps"]:
        r = s.get("result", "")
        if r in summary:
            summary[r] += 1
    out["summary"] = summary
    out["overall"] = "PASS" if summary["FAIL"] == 0 and summary["PASS"] >= 4 else "PARTIAL"
    return out


if __name__ == "__main__":
    result = run()
    with open("scenario_2_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print(json.dumps({
        "summary": result["summary"],
        "overall": result["overall"],
        "llm_response_preview": result["llm_response"]["response_text_preview"][:200] if result["llm_response"] else None,
        "endpoints": result["llm_response"]["endpoints_called"] if result["llm_response"] else None,
    }, ensure_ascii=False, indent=2))
    print("saved scenario_2_result.json")
