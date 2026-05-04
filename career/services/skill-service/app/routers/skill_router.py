from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from ..schemas import (
    SkillResponse,
    StudentSkillResponse,
    StudentSkillUpdate,
    RoleSkillMapResponse,
    SkillGraphResponse,
    GapAnalysisRequest,
    GapAnalysisResponse,
    SkillRelationResponse,
    RoleRequirementResponse,
)
from ..services import skill_service

router = APIRouter(prefix="/skills", tags=["Skills"])


# ============================================
# IMPORTANT: Route Order Matters!
# Static routes (/graph, /roles, /student, etc.) MUST come BEFORE
# dynamic routes (/{skill_cd}) to prevent path parameter matching
# ============================================


# ============================================
# Skill Graph (MUST be before /{skill_cd})
# ============================================

@router.get("/graph", response_model=SkillGraphResponse)
async def get_skill_graph(
    student_id: Optional[str] = Query(None, description="Include student skill levels"),
    role_cd: Optional[str] = Query(None, description="Filter by role requirements")
):
    """
    Get skill graph for visualization

    - **student_id**: Optional. Include student's current skill levels
    - **role_cd**: Optional. Filter to skills required for this role
    """
    return await skill_service.get_skill_graph(student_id, role_cd)


@router.get("/graph/student/{student_id}", response_model=SkillGraphResponse)
async def get_student_skill_graph(
    student_id: str,
    role_cd: Optional[str] = Query(None, description="Filter by role requirements")
):
    """
    Get skill graph for a specific student

    - **student_id**: Student ID to get skill graph for
    - **role_cd**: Optional. Filter to skills required for this role
    """
    return await skill_service.get_skill_graph(student_id, role_cd)


# ============================================
# Roles (MUST be before /{skill_cd})
# ============================================

@router.get("/roles", response_model=List[dict])
async def get_all_roles():
    """Get all available roles for skill mapping"""
    return await skill_service.get_all_roles()


@router.get("/roles/student/{student_id}", response_model=List[dict])
async def get_roles_for_student(student_id: str):
    """Get roles relevant to student's department"""
    return await skill_service.get_roles_for_student(student_id)


@router.get("/role/{role_cd}", response_model=List[RoleSkillMapResponse])
async def get_role_skills(role_cd: str):
    """Get all skills required for a role"""
    return await skill_service.get_role_skills(role_cd)


@router.get("/role/{role_cd}/requirements", response_model=RoleRequirementResponse)
async def get_role_requirements(role_cd: str):
    """Get complete role requirements with skills"""
    result = await skill_service.get_role_requirements(role_cd)
    if not result:
        raise HTTPException(status_code=404, detail=f"Role {role_cd} not found")
    return result


# ============================================
# Student Skills (MUST be before /{skill_cd})
# ============================================

@router.get("/student/{student_id}", response_model=List[StudentSkillResponse])
async def get_student_skills(student_id: str):
    """Get all skills for a student"""
    return await skill_service.get_student_skills(student_id)


@router.get("/student/{student_id}/graph", response_model=SkillGraphResponse)
async def get_student_graph_alt(
    student_id: str,
    role_cd: Optional[str] = Query(None, description="Filter by role requirements")
):
    """
    Get skill graph for a specific student (for frontend compatibility)
    """
    return await skill_service.get_skill_graph(student_id, role_cd)


@router.get("/student/{student_id}/{skill_cd}", response_model=StudentSkillResponse)
async def get_student_skill(student_id: str, skill_cd: str):
    """Get a specific skill for a student"""
    skill = await skill_service.get_student_skill(student_id, skill_cd)
    if not skill:
        raise HTTPException(
            status_code=404,
            detail=f"Skill {skill_cd} not found for student {student_id}"
        )
    return skill


@router.put("/student/{student_id}/{skill_cd}", response_model=StudentSkillResponse)
async def update_student_skill(
    student_id: str,
    skill_cd: str,
    update: StudentSkillUpdate
):
    """Update or create a student skill record"""
    result = await skill_service.update_student_skill(
        student_id=student_id,
        skill_cd=skill_cd,
        current_level=update.current_level,
        target_level=update.target_level,
        verification_source=update.verification_source
    )
    if not result:
        raise HTTPException(status_code=400, detail="Failed to update skill")
    return result


# ============================================
# Gap Analysis (MUST be before /{skill_cd})
# ============================================

@router.post("/gap-analysis", response_model=GapAnalysisResponse)
async def analyze_skill_gap(request: GapAnalysisRequest):
    """
    Analyze skill gaps between student and target role

    Returns detailed analysis including:
    - Overall gap score (lower is better)
    - Readiness percentage (higher is better)
    - List of skill gaps with priorities
    - Recommended actions for each gap
    - Summary and strengths
    """
    return await skill_service.analyze_skill_gap(
        student_id=request.student_id,
        target_role_cd=request.target_role_cd,
        include_recommendations=request.include_recommendations
    )


@router.get("/gap-analysis/{student_id}/{role_cd}", response_model=GapAnalysisResponse)
async def get_skill_gap_analysis(
    student_id: str,
    role_cd: str,
    include_recommendations: bool = Query(True, description="Include action recommendations")
):
    """Analyze skill gaps between student and target role (GET version)"""
    return await skill_service.analyze_skill_gap(
        student_id=student_id,
        target_role_cd=role_cd,
        include_recommendations=include_recommendations
    )


# ============================================
# Skill Master Data
# ============================================

@router.get("", response_model=List[SkillResponse])
async def get_skills(
    category: Optional[str] = Query(None, description="Filter by category (technical, soft, domain)")
):
    """
    Get all skills

    - **category**: Optional filter by skill category
    """
    return await skill_service.get_all_skills(category)


# ============================================
# Dynamic Skill Routes (MUST be LAST)
# These routes use path parameters that could match static paths
# ============================================

@router.get("/{skill_cd}", response_model=SkillResponse)
async def get_skill(skill_cd: str):
    """Get a specific skill by code"""
    skill = await skill_service.get_skill(skill_cd)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill {skill_cd} not found")
    return skill


@router.get("/{skill_cd}/relations", response_model=List[SkillRelationResponse])
async def get_skill_relations(skill_cd: str):
    """Get all relations for a skill"""
    return await skill_service.get_skill_relations(skill_cd)


@router.get("/{skill_cd}/prerequisites", response_model=List[SkillResponse])
async def get_prerequisite_skills(skill_cd: str):
    """Get prerequisite skills for a skill"""
    return await skill_service.get_prerequisite_skills(skill_cd)


@router.get("/{skill_cd}/next", response_model=List[SkillResponse])
async def get_next_skills(skill_cd: str):
    """Get skills that build on a given skill"""
    return await skill_service.get_next_skills(skill_cd)
