"""Phase 4 S1 D2 Step 5 — Migration 적용 검증.

- 신규 테이블 스키마 (\d+ 대체 — information_schema 사용)
- 인덱스 목록 (GIN 포함)
- CHECK 제약 목록
- tb_generated_reports / tb_generated_reports_archive 전환 확인 및 행수 보존
- tb_agents CHECK 5종 확정
- 기존 데이터 무결성
"""
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SERVER = "192.168.10.39"
USER = "idino"
PASS = "dkdlelsh@12"
REMOTE_DIR = "/home/idino/docutil"

PSQL = (
    "docker exec -e PGPASSWORD=docutil docutil-postgres "
    "psql -U docutil -d docutil"
)


def run(ssh, cmd, label, timeout=60):
    print(f"\n--- {label} ---")
    print(f"$ {cmd}")
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    rc = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    if out:
        print(out.rstrip())
    if err:
        print(f"[stderr] {err.rstrip()}", file=sys.stderr)
    return out, err, rc


def psql_q(sql, label, ssh, timeout=60, flags="-A -t"):
    """psql 쿼리 실행 헬퍼."""
    # 따옴표 이스케이프: 외부 쉘로 전달되므로 $'...' 사용 또는 heredoc
    cmd = f"{PSQL} {flags} -c \"{sql}\""
    return run(ssh, cmd, label, timeout)


def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASS, timeout=15)

    # ========================================================================
    # A. 테이블 존재 확인
    # ========================================================================
    psql_q(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('tb_documents_v2', 'tb_documents_v2_templates', 'tb_generated_reports', 'tb_generated_reports_archive') ORDER BY table_name;",
        "A1. 관련 4종 테이블 존재 확인",
        ssh,
    )

    # ========================================================================
    # B. tb_documents_v2 상세 스키마 (\d+ 대체)
    # ========================================================================
    psql_q(
        "SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_name='tb_documents_v2' ORDER BY ordinal_position;",
        "B1. tb_documents_v2 컬럼 (\d+ 대체)",
        ssh,
        flags="",
    )

    psql_q(
        "SELECT indexname, indexdef FROM pg_indexes WHERE tablename='tb_documents_v2' ORDER BY indexname;",
        "B2. tb_documents_v2 인덱스 (GIN + B-tree 7개)",
        ssh,
        flags="",
    )

    psql_q(
        "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid='tb_documents_v2'::regclass ORDER BY contype, conname;",
        "B3. tb_documents_v2 제약 (CHECK/FK/UNIQUE)",
        ssh,
        flags="",
    )

    # ========================================================================
    # C. tb_documents_v2_templates 상세
    # ========================================================================
    psql_q(
        "SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_name='tb_documents_v2_templates' ORDER BY ordinal_position;",
        "C1. tb_documents_v2_templates 컬럼",
        ssh,
        flags="",
    )

    psql_q(
        "SELECT indexname, indexdef FROM pg_indexes WHERE tablename='tb_documents_v2_templates' ORDER BY indexname;",
        "C2. tb_documents_v2_templates 인덱스",
        ssh,
        flags="",
    )

    psql_q(
        "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid='tb_documents_v2_templates'::regclass ORDER BY contype, conname;",
        "C3. tb_documents_v2_templates 제약",
        ssh,
        flags="",
    )

    # ========================================================================
    # D. tb_generated_reports → archive 리네이밍 확인
    # ========================================================================
    psql_q(
        "SELECT COUNT(*) AS rows_archive FROM tb_generated_reports_archive;",
        "D1. archive 테이블 행 수 (57건 보존 기대)",
        ssh,
        flags="",
    )

    psql_q(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name='tb_generated_reports';",
        "D2. 원본 tb_generated_reports (없어야 정상)",
        ssh,
        flags="",
    )

    psql_q(
        "SELECT indexname FROM pg_indexes WHERE tablename='tb_generated_reports_archive' ORDER BY indexname;",
        "D3. archive 테이블 인덱스 (자동 이동됨)",
        ssh,
        flags="",
    )

    # ========================================================================
    # E. tb_agents CHECK 5종 + 데이터 무결성
    # ========================================================================
    psql_q(
        "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid='tb_agents'::regclass AND contype='c';",
        "E1. tb_agents CHECK 제약 (ck_tb_agents_agent_type 기대)",
        ssh,
        flags="",
    )

    psql_q(
        "SELECT agent_type, COUNT(*) FROM tb_agents GROUP BY agent_type ORDER BY agent_type;",
        "E2. tb_agents 데이터 (chatbot/minutes/proposal/report 각 1)",
        ssh,
        flags="",
    )

    # CHECK 위반 값 존재 여부 (0이 정상)
    psql_q(
        "SELECT COUNT(*) FROM tb_agents WHERE agent_type NOT IN ('chatbot','report','proposal','minutes','freeform_doc');",
        "E3. 허용 목록 외 agent_type 건수 (0이 정상)",
        ssh,
        flags="",
    )

    # ========================================================================
    # F. Alembic version
    # ========================================================================
    psql_q(
        "SELECT version_num FROM alembic_version;",
        "F1. alembic_version 테이블 (007_documents_v2)",
        ssh,
        flags="",
    )

    # ========================================================================
    # G. 다른 FK 영향 체크 — tb_generated_reports를 참조하던 코드/테이블이 있는지 재확인
    # ========================================================================
    psql_q(
        "SELECT conname, conrelid::regclass AS referencing_table FROM pg_constraint WHERE contype='f' AND (confrelid='tb_generated_reports_archive'::regclass);",
        "G1. archive 테이블을 참조하는 FK (있으면 주의)",
        ssh,
        flags="",
    )

    # ========================================================================
    # H. GIN 인덱스 동작 smoke check
    # ========================================================================
    psql_q(
        "EXPLAIN SELECT 1 FROM tb_documents_v2 WHERE document_schema @> '{}'::jsonb;",
        "H1. GIN 인덱스 plan 확인 (idx_tb_documents_v2_schema_gin)",
        ssh,
        flags="",
    )

    ssh.close()
    print("\n[DONE] Step 5 verify complete.")


if __name__ == "__main__":
    main()
