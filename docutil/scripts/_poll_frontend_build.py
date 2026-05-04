"""프론트 빌드 완료 대기. 30초 간격, 최대 20분."""
import paramiko
import sys
import time

for i in range(40):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect("192.168.10.39", username="idino", password="dkdlelsh@12", timeout=15)
        _, so, _ = ssh.exec_command(
            "grep -E 'FE_DONE|FE_FAIL|=== fe (build|up) ok' /tmp/frontend_build.log 2>/dev/null | tail -5;"
            "echo '---tail---';"
            "tail -3 /tmp/frontend_build.log 2>/dev/null",
            timeout=15,
        )
        out = so.read().decode(errors="replace").strip()
        ssh.close()
        # 배너 한 줄로 축약
        first_line = (out.splitlines() or [""])[0][:150]
        print(f"[poll {i+1:02d}] {first_line}", flush=True)
        if "FE_DONE" in out:
            print("FE_DONE_DETECTED", flush=True)
            sys.exit(0)
        if "FE_FAIL" in out:
            print("FE_FAIL_DETECTED", flush=True)
            sys.exit(1)
    except Exception as e:
        print(f"[poll {i+1:02d}] error: {e!r}", flush=True)
    time.sleep(30)

print("TIMEOUT", flush=True)
sys.exit(2)
