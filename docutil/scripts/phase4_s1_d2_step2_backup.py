"""Phase 4 S1 D2 Step 2 — pg_dump 전체 백업.

- /home/idino/docutil/backups/pre_007_YYYYMMDD_HHMM.sql
- 파일 크기 확인
- 복원 명령 예시 출력
"""
import paramiko
import sys
import io
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SERVER = "192.168.10.39"
USER = "idino"
PASS = "dkdlelsh@12"
REMOTE_DIR = "/home/idino/docutil"


def run(ssh, cmd, label, timeout=300):
    print(f"\n--- {label} ---")
    print(f"$ {cmd}")
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    if out:
        print(out.rstrip())
    if err:
        print(f"[stderr] {err.rstrip()}", file=sys.stderr)
    return out, err


def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASS, timeout=15)

    # 백업 파일명 (서버 로컬 시간대 기준)
    run(ssh, "date '+%Y-%m-%d %H:%M:%S %Z'", "서버 현재 시각")

    # 한국 시간대 기준 타임스탬프로 통일
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    backup_file = f"{REMOTE_DIR}/backups/pre_007_{stamp}.sql"

    print(f"\n백업 대상 파일: {backup_file}")

    # PostgreSQL 비밀번호 확인 — .env 에서 읽기
    run(ssh, f"grep -E 'POSTGRES_(USER|PASSWORD|DB)=' {REMOTE_DIR}/.env", ".env DB 설정")

    # pg_dump 실행 (컨테이너 내부에서 수행 후 host 파일로 복사)
    # docker exec 로 직접 파일 쓰기는 볼륨 경로를 모르므로 stdout 리다이렉트가 안전
    cmd = (
        f"docker exec -e PGPASSWORD=docutil docutil-postgres "
        f"pg_dump -U docutil -d docutil --no-owner --no-privileges "
        f"> {backup_file} 2>/tmp/pg_dump_err.log"
    )
    run(ssh, cmd, "pg_dump 실행", timeout=600)

    run(ssh, "cat /tmp/pg_dump_err.log", "pg_dump stderr 로그")

    # 파일 크기 확인
    run(ssh, f"ls -la {backup_file}", "백업 파일 크기")
    run(ssh, f"du -h {backup_file}", "백업 파일 용량 (사람 읽기)")
    run(ssh, f"head -20 {backup_file}", "백업 파일 헤더")
    run(ssh, f"tail -5 {backup_file}", "백업 파일 꼬리")

    # 핵심 테이블 DDL 존재 확인 (dump 내용 정합)
    run(
        ssh,
        f"grep -c 'CREATE TABLE public.tb_' {backup_file}",
        "CREATE TABLE 개수 (50+ 예상)",
    )
    run(
        ssh,
        f"grep -c 'COPY public.tb_generated_reports' {backup_file}",
        "tb_generated_reports COPY 섹션",
    )

    # 롤백 명령 예시
    print("\n=== 롤백 시 복원 명령 (기록용) ===")
    print(f"cat {backup_file} | docker exec -i -e PGPASSWORD=docutil docutil-postgres psql -U docutil -d docutil")

    # 경로를 파일로 남겨 후속 스크립트가 참조 가능하도록
    pointer = f"{REMOTE_DIR}/backups/LATEST_PRE_007.txt"
    run(ssh, f"echo {backup_file} > {pointer} && cat {pointer}", "백업 경로 포인터 저장")

    ssh.close()
    print(f"\n[DONE] Step 2 backup complete: {backup_file}")


if __name__ == "__main__":
    main()
