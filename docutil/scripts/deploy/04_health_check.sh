#!/bin/bash
set -euo pipefail

# =============================================================================
# 04_health_check.sh - 서비스 상태 점검 스크립트
# 카테고리: 모니터링
# 설명: API 및 Frontend 서비스 상태 확인
# =============================================================================

API_URL="${API_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
MAX_RETRIES=5
RETRY_INTERVAL=5

echo "=========================================="
echo "서비스 상태 점검 시작"
echo "=========================================="

check_service() {
    local name="$1"
    local url="$2"
    local endpoint="$3"
    local retries=0

    echo "[$name] 상태 확인 중..."

    while [ $retries -lt $MAX_RETRIES ]; do
        if curl -sf "${url}${endpoint}" > /dev/null 2>&1; then
            echo "  ✓ $name 정상 동작 중"
            return 0
        fi
        retries=$((retries + 1))
        echo "  재시도 $retries/$MAX_RETRIES..."
        sleep $RETRY_INTERVAL
    done

    echo "  ✗ $name 응답 없음"
    return 1
}

# API 상태 확인
echo "[1/3] API 서비스 점검..."
check_service "API" "$API_URL" "/health" || API_STATUS="FAIL"
API_STATUS="${API_STATUS:-OK}"

# Frontend 상태 확인
echo "[2/3] Frontend 서비스 점검..."
check_service "Frontend" "$FRONTEND_URL" "/" || FRONTEND_STATUS="FAIL"
FRONTEND_STATUS="${FRONTEND_STATUS:-OK}"

# Docker 컨테이너 상태
echo "[3/3] Docker 컨테이너 상태..."
docker-compose ps

echo "=========================================="
echo "상태 점검 결과"
echo "=========================================="
echo "  API:      $API_STATUS"
echo "  Frontend: $FRONTEND_STATUS"
echo "=========================================="

if [ "$API_STATUS" = "FAIL" ] || [ "$FRONTEND_STATUS" = "FAIL" ]; then
    exit 1
fi
