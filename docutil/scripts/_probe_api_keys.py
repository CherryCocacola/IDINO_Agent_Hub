"""DB 에 저장된 LLM API 키 존재 현황을 조회한다 (복호화는 하지 않음)."""

from __future__ import annotations

import io
import os
import sys

import paramiko

SERVER = "192.168.10.39"
USER = "idino"
PASS = os.environ.get("DOCUTIL_SERVER_PASS", "dkdlelsh@12")


PROBE_SCRIPT = r"""
import asyncio
from sqlalchemy import select
from app.core.database import async_session_factory
from app.modules.api_keys.models import LLMApiKey


async def main():
    async with async_session_factory() as s:
        rows = (
            await s.execute(
                select(
                    LLMApiKey.id,
                    LLMApiKey.organization_id,
                    LLMApiKey.llm_name,
                    LLMApiKey.api_key_prefix,
                    LLMApiKey.is_verified,
                )
            )
        ).all()
        for r in rows:
            print(tuple(r))


asyncio.run(main())
"""


def run(ssh: paramiko.SSHClient, cmd: str) -> None:
    print(f"$ {cmd}")
    _, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    print(stdout.read().decode("utf-8", errors="replace"))
    err = stderr.read().decode("utf-8", errors="replace")
    if err.strip():
        print("STDERR:", err)


def main() -> int:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASS, timeout=15)

    # 스크립트를 /tmp 에 업로드한 뒤 docker cp 로 컨테이너에 복사.
    sftp = ssh.open_sftp()
    host_path = "/tmp/_probe_api_keys_inside.py"
    with sftp.file(host_path, "wb") as f:
        f.write(PROBE_SCRIPT.encode("utf-8"))
    sftp.close()

    run(ssh, f"docker cp {host_path} docutil-api:/app/_probe_api_keys_inside.py")
    run(
        ssh,
        "docker exec -w /app -e PYTHONPATH=/app docutil-api python /app/_probe_api_keys_inside.py",
    )
    ssh.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
