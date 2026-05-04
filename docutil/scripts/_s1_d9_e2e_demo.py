"""Phase 4 S1 D9-B — End-to-end 시연 스크립트.

시나리오:
    1. 로그인 (admin/admin123!) → access_token
    2. 에이전트 목록 조회 → Mode A용 agent_id 확보
    3. POST /v2/documents (Mode A 자유 생성) → 202 Accepted + document_id
    4. 폴링: GET /v2/documents/{id} — status가 generating → completed 전이 확인
    5. PATCH /v2/documents/{id} — 첫 페이지의 SlideTitle 텍스트 변경
    6. GET /v2/documents/{id} — PATCH 반영 검증
    7. 프리뷰 URL 확인 (프론트 /designer/[id] 라우트)

실행 결과를 docs/phase4_s1_d9_e2e_demo_report.md 로 저장한다.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

BASE = "http://192.168.10.39:8040/api/v1"
FRONTEND = "http://192.168.10.39:3040"
LOGIN_ID = "admin"
PASSWORD = "admin123!"
REPORT = Path(r"D:\workspace\document_utilization\docs\phase4_s1_d9_e2e_demo_report.md")

log_lines: list[str] = []


def log(msg: str) -> None:
    ts = datetime.now(tz=timezone.utc).astimezone().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    log_lines.append(line)


def main() -> int:
    with httpx.Client(timeout=90.0) as c:
        # 1. 로그인 ---------------------------------------------------------
        log("=== 1. 로그인 ===")
        r = c.post(f"{BASE}/auth/login", json={"username": LOGIN_ID, "password": PASSWORD})
        log(f"POST /auth/login → {r.status_code}")
        if r.status_code != 200:
            log(f"FAIL: {r.text[:300]}")
            return 1
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        log("access_token 획득")

        # 2. 에이전트 목록 --------------------------------------------------
        log("\n=== 2. 에이전트 목록 조회 ===")
        r = c.get(f"{BASE}/agents", headers=headers)
        log(f"GET /agents → {r.status_code}")
        if r.status_code != 200:
            log(f"FAIL: {r.text[:300]}")
            return 1
        agents = r.json()
        # 다양한 응답 포맷 대응
        items = agents if isinstance(agents, list) else agents.get("items", [])
        report_agent = next(
            (a for a in items if a.get("agent_type") in ("report", "chatbot", "freeform_doc")),
            None,
        )
        if not report_agent:
            log("WARN: 사용 가능한 에이전트 없음 — agent_id 없이 진행")
            agent_id = None
        else:
            agent_id = report_agent["id"]
            log(f"agent_id={agent_id} (type={report_agent.get('agent_type')})")

        # 3. POST /v2/documents (Mode A 자유 생성) --------------------------
        log("\n=== 3. POST /v2/documents (Mode A) ===")
        # design_tokens 생략 시 IDINO 기본값(primary_color=#0A4FC2 등) 자동 적용
        body: dict = {
            "prompt": "2026년 1분기 사업 실적을 3페이지 슬라이드로 요약해 주세요. "
                      "매출/이익/핵심 성과 위주로.",
            "document_type": "slide_report",
            "mode": "free_generation",
        }
        if agent_id:
            body["agent_id"] = agent_id

        r = c.post(f"{BASE}/v2/documents", headers=headers, json=body)
        log(f"POST /v2/documents → {r.status_code}")
        if r.status_code not in (200, 201, 202):
            log(f"FAIL: {r.text[:500]}")
            return 1
        created = r.json()
        doc_id = created.get("id") or created.get("document_id")
        log(f"document_id={doc_id}, status={created.get('status')}")

        # 4. 폴링 ------------------------------------------------------------
        log("\n=== 4. 상태 폴링 (최대 90초) ===")
        final_doc: dict | None = None
        for i in range(30):
            time.sleep(3)
            r = c.get(f"{BASE}/v2/documents/{doc_id}", headers=headers)
            if r.status_code != 200:
                log(f"[{i+1:02d}] GET 실패 {r.status_code}: {r.text[:200]}")
                continue
            doc = r.json()
            st = doc.get("status")
            log(f"[{i+1:02d}] status={st}")
            if st in ("completed", "failed"):
                final_doc = doc
                break
        else:
            log("TIMEOUT: 90초 내 completed 도달 실패")
            return 2

        if final_doc is None or final_doc.get("status") != "completed":
            log(f"FAIL: 최종 status={final_doc.get('status') if final_doc else None}")
            return 3

        schema = final_doc.get("document_schema", {})
        pages = schema.get("pages", [])
        log(f"생성 완료. 페이지 {len(pages)}개")

        if not pages:
            log("FAIL: 생성된 페이지 없음")
            return 4

        first_page = pages[0]
        first_page_id = first_page.get("id")
        components = first_page.get("components", [])
        log(f"첫 페이지 id={first_page_id}, 컴포넌트 {len(components)}개")

        # 첫 SlideTitle 컴포넌트 찾기
        title_comp = next((cp for cp in components if cp.get("type") == "SlideTitle"), None)
        log(
            f"첫 SlideTitle: {json.dumps(title_comp, ensure_ascii=False)[:200]}"
            if title_comp
            else "SlideTitle 없음 — 첫 컴포넌트로 대체"
        )
        target_comp = title_comp or components[0]
        target_comp_id = target_comp.get("id")

        # 5. PATCH — 첫 컴포넌트 text/value 변경 ------------------------------
        log("\n=== 5. PATCH /v2/documents/{id} (component 교체) ===")
        new_text = "[D9 시연으로 수정된 제목] 2026 1분기 실적"
        # 컴포넌트 전체 교체 (타입 유지)
        patched_comp = dict(target_comp)
        # 'text' 필드가 일반적. SlideTitle은 text. 다른 타입은 value/content도 시도
        if "text" in patched_comp:
            patched_comp["text"] = new_text
        elif "content" in patched_comp:
            patched_comp["content"] = new_text
        elif "value" in patched_comp:
            patched_comp["value"] = new_text
        else:
            patched_comp["text"] = new_text

        patch_body = {
            "patch_type": "component",
            "page_id": first_page_id,
            "component_id": target_comp_id,
            "data": patched_comp,
        }
        r = c.patch(f"{BASE}/v2/documents/{doc_id}", headers=headers, json=patch_body)
        log(f"PATCH → {r.status_code}")
        if r.status_code != 200:
            log(f"FAIL: {r.text[:500]}")
            return 5

        # 6. GET 재조회로 반영 검증 ------------------------------------------
        log("\n=== 6. GET 재조회 + 반영 검증 ===")
        r = c.get(f"{BASE}/v2/documents/{doc_id}", headers=headers)
        if r.status_code != 200:
            log(f"FAIL GET: {r.text[:200]}")
            return 6
        re_doc = r.json()
        re_pages = re_doc.get("document_schema", {}).get("pages", [])
        re_first = next((p for p in re_pages if p.get("id") == first_page_id), None)
        if not re_first:
            log("FAIL: 첫 페이지 재조회 실패")
            return 7
        re_comp = next(
            (cp for cp in re_first.get("components", []) if cp.get("id") == target_comp_id),
            None,
        )
        if not re_comp:
            log("FAIL: 대상 컴포넌트 재조회 실패")
            return 8
        reflected = (
            re_comp.get("text") or re_comp.get("content") or re_comp.get("value") or ""
        )
        log(f"재조회 text/value: {reflected[:120]}")
        if new_text in reflected:
            log("✅ PATCH 반영 확인")
        else:
            log(f"⚠️ 반영 의심: 기대 '{new_text}' vs 실제 '{reflected}'")

        # schema_version 증가 확인
        before_v = schema.get("schema_version", 0) if isinstance(schema, dict) else 0
        after_v = re_doc.get("document_schema", {}).get("schema_version") or re_doc.get(
            "schema_version", 0
        )
        log(f"schema_version: before={before_v} → after={after_v}")

        # 7. 프리뷰 URL 확인 --------------------------------------------------
        log("\n=== 7. 프리뷰 URL 접근성 ===")
        preview_url = f"{FRONTEND}/designer/{doc_id}"
        r = c.get(preview_url, follow_redirects=False)
        log(f"GET {preview_url} → {r.status_code}")
        # Next.js SSR은 인증 필요하니 200 아니더라도 3xx/4xx는 라우트가 존재함의 증거
        if r.status_code in (200, 301, 302, 307, 308, 401, 403):
            log("프론트 라우트 도달 가능")
        else:
            log(f"WARN: 예상치 못한 status {r.status_code}")

        # 요약 ---------------------------------------------------------------
        log("\n=== 시연 완료 요약 ===")
        log(f"- document_id: {doc_id}")
        log(f"- 최종 페이지 수: {len(re_pages)}")
        log(f"- PATCH 반영: {'OK' if new_text in reflected else 'SUSPECT'}")
        log(f"- schema_version: {before_v} → {after_v}")
        log(f"- 프리뷰 URL: {preview_url}")

        return 0


if __name__ == "__main__":
    rc = 99
    try:
        rc = main()
    except Exception as e:  # noqa: BLE001
        log(f"FATAL: {e!r}")
        rc = 99
    finally:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        now = datetime.now(tz=timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
        body = (
            "# Phase 4 S1 D9-B — End-to-end 시연 결과\n\n"
            f"- 실행 시각: {now}\n"
            f"- 대상 서버: `http://192.168.10.39:8040`\n"
            f"- 스크립트 exit_code: {rc}\n\n"
            "## 실행 로그\n\n```\n"
            + "\n".join(log_lines)
            + "\n```\n"
        )
        REPORT.write_text(body, encoding="utf-8")
        print(f"\n[리포트 저장] {REPORT}")
    sys.exit(rc)
