#!/bin/bash
set -euo pipefail

# =============================================================================
# 06_backup_database.sh - 데이터베이스 백업 스크립트
# 카테고리: 백업
# 설명: PostgreSQL 데이터베이스 백업
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 환경 변수 (docker-compose.yml에서 가져옴)
DB_NAME="${POSTGRES_DB:-docutil}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_CONTAINER="docutil-postgres"

echo "=========================================="
echo "데이터베이스 백업 시작"
echo "=========================================="

# 백업 디렉토리 생성
mkdir -p "$BACKUP_DIR"

BACKUP_FILE="$BACKUP_DIR/db_backup_${TIMESTAMP}.sql"

echo "[1/3] 데이터베이스 덤프 생성..."
docker exec $DB_CONTAINER pg_dump -U $DB_USER $DB_NAME > "$BACKUP_FILE"

echo "[2/3] 백업 파일 압축..."
gzip "$BACKUP_FILE"

echo "[3/3] 오래된 백업 정리 (7일 이상)..."
find "$BACKUP_DIR" -name "db_backup_*.sql.gz" -mtime +7 -delete

echo "=========================================="
echo "백업 완료: ${BACKUP_FILE}.gz"
echo "=========================================="

# 백업 파일 목록
echo "현재 백업 파일:"
ls -lh "$BACKUP_DIR"/*.gz 2>/dev/null || echo "  백업 파일 없음"
