"""트랙 #105 Phase B.4 — 5계정 × 전체 GET endpoint 자동 권한 매트릭스 검증.

대상:
- DocUtil 135 endpoint 중 GET 만 (path parameter 없는 것)
- AgentHub 275 endpoint 중 GET 만 (path parameter 없는 것)
- 4계정 (admin@example.com / user@example.com / hslee / shbaek) — dev@example.com 미존재 SKIP

각 endpoint × 각 계정:
- expected = 카탈로그의 화이트리스트 (DocUtil roles / AgentHub Roles 매핑)
- actual = 운영 호출 결과 (200 / 401 / 403 / 404)
- 판정 = expected vs actual 비교

산출물:
- user_mig/track105_permission_matrix_results.json — raw 호출 결과
- user_mig/track105_permission_matrix_summary.md — PASS/FAIL 요약 + FAIL 목록

mutation endpoint (POST/PUT/PATCH/DELETE) 는 본 트랙 범위 외 — 별도 dry-run 트랙 분리.
path parameter ({user_id}, {project_id} 등) 있는 endpoint 는 SKIP (자동 채움 안전성 부족).
"""
from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

import paramiko

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
HOST, USER, PWD = "192.168.10.39", "idino", "dkdlelsh@12"

# 4계정 명세 (트랙 #105 Phase A.3 실측 검증된 계정만)
ACCOUNTS = [
    {"label": "SuperAdmin", "docutil_user": "admin@example.com", "docutil_pwd": "Admin123!",
     "agenthub_user": "admin@example.com", "agenthub_pwd": "Admin123!",
     "docutil_role": "super_admin", "agenthub_role": "Admin,SuperAdmin"},
    {"label": "UserLegacy", "docutil_user": "user@example.com", "docutil_pwd": "Admin123!",
     "agenthub_user": "user@example.com", "agenthub_pwd": "Admin123!",
     "docutil_role": "user", "agenthub_role": "User"},
    {"label": "EmployeeHslee", "docutil_user": "hslee", "docutil_pwd": "Admin123!",
     "agenthub_user": "hslee@idino.co.kr", "agenthub_pwd": "Admin123!",
     "docutil_role": "user", "agenthub_role": "User"},
    {"label": "EmployeeShbaek", "docutil_user": "shbaek", "docutil_pwd": "Admin123!",
     "agenthub_user": "shbaek@idino.co.kr", "agenthub_pwd": "Admin123!",
     "docutil_role": "user", "agenthub_role": "Admin"},  # 실측: shbaek 은 Admin role
]

DOCUTIL_BASE = "http://192.168.10.39:8040"
AGENTHUB_BASE = "http://192.168.10.39:64005"  # 운영 AgentHub Vue SPA + Web API

CATALOG_PATH = ROOT / "user_mig" / "track105_endpoint_catalog.json"
RESULTS_PATH = ROOT / "user_mig" / "track105_permission_matrix_results.json"
SUMMARY_PATH = ROOT / "user_mig" / "track105_permission_matrix_summary.md"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PWD, timeout=30)


def run(cmd: str, t: int = 60) -> str:
    _, o, _ = ssh.exec_command(cmd, timeout=t)
    return o.read().decode("utf-8", "replace")


def has_path_param(path: str) -> bool:
    return "{" in path and "}" in path


def login_docutil(username: str, password: str) -> str:
    body = json.dumps({"username": username, "password": password})
    run(
        f"curl -ksS -m 10 -X POST -H 'Content-Type: application/json' "
        f"-d '{body}' {DOCUTIL_BASE}/api/v1/auth/login -o /tmp/login_du.json",
        t=15,
    )
    raw = run("cat /tmp/login_du.json", t=5)
    try:
        return json.loads(raw).get("access_token", "")
    except Exception:
        return ""


def login_agenthub(email: str, password: str) -> str:
    body = json.dumps({"email": email, "password": password})
    run(
        f"curl -ksS -m 10 -X POST -H 'Content-Type: application/json' "
        f"-d '{body}' {AGENTHUB_BASE}/api/auth/login -o /tmp/login_ah.json",
        t=15,
    )
    raw = run("cat /tmp/login_ah.json", t=5)
    try:
        d = json.loads(raw)
        return d.get("token", d.get("access_token", d.get("accessToken", "")))
    except Exception:
        return ""


def call_endpoint(base: str, path: str, token: str | None) -> tuple[str, int | None]:
    """단순 GET 호출. HTTP status + 응답 크기 반환."""
    auth_header = f"-H 'Authorization: Bearer {token}'" if token else ""
    out = run(
        f"curl -ksS -m 8 -w '\\nHTTP_STATUS=%{{http_code}}\\nSIZE=%{{size_download}}' "
        f"{auth_header} '{base}{path}' -o /dev/null",
        t=12,
    )
    status = "?"
    size = None
    for line in out.splitlines():
        if line.startswith("HTTP_STATUS="):
            status = line.split("=", 1)[1].strip()
        elif line.startswith("SIZE="):
            try:
                size = int(line.split("=", 1)[1].strip())
            except ValueError:
                pass
    return status, size


def expected_docutil(roles: list[str] | None, account_role: str) -> str:
    """DocUtil endpoint 의 expected status (계정 role 기준).

    roles=None = require_role 미사용 = 인증만 → 200/4xx (endpoint 별)
    roles=리스트 = 화이트리스트 → account_role 이 in 이면 200, 아니면 403
    """
    if roles is None:
        # require_role 없음. 인증된 토큰이면 200 가능 (단 endpoint 별 다른 정책 있을 수 있음)
        return "200_or_403"
    if account_role in roles:
        return "200"
    return "403"


def expected_agenthub(roles: list[str], auth: str, account_role: str) -> str:
    """AgentHub endpoint 의 expected status."""
    if auth == "anonymous":
        return "200_or_404"
    if auth == "none":
        return "200_or_4xx"
    # authenticated + Roles 확인
    if not roles:
        # Roles 명시 없음 → 인증만 필요
        return "200"
    # account_role 이 콤마 분리된 경우 처리
    account_roles = [r.strip() for r in account_role.split(",")]
    if any(r in roles for r in account_roles):
        return "200"
    return "403"


def judge(expected: str, actual: str) -> str:
    """판정. PASS / FAIL / INFO."""
    if expected == "200":
        return "PASS" if actual == "200" else "FAIL"
    if expected == "403":
        return "PASS" if actual in ("403", "401") else "FAIL"
    if expected.startswith("200_or"):
        # 허용 가능 status 셋
        if actual == "200":
            return "PASS"
        if expected == "200_or_403" and actual in ("403", "401"):
            return "PASS"
        if expected == "200_or_404" and actual == "404":
            return "PASS"
        if expected == "200_or_4xx" and actual.startswith("4"):
            return "PASS"
        return "INFO"
    return "INFO"


def main() -> int:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    docutil_eps = catalog["docutil"]["endpoints"]
    agenthub_eps = catalog["agenthub"]["endpoints"]

    # GET + path parameter 없는 endpoint 만 필터링
    docutil_get = [
        e for e in docutil_eps if e["method"] == "GET" and not has_path_param(e["path"])
    ]
    agenthub_get = [
        e for e in agenthub_eps if e["http_method"] == "GET" and not has_path_param(e["path"])
    ]
    print(f"DocUtil GET (no path param): {len(docutil_get)}/{len(docutil_eps)}")
    print(f"AgentHub GET (no path param): {len(agenthub_get)}/{len(agenthub_eps)}")
    print(f"매트릭스: {len(ACCOUNTS)} 계정 × {len(docutil_get) + len(agenthub_get)} endpoint = {len(ACCOUNTS) * (len(docutil_get) + len(agenthub_get))} cell\n")

    # 4계정 로그인 (DocUtil + AgentHub 각각)
    tokens: dict[str, dict[str, str]] = {}
    for acc in ACCOUNTS:
        label = acc["label"]
        print(f"[login] {label}")
        du_tok = login_docutil(acc["docutil_user"], acc["docutil_pwd"])
        ah_tok = login_agenthub(acc["agenthub_user"], acc["agenthub_pwd"])
        tokens[label] = {"docutil": du_tok, "agenthub": ah_tok}
        print(f"  docutil token: {len(du_tok)} chars")
        print(f"  agenthub token: {len(ah_tok)} chars")

    results: dict[str, list[dict]] = {acc["label"]: [] for acc in ACCOUNTS}

    print("\n[DocUtil endpoint 호출 시작]")
    for idx, ep in enumerate(docutil_get):
        path = ep["full_path"]
        for acc in ACCOUNTS:
            label = acc["label"]
            tok = tokens[label]["docutil"]
            if not tok:
                results[label].append(
                    {**ep, "actual": "no_token", "expected": "n/a", "judge": "SKIP"}
                )
                continue
            status, size = call_endpoint(DOCUTIL_BASE, path, tok)
            exp = expected_docutil(ep["roles"], acc["docutil_role"])
            verdict = judge(exp, status)
            results[label].append(
                {**ep, "actual": status, "size": size, "expected": exp, "judge": verdict}
            )
        if (idx + 1) % 20 == 0:
            print(f"  ...{idx + 1}/{len(docutil_get)} DocUtil endpoint 처리됨")

    print("\n[AgentHub endpoint 호출 시작]")
    for idx, ep in enumerate(agenthub_get):
        # AgentHub path: 카탈로그의 path 가 controller prefix 추출 결과. 보정 필요.
        # 기본 prefix: /api/<lowercase controller name without 'Controller'>
        path = ep["path"]
        if not path.startswith("/"):
            path = "/" + path
        # AgentHub 의 통상 API 는 /api prefix
        if not path.startswith("/api"):
            path = "/api" + path
        for acc in ACCOUNTS:
            label = acc["label"]
            tok = tokens[label]["agenthub"]
            if not tok:
                results[label].append(
                    {**ep, "actual": "no_token", "expected": "n/a", "judge": "SKIP",
                     "called_path": path}
                )
                continue
            status, size = call_endpoint(AGENTHUB_BASE, path, tok)
            exp = expected_agenthub(ep["roles"], ep["auth"], acc["agenthub_role"])
            verdict = judge(exp, status)
            results[label].append(
                {**ep, "actual": status, "size": size, "expected": exp, "judge": verdict,
                 "called_path": path}
            )
        if (idx + 1) % 20 == 0:
            print(f"  ...{idx + 1}/{len(agenthub_get)} AgentHub endpoint 처리됨")

    ssh.close()

    # 저장
    RESULTS_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[JSON] {RESULTS_PATH.relative_to(ROOT)} ({RESULTS_PATH.stat().st_size:,} bytes)")

    # 요약 MD
    lines: list[str] = []
    lines.append("# 트랙 #105 Phase B.4 — 5계정 × 410 endpoint 권한 매트릭스 결과\n\n")
    lines.append(f"**검증일**: 2026-05-20\n")
    lines.append(f"**대상**: 4계정 × (DocUtil {len(docutil_get)} GET + AgentHub {len(agenthub_get)} GET) = {len(ACCOUNTS) * (len(docutil_get) + len(agenthub_get))} cell\n\n")
    lines.append("(POST/PUT/PATCH/DELETE 및 path parameter 있는 endpoint 는 본 트랙 범위 외)\n\n---\n\n")

    # 계정별 집계
    lines.append("## 계정별 집계\n\n")
    lines.append("| 계정 | DocUtil PASS | DocUtil FAIL | AgentHub PASS | AgentHub FAIL | 전체 PASS율 |\n")
    lines.append("|---|---|---|---|---|---|\n")
    for acc in ACCOUNTS:
        label = acc["label"]
        rs = results[label]
        du_rs = [r for r in rs if r["system"] == "docutil"]
        ah_rs = [r for r in rs if r["system"] == "agenthub"]
        du_pass = sum(1 for r in du_rs if r["judge"] == "PASS")
        du_fail = sum(1 for r in du_rs if r["judge"] == "FAIL")
        ah_pass = sum(1 for r in ah_rs if r["judge"] == "PASS")
        ah_fail = sum(1 for r in ah_rs if r["judge"] == "FAIL")
        all_total = len(du_rs) + len(ah_rs)
        all_pass = du_pass + ah_pass
        rate = f"{(all_pass / all_total * 100):.1f}%" if all_total else "—"
        lines.append(f"| {label} | {du_pass} | {du_fail} | {ah_pass} | {ah_fail} | {rate} |\n")
    lines.append("\n")

    # FAIL endpoint 상세
    lines.append("## FAIL endpoint 상세 (계정별)\n\n")
    for acc in ACCOUNTS:
        label = acc["label"]
        fails = [r for r in results[label] if r["judge"] == "FAIL"]
        lines.append(f"### {label} — {len(fails)} FAIL\n\n")
        if not fails:
            lines.append("(FAIL 없음)\n\n")
            continue
        lines.append("| system | method | path | roles/auth | expected | actual | 비고 |\n")
        lines.append("|---|---|---|---|---|---|---|\n")
        for r in fails[:40]:
            roles_str = ",".join(r.get("roles") or []) if r.get("roles") else (r.get("auth", "—"))
            method = r.get("method") or r.get("http_method", "?")
            path = r.get("called_path") or r.get("full_path") or r.get("path", "?")
            lines.append(
                f"| {r['system']} | {method} | {path} | {roles_str} | {r['expected']} | {r['actual']} | |\n"
            )
        if len(fails) > 40:
            lines.append(f"\n_(추가 {len(fails) - 40} 건 생략, raw JSON 참조)_\n")
        lines.append("\n")

    SUMMARY_PATH.write_text("".join(lines), encoding="utf-8")
    print(f"[MD]   {SUMMARY_PATH.relative_to(ROOT)} ({SUMMARY_PATH.stat().st_size:,} bytes)")

    # 콘솔 요약
    print("\n[7] 계정별 PASS/FAIL 집계")
    for acc in ACCOUNTS:
        label = acc["label"]
        rs = results[label]
        passes = sum(1 for r in rs if r["judge"] == "PASS")
        fails = sum(1 for r in rs if r["judge"] == "FAIL")
        infos = sum(1 for r in rs if r["judge"] == "INFO")
        skips = sum(1 for r in rs if r["judge"] == "SKIP")
        total = len(rs)
        print(f"  {label:18s} PASS={passes:3d} FAIL={fails:3d} INFO={infos:3d} SKIP={skips:3d} TOTAL={total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
