"""
HRD-Net API endpoints.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Query

from ..connectors import HRDConnector
from ..schemas.integration import HRDAlumniResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Create connector instance
connector = HRDConnector()


@router.get("/alumni", response_model=List[HRDAlumniResponse])
async def get_alumni(
    department_id: Optional[str] = None,
    graduation_year: Optional[int] = Query(None, ge=2000, le=2030),
    limit: int = Query(50, ge=1, le=200),
):
    """
    Get alumni employment data from HRD-Net.

    Can be filtered by department and graduation year.
    """
    alumni = await connector.get_alumni(
        department_id=department_id,
        graduation_year=graduation_year,
        limit=limit,
    )

    return alumni


@router.get("/alumni/{alumni_id}", response_model=HRDAlumniResponse)
async def get_alumni_by_id(alumni_id: str):
    """Get specific alumni by ID."""
    alumni = await connector.get_alumni_by_id(alumni_id)

    if not alumni:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alumni {alumni_id} not found"
        )

    return alumni


@router.get("/statistics/{department_id}")
async def get_employment_statistics(
    department_id: str,
    graduation_year: Optional[int] = Query(None, ge=2000, le=2030),
):
    """
    Get employment statistics for a department.

    Returns aggregated employment data including employment rate,
    average salary, and top employers.
    """
    stats = await connector.get_employment_statistics(
        department_id=department_id,
        graduation_year=graduation_year,
    )

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No statistics found for department {department_id}"
        )

    return stats
