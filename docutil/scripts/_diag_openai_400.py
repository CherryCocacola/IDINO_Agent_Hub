"""단 1회 OpenAI generate_structured 호출을 수행하여 400 에러 응답 본문을 기록한다.

서버 컨테이너에서 실행될 스크립트 본체를 별도로 업로드한다.
"""

from __future__ import annotations

import os
import sys

import paramiko

SERVER = "192.168.10.39"
USER = "idino"
PASS = os.environ.get("DOCUTIL_SERVER_PASS", "dkdlelsh@12")


INSIDE_SCRIPT = r"""
import asyncio
import json
import httpx
from app.integrations.llm.schema_adapter import pydantic_to_openai_schema
from app.modules.documents_v2.schemas import DocumentSchema
from app.core.config import get_settings

settings = get_settings()
api_key = settings.openai_api_key

schema = pydantic_to_openai_schema(DocumentSchema)
payload = {
    "model": "gpt-4o",
    "messages": [
        {"role": "system", "content": "너는 JSON 생성기."},
        {"role": "user", "content": "간단한 slide_report 를 JSON 으로 만들어."},
    ],
    "temperature": 0.0,
    "max_tokens": 1024,
    "stream": False,
    "response_format": {"type": "json_schema", "json_schema": schema},
}

# 스키마 구조 검사: 최상위 크기, $defs 개수, oneOf 건수 등 요약.
as_str = json.dumps(schema)
print("[SCHEMA_JSON_LEN]", len(as_str))
print("[SCHEMA_KEYS]", sorted(schema.keys()))
inner = schema.get("schema", {})
print("[INNER_KEYS]", sorted(inner.keys()))
print("[HAS_$DEFS]", "$defs" in inner)
if "$defs" in inner:
    print("[NUM_DEFS]", len(inner["$defs"]))
print("[HAS_ONEOF]", as_str.count("oneOf"))
print("[HAS_ANYOF]", as_str.count("anyOf"))

async def call():
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            json=payload,
        )
        print("[STATUS]", r.status_code)
        print("[BODY]", r.text[:4000])

asyncio.run(call())
"""


def main() -> int:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASS, timeout=15)

    sftp = ssh.open_sftp()
    host_path = "/tmp/_diag_openai_400.py"
    with sftp.file(host_path, "wb") as f:
        f.write(INSIDE_SCRIPT.encode("utf-8"))
    sftp.close()

    _, so, _ = ssh.exec_command(
        f"docker cp {host_path} docutil-api:/app/_diag_openai_400.py", timeout=30
    )
    so.channel.recv_exit_status()

    _, so, se = ssh.exec_command(
        "docker exec -w /app -e PYTHONPATH=/app docutil-api python /app/_diag_openai_400.py",
        timeout=120,
    )
    rc = so.channel.recv_exit_status()
    print(so.read().decode("utf-8", errors="replace"))
    print("STDERR:", se.read().decode("utf-8", errors="replace"))
    ssh.close()
    return rc


if __name__ == "__main__":
    sys.exit(main())
