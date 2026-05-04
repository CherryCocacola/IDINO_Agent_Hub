#!/bin/bash
set -euo pipefail

# =============================================================================
# 02_run_migrations.sh - 데이터베이스 마이그레이션 스크립트
# 카테고리: 데이터베이스
# 설명: Alembic을 사용하여 데이터베이스 스키마 마이그레이션 실행
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo "=========================================="
echo "데이터베이스 마이그레이션 시작"
echo "=========================================="

cd "$PROJECT_ROOT/backend"

# 마이그레이션 실행
echo "[1/2] 마이그레이션 상태 확인..."
docker-compose exec -T api alembic current

echo "[2/2] 마이그레이션 실행..."
docker-compose exec -T api alembic upgrade head

echo "=========================================="
echo "데이터베이스 마이그레이션 완료"
echo "=========================================="

# 현재 버전 확인
docker-compose exec -T api alembic current
