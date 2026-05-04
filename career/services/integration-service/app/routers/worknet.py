"""
Worknet API endpoints.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Query

from ..connectors import WorknetConnector
from ..schemas.integration import (
    WorknetJobResponse,
    WorknetSearchRequest,
    WorknetSearchResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Create connector instance
connector = WorknetConnector()


@router.get("/jobs/{job_code}", response_model=WorknetJobResponse)
async def get_job(job_code: str):
    """
    Get job information from Worknet.

    Returns detailed job information including requirements,
    salary data, and related information.
    """
    job = await connector.get_job(job_code)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_code} not found"
        )

    return job


@router.get("/jobs", response_model=List[WorknetJobResponse])
async def list_jobs(
    category: Optional[str] = Query(None, description="Job category filter"),
    department: Optional[str] = Query(None, description="Department name for category inference"),
):
    """
    Get available jobs with optional filtering.

    - If department is provided, jobs matching the department's category are returned
    - If category is provided, jobs matching the category are returned
    - If neither is provided, all jobs are returned
    """
    if department:
        return await connector.get_jobs_by_department(department)
    elif category:
        return await connector.get_jobs_by_category(category)
    return await connector.get_all_jobs()


@router.post("/search", response_model=WorknetSearchResponse)
async def search_jobs(request: WorknetSearchRequest):
    """
    Search for jobs in Worknet.

    Supports filtering by category and education level.
    """
    results = await connector.search_jobs(
        query=request.query,
        category=request.category,
        education_level=request.education_level,
        limit=request.limit,
    )

    return WorknetSearchResponse(
        query=request.query,
        total_count=len(results),
        results=results,
    )


@router.get("/search", response_model=WorknetSearchResponse)
async def search_jobs_get(
    query: str,
    category: Optional[str] = None,
    education_level: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
):
    """
    Search for jobs in Worknet (GET method).

    Alternative to POST search for simple queries.
    """
    results = await connector.search_jobs(
        query=query,
        category=category,
        education_level=education_level,
        limit=limit,
    )

    return WorknetSearchResponse(
        query=query,
        total_count=len(results),
        results=results,
    )
