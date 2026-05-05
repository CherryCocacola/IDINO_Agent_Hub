"""
Student Service Models.
Updated to match actual database schema.
"""
from .student import (
    College,
    Department,
    Student,
    Term,
    Course,
    CourseOffering,
    Enrollment,
    Grade,
    Program,
    Activity,
    Achievement,
)

__all__ = [
    "College",
    "Department",
    "Student",
    "Term",
    "Course",
    "CourseOffering",
    "Enrollment",
    "Grade",
    "Program",
    "Activity",
    "Achievement",
]
