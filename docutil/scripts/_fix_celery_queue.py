"""celery-worker command에 -Q 옵션 추가 후 재기동 (이미지 재빌드 불필요).

docker-compose.yml 의 celery-worker command 맨 끝에 `-Q ...` 옵션을 삽입하여
worker가 document_export + evaluation queue도 함께 listen하게 한다.
"""
from __future__ import annotations

import sys
import paramiko

SERVER = "192.168.10.39"
USER = "idino"
PASS = "dkdlelsh@12"
REMOTE = "/home/idino/docutil"
Q_LIST = "default,document_processing,embedding,report_generation,document_export,evaluation"


def main() -> int:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASS, timeout=15)
    print("[접속 OK]")

    # 1. 현재 celery-worker command 확인
    print("\n=== 현재 docker-compose.yml celery-worker 블록 ===")
    _, so, _ = ssh.exec_command(
        f"cd {REMOTE} && awk '/^  celery-worker:/,/^  [a-z]+:/' docker-compose.yml | head -30",
        timeout=10,
    )
    print(so.read().decode(errors="replace"))

    # 2. 이미 -Q 있는지 확인
    _, so, _ = ssh.exec_command(
        f"grep -c '\\-Q ' {REMOTE}/docker-compose.yml", timeout=5
    )
    already = so.read().decode().strip()
    if already and int(already) > 0:
        print(f"[-Q 옵션 이미 존재: {already}건]")
    else:
        # 3. --max-tasks-per-child 라인 뒤에 -Q 옵션 추가 (첫 매칭만, celery-worker에 해당)
        sed = (
            f"sed -i '0,/--max-tasks-per-child=/{{s|--max-tasks-per-child=\\${{CELERY_MAX_TASKS_PER_CHILD:-100}}|--max-tasks-per-child=\\${{CELERY_MAX_TASKS_PER_CHILD:-100}}\\n      -Q {Q_LIST}|}}' {REMOTE}/docker-compose.yml"
        )
        _, so, se = ssh.exec_command(sed, timeout=10)
        print("sed exit:", so.channel.recv_exit_status())
        err = se.read().decode(errors="replace")
        if err:
            print("stderr:", err[:200])

    # 4. 수정 결과 확인
    print("\n=== 수정 후 celery-worker command ===")
    _, so, _ = ssh.exec_command(
        f"cd {REMOTE} && awk '/^  celery-worker:/,/^  [a-z]+:/' docker-compose.yml | head -20",
        timeout=10,
    )
    print(so.read().decode(errors="replace"))

    # 5. celery-worker 재생성 (이미지는 그대로, command만 변경)
    print("\n=== celery-worker 재생성 ===")
    _, so, _ = ssh.exec_command(
        f"cd {REMOTE} && docker compose up -d --force-recreate --no-deps celery-worker 2>&1",
        timeout=60,
    )
    print(so.read().decode(errors="replace"))

    # 6. 재기동 후 queue 목록 확인
    print("\n=== 재기동 후 worker queues ===")
    import time
    time.sleep(10)
    _, so, _ = ssh.exec_command(
        "docker logs docutil-celery-worker-1 2>&1 | grep -A 8 'queues' | head -15",
        timeout=15,
    )
    print(so.read().decode(errors="replace"))

    ssh.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
