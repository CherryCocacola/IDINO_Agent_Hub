"""Portfolio Schemas"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from enum import Enum


class ArtifactType(str, Enum):
    """Portfolio artifact types"""
    GITHUB = "github"
    NOTION = "notion"
    BLOG = "blog"
    WEBSITE = "website"
    PROJECT = "project"
    PAPER = "paper"
    VIDEO = "video"
    DOCUMENT = "document"
    CERTIFICATION = "certification"
    EXPERIENCE = "experience"
    AWARD = "award"
    PRESENTATION = "presentation"
    DESIGN = "design"
    CODE = "code"
    OTHER = "other"


class PortfolioBase(BaseModel):
    """Base portfolio schema"""
    artifact_type: ArtifactType
    title: str = Field(..., min_length=1, max_length=200, description="Portfolio item title")
    url: Optional[str] = Field(None, description="URL of the portfolio item")
    description: Optional[str] = Field(None, max_length=2000, description="Description of the item")
    is_primary: bool = Field(default=False, description="Mark as primary portfolio item")
    tags: Optional[List[str]] = Field(default=None, description="Tags for categorization")
    skills: Optional[List[str]] = Field(default=None, description="Skills demonstrated")


class PortfolioCreate(PortfolioBase):
    """Schema for creating a new portfolio item"""
    student_id: str = Field(..., description="Student ID")


class PortfolioUpdate(BaseModel):
    """Schema for updating a portfolio item"""
    artifact_type: Optional[ArtifactType] = None
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    url: Optional[str] = None
    description: Optional[str] = Field(None, max_length=2000)
    is_primary: Optional[bool] = None
    tags: Optional[List[str]] = None
    skills: Optional[List[str]] = None


class PortfolioResponse(PortfolioBase):
    """Response schema for a portfolio item"""
    portfolio_id: str
    student_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PortfolioListResponse(BaseModel):
    """Response schema for a list of portfolio items"""
    student_id: str
    total_count: int
    items: List[PortfolioResponse]
    primary_item: Optional[PortfolioResponse] = None


class PortfolioSummaryResponse(BaseModel):
    """Summary statistics for student's portfolio"""
    student_id: str
    total_items: int
    by_type: Dict[str, int]
    has_primary: bool
    primary_url: Optional[str] = None
    top_skills: List[str]
    last_updated: Optional[datetime] = None


class PortfolioTypeInfo(BaseModel):
    """Information about a portfolio type"""
    type: ArtifactType
    display_name: str
    description: str
    icon: str


class PortfolioTypesResponse(BaseModel):
    """Response for available portfolio types"""
    types: List[PortfolioTypeInfo]
