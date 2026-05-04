"""서버 에이전트 상태 확인 스크립트."""
import requests
import json

BASE = "http://localhost:8000/api/v1"
r = requests.post(f"{BASE}/auth/login", json={"username":"jyj7970","password":"idino!@#$"})
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

# 에이전트 목록
r2 = requests.get(f"{BASE}/agents", headers=h)
agents = r2.json().get("items", [])
print(f"에이전트: {len(agents)}개")
for a in agents:
    print(f"  {a['id'][:8]}... | {a.get('agent_type',''):10s} | temp={a.get('temperature','')} | {a['name']}")
    if a.get("system_prompt"):
        print(f"    prompt: {a['system_prompt'][:80]}...")

# 회의록 에이전트로 보고서 생성 테스트
minutes_agent = None
for a in agents:
    if a.get("agent_type") == "minutes" or "회의록" in a.get("name",""):
        minutes_agent = a
        break

if minutes_agent:
    print(f"\n회의록 에이전트 발견: {minutes_agent['name']} (id={minutes_agent['id'][:8]}...)")

    # 템플릿 확인
    r3 = requests.get(f"{BASE}/templates?page=1&size=10", headers=h)
    templates = r3.json().get("items", [])
    meeting_tpl = None
    for t in templates:
        if "회의록" in t.get("name",""):
            meeting_tpl = t
            break

    # 소스 문서
    r4 = requests.get(f"{BASE}/documents?page=1&page_size=3", headers=h)
    docs = r4.json().get("items", [])
    doc_id = docs[0]["id"] if docs else None

    if meeting_tpl and doc_id:
        print(f"템플릿: {meeting_tpl['name']} (id={meeting_tpl['id'][:8]}...)")
        print(f"소스 문서: {doc_id[:8]}...")

        # 생성 요청 (에이전트 포함)
        body = {
            "title": "에이전트 테스트 회의록",
            "output_format": "docx",
            "source_document_ids": [doc_id],
            "generation_params": {
                "document_template_id": meeting_tpl["id"],
                "agent_id": minutes_agent["id"],
            },
            "custom_context": {
                "장소": "본사 회의실",
                "일시": "2026-03-26",
                "참석자": "테스트 참석자",
                "주제": "에이전트 동작 테스트",
            },
        }
        r5 = requests.post(f"{BASE}/reports/generate", headers={**h, "Content-Type":"application/json"}, json=body)
        print(f"생성 요청: {r5.status_code}")
        rd = r5.json()
        print(f"report_id: {rd.get('id')}, status: {rd.get('status')}")

        # 30초 대기 후 결과 확인
        import time
        print("30초 대기...")
        time.sleep(30)
        r6 = requests.get(f"{BASE}/reports/{rd.get('id')}", headers=h)
        rd6 = r6.json()
        print(f"결과: status={rd6.get('status')}, error={rd6.get('error_message','')[:200]}")
    else:
        print(f"템플릿: {meeting_tpl}, 소스문서: {doc_id}")
else:
    print("회의록 에이전트를 찾지 못했습니다.")
