"""서버 api/celery 이미지 재빌드 + 재기동 (nohup 백그라운드).

paramiko PipeTimeout 없이 동작하도록:
1) nohup으로 빌드 명령을 서버 측 백그라운드 실행
2) 로그 파일 `/tmp/d8_build.log`에 출력 저장
3) 완료 마커 `BUILD_DONE` 또는 `BUILD_FAIL` 로 polling 가능
"""
import paramiko

SERVER = "192.168.10.39"
USER = "idino"
PASS = "dkdlelsh@12"
REMOTE_DIR = "/home/idino/docutil"

BUILD_CMD = (
    f"cd {REMOTE_DIR} && "
    "( "
    "echo '=== build start ===' && "
    "docker compose build api celery-worker && "
    "echo '=== build ok ===' && "
    "docker compose up -d --force-recreate api celery-worker && "
    "echo '=== up ok ===' && "
    "sleep 8 && "
    "docker compose restart nginx && "
    "echo 'BUILD_DONE' "
    ") || echo 'BUILD_FAIL'"
)

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASS, timeout=15)
    print("[접속 성공]")

    # 기존 로그 삭제
    ssh.exec_command("rm -f /tmp/d8_build.log", timeout=5)

    # nohup으로 서버 측 백그라운드 실행
    remote = (
        f"nohup bash -c \"{BUILD_CMD}\" > /tmp/d8_build.log 2>&1 &"
        " disown"
    )
    # setsid로 더 확실하게 detach
    remote = (
        "setsid bash -c '"
        + BUILD_CMD.replace("'", "'\"'\"'")
        + "' > /tmp/d8_build.log 2>&1 < /dev/null &"
    )
    print("[빌드 명령 시작]")
    _, stdout, stderr = ssh.exec_command(remote, timeout=10)
    # 채널을 바로 닫아도 setsid로 detach된 프로세스는 계속 돈다
    print("stdout:", stdout.read().decode(errors="replace")[:200])
    print("stderr:", stderr.read().decode(errors="replace")[:200])

    # 프로세스가 실제로 기동됐는지 확인
    import time
    time.sleep(2)
    _, s2, _ = ssh.exec_command(
        "ps -ef | grep -E 'docker compose build|BUILD_DONE' | grep -v grep | head -5",
        timeout=10,
    )
    print("---확인: 백그라운드 프로세스---")
    print(s2.read().decode(errors="replace"))

    # 로그 첫 줄 확인
    _, s3, _ = ssh.exec_command("head -5 /tmp/d8_build.log 2>&1", timeout=10)
    print("---로그 초기:---")
    print(s3.read().decode(errors="replace"))

    ssh.close()
    print("[detach 완료 — 서버 측에서 빌드 진행 중]")
    print("polling: ssh + tail /tmp/d8_build.log  또는  grep 'BUILD_DONE|BUILD_FAIL'")


if __name__ == "__main__":
    main()
