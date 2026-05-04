from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from uuid import UUID
import json
import logging
import httpx

from ..database import execute_query, execute_one, execute_scalar, execute_command

logger = logging.getLogger(__name__)
from ..schemas import (
    GoalStatus,
    GoalPriority,
    CheckinMood,
    GoalCreate,
    GoalUpdate,
    GoalResponse,
    PlanItemCreate,
    PlanItemUpdate,
    PlanItemResponse,
    CheckinCreate,
    CheckinResponse,
    RetrospectiveCreate,
    RetrospectiveResponse,
    AICoachResponse,
    GoalProgressSummary,
)
from ..config import get_settings


class CoachingService:
    """AI 코칭 서비스"""

    # ============================================
    # Goal CRUD
    # ============================================

    async def create_goal(self, data: GoalCreate) -> Dict:
        """목표 생성"""
        query = """
            INSERT INTO tb_coaching_goal (
                std_id, title, description, goal_type, priority,
                target_date, target_role_cd, related_skills,
                success_criteria, motivation, status, progress_percentage
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 'active', 0
            )
            RETURNING
                goal_id, std_id as student_id, title, description, goal_type, priority,
                status, progress_percentage, target_date, target_role_cd,
                related_skills, success_criteria, motivation,
                created_at, updated_at, completed_at
        """
        result = await execute_one(
            query,
            data.student_id,
            data.title,
            data.description,
            data.goal_type,
            data.priority.value,
            data.target_date,
            data.target_role_cd,
            data.related_skills,
            data.success_criteria,
            data.motivation,
        )

        # Add computed fields
        result["plan_items_count"] = 0
        result["completed_items_count"] = 0
        result["checkins_count"] = 0
        result["last_checkin_at"] = None

        return result

    async def get_goal(self, goal_id: UUID) -> Optional[Dict]:
        """목표 조회"""
        query = """
            SELECT
                g.goal_id, g.std_id as student_id, g.title, g.description,
                g.goal_type, g.priority, g.status, g.progress_percentage,
                g.target_date, g.target_role_cd, g.related_skills,
                g.success_criteria, g.motivation,
                g.created_at, g.updated_at, g.completed_at,
                COALESCE(p.plan_count, 0) as plan_items_count,
                COALESCE(p.completed_count, 0) as completed_items_count,
                COALESCE(c.checkin_count, 0) as checkins_count,
                c.last_checkin_at
            FROM tb_coaching_goal g
            LEFT JOIN (
                SELECT goal_id,
                       COUNT(*) as plan_count,
                       COUNT(*) FILTER (WHERE is_completed) as completed_count
                FROM tb_coaching_plan
                GROUP BY goal_id
            ) p ON g.goal_id = p.goal_id
            LEFT JOIN (
                SELECT goal_id,
                       COUNT(*) as checkin_count,
                       MAX(created_at) as last_checkin_at
                FROM tb_coaching_checkin
                GROUP BY goal_id
            ) c ON g.goal_id = c.goal_id
            WHERE g.goal_id = $1
        """
        return await execute_one(query, goal_id)

    async def get_student_goals(
        self,
        student_id: str,
        status: Optional[GoalStatus] = None,
        goal_type: Optional[str] = None,
    ) -> List[Dict]:
        """학생 목표 목록"""
        conditions = ["g.std_id = $1"]
        params = [student_id]
        param_idx = 2

        if status:
            conditions.append(f"g.status = ${param_idx}")
            params.append(status.value)
            param_idx += 1

        if goal_type:
            conditions.append(f"g.goal_type = ${param_idx}")
            params.append(goal_type)
            param_idx += 1

        query = f"""
            SELECT
                g.goal_id, g.std_id as student_id, g.title, g.description,
                g.goal_type, g.priority, g.status, g.progress_percentage,
                g.target_date, g.target_role_cd, g.related_skills,
                g.success_criteria, g.motivation,
                g.created_at, g.updated_at, g.completed_at,
                COALESCE(p.plan_count, 0) as plan_items_count,
                COALESCE(p.completed_count, 0) as completed_items_count,
                COALESCE(c.checkin_count, 0) as checkins_count,
                c.last_checkin_at
            FROM tb_coaching_goal g
            LEFT JOIN (
                SELECT goal_id,
                       COUNT(*) as plan_count,
                       COUNT(*) FILTER (WHERE is_completed) as completed_count
                FROM tb_coaching_plan
                GROUP BY goal_id
            ) p ON g.goal_id = p.goal_id
            LEFT JOIN (
                SELECT goal_id,
                       COUNT(*) as checkin_count,
                       MAX(created_at) as last_checkin_at
                FROM tb_coaching_checkin
                GROUP BY goal_id
            ) c ON g.goal_id = c.goal_id
            WHERE {" AND ".join(conditions)}
            ORDER BY
                CASE g.status WHEN 'active' THEN 0 WHEN 'paused' THEN 1 ELSE 2 END,
                CASE g.priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 WHEN 'low' THEN 2 ELSE 1 END,
                g.created_at DESC
        """
        return await execute_query(query, *params)

    async def update_goal(self, goal_id: UUID, data: GoalUpdate) -> Optional[Dict]:
        """목표 수정"""
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_goal(goal_id)

        # Convert enums
        if "priority" in update_data and update_data["priority"]:
            update_data["priority"] = update_data["priority"].value
        if "status" in update_data and update_data["status"]:
            update_data["status"] = update_data["status"].value
            # If completing, set completed_at
            if update_data["status"] == "completed":
                update_data["completed_at"] = datetime.now()

        set_clauses = []
        params = []
        for idx, (key, value) in enumerate(update_data.items(), 1):
            set_clauses.append(f"{key} = ${idx}")
            params.append(value)

        params.append(goal_id)

        query = f"""
            UPDATE tb_coaching_goal
            SET {", ".join(set_clauses)}, updated_at = NOW()
            WHERE goal_id = ${len(params)}
        """
        await execute_command(query, *params)
        return await self.get_goal(goal_id)

    async def delete_goal(self, goal_id: UUID) -> bool:
        """목표 삭제"""
        query = "DELETE FROM tb_coaching_goal WHERE goal_id = $1"
        result = await execute_command(query, goal_id)
        return "DELETE 1" in result

    # ============================================
    # Plan Items CRUD
    # ============================================

    async def create_plan_item(self, data: PlanItemCreate) -> Dict:
        """플랜 항목 생성"""
        # Get next order index
        max_order = await execute_scalar(
            "SELECT COALESCE(MAX(order_index), -1) + 1 FROM tb_coaching_plan WHERE goal_id = $1",
            data.goal_id,
        )

        query = """
            INSERT INTO tb_coaching_plan (
                goal_id, title, description, order_index,
                due_date, estimated_hours, related_skill_cd
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING
                plan_id, goal_id, title, description, order_index,
                due_date, estimated_hours, related_skill_cd,
                is_completed, completed_at, actual_hours, notes,
                created_at, updated_at
        """
        return await execute_one(
            query,
            data.goal_id,
            data.title,
            data.description,
            data.order_index if data.order_index > 0 else max_order,
            data.due_date,
            data.estimated_hours,
            data.related_skill_cd,
        )

    async def get_plan_items(self, goal_id: UUID) -> List[Dict]:
        """플랜 항목 목록"""
        query = """
            SELECT
                plan_id, goal_id, title, description, order_index,
                due_date, estimated_hours, related_skill_cd,
                is_completed, completed_at, actual_hours, notes,
                created_at, updated_at
            FROM tb_coaching_plan
            WHERE goal_id = $1
            ORDER BY order_index, created_at
        """
        return await execute_query(query, goal_id)

    async def update_plan_item(
        self, plan_id: UUID, data: PlanItemUpdate
    ) -> Optional[Dict]:
        """플랜 항목 수정"""
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return None

        # If completing, set completed_at
        if update_data.get("is_completed") and "completed_at" not in update_data:
            update_data["completed_at"] = datetime.now()

        set_clauses = []
        params = []
        for idx, (key, value) in enumerate(update_data.items(), 1):
            set_clauses.append(f"{key} = ${idx}")
            params.append(value)

        params.append(plan_id)

        query = f"""
            UPDATE tb_coaching_plan
            SET {", ".join(set_clauses)}, updated_at = NOW()
            WHERE plan_id = ${len(params)}
            RETURNING
                plan_id, goal_id, title, description, order_index,
                due_date, estimated_hours, related_skill_cd,
                is_completed, completed_at, actual_hours, notes,
                created_at, updated_at
        """
        result = await execute_one(query, *params)

        # Update goal progress
        if result and "is_completed" in update_data:
            await self._update_goal_progress(result["goal_id"])

        return result

    async def _update_goal_progress(self, goal_id: UUID):
        """목표 진행률 업데이트"""
        query = """
            UPDATE tb_coaching_goal
            SET progress_percentage = (
                SELECT COALESCE(
                    (COUNT(*) FILTER (WHERE is_completed)::float / NULLIF(COUNT(*), 0) * 100)::int,
                    0
                )
                FROM tb_coaching_plan
                WHERE goal_id = $1
            ),
            updated_at = NOW()
            WHERE goal_id = $1
        """
        await execute_command(query, goal_id)

    async def delete_plan_item(self, plan_id: UUID) -> bool:
        """플랜 항목 삭제"""
        # Get goal_id first
        goal_id = await execute_scalar(
            "SELECT goal_id FROM tb_coaching_plan WHERE plan_id = $1", plan_id
        )

        result = await execute_command(
            "DELETE FROM tb_coaching_plan WHERE plan_id = $1", plan_id
        )

        if goal_id:
            await self._update_goal_progress(goal_id)

        return "DELETE 1" in result

    # ============================================
    # Check-ins
    # ============================================

    async def create_checkin(self, data: CheckinCreate) -> Dict:
        """체크인 생성"""
        query = """
            INSERT INTO tb_coaching_checkin (
                goal_id, mood, progress_note, blockers, next_steps, reflection
            ) VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING
                checkin_id, goal_id, mood, progress_note, blockers,
                next_steps, reflection, ai_feedback, ai_suggestions, created_at
        """
        result = await execute_one(
            query,
            data.goal_id,
            data.mood.value,
            data.progress_note,
            data.blockers,
            data.next_steps,
            data.reflection,
        )

        # Get goal title
        goal = await self.get_goal(data.goal_id)
        if goal:
            result["goal_title"] = goal["title"]

        # Generate AI feedback (async, could be improved)
        ai_feedback = await self._generate_checkin_feedback(result, goal)
        if ai_feedback:
            await execute_command(
                """
                UPDATE tb_coaching_checkin
                SET ai_feedback = $1, ai_suggestions = $2
                WHERE checkin_id = $3
                """,
                ai_feedback.get("feedback"),
                ai_feedback.get("suggestions"),
                result["checkin_id"],
            )
            result["ai_feedback"] = ai_feedback.get("feedback")
            result["ai_suggestions"] = ai_feedback.get("suggestions")

        return result

    async def _generate_checkin_feedback(
        self, checkin: Dict, goal: Optional[Dict]
    ) -> Optional[Dict]:
        """AI 체크인 피드백 생성"""
        # Simple rule-based feedback for now (can be replaced with LLM)
        feedback_parts = []
        suggestions = []

        mood = checkin.get("mood")
        blockers = checkin.get("blockers")
        progress = goal.get("progress_percentage", 0) if goal else 0

        if mood in ["great", "good"]:
            feedback_parts.append("좋은 진행 상황이네요! 이 모멘텀을 유지하세요.")
        elif mood == "neutral":
            feedback_parts.append("꾸준히 진행하고 있군요. 작은 성취도 인정해주세요.")
        elif mood == "struggling":
            feedback_parts.append("어려움을 겪고 있군요. 잠시 휴식을 취하거나 목표를 작게 나눠보세요.")
            suggestions.append("목표를 더 작은 단위로 분해해보세요")
        elif mood == "blocked":
            feedback_parts.append("막힌 상황이군요. 도움을 요청하거나 다른 접근법을 시도해보세요.")
            suggestions.append("멘토나 동료에게 조언을 구해보세요")

        if blockers:
            suggestions.append("블로커 해결을 위한 구체적인 액션을 정해보세요")

        if progress > 75:
            feedback_parts.append(f"이미 {progress}% 진행했습니다. 거의 다 왔어요!")
        elif progress > 50:
            feedback_parts.append(f"절반 이상({progress}%) 왔네요! 끝까지 화이팅!")

        return {
            "feedback": " ".join(feedback_parts) if feedback_parts else None,
            "suggestions": suggestions if suggestions else None,
        }

    async def get_checkins(
        self, goal_id: UUID, limit: int = 10
    ) -> List[Dict]:
        """체크인 목록"""
        query = """
            SELECT
                c.checkin_id, c.goal_id, c.mood, c.progress_note, c.blockers,
                c.next_steps, c.reflection, c.ai_feedback, c.ai_suggestions,
                c.created_at, g.title as goal_title
            FROM tb_coaching_checkin c
            JOIN tb_coaching_goal g ON c.goal_id = g.goal_id
            WHERE c.goal_id = $1
            ORDER BY c.created_at DESC
            LIMIT $2
        """
        return await execute_query(query, goal_id, limit)

    async def get_student_recent_checkins(
        self, student_id: str, days: int = 7
    ) -> List[Dict]:
        """학생 최근 체크인"""
        query = """
            SELECT
                c.checkin_id, c.goal_id, c.mood, c.progress_note, c.blockers,
                c.next_steps, c.reflection, c.ai_feedback, c.ai_suggestions,
                c.created_at, g.title as goal_title
            FROM tb_coaching_checkin c
            JOIN tb_coaching_goal g ON c.goal_id = g.goal_id
            WHERE g.std_id = $1 AND c.created_at >= NOW() - INTERVAL '%s days'
            ORDER BY c.created_at DESC
        """ % days
        return await execute_query(query, student_id)

    # ============================================
    # Retrospectives
    # ============================================

    async def create_retrospective(self, data: RetrospectiveCreate) -> Dict:
        """회고 생성"""
        query = """
            INSERT INTO tb_coaching_retrospective (
                goal_id, what_went_well, what_could_improve,
                lessons_learned, next_goals, satisfaction_rating
            ) VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING
                retrospective_id, goal_id, what_went_well, what_could_improve,
                lessons_learned, next_goals, satisfaction_rating,
                ai_analysis, ai_recommendations, created_at
        """
        result = await execute_one(
            query,
            data.goal_id,
            data.what_went_well,
            data.what_could_improve,
            data.lessons_learned,
            data.next_goals,
            data.satisfaction_rating,
        )

        # Get goal title
        goal = await self.get_goal(data.goal_id)
        if goal:
            result["goal_title"] = goal["title"]

        return result

    async def get_retrospective(self, goal_id: UUID) -> Optional[Dict]:
        """회고 조회"""
        query = """
            SELECT
                r.retrospective_id, r.goal_id, r.what_went_well, r.what_could_improve,
                r.lessons_learned, r.next_goals, r.satisfaction_rating,
                r.ai_analysis, r.ai_recommendations, r.created_at,
                g.title as goal_title
            FROM tb_coaching_retrospective r
            JOIN tb_coaching_goal g ON r.goal_id = g.goal_id
            WHERE r.goal_id = $1
            ORDER BY r.created_at DESC
            LIMIT 1
        """
        return await execute_one(query, goal_id)

    # ============================================
    # Student Profile Lookup
    # ============================================

    async def _get_student_profile(self, student_id: str) -> Optional[Dict[str, Any]]:
        """학생 프로필 조회 (student-service 호출)"""
        try:
            settings = get_settings()
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{settings.STUDENT_SERVICE_URL}/students/{student_id}"
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.warning(f"Failed to fetch student profile: {e}")
        return None

    def _generate_no_goal_advice(self, profile: Optional[Dict[str, Any]]) -> tuple[str, list, list]:
        """목표 미설정 시 학생 프로필 기반 맞춤 조언 생성"""
        if not profile:
            return (
                "아직 설정된 목표가 없네요. 먼저 커리어 목표를 설정해보시는 건 어떨까요?",
                ["단기 목표와 장기 목표를 구분해서 설정하세요", "SMART 기준으로 목표를 구체화하세요"],
                ["첫 번째 목표 설정하기"],
            )

        dept_nm = ""
        if profile.get("department"):
            dept_nm = profile["department"].get("department_nm", "")
        career_goal = profile.get("career_goal", "")
        grade = profile.get("current_grade", 1)

        parts = []
        suggestions = []
        actions = ["첫 번째 목표 설정하기"]

        if dept_nm and career_goal:
            parts.append(
                f"{dept_nm} 재학 중이시고, '{career_goal}'에 관심이 있으시군요. "
                f"이 목표를 구체적으로 설정하면 맞춤형 코칭을 받을 수 있어요."
            )
            suggestions.append(f"'{career_goal}' 관련 단기 목표를 설정해보세요")
            suggestions.append(f"{grade}학년에 맞는 자격증이나 프로젝트 목표를 추가하세요")
        elif dept_nm:
            parts.append(
                f"{dept_nm} 재학 중이시네요. 전공과 관련된 커리어 목표를 설정해보시는 건 어떨까요?"
            )
            suggestions.append("전공 관련 직무를 탐색해보세요")
            suggestions.append("관심 있는 분야의 자격증을 알아보세요")
        else:
            parts.append("아직 설정된 목표가 없네요. 먼저 커리어 목표를 설정해보시는 건 어떨까요?")
            suggestions.append("단기 목표와 장기 목표를 구분해서 설정하세요")

        suggestions.append("SMART 기준으로 목표를 구체화하세요")

        if grade <= 2:
            actions.append("기초 역량 강화 목표 설정하기")
        else:
            actions.append("취업 준비 목표 설정하기")

        return (" ".join(parts), suggestions, actions)

    # ============================================
    # AI Coach
    # ============================================

    async def _call_ai_service(
        self,
        student_id: str,
        message: str,
        coaching_context: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """AI 서비스의 /ai/chat 엔드포인트를 호출하여 LLM 응답을 받습니다."""
        settings = get_settings()
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{settings.AI_SERVICE_URL}/ai/chat",
                    json={
                        "student_id": student_id,
                        "message": message,
                        "context": coaching_context,
                    },
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"AI service returned {response.status_code}")
        except Exception as e:
            logger.warning(f"Failed to call AI service: {e}")
        return None

    def _build_coaching_context(
        self,
        goals: List[Dict],
        recent_checkins: List[Dict],
        goal_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """LLM에 전달할 코칭 컨텍스트를 구성합니다."""
        goals_summary = []
        for g in goals[:5]:
            goal_info = {
                "title": g.get("title"),
                "status": g.get("status"),
                "progress": g.get("progress_percentage", 0),
                "priority": g.get("priority"),
            }
            if g.get("target_date"):
                goal_info["target_date"] = str(g["target_date"])
            goals_summary.append(goal_info)

        checkins_summary = []
        for c in recent_checkins[:5]:
            checkin_info = {
                "goal_title": c.get("goal_title"),
                "mood": c.get("mood"),
                "progress_note": c.get("progress_note", "")[:100],
            }
            if c.get("blockers"):
                checkin_info["blockers"] = c["blockers"][:100]
            checkins_summary.append(checkin_info)

        return {
            "role": "AI 코칭 상담사",
            "goals": goals_summary,
            "recent_checkins": checkins_summary,
            "active_goals_count": len([g for g in goals if g.get("status") == "active"]),
        }

    async def get_ai_coaching(
        self,
        student_id: str,
        goal_id: Optional[UUID] = None,
        query_type: str = "advice",
        context: Optional[str] = None,
    ) -> AICoachResponse:
        """AI 코칭 조언 생성 - LLM 우선, 실패 시 규칙 기반 fallback"""
        # Gather context
        goals = await self.get_student_goals(student_id, status=GoalStatus.ACTIVE)
        recent_checkins = await self.get_student_recent_checkins(student_id, days=7)

        # LLM 호출 시도 (사용자 메시지가 있을 때)
        if context:
            coaching_ctx = self._build_coaching_context(goals, recent_checkins, goal_id)
            ai_result = await self._call_ai_service(student_id, context, coaching_ctx)

            if ai_result and ai_result.get("response"):
                response_text = ai_result["response"]
                ai_suggestions = ai_result.get("suggestions", [])

                return AICoachResponse(
                    message=response_text,
                    suggestions=[],
                    recommended_actions=[],
                    resources=[],
                    follow_up_questions=ai_suggestions if isinstance(ai_suggestions, list) else [],
                    generated_at=datetime.now(),
                )

        # Fallback: 규칙 기반 응답
        message = ""
        suggestions = []
        actions = []
        questions = []

        if query_type == "advice":
            if not goals:
                profile = await self._get_student_profile(student_id)
                message, suggestions, actions = self._generate_no_goal_advice(profile)
            else:
                active_count = len([g for g in goals if g["status"] == "active"])
                message = f"현재 {active_count}개의 활성 목표가 있습니다. "

                # Check for stale goals (no checkin in 3 days)
                stale_goals = [
                    g for g in goals
                    if g["status"] == "active" and (
                        not g.get("last_checkin_at") or
                        (datetime.now() - g["last_checkin_at"]).days > 3
                    )
                ]
                if stale_goals:
                    message += f"{len(stale_goals)}개 목표가 최근 체크인이 없습니다. 진행 상황을 업데이트해보세요."
                    actions.extend([f"'{g['title']}' 체크인하기" for g in stale_goals[:2]])

        elif query_type == "motivation":
            if recent_checkins:
                moods = [c["mood"] for c in recent_checkins]
                if "blocked" in moods or "struggling" in moods:
                    message = "어려움을 겪고 있는 것 같네요. 괜찮아요, 모든 성장에는 어려움이 따릅니다. "
                    message += "작은 단계로 나누어 하나씩 해결해보세요."
                    suggestions = [
                        "가장 작고 쉬운 것부터 시작하세요",
                        "5분만 투자해보세요, 시작이 반입니다",
                        "완벽하지 않아도 괜찮아요",
                    ]
                else:
                    message = "좋은 페이스로 진행하고 있네요! 이 모멘텀을 유지하면 목표 달성이 가까워질 거예요."
            else:
                message = "첫 체크인을 해보세요! 정기적인 체크인이 목표 달성의 핵심입니다."

        elif query_type == "blockers":
            blockers_found = [c for c in recent_checkins if c.get("blockers")]
            if blockers_found:
                message = "최근 블로커들을 분석해봤습니다: "
                unique_blockers = set()
                for c in blockers_found:
                    unique_blockers.add(c["blockers"][:100])
                suggestions = list(unique_blockers)[:3]
                actions = ["블로커 해결을 위한 미팅 잡기", "도움을 줄 수 있는 사람 찾기"]
            else:
                message = "다행히 최근 보고된 블로커가 없습니다. 순조롭게 진행 중이네요!"

        elif query_type == "review":
            if goals:
                completed = [g for g in goals if g["status"] == "completed"]
                message = f"총 {len(goals)}개 목표 중 {len(completed)}개 완료. "
                avg_progress = float(sum(float(g["progress_percentage"]) for g in goals)) / len(goals)
                message += f"평균 진행률 {avg_progress:.0f}%입니다."

                high_progress = [g for g in goals if float(g["progress_percentage"]) >= 80 and g["status"] == "active"]
                if high_progress:
                    actions = [f"'{g['title']}' 완료 처리하기" for g in high_progress[:2]]

        return AICoachResponse(
            message=message or "어떻게 도와드릴까요?",
            suggestions=suggestions,
            recommended_actions=actions,
            resources=[],
            follow_up_questions=questions,
            generated_at=datetime.now(),
        )

    # ============================================
    # Progress Summary
    # ============================================

    async def get_progress_summary(self, student_id: str) -> GoalProgressSummary:
        """학생 진행 요약"""
        goals = await self.get_student_goals(student_id)

        total = len(goals)
        active = len([g for g in goals if g["status"] == "active"])
        completed = len([g for g in goals if g["status"] == "completed"])
        avg_progress = float(sum(float(g["progress_percentage"]) for g in goals)) / total if total > 0 else 0

        # Count total checkins
        checkin_count = await execute_scalar(
            """
            SELECT COUNT(*)
            FROM tb_coaching_checkin c
            JOIN tb_coaching_goal g ON c.goal_id = g.goal_id
            WHERE g.std_id = $1
            """,
            student_id,
        )

        # Calculate streak (simplified)
        streak = 0
        recent = await self.get_student_recent_checkins(student_id, days=30)
        if recent:
            dates = sorted(set(c["created_at"].date() for c in recent), reverse=True)
            today = date.today()
            for i, d in enumerate(dates):
                if d == today - timedelta(days=i):
                    streak += 1
                else:
                    break

        # Recent activity
        recent_activity = []
        for c in recent[:5]:
            recent_activity.append({
                "type": "checkin",
                "goal_title": c.get("goal_title"),
                "mood": c.get("mood"),
                "date": c["created_at"].isoformat(),
            })

        return GoalProgressSummary(
            student_id=student_id,
            total_goals=total,
            active_goals=active,
            completed_goals=completed,
            average_progress=round(avg_progress, 1),
            total_checkins=checkin_count or 0,
            streak_days=streak,
            goals=[GoalResponse(**g) for g in goals],
            recent_activity=recent_activity,
        )


# Singleton instance
coaching_service = CoachingService()
