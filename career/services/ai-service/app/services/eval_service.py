"""
Evaluation Service for Recommendation Quality Assessment
Phase 4: Eval System

This service tracks recommendation quality through:
- Recommendation run logging with metadata
- User feedback collection (click, complete, dismiss, rating)
- Metrics calculation for quality monitoring
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings

logger = logging.getLogger(__name__)


class EvalService:
    """
    Evaluation service for tracking and measuring recommendation quality.

    Responsibilities:
    - Log each recommendation run with full context
    - Record user interactions and feedback
    - Calculate quality metrics for monitoring
    - Support A/B testing through run metadata
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    async def log_recommendation_run(
        self,
        student_id: str,
        run_type: str,
        input_snapshot: Dict[str, Any],
        model_version: str,
        prompt_version: str,
        policy_version: str,
        latency_ms: int,
        token_usage: Dict[str, int],
        recommendations: Optional[List[Dict]] = None,
        tool_calls: Optional[List[Dict]] = None,
        evidence_used: Optional[List[Dict]] = None,
    ) -> Optional[int]:
        """
        Log a recommendation run for evaluation.

        Args:
            student_id: The student being recommended for
            run_type: Type of run (tool_calling, rag, hybrid, etc.)
            input_snapshot: Snapshot of input data used
            model_version: LLM model version used
            prompt_version: System prompt version
            policy_version: Policy rules version
            latency_ms: Total execution time in milliseconds
            token_usage: Token usage breakdown
            recommendations: Generated recommendations
            tool_calls: Tool calls made during generation
            evidence_used: RAG evidence retrieved

        Returns:
            run_id of the logged run, or None on failure
        """
        try:
            # Prepare input snapshot with additional context
            full_snapshot = {
                **input_snapshot,
                "recommendations": recommendations or [],
                "tool_calls": tool_calls or [],
                "evidence_used": evidence_used or [],
            }

            sql = text("""
                INSERT INTO tb_recommendation_run (
                    student_id, run_type, input_snapshot, model_version,
                    prompt_version, policy_version, latency_ms, token_usage,
                    ins_user_id, ins_dt
                ) VALUES (
                    :student_id, :run_type, :input_snapshot, :model_version,
                    :prompt_version, :policy_version, :latency_ms, :token_usage,
                    'SYSTEM', CURRENT_TIMESTAMP
                )
                RETURNING run_id
            """)

            result = await self.db.execute(sql, {
                "student_id": student_id,
                "run_type": run_type,
                "input_snapshot": json.dumps(full_snapshot, ensure_ascii=False),
                "model_version": model_version,
                "prompt_version": prompt_version,
                "policy_version": policy_version,
                "latency_ms": latency_ms,
                "token_usage": json.dumps(token_usage),
            })

            run_id = result.scalar()
            await self.db.commit()

            logger.info(f"Logged recommendation run {run_id} for student {student_id}")
            return run_id

        except Exception as e:
            logger.error(f"Failed to log recommendation run: {e}")
            await self.db.rollback()
            return None

    async def log_recommendation_items(
        self,
        run_id: int,
        recommendations: List[Dict[str, Any]]
    ) -> List[int]:
        """
        Log individual recommendation items from a run.

        Args:
            run_id: The parent run ID
            recommendations: List of recommendation dictionaries

        Returns:
            List of item_ids created
        """
        item_ids = []

        try:
            for idx, rec in enumerate(recommendations):
                sql = text("""
                    INSERT INTO tb_recommendation_item (
                        run_id, item_order, action_type, title, description,
                        priority, deadline, target_competency_id, evidence_list,
                        constraints_checked, risk_factors, expected_impact,
                        ins_user_id, ins_dt
                    ) VALUES (
                        :run_id, :item_order, :action_type, :title, :description,
                        :priority, :deadline, :target_competency_id, :evidence_list,
                        :constraints_checked, :risk_factors, :expected_impact,
                        'SYSTEM', CURRENT_TIMESTAMP
                    )
                    RETURNING item_id
                """)

                result = await self.db.execute(sql, {
                    "run_id": run_id,
                    "item_order": idx + 1,
                    "action_type": rec.get("icon_type", "book"),
                    "title": rec.get("title", ""),
                    "description": rec.get("description", ""),
                    "priority": rec.get("priority", "medium"),
                    "deadline": rec.get("deadline"),
                    "target_competency_id": rec.get("competency"),
                    "evidence_list": json.dumps(rec.get("evidence", [])),
                    "constraints_checked": json.dumps(rec.get("constraints", {})),
                    "risk_factors": json.dumps(rec.get("risks", [])),
                    "expected_impact": rec.get("reasoning", ""),
                })

                item_id = result.scalar()
                item_ids.append(item_id)

            await self.db.commit()
            logger.info(f"Logged {len(item_ids)} recommendation items for run {run_id}")
            return item_ids

        except Exception as e:
            logger.error(f"Failed to log recommendation items: {e}")
            await self.db.rollback()
            return []

    async def record_feedback(
        self,
        student_id: str,
        item_id: int,
        feedback_type: str,
        rating: Optional[int] = None,
        comment: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[int]:
        """
        Record user feedback on a recommendation.

        Args:
            student_id: The student providing feedback
            item_id: The recommendation item ID
            feedback_type: Type of feedback (accepted, rejected, viewed, clicked, rated)
            rating: Optional rating (1-5)
            comment: Optional comment text
            context_data: Optional additional context

        Returns:
            feedback_id if successful, None otherwise
        """
        try:
            sql = text("""
                INSERT INTO tb_feedback_event (
                    student_id, item_id, feedback_type, rating, comment,
                    context_data, ins_user_id, ins_dt
                ) VALUES (
                    :student_id, :item_id, :feedback_type, :rating, :comment,
                    :context_data, :student_id, CURRENT_TIMESTAMP
                )
                RETURNING feedback_id
            """)

            result = await self.db.execute(sql, {
                "student_id": student_id,
                "item_id": item_id,
                "feedback_type": feedback_type,
                "rating": rating,
                "comment": comment,
                "context_data": json.dumps(context_data or {}),
            })

            feedback_id = result.scalar()
            await self.db.commit()

            logger.info(f"Recorded feedback {feedback_id} for item {item_id}")
            return feedback_id

        except Exception as e:
            logger.error(f"Failed to record feedback: {e}")
            await self.db.rollback()
            return None

    async def get_feedback_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Get aggregated feedback statistics.

        Args:
            days: Number of days to look back

        Returns:
            Dictionary with feedback statistics by action type
        """
        try:
            sql = text("""
                SELECT
                    ri.action_type,
                    AVG(fe.rating) as avg_rating,
                    COUNT(*) as feedback_count,
                    COUNT(CASE WHEN fe.feedback_type = 'accepted' THEN 1 END) as accepted_count,
                    COUNT(CASE WHEN fe.feedback_type = 'rejected' THEN 1 END) as rejected_count,
                    COUNT(CASE WHEN fe.feedback_type = 'viewed' THEN 1 END) as viewed_count,
                    COUNT(CASE WHEN fe.feedback_type = 'clicked' THEN 1 END) as clicked_count
                FROM tb_feedback_event fe
                JOIN tb_recommendation_item ri ON fe.item_id = ri.item_id
                WHERE fe.ins_dt >= CURRENT_DATE - INTERVAL ':days days'
                GROUP BY ri.action_type
            """)

            result = await self.db.execute(sql, {"days": days})
            rows = result.fetchall()

            stats = {}
            for row in rows:
                stats[row.action_type] = {
                    "avg_rating": float(row.avg_rating) if row.avg_rating else None,
                    "feedback_count": row.feedback_count,
                    "accepted_count": row.accepted_count,
                    "rejected_count": row.rejected_count,
                    "viewed_count": row.viewed_count,
                    "clicked_count": row.clicked_count,
                    "acceptance_rate": (
                        row.accepted_count / (row.accepted_count + row.rejected_count)
                        if (row.accepted_count + row.rejected_count) > 0
                        else None
                    ),
                }

            return stats

        except Exception as e:
            logger.error(f"Failed to get feedback stats: {e}")
            return {}

    async def calculate_metrics(self, days: int = 30) -> Dict[str, Any]:
        """
        Calculate comprehensive evaluation metrics.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with quality metrics
        """
        try:
            # Get run statistics
            run_sql = text("""
                SELECT
                    COUNT(*) as total_runs,
                    AVG(latency_ms) as avg_latency_ms,
                    COUNT(DISTINCT student_id) as unique_students,
                    AVG((token_usage->>'total_tokens')::int) as avg_tokens
                FROM tb_recommendation_run
                WHERE ins_dt >= CURRENT_DATE - INTERVAL ':days days'
            """)

            run_result = await self.db.execute(run_sql, {"days": days})
            run_row = run_result.fetchone()

            # Get feedback statistics
            feedback_sql = text("""
                SELECT
                    COUNT(DISTINCT fe.item_id) as items_with_feedback,
                    AVG(CASE WHEN fe.feedback_type = 'rated' THEN fe.rating END) as avg_rating,
                    COUNT(CASE WHEN fe.feedback_type = 'accepted' THEN 1 END) as total_accepted,
                    COUNT(CASE WHEN fe.feedback_type = 'rejected' THEN 1 END) as total_rejected
                FROM tb_feedback_event fe
                JOIN tb_recommendation_item ri ON fe.item_id = ri.item_id
                JOIN tb_recommendation_run rr ON ri.run_id = rr.run_id
                WHERE rr.ins_dt >= CURRENT_DATE - INTERVAL ':days days'
            """)

            feedback_result = await self.db.execute(feedback_sql, {"days": days})
            feedback_row = feedback_result.fetchone()

            # Calculate derived metrics
            total_feedback = (feedback_row.total_accepted or 0) + (feedback_row.total_rejected or 0)
            acceptance_rate = (
                feedback_row.total_accepted / total_feedback
                if total_feedback > 0
                else None
            )

            return {
                "period_days": days,
                "run_metrics": {
                    "total_runs": run_row.total_runs or 0,
                    "avg_latency_ms": float(run_row.avg_latency_ms or 0),
                    "unique_students": run_row.unique_students or 0,
                    "avg_tokens_per_run": float(run_row.avg_tokens or 0),
                },
                "feedback_metrics": {
                    "items_with_feedback": feedback_row.items_with_feedback or 0,
                    "avg_rating": float(feedback_row.avg_rating) if feedback_row.avg_rating else None,
                    "acceptance_rate": acceptance_rate,
                    "total_accepted": feedback_row.total_accepted or 0,
                    "total_rejected": feedback_row.total_rejected or 0,
                },
                "quality_indicators": {
                    "engagement_rate": (
                        feedback_row.items_with_feedback / (run_row.total_runs or 1)
                        if run_row.total_runs
                        else 0
                    ),
                },
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to calculate metrics: {e}")
            return {
                "error": str(e),
                "period_days": days,
                "generated_at": datetime.utcnow().isoformat(),
            }

    async def get_run_details(self, run_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific run.

        Args:
            run_id: The run ID to retrieve

        Returns:
            Dictionary with run details or None if not found
        """
        try:
            sql = text("""
                SELECT
                    rr.run_id,
                    rr.student_id,
                    rr.run_type,
                    rr.input_snapshot,
                    rr.model_version,
                    rr.prompt_version,
                    rr.policy_version,
                    rr.latency_ms,
                    rr.token_usage,
                    rr.ins_dt as created_at
                FROM tb_recommendation_run rr
                WHERE rr.run_id = :run_id
            """)

            result = await self.db.execute(sql, {"run_id": run_id})
            row = result.fetchone()

            if not row:
                return None

            # Get associated items
            items_sql = text("""
                SELECT
                    ri.item_id,
                    ri.item_order,
                    ri.action_type,
                    ri.title,
                    ri.description,
                    ri.priority,
                    ri.deadline,
                    ri.expected_impact
                FROM tb_recommendation_item ri
                WHERE ri.run_id = :run_id
                ORDER BY ri.item_order
            """)

            items_result = await self.db.execute(items_sql, {"run_id": run_id})
            items = [
                {
                    "item_id": item.item_id,
                    "order": item.item_order,
                    "action_type": item.action_type,
                    "title": item.title,
                    "description": item.description,
                    "priority": item.priority,
                    "deadline": item.deadline,
                    "expected_impact": item.expected_impact,
                }
                for item in items_result.fetchall()
            ]

            return {
                "run_id": row.run_id,
                "student_id": row.student_id,
                "run_type": row.run_type,
                "input_snapshot": json.loads(row.input_snapshot) if row.input_snapshot else {},
                "model_version": row.model_version,
                "prompt_version": row.prompt_version,
                "policy_version": row.policy_version,
                "latency_ms": row.latency_ms,
                "token_usage": json.loads(row.token_usage) if row.token_usage else {},
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "items": items,
            }

        except Exception as e:
            logger.error(f"Failed to get run details: {e}")
            return None

    async def get_eval_cases(self, case_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get evaluation test cases for quality testing.

        Args:
            case_type: Optional filter by case type

        Returns:
            List of evaluation cases
        """
        try:
            sql = text("""
                SELECT
                    case_id,
                    case_nm,
                    case_type,
                    input_data,
                    expected_output,
                    quality_criteria,
                    use_fg
                FROM tb_eval_case
                WHERE use_fg = 'Y'
                    AND (:case_type IS NULL OR case_type = :case_type)
                ORDER BY case_nm
            """)

            result = await self.db.execute(sql, {"case_type": case_type})
            rows = result.fetchall()

            return [
                {
                    "case_id": row.case_id,
                    "case_name": row.case_nm,
                    "case_type": row.case_type,
                    "input_data": json.loads(row.input_data) if row.input_data else {},
                    "expected_output": json.loads(row.expected_output) if row.expected_output else {},
                    "quality_criteria": json.loads(row.quality_criteria) if row.quality_criteria else {},
                }
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Failed to get eval cases: {e}")
            return []

    async def save_eval_result(
        self,
        case_id: int,
        run_id: int,
        actual_output: Dict[str, Any],
        passed: bool,
        score: float,
        details: Dict[str, Any],
    ) -> Optional[int]:
        """
        Save an evaluation result.

        Args:
            case_id: The test case ID
            run_id: The recommendation run ID
            actual_output: The actual output from the run
            passed: Whether the test passed
            score: Quality score (0-100)
            details: Detailed evaluation results

        Returns:
            result_id if successful, None otherwise
        """
        try:
            sql = text("""
                INSERT INTO tb_eval_result (
                    case_id, run_id, actual_output, pass_fg,
                    score, details, ins_user_id, ins_dt
                ) VALUES (
                    :case_id, :run_id, :actual_output, :pass_fg,
                    :score, :details, 'SYSTEM', CURRENT_TIMESTAMP
                )
                RETURNING result_id
            """)

            result = await self.db.execute(sql, {
                "case_id": case_id,
                "run_id": run_id,
                "actual_output": json.dumps(actual_output, ensure_ascii=False),
                "pass_fg": "Y" if passed else "N",
                "score": score,
                "details": json.dumps(details, ensure_ascii=False),
            })

            result_id = result.scalar()
            await self.db.commit()

            logger.info(f"Saved eval result {result_id} for case {case_id}, run {run_id}")
            return result_id

        except Exception as e:
            logger.error(f"Failed to save eval result: {e}")
            await self.db.rollback()
            return None
