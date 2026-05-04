import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .routers import badge_router
from .config import get_settings
from .database import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    print(f"Badge Service starting on port {settings.SERVICE_PORT}")
    try:
        await init_db()
    except Exception as e:
        print(f"Database init error: {e}")
    yield
    await close_db()


app = FastAPI(
    title="Badge & Skill Passport Service",
    description="Phase 11: Skill Passport/Badges - 디지털 뱃지 및 스킬 인증",
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

app.include_router(badge_router)


@app.get("/")
async def root():
    return {
        "service": "badge-service", "version": "1.0.0", "phase": "P2 - Skill Passport",
        "endpoints": {
            "badges": "/badges", "student_badges": "/badges/student/{student_id}",
            "passport": "/passport/{student_id}", "verify": "/badges/verify/{hash}",
        },
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "badge-service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=get_settings().SERVICE_PORT, reload=True)
