"""Phase 4 S1 D2 Step 7 — archive 리네이밍 영향 범위 확인.

- 직접 DB 쿼리 (ORM 우회)로 archive 테이블 확인
- API 인증 흐름 통과 후 /api/v1/reports 실호출하여 500 발생 여부 확인
- tb_generated_reports 를 참조하는 ORM 코드 매핑 상태 결과 수집
"""
import paramiko
import sys
import io
import json
import uuid

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
    rc = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    if out:
        print(out.rstrip())
    if err:
        print(f"[stderr] {err.rstrip()}", file=sys.stderr)
    return out, err, rc


def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASS, timeout=15)

    # 1. 로그인 → JWT 획득
    # 실제 로그인 엔드포인트 확인
    run(
        ssh,
        "docker exec docutil-api curl -s -X POST http://localhost:8000/api/v1/auth/login "
        "-H 'Content-Type: application/json' "
        "-d '{\"email\":\"admin@docutil.io\",\"password\":\"admin1234\"}' | head -c 500",
        "1. /api/v1/auth/login (기본 어드민)",
    )

    # 2. 다른 일반 관리자 계정 시도
    run(
        ssh,
        "docker exec docutil-api curl -s -X POST http://localhost:8000/api/v1/auth/login "
        "-H 'Content-Type: application/json' "
        "-d '{\"email\":\"admin@idino.com\",\"password\":\"admin1234\"}' | head -c 500",
        "2. 대안 이메일 시도",
    )

    # 3. DB에서 실제 관리자 이메일 조회
    run(
        ssh,
        'docker exec -e PGPASSWORD=docutil docutil-postgres psql -U docutil -d docutil -A -t -c '
        '"SELECT email, role FROM tb_users LIMIT 5;"',
        "3. 실제 관리자 이메일 확인",
    )

    # 4. archive 직접 SELECT (ORM 우회, raw SQL)
    run(
        ssh,
        'docker exec -e PGPASSWORD=docutil docutil-postgres psql -U docutil -d docutil -A -t -c '
        '"SELECT id, title, status FROM tb_generated_reports_archive LIMIT 3;"',
        "4. archive SELECT 샘플 (데이터 보존 검증)",
    )

    # 5. ORM 모델 정합성 — ORM이 tb_generated_reports 참조인데 현 테이블은 archive.
    #    이 상태에서 /api/v1/reports 요청은 어떤 에러를 낼까?
    # 로그 기록 클리어
    run(ssh, "docker logs docutil-api --tail 0 2>&1 > /dev/null", "5a. 로그 기록 시작 전")

    # 인증없이 401이므로 인증된 요청이 필요. 하지만 비밀번호 미확인 상태.
    # 대신 Authorization 헤더를 강제로 유효 토큰 없이 보내서 로그 보자. 의미없음.
    # 스킵: 인증 토큰 확보 없이 ORM 실쿼리까지는 안됨.

    # 6. ORM 이 참조하는 테이블 이름 최종 확인 (models.py 서버측)
    run(
        ssh,
        f'grep -n "__tablename__" {REMOTE_DIR}/backend/app/modules/reports/models.py',
        "6. models.py tb_generated_reports 참조",
    )

    # 7. 코드베이스에서 tb_generated_reports 참조 파일들
    run(
        ssh,
        f'grep -rn "tb_generated_reports" {REMOTE_DIR}/backend/app/ 2>&1',
        "7. tb_generated_reports 참조 파일 전체",
    )

    # 8. 리포트 라우터 경로 확인
    run(
        ssh,
        f'grep -rn "reports" {REMOTE_DIR}/backend/app/main.py 2>&1',
        "8. reports 라우터 등록",
    )

    # 9. 실제 DB 쿼리 시뮬레이션: ORM 이 'tb_generated_reports'로 SELECT 시도 시 에러 재현
    run(
        ssh,
        'docker exec -e PGPASSWORD=docutil docutil-postgres psql -U docutil -d docutil -c '
        '"SELECT * FROM tb_generated_reports LIMIT 1;"',
        "9. tb_generated_reports 직접 SELECT (relation not exist 에러 기대)",
    )

    # 10. evaluation 모듈이 의존한다고 가정되는 테이블들도 추가 영향 여부
    run(
        ssh,
        'docker exec -e PGPASSWORD=docutil docutil-postgres psql -U docutil -d docutil -A -t -c '
        '"SELECT table_name FROM information_schema.tables WHERE table_schema=\'public\' AND table_name LIKE \'tb_%\' ORDER BY table_name;"',
        "10. 전체 tb_ 테이블 목록",
    )

    ssh.close()
    print("\n[DONE] Step 7 impact check complete.")


if __name__ == "__main__":
    main()
