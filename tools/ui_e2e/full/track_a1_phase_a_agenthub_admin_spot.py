"""트랙 A1 Phase A — AgentHub 13 admin/docutil-* 화면 회귀 spot check.

목적:
- Phase 10.1a~10.2e 에서 신설된 13 Vue 화면이 운영에서 정상 동작하는지 확인.
- 4 계정 × 13 핵심 GET endpoint = 52 cell.
- 결함 발견 시 Phase A.2 fix 로 진입.

대상 매트릭스:
  계정 (4):
    1. SuperAdmin (admin@example.com)              role=Admin,SuperAdmin -> 200 expected
    2. UserLegacy (user@example.com)               role=User             -> 403 expected
    3. EmployeeHslee (hslee@idino.co.kr)           role=User             -> 403 expected
    4. EmployeeShbaek (shbaek@idino.co.kr)         role=Admin            -> 200 expected
  화면 × 핵심 GET endpoint (13):
    13 admin/docutil-* 라우트 각각의 핵심 list endpoint

판정:
  Admin role 계정 (SuperAdmin, Shbaek): status 200 = PASS, 그 외 = FAIL
  User role 계정 (UserLegacy, Hslee): status 401/403 = PASS (정상 거부), 200/5xx = FAIL

산출:
  user_mig/track_a1_phase_a_results.json — raw 호출 결과 + 판정
  user_mig/track_a1_phase_a_summary.md — PASS/FAIL 요약
"""
from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

import paramiko

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# 운영 서버 SSH (트랙 #105 패턴 재사용)
HOST, USER, PWD = "192.168.10.39", "idino", "dkdlelsh@12"
AGENTHUB_BASE = "http://192.168.10.39:64005"  # AgentHub Vue SPA + Web API

ROOT = Path(__file__).resolve().parents[3]
RESULTS_PATH = ROOT / "user_mig" / "track_a1_phase_a_results.json"
SUMMARY_PATH = ROOT / "user_mig" / "track_a1_phase_a_summary.md"

# 4 계정 명세 (트랙 #105 Phase B.4 검증된 계정만)
ACCOUNTS = [
    {"label": "SuperAdmin", "email": "admin@example.com", "pwd": "Admin123!",
     "agenthub_role": "Admin,SuperAdmin", "expect_admin_access": True},
    {"label": "UserLegacy", "email": "user@example.com", "pwd": "Admin123!",
     "agenthub_role": "User", "expect_admin_access": False},
    {"label": "EmployeeHslee", "email": "hslee@idino.co.kr", "pwd": "Admin123!",
     "agenthub_role": "User", "expect_admin_access": False},
    {"label": "EmployeeShbaek", "email": "shbaek@idino.co.kr", "pwd": "Admin123!",
     "agenthub_role": "Admin", "expect_admin_access": True},
]

# 13 admin/docutil-* 화면 × 핵심 GET endpoint (page load 직후 호출되는 list/initial fetch)
SCREENS = [
    {"route": "/admin/docutil-users",         "endpoint": "/api/admin/docutil/users"},
    {"route": "/admin/docutil-departments",   "endpoint": "/api/admin/docutil/departments"},
    {"route": "/admin/docutil-projects",      "endpoint": "/api/admin/docutil/projects"},
    {"route": "/admin/docutil-dashboard",     "endpoint": "/api/admin/docutil/dashboard/metrics"},
    {"route": "/admin/docutil-audit",         "endpoint": "/api/admin/docutil/audit-logs"},
    {"route": "/admin/docutil-search-scopes", "endpoint": "/api/admin/docutil/search-scopes"},
    {"route": "/admin/docutil-evaluation",    "endpoint": "/api/admin/docutil/evaluation/config"},
    {"route": "/admin/docutil-faq",           "endpoint": "/api/admin/docutil/faq"},
    {"route": "/admin/docutil-reports",       "endpoint": "/api/admin/docutil/reports"},
    {"route": "/admin/docutil-templates",     "endpoint": "/api/admin/docutil/templates"},
    {"route": "/admin/docutil-api-keys",      "endpoint": "/api/admin/docutil/api-keys"},
    {"route": "/admin/docutil-doc-agents",    "endpoint": "/api/admin/docutil/agents"},
    {"route": "/admin/docutil-documents-v2",  "endpoint": "/api/admin/docutil/documents-v2"},
]


def ssh_connect() -> paramiko.SSHClient:
    """운영 서버 SSH 연결 — 운영 nginx 경유로 호출하기 위함."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PWD, timeout=30)
    return client


def run_remote(ssh: paramiko.SSHClient, cmd: str, timeout: int = 60) -> str:
    """원격 명령 실행 후 stdout 반환 (utf-8 안전)."""
    _, stdout, _ = ssh.exec_command(cmd, timeout=timeout)
    return stdout.read().decode("utf-8", "replace")


def login_agenthub(ssh: paramiko.SSHClient, email: str, password: str) -> str:
    """AgentHub /api/auth/login 호출 후 token 추출."""
    body = json.dumps({"email": email, "password": password})
    # 작은따옴표 escape — body 안에는 작은따옴표가 없음 (안전)
    run_remote(
        ssh,
        f"curl -ksS -m 10 -X POST -H 'Content-Type: application/json' "
        f"-d '{body}' {AGENTHUB_BASE}/api/auth/login -o /tmp/login_ah_a1.json",
        timeout=15,
    )
    raw = run_remote(ssh, "cat /tmp/login_ah_a1.json", timeout=5)
    try:
        data = json.loads(raw)
        # AgentHub 응답 키 다양성 대응
        return data.get("token") or data.get("accessToken") or data.get("access_token") or ""
    except json.JSONDecodeError:
        return ""


def call_endpoint(
    ssh: paramiko.SSHClient, token: str, endpoint: str
) -> tuple[int, str]:
    """endpoint 를 GET 호출 후 (status, body 200char) 반환."""
    auth_header = f"-H 'Authorization: Bearer {token}'" if token else ""
    cmd = (
        f"curl -ksS -m 15 -o /tmp/resp_a1.txt -w '%{{http_code}}' "
        f"{auth_header} {AGENTHUB_BASE}{endpoint}"
    )
    status_raw = run_remote(ssh, cmd, timeout=20).strip()
    try:
        status = int(status_raw)
    except ValueError:
        status = 0
    body = run_remote(ssh, "head -c 200 /tmp/resp_a1.txt", timeout=5)
    return status, body.replace("\n", " ").replace("\r", " ")[:200]


def judge_pass(
    expect_admin_access: bool, status: int
) -> tuple[str, str]:
    """판정 — (verdict, reason)."""
    if expect_admin_access:
        # Admin role 기대 → 200 = PASS
        if status == 200:
            return ("PASS", "Admin 접근 정상 (200)")
        if status in (401, 403):
            return ("FAIL", f"Admin 접근 거부됨 (status={status}) — 인증/권한 결함")
        if 500 <= status < 600:
            return ("FAIL", f"서버 오류 (status={status}) — BFF 또는 DocUtil 위임 결함")
        return ("FAIL", f"예상 외 status={status}")
    else:
        # User role 기대 → 401/403 = PASS (정상 거부)
        if status in (401, 403):
            return ("PASS", f"정상 거부됨 (status={status})")
        if status == 200:
            return ("FAIL", "비-Admin 이 admin endpoint 접근 성공 — 권한 우회 결함")
        if 500 <= status < 600:
            return ("FAIL", f"서버 오류 (status={status}) — 권한 검사 전 5xx 발생")
        return ("FAIL", f"예상 외 status={status}")


def main() -> None:
    print(f"[track A1 Phase A] AgentHub 13 admin/docutil-* spot check")
    print(f"[base] {AGENTHUB_BASE}")
    print(f"[matrix] {len(ACCOUNTS)} 계정 × {len(SCREENS)} 화면 = {len(ACCOUNTS) * len(SCREENS)} cell")
    print()

    ssh = ssh_connect()
    try:
        # 1) 각 계정 로그인 → token 확보
        tokens: dict[str, str] = {}
        for acc in ACCOUNTS:
            print(f"  [login] {acc['label']:<16} ({acc['email']}) ...", end="", flush=True)
            token = login_agenthub(ssh, acc["email"], acc["pwd"])
            tokens[acc["label"]] = token
            print(f" {'OK' if token else 'FAIL'} (token len={len(token)})")

        # 2) 매트릭스 호출
        print()
        results: list[dict] = []
        for acc in ACCOUNTS:
            token = tokens.get(acc["label"], "")
            if not token:
                # 로그인 실패 → 13 화면 모두 SKIP
                for screen in SCREENS:
                    results.append({
                        "account": acc["label"],
                        "expect_admin_access": acc["expect_admin_access"],
                        "route": screen["route"],
                        "endpoint": screen["endpoint"],
                        "status": 0,
                        "body_head": "(login failed)",
                        "verdict": "SKIP",
                        "reason": "로그인 실패로 호출 불가",
                    })
                continue
            for screen in SCREENS:
                status, body = call_endpoint(ssh, token, screen["endpoint"])
                verdict, reason = judge_pass(acc["expect_admin_access"], status)
                results.append({
                    "account": acc["label"],
                    "expect_admin_access": acc["expect_admin_access"],
                    "route": screen["route"],
                    "endpoint": screen["endpoint"],
                    "status": status,
                    "body_head": body,
                    "verdict": verdict,
                    "reason": reason,
                })
                tag = "PASS" if verdict == "PASS" else ("SKIP" if verdict == "SKIP" else "FAIL")
                print(f"  [{tag}] {acc['label']:<16} {screen['endpoint']:<55} {status} — {reason}")

        # 3) 결과 저장
        RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        out = {
            "track": "A1 Phase A — AgentHub 13 admin/docutil-* spot check",
            "ran_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "base_url": AGENTHUB_BASE,
            "accounts": [
                {"label": a["label"], "agenthub_role": a["agenthub_role"],
                 "expect_admin_access": a["expect_admin_access"]}
                for a in ACCOUNTS
            ],
            "screens": SCREENS,
            "results": results,
            "summary": {
                "total": len(results),
                "pass": sum(1 for r in results if r["verdict"] == "PASS"),
                "fail": sum(1 for r in results if r["verdict"] == "FAIL"),
                "skip": sum(1 for r in results if r["verdict"] == "SKIP"),
            },
        }
        RESULTS_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print()
        print(f"[saved] {RESULTS_PATH}")
        print(f"[summary] PASS={out['summary']['pass']} / FAIL={out['summary']['fail']} / SKIP={out['summary']['skip']} / TOTAL={out['summary']['total']}")

        # 4) 요약 md 생성
        md_lines: list[str] = [
            "# 트랙 A1 Phase A — AgentHub 13 admin/docutil-* 회귀 spot check",
            "",
            f"- 실행일시: {out['ran_at']}",
            f"- base: {AGENTHUB_BASE}",
            f"- 매트릭스: {len(ACCOUNTS)} 계정 × {len(SCREENS)} 화면 = **{len(results)} cell**",
            f"- 결과: **PASS {out['summary']['pass']} / FAIL {out['summary']['fail']} / SKIP {out['summary']['skip']}**",
            "",
            "## 계정별 요약",
            "",
            "| 계정 | role | expected | PASS | FAIL | SKIP |",
            "|---|---|---|---:|---:|---:|",
        ]
        for acc in ACCOUNTS:
            account_results = [r for r in results if r["account"] == acc["label"]]
            ap = sum(1 for r in account_results if r["verdict"] == "PASS")
            af = sum(1 for r in account_results if r["verdict"] == "FAIL")
            askip = sum(1 for r in account_results if r["verdict"] == "SKIP")
            md_lines.append(
                f"| {acc['label']} | {acc['agenthub_role']} | "
                f"{'200' if acc['expect_admin_access'] else '401/403'} | {ap} | {af} | {askip} |"
            )

        # FAIL 상세
        fail_results = [r for r in results if r["verdict"] == "FAIL"]
        if fail_results:
            md_lines += ["", "## FAIL 상세", "",
                         "| 계정 | route | endpoint | status | reason | body head |",
                         "|---|---|---|---:|---|---|"]
            for r in fail_results:
                body_safe = r["body_head"].replace("|", "\\|")[:100]
                md_lines.append(
                    f"| {r['account']} | `{r['route']}` | `{r['endpoint']}` | {r['status']} | "
                    f"{r['reason']} | `{body_safe}` |"
                )
        else:
            md_lines += ["", "## FAIL 없음 — 전 매트릭스 PASS", ""]

        SUMMARY_PATH.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
        print(f"[saved] {SUMMARY_PATH}")

    finally:
        ssh.close()


if __name__ == "__main__":
    main()
