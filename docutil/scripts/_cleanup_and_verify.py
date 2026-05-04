"""불필요한 --no-cache 빌드 중단 + 현재 상태 최종 확인."""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("192.168.10.39", username="idino", password="dkdlelsh@12", timeout=15)


def run(cmd, timeout=30):
    _, so, _ = ssh.exec_command(cmd, timeout=timeout)
    return so.read().decode(errors="replace")


# 1. 불필요한 nocache 빌드 프로세스 찾아서 kill
print("=== 1. 불필요한 --no-cache 프로세스 탐지/종료 ===")
print(run("pgrep -af 'docker compose build --no-cache' | head -5"))
# 발견 시 kill
print(run("pkill -f 'docker compose build --no-cache' 2>&1; echo exit=$?"))
# 잠시 후 확인
import time
time.sleep(2)
print("kill 후:", run("pgrep -af 'docker compose build --no-cache' | head -5") or "(없음)")
# buildkit 프로세스도 함께
print(run("pgrep -af 'buildkitd\\|buildkit-runc' | head -5"))

# 2. 컨테이너 최종 상태
print("\n=== 2. 컨테이너 상태 ===")
print(run(
    "cd /home/idino/docutil && "
    "docker compose ps --format 'table {{.Service}}\t{{.Status}}\t{{.CreatedAt}}' | head -20",
    timeout=30,
))

# 3. api, celery StartedAt 재확인
print("\n=== 3. 재기동 시각 ===")
print(run(
    "docker inspect docutil-api --format 'api StartedAt: {{.State.StartedAt}} Image: {{.Image}}' 2>&1; "
    "docker inspect docutil-celery-worker-1 --format 'celery StartedAt: {{.State.StartedAt}} Image: {{.Image}}' 2>&1"
))

# 4. 이미지 내부 코드 mtime
print("\n=== 4. 이미지 내부 D8 코드 mtime ===")
print(run(
    "docker exec docutil-api stat -c '%y %n' "
    "/app/app/integrations/llm/schema_adapter.py "
    "/app/app/modules/documents_v2/service.py "
    "/app/app/modules/documents_v2/router.py 2>&1",
    timeout=30,
))

# 5. API 헬스
print("\n=== 5. API 헬스체크 ===")
print(run("docker exec docutil-api curl -sf http://localhost:8000/health 2>&1"))

ssh.close()
