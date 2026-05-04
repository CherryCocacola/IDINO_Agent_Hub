"""서버 /tmp/d8_build.log 전체 덤프 + 이미지 상태."""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("192.168.10.39", username="idino", password="dkdlelsh@12", timeout=15)

print("=== d8_build.log 전체 ===")
_, so, _ = ssh.exec_command("cat /tmp/d8_build.log 2>&1 | tail -150", timeout=15)
print(so.read().decode(errors="replace"))

print("\n=== /tmp/d8_build.log 크기 ===")
_, so, _ = ssh.exec_command("ls -la /tmp/d8_build.log 2>&1", timeout=10)
print(so.read().decode(errors="replace"))

print("\n=== docker compose build/up 프로세스 ===")
_, so, _ = ssh.exec_command("pgrep -af 'docker compose' | head -10", timeout=10)
print(so.read().decode(errors="replace") or "(없음)")

print("\n=== docker compose images api celery-worker ===")
_, so, _ = ssh.exec_command(
    "cd /home/idino/docutil && docker compose images api celery-worker 2>&1",
    timeout=15,
)
print(so.read().decode(errors="replace"))

print("\n=== docutil-api 컨테이너 StartedAt ===")
_, so, _ = ssh.exec_command(
    "docker inspect docutil-api --format '{{.State.StartedAt}}' 2>&1;"
    "docker inspect docutil-celery-worker-1 --format '{{.State.StartedAt}}' 2>&1",
    timeout=10,
)
print(so.read().decode(errors="replace"))

print("\n=== docker images | head ===")
_, so, _ = ssh.exec_command(
    "docker images | grep -E 'docutil-api|docutil-celery' | head -10",
    timeout=10,
)
print(so.read().decode(errors="replace"))

ssh.close()
