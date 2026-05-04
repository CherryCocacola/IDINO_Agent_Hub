"""Roadmap Service - Main Application"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers.roadmap import router as roadmap_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="IDINO Career - Roadmap Service",
    description="Career roadmap generation and management service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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
app.include_router(roadmap_router)


@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "GET /roadmap/student/{student_id}/grade/{grade_level}",
            "GET /roadmap/student/{student_id}/full",
            "POST /roadmap/generate",
            "GET /roadmap/templates/courses/{grade_level}/{semester}",
            "GET /roadmap/templates/activities/{grade_level}/{semester}",
            "GET /roadmap/milestones/{grade_level}/{semester}",
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
