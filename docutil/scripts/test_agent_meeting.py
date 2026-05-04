"""회의록 에이전트 연동 테스트."""
import requests, json, time

BASE = "http://localhost:8000/api/v1"
r = requests.post(BASE+"/auth/login", json={"username":"jyj7970","password":"idino!@#$"})
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

# 1. 템플릿 업로드
with open("/tmp/meeting_form.docx", "rb") as f:
    resp = requests.post(BASE+"/templates/upload-smart", headers=h,
        files={"file": ("회의록_양식.docx", f)},
        data={"name": "회의록", "template_type": "minutes", "tone": "formal"})
print(f"업로드: {resp.status_code}")
d = resp.json()
tid = d.get("id","")
print(f"  id={tid[:8]}, mode={d.get('rendering_mode')}, vars={len(d.get('variables',[]))}")

# 2. 에이전트
r2 = requests.get(BASE+"/agents", headers=h)
agents = r2.json().get("items",[])
agent_id = None
for a in agents:
    if a.get("agent_type") == "minutes":
        agent_id = a["id"]
        print(f"에이전트: {a['name']} ({a['id'][:8]})")
        break

# 3. 소스 문서
r3 = requests.get(BASE+"/documents?page=1&page_size=3", headers=h)
docs = r3.json().get("items",[])
doc_id = docs[0]["id"] if docs else None

# 4. 생성
body = {
    "title": "부산 중소기업 기술개발 회의록",
    "output_format": "docx",
    "source_document_ids": [doc_id] if doc_id else [],
    "generation_params": {
        "document_template_id": tid,
        "agent_id": agent_id,
    },
    "custom_context": {
        "장소": "본사 3층 대회의실",
        "일시": "2026-03-26",
        "참석자": "변동언, 김용휴, 백성현, 이현수",
        "주제": "부산지역 중소기업유망기술개발 세부 지원내용 검토",
    },
}
r4 = requests.post(BASE+"/reports/generate", headers={**h,"Content-Type":"application/json"}, json=body)
print(f"생성: {r4.status_code}")
rd = r4.json()
rid = rd.get("id","")
print(f"  report_id={rid[:8]}, status={rd.get('status')}")

print("40초 대기...")
time.sleep(40)
r5 = requests.get(f"{BASE}/reports/{rid}", headers=h)
rd5 = r5.json()
print(f"결과: status={rd5.get('status')}")
err = rd5.get("error_message","")
if err: print(f"  error: {err[:200]}")
if rd5.get("status") == "completed":
    print("생성 완료!")
