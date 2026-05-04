"""Phase 4 S1 D2 Step 1 — 현재 상태 스냅샷.

실행 순서:
- alembic current
- tb_documents_v2 / tb_documents_v2_templates 존재 여부 (없어야 정상)
- tb_generated_reports 존재 여부 + 행수 (49건 예상)
- tb_agents.agent_type DISTINCT
- 007 migration 파일이 서버에 이미 존재하는지
"""
import paramiko
import sys
import io

# Windows CP949 콘솔에서 UTF-8로 출력 강제 (서버 출력 한글/하이픈 처리)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SERVER = "192.168.10.39"
USER = "idino"
PASS = "dkdlelsh@12"
REMOTE_DIR = "/home/idino/docutil"


def run(ssh, cmd, label, timeout=60):
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
    print(f"[OK] Connected to {SERVER}")

    # 1. 디렉토리 존재 확인
    run(ssh, f"ls -la {REMOTE_DIR}/ | head -20", "1. docutil 디렉토리")

    # 2. 컨테이너 상태
    run(ssh, "docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E '(docutil|postgres|api)'", "2. 컨테이너 상태")

    # 3. Alembic current
    run(
        ssh,
        f"cd {REMOTE_DIR} && docker exec docutil-api alembic current 2>&1",
        "3. Alembic current",
    )

    # 4. 007 migration 파일 존재 확인 (서버측 복사본)
    run(
        ssh,
        f"ls -la {REMOTE_DIR}/backend/alembic/versions/ | grep -E '(006|007)'",
        "4. Migration 파일 목록",
    )

    # 5. 서버측 007 파일 head/tail (revision 확인)
    run(
        ssh,
        f"head -50 {REMOTE_DIR}/backend/alembic/versions/007_documents_v2_and_template_consolidation.py 2>&1",
        "5. 서버측 007 파일 head",
    )

    # 6. 데이터베이스 상태 점검 SQL
    psql = (
        'docker exec -e PGPASSWORD=docutil docutil-postgres psql -U docutil -d docutil -A -t -c '
    )

    # 6a. tb_documents_v2 존재 여부
    run(
        ssh,
        psql + '"SELECT table_name FROM information_schema.tables WHERE table_schema=\'public\' AND table_name IN (\'tb_documents_v2\', \'tb_documents_v2_templates\', \'tb_generated_reports\', \'tb_generated_reports_archive\') ORDER BY table_name;"',
        "6a. 관련 테이블 존재 여부",
    )

    # 6b. tb_generated_reports 행수
    run(
        ssh,
        psql + '"SELECT COUNT(*) FROM tb_generated_reports;"',
        "6b. tb_generated_reports 행수",
    )

    # 6c. tb_agents 행수 + agent_type DISTINCT
    run(
        ssh,
        psql + '"SELECT agent_type, COUNT(*) FROM tb_agents GROUP BY agent_type ORDER BY agent_type;"',
        "6c. tb_agents.agent_type 분포",
    )

    # 6d. tb_agents CHECK 제약 유무
    run(
        ssh,
        psql + '"SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = \'tb_agents\'::regclass AND contype = \'c\';"',
        "6d. tb_agents 기존 CHECK 제약",
    )

    # 6e. alembic_version 테이블 실제 값
    run(
        ssh,
        psql + '"SELECT version_num FROM alembic_version;"',
        "6e. alembic_version 테이블",
    )

    # 6f. tb_generated_reports 스키마
    run(
        ssh,
        psql + '"SELECT column_name, data_type FROM information_schema.columns WHERE table_name=\'tb_generated_reports\' ORDER BY ordinal_position;"',
        "6f. tb_generated_reports 스키마",
    )

    # 6g. 주요 FK 참조자 (archive 리네이밍 영향 점검)
    run(
        ssh,
        psql + '"SELECT conname, conrelid::regclass AS table_name, pg_get_constraintdef(oid) FROM pg_constraint WHERE contype = \'f\' AND confrelid = \'tb_generated_reports\'::regclass;"',
        "6g. tb_generated_reports를 참조하는 FK",
    )

    # 7. backup 디렉토리 존재 확인 / 생성
    run(
        ssh,
        f"mkdir -p {REMOTE_DIR}/backups && ls -la {REMOTE_DIR}/backups/",
        "7. backups 디렉토리",
    )

    ssh.close()
    print("\n[DONE] Step 1 snapshot complete.")


if __name__ == "__main__":
    main()
