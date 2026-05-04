# DocUtil 마이그레이션 계획서
# Windows Docker Compose → Ubuntu Docker Compose → Kubernetes

---

## 목차

1. [개요 및 현황 분석](#1-개요-및-현황-분석)
2. [Phase 1: Ubuntu 서버 Docker Compose 이전](#2-phase-1-ubuntu-서버-docker-compose-이전)
3. [Phase 2: Kubernetes 전환](#3-phase-2-kubernetes-전환)
4. [Phase 3: 운영 안정화](#4-phase-3-운영-안정화)
5. [리스크 관리 및 롤백 전략](#5-리스크-관리-및-롤백-전략)
6. [일정 계획](#6-일정-계획)

---

## 1. 개요 및 현황 분석

### 1.1 현재 아키텍처

```
[Windows 11 Pro + Docker Desktop]
    |
    +-- docutil-network (bridge, 172.28.0.0/16)
        |
        +-- Stateless Services
        |   +-- frontend (Next.js 16, :3002)
        |   +-- api (FastAPI, :8000)
        |   +-- celery-worker (x2 replicas, concurrency=4)
        |   +-- celery-beat (스케줄러)
        |   +-- flower (Celery 모니터, :5555)
        |   +-- nginx (리버스 프록시, :80/443)
        |
        +-- Stateful Services
        |   +-- postgres (17-alpine, :5432, 256MB shared_buffers)
        |   +-- qdrant (v1.16, :6333/6334, dense+sparse vectors)
        |   +-- redis (7-alpine, :6379, 512MB maxmemory, AOF+RDB)
        |   +-- rabbitmq (4.0-management, :5672/15672)
        |   +-- minio (latest, :9000/9001)
        |
        +-- Monitoring
            +-- prometheus (v2.55, :9090, 15d retention)
            +-- grafana (11.4, :3001)
            +-- loki (3.3, :3100)
```

### 1.2 데이터 볼륨 목록

| 볼륨명 | 서비스 | 지속성 | 마이그레이션 필수 |
|--------|--------|--------|-------------------|
| docutil-postgres-data | PostgreSQL | 필수 | O (pg_dump) |
| docutil-qdrant-data | Qdrant | 필수 | O (snapshot API) |
| docutil-qdrant-snapshots | Qdrant | 필수 | O (파일 복사) |
| docutil-minio-data | MinIO | 필수 | O (mc mirror) |
| docutil-redis-data | Redis | 선택 | X (캐시, 재생성 가능) |
| docutil-rabbitmq-data | RabbitMQ | 선택 | X (큐 비우고 이전) |
| docutil-flower-data | Flower | 선택 | X (모니터링 히스토리) |
| docutil-prometheus-data | Prometheus | 선택 | X (메트릭 히스토리) |
| docutil-grafana-data | Grafana | 선택 | △ (대시보드 설정만) |
| docutil-loki-data | Loki | 선택 | X (로그 히스토리) |
| docutil-api-tmp | API | 임시 | X |
| docutil-nginx-logs | Nginx | 선택 | X |

### 1.3 외부 의존성

- OpenAI API (GPT-4o, text-embedding-3-small): API Key만 이전
- Unsplash API: API Key만 이전
- DNS/도메인: 새 서버 IP로 A 레코드 변경 필요

---

## 2. Phase 1: Ubuntu 서버 Docker Compose 이전

**목표**: Windows 개발환경에서 Ubuntu 서버로 동일한 Docker Compose 스택을 무손실 이전
**예상 소요**: 2~3일 (사전 준비 포함 1주)
**다운타임**: 30분~1시간 (DNS 전환 + 데이터 최종 동기화)

### 2.1 서버 하드웨어 권장 스펙

#### 최소 사양 (개발/스테이징)
| 항목 | 스펙 | 근거 |
|------|------|------|
| CPU | 4코어 (8스레드) | Celery worker concurrency=4, API workers=4 |
| RAM | 16GB | PG 256MB + Redis 512MB + Qdrant ~2GB + Workers 4GB + 시스템 여유 |
| 디스크 | 100GB SSD (NVMe 권장) | PG + Qdrant + MinIO + Docker 이미지 |
| 네트워크 | 1Gbps | 문서 업로드/다운로드, OpenAI API 호출 |

#### 권장 사양 (운영)
| 항목 | 스펙 | 근거 |
|------|------|------|
| CPU | 8코어 (16스레드) | 동시 문서 처리 + 검색 + 챗봇 |
| RAM | 32GB | Qdrant 인덱스 증가 대비, Celery worker 스케일링 |
| 디스크 | 500GB NVMe SSD | 문서 증가 대비 (MinIO), Qdrant 벡터 확장 |
| 네트워크 | 1Gbps+ | 다수 동시 사용자 |

### 2.2 Ubuntu 서버 초기 설정

#### 2.2.1 OS 설치 및 기본 설정

```bash
# Ubuntu 24.04 LTS 설치 후

# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 필수 패키지
sudo apt install -y \
    curl wget git htop iotop \
    ufw fail2ban \
    unzip jq

# 타임존 설정
sudo timedatectl set-timezone Asia/Seoul

# 호스트명 설정
sudo hostnamectl set-hostname docutil-prod

# swap 설정 (RAM의 50%, 최대 8GB)
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 커널 파라미터 최적화
cat <<'EOF' | sudo tee /etc/sysctl.d/99-docutil.conf
# 네트워크 최적화
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_tw_reuse = 1

# 파일 디스크립터
fs.file-max = 2097152

# 메모리 overcommit (PostgreSQL 권장)
vm.overcommit_memory = 1

# Qdrant/Redis 성능
vm.swappiness = 10
EOF
sudo sysctl --system

# 파일 디스크립터 제한
cat <<'EOF' | sudo tee /etc/security/limits.d/99-docutil.conf
*    soft    nofile    65536
*    hard    nofile    65536
root soft    nofile    65536
root hard    nofile    65536
EOF
```

#### 2.2.2 Docker 설치

```bash
# Docker CE 설치 (공식 저장소)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER

# Docker Compose 플러그인 확인 (Docker CE에 포함)
docker compose version

# Docker 데몬 설정
sudo mkdir -p /etc/docker
cat <<'EOF' | sudo tee /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "live-restore": true,
  "default-address-pools": [
    {"base": "172.28.0.0/16", "size": 24}
  ]
}
EOF

# Docker 재시작
sudo systemctl restart docker
sudo systemctl enable docker

# 로그아웃 후 재로그인 (docker 그룹 적용)
```

#### 2.2.3 방화벽 설정

```bash
# UFW 기본 정책
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH
sudo ufw allow 22/tcp

# HTTP/HTTPS (Nginx)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 필요시 개발/관리용 (IP 제한 권장)
# sudo ufw allow from <관리자IP> to any port 5555  # Flower
# sudo ufw allow from <관리자IP> to any port 3001  # Grafana
# sudo ufw allow from <관리자IP> to any port 9041  # MinIO Console

# UFW 활성화
sudo ufw enable
sudo ufw status verbose
```

#### 2.2.4 Fail2ban 설정

```bash
cat <<'EOF' | sudo tee /etc/fail2ban/jail.local
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 86400
EOF

sudo systemctl restart fail2ban
sudo systemctl enable fail2ban
```

### 2.3 프로젝트 코드 전송

#### 방법 A: Git 기반 (권장)

```bash
# Ubuntu 서버에서
cd /opt
sudo mkdir docutil && sudo chown $USER:$USER docutil
cd docutil

# private 저장소라면 SSH key 또는 deploy key 설정
git clone <repository-url> .
```

#### 방법 B: rsync 직접 전송

```bash
# Windows (Git Bash 또는 WSL)에서
rsync -avz --progress \
    --exclude='node_modules' \
    --exclude='.next' \
    --exclude='__pycache__' \
    --exclude='.env' \
    --exclude='*.pyc' \
    --exclude='.git' \
    /d/workspace/document_utilization/ \
    user@server:/opt/docutil/
```

### 2.4 환경변수 및 시크릿 관리

```bash
# Ubuntu 서버에서
cd /opt/docutil

# .env 파일 생성 (절대 Git에 커밋하지 않음)
cp .env.example .env

# 시크릿 값 생성
JWT_SECRET=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
FIELD_KEY=$(openssl rand -hex 32)

echo "JWT_SECRET_KEY=$JWT_SECRET"
echo "ENCRYPTION_KEY=$ENCRYPTION_KEY"
echo "FIELD_ENCRYPTION_KEY=$FIELD_KEY"

# .env 편집 (운영 환경 값으로 수정)
nano .env
```

**운영 환경에서 변경해야 할 주요 값**:

```bash
# .env 수정 사항

# 일반
APP_ENV=production
DEBUG=false
ALLOWED_HOSTS=docutil.yourdomain.com,your-server-ip

# 포트 (호스트 포트, Nginx 뒤에서는 외부 노출 불필요)
POSTGRES_PORT=5440          # 외부 접근 차단 시 제거 가능
REDIS_PORT=6340
RABBITMQ_PORT=5640
RABBITMQ_MGMT_PORT=15640
QDRANT_PORT=6341
MINIO_API_PORT=9040
MINIO_CONSOLE_PORT=9041
FLOWER_PORT=5540
FRONTEND_PORT=3040
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443

# 패스워드 (반드시 강력한 값으로 변경)
POSTGRES_PASSWORD=<strong-random-password>
REDIS_PASSWORD=<strong-random-password>
RABBITMQ_PASSWORD=<strong-random-password>
MINIO_ROOT_PASSWORD=<strong-random-password>
JWT_SECRET_KEY=<openssl-rand-hex-32>
ENCRYPTION_KEY=<fernet-key>
FLOWER_PASSWORD=<strong-random-password>
GRAFANA_ADMIN_PASSWORD=<strong-random-password>

# OpenAI (기존 키 유지)
OPENAI_API_KEY=sk-...

# MinIO 브라우저 URL
MINIO_BROWSER_REDIRECT_URL=https://docutil.yourdomain.com:9041

# Grafana URL
GRAFANA_ROOT_URL=https://docutil.yourdomain.com:3041

# CORS
API_CORS_ORIGINS=https://docutil.yourdomain.com
```

**.env 파일 권한 보호**:

```bash
chmod 600 .env
```

### 2.5 데이터 마이그레이션

#### 2.5.1 마이그레이션 순서

```
1. Windows에서 서비스 중지 (쓰기 차단)
2. PostgreSQL pg_dump → 파일 전송 → pg_restore
3. Qdrant snapshot → 파일 전송 → snapshot restore
4. MinIO mc mirror → 파일 전송
5. Ubuntu에서 서비스 기동 + Alembic migrate
6. 검증
7. DNS 전환
```

#### 2.5.2 PostgreSQL 마이그레이션

```bash
# === Windows 측 (소스) ===

# 1. 현재 데이터 확인
docker exec docutil-postgres psql -U docutil -d docutil -c "\dt"
docker exec docutil-postgres psql -U docutil -d docutil -c "SELECT count(*) FROM users;"

# 2. 전체 덤프 생성 (custom format, 압축 포함)
docker exec docutil-postgres pg_dump \
    -U docutil -d docutil \
    --format=custom \
    --compress=9 \
    --verbose \
    --file=/tmp/docutil_dump.backup

# 3. 컨테이너에서 호스트로 복사
docker cp docutil-postgres:/tmp/docutil_dump.backup ./backups/docutil_dump.backup

# 4. Ubuntu 서버로 전송
scp ./backups/docutil_dump.backup user@server:/opt/docutil/backups/

# === Ubuntu 측 (대상) ===

# 5. PostgreSQL만 먼저 기동
cd /opt/docutil
docker compose up -d postgres
# healthy 상태까지 대기
docker compose exec postgres pg_isready -U docutil

# 6. 백업 파일을 컨테이너로 복사
docker cp ./backups/docutil_dump.backup docutil-postgres:/tmp/

# 7. 복원
docker exec docutil-postgres pg_restore \
    -U docutil -d docutil \
    --verbose \
    --clean --if-exists \
    /tmp/docutil_dump.backup

# 8. 검증
docker exec docutil-postgres psql -U docutil -d docutil \
    -c "SELECT schemaname, tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;"
docker exec docutil-postgres psql -U docutil -d docutil \
    -c "SELECT count(*) FROM users;"
```

**주의**: 만약 Windows와 Ubuntu에서 `.env`의 `POSTGRES_PASSWORD`가 다르면, dump 파일에는 비밀번호가 포함되지 않으므로 문제없음. 다만 `JWT_SECRET_KEY`가 다르면 기존 세션이 무효화되므로, 사용자 재로그인이 필요함.

#### 2.5.3 Qdrant 마이그레이션

```bash
# === Windows 측 (소스) ===

# 1. 컬렉션 목록 확인
curl http://localhost:6341/collections

# 2. 스냅샷 생성 (컬렉션 이름 = doc_embeddings 가정)
curl -X POST "http://localhost:6341/collections/doc_embeddings/snapshots"
# 응답에서 snapshot 이름 확인 (예: doc_embeddings-1234567890.snapshot)

# 3. 스냅샷 다운로드
SNAPSHOT_NAME="<위에서 확인한 이름>"
curl -o ./backups/qdrant_snapshot.snapshot \
    "http://localhost:6341/collections/doc_embeddings/snapshots/${SNAPSHOT_NAME}"

# 4. Ubuntu 서버로 전송
scp ./backups/qdrant_snapshot.snapshot user@server:/opt/docutil/backups/

# === Ubuntu 측 (대상) ===

# 5. Qdrant만 먼저 기동
docker compose up -d qdrant
sleep 10

# 6. 스냅샷으로 컬렉션 복원
curl -X PUT "http://localhost:6341/collections/doc_embeddings/snapshots/recover" \
    -H "Content-Type: application/json" \
    -d "{
        \"location\": \"file:///opt/docutil/backups/qdrant_snapshot.snapshot\"
    }"

# 주의: 위 경로는 호스트 경로가 아닌 Qdrant 컨테이너 내부 경로여야 함
# 방법 1: 볼륨 마운트로 snapshot 파일 전달
docker cp ./backups/qdrant_snapshot.snapshot docutil-qdrant:/qdrant/snapshots/
curl -X PUT "http://localhost:6341/collections/doc_embeddings/snapshots/recover" \
    -H "Content-Type: application/json" \
    -d '{"location": "file:///qdrant/snapshots/qdrant_snapshot.snapshot"}'

# 방법 2: HTTP 업로드 (Qdrant 1.7+)
curl -X POST "http://localhost:6341/collections/doc_embeddings/snapshots/upload" \
    -H "Content-Type: multipart/form-data" \
    -F "snapshot=@./backups/qdrant_snapshot.snapshot"

# 7. 검증
curl "http://localhost:6341/collections/doc_embeddings" | jq '.result.points_count'
```

#### 2.5.4 MinIO 마이그레이션

```bash
# === Windows 측 (소스) ===

# 1. mc 클라이언트 설정
docker run --rm -it --network docutil-network \
    --entrypoint /bin/sh minio/mc -c "
    mc alias set source http://minio:9000 docutil <MINIO_PASSWORD>
    mc ls source/
    mc du source/
"

# 2. 방법 A: mc mirror (네트워크 직접 연결 가능 시)
# Ubuntu에서 MinIO 기동 후
mc alias set target http://<ubuntu-server>:9040 docutil <NEW_MINIO_PASSWORD>
mc mirror source/ target/

# 3. 방법 B: 로컬 다운로드 후 전송 (네트워크 분리 시)
# Windows에서 MinIO 데이터 볼륨 직접 복사
docker run --rm \
    -v docutil-minio-data:/data \
    -v $(pwd)/backups/minio:/backup \
    alpine tar czf /backup/minio_data.tar.gz -C /data .

# Ubuntu 서버로 전송
scp ./backups/minio/minio_data.tar.gz user@server:/opt/docutil/backups/

# === Ubuntu 측 (대상) ===

# MinIO 기동 전에 데이터 복원
docker compose up -d minio
sleep 5

# 볼륨에 데이터 복원
docker run --rm \
    -v docutil-minio-data:/data \
    -v /opt/docutil/backups:/backup \
    alpine sh -c "cd /data && tar xzf /backup/minio_data.tar.gz"

# MinIO 재시작
docker compose restart minio

# 검증
docker exec docutil-minio mc ls local/documents/
```

#### 2.5.5 Grafana 대시보드 백업 (선택)

```bash
# Windows에서 Grafana 대시보드 내보내기
# API로 모든 대시보드 JSON 추출
GRAFANA_URL="http://localhost:3041"
GRAFANA_AUTH="admin:changeme"

mkdir -p ./backups/grafana

# 대시보드 목록
curl -s -u "$GRAFANA_AUTH" "$GRAFANA_URL/api/search?type=dash-db" | \
    jq -r '.[].uid' | while read uid; do
    curl -s -u "$GRAFANA_AUTH" "$GRAFANA_URL/api/dashboards/uid/$uid" > \
        "./backups/grafana/dashboard_${uid}.json"
done

# Ubuntu에서 복원
scp -r ./backups/grafana/ user@server:/opt/docutil/backups/
# Grafana 기동 후 API로 import 또는 provisioning 디렉토리에 배치
```

### 2.6 SSL/TLS 인증서 설정 (Let's Encrypt)

#### 2.6.1 Certbot으로 인증서 발급

```bash
# Ubuntu 서버에서
sudo apt install -y certbot

# DNS A 레코드가 서버 IP를 가리키고 있어야 함
# standalone 모드 (Nginx 중지 상태에서)
sudo certbot certonly --standalone \
    -d docutil.yourdomain.com \
    --email admin@yourdomain.com \
    --agree-tos \
    --no-eff-email

# 인증서 위치
# /etc/letsencrypt/live/docutil.yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/docutil.yourdomain.com/privkey.pem

# Docker에서 접근할 수 있도록 복사
sudo mkdir -p /opt/docutil/nginx/certs
sudo cp /etc/letsencrypt/live/docutil.yourdomain.com/fullchain.pem /opt/docutil/nginx/certs/
sudo cp /etc/letsencrypt/live/docutil.yourdomain.com/privkey.pem /opt/docutil/nginx/certs/
sudo chmod 644 /opt/docutil/nginx/certs/fullchain.pem
sudo chmod 600 /opt/docutil/nginx/certs/privkey.pem
```

#### 2.6.2 Nginx SSL 설정

기존 `nginx/nginx.conf`를 수정하여 SSL 지원 추가.

```nginx
# nginx/nginx.conf (Ubuntu 운영 환경용)
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 2048;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] '
                    '"$request" $status $body_bytes_sent '
                    '"$http_referer" "$http_user_agent" '
                    'rt=$request_time';
    access_log /var/log/nginx/access.log main;

    sendfile        on;
    tcp_nopush      on;
    keepalive_timeout 65;
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

    upstream frontend {
        server frontend:3002;
    }

    upstream api {
        server api:8000;
    }

    # HTTP → HTTPS 리다이렉트
    server {
        listen 80;
        server_name docutil.yourdomain.com;

        # Let's Encrypt ACME challenge
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        location / {
            return 301 https://$host$request_uri;
        }
    }

    # HTTPS 서버
    server {
        listen 443 ssl http2;
        server_name docutil.yourdomain.com;

        ssl_certificate     /etc/nginx/certs/fullchain.pem;
        ssl_certificate_key /etc/nginx/certs/privkey.pem;

        # SSL 보안 설정
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        ssl_session_timeout 1d;
        ssl_session_cache shared:SSL:10m;
        ssl_session_tickets off;

        # HSTS
        add_header Strict-Transport-Security "max-age=63072000" always;

        # 보안 헤더
        add_header X-Frame-Options DENY always;
        add_header X-Content-Type-Options nosniff always;
        add_header X-XSS-Protection "1; mode=block" always;

        client_max_body_size 500M;

        # WebSocket for chat
        location /api/v1/chat/ws/ {
            proxy_pass http://api;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 3600s;
            proxy_send_timeout 3600s;
        }

        # API with rate limiting
        location /api/v1/auth/login {
            limit_req zone=login burst=3 nodelay;
            proxy_pass http://api;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /api/ {
            limit_req zone=api burst=50 nodelay;
            proxy_pass http://api;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 300s;
            proxy_connect_timeout 75s;
        }

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check (internal only)
        location /health {
            proxy_pass http://api/health;
            allow 172.16.0.0/12;
            allow 127.0.0.1;
            deny all;
        }

        # Metrics (internal only)
        location /metrics {
            proxy_pass http://api/metrics;
            allow 172.16.0.0/12;
            allow 127.0.0.1;
            deny all;
        }
    }

    include /etc/nginx/conf.d/*.conf;
}
```

#### 2.6.3 인증서 자동 갱신

```bash
# crontab에 갱신 스크립트 등록
cat <<'SCRIPT' | sudo tee /opt/docutil/scripts/renew-cert.sh
#!/bin/bash
certbot renew --quiet
cp /etc/letsencrypt/live/docutil.yourdomain.com/fullchain.pem /opt/docutil/nginx/certs/
cp /etc/letsencrypt/live/docutil.yourdomain.com/privkey.pem /opt/docutil/nginx/certs/
docker exec docutil-nginx nginx -s reload
SCRIPT

sudo chmod +x /opt/docutil/scripts/renew-cert.sh

# 매일 새벽 3시에 갱신 시도
(crontab -l 2>/dev/null; echo "0 3 * * * /opt/docutil/scripts/renew-cert.sh >> /var/log/certbot-renew.log 2>&1") | crontab -
```

### 2.7 Docker Compose 운영 환경 오버라이드

Ubuntu 서버에서는 `docker-compose.override.yml`로 포트 매핑을 조정합니다. Stateful 서비스의 호스트 포트 노출을 제한하고, 모니터링 도구도 내부 네트워크에서만 접근 가능하게 합니다.

```yaml
# docker-compose.override.yml (Ubuntu 운영 서버용)
# 기존 docker-compose.yml 위에 오버라이드

services:
  # PostgreSQL - 외부 접근 차단 (내부 네트워크만)
  postgres:
    ports: !override
      - "127.0.0.1:5440:5432"

  # Redis - 외부 접근 차단
  redis:
    ports: !override
      - "127.0.0.1:6340:6379"

  # RabbitMQ - 관리 UI만 localhost
  rabbitmq:
    ports: !override
      - "127.0.0.1:5640:5672"
      - "127.0.0.1:15640:15672"

  # Qdrant - 외부 접근 차단
  qdrant:
    ports: !override
      - "127.0.0.1:6341:6333"
      - "127.0.0.1:6342:6334"

  # MinIO - API 내부만, Console은 localhost
  minio:
    ports: !override
      - "127.0.0.1:9040:9000"
      - "127.0.0.1:9041:9001"

  # API - Nginx 뒤에서만 접근 (호스트 포트 미노출)
  api:
    ports: !override []

  # Frontend - Nginx 뒤에서만 접근
  frontend:
    ports: !override []

  # Flower - localhost만
  flower:
    ports: !override
      - "127.0.0.1:5540:5555"

  # Monitoring - localhost만
  prometheus:
    ports: !override
      - "127.0.0.1:9042:9090"

  grafana:
    ports: !override
      - "127.0.0.1:3041:3000"

  loki:
    ports: !override
      - "127.0.0.1:3042:3100"

  # Nginx - HTTP/HTTPS만 외부 노출
  nginx:
    ports: !override
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/certs:/etc/nginx/certs:ro
      - nginx-logs:/var/log/nginx
```

**참고**: Docker Compose v2에서 `!override`는 지원되지 않을 수 있음. 대신 `docker-compose.prod.yml`을 별도로 만들어 `-f` 옵션으로 사용하는 것이 더 안전합니다.

```bash
# 운영 서버 기동 명령
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 2.8 서비스 기동 및 검증

```bash
# Ubuntu 서버에서 전체 기동
cd /opt/docutil

# 1. 인프라 서비스 먼저 (Stateful)
docker compose up -d postgres redis rabbitmq qdrant minio
sleep 30  # 모든 서비스 healthy 확인

docker compose ps  # 모든 서비스 healthy 확인

# 2. 데이터 마이그레이션 (2.5절 참조)
# pg_restore, qdrant snapshot, minio mirror 수행

# 3. Alembic 마이그레이션 (스키마 최신화)
docker compose up -d api
docker exec docutil-api alembic upgrade head

# 4. 나머지 서비스 기동
docker compose up -d

# 5. 전체 상태 확인
docker compose ps

# 6. 헬스체크
curl http://localhost:8040/health
curl http://localhost:3040
curl -k https://docutil.yourdomain.com/health

# 7. 기능 검증
# - 로그인: admin / admin123!
# - 문서 목록 확인
# - 검색 테스트
# - 챗봇 테스트
# - 문서 업로드 테스트
```

### 2.9 백업 자동화

```bash
# /opt/docutil/scripts/backup.sh
cat <<'SCRIPT' > /opt/docutil/scripts/backup.sh
#!/bin/bash
set -euo pipefail

BACKUP_DIR="/opt/docutil/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=14

mkdir -p "$BACKUP_DIR"

echo "[$(date)] === 백업 시작 ==="

# 1. PostgreSQL
echo "[$(date)] PostgreSQL 덤프..."
docker exec docutil-postgres pg_dump \
    -U docutil -d docutil \
    --format=custom --compress=9 \
    --file=/tmp/pg_backup.backup
docker cp docutil-postgres:/tmp/pg_backup.backup \
    "$BACKUP_DIR/postgres_${TIMESTAMP}.backup"

# 2. Qdrant 스냅샷
echo "[$(date)] Qdrant 스냅샷..."
SNAP_RESP=$(curl -s -X POST "http://localhost:6341/collections/doc_embeddings/snapshots")
SNAP_NAME=$(echo "$SNAP_RESP" | jq -r '.result.name')
curl -s -o "$BACKUP_DIR/qdrant_${TIMESTAMP}.snapshot" \
    "http://localhost:6341/collections/doc_embeddings/snapshots/${SNAP_NAME}"

# 3. MinIO (증분)
echo "[$(date)] MinIO 동기화..."
docker exec docutil-minio mc alias set local http://localhost:9000 docutil "${MINIO_ROOT_PASSWORD}"
docker run --rm --network docutil-network \
    -v "$BACKUP_DIR/minio:/backup" \
    minio/mc mirror --overwrite \
    http://minio:9000/documents /backup/documents/ 2>/dev/null || true

# 4. 오래된 백업 삭제
echo "[$(date)] ${RETENTION_DAYS}일 이상 된 백업 정리..."
find "$BACKUP_DIR" -name "postgres_*.backup" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "qdrant_*.snapshot" -mtime +$RETENTION_DAYS -delete

echo "[$(date)] === 백업 완료 ==="
du -sh "$BACKUP_DIR"
SCRIPT

chmod +x /opt/docutil/scripts/backup.sh

# 매일 새벽 2시 백업
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/docutil/scripts/backup.sh >> /var/log/docutil-backup.log 2>&1") | crontab -
```

### 2.10 CI/CD 파이프라인 (GitHub Actions → Ubuntu 배포)

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  SERVER_HOST: ${{ secrets.SERVER_HOST }}
  SERVER_USER: ${{ secrets.SERVER_USER }}
  DEPLOY_PATH: /opt/docutil

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
      - run: pip install -r backend/requirements.txt && pip install aiosqlite ruff
      - run: ruff check backend/ && ruff format --check backend/
      - run: cd backend && python -m pytest --tb=short -q
        env:
          JWT_SECRET_KEY: test-secret
          ENCRYPTION_KEY: '0123456789abcdef0123456789abcdef'

  deploy:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/docutil

            # 코드 업데이트
            git fetch origin main
            git reset --hard origin/main

            # 이미지 빌드
            docker compose build --parallel

            # 서비스 업데이트 (zero-downtime: 의존성 없는 서비스부터)
            docker compose up -d --no-deps api
            docker compose up -d --no-deps celery-worker
            docker compose up -d --no-deps celery-beat

            # Frontend는 --no-cache (NEXT_PUBLIC_* 빌드타임 변수)
            docker compose build --no-cache frontend
            docker compose up -d --no-deps frontend

            # Nginx 리로드
            docker exec docutil-nginx nginx -s reload

            # 헬스체크
            sleep 10
            curl -f http://localhost:8040/health || exit 1

            # 미사용 이미지 정리
            docker image prune -f

      - name: Notify on failure
        if: failure()
        run: echo "Deployment failed - manual intervention required"
```

**GitHub Secrets 설정**:
- `SERVER_HOST`: Ubuntu 서버 IP
- `SERVER_USER`: SSH 사용자명
- `SSH_PRIVATE_KEY`: SSH 프라이빗 키

### 2.11 이전 실행 체크리스트

```
Phase 1 체크리스트:

사전 준비:
[ ] Ubuntu 서버 프로비저닝 (하드웨어 확인)
[ ] Ubuntu 24.04 LTS 설치
[ ] Docker CE + Compose 설치
[ ] 방화벽 (UFW) 설정
[ ] Fail2ban 설정
[ ] DNS A 레코드 설정 (또는 사전 테스트용 hosts 파일)
[ ] SSL 인증서 발급 (Let's Encrypt)
[ ] 코드 전송 (git clone)
[ ] .env 파일 생성 및 시크릿 설정

데이터 이전:
[ ] PostgreSQL pg_dump → scp → pg_restore
[ ] Qdrant snapshot → scp → recover
[ ] MinIO data tar → scp → extract
[ ] Grafana 대시보드 export (선택)

서비스 기동:
[ ] Stateful 서비스 기동 (PG, Redis, RabbitMQ, Qdrant, MinIO)
[ ] 데이터 복원 완료 확인
[ ] Alembic upgrade head
[ ] Stateless 서비스 기동 (API, Frontend, Workers, Nginx)
[ ] 전체 healthcheck 통과

검증:
[ ] 로그인 (admin / admin123!)
[ ] 문서 목록 조회
[ ] 문서 업로드
[ ] 하이브리드 검색
[ ] 챗봇 대화 (WebSocket)
[ ] 보고서 생성
[ ] Grafana 대시보드 접근

전환:
[ ] DNS 전환 (A 레코드 → 새 서버 IP)
[ ] Windows 서버 서비스 중지
[ ] 모니터링 알림 확인
[ ] 백업 cron 활성화
```

---

## 3. Phase 2: Kubernetes 전환

**목표**: Docker Compose에서 Kubernetes로 전환하여 자동 스케일링, 자가 복구, 무중단 배포를 확보
**예상 소요**: 2~3주
**전제 조건**: Phase 1 Ubuntu Docker Compose 환경이 안정적으로 운영 중

### 3.1 K8s 클러스터 선택

#### 비교표

| 항목 | k3s | kubeadm | Managed (EKS/GKE/AKS) |
|------|-----|---------|------------------------|
| 복잡도 | 낮음 | 중간 | 낮음 |
| 리소스 사용 | 적음 (512MB~) | 보통 (2GB~) | 보통 |
| 단일 노드 | 최적 | 가능 | 과잉 |
| 멀티 노드 확장 | 용이 | 용이 | 매우 용이 |
| HA | 내장 지원 | 수동 구성 | 자동 |
| 운영 비용 | 서버 비용만 | 서버 비용만 | 서버 + 관리비 |
| 적합 환경 | 중소규모 | 중대규모 | 대규모/엔터프라이즈 |

**권장**: **k3s** (단일 서버 또는 소규모 멀티 노드)

- DocUtil은 14개 컨테이너로 단일 서버에서 충분히 운영 가능
- k3s는 경량 K8s로 etcd 대신 sqlite/postgres 사용, 빠른 설치
- 필요시 agent 노드 추가로 멀티 노드 확장 가능
- 향후 managed K8s로 이전 시에도 YAML 호환

### 3.2 k3s 클러스터 설치

```bash
# === 서버 (Control Plane) 노드 ===

# k3s 설치 (Traefik 비활성화 → 별도 Nginx Ingress 사용)
curl -sfL https://get.k3s.io | sh -s - \
    --write-kubeconfig-mode 644 \
    --disable traefik \
    --disable servicelb \
    --kube-apiserver-arg service-node-port-range=1-65535

# kubeconfig 설정
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER:$USER ~/.kube/config

# 확인
kubectl get nodes
kubectl get pods -A

# Helm 설치
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# (선택) 추가 Agent 노드
# 다른 서버에서:
# K3S_TOKEN=$(sudo cat /var/lib/rancher/k3s/server/node-token)
# curl -sfL https://get.k3s.io | K3S_URL=https://<server-ip>:6443 K3S_TOKEN=$K3S_TOKEN sh -
```

### 3.3 디렉토리 구조 (Kustomize)

```
k8s/
├── base/
│   ├── kustomization.yaml
│   ├── namespace.yaml
│   │
│   ├── configmaps/
│   │   ├── app-config.yaml
│   │   ├── nginx-config.yaml
│   │   └── prometheus-config.yaml
│   │
│   ├── secrets/
│   │   └── app-secrets.yaml          # sealed-secrets 또는 외부 참조
│   │
│   ├── stateless/
│   │   ├── api-deployment.yaml
│   │   ├── api-service.yaml
│   │   ├── frontend-deployment.yaml
│   │   ├── frontend-service.yaml
│   │   ├── celery-worker-deployment.yaml
│   │   ├── celery-beat-deployment.yaml
│   │   └── flower-deployment.yaml
│   │
│   ├── stateful/
│   │   ├── postgres-statefulset.yaml
│   │   ├── postgres-service.yaml
│   │   ├── qdrant-statefulset.yaml
│   │   ├── qdrant-service.yaml
│   │   ├── redis-statefulset.yaml
│   │   ├── redis-service.yaml
│   │   ├── rabbitmq-statefulset.yaml
│   │   ├── rabbitmq-service.yaml
│   │   ├── minio-statefulset.yaml
│   │   └── minio-service.yaml
│   │
│   ├── monitoring/
│   │   ├── prometheus-statefulset.yaml
│   │   ├── grafana-deployment.yaml
│   │   └── loki-statefulset.yaml
│   │
│   ├── ingress/
│   │   └── ingress.yaml
│   │
│   └── hpa/
│       ├── api-hpa.yaml
│       └── celery-worker-hpa.yaml
│
└── overlays/
    ├── dev/
    │   ├── kustomization.yaml
    │   └── patches/
    └── prod/
        ├── kustomization.yaml
        └── patches/
            ├── resource-limits.yaml
            └── replicas.yaml
```

### 3.4 핵심 K8s 매니페스트

#### 3.4.1 Namespace

```yaml
# k8s/base/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: docutil
  labels:
    app.kubernetes.io/part-of: docutil
```

#### 3.4.2 ConfigMap

```yaml
# k8s/base/configmaps/app-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: docutil-config
  namespace: docutil
data:
  APP_NAME: "document-utilization"
  APP_ENV: "production"
  DEBUG: "false"
  LOG_LEVEL: "info"
  TIMEZONE: "UTC"

  # 내부 서비스 주소 (K8s Service DNS)
  DATABASE_URL: "postgresql+asyncpg://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@postgres.docutil.svc:5432/$(POSTGRES_DB)"
  DATABASE_URL_SYNC: "postgresql://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@postgres.docutil.svc:5432/$(POSTGRES_DB)"
  REDIS_URL: "redis://:$(REDIS_PASSWORD)@redis.docutil.svc:6379/0"
  RABBITMQ_URL: "amqp://$(RABBITMQ_USER):$(RABBITMQ_PASSWORD)@rabbitmq.docutil.svc:5672/"
  CELERY_BROKER_URL: "amqp://$(RABBITMQ_USER):$(RABBITMQ_PASSWORD)@rabbitmq.docutil.svc:5672/"
  CELERY_RESULT_BACKEND: "redis://:$(REDIS_PASSWORD)@redis.docutil.svc:6379/1"
  MINIO_ENDPOINT: "minio.docutil.svc:9000"
  MINIO_SECURE: "false"
  QDRANT_HOST: "qdrant.docutil.svc"
  QDRANT_PORT: "6333"
  QDRANT_COLLECTION_NAME: "doc_embeddings"

  # LLM
  LLM_PROVIDER: "openai"
  OPENAI_MODEL: "gpt-4o"
```

#### 3.4.3 Secret

```yaml
# k8s/base/secrets/app-secrets.yaml
# 주의: 실제 운영에서는 Sealed Secrets 또는 External Secrets Operator 사용 권장
apiVersion: v1
kind: Secret
metadata:
  name: docutil-secrets
  namespace: docutil
type: Opaque
stringData:
  POSTGRES_USER: "docutil"
  POSTGRES_PASSWORD: "<CHANGE_ME>"
  POSTGRES_DB: "docutil"
  REDIS_PASSWORD: "<CHANGE_ME>"
  RABBITMQ_USER: "docutil"
  RABBITMQ_PASSWORD: "<CHANGE_ME>"
  MINIO_ROOT_USER: "docutil"
  MINIO_ROOT_PASSWORD: "<CHANGE_ME>"
  JWT_SECRET_KEY: "<CHANGE_ME>"
  ENCRYPTION_KEY: "<CHANGE_ME>"
  FIELD_ENCRYPTION_KEY: "<CHANGE_ME>"
  OPENAI_API_KEY: "<CHANGE_ME>"
  QDRANT_API_KEY: ""
  FLOWER_USER: "admin"
  FLOWER_PASSWORD: "<CHANGE_ME>"
  GRAFANA_ADMIN_USER: "admin"
  GRAFANA_ADMIN_PASSWORD: "<CHANGE_ME>"
```

#### 3.4.4 PostgreSQL StatefulSet

```yaml
# k8s/base/stateful/postgres-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: docutil
  labels:
    app: postgres
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:17-alpine
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: docutil-secrets
                  key: POSTGRES_USER
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: docutil-secrets
                  key: POSTGRES_PASSWORD
            - name: POSTGRES_DB
              valueFrom:
                secretKeyRef:
                  name: docutil-secrets
                  key: POSTGRES_DB
            - name: PGDATA
              value: /var/lib/postgresql/data/pgdata
          args:
            - postgres
            - -c
            - shared_buffers=256MB
            - -c
            - effective_cache_size=512MB
            - -c
            - maintenance_work_mem=128MB
            - -c
            - max_connections=200
            - -c
            - work_mem=4MB
            - -c
            - wal_buffers=16MB
          resources:
            requests:
              cpu: 500m
              memory: 512Mi
            limits:
              cpu: "2"
              memory: 1Gi
          readinessProbe:
            exec:
              command:
                - pg_isready
                - -U
                - docutil
            initialDelaySeconds: 15
            periodSeconds: 10
          livenessProbe:
            exec:
              command:
                - pg_isready
                - -U
                - docutil
            initialDelaySeconds: 30
            periodSeconds: 15
          volumeMounts:
            - name: postgres-data
              mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
    - metadata:
        name: postgres-data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: local-path  # k3s 기본 StorageClass
        resources:
          requests:
            storage: 20Gi
---
# k8s/base/stateful/postgres-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: docutil
spec:
  selector:
    app: postgres
  ports:
    - port: 5432
      targetPort: 5432
  clusterIP: None  # Headless (StatefulSet)
```

#### 3.4.5 Qdrant StatefulSet

```yaml
# k8s/base/stateful/qdrant-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: qdrant
  namespace: docutil
  labels:
    app: qdrant
spec:
  serviceName: qdrant
  replicas: 1
  selector:
    matchLabels:
      app: qdrant
  template:
    metadata:
      labels:
        app: qdrant
    spec:
      containers:
        - name: qdrant
          image: qdrant/qdrant:v1.16.0
          ports:
            - containerPort: 6333
              name: http
            - containerPort: 6334
              name: grpc
          env:
            - name: QDRANT__SERVICE__API_KEY
              valueFrom:
                secretKeyRef:
                  name: docutil-secrets
                  key: QDRANT_API_KEY
            - name: QDRANT__STORAGE__STORAGE_PATH
              value: /qdrant/storage
            - name: QDRANT__STORAGE__SNAPSHOTS_PATH
              value: /qdrant/snapshots
            - name: QDRANT__LOG_LEVEL
              value: INFO
          resources:
            requests:
              cpu: 500m
              memory: 1Gi
            limits:
              cpu: "2"
              memory: 4Gi
          readinessProbe:
            httpGet:
              path: /readyz
              port: 6333
            initialDelaySeconds: 10
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /healthz
              port: 6333
            initialDelaySeconds: 15
            periodSeconds: 15
          volumeMounts:
            - name: qdrant-data
              mountPath: /qdrant/storage
            - name: qdrant-snapshots
              mountPath: /qdrant/snapshots
  volumeClaimTemplates:
    - metadata:
        name: qdrant-data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: local-path
        resources:
          requests:
            storage: 20Gi
    - metadata:
        name: qdrant-snapshots
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: local-path
        resources:
          requests:
            storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: qdrant
  namespace: docutil
spec:
  selector:
    app: qdrant
  ports:
    - port: 6333
      targetPort: 6333
      name: http
    - port: 6334
      targetPort: 6334
      name: grpc
  clusterIP: None
```

#### 3.4.6 Redis StatefulSet

```yaml
# k8s/base/stateful/redis-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
  namespace: docutil
  labels:
    app: redis
spec:
  serviceName: redis
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          ports:
            - containerPort: 6379
          command:
            - redis-server
            - --requirepass
            - $(REDIS_PASSWORD)
            - --maxmemory
            - 512mb
            - --maxmemory-policy
            - allkeys-lru
            - --appendonly
            - "yes"
            - --appendfsync
            - everysec
          env:
            - name: REDIS_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: docutil-secrets
                  key: REDIS_PASSWORD
          resources:
            requests:
              cpu: 100m
              memory: 256Mi
            limits:
              cpu: 500m
              memory: 768Mi
          readinessProbe:
            exec:
              command: ["redis-cli", "ping"]
            initialDelaySeconds: 5
            periodSeconds: 10
          volumeMounts:
            - name: redis-data
              mountPath: /data
  volumeClaimTemplates:
    - metadata:
        name: redis-data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: local-path
        resources:
          requests:
            storage: 5Gi
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: docutil
spec:
  selector:
    app: redis
  ports:
    - port: 6379
      targetPort: 6379
  clusterIP: None
```

#### 3.4.7 RabbitMQ StatefulSet

```yaml
# k8s/base/stateful/rabbitmq-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: rabbitmq
  namespace: docutil
  labels:
    app: rabbitmq
spec:
  serviceName: rabbitmq
  replicas: 1
  selector:
    matchLabels:
      app: rabbitmq
  template:
    metadata:
      labels:
        app: rabbitmq
    spec:
      containers:
        - name: rabbitmq
          image: rabbitmq:4.0-management-alpine
          ports:
            - containerPort: 5672
              name: amqp
            - containerPort: 15672
              name: management
          env:
            - name: RABBITMQ_DEFAULT_USER
              valueFrom:
                secretKeyRef:
                  name: docutil-secrets
                  key: RABBITMQ_USER
            - name: RABBITMQ_DEFAULT_PASS
              valueFrom:
                secretKeyRef:
                  name: docutil-secrets
                  key: RABBITMQ_PASSWORD
          resources:
            requests:
              cpu: 200m
              memory: 256Mi
            limits:
              cpu: "1"
              memory: 512Mi
          readinessProbe:
            exec:
              command: ["rabbitmq-diagnostics", "-q", "check_running"]
            initialDelaySeconds: 30
            periodSeconds: 15
          volumeMounts:
            - name: rabbitmq-data
              mountPath: /var/lib/rabbitmq
  volumeClaimTemplates:
    - metadata:
        name: rabbitmq-data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: local-path
        resources:
          requests:
            storage: 5Gi
---
apiVersion: v1
kind: Service
metadata:
  name: rabbitmq
  namespace: docutil
spec:
  selector:
    app: rabbitmq
  ports:
    - port: 5672
      targetPort: 5672
      name: amqp
    - port: 15672
      targetPort: 15672
      name: management
  clusterIP: None
```

#### 3.4.8 MinIO StatefulSet

```yaml
# k8s/base/stateful/minio-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: minio
  namespace: docutil
  labels:
    app: minio
spec:
  serviceName: minio
  replicas: 1
  selector:
    matchLabels:
      app: minio
  template:
    metadata:
      labels:
        app: minio
    spec:
      containers:
        - name: minio
          image: minio/minio:latest
          ports:
            - containerPort: 9000
              name: api
            - containerPort: 9001
              name: console
          command:
            - minio
            - server
            - /data
            - --console-address
            - ":9001"
          env:
            - name: MINIO_ROOT_USER
              valueFrom:
                secretKeyRef:
                  name: docutil-secrets
                  key: MINIO_ROOT_USER
            - name: MINIO_ROOT_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: docutil-secrets
                  key: MINIO_ROOT_PASSWORD
          resources:
            requests:
              cpu: 200m
              memory: 256Mi
            limits:
              cpu: "1"
              memory: 1Gi
          readinessProbe:
            httpGet:
              path: /minio/health/ready
              port: 9000
            initialDelaySeconds: 15
            periodSeconds: 10
          volumeMounts:
            - name: minio-data
              mountPath: /data
  volumeClaimTemplates:
    - metadata:
        name: minio-data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: local-path
        resources:
          requests:
            storage: 50Gi
---
apiVersion: v1
kind: Service
metadata:
  name: minio
  namespace: docutil
spec:
  selector:
    app: minio
  ports:
    - port: 9000
      targetPort: 9000
      name: api
    - port: 9001
      targetPort: 9001
      name: console
  clusterIP: None
```

#### 3.4.9 API Deployment

```yaml
# k8s/base/stateless/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: docutil
  labels:
    app: api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  template:
    metadata:
      labels:
        app: api
    spec:
      initContainers:
        - name: wait-for-postgres
          image: busybox:1.36
          command: ['sh', '-c', 'until nc -z postgres.docutil.svc 5432; do sleep 2; done']
        - name: run-migrations
          image: docutil-backend:latest
          command: ['alembic', 'upgrade', 'head']
          envFrom:
            - configMapRef:
                name: docutil-config
            - secretRef:
                name: docutil-secrets
      containers:
        - name: api
          image: docutil-backend:latest
          imagePullPolicy: Always
          ports:
            - containerPort: 8000
          envFrom:
            - configMapRef:
                name: docutil-config
            - secretRef:
                name: docutil-secrets
          env:
            - name: DATABASE_URL
              value: "postgresql+asyncpg://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@postgres.docutil.svc:5432/$(POSTGRES_DB)"
            - name: DATABASE_URL_SYNC
              value: "postgresql://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@postgres.docutil.svc:5432/$(POSTGRES_DB)"
            - name: REDIS_URL
              value: "redis://:$(REDIS_PASSWORD)@redis.docutil.svc:6379/0"
            - name: CELERY_BROKER_URL
              value: "amqp://$(RABBITMQ_USER):$(RABBITMQ_PASSWORD)@rabbitmq.docutil.svc:5672/"
            - name: CELERY_RESULT_BACKEND
              value: "redis://:$(REDIS_PASSWORD)@redis.docutil.svc:6379/1"
            - name: MINIO_ENDPOINT
              value: "minio.docutil.svc:9000"
            - name: MINIO_ACCESS_KEY
              valueFrom:
                secretKeyRef:
                  name: docutil-secrets
                  key: MINIO_ROOT_USER
            - name: MINIO_SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: docutil-secrets
                  key: MINIO_ROOT_PASSWORD
            - name: MINIO_SECURE
              value: "false"
            - name: QDRANT_HOST
              value: "qdrant.docutil.svc"
            - name: QDRANT_PORT
              value: "6333"
          resources:
            requests:
              cpu: 250m
              memory: 512Mi
            limits:
              cpu: "2"
              memory: 1Gi
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 15
          volumeMounts:
            - name: tmp
              mountPath: /tmp/docutil
      volumes:
        - name: tmp
          emptyDir: {}
---
# k8s/base/stateless/api-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: api
  namespace: docutil
spec:
  selector:
    app: api
  ports:
    - port: 8000
      targetPort: 8000
```

#### 3.4.10 Frontend Deployment

```yaml
# k8s/base/stateless/frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: docutil
  labels:
    app: frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
        - name: frontend
          image: docutil-frontend:latest
          imagePullPolicy: Always
          ports:
            - containerPort: 3002
          env:
            - name: NODE_ENV
              value: production
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 256Mi
          readinessProbe:
            httpGet:
              path: /
              port: 3002
            initialDelaySeconds: 10
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: docutil
spec:
  selector:
    app: frontend
  ports:
    - port: 3002
      targetPort: 3002
```

#### 3.4.11 Celery Worker Deployment

```yaml
# k8s/base/stateless/celery-worker-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker
  namespace: docutil
  labels:
    app: celery-worker
spec:
  replicas: 2
  selector:
    matchLabels:
      app: celery-worker
  template:
    metadata:
      labels:
        app: celery-worker
    spec:
      containers:
        - name: celery-worker
          image: docutil-backend:latest
          imagePullPolicy: Always
          command:
            - celery
            - -A
            - app.workers
            - worker
            - --loglevel=info
            - --concurrency=4
            - --max-tasks-per-child=100
            - -Q
            - default,document_processing,embedding,report_generation
            - -n
            - worker@%h
          envFrom:
            - configMapRef:
                name: docutil-config
            - secretRef:
                name: docutil-secrets
          env:
            - name: DATABASE_URL
              value: "postgresql+asyncpg://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@postgres.docutil.svc:5432/$(POSTGRES_DB)"
            - name: DATABASE_URL_SYNC
              value: "postgresql://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@postgres.docutil.svc:5432/$(POSTGRES_DB)"
            - name: REDIS_URL
              value: "redis://:$(REDIS_PASSWORD)@redis.docutil.svc:6379/0"
            - name: CELERY_BROKER_URL
              value: "amqp://$(RABBITMQ_USER):$(RABBITMQ_PASSWORD)@rabbitmq.docutil.svc:5672/"
            - name: CELERY_RESULT_BACKEND
              value: "redis://:$(REDIS_PASSWORD)@redis.docutil.svc:6379/1"
            - name: MINIO_ENDPOINT
              value: "minio.docutil.svc:9000"
            - name: MINIO_ACCESS_KEY
              valueFrom:
                secretKeyRef:
                  name: docutil-secrets
                  key: MINIO_ROOT_USER
            - name: MINIO_SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: docutil-secrets
                  key: MINIO_ROOT_PASSWORD
            - name: QDRANT_HOST
              value: "qdrant.docutil.svc"
            - name: QDRANT_PORT
              value: "6333"
          resources:
            requests:
              cpu: 500m
              memory: 512Mi
            limits:
              cpu: "2"
              memory: 2Gi
          readinessProbe:
            exec:
              command: ["celery", "-A", "app.workers", "inspect", "ping", "--timeout", "10"]
            initialDelaySeconds: 30
            periodSeconds: 60
          volumeMounts:
            - name: tmp
              mountPath: /tmp/docutil
      volumes:
        - name: tmp
          emptyDir: {}
```

#### 3.4.12 Celery Beat Deployment

```yaml
# k8s/base/stateless/celery-beat-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-beat
  namespace: docutil
  labels:
    app: celery-beat
spec:
  replicas: 1  # Beat는 반드시 1개만
  selector:
    matchLabels:
      app: celery-beat
  strategy:
    type: Recreate  # Beat는 동시 실행 방지
  template:
    metadata:
      labels:
        app: celery-beat
    spec:
      containers:
        - name: celery-beat
          image: docutil-backend:latest
          command:
            - celery
            - -A
            - app.workers
            - beat
            - --loglevel=info
            - --schedule=/tmp/celerybeat-schedule
            - --pidfile=/tmp/celerybeat.pid
          envFrom:
            - configMapRef:
                name: docutil-config
            - secretRef:
                name: docutil-secrets
          env:
            - name: DATABASE_URL_SYNC
              value: "postgresql://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@postgres.docutil.svc:5432/$(POSTGRES_DB)"
            - name: REDIS_URL
              value: "redis://:$(REDIS_PASSWORD)@redis.docutil.svc:6379/0"
            - name: CELERY_BROKER_URL
              value: "amqp://$(RABBITMQ_USER):$(RABBITMQ_PASSWORD)@rabbitmq.docutil.svc:5672/"
            - name: CELERY_RESULT_BACKEND
              value: "redis://:$(REDIS_PASSWORD)@redis.docutil.svc:6379/1"
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 256Mi
```

#### 3.4.13 Ingress (Nginx Ingress Controller)

```bash
# Nginx Ingress Controller 설치
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm install ingress-nginx ingress-nginx/ingress-nginx \
    --namespace ingress-nginx --create-namespace \
    --set controller.service.type=NodePort \
    --set controller.service.nodePorts.http=80 \
    --set controller.service.nodePorts.https=443
```

```yaml
# k8s/base/ingress/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: docutil-ingress
  namespace: docutil
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "500m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "75"
    # cert-manager 사용 시
    # cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - docutil.yourdomain.com
      secretName: docutil-tls
  rules:
    - host: docutil.yourdomain.com
      http:
        paths:
          - path: /api/v1/chat/ws
            pathType: Prefix
            backend:
              service:
                name: api
                port:
                  number: 8000
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: api
                port:
                  number: 8000
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend
                port:
                  number: 3002
```

**WebSocket Ingress 추가 설정**:

```yaml
# k8s/base/ingress/websocket-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: docutil-ws-ingress
  namespace: docutil
  annotations:
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
    nginx.ingress.kubernetes.io/upstream-hash-by: "$remote_addr"
    nginx.ingress.kubernetes.io/configuration-snippet: |
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection "upgrade";
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - docutil.yourdomain.com
      secretName: docutil-tls
  rules:
    - host: docutil.yourdomain.com
      http:
        paths:
          - path: /api/v1/chat/ws
            pathType: Prefix
            backend:
              service:
                name: api
                port:
                  number: 8000
```

#### 3.4.14 HPA (Horizontal Pod Autoscaler)

```yaml
# k8s/base/hpa/api-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
  namespace: docutil
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 2
  maxReplicas: 6
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Pods
          value: 1
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Pods
          value: 1
          periodSeconds: 120
---
# k8s/base/hpa/celery-worker-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: celery-worker-hpa
  namespace: docutil
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: celery-worker
  minReplicas: 2
  maxReplicas: 8
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 30
      policies:
        - type: Pods
          value: 2
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
```

### 3.5 Container Registry 전략

```bash
# 방법 A: k3s 로컬 이미지 (단일 노드, 가장 간단)
# 서버에서 직접 빌드하면 k3s가 로컬 이미지 사용
docker build -t docutil-backend:latest ./backend
docker build -t docutil-frontend:latest ./frontend

# k3s에 이미지 임포트
sudo k3s ctr images import <(docker save docutil-backend:latest)
sudo k3s ctr images import <(docker save docutil-frontend:latest)

# 방법 B: Private Registry (멀티 노드 시)
# k3s에 내장 registry 미러 사용 또는 Harbor 설치
docker run -d -p 5000:5000 --restart always --name registry registry:2

# 이미지 태깅 및 푸시
docker tag docutil-backend:latest localhost:5000/docutil-backend:latest
docker push localhost:5000/docutil-backend:latest

# 방법 C: GitHub Container Registry (GHCR)
# CI/CD에서 빌드 후 ghcr.io에 푸시
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
docker tag docutil-backend:latest ghcr.io/your-org/docutil-backend:latest
docker push ghcr.io/your-org/docutil-backend:latest
```

### 3.6 모니터링 (Prometheus Operator)

```bash
# kube-prometheus-stack 설치 (Prometheus + Grafana + Alertmanager)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install kube-prometheus prometheus-community/kube-prometheus-stack \
    --namespace monitoring --create-namespace \
    --set grafana.adminPassword='<GRAFANA_PASSWORD>' \
    --set prometheus.prometheusSpec.retention=15d \
    --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.storageClassName=local-path \
    --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=20Gi
```

```yaml
# k8s/base/monitoring/servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: docutil-api
  namespace: docutil
  labels:
    release: kube-prometheus
spec:
  selector:
    matchLabels:
      app: api
  endpoints:
    - port: http
      path: /metrics
      interval: 15s
```

### 3.7 로깅 (Loki Stack)

```bash
# Loki + Promtail 설치
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

helm install loki grafana/loki-stack \
    --namespace monitoring \
    --set loki.persistence.enabled=true \
    --set loki.persistence.size=20Gi \
    --set promtail.enabled=true
```

### 3.8 Docker Compose → K8s 마이그레이션 절차

```
1. [사전] K8s 매니페스트 준비 및 검증 (dry-run)
2. [사전] Container Registry에 이미지 빌드/푸시
3. [사전] K8s에서 Stateful 서비스만 먼저 배포
4. Docker Compose 서비스 중지
5. PV에 데이터 복원 (PG dump, Qdrant snapshot, MinIO data)
6. K8s Stateless 서비스 배포
7. Ingress 설정 + DNS 전환
8. 검증
9. Docker Compose 환경 정리
```

**세부 명령**:

```bash
# 1. 네임스페이스 및 시크릿 생성
kubectl apply -f k8s/base/namespace.yaml
kubectl apply -f k8s/base/secrets/app-secrets.yaml
kubectl apply -f k8s/base/configmaps/app-config.yaml

# 2. Stateful 서비스 배포
kubectl apply -f k8s/base/stateful/

# 모든 StatefulSet이 Ready 될 때까지 대기
kubectl -n docutil rollout status statefulset/postgres
kubectl -n docutil rollout status statefulset/qdrant
kubectl -n docutil rollout status statefulset/redis
kubectl -n docutil rollout status statefulset/rabbitmq
kubectl -n docutil rollout status statefulset/minio

# 3. 데이터 복원 (PostgreSQL 예시)
# Pod에 백업 파일 복사
kubectl cp ./backups/docutil_dump.backup docutil/postgres-0:/tmp/

# 복원 실행
kubectl exec -n docutil postgres-0 -- pg_restore \
    -U docutil -d docutil --clean --if-exists /tmp/docutil_dump.backup

# 4. Stateless 서비스 배포
kubectl apply -f k8s/base/stateless/

# 5. Ingress 배포
kubectl apply -f k8s/base/ingress/

# 6. HPA 배포
kubectl apply -f k8s/base/hpa/

# 7. 전체 확인
kubectl -n docutil get all
kubectl -n docutil get ingress
```

### 3.9 Kustomize 기본 설정

```yaml
# k8s/base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: docutil

resources:
  - namespace.yaml
  - configmaps/app-config.yaml
  - secrets/app-secrets.yaml
  - stateful/postgres-statefulset.yaml
  - stateful/postgres-service.yaml
  - stateful/qdrant-statefulset.yaml
  - stateful/redis-statefulset.yaml
  - stateful/rabbitmq-statefulset.yaml
  - stateful/minio-statefulset.yaml
  - stateless/api-deployment.yaml
  - stateless/api-service.yaml
  - stateless/frontend-deployment.yaml
  - stateless/frontend-service.yaml
  - stateless/celery-worker-deployment.yaml
  - stateless/celery-beat-deployment.yaml
  - stateless/flower-deployment.yaml
  - ingress/ingress.yaml
  - hpa/api-hpa.yaml
  - hpa/celery-worker-hpa.yaml

commonLabels:
  app.kubernetes.io/part-of: docutil
  app.kubernetes.io/managed-by: kustomize
```

```yaml
# k8s/overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

patches:
  - path: patches/replicas.yaml
  - path: patches/resource-limits.yaml

images:
  - name: docutil-backend
    newName: ghcr.io/your-org/docutil-backend
    newTag: "1.0.0"
  - name: docutil-frontend
    newName: ghcr.io/your-org/docutil-frontend
    newTag: "1.0.0"
```

```yaml
# k8s/overlays/prod/patches/replicas.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 3
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker
spec:
  replicas: 3
```

```bash
# Kustomize로 배포
kubectl apply -k k8s/overlays/prod/

# dry-run으로 먼저 확인
kubectl apply -k k8s/overlays/prod/ --dry-run=client -o yaml
```

---

## 4. Phase 3: 운영 안정화

### 4.1 모니터링 및 알림

#### Prometheus AlertManager 규칙

```yaml
# k8s/base/monitoring/alerts.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: docutil-alerts
  namespace: monitoring
  labels:
    release: kube-prometheus
spec:
  groups:
    - name: docutil.rules
      rules:
        # API 응답 시간 초과
        - alert: APIHighLatency
          expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{service="api"}[5m])) by (le)) > 2
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "API P95 응답시간 2초 초과"

        # API Pod 다운
        - alert: APIPodDown
          expr: kube_deployment_status_replicas_available{deployment="api",namespace="docutil"} == 0
          for: 1m
          labels:
            severity: critical
          annotations:
            summary: "API Pod가 모두 다운됨"

        # PostgreSQL 커넥션 부족
        - alert: PostgresConnectionHigh
          expr: pg_stat_activity_count / pg_settings_max_connections > 0.8
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "PostgreSQL 커넥션 사용률 80% 초과"

        # Celery 큐 적체
        - alert: CeleryQueueBacklog
          expr: celery_active_tasks > 50
          for: 10m
          labels:
            severity: warning
          annotations:
            summary: "Celery 작업 큐가 적체됨 (50개 초과)"

        # 디스크 사용률
        - alert: DiskUsageHigh
          expr: (node_filesystem_size_bytes - node_filesystem_avail_bytes) / node_filesystem_size_bytes > 0.85
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "디스크 사용률 85% 초과"

        # Qdrant 비정상
        - alert: QdrantUnhealthy
          expr: up{job="qdrant"} == 0
          for: 2m
          labels:
            severity: critical
          annotations:
            summary: "Qdrant 벡터DB가 응답하지 않음"
```

### 4.2 백업/복구 자동화 (K8s CronJob)

```yaml
# k8s/base/jobs/backup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: db-backup
  namespace: docutil
spec:
  schedule: "0 2 * * *"  # 매일 새벽 2시
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: backup
              image: postgres:17-alpine
              command:
                - /bin/sh
                - -c
                - |
                  TIMESTAMP=$(date +%Y%m%d_%H%M%S)
                  pg_dump -h postgres.docutil.svc -U $POSTGRES_USER -d $POSTGRES_DB \
                      --format=custom --compress=9 \
                      --file=/backups/postgres_${TIMESTAMP}.backup
                  # 14일 이상 된 백업 삭제
                  find /backups -name "postgres_*.backup" -mtime +14 -delete
              env:
                - name: POSTGRES_USER
                  valueFrom:
                    secretKeyRef:
                      name: docutil-secrets
                      key: POSTGRES_USER
                - name: POSTGRES_DB
                  valueFrom:
                    secretKeyRef:
                      name: docutil-secrets
                      key: POSTGRES_DB
                - name: PGPASSWORD
                  valueFrom:
                    secretKeyRef:
                      name: docutil-secrets
                      key: POSTGRES_PASSWORD
              volumeMounts:
                - name: backup-storage
                  mountPath: /backups
          volumes:
            - name: backup-storage
              persistentVolumeClaim:
                claimName: backup-pvc
          restartPolicy: OnFailure
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
```

### 4.3 스케일링 전략

| 서비스 | 스케일링 유형 | 전략 |
|--------|-------------|------|
| API | HPA (CPU 70%) | min=2, max=6, 1 Pod/60초 |
| Frontend | HPA (CPU 70%) | min=2, max=4 |
| Celery Worker | HPA (CPU 70%) | min=2, max=8, 큐 길이 기반 확장 권장 |
| Celery Beat | 고정 1 | 절대 1개 초과 불가 (중복 스케줄 방지) |
| PostgreSQL | 수직 스케일링 | CPU/RAM 증설, Read Replica 추가(별도 구성) |
| Qdrant | 수직 스케일링 | RAM 증설 (인덱스 크기에 비례) |
| Redis | 수직 스케일링 | maxmemory 조정, Sentinel/Cluster(별도) |
| RabbitMQ | 수직 스케일링 | 필요시 클러스터 구성 |

### 4.4 장애 대응 절차

```
Level 1 - 자동 복구 (K8s 내장):
  - Pod CrashLoopBackOff → liveness probe 실패 시 자동 재시작
  - Pod 비정상 → readiness probe 실패 시 트래픽 제외 + 재시작
  - 노드 장애 → Pod 다른 노드에 재스케줄 (멀티 노드 시)

Level 2 - 수동 개입 필요:
  - Stateful 서비스 장애 (PG, Qdrant)
    1. kubectl describe pod 로 원인 파악
    2. 데이터 무결성 확인
    3. StatefulSet 재시작: kubectl rollout restart statefulset/postgres -n docutil
    4. 필요시 백업으로 복원

  - 전체 서비스 다운
    1. kubectl get events -n docutil --sort-by='.lastTimestamp' 로 이벤트 확인
    2. 노드 리소스 확인: kubectl top nodes
    3. 인프라 서비스부터 순차 복구: PG → Redis → RabbitMQ → Qdrant → MinIO → API → Workers

Level 3 - 재해 복구:
  1. 최신 백업 파일 확인
  2. K8s 클러스터 재구축 (k3s install)
  3. PV/PVC 재생성
  4. 백업 데이터 복원
  5. 서비스 배포
  6. DNS 확인
```

---

## 5. 리스크 관리 및 롤백 전략

### 5.1 주요 리스크

| 리스크 | 영향도 | 발생 확률 | 완화 전략 |
|--------|--------|----------|----------|
| 데이터 손실 | 치명적 | 낮음 | 이중 백업 (로컬 + 원격), 이전 전 체크섬 검증 |
| 긴 다운타임 | 높음 | 중간 | 사전 리허설, 병렬 환경 구축 후 DNS 스위칭 |
| 환경 차이 (Win/Linux) | 중간 | 중간 | Docker 기반이므로 차이 최소, 경로 구분자 주의 |
| SSL 인증서 만료 | 중간 | 낮음 | certbot 자동 갱신 + 만료 알림 |
| K8s 전환 실패 | 중간 | 중간 | Docker Compose 환경 유지하면서 병렬 테스트 |

### 5.2 롤백 전략

#### Phase 1 롤백 (Ubuntu Docker Compose)

```bash
# Ubuntu 서비스 중지
cd /opt/docutil
docker compose down

# DNS를 원래 Windows 서버로 되돌림 (또는 hosts 파일 복원)

# Windows에서 서비스 재기동
cd /d/workspace/document_utilization
docker compose up -d
```

#### Phase 2 롤백 (K8s → Docker Compose)

```bash
# K8s 서비스 중지
kubectl delete -k k8s/overlays/prod/

# Docker Compose로 복귀
cd /opt/docutil
docker compose up -d

# 최신 데이터가 K8s PV에만 있을 경우:
# PV에서 데이터를 추출하여 Docker 볼륨에 복원
```

---

## 6. 일정 계획

```
Week 1: Phase 1 준비
  - Day 1-2: Ubuntu 서버 프로비저닝 + OS 설정 + Docker 설치
  - Day 3: SSL 인증서 + nginx 설정 + 코드 전송
  - Day 4: .env 설정 + 서비스 기동 테스트 (빈 데이터)
  - Day 5: 데이터 마이그레이션 리허설

Week 2: Phase 1 실행
  - Day 1: 데이터 마이그레이션 본 실행 + 서비스 전환
  - Day 2-3: 검증 + 모니터링 + 버그 수정
  - Day 4-5: CI/CD 파이프라인 구축 + 백업 자동화

Week 3: Phase 1 안정화 + Phase 2 준비
  - Day 1-2: 운영 모니터링 + 성능 튜닝
  - Day 3-5: K8s 매니페스트 작성 + 로컬 테스트

Week 4: Phase 2 실행
  - Day 1: k3s 설치 + Nginx Ingress + cert-manager
  - Day 2: Stateful 서비스 배포 + 데이터 이전
  - Day 3: Stateless 서비스 배포 + Ingress 설정
  - Day 4: 검증 + HPA + 모니터링 연동
  - Day 5: DNS 전환 + Phase 2 완료

Week 5: Phase 3 안정화
  - 알림 규칙 설정
  - 백업 CronJob 활성화
  - 장애 대응 매뉴얼 정리
  - 성능 테스트 + 튜닝
```

---

## ADR (Architecture Decision Records)

### ADR-001: K8s 배포 도구로 k3s 선택

- **컨텍스트**: 14개 컨테이너를 단일(또는 소규모) 서버에서 K8s로 운영해야 함
- **결정**: k3s 사용
- **대안**: kubeadm (리소스 과다), microk8s (snap 의존성), managed K8s (비용 과다)
- **결과**: 경량 K8s로 리소스 절약, 단일 바이너리로 설치/운영 단순화. 단 etcd 대신 sqlite 사용으로 대규모 클러스터에는 부적합

### ADR-002: Stateful 서비스 자체 관리 vs Operator

- **컨텍스트**: PostgreSQL, Redis, RabbitMQ를 K8s에서 어떻게 운영할 것인가
- **결정**: Phase 2에서는 StatefulSet 직접 관리. 운영 안정화 후 Operator 도입 검토
- **대안**: CloudNativePG Operator, Redis Operator, RabbitMQ Cluster Operator
- **결과**: 초기 복잡도를 낮추고 Docker Compose와 최대한 유사한 구조를 유지. 향후 HA 필요시 Operator로 전환

### ADR-003: Ingress Controller로 Nginx Ingress 선택

- **컨텍스트**: 기존 Nginx 리버스 프록시 설정을 K8s에서도 유지하고 싶음
- **결정**: Nginx Ingress Controller 사용 (k3s 기본 Traefik 대신)
- **대안**: Traefik (k3s 기본), Istio Gateway
- **결과**: 기존 Nginx 설정의 1:1 대응이 가능하여 마이그레이션 리스크 최소화. WebSocket 설정도 annotation으로 처리 가능

### ADR-004: 서비스 메시 도입 보류

- **컨텍스트**: 서비스 간 통신 보안, 관측성, 트래픽 관리를 강화할 필요가 있는가
- **결정**: Phase 2~3에서는 서비스 메시 미도입
- **대안**: Istio, Linkerd
- **결과**: 현재 14개 컨테이너 규모에서 서비스 메시의 리소스 오버헤드와 운영 복잡도가 이점 대비 과도함. 서비스 수가 30개 이상으로 증가하거나 mTLS가 필수 요건이 될 때 재검토
