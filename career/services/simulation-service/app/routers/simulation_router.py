from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from uuid import UUID

from ..schemas import (
    ScenarioType,
    ScenarioCreate,
    ScenarioResponse,
    ComparisonRequest,
    ComparisonResponse,
    CareerPathSimulation,
    SkillDevelopmentSimulation,
    CourseSelectionSimulation,
    TimelineSimulation,
    ScenarioTypeInfo,
    SuggestedScenario,
    ScenarioGuide,
    VariableGuide,
    MetricExplanation,
)
from ..services import simulation_service

router = APIRouter(prefix="/simulation", tags=["What-if Planner"])


# ============================================
# Static metadata endpoints (MUST be before dynamic routes)
# ============================================

@router.get("/types", response_model=List[ScenarioTypeInfo])
async def get_scenario_types():
    """
    시나리오 유형 목록 조회

    사용 가능한 모든 시뮬레이션 시나리오 유형을 반환합니다.
    """
    return [
        {"value": "course_selection", "label": "과목 선택", "description": "수강 과목 변경 시 학점/역량 영향 분석"},
        {"value": "career_path", "label": "진로 경로", "description": "목표 직무에 대한 준비도 분석"},
        {"value": "skill_development", "label": "스킬 개발", "description": "스킬 레벨업 시 효과 및 소요시간 분석"},
        {"value": "opportunity", "label": "기회 선택", "description": "인턴십/프로젝트/대회 참여 효과 분석"},
        {"value": "timeline", "label": "타임라인", "description": "목표 기한 내 성장 경로 예측"},
    ]


@router.get("/guide/{scenario_type}", response_model=ScenarioGuide)
async def get_scenario_guide(scenario_type: ScenarioType):
    """
    시나리오 유형별 상세 가이드 조회

    각 시나리오 유형에 대한 상세 설명, 사용 방법, 변수 설정 가이드,
    예상 결과 메트릭의 의미 등을 반환합니다.

    프론트엔드에서 사용자에게 시나리오 설정 방법을 안내할 때 사용합니다.

    **반환 정보:**
    - `how_it_works`: 시뮬레이션 작동 방식 설명
    - `steps`: 시뮬레이션 진행 단계
    - `variables`: 설정 가능한 변수와 입력 방법
    - `expected_metrics`: 결과 메트릭의 의미와 해석 방법
    - `tips`: 효과적인 사용 팁
    """
    return simulation_service.get_scenario_guide(scenario_type)


@router.get("/suggestions/{student_id}", response_model=List[SuggestedScenario])
async def get_suggested_scenarios(student_id: str):
    """
    학생 맞춤 추천 시나리오 목록

    학생의 현재 상태와 목표를 기반으로 유용한 시뮬레이션 시나리오를 추천합니다.
    """
    return await simulation_service.get_suggested_scenarios(student_id)


# ============================================
# Static routes MUST come BEFORE dynamic routes
# ============================================

@router.get("/scenarios", response_model=List[ScenarioResponse])
async def get_all_scenarios(
    student_id: Optional[str] = Query(None, description="Filter by student ID"),
    scenario_type: Optional[ScenarioType] = Query(None, description="Filter by scenario type"),
):
    """
    모든 시나리오 목록 조회

    - **student_id**: 학생 ID로 필터링 (선택)
    - **scenario_type**: 시나리오 유형으로 필터링 (선택)
    """
    return await simulation_service.get_all_scenarios(student_id, scenario_type)


@router.post("/scenarios", response_model=ScenarioResponse, status_code=201)
async def create_scenario(data: ScenarioCreate):
    """
    새 시뮬레이션 시나리오 생성

    다양한 가정을 시뮬레이션하고 결과를 예측합니다.
    """
    return await simulation_service.create_scenario(data)


@router.get("/scenarios/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(scenario_id: UUID):
    """시나리오 상세 조회"""
    scenario = await simulation_service.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.get("/scenarios/student/{student_id}", response_model=List[ScenarioResponse])
async def get_student_scenarios(
    student_id: str,
    scenario_type: Optional[ScenarioType] = Query(None),
):
    """학생의 시나리오 목록"""
    return await simulation_service.get_student_scenarios(student_id, scenario_type)


@router.delete("/scenarios/{scenario_id}", status_code=204)
async def delete_scenario(scenario_id: UUID):
    """시나리오 삭제"""
    if not await simulation_service.delete_scenario(scenario_id):
        raise HTTPException(status_code=404, detail="Scenario not found")


@router.post("/compare", response_model=ComparisonResponse)
async def compare_scenarios(request: ComparisonRequest):
    """
    여러 시나리오 비교

    2-5개의 시나리오를 비교하여 최적의 선택을 권장합니다.
    """
    try:
        return await simulation_service.compare_scenarios(request.student_id, request.scenario_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/career-path", response_model=ScenarioResponse)
async def simulate_career_path(request: CareerPathSimulation):
    """진로 경로 시뮬레이션"""
    return await simulation_service.simulate_career_path(request)


@router.post("/skill-development", response_model=ScenarioResponse)
async def simulate_skill_development(request: SkillDevelopmentSimulation):
    """스킬 개발 시뮬레이션"""
    return await simulation_service.simulate_skill_development(request)


@router.post("/course-selection", response_model=ScenarioResponse)
async def simulate_course_selection(request: CourseSelectionSimulation):
    """
    과목 선택 시뮬레이션

    특정 과목들을 수강했을 때의 학점, 역량 변화를 예측합니다.
    """
    return await simulation_service.simulate_course_selection(request)


@router.post("/timeline", response_model=ScenarioResponse)
async def simulate_timeline(request: TimelineSimulation):
    """
    타임라인 시뮬레이션

    목표 날짜까지의 성장 경로와 필요한 마일스톤을 예측합니다.
    """
    return await simulation_service.simulate_timeline(request)


@router.post("/scenarios/{scenario_id}/save", response_model=ScenarioResponse)
async def save_scenario(scenario_id: UUID):
    """
    시나리오 저장 (즐겨찾기)

    시나리오를 즐겨찾기로 저장하여 나중에 쉽게 접근할 수 있습니다.
    """
    scenario = await simulation_service.save_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario
