"""Portfolio Service - Main Application"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers.portfolio import router as portfolio_router
from .database import init_db_pool, close_db_pool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting {settings.SERVICE_NAME}...")
    await init_db_pool()
    yield
    # Shutdown
    logger.info(f"Shutting down {settings.SERVICE_NAME}...")
    await close_db_pool()


# Create FastAPI app
app = FastAPI(
    title="IDINO Career - Portfolio Service",
    description="Student portfolio management service for GitHub, Notion, blogs, projects, and other artifacts",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(portfolio_router)


@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "GET /portfolio/student/{student_id}",
            "GET /portfolio/{portfolio_id}",
            "POST /portfolio",
            "PUT /portfolio/{portfolio_id}",
            "DELETE /portfolio/{portfolio_id}",
            "PUT /portfolio/{portfolio_id}/primary",
            "GET /portfolio/student/{student_id}/summary",
            "GET /portfolio/types",
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": settings.SERVICE_NAME}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=True
    )
