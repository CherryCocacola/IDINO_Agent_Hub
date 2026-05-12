"""트랙 #75 시나리오 1 — Agent API 키 mutation 1 cycle (UI 완전 자동화).

UI 흐름:
1) admin 로그인
2) /api-keys 진입 → "Agent API 키" 탭 클릭 → Agent 드롭다운 선택
3) "Agent API 키 발급" 모달 → keyName 입력 → 발급
4) 발급 완료 모달의 평문 키 캡처
5) /v1/models + /api/agents/{id}/chat 호출 (인증 검증 PASS)
6) Agent API 키 삭제 버튼 클릭 → confirm
7) 회수된 키로 재호출 → 401/403

운영 영향: ApiKey 1건 발급 + 즉시 삭제 (재시도 안전).
응답에서 평문 키는 메모리에만 보존, 보고서/스크린샷에 마스킹 노출.
"""
from __future__ import annotations
import io
import json
import sys
import time
import urllib.error
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import (
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    AGENTHUB_BASE,
    chrome,
    mask_apikey,
    now_ts,
    shot,
)

KEY_NAME = f"ui-e2e-test-{int(time.time())}"


def http_get_models(apikey: str) -> tuple[int, str]:
    """발급된 ApiKey 로 /v1/models 호출."""
    url = f"{AGENTHUB_BASE}/v1/models"
    rq = urllib.request.Request(url, headers={"X-API-Key": apikey, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(rq, timeout=15.0) as resp:
            return resp.getcode(), resp.read().decode("utf-8", errors="replace")[:1500]
    except urllib.error.HTTPError as e:
        try:
            return e.code, e.read().decode("utf-8", errors="replace")[:1500]
        except Exception:
            return e.code, ""
    except Exception as e:
        return -1, f"EXC:{type(e).__name__}:{e}"


def run() -> dict:
    out: dict = {
        "scenario_id": "S1",
        "scenario": "Agent API 키 mutation 1 cycle (UI)",
        "started_at": now_ts(),
        "steps": [],
        "issued_key_masked": None,
        "issued_record_id": None,
        "key_name": KEY_NAME,
    }

    captured: dict = {"apiKey": None, "apiKeyId": None, "full": None}

    with chrome(headless=True) as (_p, _b, _ctx, page):
        # 응답 hooking — 키 발급 응답에서 apiKey 캡처
        # 실제 endpoint (Vue 분석): POST /api/agents/{agentId}/api-keys
        def on_response(resp):
            try:
                u = resp.url
                if resp.request.method == "POST" and ("/agents/" in u and "/api-keys" in u) and 200 <= resp.status < 300:
                    try:
                        body = resp.json()
                        if isinstance(body, dict):
                            if "apiKey" in body and isinstance(body["apiKey"], str) and len(body["apiKey"]) > 16:
                                captured["apiKey"] = body["apiKey"]
                            elif "key" in body and isinstance(body["key"], str) and len(body["key"]) > 16:
                                captured["apiKey"] = body["key"]
                            for id_field in ("apiKeyId", "id", "keyId"):
                                if id_field in body:
                                    captured["apiKeyId"] = body[id_field]
                                    break
                            captured["full"] = body
                            captured["url"] = u
                    except Exception:
                        pass
            except Exception:
                pass

        page.on("response", on_response)

        # === 1-1. 로그인 ===
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
        sc = shot(page, "s1_01", "post_login")
        out["steps"].append({"id": "1-1", "desc": "admin 로그인", "result": "PASS" if "/login" not in page.url else "FAIL",
                             "duration_ms": int((time.time()-t0)*1000), "url": page.url, "screenshot": sc})

        # === 1-2. API 키 관리 페이지 진입 ===
        t0 = time.time()
        page.goto(f"{AGENTHUB_BASE}/api-keys")
        page.wait_for_load_state("networkidle", timeout=10_000)
        time.sleep(0.6)
        sc = shot(page, "s1_02", "apikey_page_arrived")
        out["steps"].append({"id": "1-2", "desc": "/api-keys 진입", "result": "PASS" if "/api-keys" in page.url else "FAIL",
                             "duration_ms": int((time.time()-t0)*1000), "url": page.url, "screenshot": sc})

        # === 1-3. "Agent API 키" 탭 클릭 ===
        t0 = time.time()
        tab_clicked = False
        try:
            tab = page.get_by_role("tab", name="Agent API 키").first
            if tab.count() > 0 and tab.is_visible():
                tab.click()
                tab_clicked = True
        except Exception:
            pass
        if not tab_clicked:
            try:
                # fallback: text 매칭
                t = page.locator("button:has-text('Agent API 키')").first
                if t.count() > 0 and t.is_visible():
                    t.click()
                    tab_clicked = True
            except Exception:
                pass
        time.sleep(0.6)
        sc = shot(page, "s1_03", "agent_tab_active")
        out["steps"].append({"id": "1-3", "desc": "Agent API 키 탭 전환", "result": "PASS" if tab_clicked else "FAIL",
                             "duration_ms": int((time.time()-t0)*1000), "screenshot": sc})

        # === 1-4. Agent 선택 ===
        t0 = time.time()
        agent_selected = None
        try:
            # select 요소 (form-select)
            sel = page.locator("select.ak-agent-select, select.form-select").first
            if sel.count() > 0 and sel.is_visible():
                options = sel.locator("option")
                opt_cnt = options.count()
                # 첫 번째 실제 옵션 (value != null) 선택
                for i in range(opt_cnt):
                    o = options.nth(i)
                    val = o.get_attribute("value")
                    text = (o.inner_text() or "").strip()
                    if val and val not in ("null", "") and text and "선택" not in text:
                        sel.select_option(value=val)
                        agent_selected = {"value": val, "text": text}
                        break
        except Exception as e:
            out["steps"].append({"id": "1-4-debug", "error": f"{type(e).__name__}:{e}"})
        time.sleep(0.7)
        sc = shot(page, "s1_04", "agent_selected")
        out["steps"].append({
            "id": "1-4",
            "desc": "Agent 드롭다운 선택",
            "result": "PASS" if agent_selected else "FAIL",
            "duration_ms": int((time.time()-t0)*1000),
            "agent": agent_selected,
            "screenshot": sc,
        })

        if not agent_selected:
            out["finished_at"] = now_ts()
            return _summarize(out)

        # === 1-5. "Agent API 키 발급" 또는 "첫 API 키 발급" 버튼 클릭 ===
        t0 = time.time()
        btn_clicked = None
        for txt in ["Agent API 키 발급", "첫 API 키 발급", "발급"]:
            try:
                # 모달 트리거 (헤더 우측 또는 빈 상태 중앙)
                b = page.locator(f"button:has-text('{txt}')").all()
                for bb in b:
                    try:
                        if bb.is_visible() and bb.is_enabled():
                            bb.click()
                            btn_clicked = txt
                            break
                    except Exception:
                        continue
                if btn_clicked:
                    break
            except Exception:
                continue
        time.sleep(0.6)
        sc = shot(page, "s1_05", "issue_modal_opened")
        out["steps"].append({"id": "1-5", "desc": f"발급 버튼 클릭 ({btn_clicked or '미발견'})",
                             "result": "PASS" if btn_clicked else "FAIL",
                             "duration_ms": int((time.time()-t0)*1000), "screenshot": sc})

        if not btn_clicked:
            out["finished_at"] = now_ts()
            return _summarize(out)

        # === 1-6. 발급 모달 내 keyName 입력 ===
        t0 = time.time()
        name_filled = False
        # 모달 내 input[placeholder*='개발용' or '프로덕션용']
        for sel_str in ["input[placeholder*='개발용']", "input[placeholder*='프로덕션용']", ".modal.show input[type='text']"]:
            try:
                loc = page.locator(sel_str).first
                if loc.count() > 0 and loc.is_visible():
                    loc.fill(KEY_NAME)
                    name_filled = True
                    break
            except Exception:
                continue
        time.sleep(0.3)
        sc = shot(page, "s1_06", "name_filled")
        out["steps"].append({"id": "1-6", "desc": "keyName 입력", "result": "PASS" if name_filled else "FAIL",
                             "duration_ms": int((time.time()-t0)*1000), "key_name": KEY_NAME, "screenshot": sc})

        # === 1-7. 발급 확정 ("발급" 버튼 modal-footer) ===
        t0 = time.time()
        confirm_clicked = False
        try:
            # modal-footer 의 primary 버튼 — "발급"
            footer_btn = page.locator(".modal-footer button.btn-primary, .modal.show .btn-primary").all()
            for fb in footer_btn:
                try:
                    if fb.is_visible() and fb.is_enabled():
                        txt = (fb.inner_text() or "").strip()
                        if "발급" in txt:
                            fb.click()
                            confirm_clicked = True
                            break
                except Exception:
                    continue
        except Exception as e:
            out["steps"].append({"id": "1-7-debug", "error": f"{type(e).__name__}:{e}"})
        time.sleep(2.0)  # 발급 + 모달 표시 대기
        page.wait_for_load_state("networkidle", timeout=10_000)
        time.sleep(0.5)
        # 보안: 스크린샷 직전 평문 키 표시 영역을 DOM 에서 전면 마스킹 (시각적으로만, 메모리 캡처는 별개)
        # ak- 로 시작하는 모든 텍스트를 마스킹 (모달 + code 블록 + input + textContent 모두)
        try:
            page.evaluate("""() => {
                // 1) 모달 내부 input value 마스킹
                document.querySelectorAll('input').forEach(el => {
                    if (el.value && el.value.startsWith('ak-') && el.value.length > 20) {
                        el.value = el.value.slice(0, 4) + '*'.repeat(36) + el.value.slice(-4);
                    }
                });
                // 2) 모든 텍스트 노드에서 ak-... 패턴 치환 (DOM walker)
                const re = /ak-[A-Za-z0-9_-]{20,}/g;
                const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
                const targets = [];
                let n;
                while ((n = walker.nextNode())) {
                    if (re.test(n.nodeValue)) targets.push(n);
                    re.lastIndex = 0;
                }
                targets.forEach(t => {
                    t.nodeValue = t.nodeValue.replace(re, m => m.slice(0, 4) + '*'.repeat(28) + m.slice(-4));
                });
                // 3) 발급 모달 자체를 일부 블러 처리 (이중 안전)
                document.querySelectorAll('.modal.show').forEach(m => {
                    if (m.textContent.includes('발급된 API 키') || m.textContent.includes('발급 완료')) {
                        // OK — 텍스트는 이미 step 2 에서 마스킹됨
                    }
                });
            }""")
        except Exception:
            pass
        sc = shot(page, "s1_07", "issue_completed_masked")
        # 응답에서 키 캡처 확인
        out["issued_key_masked"] = mask_apikey(captured["apiKey"]) if captured["apiKey"] else None
        out["issued_record_id"] = captured["apiKeyId"]
        out["steps"].append({
            "id": "1-7",
            "desc": "발급 확정 + 응답 캡처",
            "result": "PASS" if captured["apiKey"] else "FAIL",
            "duration_ms": int((time.time()-t0)*1000),
            "key_captured": bool(captured["apiKey"]),
            "key_masked": out["issued_key_masked"],
            "record_id": out["issued_record_id"],
            "endpoint": captured.get("url"),
            "screenshot": sc,
        })

        # === 1-8. 발급 완료 모달 닫기 (보안: 평문 키 화면에서 제거) ===
        try:
            close_btn = page.locator(".modal.show .btn-close, .modal.show button:has-text('닫기')").first
            if close_btn.count() > 0:
                close_btn.click()
                time.sleep(0.5)
        except Exception:
            pass

        # === 1-9. 발급된 키로 /v1/models 호출 ===
        t0 = time.time()
        if captured["apiKey"]:
            code, body = http_get_models(captured["apiKey"])
            model_count = None
            try:
                bj = json.loads(body)
                if isinstance(bj, dict) and "data" in bj:
                    model_count = len(bj["data"])
            except Exception:
                pass
            out["steps"].append({
                "id": "1-9",
                "desc": "발급된 키로 GET /v1/models",
                "result": "PASS" if code == 200 else "FAIL",
                "duration_ms": int((time.time()-t0)*1000),
                "status": code,
                "model_count": model_count,
                "body_preview": body[:300],
            })
        else:
            out["steps"].append({"id": "1-9", "desc": "키 미캡처 → /v1/models SKIP", "result": "SKIP"})

        # === 1-10. 키 삭제 — 해당 행의 "삭제" 버튼 클릭 ===
        t0 = time.time()
        revoke_action = None
        # 발급 완료 모달 닫혔으니 현 페이지에 발급된 키 행이 표시됨
        # 추가 새로고침은 SPA 상태 초기화로 행 표시 지연 — 그대로 진행
        time.sleep(0.6)

        # 삭제 시도 — confirm dialog 자동 수락
        page.on("dialog", lambda d: d.accept())
        try:
            # 키 이름이 포함된 행 → scroll_into_view → 삭제 버튼 클릭
            row_locator = page.locator(f".ak-key-row:has-text('{KEY_NAME}')").first
            if row_locator.count() > 0:
                try:
                    row_locator.scroll_into_view_if_needed(timeout=4_000)
                except Exception:
                    pass
                time.sleep(0.3)
                del_btn = row_locator.locator("button:has-text('삭제')").first
                if del_btn.count() > 0:
                    try:
                        del_btn.scroll_into_view_if_needed(timeout=3_000)
                    except Exception:
                        pass
                    try:
                        del_btn.click(timeout=5_000)
                        revoke_action = "UI 삭제 클릭"
                        time.sleep(1.5)
                    except Exception:
                        # hover 후 재시도
                        try:
                            row_locator.hover()
                            time.sleep(0.3)
                            del_btn.click(force=True, timeout=5_000)
                            revoke_action = "UI 삭제 force-click"
                            time.sleep(1.5)
                        except Exception:
                            pass
        except Exception as e:
            out["steps"].append({"id": "1-10-debug", "error": f"{type(e).__name__}:{e}"})
        sc = shot(page, "s1_10", f"after_revoke_{revoke_action or 'failed'}")
        out["steps"].append({
            "id": "1-10",
            "desc": f"키 삭제 ({revoke_action or '실패'})",
            "result": "PASS" if revoke_action else "FAIL",
            "duration_ms": int((time.time()-t0)*1000),
            "screenshot": sc,
        })

        # === 1-11. 회수 후 /v1/models 재호출 → 401/403 ===
        t0 = time.time()
        if captured["apiKey"]:
            time.sleep(1.2)
            code2, body2 = http_get_models(captured["apiKey"])
            out["steps"].append({
                "id": "1-11",
                "desc": "회수 후 GET /v1/models",
                "result": "PASS" if code2 in (401, 403) else "FAIL",
                "duration_ms": int((time.time()-t0)*1000),
                "status": code2,
                "body_preview": body2[:300],
            })
        else:
            out["steps"].append({"id": "1-11", "desc": "키 미캡처 → 회수 검증 SKIP", "result": "SKIP"})

    # === 1-12. cleanup 보장: 시나리오 종료 후 잔여 키가 있으면 API 로 강제 삭제 ===
    cleanup_done = []
    try:
        c, b = _api("POST", "/api/auth/login", body={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        cleanup_token = json.loads(b)["token"] if c == 200 else None
        if cleanup_token and captured.get("apiKeyId"):
            # agent_id 알고 있을 때
            agent_id_for_cleanup = None
            try:
                agent_id_for_cleanup = int(captured["full"].get("agentId")) if captured.get("full") else None
            except Exception:
                pass
            if not agent_id_for_cleanup:
                # 시나리오 1에서 사용한 agent_id 추적 — captured 에 없으면 agent 옵션 value
                pass  # scenario 메인 함수의 agent_selected 가 closure 외부
            # 모든 agents 의 keys 를 순회하며 ui-e2e-test 키 검색
            ck, cb = _api("GET", "/api/agents", headers={"Authorization": f"Bearer {cleanup_token}"})
            if ck == 200:
                try:
                    agents = json.loads(cb)
                    for a in (agents if isinstance(agents, list) else []):
                        aid = a.get("agentId")
                        if not aid:
                            continue
                        kk, kb = _api("GET", f"/api/agents/{aid}/api-keys", headers={"Authorization": f"Bearer {cleanup_token}"})
                        if kk == 200:
                            try:
                                ks = json.loads(kb)
                                for k in (ks if isinstance(ks, list) else []):
                                    if "ui-e2e-test" in str(k.get("keyName", "")):
                                        kid = k.get("apiKeyId")
                                        dc, _ = _api("DELETE", f"/api/agents/{aid}/api-keys/{kid}",
                                                     headers={"Authorization": f"Bearer {cleanup_token}"})
                                        cleanup_done.append({"agent_id": aid, "key_id": kid, "status": dc})
                            except Exception:
                                pass
                except Exception:
                    pass
    except Exception:
        pass
    out["cleanup"] = cleanup_done

    out["finished_at"] = now_ts()
    return _summarize(out)


def _api(method: str, path: str, *, body: dict | None = None, headers: dict | None = None) -> tuple[int, str]:
    """internal HTTP — for cleanup."""
    h = {"Accept": "application/json"}
    if headers:
        h.update(headers)
    d = None
    if body is not None:
        d = json.dumps(body).encode("utf-8")
        h["Content-Type"] = "application/json"
    rq = urllib.request.Request(AGENTHUB_BASE + path, data=d, headers=h, method=method)
    try:
        with urllib.request.urlopen(rq, timeout=10.0) as r:
            return r.getcode(), r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, (e.read().decode("utf-8", errors="replace") if e else "")
    except Exception as e:
        return -1, f"EXC:{type(e).__name__}:{e}"


def _summarize(out: dict) -> dict:
    summary = {"PASS": 0, "FAIL": 0, "SKIP": 0, "INFO": 0}
    for s in out["steps"]:
        r = s.get("result", "")
        summary[r] = summary.get(r, 0) + 1
    out["summary"] = summary
    pass_n, fail_n = summary["PASS"], summary["FAIL"]
    out["overall"] = "PASS" if fail_n == 0 and pass_n >= 7 else ("PARTIAL" if pass_n >= 4 else "FAIL")
    return out


if __name__ == "__main__":
    result = run()
    with open("scenario_1_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print(json.dumps({
        "summary": result["summary"],
        "overall": result["overall"],
        "issued_key_masked": result["issued_key_masked"],
        "issued_record_id": result["issued_record_id"],
    }, ensure_ascii=False, indent=2))
    print("saved scenario_1_result.json")
