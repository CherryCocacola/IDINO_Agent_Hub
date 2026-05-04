"""Phase 4 S1 D2 Step 6 — API / Celery 재시작 + 스모크 테스트.

- docker compose restart api celery-worker
- docker ps 로 healthy 확인
- alembic current 재확인
- /health 엔드포인트
- 기존 /api/v1/reports 엔드포인트 호출 (archive 리네이밍 영향 파악)
"""
import paramiko
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SERVER = "192.168.10.39"
USER = "idino"
PASS = "dkdlelsh@12"
REMOTE_DIR = "/home/idino/docutil"


def run(ssh, cmd, label, timeout=180):
    print(f"\n--- {label} ---")
    print(f"$ {cmd}")
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    rc = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    if out:
        print(out.rstrip())
    if err:
        print(f"[stderr] {err.rstrip()}", file=sys.stderr)
    print(f"[exit={rc}]")
    return out, err, rc


def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASS, timeout=15)

    # 1. 재시작 전 상태
    run(ssh, "docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E '(docutil-api|celery)'", "1. 재시작 전 상태")

    # 2. restart (stop 금지, restart만)
    run(
        ssh,
        f"cd {REMOTE_DIR} && docker compose restart api celery-worker 2>&1",
        "2. api + celery-worker restart",
        timeout=120,
    )

    # 3. 15초 대기
    print("\n[WAIT] 15초 대기…")
    time.sleep(15)

    # 4. 컨테이너 상태
    run(ssh, "docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E '(docutil-api|celery)'", "4. 재시작 후 상태")

    # 5. alembic current (ORM 재로드 후에도 동일해야)
    run(
        ssh,
        f"cd {REMOTE_DIR} && docker exec docutil-api alembic current",
        "5. alembic current 재확인 (007_documents_v2)",
    )

    # 6. /health 엔드포인트
    run(
        ssh,
        "docker exec docutil-api curl -sf http://localhost:8000/health",
        "6. /health (docutil-api 컨테이너 내부)",
    )

    # 7. /api/v1/reports — archive 리네이밍 영향 측정
    #    인증 필요할 수 있으니 HTTP 상태만 확인
    run(
        ssh,
        "docker exec docutil-api curl -s -o /dev/null -w 'HTTP:%{http_code} TIME:%{time_total}s\\n' http://localhost:8000/api/v1/reports",
        "7. /api/v1/reports (인증 없이 상태코드)",
    )

    # 7b. 요청 바디 확인 (401 예상하지만 500 아닌지)
    run(
        ssh,
        "docker exec docutil-api curl -s http://localhost:8000/api/v1/reports | head -c 500",
        "7b. /api/v1/reports 응답 본문 (앞 500자)",
    )

    # 8. 최근 API 로그 (오류 탐지)
    run(
        ssh,
        "docker logs docutil-api --since 60s 2>&1 | tail -80",
        "8. docutil-api 최근 60초 로그",
    )

    # 9. celery-worker 최근 로그
    run(
        ssh,
        "docker logs docutil-celery-worker-1 --since 60s 2>&1 | tail -30",
        "9. celery-worker 최근 60초 로그",
    )

    # 10. 컨테이너 health 최종
    run(
        ssh,
        "docker inspect --format '{{.Name}}: {{.State.Health.Status}}' docutil-api docutil-celery-worker-1",
        "10. health 상태",
    )

    ssh.close()
    print("\n[DONE] Step 6 restart + smoke test complete.")


if __name__ == "__main__":
    main()
