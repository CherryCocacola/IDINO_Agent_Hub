"""서버에 이미 전송된 파일로 프론트엔드만 재빌드하는 스크립트.

deploy_to_server.py 실행 후 호출한다. Next.js(NEXT_PUBLIC_* 빌드타임 변수)
특성상 소스 변경이 있으면 반드시 `--no-cache` 로 재빌드해야 한다.

단계:
  1. 기존 BuildKit 캐시 정리 (docker builder prune -af)
  2. 프론트 이미지 --no-cache 재빌드
  3. frontend + nginx 강제 재기동
  4. 헬스 체크 (Nginx 80 → frontend:3002)
"""

import time

import paramiko

SERVER = "192.168.10.39"
USER = "idino"
PASS = "dkdlelsh@12"
REMOTE_DIR = "/home/idino/docutil"


def run(ssh, cmd, timeout=900):
    """SSH 로 원격 명령을 실행하고 (exit_code, output) 을 반환한다."""
    _, stdout, _ = ssh.exec_command(cmd, timeout=timeout)
    text = stdout.read().decode("utf-8", errors="replace")
    exit_code = stdout.channel.recv_exit_status()
    return exit_code, text


def main() -> None:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("=== 서버 접속 ===")
    ssh.connect(SERVER, username=USER, password=PASS, timeout=15)
    print("  접속 성공")

    print("=== 1. BuildKit 캐시 정리 ===")
    code, out = run(ssh, f"cd {REMOTE_DIR} && docker builder prune -af 2>&1", timeout=180)
    print(out[-400:])

    print("=== 2. 프론트 이미지 재빌드 (--no-cache) ===")
    code, out = run(
        ssh,
        f"cd {REMOTE_DIR} && docker compose build --no-cache frontend 2>&1",
        timeout=1800,
    )
    tail = out[-800:]
    print(tail)
    if code != 0:
        print(f"  FAILED: exit={code}")
        ssh.close()
        return

    print("=== 3. frontend + nginx 강제 재기동 ===")
    code, out = run(
        ssh,
        f"cd {REMOTE_DIR} && docker compose up -d --force-recreate frontend nginx 2>&1",
        timeout=120,
    )
    print(out[-400:])

    print("=== 4. 헬스 체크 ===")
    for attempt in range(6):
        time.sleep(8)
        code, out = run(
            ssh,
            "curl -sf -o /dev/null -w '%{http_code}' http://localhost/ 2>&1",
            timeout=15,
        )
        if out.strip().startswith("2") or out.strip().startswith("3"):
            print(f"  Nginx OK (attempt {attempt + 1}, http={out.strip()})")
            break
        print(f"  attempt {attempt + 1}: http={out.strip()}")
    else:
        print("  WARNING: Nginx health check failed after ~48s")

    print("=== 완료 ===")
    ssh.close()


if __name__ == "__main__":
    main()
