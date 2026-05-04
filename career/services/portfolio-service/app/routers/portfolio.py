"""Portfolio Router - API Endpoints"""
from typing import List
from fastapi import APIRouter, HTTPException, status

from ..services.portfolio_service import PortfolioService
from ..schemas.portfolio import (
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioResponse,
    PortfolioListResponse,
    PortfolioSummaryResponse,
    PortfolioTypesResponse,
)

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

# Service instance
portfolio_service = PortfolioService()


@router.get("/types", response_model=PortfolioTypesResponse)
async def get_portfolio_types():
    """
    Get list of available portfolio types.

    Returns all supported artifact types with display names and icons.
    """
    return portfolio_service.get_portfolio_types()


@router.get("/student/{student_id}", response_model=PortfolioListResponse)
async def get_student_portfolios(student_id: str):
    """
    Get all portfolio items for a student.

    - **student_id**: Student ID
    """
    try:
        return await portfolio_service.get_student_portfolios(student_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/student/{student_id}/summary", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary(student_id: str):
    """
    Get portfolio summary statistics for a student.

    - **student_id**: Student ID

    Returns aggregated statistics about the student's portfolio items.
    """
    try:
        return await portfolio_service.get_portfolio_summary(student_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(portfolio_id: str):
    """
    Get a specific portfolio item by ID.

    - **portfolio_id**: Portfolio item UUID
    """
    try:
        result = await portfolio_service.get_portfolio_by_id(portfolio_id)
        if not result:
            raise HTTPException(status_code=404, detail="Portfolio item not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(data: PortfolioCreate):
    """
    Create a new portfolio item.

    - **student_id**: Student ID
    - **artifact_type**: Type of artifact (github, notion, blog, website, project, paper, video, document, other)
    - **title**: Title of the portfolio item
    - **url**: URL of the portfolio item
    - **description**: Optional description
    - **is_primary**: Mark as primary portfolio item (optional)
    """
    try:
        # Verify student exists
        student_exists = await portfolio_service.verify_student_exists(data.student_id)
        if not student_exists:
            raise HTTPException(
                status_code=404,
                detail=f"Student {data.student_id} not found"
            )

        return await portfolio_service.create_portfolio(data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(portfolio_id: str, data: PortfolioUpdate):
    """
    Update a portfolio item.

    - **portfolio_id**: Portfolio item UUID
    - All fields are optional; only provided fields will be updated
    """
    try:
        result = await portfolio_service.update_portfolio(portfolio_id, data)
        if not result:
            raise HTTPException(status_code=404, detail="Portfolio item not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(portfolio_id: str):
    """
    Delete a portfolio item.

    - **portfolio_id**: Portfolio item UUID
    """
    try:
        deleted = await portfolio_service.delete_portfolio(portfolio_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Portfolio item not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{portfolio_id}/primary", response_model=PortfolioResponse)
async def set_primary_portfolio(portfolio_id: str):
    """
    Set a portfolio item as primary.

    This will unset any existing primary item for the student.

    - **portfolio_id**: Portfolio item UUID
    """
    try:
        result = await portfolio_service.set_primary(portfolio_id)
        if not result:
            raise HTTPException(status_code=404, detail="Portfolio item not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
