# =============================================================================
# Project Nexus - Docker 이미지 (Machine A — Orchestrator 전용)
# ---------------------------------------------------------------------------
# 본 Dockerfile 은 Nexus 의 2-Machine 토폴로지(Architecture P4) 중 Machine A
# (오케스트레이터, FastAPI 진입점) 을 컨테이너화한다. Machine B (GPU 서버, vLLM)
# 는 별도 호스트에서 동작하며 본 컨테이너는 LAN HTTP/SSE 로만 호출한다.
#
# 정책 준수:
#   - ADR-11: Nexus 별도 PG 인스턴스 유지 (에어갭 격리). 통합 PG 와 미공유.
#   - architecture.md P4: Machine A 는 GPU/CUDA 직접 호출 금지 (vLLM 은 Machine B)
#   - anti-patterns #10: 외부 네트워크 호출 금지. 모든 URL = LAN 주소만.
#
# 미해결 이슈 (시연 호스트 192.168.10.39 미적합):
#   1) GPU 부재 → Machine B (vLLM 서버) 미배포 시 본 컨테이너 호출 모두 timeout
#   2) ADR-13 공유 시크릿 인증 + LAN-only 정책 — 외부망 노출 금지
# 따라서 본 Dockerfile 은 monorepo 자산으로만 보존하고 실제 부팅은 별도 LAN 호스트
# (예: 192.168.22.28 — CLAUDE.md 명시 LAN 전용 Nexus 호스트) 에서 진행한다.
# =============================================================================

FROM python:3.11-slim AS build

# 시스템 의존성 (sentence-transformers, asyncpg, redis 등 빌드 타임)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        build-essential gcc git curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /src

# requirements 만 먼저 복사하여 pip 캐시 레이어 확보
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir --prefix=/install -r requirements.txt

# 소스 복사 (.dockerignore 가 tests/.git/cache 등 제외)
COPY . ./


FROM python:3.11-slim AS runtime

# 런타임 의존성 (curl 헬스체크용)
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# build stage 에서 설치된 site-packages 복사
COPY --from=build /install /usr/local
COPY --from=build /src /app

WORKDIR /app
EXPOSE 8001

# 에어갭 정책 — 외부 네트워크 차단을 호스트 방화벽 / docker network 에서 강제.
# 본 컨테이너 자체에 PIP_INDEX_URL 등 외부 URL 미설정.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD curl -fsS http://localhost:8001/health >/dev/null || exit 1

# Nexus FastAPI 진입점 (web/app.py 의 ASGI app)
ENTRYPOINT ["python", "-m", "uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8001"]
