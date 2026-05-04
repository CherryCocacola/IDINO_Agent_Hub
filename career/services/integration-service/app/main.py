"""
Integration Service - Main Application.

Handles external API integrations with Worknet, University, and HRD-Net.
Uses mock data when USE_MOCK_DATA is enabled.
"""
import sys
from pathlib import Path

# Add project root to path for shared imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import worknet_router, university_router, hrd_router, sync_router

# Setup logging with file handlers
from shared.common.logging import setup_logging, get_logger

setup_logging("integration-service", json_format=False)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info(f"Starting {settings.SERVICE_NAME} on port {settings.SERVICE_PORT}")
    logger.info(f"Mock mode: {settings.USE_MOCK_DATA}")

    # TODO: Initialize Redis connection for caching
    # redis = await aioredis.from_url(settings.REDIS_URL)

    yield

    # Cleanup
    # await redis.close()
    logger.info(f"{settings.SERVICE_NAME} shutdown complete")


app = FastAPI(
    title=settings.SERVICE_NAME,
    description="External API integration service for Worknet, University, and HRD-Net",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(
    worknet_router,
    prefix="/integration/worknet",
    tags=["worknet"]
)

app.include_router(
    university_router,
    prefix="/integration/university",
    tags=["university"]
)

app.include_router(
    hrd_router,
    prefix="/integration/hrd",
    tags=["hrd"]
)

app.include_router(
    sync_router,
    prefix="/integration/sync",
    tags=["sync"]
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "mock_mode": settings.USE_MOCK_DATA
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.SERVICE_NAME,
        "description": "External API integration service",
        "docs": "/docs",
        "integrations": {
            "worknet": "/integration/worknet",
            "university": "/integration/university",
            "hrd": "/integration/hrd",
            "sync": "/integration/sync"
        },
        "mock_mode": settings.USE_MOCK_DATA
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=True
    )
