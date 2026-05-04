"""Phase 4 S1 D2 Step 4 — Alembic upgrade head 실행.

- 실행 전 현재 head 확인
- upgrade head
- 실행 후 head 확인
- 로그 전체 보존
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


def run(ssh, cmd, label, timeout=300):
    print(f"\n--- {label} ---")
    print(f"$ {cmd}")
    t0 = time.time()
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    # exec_command 는 non-blocking. exit_status 기다리기
    exit_status = stdout.channel.recv_exit_status()
    elapsed = time.time() - t0
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    if out:
        print(out.rstrip())
    if err:
        print(f"[stderr] {err.rstrip()}", file=sys.stderr)
    print(f"[exit={exit_status}, elapsed={elapsed:.2f}s]")
    return out, err, exit_status


def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASS, timeout=15)

    # 1. 실행 전 alembic heads / current
    run(ssh, f"cd {REMOTE_DIR} && docker exec docutil-api alembic heads", "실행 전 heads")
    run(ssh, f"cd {REMOTE_DIR} && docker exec docutil-api alembic current", "실행 전 current")

    # 2. 007 업그레이드 미리 SQL 만 출력 (참고용, 실행은 하지 않음)
    # --sql 모드는 offline mode 라 some ops 는 fail. 스킵.

    # 3. upgrade head 실행 (verbose)
    out, err, rc = run(
        ssh,
        f"cd {REMOTE_DIR} && docker exec docutil-api alembic upgrade head 2>&1",
        "★ alembic upgrade head 실행",
        timeout=600,
    )

    if rc != 0:
        print("\n[FAIL] upgrade 실패. Step 5 검증 생략하고 롤백 단계로.")
        ssh.close()
        sys.exit(1)

    # 4. 실행 후 current
    run(ssh, f"cd {REMOTE_DIR} && docker exec docutil-api alembic current", "실행 후 current")
    run(ssh, f"cd {REMOTE_DIR} && docker exec docutil-api alembic history -r-2:head", "최근 history")

    ssh.close()
    print("\n[DONE] Step 4 upgrade complete.")


if __name__ == "__main__":
    main()
