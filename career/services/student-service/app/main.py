"""
Student Service - Main Application Entry Point.
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
from sqlalchemy import text

from .config import settings
from .database import engine
from .routers import students_router, curriculum_router

# Setup logging with file handlers
from shared.common.logging import setup_logging, get_logger

setup_logging("student-service", log_level=settings.LOG_LEVEL, json_format=False)
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
    # Startup
    logger.info(f"Starting {settings.SERVICE_NAME}...")
    logger.info(f"Database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    logger.info(f"Schema: {settings.DB_SCHEMA}")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.SERVICE_NAME}...")
    await engine.dispose()


# Create FastAPI application
app = FastAPI(
    title="Student Service",
    description="Student data management service",
    version="1.0.0",
    lifespan=lifespan,
    default_response_class=UTF8JSONResponse,  # Use UTF-8 JSON response by default
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
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
app.include_router(students_router, prefix="/students", tags=["Students"])
app.include_router(curriculum_router, prefix="/curriculum", tags=["Curriculum"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Simple database connectivity check (SQLAlchemy 2.0 requires text())
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"

    return {
        "service": settings.SERVICE_NAME,
        "status": "healthy",
        "database": db_status,
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "docs": "/docs" if settings.DEBUG else "Disabled in production",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
    )
