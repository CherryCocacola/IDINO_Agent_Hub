"""트랙 #75 시나리오 3 보정 후 직접 검증.

발견한 정확 endpoint 들을 admin Bearer 로 호출 → 200 검증.
+ E-02 SignalR negotiate 호출 페이지 추가 탐색 (대시보드/Agent 빌더 등).
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
from common import ADMIN_EMAIL, ADMIN_PASSWORD, AGENTHUB_BASE, chrome, now_ts, shot


def http(m, p, body=None, headers=None):
    h = {"Accept": "application/json"}
    if headers:
        h.update(headers)
    d = None
    if body is not None:
        d = json.dumps(body).encode("utf-8")
        h["Content-Type"] = "application/json"
    rq = urllib.request.Request(AGENTHUB_BASE + p, data=d, headers=h, method=m)
    try:
        with urllib.request.urlopen(rq, timeout=10) as r:
            return r.getcode(), r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as he:
        return he.code, (he.read().decode("utf-8", errors="replace") if he else "")
    except Exception as e:
        return -1, f"EXC:{type(e).__name__}:{e}"


def main():
    out = {"started_at": now_ts(), "steps": []}

    # admin JWT
    c, b = http("POST", "/api/auth/login", body={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    token = json.loads(b)["token"]
    H = {"Authorization": f"Bearer {token}"}

    # G-04a 검증 — 5개 sub-endpoint
    g04a_endpoints = [
        "/api/admin/docutil/dashboard/metrics",
        "/api/admin/docutil/dashboard/response-times",
        "/api/admin/docutil/dashboard/search-errors",
        "/api/admin/docutil/dashboard/search-usage",
        "/api/admin/docutil/dashboard/upload-status",
    ]
    for ep in g04a_endpoints:
        c, b = http("GET", ep, headers=H)
        out["steps"].append({
            "id": f"G-04a:{ep.rsplit('/',1)[-1]}",
            "ep": ep,
            "admin_status": c,
            "result": "PASS" if c == 200 else "FAIL",
            "preview": b[:200],
        })
        # anonymous 검증
        c2, b2 = http("GET", ep)
        out["steps"].append({
            "id": f"G-04a-anon:{ep.rsplit('/',1)[-1]}",
            "ep": ep,
            "anonymous_status": c2,
            "result": "PASS" if c2 == 401 else "FAIL",
            "preview": b2[:120],
        })

    # G-07a 검증
    g07a_endpoints = [
        "/api/admin/docutil/evaluation/config",
    ]
    for ep in g07a_endpoints:
        c, b = http("GET", ep, headers=H)
        out["steps"].append({"id": f"G-07a:{ep.rsplit('/',1)[-1]}", "ep": ep, "admin_status": c,
                             "result": "PASS" if c == 200 else "FAIL", "preview": b[:200]})
        c2, b2 = http("GET", ep)
        out["steps"].append({"id": f"G-07a-anon:{ep.rsplit('/',1)[-1]}", "ep": ep, "anonymous_status": c2,
                             "result": "PASS" if c2 == 401 else "FAIL", "preview": b2[:120]})

    # A-06 — UI 가 호출하는 정확한 로그아웃 endpoint
    out["steps"].append({"id": "A-06 (UI flow)", "ep": "POST /api/auth/logout (Bearer + body {})",
                         "note": "UI 로그아웃 흐름은 JSON body 와 함께 호출. 트랙 #74의 415는 body 없는 curl 때문",
                         "result": "INFO"})
    c, b = http("POST", "/api/auth/logout", body={}, headers=H)
    out["steps"].append({"id": "A-06 verify", "admin_status": c, "result": "PASS" if c in (200, 204) else "FAIL", "preview": b[:200]})

    # E-02 — SignalR negotiate 호출 페이지 탐색
    # multi-chat 페이지에서 캡처 안 됐으므로 다른 페이지 시도
    network_log: list = []
    websockets_observed: list = []
    with chrome(headless=True) as (_p, _b, _ctx, page):
        page.on("response", lambda r: network_log.append({"method": r.request.method, "url": r.url, "status": r.status}))
        page.on("websocket", lambda ws: websockets_observed.append({"url": ws.url, "ts": now_ts()}))

        # 로그인
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
        time.sleep(3.0)  # 대시보드 로딩 + SignalR 자동 negotiate 대기

        # 채팅 페이지 진입 → 더 긴 대기
        page.goto(f"{AGENTHUB_BASE}/agents/multi-chat")
        page.wait_for_load_state("networkidle", timeout=10_000)
        time.sleep(5.0)

        # 기존 대화로 진입 (이미 conversations/262 에 대화 있음)
        page.goto(f"{AGENTHUB_BASE}/agents/chat")
        page.wait_for_load_state("networkidle", timeout=10_000)
        time.sleep(4.0)

    negotiate_calls = [n for n in network_log if "negotiate" in n["url"]]
    out["steps"].append({
        "id": "E-02 (SignalR negotiate hunt)",
        "negotiate_calls": negotiate_calls[:10],
        "websockets_observed": websockets_observed[:5],
        "result": "PASS" if negotiate_calls or websockets_observed else "FAIL",
        "note": "여러 페이지(/, /agents/multi-chat, /agents/chat)에서 자동 negotiate 캡처 시도",
    })

    out["finished_at"] = now_ts()
    summary = {"PASS": 0, "FAIL": 0, "SKIP": 0, "INFO": 0}
    for s in out["steps"]:
        r = s.get("result", "")
        if r in summary:
            summary[r] += 1
    out["summary"] = summary
    return out


if __name__ == "__main__":
    result = main()
    with open("scenario_3_verify.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    print("saved scenario_3_verify.json")
