"""WorkNet Service - Vocational Diagnosis Integration"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import create_pool, close_pool
from .routers import worknet_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup - database connection is optional (retry logic in database.py)
    pool = await create_pool()
    if pool is None:
        import logging
        logging.warning("WorkNet service starting without database - some features unavailable")
    yield
    # Shutdown
    await close_pool()


app = FastAPI(
    title="WorkNet Diagnosis Service",
    description="""
    Integration service for Korea WorkNet vocational diagnosis tests.

    ## Overview

    This service provides integration with WorkNet (고용노동부 워크넷) for comprehensive
    vocational diagnosis and career guidance.

    ## Available Diagnosis Types

    ### 직업적성검사 (Vocational Aptitude Test)
    - Measures 9 aptitude factors
    - Duration: ~50 minutes
    - Identifies suitable occupations based on aptitude profile

    ### 직업흥미검사 (Vocational Interest Test)
    - Based on Holland's RIASEC model
    - Duration: ~30 minutes
    - Matches interests to career fields

    ### 직업가치관검사 (Work Values Test)
    - Assesses work-related values
    - Duration: ~25 minutes
    - Helps prioritize career choices

    ### 성인용 직업성격검사 (Adult Vocational Personality Test)
    - MBTI-based personality assessment
    - Duration: ~40 minutes
    - Matches personality to work environments

    ### 창업적성검사 (Entrepreneurship Aptitude Test)
    - Evaluates entrepreneurial capabilities
    - Duration: ~35 minutes
    - Identifies startup readiness

    ### 진로성숙도검사 (Career Maturity Test)
    - Measures career decision readiness
    - Duration: ~30 minutes
    - Assesses career planning capability

    ## Integration Flow

    1. Create a diagnosis session via POST /worknet/sessions
    2. Redirect user to the returned WorkNet URL
    3. User completes the test on WorkNet
    4. WorkNet sends results via callback
    5. Results are stored and can be retrieved via GET endpoints

    ## Data Retention

    - Test results are retained for 2 years
    - Historical comparison is available
    - Career profile is continuously updated
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
app.include_router(worknet_router)


@app.get("/")
async def root():
    """Service information"""
    return {
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "status": "running",
        "provider": "Korea Employment Information Service (WorkNet)",
        "supported_tests": len(settings.SUPPORTED_DIAGNOSIS_TYPES),
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
