"""
Auth Service - Main Application Entry Point.
"""
import logging
import json
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from .config import settings
from .database import engine
from .routers import auth_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


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

    # Initialize Redis connection
    redis_connected = False
    try:
        app.state.redis = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        await app.state.redis.ping()
        redis_connected = True
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis connection failed (service will continue): {e}")
        # Create a mock redis for development without Redis
        app.state.redis = None

    # Test database connection
    db_connected = False
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        db_connected = True
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

    logger.info(f"{settings.SERVICE_NAME} started successfully")
    logger.info(f"  - Database: {'connected' if db_connected else 'disconnected'}")
    logger.info(f"  - Redis: {'connected' if redis_connected else 'disconnected'}")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.SERVICE_NAME}...")

    if app.state.redis:
        await app.state.redis.close()

    await engine.dispose()
    logger.info(f"{settings.SERVICE_NAME} shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Auth Service",
    description="JWT authentication and session management service with 2FA support",
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
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    # Check Redis
    redis_status = "disconnected"
    if app.state.redis:
        try:
            await app.state.redis.ping()
            redis_status = "healthy"
        except Exception:
            redis_status = "unhealthy"

    # Check Database
    db_status = "disconnected"
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    return {
        "service": settings.SERVICE_NAME,
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "redis": redis_status,
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
