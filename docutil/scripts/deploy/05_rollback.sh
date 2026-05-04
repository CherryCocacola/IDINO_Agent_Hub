#!/bin/bash
set -euo pipefail

# =============================================================================
# 05_rollback.sh - 서비스 롤백 스크립트
# 카테고리: 배포
# 설명: 이전 버전으로 롤백
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo "=========================================="
echo "서비스 롤백 시작"
echo "=========================================="

cd "$PROJECT_ROOT"

# 이전 이미지 태그 확인
PREV_API_TAG="${PREV_API_TAG:-previous}"
PREV_FRONTEND_TAG="${PREV_FRONTEND_TAG:-previous}"

echo "롤백 대상 이미지:"
echo "  API:      docutil-api:$PREV_API_TAG"
echo "  Frontend: docutil-frontend:$PREV_FRONTEND_TAG"

# 확인 프롬프트
read -p "계속 진행하시겠습니까? (y/N): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "롤백이 취소되었습니다."
    exit 0
fi

# 서비스 중지
echo "[1/4] 서비스 중지..."
docker-compose down

# 이미지 태그 변경
echo "[2/4] 이미지 태그 변경..."
docker tag docutil-api:$PREV_API_TAG docutil-api:latest
docker tag docutil-frontend:$PREV_FRONTEND_TAG docutil-frontend:latest

# 서비스 재시작
echo "[3/4] 서비스 재시작..."
docker-compose up -d

# 상태 확인
echo "[4/4] 서비스 상태 확인..."
sleep 10
docker-compose ps

echo "=========================================="
echo "롤백 완료"
echo "=========================================="
