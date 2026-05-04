import sys
from pathlib import Path

# Add project root to path for shared imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import traceback
import logging

from .routers import coaching_router
from .config import get_settings
from .database import init_db, close_db

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    print(f"Coaching Service starting on port {settings.SERVICE_PORT}")
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
    print("Coaching Service shutting down")


app = FastAPI(
    title="AI Coaching Service",
    description="Phase 9: AI Coach Loop - Goal → Plan → Check-in → Retrospective",
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
app.include_router(coaching_router)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_trace = traceback.format_exc()
    logger.error(f"Unhandled error: {exc}")
    logger.error(f"Traceback: {error_trace}")
    print(f"ERROR: {exc}")
    print(f"TRACEBACK: {error_trace}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": error_trace}
    )


@app.get("/")
async def root():
    return {
        "service": "coaching-service",
        "version": "1.0.0",
        "phase": "P1 - AI Coach Loop",
        "description": "AI 코칭 서비스 - 목표 설정, 계획, 체크인, 회고",
        "endpoints": {
            "goals": "/coaching/goals",
            "plans": "/coaching/plans",
            "checkins": "/coaching/checkins",
            "retrospectives": "/coaching/retrospectives",
            "session": "/coaching/session/{goal_id}",
            "ai_coach": "/coaching/ai-coach",
            "progress": "/coaching/progress/{student_id}",
            "health": "/health",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "coaching-service"}


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=True
    )
