"""Comprehensive API E2E test for all defined features."""
import base64
import json
import sys
import time

import httpx

sys.stdout.reconfigure(encoding="utf-8")

BASE = "http://192.168.10.39:8040/api/v1"
NGINX = "http://192.168.10.39:8041/api/v1"
p = 0
f = 0
issues = []


def chk(name, status, expect=None, detail=""):
    global p, f
    if expect is None:
        expect = {200}
    ok = status in expect
    if ok:
        p += 1
    else:
        f += 1
        issues.append((name, status, detail))
    tag = "PASS" if ok else "FAIL"
    extra = f" - {detail[:80]}" if detail and not ok else ""
    print(f"[{tag}] {name}: {status}{extra}")
    return ok


# === Login ===
r = httpx.post(BASE + "/auth/login", json={"username": "admin", "password": "admin123!"}, timeout=10)
admin_token = r.json()["access_token"]
ha = {"Authorization": f"Bearer {admin_token}"}
print("--- Admin login OK ---\n")

r = httpx.post(BASE + "/auth/login", json={"username": "shbaek", "password": "idino!@#$"}, timeout=10)
chk("로그인(member:shbaek)", r.status_code)
member_token = r.json()["access_token"]
hm = {"Authorization": f"Bearer {member_token}"}

# === 1. Auth ===
print("\n=== 인증/인가 ===")
login_data = httpx.post(BASE + "/auth/login", json={"username": "admin", "password": "admin123!"}, timeout=10).json()
rt = login_data.get("refresh_token", "")
if rt:
    r = httpx.post(BASE + "/auth/refresh", json={"refresh_token": rt}, timeout=10)
    chk("토큰 갱신", r.status_code)
else:
    chk("토큰 갱신(refresh_token 없음)", 0, detail="no refresh_token in login response")

# === 2. Users ===
print("\n=== 사용자 관리 ===")
r = httpx.get(BASE + "/users/", headers=ha, timeout=10)
chk("사용자 목록(admin)", r.status_code)
r = httpx.get(BASE + "/users/", headers=hm, timeout=10)
chk("사용자 목록(member) -> 403", r.status_code, {403})

# === 3. Organizations ===
print("\n=== 부서/조직 ===")
payload_b64 = admin_token.split(".")[1]
payload_b64 += "=" * (4 - len(payload_b64) % 4)
jwt_payload = json.loads(base64.b64decode(payload_b64))
org_id = jwt_payload.get("org_id", "")
r = httpx.get(f"{BASE}/organizations/{org_id}", headers=ha, timeout=10)
chk("조직 조회", r.status_code)
r = httpx.get(f"{BASE}/organizations/{org_id}/departments", headers=ha, timeout=10)
chk("부서 목록", r.status_code)
depts = r.json() if r.status_code == 200 else []
if isinstance(depts, list) and depts:
    dept_id = depts[0].get("id")
    if dept_id:
        r = httpx.get(f"{BASE}/organizations/{org_id}/departments/{dept_id}/members", headers=ha, timeout=10)
        chk("부서 멤버 조회", r.status_code)

# === 4. Projects ===
print("\n=== 프로젝트 ===")
r = httpx.get(BASE + "/projects", headers=ha, timeout=10)
chk("프로젝트 목록(admin)", r.status_code)
r = httpx.get(BASE + "/projects", headers=hm, timeout=10)
chk("프로젝트 목록(member)", r.status_code)
r = httpx.get(BASE + "/projects/tree", headers=ha, timeout=10)
chk("프로젝트 트리", r.status_code)

# === 5. Documents ===
print("\n=== 문서 ===")
r = httpx.get(BASE + "/documents", headers=ha, params={"size": "10"}, timeout=10)
chk("문서 목록(admin)", r.status_code)
docs = r.json().get("items", []) if r.status_code == 200 else []

r = httpx.get(BASE + "/documents", headers=hm, params={"size": "10"}, timeout=10)
chk("문서 목록(member)", r.status_code)

if docs:
    doc_id = docs[0]["id"]
    r = httpx.get(f"{BASE}/documents/{doc_id}", headers=ha, timeout=10)
    chk("문서 상세", r.status_code)
    r = httpx.get(f"{BASE}/documents/{doc_id}/download", headers=ha, timeout=30)
    chk("문서 다운로드", r.status_code)
    r = httpx.get(f"{BASE}/documents/{doc_id}/chunks", headers=ha, timeout=10)
    chk("문서 청크", r.status_code)

# === 6. Search ===
print("\n=== 검색 ===")
r = httpx.post(BASE + "/search", json={"query": "기술 스택", "max_results": 5}, headers=ha, timeout=15)
chk("하이브리드 검색", r.status_code)
if r.status_code == 200:
    d = r.json()
    print(f"    -> {d.get('total_results', 0)} results, {d.get('latency_ms')}ms")

r = httpx.post(BASE + "/search", json={"query": "기술 스택", "max_results": 5, "agentic": True}, headers=ha, timeout=25)
chk("Agentic 검색", r.status_code)
if r.status_code == 200:
    d = r.json()
    print(f"    -> type={d.get('search_type')}, {d.get('total_results', 0)} results, {d.get('latency_ms')}ms")

r = httpx.post(BASE + "/search/keyword", json={"query": "FastAPI"}, headers=ha, timeout=15)
chk("키워드 검색", r.status_code)

r = httpx.get(BASE + "/search/history", headers=ha, timeout=10)
chk("검색 히스토리", r.status_code)

# Chatbot search (needs scope)
scopes_r = httpx.get(BASE + "/search-scopes", headers=ha, timeout=10)
scopes = scopes_r.json().get("items", []) if scopes_r.status_code == 200 else []
if scopes:
    scope_id = scopes[0]["id"]
    r = httpx.post(BASE + "/search/chatbot", json={"query": "기술 스택", "search_scope_id": scope_id}, headers=ha, timeout=20)
    chk("챗봇 검색", r.status_code)
    r = httpx.post(BASE + "/search/qa", json={"query": "기술 스택", "search_scope_id": scope_id}, headers=ha, timeout=20)
    chk("QA 검색(citations)", r.status_code)

# === 7. Chat ===
print("\n=== 챗봇 ===")
r = httpx.get(BASE + "/chat/sessions", headers=ha, timeout=10)
chk("챗봇 세션 목록(admin)", r.status_code)
r = httpx.get(BASE + "/chat/sessions", headers=hm, timeout=10)
chk("챗봇 세션 목록(member)", r.status_code)

r = httpx.post(BASE + "/chat/sessions", json={"title": "E2E full"}, headers=ha, timeout=10)
chk("세션 생성", r.status_code, {200, 201})
if r.status_code in (200, 201):
    sid = r.json()["id"]
    r2 = httpx.post(f"{BASE}/chat/sessions/{sid}/messages", json={"content": "DocUtil이란?"}, headers=ha, timeout=20)
    chk("메시지 전송(REST)", r2.status_code, {200, 201})
    r3 = httpx.get(f"{BASE}/chat/sessions/{sid}/messages", headers=ha, timeout=10)
    chk("메시지 히스토리", r3.status_code)
    r4 = httpx.get(f"{BASE}/chat/sessions/{sid}", headers=ha, timeout=10)
    chk("세션 상세", r4.status_code)

# === 8. Reports ===
print("\n=== 보고서 ===")
r = httpx.get(BASE + "/reports", headers=ha, timeout=10)
chk("보고서 목록(admin)", r.status_code)
r = httpx.get(BASE + "/reports", headers=hm, timeout=10)
chk("보고서 목록(member)", r.status_code)

# Free-form report
r = httpx.post(BASE + "/reports/generate", json={
    "title": "E2E DOCX", "report_type": "report", "format": "docx", "content": "테스트 보고서"
}, headers=ha, timeout=15)
chk("보고서 생성(DOCX 자유형)", r.status_code, {200, 201, 202})

r = httpx.post(BASE + "/reports/generate", json={
    "title": "E2E PPTX", "report_type": "proposal", "format": "pptx", "content": "테스트 제안서"
}, headers=ha, timeout=15)
chk("보고서 생성(PPTX 자유형)", r.status_code, {200, 201, 202})

# With template
templates_r = httpx.get(BASE + "/templates", headers=ha, timeout=10)
templates = templates_r.json().get("items", []) if templates_r.status_code == 200 else []
if templates:
    tmpl = templates[0]
    r = httpx.post(BASE + "/reports/generate", json={
        "title": "E2E 템플릿",
        "report_type": "report",
        "format": tmpl.get("format", "docx"),
        "template_id": tmpl["id"],
        "content": "템플릿 테스트",
    }, headers=ha, timeout=15)
    chk("보고서 생성(템플릿)", r.status_code, {200, 201, 202}, r.text[:100] if r.status_code >= 400 else "")

# Download existing report
reports = httpx.get(BASE + "/reports", headers=ha, timeout=10).json().get("items", [])
completed = [rp for rp in reports if rp.get("status") == "completed"]
if completed:
    rid = completed[0]["id"]
    r = httpx.get(f"{BASE}/reports/{rid}/download", headers=ha, timeout=30)
    chk("보고서 다운로드", r.status_code)

# === 9. Templates ===
print("\n=== 템플릿 ===")
r = httpx.get(BASE + "/templates", headers=ha, timeout=10)
chk("템플릿 목록", r.status_code)
if templates:
    r = httpx.get(f"{BASE}/templates/{templates[0]['id']}", headers=ha, timeout=10)
    chk("템플릿 상세", r.status_code)

# === 10. Agents ===
print("\n=== 에이전트 ===")
r = httpx.get(BASE + "/agents", headers=ha, timeout=10)
chk("에이전트 목록", r.status_code)
agents = r.json().get("items", []) if r.status_code == 200 else []
if agents:
    r = httpx.get(f"{BASE}/agents/{agents[0]['id']}", headers=ha, timeout=10)
    chk("에이전트 상세", r.status_code)

# === 11. Search Scopes ===
print("\n=== 검색범위 ===")
r = httpx.get(BASE + "/search-scopes", headers=ha, timeout=10)
chk("검색범위 목록", r.status_code)

# === 12. API Keys ===
print("\n=== API 키 ===")
r = httpx.get(BASE + "/api-keys", headers=ha, timeout=10)
chk("API키 목록", r.status_code)

# === 13. Audit ===
print("\n=== 감사 로그 ===")
r = httpx.get(BASE + "/audit-logs", headers=ha, timeout=10)
chk("감사로그(admin)", r.status_code)

# === 14. FAQ ===
print("\n=== FAQ ===")
r = httpx.get(BASE + "/faq", headers=ha, timeout=10)
chk("FAQ 목록", r.status_code)

# === 15. Health/Dashboard ===
print("\n=== 시스템 ===")
r = httpx.get("http://192.168.10.39:8040/health", timeout=5)
chk("헬스체크", r.status_code)
r = httpx.get(BASE + "/dashboard/search-usage", headers=ha, timeout=10)
chk("대시보드 검색사용량", r.status_code)

# === 16. CORS ===
print("\n=== CORS ===")
for path in ["/documents/upload", "/templates/upload-smart", "/chat/sessions"]:
    r = httpx.options(NGINX + path, headers={
        "Origin": "http://192.168.10.39:3040",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type",
    }, timeout=10)
    chk(f"CORS {path}", r.status_code)

# === 17. Evaluation ===
print("\n=== 평가 ===")
r = httpx.get(BASE + "/evaluation/config", headers=ha, timeout=10)
chk("평가 설정", r.status_code)

# === Summary ===
print(f"\n{'=' * 60}")
print(f"Total: {p + f} tests | PASS: {p} | FAIL: {f}")
if issues:
    print(f"\n--- Failed ({f}) ---")
    for name, status, detail in issues:
        print(f"  [{status}] {name}" + (f": {detail[:80]}" if detail else ""))
else:
    print("\nALL PASSED!")
