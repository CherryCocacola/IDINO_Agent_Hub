import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..config import get_settings
from .llm_service import LLMService


class RecommendationService:
    def __init__(self):
        self.settings = get_settings()
        self.llm_service = LLMService()
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def get_student_data(self, student_id: str) -> Dict[str, Any]:
        """Fetch student data from student-service."""
        try:
            response = await self.http_client.get(
                f"{self.settings.STUDENT_SERVICE_URL}/students/{student_id}"
            )
            if response.status_code == 200:
                data = response.json()
                # Map field names to AI service format
                return {
                    "student_id": data.get("student_id"),
                    "name": data.get("student_nm", "학생"),
                    "department_id": data.get("department_cd"),
                    "department_name": data.get("department_cd", "미정"),  # Will be enhanced with lookup
                    "grade": data.get("current_grade", 1),
                    "gpa": data.get("gpa"),  # May be None
                    "career_goal": data.get("career_goal", "소프트웨어 개발자"),
                }
        except Exception as e:
            print(f"Failed to fetch student data: {e}")

        # Return minimal data without mock values for 2023-2025 students
        return {
            "student_id": student_id,
            "name": None,
            "department_id": None,
            "department_name": None,
            "grade": None,
            "gpa": None,
            "career_goal": None,
        }

    async def get_competency_data(self, student_id: str) -> List[Dict[str, Any]]:
        """Fetch competency data from competency-service."""
        try:
            response = await self.http_client.get(
                f"{self.settings.COMPETENCY_SERVICE_URL}/competency/{student_id}/scores"
            )
            if response.status_code == 200:
                data = response.json()
                # Map field names to AI service format
                return [
                    {
                        "name": item.get("competency_nm", item.get("competency_cd")),
                        "score": item.get("current_score", 0),
                        "status": self._get_status_korean(item.get("status", "developing")),
                        "target": item.get("target_score", 85),
                        "gap": item.get("gap_score", 0),
                    }
                    for item in data
                ]
        except Exception as e:
            print(f"Failed to fetch competency data: {e}")

        # Return empty list if service unavailable (no mock data)
        return []

    def _get_status_korean(self, status: str) -> str:
        """Convert English status to Korean."""
        status_map = {
            "proficient": "우수",
            "developing": "양호",
            "beginner": "보통",
            "improve": "개선필요",
        }
        return status_map.get(status.lower(), "보통") if status else "보통"

    async def get_action_recommendations(self, student_id: str) -> Dict[str, Any]:
        """Generate personalized action recommendations."""
        # Fetch student and competency data
        student_data = await self.get_student_data(student_id)
        competency_scores = await self.get_competency_data(student_id)

        career_goal = student_data.get("career_goal", "소프트웨어 개발자")

        # Generate AI recommendations
        recommendations = await self.llm_service.generate_action_recommendations(
            student_data=student_data,
            competency_scores=competency_scores,
            career_goal=career_goal,
        )

        return {
            "student_id": student_id,
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat(),
            "model_used": self.settings.OPENAI_MODEL,
        }

    async def analyze_competencies(
        self, student_id: str, competencies: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Analyze student competencies with AI."""
        student_data = await self.get_student_data(student_id)

        if competencies is None:
            competencies = await self.get_competency_data(student_id)

        career_goal = student_data.get("career_goal", "소프트웨어 개발자")

        analysis = await self.llm_service.analyze_competencies(
            competency_scores=competencies,
            career_goal=career_goal,
        )

        return {
            "student_id": student_id,
            **analysis,
            "generated_at": datetime.now().isoformat(),
        }

    async def chat(
        self,
        student_id: str,
        message: str,
        history: List[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Handle chatbot conversation with context."""
        if history is None:
            history = []

        # Get student context
        student_data = await self.get_student_data(student_id)
        competency_scores = await self.get_competency_data(student_id)

        context = {
            "student": student_data,
            "competencies": competency_scores,
        }

        result = await self.llm_service.chat(
            message=message,
            history=history,
            context=context,
        )

        return {
            "student_id": student_id,
            "response": result.get("response", ""),
            "suggestions": result.get("suggestions", []),
            "generated_at": datetime.now().isoformat(),
        }

    async def get_heatstrip_data(self, student_id: str) -> Dict[str, Any]:
        """Generate heatstrip visualization data from actual competency scores."""
        competencies = await self.get_competency_data(student_id)

        heatstrip_data = []
        colors = ["#5b6dff", "#00b7a8", "#ff8a5c", "#f6c343", "#9b59b6", "#e74c3c"]

        for i, comp in enumerate(competencies[:6]):
            current_score = comp.get("score", 0)
            target_score = comp.get("target", 85)
            gap = comp.get("gap", 0)

            # Determine trend based on gap: negative gap means below target
            if gap >= 5:
                trend = "above"
            elif gap >= 0:
                trend = "on_track"
            elif gap >= -10:
                trend = "developing"
            else:
                trend = "needs_improvement"

            heatstrip_data.append({
                "name": comp.get("name", f"역량 {i+1}"),
                "current_score": current_score,
                "target_score": target_score,
                "gap": gap,
                "status": comp.get("status", "보통"),
                "color": colors[i] if i < len(colors) else "#888888",
                "trend": trend,
            })

        return {
            "student_id": student_id,
            "competencies": heatstrip_data,
            "total_competencies": len(competencies),
            "generated_at": datetime.now().isoformat(),
        }

    async def get_semester_sprint(self, student_id: str) -> Dict[str, Any]:
        """Generate semester sprint goals and progress from database."""
        student_data = await self.get_student_data(student_id)
        competency_scores = await self.get_competency_data(student_id)

        # Fetch goals from database
        current_goals = await self._fetch_student_goals(student_id)

        # Return empty goals if no data found (no mock data)
        # current_goals stays empty [] if no database records

        # Get AI suggestions
        result = await self.llm_service.generate_semester_goals(
            student_data=student_data,
            competency_scores=competency_scores,
            current_goals=current_goals,
        )

        completed_count = sum(1 for g in current_goals if g["completed"])
        total_count = len(current_goals)

        # Get current semester
        now = datetime.now()
        semester = f"{now.year}-{'1' if now.month <= 6 else '2'}학기"

        return {
            "student_id": student_id,
            "semester": semester,
            "goals": current_goals,
            "completion_rate": completed_count / total_count if total_count > 0 else 0,
            "ai_suggestions": result.get("ai_suggestions", []),
            "generated_at": datetime.now().isoformat(),
        }

    async def _fetch_student_goals(self, student_id: str) -> List[Dict[str, Any]]:
        """Fetch student goals from tb_coaching_goal table."""
        try:
            import asyncpg
            conn = await asyncpg.connect(
                host=self.settings.DB_HOST,
                port=self.settings.DB_PORT,
                database=self.settings.DB_NAME,
                user=self.settings.DB_USER,
                password=self.settings.DB_PASSWORD,
            )
            try:
                rows = await conn.fetch(
                    """
                    SELECT title, description, priority, status, progress_percentage
                    FROM idino_career.tb_coaching_goal
                    WHERE std_id = $1
                    ORDER BY
                        CASE priority
                            WHEN 'high' THEN 1
                            WHEN 'medium' THEN 2
                            ELSE 3
                        END,
                        created_at DESC
                    LIMIT 5
                    """,
                    student_id
                )
                goals = []
                for row in rows:
                    goals.append({
                        "label": row["title"],
                        "description": row["description"] or "",
                        "completed": row["status"] == "completed" or row["progress_percentage"] == 100,
                        "priority": row["priority"] or "medium",
                        "progress": row["progress_percentage"] or 0,
                    })
                return goals
            finally:
                await conn.close()
        except Exception as e:
            print(f"Failed to fetch goals from database: {e}")
            return []

    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()
