"""
FastAPI application entry point for the Document Utilization System.

Creates the FastAPI application instance, registers all middleware, and
includes all module routers under the ``/api/v1`` prefix.

Usage
-----
Start the development server::

    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

import app.modules.agents.models  # noqa: F401
import app.modules.api_keys.models  # noqa: F401
import app.modules.audit.models  # noqa: F401
import app.modules.chat.models  # noqa: F401
import app.modules.documents.models  # noqa: F401
import app.modules.documents_v2.models  # noqa: F401
import app.modules.faq.models  # noqa: F401
import app.modules.organizations.models  # noqa: F401
import app.modules.projects.models  # noqa: F401
import app.modules.reports.models  # noqa: F401
import app.modules.search.models  # noqa: F401
import app.modules.search_scopes.models  # noqa: F401
import app.modules.templates.models  # noqa: F401

# ---------------------------------------------------------------------------
# 모든 ORM 모델을 미리 import하여 SQLAlchemy MetaData에 등록한다.
# 이렇게 해야 FK 참조(tb_folders, tb_search_scopes 등)가 정상 동작한다.
# ---------------------------------------------------------------------------
import app.modules.evaluation.models  # noqa: F401
import app.modules.users.models  # noqa: F401
from app.core.config import get_settings
from app.core.middleware import RateLimitMiddleware, RequestLoggingMiddleware
from app.modules.admin.router import router as admin_router
from app.modules.agents.router import router as agents_router
from app.modules.api_keys.router import router as api_keys_router
from app.modules.audit.router import router as audit_router

# ---------------------------------------------------------------------------
# Import all routers
# ---------------------------------------------------------------------------
from app.modules.auth.router import router as auth_router
from app.modules.chat.router import router as chat_router
from app.modules.chat.websocket import ws_router as chat_ws_router
from app.modules.documents.router import router as documents_router
from app.modules.documents_v2.router import router as documents_v2_router
from app.modules.faq.router import router as faq_router
from app.modules.organizations.router import router as organizations_router
from app.modules.projects.router import router as projects_router
from app.modules.reports.router import router as reports_router
from app.modules.search.router import router as search_router
from app.modules.search_scopes.router import router as search_scopes_router
from app.modules.templates.router import router as templates_router
from app.modules.evaluation.router import router as evaluation_router
from app.modules.users.router import router as users_router
from app.modules.settings.router import router as settings_router

settings = get_settings()


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager.

    Startup
    -------
    Initialise shared resources such as Redis connection pools, Qdrant client
    connections, or Celery workers.

    Shutdown
    --------
    Gracefully close all connections and release resources.
    """
    # Startup
    yield
    # Shutdown: cleanup shared resources
    from app.core.cache import close_redis
    from app.modules.search.service import close_http_client

    await close_http_client()
    await close_redis()


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Document Utilization System",
    description="통합 문서 활용 시스템 API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    redirect_slashes=False,
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

# CORS -- must be added before other middleware so that preflight requests
# are handled correctly regardless of other middleware ordering.
# allow_origins=["*"] + allow_credentials=True 는 Starlette에서 요청
# Origin을 그대로 미러링하여 처리하므로 외부 IP 접속 시에도 동작한다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis 기반 슬라이딩 윈도우 Rate Limiter
# 개발 환경에서는 충분히 여유있게 설정 (프로덕션에서 조정)
app.add_middleware(
    RateLimitMiddleware,
    redis_url=settings.redis_url,
    max_requests=1000,
    window_seconds=60,
)

# 요청 로깅 미들웨어
app.add_middleware(RequestLoggingMiddleware)

# Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# ---------------------------------------------------------------------------
# Register routers
# ---------------------------------------------------------------------------
API_V1 = "/api/v1"

app.include_router(auth_router, prefix=f"{API_V1}/auth", tags=["Authentication"])
app.include_router(users_router, prefix=f"{API_V1}/users", tags=["Users"])
app.include_router(organizations_router, prefix=f"{API_V1}/organizations", tags=["Organizations"])
app.include_router(projects_router, prefix=f"{API_V1}", tags=["Projects"])
app.include_router(documents_router, prefix=f"{API_V1}", tags=["Documents"])
app.include_router(documents_v2_router, prefix=f"{API_V1}", tags=["Documents V2"])
app.include_router(search_scopes_router, prefix=f"{API_V1}", tags=["Search Scopes"])
app.include_router(search_router, prefix=f"{API_V1}", tags=["Search"])
app.include_router(chat_router, prefix=f"{API_V1}", tags=["Chat"])
app.include_router(chat_ws_router, prefix=f"{API_V1}", tags=["Chat WebSocket"])
app.include_router(reports_router, prefix=f"{API_V1}", tags=["Reports"])
app.include_router(admin_router, prefix=f"{API_V1}", tags=["Admin"])
app.include_router(api_keys_router, prefix=f"{API_V1}", tags=["API Keys"])
app.include_router(audit_router, prefix=f"{API_V1}", tags=["Audit"])
app.include_router(faq_router, prefix=f"{API_V1}", tags=["FAQ"])
app.include_router(templates_router, prefix=f"{API_V1}", tags=["Templates"])
app.include_router(agents_router, prefix=f"{API_V1}", tags=["Agents"])
app.include_router(evaluation_router, prefix=f"{API_V1}", tags=["Evaluation"])
app.include_router(settings_router, prefix=f"{API_V1}", tags=["Settings"])


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health")
async def health_check():
    """Simple health-check endpoint for load balancers and orchestrators."""
    return {"status": "healthy", "version": "1.0.0"}
