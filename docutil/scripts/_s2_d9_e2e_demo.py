"""Phase 4 S2 D9 — Mode A → PPTX 다운로드 end-to-end 시연.

시나리오:
    1. 로그인 (admin)
    2. 에이전트 목록 → report agent_id
    3. POST /v2/documents (Mode A, slide_report) → completed 폴링
    4. POST /v2/documents/{id}/export (format=pptx) → job_id
    5. GET /v2/documents/exports/{job_id} 폴링 → completed + download_url
    6. download_url GET 으로 PPTX bytes 획득 → ZIP 시그니처 검증 + 파일 저장
    7. /reports 레거시 호출 0건 확인 (본 세션의 호출 URL 추적)
"""
from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

BASE = "http://192.168.10.39:8040/api/v1"
LOGIN_ID = "admin"
PASSWORD = "admin123!"
OUT_DIR = Path(r"D:\workspace\document_utilization\docs\s2_d9_e2e")
OUT_DIR.mkdir(parents=True, exist_ok=True)
PPTX_PATH = OUT_DIR / f"mode_a_demo_{datetime.now().strftime('%H%M%S')}.pptx"
REPORT = OUT_DIR / "report.md"

log: list[str] = []
called_urls: list[str] = []


def _hdr(url: str) -> None:
    called_urls.append(url)


def _l(msg: str) -> None:
    ts = datetime.now(tz=timezone.utc).astimezone().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    log.append(line)


def main() -> int:
    with httpx.Client(timeout=120.0) as c:
        # 1. 로그인
        _l("=== 1. 로그인 ===")
        url = f"{BASE}/auth/login"; _hdr(url)
        r = c.post(url, json={"username": LOGIN_ID, "password": PASSWORD})
        _l(f"POST /auth/login → {r.status_code}")
        if r.status_code != 200:
            _l(f"FAIL: {r.text[:300]}"); return 1
        token = r.json()["access_token"]
        H = {"Authorization": f"Bearer {token}"}

        # 2. agent
        _l("\n=== 2. 에이전트 조회 ===")
        url = f"{BASE}/agents"; _hdr(url)
        r = c.get(url, headers=H)
        items = r.json() if isinstance(r.json(), list) else r.json().get("items", [])
        agent = next((a for a in items if a.get("agent_type") == "report"), None)
        agent_id = agent["id"] if agent else None
        _l(f"agent_id={agent_id}")

        # 3. POST generate
        _l("\n=== 3. POST /v2/documents (Mode A) ===")
        body = {
            "prompt": "2026년 1분기 매출 실적 요약 — KPI 4종(매출/영업이익/신규고객/이탈률), 카테고리 성장표, 분기 동향 차트 포함",
            "document_type": "slide_report",
            "mode": "free_generation",
        }
        if agent_id:
            body["agent_id"] = agent_id
        url = f"{BASE}/v2/documents"; _hdr(url)
        r = c.post(url, headers=H, json=body)
        _l(f"POST /v2/documents → {r.status_code}")
        if r.status_code not in (200, 201, 202):
            _l(f"FAIL: {r.text[:400]}"); return 2
        doc = r.json()
        doc_id = doc.get("id") or doc.get("document_id")
        _l(f"document_id={doc_id}, status={doc.get('status')}")

        # 4. 폴링 (생성 완료)
        _l("\n=== 4. 생성 완료 폴링 ===")
        for i in range(20):
            time.sleep(3)
            url = f"{BASE}/v2/documents/{doc_id}"; _hdr(url)
            r = c.get(url, headers=H)
            if r.status_code != 200:
                continue
            st = r.json().get("status")
            _l(f"[{i+1:02d}] status={st}")
            if st in ("completed", "failed"):
                if st != "completed":
                    _l("FAIL: 생성 실패"); return 3
                break
        else:
            _l("TIMEOUT"); return 4

        pages = r.json().get("document_schema", {}).get("pages", [])
        _l(f"생성 완료: 페이지 {len(pages)}개")

        # 5. export 요청
        _l("\n=== 5. POST /v2/documents/{id}/export?format=pptx ===")
        url = f"{BASE}/v2/documents/{doc_id}/export"; _hdr(url)
        r = c.post(url, headers=H, json={"format": "pptx"})
        _l(f"POST export → {r.status_code}")
        if r.status_code not in (200, 202):
            _l(f"FAIL: {r.text[:400]}"); return 5
        job = r.json()
        job_id = job.get("job_id") or job.get("jobId")
        _l(f"job_id={job_id}")

        # 6. export 상태 폴링
        _l("\n=== 6. export 상태 폴링 ===")
        download_url = None
        for i in range(30):
            time.sleep(2)
            url = f"{BASE}/v2/documents/exports/{job_id}"; _hdr(url)
            r = c.get(url, headers=H)
            if r.status_code != 200:
                _l(f"[{i+1:02d}] GET status {r.status_code}: {r.text[:150]}"); continue
            data = r.json()
            st = data.get("status")
            prog = data.get("progress")
            _l(f"[{i+1:02d}] status={st} progress={prog}")
            if st == "completed":
                download_url = data.get("download_url")
                break
            if st == "failed":
                _l(f"FAIL: {data.get('error')}"); return 6
        else:
            _l("TIMEOUT export 폴링"); return 7

        if not download_url:
            _l("FAIL: download_url 없음"); return 8
        _l(f"download_url={download_url[:120]}...")

        # 7. 파일 다운로드 — 운영 환경 MINIO_ENDPOINT 가 Docker 내부 hostname(`minio:9000`) 이라
        #    presigned URL 을 외부에서 직접 못 연다. SSH → docker exec 우회로 시연 완료 증빙.
        #    (운영 fix: D10 Watch 에 API 프록시 엔드포인트 추가 또는 MINIO_ENDPOINT 외부 주소화)
        # 7. 파일 다운로드 — S2 D10 W4 해소: API 프록시 엔드포인트로 직접 스트리밍
        _l("\n=== 7. API 프록시 다운로드 ===")
        dl_url = f"{BASE}{download_url}" if download_url.startswith("/api/v1") else download_url
        # BASE 가 이미 /api/v1 포함이면 중복 제거
        if dl_url.count("/api/v1") > 1:
            dl_url = dl_url.replace("/api/v1/api/v1", "/api/v1", 1)
        _hdr(dl_url)
        r = c.get(dl_url, headers=H)
        _l(f"GET {dl_url[-80:]} → {r.status_code}, {len(r.content)} bytes")
        if r.status_code != 200:
            _l(f"FAIL: {r.text[:200]}"); return 9
        content = r.content
        sig_ok = content[:2] == b"PK"
        PPTX_PATH.write_bytes(content)
        _l(f"ZIP 시그니처: {sig_ok}")
        _l(f"저장: {PPTX_PATH} ({len(content)} bytes)")
        r_content_len = len(content)

        # 8. /reports 레거시 호출 0건 검증
        _l("\n=== 8. /reports 레거시 호출 검증 ===")
        legacy_calls = [u for u in called_urls if "/reports" in u and "/v2/" not in u]
        _l(f"/reports 호출 건수: {len(legacy_calls)}")
        if legacy_calls:
            for u in legacy_calls:
                _l(f"  - {u}")

        # 요약
        _l("\n=== 요약 ===")
        _l(f"- document_id: {doc_id}")
        _l(f"- job_id: {job_id}")
        _l(f"- 페이지 수: {len(pages)}")
        _l(f"- PPTX 크기: {r_content_len / 1024:.1f}KB")
        _l(f"- ZIP 시그니처: {sig_ok}")
        _l(f"- 총 API 호출: {len(called_urls)} (레거시 {len(legacy_calls)})")

        return 0 if sig_ok and not legacy_calls else 10


if __name__ == "__main__":
    rc = 99
    try:
        rc = main()
    except Exception as e:  # noqa: BLE001
        _l(f"FATAL: {e!r}")
        rc = 99
    finally:
        now = datetime.now(tz=timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
        body = (
            "# Phase 4 S2 D9 E2E 시연 결과\n\n"
            f"- 실행 시각: {now}\n"
            f"- 대상: http://192.168.10.39:8040\n"
            f"- exit_code: {rc}\n"
            f"- 생성 PPTX: `{PPTX_PATH.name}`\n\n"
            "## 호출된 URL 목록 (중복 포함)\n\n```\n"
            + "\n".join(called_urls[:50]) + f"\n... (총 {len(called_urls)}건)\n```\n\n"
            "## 실행 로그\n\n```\n" + "\n".join(log) + "\n```\n"
        )
        REPORT.write_text(body, encoding="utf-8")
        print(f"\n[리포트] {REPORT}")
    sys.exit(rc)
