"""
Competency Service - Main Application.

Handles competency definitions, assessments, scoring, and reporting.
"""
import sys
import json
from pathlib import Path

# Add project root to path for shared imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .database import engine, Base
from .routers import competency_router

# Setup logging with file handlers
from shared.common.logging import setup_logging, get_logger

setup_logging("competency-service", json_format=False)
logger = get_logger(__name__)


class UTF8JSONResponse(JSONResponse):
    """Custom JSON response with explicit UTF-8 encoding."""
    media_type = "application/json; charset=utf-8"

    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,  # Allow non-ASCII characters (Korean, etc.)
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info(f"Starting {settings.SERVICE_NAME} on port {settings.SERVICE_PORT}")

    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables initialized")

    yield

    # Cleanup
    await engine.dispose()
    logger.info(f"{settings.SERVICE_NAME} shutdown complete")


app = FastAPI(
    title=settings.SERVICE_NAME,
    description="Competency assessment, scoring, and reporting service",
    version="1.0.0",
    lifespan=lifespan,
    default_response_class=UTF8JSONResponse,  # Use UTF-8 JSON response by default
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


@app.middleware("http")
async def add_charset_header(request: Request, call_next):
    """Middleware to ensure UTF-8 charset in all JSON responses."""
    response: Response = await call_next(request)
    
    # Add charset to content-type if it's JSON
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type and "charset" not in content_type:
        response.headers["content-type"] = "application/json; charset=utf-8"
    
    return response


# Include routers
app.include_router(
    competency_router,
    prefix="/competency",
    tags=["competency"]
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.SERVICE_NAME,
        "description": "Competency assessment and scoring service",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=True
    )
