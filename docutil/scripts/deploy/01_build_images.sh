#!/bin/bash
set -euo pipefail

# =============================================================================
# 01_build_images.sh - Docker 이미지 빌드 스크립트
# 카테고리: 빌드
# 설명: API 및 Frontend Docker 이미지 빌드
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo "=========================================="
echo "Docker 이미지 빌드 시작"
echo "=========================================="

cd "$PROJECT_ROOT"

# API 이미지 빌드
echo "[1/2] API 이미지 빌드 중..."
docker build -t docutil-api:latest -f backend/Dockerfile backend/

# Frontend 이미지 빌드
echo "[2/2] Frontend 이미지 빌드 중..."
docker build -t docutil-frontend:latest -f frontend/Dockerfile frontend/

echo "=========================================="
echo "Docker 이미지 빌드 완료"
echo "=========================================="

# 빌드된 이미지 확인
docker images | grep docutil
