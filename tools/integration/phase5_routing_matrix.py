"""Phase 5.7 자동 검증 매트릭스 — 3 라우팅 (External/Internal/Hybrid) × 시나리오.

목적: Phase 5 (NexusClient + LlmRouting + HybridRouter) 의 운영 회귀 차단 자산.
향후 트랙에서 NexusClient / AiProxyService / HybridRouter 코드 변경 시 본 매트릭스
재실행으로 회귀 즉시 감지.

검증 시나리오:
  - Internal Agent: Nexus 직접 호출 (id=30 career-action-recommender)
  - External Agent: OpenAI 호출 — 운영 quota 초과 시 503 + 한국어 메시지
    (트랙 #141~#143 의 정합 응답 확인)
  - Hybrid Agent PII: 주민번호 포함 → internal 라우팅
  - Hybrid Agent capability: vision 모델 → 정책에 따라 분기

각 시나리오 결과를 JSON 저장 + 콘솔 표시. CI 인테그레이션 시 exit code 활용
(전체 PASS → 0, 1건이라도 FAIL → 1).
"""
from __future__ import annotations
import argparse, io, json, sys, time
from datetime import datetime, timezone
from pathlib import Path
import paramiko

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "192.168.10.39"
USER = "idino"
PWD = "dkdlelsh@12"
AH = "http://192.168.10.39:64005"


def open_ssh() -> paramiko.SSHClient:
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    s.connect(HOST, username=USER, password=PWD, timeout=30)
    return s


def run(ssh: paramiko.SSHClient, cmd: str, timeout: int = 60) -> str:
    _, o, e = ssh.exec_command(cmd, timeout=timeout)
    return o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')


def login_admin(ssh) -> str:
    body = json.dumps({"email": "admin@example.com", "password": "Admin123!"})
    run(ssh, f"curl -ksS -m 10 -X POST -H 'Content-Type: application/json' -d '{body}' {AH}/api/auth/login -o /tmp/l.json", t=15) if False else None
    run(ssh, f"curl -ksS -m 10 -X POST -H 'Content-Type: application/json' -d '{body}' {AH}/api/auth/login -o /tmp/l.json", timeout=15)
    return json.loads(run(ssh, "cat /tmp/l.json"))["token"]


def call_agent(ssh, tok: str, agent_id: int, message: str, timeout: int = 90) -> dict:
    body = json.dumps({"message": message})
    out_path = f"/tmp/m_{agent_id}_{int(time.time())}.json"
    cmd = (
        f"curl -ksS -m {timeout} -X POST -H 'Authorization: Bearer {tok}' "
        f"-H 'Content-Type: application/json' -d '{body}' "
        f"-w '\\nHTTP=%{{http_code}}\\nTOTAL=%{{time_total}}s\\n' "
        f"'{AH}/api/agents/{agent_id}/chat' -o {out_path}"
    )
    out = run(ssh, cmd, timeout=timeout + 10)
    # HTTP / TOTAL 추출
    http = "?"
    total = "?"
    for line in out.strip().splitlines():
        if line.startswith("HTTP="):
            http = line.split("=", 1)[1].strip()
        elif line.startswith("TOTAL="):
            total = line.split("=", 1)[1].strip().rstrip("s")
    body_text = run(ssh, f"cat {out_path}")
    try:
        body_json = json.loads(body_text)
    except Exception:
        body_json = {"raw": body_text[:400]}
    return {"http": http, "total_seconds": total, "body": body_json}


def fetch_recent_router_logs(ssh, since_seconds: int = 30) -> list[str]:
    cmd = (
        f"docker logs agenthub --since {since_seconds}s 2>&1 | "
        f"grep -E 'HybridRouter|라우팅 적용|Decision=|Reason=' | tail -10"
    )
    out = run(ssh, cmd, timeout=15)
    return [l.strip() for l in out.splitlines() if l.strip()]


def assert_case(name: str, ok: bool, detail: str) -> dict:
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {name} — {detail}")
    return {"name": name, "status": status, "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="user_mig/PHASE5_VALIDATION.json")
    args = parser.parse_args()

    ssh = open_ssh()
    started = datetime.now(timezone.utc).isoformat()
    tok = login_admin(ssh)
    print(f"[matrix start] {started}")

    results: list[dict] = []

    # 1. Internal Agent (id=30 career-action-recommender)
    print("\n[1] Internal Agent (id=30) — Nexus 직접 호출")
    r1 = call_agent(ssh, tok, 30, "안녕하세요. 짧게 자기소개 부탁드립니다.")
    ok1 = r1["http"] == "200" and isinstance(r1["body"], dict) and r1["body"].get("content")
    results.append(assert_case(
        "internal_nexus_direct",
        ok1,
        f"HTTP={r1['http']} time={r1['total_seconds']}s content={(r1['body'].get('content') or '')[:60]!r}"
    ))

    # 2. Hybrid Agent PII 검증 (id=29 career-action-recommender — Hybrid, gpt-4o-mini)
    print("\n[2] Hybrid PII 룰 (id=29) — 주민번호 포함 → internal 기대")
    r2 = call_agent(ssh, tok, 29, "안녕하세요. 제 주민번호는 901225-1234567 입니다.")
    # 직전 호출 직후 로그 fetch — 시점 보강
    logs2 = fetch_recent_router_logs(ssh, since_seconds=15)
    pii_match = any("pii_detected" in l.lower() or "pii" in l.lower() for l in logs2)
    nexus_match = any("nexus" in l.lower() for l in logs2)
    ok2 = r2["http"] == "200" and (pii_match or nexus_match)  # 둘 중 하나만 매치되어도 PASS (capability 룰이 먼저 매치되는 케이스 허용)
    results.append(assert_case(
        "hybrid_pii_to_internal",
        ok2,
        f"HTTP={r2['http']} pii_log={pii_match} nexus_route={nexus_match}"
    ))

    # 3. Hybrid Agent capability 룰 (id=22 docutil-rag-chat, gpt-4o)
    # 옵션 A:c 정책 적용 상태에서는 vision=internal → Nexus 라우팅 200
    print("\n[3] Hybrid capability 룰 (id=22) — vision 모델 → 정책 분기")
    r3 = call_agent(ssh, tok, 22, "문서 챗봇 기능 테스트입니다.")
    logs3 = fetch_recent_router_logs(ssh, 30)
    capability_match = any("capability_required" in l.lower() for l in logs3)
    ok3 = r3["http"] == "200" and capability_match
    results.append(assert_case(
        "hybrid_capability_branch",
        ok3,
        f"HTTP={r3['http']} capability_log={capability_match}"
    ))

    # 4. External Agent (id=43 테스트) — OpenAI 응답 정합성 (트랙 #141~#143)
    print("\n[4] External Agent (id=43) — OpenAI 응답 정합성")
    r4 = call_agent(ssh, tok, 43, "hi", timeout=30)
    body4 = r4["body"]
    msg4 = (body4.get("message") if isinstance(body4, dict) else "") or ""
    is_200 = r4["http"] == "200"
    is_quota_503 = r4["http"] == "503" and "사용량 한도" in msg4
    # 트랙 #145 (2026-06-01): 비-429 외부 LLM 결함도 한국어 변환. 401/403 → 502 + "인증에 실패".
    is_auth_502 = r4["http"] == "502" and ("인증에 실패" in msg4 or "API key" in msg4)
    # 5xx upstream 다운 → 502 + "서버 오류"
    is_upstream_502 = r4["http"] == "502" and "서버 오류" in msg4
    # 4xx 요청 결함 → 502 + "호출 거부"
    is_request_502 = r4["http"] == "502" and "호출 거부" in msg4
    ok4 = is_200 or is_quota_503 or is_auth_502 or is_upstream_502 or is_request_502
    label = (
        "(정상 200)" if is_200 else
        "(quota 503 한국어)" if is_quota_503 else
        "(auth 502 한국어 #145)" if is_auth_502 else
        "(upstream 502 한국어 #145)" if is_upstream_502 else
        "(request 502 한국어 #145)" if is_request_502 else
        "(기타 — 후속 트랙 후보)"
    )
    results.append(assert_case(
        "external_openai_uniform_response",
        ok4,
        f"HTTP={r4['http']} {label}"
    ))

    finished = datetime.now(timezone.utc).isoformat()
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    fail_count = len(results) - pass_count

    summary = {
        "started_at": started,
        "finished_at": finished,
        "host": HOST,
        "passed": pass_count,
        "failed": fail_count,
        "total": len(results),
        "results": results
    }

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f"\n[summary] PASS={pass_count} FAIL={fail_count} / 결과: {args.out}")
    ssh.close()
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
