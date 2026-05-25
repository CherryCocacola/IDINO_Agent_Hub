"""트랙 #106 P0 — DocumentSchema ValidationError ~50% 해소 검증 (closed-loop).

목적:
  schemas.py field_validator(mode="before") padding/truncate + service.py 1회
  자동 재시도 + constants.py prompt 강화 적용 후, DocUtil documents_v2 의
  POST /v2/documents 성공률이 ≥95% 인지 검증.

방법 (직접 API 호출, 브라우저 미사용 — 더 빠르고 신뢰성 높음):
  1. POST /api/v1/auth/login → access_token 획득
  2. 10 회 반복 POST /api/v1/v2/documents (다양한 prompt × document_type)
  3. 응답 status 분류: 200/201/202 (성공) vs 422 (ValidationError) vs 5xx
  4. 성공률 ≥95% 면 PASS, 아니면 FAIL + 실패 사유 캡처

비용 산정 (gpt-4o):
  - 정상: 10 회 × ~$0.0003 ≈ $0.003
  - 재시도 발생 시: 최대 2배 ≈ $0.006
"""
from __future__ import annotations

import io
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OUT_DIR = Path(__file__).parent
RESULT_PATH = OUT_DIR / "track106_p0_validation_loop_results.json"

DOCUTIL = "http://192.168.10.39:8041"
EMAIL = "admin@example.com"
PWD = "Admin123!"

REPEAT_COUNT = int(os.environ.get("E2E_REPEAT", "10"))

# 다양한 prompt × document_type 으로 회귀 검증.
# proposal/one_pager 는 ExecutiveSummary (min_length=3) 회귀 핵심.
# slide_report/docx_report 는 IconRow/ImageGrid/ThreeColumn 회귀 가능.
TEST_CASES = [
    ("proposal", "신규 SaaS 구독 모델 도입 제안서. 시장 분석, 경쟁사 비교, 예상 ROI 포함."),
    ("one_pager", "2026 1분기 매출 요약. 핵심 KPI 와 다음 분기 계획 한 페이지로."),
    ("proposal", "데이터 보안 강화 위한 SOC 2 인증 추진 계획서. 리스크 분석 필수."),
    ("slide_report", "AI 트렌드 발표 자료 5 페이지. ChatGPT Claude Gemini 비교."),
    ("minutes", "2026-05-25 임원 회의록. 참석자 CEO CTO CFO. 액션 아이템 3 개."),
    ("docx_report", "원격근무 정책 도입 효과 분석. 생산성 비용 직원 만족도 측정."),
    ("weekly_status", "이번 주 백엔드 팀 주간 업무 보고. 완료 진행중 다음 주 계획."),
    ("proposal", "신입 개발자 교육 6 개월 커리큘럼 제안. 단계별 목표 명시."),
    ("one_pager", "고객 NPS 점수 개선 캠페인 결과 요약 1 페이지."),
    ("freeform_doc", "회사 비전 2030 — 5년 후 모습 한 페이지 정리."),
]


def main() -> int:
    results: dict = {
        "timestamp": datetime.now().isoformat(),
        "repeat_count": REPEAT_COUNT,
        "iterations": [],
        "summary": {},
    }

    # 1) 로그인 → access_token
    with httpx.Client(base_url=DOCUTIL, timeout=30.0) as client:
        try:
            r = client.post(
                "/api/v1/auth/login",
                json={"username": EMAIL, "password": PWD},
            )
            r.raise_for_status()
            data = r.json()
            token = data["access_token"]
            print(f"[LOGIN OK] token_len={len(token)}", flush=True)
        except Exception as e:
            print(f"[LOGIN FAIL] {e}", flush=True)
            results["summary"] = {"status": "LOGIN_FAIL", "error": str(e)}
            RESULT_PATH.write_text(
                json.dumps(results, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )
            return 1

    # 2) 10 회 반복 — 각 호출은 별도 httpx.Client (timeout 120s, LLM 호출 + 재시도 1회 고려)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # AgentHub 사용자당 1 RPM 제한 — 각 iteration 사이 65초 sleep 필수.
    # 환경변수 SKIP_RATE_LIMIT=1 면 sleep 생략 (이미 분산되어 호출되는 경우).
    inter_sleep = int(os.environ.get("INTER_ITER_SLEEP_SEC", "65"))

    for i in range(REPEAT_COUNT):
        if i > 0 and inter_sleep > 0:
            print(f"  ... sleeping {inter_sleep}s to avoid AgentHub rate limit ...", flush=True)
            time.sleep(inter_sleep)

        doc_type, prompt = TEST_CASES[i % len(TEST_CASES)]
        iteration_start = time.time()

        try:
            with httpx.Client(base_url=DOCUTIL, timeout=180.0) as client:
                r = client.post(
                    "/api/v1/v2/documents",
                    headers=headers,
                    json={
                        "mode": "free_generation",
                        "document_type": doc_type,
                        "prompt": prompt,
                    },
                )
            elapsed = int((time.time() - iteration_start) * 1000)
            status = r.status_code
            body = r.text[:2000]
            is_success = 200 <= status < 300
            detail = None
            if not is_success:
                try:
                    bj = r.json()
                    detail = bj.get("detail") or bj.get("message") or body[:300]
                except Exception:
                    detail = body[:300]

            entry = {
                "iter": i + 1,
                "doc_type": doc_type,
                "prompt": prompt[:80],
                "status": status,
                "elapsed_ms": elapsed,
                "success": is_success,
                "detail": detail,
            }
            results["iterations"].append(entry)
            marker = "PASS" if is_success else "FAIL"
            line = f"[{i+1:02d}/{REPEAT_COUNT}] {marker} type={doc_type:<14} status={status} elapsed={elapsed}ms"
            if detail:
                line += f" detail={str(detail)[:180]}"
            print(line, flush=True)
        except httpx.TimeoutException as e:
            elapsed = int((time.time() - iteration_start) * 1000)
            entry = {
                "iter": i + 1,
                "doc_type": doc_type,
                "prompt": prompt[:80],
                "status": -1,
                "elapsed_ms": elapsed,
                "success": False,
                "detail": f"timeout: {e}",
            }
            results["iterations"].append(entry)
            print(f"[{i+1:02d}/{REPEAT_COUNT}] TIMEOUT elapsed={elapsed}ms", flush=True)
        except Exception as e:
            elapsed = int((time.time() - iteration_start) * 1000)
            entry = {
                "iter": i + 1,
                "doc_type": doc_type,
                "prompt": prompt[:80],
                "status": -2,
                "elapsed_ms": elapsed,
                "success": False,
                "detail": f"exception: {e}",
            }
            results["iterations"].append(entry)
            print(f"[{i+1:02d}/{REPEAT_COUNT}] EXCEPTION {e}", flush=True)

    # 3) 요약
    total = len(results["iterations"])
    passed = sum(1 for x in results["iterations"] if x["success"])
    success_rate = (passed / total * 100) if total else 0.0
    results["summary"] = {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "success_rate_pct": round(success_rate, 1),
        "verdict": "PASS" if success_rate >= 95.0 else "FAIL",
        "failure_details": [
            {"iter": x["iter"], "doc_type": x["doc_type"], "status": x["status"], "detail": x["detail"]}
            for x in results["iterations"]
            if not x["success"]
        ],
    }

    RESULT_PATH.write_text(
        json.dumps(results, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    print()
    print("=" * 70)
    print(f"결과: {passed}/{total} PASS  ({success_rate:.1f}%)")
    print(f"판정: {results['summary']['verdict']}  (목표: ≥95.0%)")
    if results["summary"]["failure_details"]:
        print(f"실패 케이스 ({len(results['summary']['failure_details'])} 건):")
        for f in results["summary"]["failure_details"]:
            print(f"  - iter={f['iter']} type={f['doc_type']} status={f['status']}")
            if f.get("detail"):
                print(f"    detail: {str(f['detail'])[:250]}")
    print("=" * 70)
    print(f"결과 파일: {RESULT_PATH}")

    return 0 if success_rate >= 95.0 else 2


if __name__ == "__main__":
    sys.exit(main())
