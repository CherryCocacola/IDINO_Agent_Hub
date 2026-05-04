"""프론트 변경분만 서버에 반영 후 Next.js 이미지 재빌드(setsid 백그라운드).

D10-A 에서 추가된 동적 라우트/리다이렉트만 서버에 업로드하고
docker compose build --no-cache frontend + up --force-recreate 로 교체한다.
paramiko PipeTimeout 을 피하기 위해 빌드는 setsid detach 후
`/tmp/frontend_build.log` 로 로그가 쌓인다.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import paramiko

SERVER = "192.168.10.39"
USER = "idino"
PASS = os.environ.get("DOCUTIL_SERVER_PASS", "dkdlelsh@12")
LOCAL_ROOT = Path(r"D:\workspace\document_utilization")
REMOTE_DIR = "/home/idino/docutil"

FILES = [
    r"frontend/src/app/(user)/designer/[documentId]/page.tsx",
    r"frontend/src/app/(user)/designer/create/page.tsx",
]


def _mkdirp(ssh: paramiko.SSHClient, path: str) -> None:
    # (user), [documentId] 등 쉘 특수문자 포함 경로를 안전하게 전달하기 위해
    # single quote 로 감싼다. 경로 자체에 작은따옴표는 없다고 가정.
    _, so, se = ssh.exec_command(f"mkdir -p '{path}'", timeout=5)
    so.channel.recv_exit_status()  # 디렉토리 생성 완료까지 동기 대기


def main() -> int:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASS, timeout=15)
    print("[접속 OK]")

    # 1. 파일 업로드
    sftp = ssh.open_sftp()
    for rel in FILES:
        local = LOCAL_ROOT / rel.replace("/", os.sep)
        if not local.exists():
            print(f"  SKIP not found: {rel}")
            continue
        remote = f"{REMOTE_DIR}/{rel}"
        _mkdirp(ssh, os.path.dirname(remote))
        sftp.put(str(local), remote)
        print(f"  UPLOADED: {rel}")
    sftp.close()

    # 2. setsid 백그라운드로 프론트 재빌드 + 교체
    print("\n[setsid 프론트 재빌드 시작]")
    build_cmd = (
        f"cd {REMOTE_DIR} && "
        "( "
        "echo '=== fe build start ===' && "
        "docker compose build --no-cache frontend && "
        "echo '=== fe build ok ===' && "
        "docker compose up -d --force-recreate frontend && "
        "echo '=== fe up ok ===' && "
        "sleep 8 && "
        "docker compose restart nginx && "
        "echo FE_DONE "
        ") || echo FE_FAIL"
    )
    escaped = build_cmd.replace("'", "'\"'\"'")
    remote = (
        "rm -f /tmp/frontend_build.log && "
        f"setsid bash -c '{escaped}' > /tmp/frontend_build.log 2>&1 < /dev/null &"
    )
    ssh.exec_command(remote, timeout=10)

    import time
    time.sleep(3)
    _, so, _ = ssh.exec_command(
        "pgrep -af 'docker compose build --no-cache frontend' | head -3",
        timeout=10,
    )
    print("빌드 프로세스:", so.read().decode(errors="replace").strip() or "(시작 실패)")

    ssh.close()
    print("\n[detach 완료] polling: _poll_frontend_build.py 또는 tail /tmp/frontend_build.log")
    return 0


if __name__ == "__main__":
    sys.exit(main())
