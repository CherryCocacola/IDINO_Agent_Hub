"""Privacy Service - Data Subject Rights Management (GDPR/PIPA Compliance)"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import create_pool, close_pool
from .routers import privacy_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    await create_pool()
    yield
    # Shutdown
    await close_pool()


app = FastAPI(
    title="Privacy Service",
    description="""
    Data Subject Rights Management API for GDPR/PIPA Compliance.

    ## Features

    ### Data Subject Requests
    - Create and track data subject requests
    - Support for all GDPR rights (Access, Rectification, Erasure, Portability, Restriction, Objection)
    - 30-day processing deadline tracking

    ### Right to Access (Article 15)
    - Retrieve all personal data held about a student
    - Categorized data presentation
    - Processing purposes and data recipients information

    ### Right to Data Portability (Article 20)
    - Export personal data in machine-readable format (JSON/CSV)
    - Secure download link generation

    ### Right to Erasure (Article 17)
    - Process deletion requests
    - Handle legal retention requirements (academic records)
    - Anonymization for retained data

    ### Consent Management
    - Record and manage consent decisions
    - Support multiple consent types
    - Consent withdrawal tracking

    ## Compliance
    - GDPR (EU General Data Protection Regulation)
    - PIPA (Korea Personal Information Protection Act)
    - Higher Education Act retention requirements
    """,
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
app.include_router(privacy_router)


@app.get("/")
async def root():
    """Service information"""
    return {
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "status": "running",
        "compliance": ["GDPR", "PIPA"],
        "processing_deadline_days": settings.REQUEST_PROCESSING_DAYS,
        "data_retention_years": settings.DATA_RETENTION_DAYS // 365,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": settings.SERVICE_NAME}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        reload=True
    )
