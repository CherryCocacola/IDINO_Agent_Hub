"""Roadmap Router - API Endpoints"""
from typing import List
from fastapi import APIRouter, HTTPException, Path, Query

from ..services.roadmap_service import RoadmapService
from ..schemas.roadmap import (
    GradeRoadmapResponse,
    FullRoadmapResponse,
    RoadmapGenerateRequest,
    RoadmapGenerateResponse,
    RoadmapItemCreate,
    RoadmapItemResponse,
)

router = APIRouter(prefix="/roadmap", tags=["roadmap"])

# Service instance
roadmap_service = RoadmapService()


@router.get("/student/{student_id}/grade/{grade_level}", response_model=GradeRoadmapResponse)
async def get_grade_roadmap(
    student_id: str,
    grade_level: int = Path(ge=1, le=4)
):
    """
    Get roadmap for a specific grade level.

    - **student_id**: Student ID
    - **grade_level**: Grade level (1-4)
    """
    try:
        return await roadmap_service.get_grade_roadmap(student_id, grade_level)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/student/{student_id}/full", response_model=FullRoadmapResponse)
async def get_full_roadmap(student_id: str):
    """
    Get complete 4-year roadmap for a student.

    - **student_id**: Student ID
    """
    try:
        roadmaps = await roadmap_service.get_full_roadmap(student_id)

        # Calculate overall completion
        total_completion = sum(r.completion_rate for r in roadmaps)
        overall_completion = total_completion / len(roadmaps) if roadmaps else 0.0

        # Determine current grade/semester based on incomplete items
        current_grade = 1
        current_semester = 1
        for roadmap in roadmaps:
            if roadmap.completion_rate < 100:
                current_grade = roadmap.grade_level
                for semester in roadmap.semesters:
                    has_incomplete = any(
                        item.status in ['planned', 'in_progress']
                        for item in semester.items
                    )
                    if has_incomplete:
                        current_semester = semester.semester
                        break
                break

        return FullRoadmapResponse(
            student_id=student_id,
            roadmaps=roadmaps,
            overall_completion=overall_completion,
            current_grade=current_grade,
            current_semester=current_semester,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", response_model=RoadmapGenerateResponse)
async def generate_ai_roadmap(request: RoadmapGenerateRequest):
    """
    Generate AI-optimized roadmap based on student goals.

    - **student_id**: Student ID
    - **target_role**: Target career role (optional)
    - **career_goal**: Career goal description (optional)
    - **preferences**: Additional preferences (optional)
    - **constraints**: Constraints to consider (optional)
    """
    try:
        return await roadmap_service.generate_ai_roadmap(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/courses/{grade_level}/{semester}")
async def get_course_templates(
    grade_level: int = Path(ge=1, le=4),
    semester: int = Path(ge=1, le=2)
):
    """
    Get course templates for a specific grade and semester.
    Useful for planning and customization.
    """
    service = RoadmapService()
    courses = await service._get_courses_from_db(grade_level, None)
    return {"grade_level": grade_level, "semester": semester, "courses": courses}


@router.get("/templates/activities/{grade_level}/{semester}")
async def get_activity_templates(
    grade_level: int = Path(ge=1, le=4),
    semester: int = Path(ge=1, le=2)
):
    """
    Get activity templates for a specific grade and semester.
    Useful for planning and customization.
    """
    service = RoadmapService()
    programs = await service._get_programs_from_db(grade_level)
    return {"grade_level": grade_level, "semester": semester, "activities": programs}


@router.get("/milestones/{grade_level}/{semester}")
async def get_milestones(
    grade_level: int = Path(ge=1, le=4),
    semester: int = Path(ge=1, le=2)
):
    """
    Get key milestones for a specific grade and semester.
    """
    service = RoadmapService()
    milestones = service._get_key_milestones(grade_level, semester)
    return {"grade_level": grade_level, "semester": semester, "milestones": milestones}


@router.post("/items", response_model=RoadmapItemResponse)
async def create_roadmap_item(item: RoadmapItemCreate):
    """
    Create a new roadmap item for a student.

    - **student_id**: Student ID
    - **item_type**: Type of item (course, activity, certificate, internship, project)
    - **title**: Item title
    - **grade_level**: Grade level (1-4)
    - **semester**: Semester (1-2)
    """
    try:
        return await roadmap_service.create_roadmap_item(item)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
