"""
Tool Executor for OpenAI Tool Calling
Executes tool calls by making HTTP requests to microservices
"""

import logging
from typing import Any, Dict, Optional

import httpx

from ..config import Settings

logger = logging.getLogger(__name__)


class ToolExecutor:
    """
    Executes tool calls by routing to appropriate microservices.

    Supported tools:
    - get_student_profile: Student Service (8002)
    - get_competency_scores: Competency Service (8003)
    - search_alumni_patterns: Alumni Service (8005)
    - check_constraints: Student Service (8002)
    """

    def __init__(self, settings: Optional[Settings] = None):
        from ..config import get_settings
        self.settings = settings or get_settings()
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool call and return the result.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments as dictionary

        Returns:
            Tool execution result as dictionary
        """
        handlers = {
            "get_student_profile": self._get_student_profile,
            "get_competency_scores": self._get_competency_scores,
            "search_alumni_patterns": self._search_alumni_patterns,
            "check_constraints": self._check_constraints,
        }

        handler = handlers.get(tool_name)
        if not handler:
            logger.error(f"Unknown tool: {tool_name}")
            return {"error": f"Unknown tool: {tool_name}"}

        try:
            logger.info(f"Executing tool: {tool_name} with args: {arguments}")
            result = await handler(**arguments)
            logger.info(f"Tool {tool_name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return {"error": str(e)}

    async def _get_student_profile(self, student_id: str) -> Dict[str, Any]:
        """
        Get student profile from Student Service (8002)

        Endpoint: GET /students/{student_id}
        """
        url = f"{self.settings.STUDENT_SERVICE_URL}/students/{student_id}"

        try:
            response = await self.http_client.get(url)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return {"error": f"Student {student_id} not found"}
            else:
                return {"error": f"Failed to fetch student profile: {response.status_code}"}
        except httpx.RequestError as e:
            logger.error(f"Request to Student Service failed: {e}")
            return {"error": f"Service unavailable: {str(e)}"}

    async def _get_competency_scores(self, student_id: str) -> Dict[str, Any]:
        """
        Get competency scores from Competency Service (8003)

        Endpoint: GET /competency/{student_id}/scores
        """
        url = f"{self.settings.COMPETENCY_SERVICE_URL}/competency/{student_id}/scores"

        try:
            response = await self.http_client.get(url)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return {"error": f"Competency scores for {student_id} not found"}
            else:
                return {"error": f"Failed to fetch competency scores: {response.status_code}"}
        except httpx.RequestError as e:
            logger.error(f"Request to Competency Service failed: {e}")
            return {"error": f"Service unavailable: {str(e)}"}

    async def _search_alumni_patterns(
        self,
        target_role: str,
        department_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search alumni patterns from Alumni Service (8005)

        Endpoint: GET /alumni/patterns?target_role=...&department_id=...
        """
        url = f"{self.settings.ALUMNI_SERVICE_URL}/alumni/patterns"
        params = {"target_role": target_role}
        if department_id:
            params["department_id"] = department_id

        try:
            response = await self.http_client.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                # Return empty patterns if not found
                logger.warning(f"Alumni patterns search returned {response.status_code}")
                return {"patterns": [], "message": "No matching alumni patterns found"}
        except httpx.RequestError as e:
            logger.error(f"Request to Alumni Service failed: {e}")
            return {"patterns": [], "error": f"Service unavailable: {str(e)}"}

    async def _check_constraints(
        self,
        student_id: str,
        course_ids: list
    ) -> Dict[str, Any]:
        """
        Check academic constraints for courses.

        Uses Student Service to get enrollment history and validate prerequisites.
        This is a simplified implementation - can be extended with prerequisite table.

        Endpoint: GET /students/{student_id}/enrollments
        """
        # Get student's enrollment history
        url = f"{self.settings.STUDENT_SERVICE_URL}/students/{student_id}/enrollments"

        try:
            response = await self.http_client.get(url)
            if response.status_code == 200:
                enrollments = response.json()
                # Extract completed course codes
                completed_courses = [
                    e.get("course_cd")
                    for e in enrollments
                    if e.get("letter_grade") is not None
                ]
            else:
                completed_courses = []
        except httpx.RequestError as e:
            logger.error(f"Request to Student Service failed: {e}")
            completed_courses = []

        # Build constraints response
        # TODO: Extend with tb_prerequisite table lookup for actual prerequisite checking
        constraints = []
        for course_id in course_ids:
            constraints.append({
                "course_id": course_id,
                "can_enroll": True,
                "prerequisites_met": True,
                "reason": "No prerequisite constraints found",
                "completed_courses": completed_courses
            })

        return {
            "student_id": student_id,
            "constraints": constraints,
            "total_completed_courses": len(completed_courses)
        }

    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()
