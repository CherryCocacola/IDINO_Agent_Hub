import sys
from pathlib import Path

# Add project root to path for shared imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routers import skill_router
from .config import get_settings
from .database import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    print(f"Skill Service starting on port {settings.SERVICE_PORT}")
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
    print("Skill Service shutting down")


app = FastAPI(
    title="Skill Service",
    description="Phase 7: Skill Graph & Gap Analysis - LinkedIn Career Explorer style",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 설정
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(skill_router)


@app.get("/")
async def root():
    return {
        "service": "skill-service",
        "version": "1.0.0",
        "phase": "P1 - Skill Graph & Gap",
        "description": "스킬 그래프 및 갭 분석 서비스",
        "endpoints": {
            "skills": "/skills",
            "student_skills": "/skills/student/{student_id}",
            "role_skills": "/skills/role/{role_cd}",
            "skill_graph": "/skills/graph",
            "gap_analysis": "/skills/gap-analysis",
            "health": "/health",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "skill-service"}


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=True
    )
