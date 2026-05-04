import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .routers import simulation_router
from .config import get_settings
from .database import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    print(f"Simulation Service starting on port {settings.SERVICE_PORT}")
    try:
        await init_db()
    except Exception as e:
        print(f"Database init error: {e}")
    yield
    await close_db()


app = FastAPI(
    title="What-if Planner Service",
    description="Phase 12: What-if Planner - 가상 시나리오 시뮬레이션",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

app.include_router(simulation_router)


@app.get("/")
async def root():
    return {
        "service": "simulation-service", "version": "1.0.0", "phase": "P2 - What-if Planner",
        "endpoints": {
            "scenarios": "/simulation/scenarios",
            "compare": "/simulation/compare",
            "career_path": "/simulation/career-path",
            "skill_development": "/simulation/skill-development",
        },
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "simulation-service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=get_settings().SERVICE_PORT, reload=True)
