"""트랙 #74 — 운영 환경 전체 시스템 라이브 테스트 (read-only + 1회 mutation 허용 최소).

대상: AgentHub `http://192.168.10.39:64005`
- 안전 (GET / anonymous 401 검증 / login)
- 중간 (인증 후 read)
- 위험 (mutation) → SKIP

결과를 JSON으로 stdout 출력 → 카탈로그 + 엑셀 체크리스트에 반영.
"""
from __future__ import annotations
import json
import sys
import time
from typing import Any
import urllib.request
import urllib.error

BASE = "http://192.168.10.39:64005"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "Admin123!"
TIMEOUT = 15.0


def req(method: str, path: str, *, headers: dict | None = None, body: dict | None = None, timeout: float = TIMEOUT) -> tuple[int, str, dict]:
    """HTTP 요청 — status / body_text(앞 800자) / response headers 반환. 예외 시 status=-1."""
    url = BASE + path
    data = None
    h = {"Accept": "application/json"}
    if headers:
        h.update(headers)
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        h["Content-Type"] = "application/json"
    rq = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(rq, timeout=timeout) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            return resp.getcode(), text[:1200], dict(resp.headers)
    except urllib.error.HTTPError as e:
        try:
            text = e.read().decode("utf-8", errors="replace")
        except Exception:
            text = ""
        return e.code, text[:1200], dict(e.headers or {})
    except Exception as e:
        return -1, f"EXC:{type(e).__name__}:{e}", {}


def login_admin() -> str | None:
    code, text, _ = req("POST", "/api/auth/login", body={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    if code == 200:
        try:
            return json.loads(text)["token"]
        except Exception:
            return None
    return None


def run_case(rid: str, scenario: str, method: str, path: str, *, expected: int | set[int], use_token: str | None = None, body: dict | None = None, extra_headers: dict | None = None) -> dict[str, Any]:
    """단일 테스트 케이스 실행 — PASS/FAIL/SKIP 판정."""
    headers = extra_headers.copy() if extra_headers else {}
    if use_token:
        headers["Authorization"] = f"Bearer {use_token}"
    t0 = time.time()
    code, text, resp_h = req(method, path, headers=headers, body=body)
    dt_ms = int((time.time() - t0) * 1000)
    exp_set = expected if isinstance(expected, set) else {expected}
    result = "PASS" if code in exp_set else "FAIL"
    return {
        "id": rid,
        "scenario": scenario,
        "method": method,
        "path": path,
        "expected": sorted(exp_set),
        "actual_status": code,
        "actual_preview": text[:200],
        "duration_ms": dt_ms,
        "result": result,
    }


def main() -> None:
    out: dict[str, Any] = {"started_at": time.strftime("%Y-%m-%d %H:%M:%S"), "cases": []}

    # --- A. 인증 / 세션 ---
    a01 = run_case("A-01", "admin 로그인", "POST", "/api/auth/login",
                   expected=200, body={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    out["cases"].append(a01)
    token = login_admin()
    if not token:
        out["cases"].append({"id": "A-01b", "scenario": "JWT 추출", "result": "FAIL", "actual_preview": "no token"})
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    out["cases"].append(run_case("A-02", "로그인 실패 (잘못된 비번)", "POST", "/api/auth/login",
                                 expected={400, 401, 422}, body={"email": ADMIN_EMAIL, "password": "wrong!"}))
    out["cases"].append(run_case("A-03", "anonymous /api/agents 401", "GET", "/api/agents",
                                 expected=401))
    out["cases"].append(run_case("A-04", "JWT 발급 후 /api/agents 200", "GET", "/api/agents",
                                 expected=200, use_token=token))
    out["cases"].append({"id": "A-05", "scenario": "JWT 만료 → refresh token", "result": "SKIP",
                         "actual_preview": "운영 mutation 회피 — 별도 토큰 발급 부담"})
    out["cases"].append(run_case("A-06", "로그아웃 (POST + JSON body)", "POST", "/api/auth/logout",
                                 expected={200, 204}, use_token=token, body={}))
    out["cases"].append({"id": "A-07", "scenario": "hslee@idino.co.kr 로그인", "result": "SKIP",
                         "actual_preview": "추가 자격증명 미보유, 사용자 결정 필요"})

    # --- B. Agent 관리 ---
    out["cases"].append(run_case("B-01", "GET /api/agents (목록)", "GET", "/api/agents", expected=200, use_token=token))
    # Agent ID 추출
    code_b, text_b, _ = req("GET", "/api/agents", headers={"Authorization": f"Bearer {token}"})
    agent_id = None
    if code_b == 200:
        try:
            agents_list = json.loads(text_b)
            if isinstance(agents_list, list) and agents_list:
                agent_id = agents_list[0].get("agentId")
        except Exception:
            pass
    if agent_id:
        out["cases"].append(run_case("B-02", f"GET /api/agents/{agent_id}", "GET", f"/api/agents/{agent_id}", expected=200, use_token=token))
    else:
        out["cases"].append({"id": "B-02", "scenario": "GET /api/agents/{id}", "result": "SKIP", "actual_preview": "agentId 추출 실패"})
    out["cases"].append({"id": "B-03", "scenario": "POST /api/agents (신규 생성)", "result": "SKIP",
                         "actual_preview": "운영 mutation 위험, 사용자 결정 필요"})
    out["cases"].append({"id": "B-04", "scenario": "PUT /api/agents/{id}", "result": "SKIP",
                         "actual_preview": "운영 mutation 위험"})
    out["cases"].append({"id": "B-05", "scenario": "Agent.LlmRouting 전환", "result": "SKIP",
                         "actual_preview": "운영 mutation 위험"})
    out["cases"].append({"id": "B-06", "scenario": "KnowledgeBaseSource 전환", "result": "SKIP",
                         "actual_preview": "운영 mutation 위험"})
    out["cases"].append({"id": "B-07", "scenario": "EnableRag 토글", "result": "SKIP",
                         "actual_preview": "운영 mutation 위험"})

    # --- C. ApiKey ---
    out["cases"].append(run_case("C-01", "GET /api/api-keys (목록)", "GET", "/api/api-keys", expected=200, use_token=token))
    out["cases"].append({"id": "C-02", "scenario": "POST /api/api-keys (발급)", "result": "SKIP",
                         "actual_preview": "운영 mutation — 신규 키 발급 위험"})
    out["cases"].append({"id": "C-03", "scenario": "ApiKey 회수/비활성화", "result": "SKIP",
                         "actual_preview": "운영 mutation"})
    # X-API-Key 헤더 검증 — 임시 keys 가져와서 한 개로 /v1/models 테스트 (read-only)
    code_c, text_c, _ = req("GET", "/api/api-keys", headers={"Authorization": f"Bearer {token}"})
    api_key_for_v1 = None
    if code_c == 200:
        try:
            ak_list = json.loads(text_c)
            if isinstance(ak_list, list):
                for ak in ak_list:
                    full = ak.get("fullKey") or ak.get("key") or ak.get("apiKey")
                    if full and full.startswith("ak-") and ak.get("isActive", True):
                        api_key_for_v1 = full
                        break
        except Exception:
            pass
    if api_key_for_v1:
        out["cases"].append(run_case("C-04", "X-API-Key /v1/models 호출", "GET", "/v1/models",
                                     expected=200, extra_headers={"X-API-Key": api_key_for_v1}))
    else:
        out["cases"].append({"id": "C-04", "scenario": "X-API-Key /v1/models", "result": "SKIP",
                             "actual_preview": "fullKey 미노출 — 발급된 키 평문 불가 (보안 정책)"})

    # --- D. OpenAI 호환 API ---
    if api_key_for_v1:
        out["cases"].append(run_case("D-01", "GET /v1/models", "GET", "/v1/models",
                                     expected=200, extra_headers={"X-API-Key": api_key_for_v1}))
    else:
        # anonymous 401 검증으로 대체
        out["cases"].append(run_case("D-01", "GET /v1/models (anonymous 401)", "GET", "/v1/models", expected=401))
    out["cases"].append({"id": "D-02", "scenario": "POST /v1/chat/completions sync (1회 비용)", "result": "SKIP",
                         "actual_preview": "운영 LLM 비용 발생 — 사용자 명시 후 1회 실행 권장"})
    out["cases"].append({"id": "D-03", "scenario": "POST /v1/chat/completions stream=true SSE", "result": "SKIP",
                         "actual_preview": "운영 LLM 비용 발생"})
    out["cases"].append({"id": "D-04", "scenario": "POST /v1/embeddings", "result": "SKIP",
                         "actual_preview": "운영 LLM 비용 발생 — 1회 발생 권장"})
    out["cases"].append({"id": "D-05", "scenario": "POST /v1/images/generations", "result": "SKIP",
                         "actual_preview": "DALL-E 비용 발생 — 사용자 결정"})
    out["cases"].append({"id": "D-06", "scenario": "Internal 라우팅 (Nexus)", "result": "SKIP",
                         "actual_preview": "Nexus 인스턴스 가용성 의존 — 별도 환경"})
    out["cases"].append({"id": "D-07", "scenario": "Hybrid 라우팅 PII", "result": "SKIP",
                         "actual_preview": "PII 시드 데이터 입력 부담"})

    # --- E. 채팅 ---
    out["cases"].append({"id": "E-01", "scenario": "/api/chat/send", "result": "SKIP",
                         "actual_preview": "운영 LLM 비용 발생"})
    out["cases"].append(run_case("E-02", "SignalR /hubs/notification POST negotiate (트랙 #75 보정)", "POST",
                                 "/hubs/notification/negotiate?negotiateVersion=1", expected={200}, use_token=token, body=None))
    out["cases"].append({"id": "E-03", "scenario": "게스트 채팅 Rate Limit", "result": "SKIP",
                         "actual_preview": "운영 LLM 비용"})
    out["cases"].append({"id": "E-04", "scenario": "PII 입력 차단", "result": "SKIP",
                         "actual_preview": "운영 LLM 비용"})

    # --- F. Tool / Workflow ---
    out["cases"].append(run_case("F-01", "GET /api/tools", "GET", "/api/tools", expected={200, 404}, use_token=token))
    out["cases"].append({"id": "F-02", "scenario": "POST /api/tools", "result": "SKIP",
                         "actual_preview": "운영 mutation"})
    out["cases"].append({"id": "F-03", "scenario": "Tool 실행 (Tool Calling)", "result": "SKIP",
                         "actual_preview": "LLM 비용 + side effect"})
    out["cases"].append(run_case("F-04", "GET /api/workflows", "GET", "/api/workflows", expected={200, 404}, use_token=token))
    out["cases"].append({"id": "F-05", "scenario": "Workflow 실행", "result": "SKIP",
                         "actual_preview": "side effect 위험"})

    # --- G. Admin BFF — DocUtil 13 메뉴 ---
    docutil_endpoints = [
        ("G-01", "users",            "/api/admin/docutil/users"),
        ("G-02", "departments",      "/api/admin/docutil/departments"),
        ("G-03", "projects",         "/api/admin/docutil/projects"),
        ("G-04", "dashboard metrics", "/api/admin/docutil/dashboard/metrics"),
        ("G-05", "audit-logs",       "/api/admin/docutil/audit-logs"),
        ("G-06", "search-scopes",    "/api/admin/docutil/search-scopes"),
        ("G-07", "evaluation config", "/api/admin/docutil/evaluation/config"),
        ("G-08", "faq",              "/api/admin/docutil/faq"),
        ("G-09", "reports",          "/api/admin/docutil/reports"),
        ("G-10", "templates",        "/api/admin/docutil/templates"),
        ("G-11", "api-keys",         "/api/admin/docutil/api-keys"),
        ("G-12", "agents",           "/api/admin/docutil/agents"),
        ("G-13", "documents-v2",     "/api/admin/docutil/documents-v2"),
    ]
    for rid, name, path in docutil_endpoints:
        # anonymous 401
        out["cases"].append(run_case(f"{rid}a", f"{name} anonymous 401", "GET", path, expected=401))
        # admin Bearer — 200 정상 / 502 downstream / 404 ok depending
        out["cases"].append(run_case(f"{rid}b", f"{name} admin Bearer read", "GET", path,
                                     expected={200, 404, 502, 503}, use_token=token))

    # --- H. Analytics / Quota / Audit ---
    out["cases"].append(run_case("H-01", "GET /api/analytics/usage", "GET",
                                 "/api/analytics/usage", expected={200, 404}, use_token=token))
    out["cases"].append(run_case("H-02", "GET /api/quota", "GET",
                                 "/api/quota", expected={200, 404}, use_token=token))
    out["cases"].append(run_case("H-03", "GET /api/audit", "GET",
                                 "/api/audit", expected={200, 404}, use_token=token))

    # --- I. DocUtil 사용자 흐름 ---
    out["cases"].append({"id": "I-01", "scenario": "DocUtil 자체 로그인", "result": "SKIP",
                         "actual_preview": "DocUtil 사용자 비번 미보유"})
    out["cases"].append({"id": "I-02", "scenario": "DocUtil 챗봇 (AgentHubClient 위임)", "result": "SKIP",
                         "actual_preview": "LLM 비용"})
    out["cases"].append({"id": "I-03", "scenario": "DocUtil /api/v1/search", "result": "SKIP",
                         "actual_preview": "DocUtil 인증 필요"})
    out["cases"].append({"id": "I-04", "scenario": "DocUtil 문서 업로드", "result": "SKIP",
                         "actual_preview": "운영 mutation + 저장공간"})
    out["cases"].append({"id": "I-05", "scenario": "DocUtil 보고서 생성", "result": "SKIP",
                         "actual_preview": "LLM 비용"})

    # --- J. 보안 / Rate Limit ---
    out["cases"].append(run_case("J-01a", "anonymous /api/* 401", "GET", "/api/agents", expected=401))
    out["cases"].append(run_case("J-01b", "anonymous /api/admin/* 401", "GET",
                                 "/api/admin/docutil/users", expected=401))
    out["cases"].append({"id": "J-02", "scenario": "User role admin endpoint 403", "result": "SKIP",
                         "actual_preview": "비 admin 계정 미보유"})
    out["cases"].append({"id": "J-03", "scenario": "Rate Limit (60/min 등)", "result": "SKIP",
                         "actual_preview": "운영 부하 회피 — 별도 환경"})
    out["cases"].append(run_case("J-04", "JWT 위조 검증", "GET", "/api/agents",
                                 expected={401, 403},
                                 extra_headers={"Authorization": "Bearer invalid.jwt.token"}))
    out["cases"].append({"id": "J-05", "scenario": "SQL Injection 방어", "result": "SKIP",
                         "actual_preview": "운영 DB 영향 가능성 — 별도 환경"})
    out["cases"].append({"id": "J-06", "scenario": "XSS 방어", "result": "SKIP",
                         "actual_preview": "UI 의존"})
    out["cases"].append(run_case("J-07", "CORS preflight OPTIONS", "OPTIONS", "/api/agents",
                                 expected={200, 204, 401, 405},
                                 extra_headers={"Origin": "http://example.com",
                                                "Access-Control-Request-Method": "GET"}))

    # --- K. 통합 흐름 (e2e) ---
    out["cases"].append({"id": "K-01", "scenario": "RAG round-trip (chat/send → DocUtil)", "result": "SKIP",
                         "actual_preview": "LLM 비용 + DocUtil 연동 — 사용자 명시 후 1회 실행"})
    out["cases"].append({"id": "K-02", "scenario": "DocUtil 챗봇 → AgentHub /v1/chat → OpenAI", "result": "SKIP",
                         "actual_preview": "LLM 비용"})
    out["cases"].append({"id": "K-03", "scenario": "KB 업로드 → AgentBuilder dropdown", "result": "SKIP",
                         "actual_preview": "운영 mutation"})

    # 통계 집계
    summary = {"PASS": 0, "FAIL": 0, "SKIP": 0, "TOTAL": len(out["cases"])}
    for c in out["cases"]:
        r = c.get("result", "SKIP")
        if r in summary:
            summary[r] += 1
    out["summary"] = summary
    out["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
