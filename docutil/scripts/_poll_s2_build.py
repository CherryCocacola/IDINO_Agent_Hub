"""S2 통합 빌드 완료 polling. 30초 간격, 최대 25분."""
import paramiko
import sys
import time

for i in range(50):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect("192.168.10.39", username="idino", password="dkdlelsh@12", timeout=15)
        _, so, _ = ssh.exec_command(
            "grep -E 'S2_DEPLOY_DONE|S2_DEPLOY_FAIL|=== s2 build ok|=== s2 up ok' /tmp/s2_build.log 2>/dev/null | tail -5;"
            "echo '---tail---';"
            "tail -3 /tmp/s2_build.log 2>/dev/null",
            timeout=15,
        )
        out = so.read().decode(errors="replace").strip()
        ssh.close()
        first = (out.splitlines() or [""])[0][:150]
        print(f"[poll {i+1:02d}] {first}", flush=True)
        if "S2_DEPLOY_DONE" in out:
            print("S2_DEPLOY_DONE_DETECTED", flush=True)
            sys.exit(0)
        if "S2_DEPLOY_FAIL" in out:
            print("S2_DEPLOY_FAIL_DETECTED", flush=True)
            sys.exit(1)
    except Exception as e:
        print(f"[poll {i+1:02d}] error: {e!r}", flush=True)
    time.sleep(30)

print("TIMEOUT", flush=True)
sys.exit(2)
