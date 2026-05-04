"""
Student Service Routers.
"""
from .students import router as students_router
from .curriculum import router as curriculum_router

__all__ = ["students_router", "curriculum_router"]
