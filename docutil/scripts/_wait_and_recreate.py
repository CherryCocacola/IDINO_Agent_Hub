"""빌드 완료 대기 후 강제 재생성. CACHED 문제 대비 nocache 옵션 포함."""
import paramiko
import sys
import time

SERVER = "192.168.10.39"
USER = "idino"
PASS = "dkdlelsh@12"
REMOTE_DIR = "/home/idino/docutil"


def connect():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASS, timeout=15)
    return ssh


def run(ssh, cmd, timeout=30):
    _, so, se = ssh.exec_command(cmd, timeout=timeout)
    return so.read().decode(errors="replace"), se.read().decode(errors="replace")


# 1. 빌드 프로세스가 아직 살아있는지 확인 + 최대 5분 대기
print("=== 1. 기존 빌드 프로세스 대기 (최대 5분) ===")
for i in range(30):
    ssh = connect()
    out, _ = run(ssh, "pgrep -af 'docker compose build' | grep -v grep | head -3")
    ssh.close()
    if not out.strip():
        print(f"  [{i+1:02d}] 기존 빌드 종료됨")
        break
    print(f"  [{i+1:02d}] 빌드 진행 중: {out.strip()[:120]}")
    time.sleep(10)
else:
    print("  [WARN] 5분 경과 — 기존 빌드가 아직 돌고 있으나 강제 진행")

# 2. 빌드 완료 후 로그 확인
print("\n=== 2. 빌드 완료 후 로그 최종 ===")
ssh = connect()
out, _ = run(ssh, "tail -20 /tmp/d8_build.log 2>&1")
ssh.close()
print(out)

# 3. 코드가 실제로 이미지에 반영됐는지 검증 — 새 이미지를 임시 컨테이너로 띄워서 해당 코드 mtime 확인
print("\n=== 3. 이미지에 D8 코드 반영 여부 검증 ===")
ssh = connect()
verify_cmd = (
    "docker run --rm docutil-api:latest bash -c "
    "'stat -c \"%y %n\" "
    "/app/integrations/llm/schema_adapter.py "
    "/app/modules/documents_v2/service.py 2>/dev/null || "
    "stat -c \"%y %n\" "
    "/app/app/integrations/llm/schema_adapter.py "
    "/app/app/modules/documents_v2/service.py 2>/dev/null' 2>&1"
)
out, _ = run(ssh, verify_cmd, timeout=60)
print(out)
ssh.close()

# 4. CACHED 판정 문제 탐지: 최신 COPY가 반영 안 됐으면 --no-cache 재빌드 필요
needs_nocache = "Apr 22" not in out or ("07:29" not in out and "07:31" not in out)
print(f"\n=== 4. --no-cache 재빌드 필요? {needs_nocache} ===")

if needs_nocache:
    print("  CACHED 판정으로 D8 변경이 이미지에 없음 — --no-cache 재빌드 실행")
    ssh = connect()
    nocache_cmd = (
        "rm -f /tmp/d8_build2.log && "
        "setsid bash -c '"
        f"cd {REMOTE_DIR} && "
        "echo \"=== nocache build start ===\" && "
        "docker compose build --no-cache api celery-worker && "
        "echo \"=== nocache build ok ===\" && "
        "docker compose up -d --force-recreate api celery-worker && "
        "echo \"=== up ok ===\" && "
        "sleep 8 && "
        "docker compose restart nginx && "
        "echo BUILD2_DONE "
        "' > /tmp/d8_build2.log 2>&1 < /dev/null &"
    )
    run(ssh, nocache_cmd, timeout=10)
    time.sleep(2)
    out, _ = run(ssh, "pgrep -af 'docker compose build --no-cache' | head -3", timeout=10)
    print("  새 빌드 프로세스:", out.strip() or "(시작 실패)")
    ssh.close()
    print("  → scripts/_poll_build2.py 로 폴링 필요")
else:
    print("  D8 코드 반영 확인됨 — up --force-recreate만 실행")
    ssh = connect()
    out, _ = run(
        ssh,
        f"cd {REMOTE_DIR} && docker compose up -d --force-recreate api celery-worker 2>&1",
        timeout=120,
    )
    print(out[-600:])
    out, _ = run(ssh, f"cd {REMOTE_DIR} && docker compose restart nginx 2>&1", timeout=30)
    print(out)
    ssh.close()

print("\n=== 완료 ===")
