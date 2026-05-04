"""
Competency Service Schemas.
"""
from .competency import (
    CompetencyResponse,
    StudentCompetencyResponse,
    StudentCompetencyWithNameResponse,
    CompetencyReportResponse,
    CompetencyDefinitionResponse,  # Legacy alias
)

__all__ = [
    "CompetencyResponse",
    "StudentCompetencyResponse",
    "StudentCompetencyWithNameResponse",
    "CompetencyReportResponse",
    "CompetencyDefinitionResponse",
]
