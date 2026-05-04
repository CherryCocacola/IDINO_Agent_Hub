import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .routers import advisor_router
from .config import get_settings
from .database import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    print(f"Advisor Service starting on port {settings.SERVICE_PORT}")
    try:
        await init_db()
    except Exception as e:
        print(f"Database init error: {e}")
    yield
    await close_db()


app = FastAPI(
    title="Advisor Workspace Service",
    description="Phase 13: Advisor Workspace - 코호트 관리 및 학생 지원",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

app.include_router(advisor_router)


@app.get("/")
async def root():
    return {
        "service": "advisor-service", "version": "1.0.0", "phase": "P2 - Advisor Workspace",
        "endpoints": {
            "dashboard": "/advisor/dashboard/{advisor_id}",
            "students": "/advisor/students/{advisor_id}",
            "interventions": "/advisor/interventions",
            "notes": "/advisor/notes",
            "snapshots": "/advisor/snapshots/{advisor_id}",
        },
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "advisor-service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=get_settings().SERVICE_PORT, reload=True)
