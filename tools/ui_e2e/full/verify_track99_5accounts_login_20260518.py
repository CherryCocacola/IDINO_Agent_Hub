"""2026-05-18 트랙 #99 4단 — 5계정 × 2시스템 로그인 검증.

5계정 (권한 수준별):
  1. admin@example.com (SuperAdmin)
  2. developer@example.com (Admin)
  3. user@example.com (User)
  4. hslee@idino.co.kr (admin role, 일반 직원)
  5. shbaek@idino.co.kr (admin role, 일반 직원)

2시스템:
  - AgentHub: http://192.168.10.39:64005/api/auth/login  (email/password)
  - DocUtil: http://192.168.10.39:8041/api/v1/auth/login  (username/password)

각 계정에 대해:
  - AgentHub email/password 로 로그인 → JWT 발급
  - DocUtil username (email 의 local part 또는 한글명) 로 로그인 → JWT 발급
  - 결과 매트릭스 + storage_state 5개 (AgentHub) + 5개 (DocUtil) 저장
"""
from __future__ import annotations
import io, json, re, sys, paramiko
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HOST, USER, PWD = "192.168.10.39", "idino", "dkdlelsh@12"

ACCOUNTS = [
    # (label, agenthub_email, docutil_username_candidates, password)
    ("SuperAdmin", "admin@example.com",
     ["admin@example.com", "admin"], "Admin123!"),
    ("Admin (Developer)", "developer@example.com",
     ["developer@example.com", "developer"], "Admin123!"),
    ("User", "user@example.com",
     ["user@example.com", "user"], "Admin123!"),
    ("Employee (hslee)", "hslee@idino.co.kr",
     ["hslee", "hslee@idino.co.kr", "이현수"], "Admin123!"),
    ("Employee (shbaek)", "shbaek@idino.co.kr",
     ["shbaek", "shbaek@idino.co.kr", "백성현"], "Admin123!"),
]

OUTPUT_JSON = Path(__file__).parent / "track99_4step_login_results.json"


def run(ssh, cmd, t=30):
    _, o, _ = ssh.exec_command(cmd, timeout=t)
    return o.read().decode("utf-8", "replace")


def agenthub_login(ssh, email: str, password: str) -> tuple[int, str, str]:
    """AgentHub /api/auth/login — email/password."""
    body = json.dumps({"email": email, "password": password})
    cmd = (
        f'curl -ksS -m 10 -o /tmp/ah_resp.txt -w "%{{http_code}}" '
        f'-X POST -H "Content-Type: application/json" '
        f"-d '{body}' http://192.168.10.39:64005/api/auth/login"
    )
    code = run(ssh, cmd, 15).strip()
    # 전체 응답을 받기 위해 head 제거 (JWT 가 1500+ 바이트일 수 있음)
    resp = run(ssh, "cat /tmp/ah_resp.txt", 5)
    try:
        data = json.loads(resp)
        jwt = data.get("token", "")
    except (ValueError, json.JSONDecodeError):
        jwt = ""
    return int(code) if code.isdigit() else 0, jwt, resp[:200]


def docutil_login(ssh, username: str, password: str) -> tuple[int, str, str]:
    """DocUtil /api/v1/auth/login — username/password."""
    body = json.dumps({"username": username, "password": password})
    cmd = (
        f'curl -ksS -m 10 -o /tmp/du_resp.txt -w "%{{http_code}}" '
        f'-X POST -H "Content-Type: application/json" '
        f"-d '{body}' http://192.168.10.39:8041/api/v1/auth/login"
    )
    code = run(ssh, cmd, 15).strip()
    resp = run(ssh, "cat /tmp/du_resp.txt", 5)
    try:
        data = json.loads(resp)
        jwt = data.get("access_token", "")
    except (ValueError, json.JSONDecodeError):
        jwt = ""
    return int(code) if code.isdigit() else 0, jwt, resp[:200]


def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PWD, timeout=30)
    print(f"[ssh] {HOST}")
    print("\n" + "=" * 80)
    print("트랙 #99 4단 — 5계정 × 2시스템 로그인 매트릭스")
    print("=" * 80)

    results = []
    for label, email, du_candidates, pw in ACCOUNTS:
        print(f"\n--- [{label}] {email} ---")
        # AgentHub
        ah_code, ah_jwt, ah_resp = agenthub_login(ssh, email, pw)
        ah_pass = ah_code == 200 and len(ah_jwt) > 0
        print(f"  AgentHub login: HTTP {ah_code} | JWT len {len(ah_jwt)} | {'PASS' if ah_pass else 'FAIL'}")
        if not ah_pass:
            print(f"    응답: {ah_resp[:150]}")

        # DocUtil — 여러 username 후보 시도
        du_results = []
        du_pass = False
        du_jwt_final = ""
        du_username_final = ""
        for candidate in du_candidates:
            du_code, du_jwt, du_resp = docutil_login(ssh, candidate, pw)
            cand_pass = du_code == 200 and len(du_jwt) > 0
            du_results.append({
                "username": candidate, "code": du_code,
                "jwt_len": len(du_jwt), "pass": cand_pass,
                "resp_preview": du_resp[:100]
            })
            print(f"  DocUtil login (username={candidate!r}): HTTP {du_code} | "
                  f"JWT len {len(du_jwt)} | {'PASS' if cand_pass else 'FAIL'}")
            if cand_pass and not du_pass:
                du_pass = True
                du_jwt_final = du_jwt
                du_username_final = candidate
                break

        results.append({
            "label": label,
            "agenthub": {
                "email": email,
                "http": ah_code,
                "jwt_len": len(ah_jwt),
                "pass": ah_pass,
                "jwt": ah_jwt if ah_pass else "",
                "resp_preview": ah_resp[:200] if not ah_pass else ""
            },
            "docutil": {
                "candidates": du_results,
                "pass": du_pass,
                "username": du_username_final if du_pass else "",
                "jwt": du_jwt_final if du_pass else ""
            }
        })

    ssh.close()

    # 종합 보고
    print("\n" + "=" * 80)
    print("종합 매트릭스")
    print("=" * 80)
    print(f"{'계정':<25} {'AgentHub':<10} {'DocUtil':<10} {'DU username':<25}")
    print("-" * 80)
    for r in results:
        ah = "PASS" if r["agenthub"]["pass"] else f"FAIL({r['agenthub']['http']})"
        du = "PASS" if r["docutil"]["pass"] else "FAIL"
        du_user = r["docutil"]["username"] if r["docutil"]["pass"] else "-"
        print(f"{r['label']:<25} {ah:<10} {du:<10} {du_user:<25}")

    pass_ah = sum(1 for r in results if r["agenthub"]["pass"])
    pass_du = sum(1 for r in results if r["docutil"]["pass"])
    print(f"\n  AgentHub: {pass_ah}/5 PASS")
    print(f"  DocUtil: {pass_du}/5 PASS")

    # JWT 제거 후 결과 저장
    safe_results = []
    for r in results:
        s = json.loads(json.dumps(r))
        s["agenthub"]["jwt"] = "<redacted>" if s["agenthub"]["jwt"] else ""
        s["docutil"]["jwt"] = "<redacted>" if s["docutil"]["jwt"] else ""
        safe_results.append(s)
    OUTPUT_JSON.write_text(json.dumps(safe_results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n결과 저장: {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
