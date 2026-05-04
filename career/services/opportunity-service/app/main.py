import sys
from pathlib import Path

# Add project root to path for shared imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routers import opportunity_router
from .config import get_settings
from .database import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    print(f"Opportunity Service starting on port {settings.SERVICE_PORT}")
    try:
        await init_db()
        print("Database connection initialized")
    except Exception as e:
        print(f"Database initialization error: {e}")
    yield
    # Shutdown
    try:
        await close_db()
        print("Database connection closed")
    except Exception as e:
        print(f"Database cleanup error: {e}")
    print("Opportunity Service shutting down")


app = FastAPI(
    title="Opportunity Service",
    description="Phase 8: Opportunity Marketplace - 통합 기회 추천 서비스",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(opportunity_router)


@app.get("/")
async def root():
    return {
        "service": "opportunity-service",
        "version": "1.0.0",
        "phase": "P1 - Opportunity Marketplace",
        "description": "인턴십, 공모전, 연구참여 등 통합 기회 추천",
        "endpoints": {
            "opportunities": "/opportunities",
            "recommend": "/opportunities/recommend",
            "applications": "/opportunities/applications/{student_id}",
            "search": "/opportunities/search",
            "health": "/health",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "opportunity-service"}


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=True
    )
