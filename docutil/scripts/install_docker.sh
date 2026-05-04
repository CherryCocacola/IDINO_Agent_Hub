#!/bin/bash
set -e

echo "=== Docker 저장소 설정 ==="
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu noble stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
cat /etc/apt/sources.list.d/docker.list

echo "=== apt update ==="
apt-get update -qq 2>&1 | tail -3

echo "=== Docker CE + Compose 설치 ==="
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin 2>&1 | tail -5

echo "=== 사용자 그룹 추가 ==="
usermod -aG docker idino
echo "GROUP_OK"

echo "=== Docker 서비스 시작 ==="
systemctl enable docker
systemctl start docker

echo "=== 버전 확인 ==="
docker --version
docker compose version

echo "=== 완료 ==="
