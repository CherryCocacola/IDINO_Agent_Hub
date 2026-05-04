from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas import (
    ActionRecommendationResponse,
    CompetencyAnalysisRequest,
    CompetencyAnalysisResponse,
    ChatRequest,
    ChatResponse,
    HeatStripResponse,
    SemesterSprintResponse,
)
from ..services import RecommendationService
from ..services.llm_service import LLMService
from ..database import get_db

router = APIRouter(prefix="/ai", tags=["AI"])


# ==========================================
# Phase 2: New Request/Response Models
# ==========================================

class ToolsRecommendationRequest(BaseModel):
    """Request for Tool Calling based recommendations."""
    student_id: str = Field(..., description="Student ID")
    task: str = Field(
        default="맞춤형 취업 역량 개발 추천을 생성해주세요",
        description="Task description for the AI"
    )
    use_rag: bool = Field(default=False, description="Whether to use RAG")
    max_tool_calls: int = Field(default=5, ge=1, le=10, description="Max tool calls")


class RAGRecommendationRequest(BaseModel):
    """Request for RAG + Tool Calling based recommendations."""
    student_id: str = Field(..., description="Student ID")
    task: str = Field(
        default="맞춤형 취업 역량 개발 추천을 생성해주세요",
        description="Task description for the AI"
    )
    use_rag: bool = Field(default=True, description="Whether to use RAG")
    max_tool_calls: int = Field(default=5, ge=1, le=10, description="Max tool calls")


def get_recommendation_service() -> RecommendationService:
    return RecommendationService()


@router.get("/actions/{student_id}", response_model=ActionRecommendationResponse)
async def get_action_recommendations(
    student_id: str,
    service: RecommendationService = Depends(get_recommendation_service),
):
    """
    AI 기반 액션 추천을 생성합니다.

    학생의 역량 점수, 이수 현황, 목표 직업을 분석하여
    가장 효과적인 4개의 액션을 추천합니다.
    """
    try:
        result = await service.get_action_recommendations(student_id)
        return ActionRecommendationResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()


@router.post("/analyze", response_model=CompetencyAnalysisResponse)
async def analyze_competencies(
    request: CompetencyAnalysisRequest,
    service: RecommendationService = Depends(get_recommendation_service),
):
    """
    역량 분석을 수행합니다.

    학생의 4대 핵심역량을 분석하고 강점, 약점, 개선 제안을 제공합니다.
    """
    try:
        competencies = [c.model_dump() for c in request.competencies] if request.competencies else None
        result = await service.analyze_competencies(
            student_id=request.student_id,
            competencies=competencies,
        )
        return CompetencyAnalysisResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    service: RecommendationService = Depends(get_recommendation_service),
):
    """
    AI 챗봇과 대화합니다.

    학생의 컨텍스트를 이해하고 커리어 관련 질문에 답변합니다.
    """
    try:
        history = [msg.model_dump() for msg in request.history] if request.history else []
        result = await service.chat(
            student_id=request.student_id,
            message=request.message,
            history=history,
        )
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()


@router.get("/heatstrip/{student_id}", response_model=HeatStripResponse)
async def get_heatstrip_data(
    student_id: str,
    service: RecommendationService = Depends(get_recommendation_service),
):
    """
    역량 변화 히트맵 데이터를 생성합니다.

    12개월간의 역량 변화 추이를 시각화할 수 있는 데이터를 반환합니다.
    """
    try:
        result = await service.get_heatstrip_data(student_id)
        return HeatStripResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()


@router.get("/sprint/{student_id}", response_model=SemesterSprintResponse)
async def get_semester_sprint(
    student_id: str,
    service: RecommendationService = Depends(get_recommendation_service),
):
    """
    학기 스프린트 목표와 진행 상황을 조회합니다.

    현재 학기 목표와 AI 추천 조언을 제공합니다.
    """
    try:
        result = await service.get_semester_sprint(student_id)
        return SemesterSprintResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()


@router.get("/health")
async def health_check():
    """서비스 상태 확인"""
    return {"status": "healthy", "service": "ai-service"}


# ==========================================
# Phase 2-1: Tool Calling Endpoint
# ==========================================

@router.post("/recommendations/tools")
async def get_recommendations_with_tools(
    request: ToolsRecommendationRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Tool Calling 기반 AI 추천을 생성합니다.

    OpenAI Function Calling을 사용하여 학생 데이터를 조회하고
    맞춤형 추천을 생성합니다.

    Available Tools:
    - get_student_profile: 학생 프로필 조회
    - get_competency_scores: 역량 점수 조회
    - search_alumni_patterns: 동문 성공 패턴 검색
    - check_constraints: 제약조건 확인
    """
    try:
        llm_service = LLMService()
        result = await llm_service.generate_with_tools(
            student_id=request.student_id,
            task=request.task,
            db=db,
            max_tool_calls=request.max_tool_calls,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Phase 2-3: RAG + Tool Calling Endpoint
# ==========================================

@router.post("/recommendations/rag")
async def get_recommendations_with_rag(
    request: RAGRecommendationRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    RAG + Tool Calling 통합 AI 추천을 생성합니다.

    Evidence 기반 검색(과목, 프로그램, 동문 패턴)과
    Tool Calling을 결합하여 근거 있는 추천을 생성합니다.

    Response includes:
    - result: Structured recommendation output (JSON Schema enforced)
    - metadata: Execution metrics (latency, token usage, etc.)
    - tool_results: Data retrieved via Tool Calling
    - evidence: RAG-retrieved evidence sources
    """
    try:
        llm_service = LLMService()
        result = await llm_service.generate_with_tools_and_rag(
            student_id=request.student_id,
            task=request.task,
            db=db,
            use_rag=request.use_rag,
            max_tool_calls=request.max_tool_calls,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
