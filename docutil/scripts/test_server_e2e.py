"""서버에서 회의록 양식 업로드 → 회의록 생성 E2E 테스트."""
import requests
import json
import time
import sys

BASE = "http://localhost:8000/api/v1"

# 1. 로그인
r = requests.post(f"{BASE}/auth/login", json={"username":"jyj7970","password":"idino!@#$"})
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}
print(f"1. 로그인 성공: {token[:20]}...")

# 2. 회의록 양식 업로드
with open("/tmp/meeting_form.docx", "rb") as f:
    resp = requests.post(f"{BASE}/templates/upload-smart", headers=h,
        files={"file": ("회의록_양식.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})
print(f"2. 업로드: {resp.status_code}")
d = resp.json()
tid = d.get("id","")
print(f"   id={tid}, name={d.get('name')}, mode={d.get('rendering_mode')}, vars={len(d.get('variables',[]))}")

# 3. 소스 문서
r3 = requests.get(f"{BASE}/documents?page=1&page_size=10", headers=h)
docs = r3.json().get("items", [])
print(f"3. 소스 문서: {len(docs)}건")
hwpx_id = None
for doc in docs:
    title = doc.get("title","") or doc.get("filename","")
    print(f"   {doc['id'][:8]}... | {title[:50]}")
    if "소부장" in title or "부산" in title or "hwpx" in title.lower():
        hwpx_id = doc["id"]
if not hwpx_id and docs:
    hwpx_id = docs[0]["id"]
print(f"   선택: {hwpx_id}")

# 4. 회의록 생성
body = {
    "title": "부산지역 중소기업유망기술개발 지원사업 회의록",
    "output_format": "docx",
    "source_document_ids": [hwpx_id] if hwpx_id else [],
    "generation_params": {"document_template_id": tid},
    "custom_context": {
        "장소": "본사 3층 대회의실",
        "일시": "2026-03-26",
        "참석자": "변동언, 김용휴, 백성현, 이현수 외 3명",
        "주제": "부산지역 중소기업유망기술개발(소부장) 세부 지원내용 검토"
    },
}
r4 = requests.post(f"{BASE}/reports/generate", headers={**h, "Content-Type":"application/json"}, json=body)
print(f"4. 생성 요청: {r4.status_code}")
rd = r4.json()
rid = rd.get("id","")
print(f"   report_id={rid}, status={rd.get('status')}")

# 5. 결과 대기
print("5. 60초 대기 중...")
time.sleep(60)
r5 = requests.get(f"{BASE}/reports/{rid}", headers=h)
rd5 = r5.json()
status = rd5.get("status","")
err = rd5.get("error_message","")
print(f"   status={status}")
if err:
    print(f"   error: {err[:200]}")
if status == "completed":
    path = rd5.get("output_storage_path","")
    print(f"   생성 완료! path={path}")
