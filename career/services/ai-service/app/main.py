import sys
from pathlib import Path

# Add project root to path for shared imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import json

from .routers import ai_router, eval_router
from .config import get_settings
from .database import init_db, close_db

# Setup logging
from shared.common.logging import setup_logging, get_logger

setup_logging("ai-service", json_format=False)
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
    # Startup
    settings = get_settings()
    logger.info(f"AI Service starting with model: {settings.OPENAI_MODEL}")
    try:
        await init_db()
        logger.info("Database connection initialized")
    except Exception as e:
        logger.warning(f"Database initialization skipped (optional): {e}")
    yield
    # Shutdown
    try:
        await close_db()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Database cleanup error: {e}")
    logger.info("AI Service shutting down")


app = FastAPI(
    title="AI Service",
    description="AI 기반 커리어 추천 서비스 - LLM을 활용한 맞춤형 액션 추천 및 분석",
    version="1.0.0",
    lifespan=lifespan,
    default_response_class=UTF8JSONResponse,  # Use UTF-8 JSON response by default
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


# 라우터 등록
app.include_router(ai_router)
app.include_router(eval_router)


@app.get("/")
async def root():
    return {
        "service": "ai-service",
        "version": "1.0.0",
        "description": "AI 기반 커리어 추천 서비스",
        "endpoints": {
            "actions": "/ai/actions/{student_id}",
            "analyze": "/ai/analyze",
            "chat": "/ai/chat",
            "heatstrip": "/ai/heatstrip/{student_id}",
            "sprint": "/ai/sprint/{student_id}",
            "recommendations_tools": "/ai/recommendations/tools",
            "recommendations_rag": "/ai/recommendations/rag",
            "health": "/ai/health",
            "eval_feedback": "/eval/feedback",
            "eval_metrics": "/eval/metrics",
            "eval_cases": "/eval/cases",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-service"}
