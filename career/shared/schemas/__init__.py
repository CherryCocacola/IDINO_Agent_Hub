"""
Shared Pydantic schemas for events and common data structures.
"""
from .events import (
    BaseEvent,
    StudentCreatedEvent,
    StudentUpdatedEvent,
    CourseCompletedEvent,
    CompetencyCalculatedEvent,
    RoadmapGeneratedEvent,
)

__all__ = [
    "BaseEvent",
    "StudentCreatedEvent",
    "StudentUpdatedEvent",
    "CourseCompletedEvent",
    "CompetencyCalculatedEvent",
    "RoadmapGeneratedEvent",
]
