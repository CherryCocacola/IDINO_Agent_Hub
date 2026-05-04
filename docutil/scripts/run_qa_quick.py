#!/usr/bin/env python
"""
DocUtil Quick QA Runner
Layers: Scenario API Tests (A,B,C,D) + AI Quality Check
Skips: Edge Cases, Cross-Module Impact
"""
import json
import io
import time
import datetime
import os
import sys
import urllib.request
import urllib.error
import urllib.parse

BASE = "http://192.168.10.39:8040/api/v1"
REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "tests", "qa_reports")

# ── colours ──────────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

results = {"pass": 0, "warn": 0, "fail": 0}
critical_issues = []
warnings = []
perf_data = {}

def ok(msg):
    results["pass"] += 1
    print(f"  {GREEN}✅ PASS{RESET} {msg}")

def warn(msg, detail=""):
    results["warn"] += 1
    warnings.append({"msg": msg, "detail": detail})
    print(f"  {YELLOW}⚠️  WARN{RESET} {msg}" + (f" — {detail}" if detail else ""))

def fail(msg, detail="", severity="HIGH", fix=""):
    results["fail"] += 1
    critical_issues.append({"msg": msg, "detail": detail, "severity": severity, "fix": fix})
    print(f"  {RED}❌ FAIL{RESET} {msg}" + (f" — {detail[:120]}" if detail else ""))

def section(title):
    print(f"\n{BOLD}{CYAN}{'='*55}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'='*55}{RESET}")

def api(method, path, data=None, token=None, timeout=30):
    """Low-level API call returning (status_code, response_dict, elapsed_sec)."""
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(f"{BASE}{path}", data=body, headers=headers, method=method)
    t0 = time.time()
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        elapsed = time.time() - t0
        if resp.status == 204:
            return 204, {}, elapsed
        return resp.status, json.loads(resp.read()), elapsed
    except urllib.error.HTTPError as e:
        elapsed = time.time() - t0
        try:
            body = json.loads(e.read())
        except Exception:
            body = {"detail": str(e)}
        return e.code, body, elapsed
    except Exception as e:
        return 0, {"detail": str(e)}, time.time() - t0

def upload_bytes(filename, file_bytes, content_type, token, visibility="public", department_id=None):
    """Multipart upload returning (status_code, response_dict, elapsed_sec)."""
    boundary = "----QABoundary7MA4YWxkTrZu0gW"
    encoded_name = urllib.parse.quote(filename)

    body = io.BytesIO()
    def w(s): body.write(s if isinstance(s, bytes) else s.encode())
    w(f"--{boundary}\r\n")
    w(f'Content-Disposition: form-data; name="file"; filename="{filename}"; filename*=UTF-8\'\'{encoded_name}\r\n')
    w(f"Content-Type: {content_type}\r\n\r\n")
    body.write(file_bytes)
    w(f"\r\n--{boundary}--\r\n")

    url = f"{BASE}/documents/upload?visibility={visibility}"
    if department_id:
        url += f"&department_id={department_id}"

    req = urllib.request.Request(url, data=body.getvalue(), method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")

    t0 = time.time()
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        elapsed = time.time() - t0
        return resp.status, json.loads(resp.read()), elapsed
    except urllib.error.HTTPError as e:
        elapsed = time.time() - t0
        try:
            body2 = json.loads(e.read())
        except Exception:
            body2 = {"detail": str(e)}
        return e.code, body2, elapsed

def login(username, password):
    code, resp, _ = api("POST", "/auth/login", {"username": username, "password": password})
    if code == 200 and "access_token" in resp:
        return resp["access_token"], resp
    return None, resp

def poll_doc_status(doc_id, token, max_wait=60):
    """Poll until status=completed or timeout. Returns final status."""
    deadline = time.time() + max_wait
    while time.time() < deadline:
        code, resp, _ = api("GET", f"/documents/{doc_id}", token=token)
        if code == 200:
            status = resp.get("status", "")
            if status == "completed":
                return "completed"
            if status in ("failed", "error"):
                return status
        time.sleep(3)
    return "timeout"

# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO A — Document Lifecycle
# ─────────────────────────────────────────────────────────────────────────────
def scenario_a():
    section("SCENARIO A — Document Lifecycle")
    test_doc_id = None

    # A1. Login
    t0 = time.time()
    token, resp = login("admin", "admin123!")
    elapsed = time.time() - t0
    if not token:
        fail("A1: Login failed", str(resp), fix="Check auth service / DB connection")
        return None
    ok(f"A1: Login OK ({elapsed:.2f}s), role={resp.get('user',{}).get('role','?')}")
    perf_data.setdefault("POST /auth/login", []).append(elapsed)

    # Validate schema fields
    for field in ["access_token", "refresh_token", "token_type"]:
        if field not in resp:
            warn(f"A1: Missing field '{field}' in login response")

    # A2. Upload with Korean filename
    korean_filename = "테스트_문서.txt"
    file_content = "이 문서는 DocUtil QA 테스트를 위한 샘플 문서입니다.\n기술 스택: FastAPI, PostgreSQL, Qdrant, Redis, MinIO\n2025년도 테스트 문서입니다.".encode("utf-8")
    code, resp_up, elapsed = upload_bytes(korean_filename, file_content, "text/plain", token)
    perf_data.setdefault("POST /documents/upload", []).append(elapsed)
    if code in (200, 201):
        test_doc_id = resp_up.get("id")
        name_back = resp_up.get("name", "")
        if "테스트" in name_back or "문서" in name_back:
            ok(f"A2: Upload with Korean filename OK — id={str(test_doc_id)[:8]}...")
        else:
            warn(f"A2: Korean filename may be corrupted: '{name_back}'")
    else:
        fail("A2: Upload failed", str(resp_up.get("detail", resp_up))[:200],
             fix="Check MinIO connectivity and document service")
        return None

    # A3. Poll until completed
    print(f"       Polling for completion (max 60s)...", end="", flush=True)
    final_status = poll_doc_status(test_doc_id, token, max_wait=60)
    print()
    if final_status == "completed":
        ok(f"A3: Document processing completed")
    elif final_status == "timeout":
        warn("A3: Document still not completed after 60s", "indexing may be slow or worker stuck")
    else:
        warn(f"A3: Document status={final_status}", "may affect search results")

    # A4. Search for uploaded document
    time.sleep(2)  # brief indexing buffer
    t0 = time.time()
    code, resp_s, elapsed = api("POST", "/search", {"query": "DocUtil QA 테스트", "limit": 10}, token)
    perf_data.setdefault("POST /search", []).append(elapsed)
    if code == 200:
        if elapsed > 2.0:
            warn(f"A4: Search response slow ({elapsed:.2f}s > 2s target)")
        else:
            ok(f"A4: Search OK ({elapsed:.2f}s)")
        hits = resp_s.get("results", resp_s.get("items", []))
        found = any(str(test_doc_id) in str(r) for r in hits)
        if found:
            ok("A4: Uploaded document found in search results")
        else:
            warn("A4: Uploaded document NOT found in search results", "may still be indexing")
    else:
        fail("A4: Search failed", str(resp_s.get("detail",""))[:200], fix="Check search service / Qdrant")

    # A5. Download
    req = urllib.request.Request(
        f"{BASE}/documents/{test_doc_id}/download",
        headers={"Authorization": f"Bearer {token}"}
    )
    t0 = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=15)
        data = r.read()
        elapsed = time.time() - t0
        if len(data) > 0:
            ok(f"A5: Download OK ({len(data)} bytes, {elapsed:.2f}s)")
        else:
            fail("A5: Download returned 0 bytes", fix="Check MinIO storage")
    except Exception as e:
        fail("A5: Download failed", str(e)[:200], fix="Check MinIO / download endpoint")

    # A6. Delete
    code, resp_del, elapsed = api("DELETE", f"/documents/{test_doc_id}", token=token)
    if code in (200, 204):
        ok("A6: Delete OK")
        # Verify gone
        code2, _, _ = api("GET", f"/documents/{test_doc_id}", token=token)
        if code2 == 404:
            ok("A6: Verified document removed (404 after delete)")
        else:
            warn("A6: Document still accessible after delete", f"HTTP {code2}")
    else:
        warn("A6: Delete returned unexpected status", f"HTTP {code} — {resp_del.get('detail','')[:100]}")

    return token  # pass token to next scenarios


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO B — Chat with Documents
# ─────────────────────────────────────────────────────────────────────────────
def scenario_b(token):
    section("SCENARIO B — Chat with Documents")

    if not token:
        token, _ = login("admin", "admin123!")
        if not token:
            fail("B0: Cannot login for chat test")
            return

    # Upload a document first
    content = "2025년 기술 현황 보고서\n기술 스택: FastAPI, React, PostgreSQL, Qdrant\n주요 안건: RAG 시스템 고도화, 멀티모달 지원 추가".encode("utf-8")
    code, resp_up, _ = upload_bytes("chat_test_doc.txt", content, "text/plain", token)
    if code not in (200, 201):
        warn("B1: Could not upload test document for chat", str(resp_up.get("detail",""))[:100])
        doc_id = None
    else:
        doc_id = resp_up.get("id")
        ok(f"B1: Uploaded chat test document (id={str(doc_id)[:8]}...)")
        print(f"       Waiting for indexing...", end="", flush=True)
        status = poll_doc_status(doc_id, token, max_wait=45)
        print(f" {status}")

    # Create chat session
    session_payload = {"title": "QA Chat Test"}
    if doc_id:
        session_payload["scoped_document_ids"] = [str(doc_id)]
    code, resp_sess, elapsed = api("POST", "/chat/sessions", session_payload, token)
    if code not in (200, 201):
        fail("B2: Create chat session failed", str(resp_sess.get("detail",""))[:200],
             fix="Check chat service / DB")
        if doc_id:
            api("DELETE", f"/documents/{doc_id}", token=token)
        return
    session_id = resp_sess.get("id")
    ok(f"B2: Chat session created (id={str(session_id)[:8]}...)")

    # Send chat message
    t0 = time.time()
    code, resp_msg, elapsed = api(
        "POST",
        f"/chat/sessions/{session_id}/messages",
        {"content": "이 문서의 기술 스택은 무엇인가요?"},
        token,
        timeout=60,
    )
    perf_data.setdefault("POST /chat", []).append(elapsed)
    if code in (200, 201):
        if elapsed > 3.0:
            warn(f"B3: Chat response slow ({elapsed:.2f}s > 3s target)")
        else:
            ok(f"B3: Chat response received ({elapsed:.2f}s)")
        msg = resp_msg.get("message", resp_msg)
        content_text = msg.get("content", "")
        if not content_text:
            fail("B3: Chat response has empty content", fix="Check LLM integration")
        else:
            ok(f"B3: Response content length={len(content_text)} chars")
            # Check for citations
            citations = msg.get("citations", [])
            if citations:
                # Validate citation schema
                c = citations[0]
                has_doc_id = "document_id" in c or "doc_id" in c
                has_snippet = "content" in c or "snippet" in c or "text" in c
                if has_doc_id and has_snippet:
                    ok(f"B3: Citations present with valid schema ({len(citations)} citations)")
                else:
                    warn("B3: Citations present but missing fields", str(c)[:100])
            else:
                warn("B3: No citations in response", "may indicate RAG not attaching sources")
    else:
        fail("B3: Chat message failed", str(resp_msg.get("detail",""))[:200],
             fix="Check LLM client, chat service, or RAG pipeline")

    # Cleanup
    if doc_id:
        api("DELETE", f"/documents/{doc_id}", token=token)
    api("DELETE", f"/chat/sessions/{session_id}", token=token)


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO C — Report Generation
# ─────────────────────────────────────────────────────────────────────────────
def scenario_c(token):
    section("SCENARIO C — Report Generation")

    if not token:
        token, _ = login("admin", "admin123!")
        if not token:
            fail("C0: Cannot login for report test")
            return

    # Get templates
    code, resp_tpl, elapsed = api("GET", "/templates?page=1&size=10", token=token)
    if code != 200 or not resp_tpl.get("items"):
        warn("C1: No templates available or template list failed",
             str(resp_tpl.get("detail",""))[:100])
        return
    template = resp_tpl["items"][0]
    ok(f"C1: Templates fetched — using '{template.get('name','?')}' (type={template.get('template_type','?')})")

    # Get existing completed documents
    code, resp_docs, _ = api("GET", "/documents?page=1&size=20&status=completed", token=token)
    doc_ids = []
    if code == 200:
        for d in resp_docs.get("items", []):
            if d.get("status") == "completed":
                doc_ids.append(str(d["id"]))
    if not doc_ids:
        warn("C2: No completed documents for report generation")
        return
    ok(f"C2: Found {len(doc_ids)} completed documents")

    # Create report
    report_payload = {
        "title": "QA 자동 생성 보고서",
        "template_id": str(template["id"]),
        "source_document_ids": doc_ids[:3],
        "user_inputs": {},
    }
    t0 = time.time()
    code, resp_rep, elapsed = api("POST", "/reports", report_payload, token, timeout=10)
    if code not in (200, 201):
        fail("C3: Report creation failed", str(resp_rep.get("detail",""))[:200],
             severity="HIGH", fix="Check report service / Celery worker")
        return
    report_id = resp_rep.get("id")
    ok(f"C3: Report creation triggered (id={str(report_id)[:8]}...)")

    # Poll for completion
    print(f"       Polling report status (max 90s)...", end="", flush=True)
    deadline = time.time() + 90
    final_status = "timeout"
    while time.time() < deadline:
        code2, resp2, _ = api("GET", f"/reports/{report_id}", token=token)
        if code2 == 200:
            s = resp2.get("status", "")
            print(".", end="", flush=True)
            if s == "completed":
                final_status = "completed"
                break
            if s in ("failed", "error"):
                final_status = s
                break
        time.sleep(5)
    print()
    elapsed_total = time.time() - t0
    perf_data.setdefault("POST /reports", []).append(elapsed_total)

    if final_status == "completed":
        if elapsed_total > 30:
            warn(f"C4: Report completed but slow ({elapsed_total:.0f}s > 30s target)")
        else:
            ok(f"C4: Report generation completed ({elapsed_total:.0f}s)")
        # Try download
        req = urllib.request.Request(
            f"{BASE}/reports/{report_id}/download",
            headers={"Authorization": f"Bearer {token}"}
        )
        try:
            r = urllib.request.urlopen(req, timeout=15)
            data = r.read()
            if len(data) > 0:
                ok(f"C5: Report download OK ({len(data)} bytes)")
            else:
                fail("C5: Report download returned 0 bytes", fix="Check report file generation")
        except Exception as e:
            fail("C5: Report download failed", str(e)[:200], fix="Check MinIO / report storage")
    elif final_status == "timeout":
        warn("C4: Report not completed within 90s", "Celery worker may be slow or overloaded")
    else:
        fail(f"C4: Report generation {final_status}", fix="Check Celery worker / LLM call in report generator")


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO D — Access Control
# ─────────────────────────────────────────────────────────────────────────────
def scenario_d(admin_token):
    section("SCENARIO D — Access Control")

    if not admin_token:
        admin_token, _ = login("admin", "admin123!")
        if not admin_token:
            fail("D0: Cannot login as admin")
            return

    # Get org + departments
    code, resp_org, _ = api("GET", "/organizations?page=1&size=5", token=admin_token)
    if code != 200 or not resp_org.get("items"):
        warn("D1: Cannot list organizations", str(resp_org)[:100])
        return
    org_id = resp_org["items"][0]["id"]

    code, resp_depts, _ = api("GET", f"/departments?organization_id={org_id}&page=1&size=20", token=admin_token)
    if code != 200 or len(resp_depts.get("items", [])) < 2:
        warn("D1: Need at least 2 departments for access control test",
             f"found {len(resp_depts.get('items',[]))}")
        return
    dept_a = resp_depts["items"][0]["id"]
    dept_b = resp_depts["items"][1]["id"]
    ok(f"D1: Found depts A={str(dept_a)[:8]}... B={str(dept_b)[:8]}...")

    # Create test user in dept_a
    ts = int(time.time())
    user_a_payload = {
        "username": f"qa_usera_{ts}",
        "email": f"qa_usera_{ts}@test.local",
        "password": "QaTest123!",
        "role": "member",
        "organization_id": str(org_id),
        "department_id": str(dept_a),
    }
    code, resp_ua, _ = api("POST", "/users", user_a_payload, admin_token)
    if code not in (200, 201):
        warn("D2: Could not create test user A", str(resp_ua.get("detail",""))[:100])
        return
    ok(f"D2: Created user A in dept_A")

    # Create test user in dept_b
    user_b_payload = {
        "username": f"qa_userb_{ts}",
        "email": f"qa_userb_{ts}@test.local",
        "password": "QaTest123!",
        "role": "member",
        "organization_id": str(org_id),
        "department_id": str(dept_b),
    }
    code, resp_ub, _ = api("POST", "/users", user_b_payload, admin_token)
    if code not in (200, 201):
        warn("D2: Could not create test user B", str(resp_ub.get("detail",""))[:100])
        return
    ok(f"D2: Created user B in dept_B")

    # Login as user_a
    token_a, _ = login(user_a_payload["username"], user_a_payload["password"])
    token_b, _ = login(user_b_payload["username"], user_b_payload["password"])
    if not token_a or not token_b:
        warn("D3: Could not login as test users")
        return
    ok("D3: Both test users can login")

    # Upload department_only doc as admin into dept_a
    content = b"This is a department-only document for dept_a"
    code, resp_doc, _ = upload_bytes(
        "dept_a_secret.txt", content, "text/plain", admin_token,
        visibility="department_only", department_id=str(dept_a)
    )
    if code not in (200, 201):
        warn("D4: Could not upload department-only document", str(resp_doc.get("detail",""))[:100])
        return
    secret_doc_id = resp_doc.get("id")
    ok(f"D4: Uploaded dept_a department_only doc (id={str(secret_doc_id)[:8]}...)")

    # user_a should see it
    code_a, resp_da, _ = api("GET", f"/documents/{secret_doc_id}", token=token_a)
    if code_a == 200:
        ok("D5: User A (same dept) CAN access department-only document ✓")
    elif code_a == 403:
        warn("D5: User A in same dept got 403 — check dept membership logic")
    else:
        warn(f"D5: Unexpected response for user A: HTTP {code_a}")

    # user_b should NOT see it
    code_b, resp_db, _ = api("GET", f"/documents/{secret_doc_id}", token=token_b)
    if code_b in (403, 404):
        ok(f"D6: User B (diff dept) CANNOT access department-only document ✓ (HTTP {code_b})")
    elif code_b == 200:
        fail("D6: SECURITY ISSUE — User from different dept can see department_only doc!",
             "Access control not enforced", severity="CRITICAL",
             fix="Review document visibility filter in DocumentService.get_document()")
    else:
        warn(f"D6: Unexpected HTTP {code_b} for user B access check")

    # Cleanup
    api("DELETE", f"/documents/{secret_doc_id}", token=admin_token)


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 3 — AI Quality Check
# ─────────────────────────────────────────────────────────────────────────────
def ai_quality_check(token):
    section("LAYER 3 — AI Quality Check")

    if not token:
        token, _ = login("admin", "admin123!")
        if not token:
            fail("AI0: Cannot login for AI quality test")
            return {}

    questions = [
        {
            "id": "Q1",
            "type": "factual",
            "q": "이 프로젝트의 기술 스택은 무엇인가요?",
            "expect_answer": True,
            "keywords": ["FastAPI", "React", "PostgreSQL", "Qdrant", "Python", "Next"],
        },
        {
            "id": "Q2",
            "type": "multi-doc synthesis",
            "q": "최근 회의에서 논의된 주요 안건을 정리해주세요",
            "expect_answer": True,
            "keywords": [],
        },
        {
            "id": "Q3",
            "type": "temporal",
            "q": "2025년도 관련 문서가 있나요?",
            "expect_answer": True,
            "keywords": [],
        },
        {
            "id": "Q4",
            "type": "no-match",
            "q": "화성 탐사 프로젝트에 대해 알려주세요",
            "expect_answer": False,
            "keywords": [],
        },
        {
            "id": "Q5",
            "type": "ambiguous",
            "q": "현황을 알려주세요",
            "expect_answer": True,
            "keywords": [],
        },
    ]

    # Create a single chat session for all questions
    code, sess, _ = api("POST", "/chat/sessions", {"title": "AI Quality QA"}, token)
    if code not in (200, 201):
        fail("AI0: Cannot create chat session for quality check", str(sess.get("detail",""))[:100])
        return {}
    sid = sess.get("id")

    scores = {"relevancy": [], "faithfulness": [], "hallucination_detected": 0}

    for q in questions:
        print(f"\n  {CYAN}[{q['id']}] {q['type'].upper()}: {q['q'][:60]}{RESET}")

        # Search
        t0 = time.time()
        code_s, resp_s, el_s = api("POST", "/search", {"query": q["q"], "limit": 5}, token)
        search_hits = resp_s.get("results", resp_s.get("items", [])) if code_s == 200 else []
        print(f"       Search: HTTP {code_s}, {len(search_hits)} hits ({el_s:.2f}s)")

        # Chat
        t0 = time.time()
        code_c, resp_c, el_c = api(
            "POST", f"/chat/sessions/{sid}/messages",
            {"content": q["q"]}, token, timeout=60
        )
        perf_data.setdefault("POST /chat", []).append(el_c)

        if code_c not in (200, 201):
            fail(f"{q['id']}: Chat failed", str(resp_c.get("detail",""))[:200])
            scores["relevancy"].append(0.0)
            scores["faithfulness"].append(0.0)
            continue

        msg = resp_c.get("message", resp_c)
        answer = msg.get("content", "")
        citations = msg.get("citations", [])

        if not answer:
            fail(f"{q['id']}: Empty answer", fix="Check LLM integration")
            scores["relevancy"].append(0.0)
            scores["faithfulness"].append(0.0)
            continue

        print(f"       Chat: {el_c:.2f}s, {len(answer)} chars, {len(citations)} citations")
        print(f"       Answer: {answer[:120]}...")

        # ── Relevancy scoring ──────────────────────────────────────
        relevancy = 0.5  # default
        if q["expect_answer"]:
            if len(answer) > 30:
                relevancy = 0.7
            if q["keywords"]:
                hits_kw = sum(1 for kw in q["keywords"] if kw.lower() in answer.lower())
                keyword_ratio = hits_kw / len(q["keywords"])
                relevancy = max(relevancy, keyword_ratio)
            if len(answer) > 100:
                relevancy = min(1.0, relevancy + 0.1)
        else:
            # No-match question: ideally model says "I don't know" or gives minimal answer
            negative_phrases = ["모르", "없습", "찾을 수 없", "관련 문서", "정보가 없"]
            if any(p in answer for p in negative_phrases):
                relevancy = 1.0  # correctly declined
            elif len(answer) > 200:
                relevancy = 0.3  # hallucination risk: long answer for no-match
                scores["hallucination_detected"] += 1
                print(f"       {RED}⚠ Possible hallucination: long answer for no-match question{RESET}")
            else:
                relevancy = 0.6

        # ── Faithfulness scoring ───────────────────────────────────
        faithfulness = 0.5
        if search_hits and citations:
            faithfulness = 0.8
        elif not search_hits and not citations:
            if not q["expect_answer"]:
                faithfulness = 0.9  # no docs, no citations — correct
            else:
                faithfulness = 0.4  # expected docs but none found
        elif citations and not search_hits:
            faithfulness = 0.6
        elif search_hits and not citations:
            faithfulness = 0.5  # has context but not cited

        scores["relevancy"].append(relevancy)
        scores["faithfulness"].append(faithfulness)

        rel_icon = "✅" if relevancy >= 0.7 else ("⚠️" if relevancy >= 0.5 else "❌")
        fai_icon = "✅" if faithfulness >= 0.7 else ("⚠️" if faithfulness >= 0.5 else "❌")
        print(f"       Relevancy: {rel_icon} {relevancy:.1f}  |  Faithfulness: {fai_icon} {faithfulness:.1f}")

    # Cleanup session
    api("DELETE", f"/chat/sessions/{sid}", token=token)

    avg_relevancy = sum(scores["relevancy"]) / len(scores["relevancy"]) if scores["relevancy"] else 0
    avg_faithfulness = sum(scores["faithfulness"]) / len(scores["faithfulness"]) if scores["faithfulness"] else 0
    hallucinations = scores["hallucination_detected"]

    print(f"\n  {BOLD}AI Quality Summary:{RESET}")
    print(f"    Avg Relevancy:    {avg_relevancy:.2f} {'✅' if avg_relevancy>=0.7 else '⚠️' if avg_relevancy>=0.5 else '❌'}")
    print(f"    Avg Faithfulness: {avg_faithfulness:.2f} {'✅' if avg_faithfulness>=0.7 else '⚠️' if avg_faithfulness>=0.5 else '❌'}")
    print(f"    Hallucinations:   {hallucinations} {'✅' if hallucinations==0 else '⚠️' if hallucinations<=1 else '❌'}")

    return {
        "relevancy": avg_relevancy,
        "faithfulness": avg_faithfulness,
        "hallucination": hallucinations,
    }


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    qa_start = time.time()
    now = datetime.datetime.now()
    date_str = now.strftime("%Y%m%d_%H%M")

    print(f"\n{BOLD}{'='*55}")
    print("  DocUtil Quick QA — Scenario Tests + AI Quality")
    print(f"  Target: http://192.168.10.39:8040")
    print(f"  Started: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}{RESET}")

    # Run scenarios
    token = scenario_a()
    scenario_b(token)
    scenario_c(token)
    scenario_d(token)
    ai_scores = ai_quality_check(token)

    total_elapsed = time.time() - qa_start

    # ── Score calculation ──────────────────────────────────────────────────
    score = 100
    score -= results["fail"] * 10
    score -= results["warn"] * 3
    if ai_scores:
        if ai_scores.get("relevancy", 1) < 0.7: score -= 5
        if ai_scores.get("faithfulness", 1) < 0.7: score -= 5
        if ai_scores.get("hallucination", 0) > 0: score -= 5
    # Performance penalties
    for ep, times in perf_data.items():
        avg = sum(times) / len(times)
        targets = {"POST /search": 2.0, "POST /chat": 3.0, "POST /reports": 30.0, "POST /auth/login": 2.0}
        target = targets.get(ep, 5.0)
        if avg > target:
            score -= 2
    score = max(0, score)

    # ── Console Summary ────────────────────────────────────────────────────
    section("FINAL SCORE & SUMMARY")
    score_color = GREEN if score >= 80 else (YELLOW if score >= 60 else RED)
    print(f"\n  {BOLD}{score_color}SCORE: {score}/100{RESET}")
    print(f"  Duration: {total_elapsed:.1f}s")
    print(f"  ✅ {results['pass']} passed  |  ⚠️  {results['warn']} warnings  |  ❌ {results['fail']} failed")

    if critical_issues:
        print(f"\n  {BOLD}{RED}Critical Issues:{RESET}")
        for i, issue in enumerate(critical_issues, 1):
            print(f"  {i}. [{issue['severity']}] {issue['msg']}")
            if issue.get("detail"):
                print(f"     Detail: {issue['detail'][:100]}")
            if issue.get("fix"):
                print(f"     Fix: {issue['fix']}")

    if warnings:
        print(f"\n  {BOLD}{YELLOW}Warnings:{RESET}")
        for w in warnings[:5]:
            print(f"  • {w['msg']}" + (f" ({w['detail'][:80]})" if w.get("detail") else ""))
        if len(warnings) > 5:
            print(f"  ... and {len(warnings)-5} more (see report)")

    print(f"\n  {BOLD}Performance:{RESET}")
    targets_map = {"POST /search": 2.0, "POST /chat": 3.0, "POST /reports": 30.0, "POST /auth/login": 2.0}
    for ep, times in sorted(perf_data.items()):
        avg = sum(times) / len(times)
        target = targets_map.get(ep, 5.0)
        icon = "✅" if avg <= target else "⚠️"
        print(f"  {icon} {ep:<30} avg={avg:.2f}s  (target <{target}s, n={len(times)})")

    if ai_scores:
        print(f"\n  {BOLD}AI Quality:{RESET}")
        r = ai_scores.get("relevancy", 0)
        f = ai_scores.get("faithfulness", 0)
        h = ai_scores.get("hallucination", 0)
        print(f"  {'✅' if r>=0.7 else '⚠️'} Relevancy:    {r:.2f}")
        print(f"  {'✅' if f>=0.7 else '⚠️'} Faithfulness: {f:.2f}")
        print(f"  {'✅' if h==0 else '⚠️'} Hallucinations: {h} detected")

    # ── Write report ───────────────────────────────────────────────────────
    os.makedirs(REPORT_DIR, exist_ok=True)
    report_path = os.path.join(REPORT_DIR, f"{date_str}_report.md")

    perf_rows = ""
    for ep, times in sorted(perf_data.items()):
        avg = sum(times) / len(times)
        target = targets_map.get(ep, 5.0)
        icon = "✅" if avg <= target else "⚠️"
        perf_rows += f"| {ep} | {avg:.2f}s | <{target}s | {icon} |\n"

    ai_rows = ""
    if ai_scores:
        r = ai_scores.get("relevancy", 0)
        f = ai_scores.get("faithfulness", 0)
        h = ai_scores.get("hallucination", 0)
        ai_rows = f"""| Relevancy | {r:.2f} | {'✅' if r>=0.7 else '⚠️' if r>=0.5 else '❌'} |
| Faithfulness | {f:.2f} | {'✅' if f>=0.7 else '⚠️' if f>=0.5 else '❌'} |
| Hallucination Detected | {h} | {'✅' if h==0 else '⚠️' if h<=1 else '❌'} |"""

    critical_md = ""
    for i, issue in enumerate(critical_issues, 1):
        critical_md += f"""
### Issue {i}: {issue['msg']}
- **Severity:** {issue['severity']}
- **Detail:** {issue.get('detail','-')}
- **Fix:** {issue.get('fix','-')}
"""

    warn_md = ""
    for w in warnings:
        warn_md += f"- **{w['msg']}**" + (f": {w['detail']}" if w.get("detail") else "") + "\n"

    recommendations = []
    if results["fail"] > 0:
        recommendations.append("1. [CRITICAL] 실패한 시나리오 즉시 수정 후 재테스트")
    if ai_scores and ai_scores.get("relevancy", 1) < 0.7:
        recommendations.append("2. [HIGH] RAG 관련성 개선 — 검색 임계값 및 임베딩 품질 점검")
    if ai_scores and ai_scores.get("hallucination", 0) > 0:
        recommendations.append("3. [HIGH] 환각 방지 강화 — 시스템 프롬프트에 근거 없는 답변 금지 추가")
    for ep, times in perf_data.items():
        avg = sum(times) / len(times)
        target = targets_map.get(ep, 5.0)
        if avg > target:
            recommendations.append(f"4. [MEDIUM] {ep} 응답 시간 최적화 (현재 {avg:.1f}s, 목표 <{target}s)")
    if results["warn"] > 3:
        recommendations.append("5. [LOW] 경고 항목 전반 검토 및 개선")
    if not recommendations:
        recommendations.append("현재 품질 수준 유지 및 정기 회귀 테스트 실행 권장")

    report_content = f"""# DocUtil QA Report
**Date:** {now.strftime('%Y-%m-%d %H:%M:%S')}
**Duration:** {total_elapsed:.1f}s
**Score:** {score}/100
**Target:** http://192.168.10.39:8040

## 요약 (Summary in Korean)
이번 Quick QA는 API 시나리오 테스트(A~D)와 AI 품질 검사로 구성되었습니다.
- 총 **{results['pass']+results['warn']+results['fail']}개** 체크 포인트 실행
- ✅ **{results['pass']}개** 통과, ⚠️ **{results['warn']}개** 경고, ❌ **{results['fail']}개** 실패
- AI 관련성 평균: **{ai_scores.get('relevancy',0):.2f}**, 신뢰도(Faithfulness): **{ai_scores.get('faithfulness',0):.2f}**
- 전체 QA 소요 시간: {total_elapsed:.1f}초

## Summary
- ✅ {results['pass']} passed
- ⚠️ {results['warn']} warnings
- ❌ {results['fail']} failed

## Critical Issues
{critical_md if critical_md else "_No critical issues found_"}

## Warnings
{warn_md if warn_md else "_No warnings_"}

## AI Quality
| Metric | Score | Status |
|--------|-------|--------|
{ai_rows if ai_rows else "| N/A | - | - |"}

## Performance
| Endpoint | Avg Response | Target | Status |
|----------|-------------|--------|--------|
{perf_rows if perf_rows else "| N/A | - | - | - |"}

## Recommendations
{chr(10).join(recommendations)}

---
_Generated by DocUtil QA Runner — Quick Mode (Scenarios A-D + AI Quality)_
"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"\n  {BOLD}Report saved:{RESET} {report_path}")
    print(f"\n{BOLD}{'='*55}{RESET}\n")

    return score


if __name__ == "__main__":
    score = main()
    sys.exit(0 if score >= 80 else 1)
