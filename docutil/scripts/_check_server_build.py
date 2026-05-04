"""배포 6단계 timeout 이후 서버 상태 확인 스크립트.

배포는 파일 전송까지 완료됐으나 docker compose up --build 도중
paramiko PipeTimeout 발생. 서버에서 빌드가 계속 진행 중인지,
종료되었는지, 이미 새 이미지로 재기동 되었는지 확인한다.
"""
import paramiko
import sys

SERVER = "192.168.10.39"
USER = "idino"
PASS = "dkdlelsh@12"
REMOTE_DIR = "/home/idino/docutil"

def run(ssh, cmd, timeout=30):
    """원격 명령 실행 후 stdout 반환."""
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    return out, err


def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASS, timeout=15)
    print("[서버 접속 성공]")

    # 1. docker 빌드 프로세스가 여전히 돌고 있는지
    print("\n=== 1. docker 빌드/compose 프로세스 확인 ===")
    out, _ = run(ssh, "ps -ef | grep -E 'docker|buildkit|compose' | grep -v grep | head -20")
    print(out or "(빌드 프로세스 없음)")

    # 2. docker compose ps
    print("\n=== 2. 컨테이너 상태 ===")
    out, _ = run(ssh, f"cd {REMOTE_DIR} && docker compose ps --format 'table {{{{.Service}}}}\t{{{{.Status}}}}'")
    print(out)

    # 3. api 이미지 생성 시각
    print("\n=== 3. docutil-api 이미지 정보 ===")
    out, _ = run(ssh, "docker inspect docutil-api --format '{{.Created}} {{.State.Status}} {{.State.StartedAt}}' 2>&1")
    print(out)

    # 4. api 이미지 빌드 시각
    out, _ = run(ssh, "docker image inspect $(docker compose -f /home/idino/docutil/docker-compose.yml images api -q 2>/dev/null) --format '{{.Created}}' 2>&1 | head -5")
    print(f"이미지 Created: {out}")

    # 5. 코드 파일 수정 시각 (배포 확인용)
    print("\n=== 4. 서버 코드 최신성 확인 ===")
    out, _ = run(ssh, f"stat -c '%y %n' {REMOTE_DIR}/backend/app/integrations/llm/schema_adapter.py {REMOTE_DIR}/backend/app/modules/documents_v2/service.py {REMOTE_DIR}/backend/tests/test_documents_v2_patch.py 2>&1")
    print(out)

    # 6. 최근 api 로그
    print("\n=== 5. docutil-api 최근 로그 (10줄) ===")
    out, _ = run(ssh, "docker logs docutil-api --tail 10 2>&1")
    print(out)

    # 7. 헬스체크
    print("\n=== 6. API 헬스체크 ===")
    out, _ = run(ssh, "docker exec docutil-api curl -sf http://localhost:8000/health 2>&1")
    print(out or "(empty)")

    ssh.close()
    print("\n[점검 완료]")


if __name__ == "__main__":
    main()
