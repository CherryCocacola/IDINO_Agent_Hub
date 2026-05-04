import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routers import risk_router
from .config import get_settings
from .database import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    print(f"Risk Service starting on port {settings.SERVICE_PORT}")
    try:
        await init_db()
        print("Database connection initialized")
    except Exception as e:
        print(f"Database initialization error: {e}")
    yield
    try:
        await close_db()
        print("Database connection closed")
    except Exception as e:
        print(f"Database cleanup error: {e}")
    print("Risk Service shutting down")


app = FastAPI(
    title="Risk Alert Service",
    description="Phase 10: Risk Alerts - 학업 제약 조기 경고 시스템",
    version="1.0.0",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(risk_router)


@app.get("/")
async def root():
    return {
        "service": "risk-service",
        "version": "1.0.0",
        "phase": "P1 - Risk Alerts",
        "description": "학업 제약 조기 경고 시스템",
        "endpoints": {
            "analyze": "/risks/analyze",
            "profile": "/risks/profile/{student_id}",
            "alerts": "/risks/alerts/{student_id}",
            "constraints": "/risks/constraints/{student_id}",
            "prerequisites": "/risks/prerequisites",
            "health": "/health",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "risk-service"}


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.SERVICE_PORT, reload=True)
