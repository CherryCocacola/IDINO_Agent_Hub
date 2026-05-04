"""docutil-api 컨테이너 내부 구조를 빠르게 확인한다."""

from __future__ import annotations

import os
import sys

import paramiko

SERVER = "192.168.10.39"
USER = "idino"
PASS = os.environ.get("DOCUTIL_SERVER_PASS", "dkdlelsh@12")


def run(ssh: paramiko.SSHClient, cmd: str) -> None:
    print(f"$ {cmd}")
    _, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    if out:
        print(out)
    if err:
        print("STDERR:", err)


def main() -> int:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASS, timeout=15)
    run(ssh, "docker exec docutil-api ls -la /app")
    run(ssh, "docker exec docutil-api ls /app/tests 2>&1 || echo NO_TESTS_DIR")
    run(ssh, "docker exec docutil-api python -c \"import sys; print(sys.version)\"")
    run(ssh, "docker exec docutil-api env | grep -iE 'OPENAI|AZURE|GOOGLE|ANTHROPIC' | sort")
    ssh.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
