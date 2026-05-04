#!/bin/bash
set -euo pipefail

# =============================================================================
# 07_restore_database.sh - 데이터베이스 복원 스크립트
# 카테고리: 백업
# 설명: PostgreSQL 데이터베이스 복원
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"

# 환경 변수
DB_NAME="${POSTGRES_DB:-docutil}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_CONTAINER="docutil-postgres"

echo "=========================================="
echo "데이터베이스 복원"
echo "=========================================="

# 백업 파일 확인
if [ -z "${1:-}" ]; then
    echo "사용법: $0 <백업파일.sql.gz>"
    echo ""
    echo "사용 가능한 백업 파일:"
    ls -lh "$BACKUP_DIR"/*.gz 2>/dev/null || echo "  백업 파일 없음"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "오류: 백업 파일을 찾을 수 없습니다: $BACKUP_FILE"
    exit 1
fi

# 확인 프롬프트
echo "경고: 이 작업은 현재 데이터베이스를 덮어씁니다!"
echo "복원할 파일: $BACKUP_FILE"
read -p "계속 진행하시겠습니까? (y/N): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "복원이 취소되었습니다."
    exit 0
fi

echo "[1/3] 백업 파일 압축 해제..."
TEMP_FILE=$(mktemp)
gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"

echo "[2/3] 데이터베이스 복원..."
docker exec -i $DB_CONTAINER psql -U $DB_USER $DB_NAME < "$TEMP_FILE"

echo "[3/3] 임시 파일 정리..."
rm -f "$TEMP_FILE"

echo "=========================================="
echo "데이터베이스 복원 완료"
echo "=========================================="
