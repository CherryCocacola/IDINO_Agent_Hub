"""서버 빌드 완료 대기 polling. 30초 간격, 최대 20분."""
import paramiko, time, sys

for i in range(40):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect("192.168.10.39", username="idino", password="dkdlelsh@12", timeout=15)
        _, so, _ = ssh.exec_command(
            "grep -E 'BUILD_DONE|BUILD_FAIL|=== build ok|=== up ok' /tmp/d8_build.log 2>/dev/null | tail -3;"
            "echo '---TAIL---';"
            "tail -3 /tmp/d8_build.log 2>/dev/null",
            timeout=15,
        )
        out = so.read().decode(errors="replace").strip()
        ssh.close()
        print(f"[poll {i+1:02d}] {out[:400]}", flush=True)
        if "BUILD_DONE" in out or "BUILD_FAIL" in out:
            print("DETECTED", flush=True)
            sys.exit(0 if "BUILD_DONE" in out else 1)
    except Exception as e:
        print(f"[poll {i+1:02d}] error: {e!r}", flush=True)
    time.sleep(30)

print("TIMEOUT", flush=True)
sys.exit(2)
