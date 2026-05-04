#!/bin/bash
set -euo pipefail

# =============================================================================
# 00_cleanup_server.sh - 서버 정리 스크립트
# 카테고리: 배포 준비
# 설명: 배포 전 서버의 기존 컨테이너 및 이미지 정리
# =============================================================================

echo "=========================================="
echo "서버 정리 시작"
echo "=========================================="

# Docker 컨테이너 중지 및 삭제
echo "[1/4] Docker 컨테이너 정리 중..."
docker-compose down --remove-orphans 2>/dev/null || true
docker container prune -f

# Docker 이미지 정리
echo "[2/4] 사용하지 않는 Docker 이미지 정리 중..."
docker image prune -f

# Docker 볼륨 정리 (데이터 보존 필요시 주석 처리)
echo "[3/4] 사용하지 않는 Docker 볼륨 정리 중..."
docker volume prune -f

# Docker 네트워크 정리
echo "[4/4] 사용하지 않는 Docker 네트워크 정리 중..."
docker network prune -f

echo "=========================================="
echo "서버 정리 완료"
echo "=========================================="
