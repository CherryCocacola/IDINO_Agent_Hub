from typing import Optional, List, Dict
from datetime import datetime, date, timedelta
from uuid import UUID
import json

from ..database import execute_query, execute_one, execute_scalar, execute_command
from ..schemas import (
    InterventionType,
    InterventionStatus,
    AdvisorAssignmentResponse,
    InterventionCreate,
    InterventionUpdate,
    InterventionResponse,
    CohortSnapshotResponse,
    AdvisorNoteCreate,
    AdvisorNoteResponse,
    StudentSummary,
    CohortAnalytics,
    CohortDashboard,
    MeetingCreate,
    MeetingStatus,
)


class AdvisorService:
    # ============================================
    # Advisor Assignments
    # ============================================

    async def get_advisor_students(self, advisor_id: str) -> List[Dict]:
        query = """
            SELECT a.assignment_id, a.advisor_id::text, a.student_id,
                   a.assigned_at, a.is_primary, a.notes,
                   s.student_nm as student_name
            FROM tb_advisor_assignment a
            JOIN tb_student s ON a.student_id = s.student_id
            WHERE a.advisor_id::text = $1
            ORDER BY s.student_nm
        """
        return await execute_query(query, advisor_id)

    async def assign_student(
        self, advisor_id: str, student_id: str, is_primary: bool = True, notes: Optional[str] = None
    ) -> Dict:
        query = """
            INSERT INTO tb_advisor_assignment (advisor_id, student_id, is_primary, notes)
            VALUES ($1::uuid, $2, $3, $4)
            ON CONFLICT (advisor_id, student_id) DO UPDATE SET is_primary = EXCLUDED.is_primary, notes = EXCLUDED.notes
            RETURNING assignment_id, advisor_id::text, student_id, assigned_at, is_primary, notes
        """
        return await execute_one(query, advisor_id, student_id, is_primary, notes)

    # ============================================
    # Interventions
    # ============================================

    async def create_intervention(self, data: InterventionCreate) -> Dict:
        # First get or create assignment
        assignment = await execute_one("""
            SELECT assignment_id FROM tb_advisor_assignment
            WHERE advisor_id::text = $1 AND student_id = $2
        """, data.advisor_id, data.student_id)

        if not assignment:
            # Create assignment if it doesn't exist
            assignment = await execute_one("""
                INSERT INTO tb_advisor_assignment (advisor_id, student_id, is_primary, status)
                VALUES ($1::uuid, $2, true, 'active')
                RETURNING assignment_id
            """, data.advisor_id, data.student_id)

        # Store title, description, priority in notes as JSON
        notes_data = {"title": data.title, "description": data.description, "priority": data.priority}

        query = """
            INSERT INTO tb_advisor_intervention (
                assignment_id, intervention_type, scheduled_at, status, notes
            ) VALUES ($1, $2, $3, 'planned', $4)
            RETURNING intervention_id, assignment_id, intervention_type,
                      status, scheduled_at, completed_at, outcome,
                      follow_up_required as follow_up_needed, follow_up_date, notes, ins_dt as created_at
        """
        result = await execute_one(
            query, assignment["assignment_id"], data.intervention_type.value,
            data.scheduled_at, json.dumps(notes_data)
        )

        # Parse notes to extract title, description, priority
        notes = result.get("notes")
        if notes and isinstance(notes, str):
            try:
                notes = json.loads(notes)
            except:
                notes = {}
        elif not isinstance(notes, dict):
            notes = {}

        result["advisor_id"] = data.advisor_id
        result["student_id"] = data.student_id
        result["title"] = notes.get("title", "")
        result["description"] = notes.get("description", "")
        result["priority"] = notes.get("priority", 1)
        result["next_action"] = None

        # Get student name
        student = await execute_one("SELECT student_nm FROM tb_student WHERE student_id = $1", data.student_id)
        if student:
            result["student_name"] = student["student_nm"]
        return result

    async def get_intervention(self, intervention_id: UUID) -> Optional[Dict]:
        query = """
            SELECT i.intervention_id, a.advisor_id::text, a.student_id, s.student_nm as student_name,
                   i.intervention_type, i.notes, i.status, i.scheduled_at,
                   i.completed_at, i.outcome, i.follow_up_required as follow_up_needed,
                   i.follow_up_date, i.ins_dt as created_at
            FROM tb_advisor_intervention i
            JOIN tb_advisor_assignment a ON i.assignment_id = a.assignment_id
            JOIN tb_student s ON a.student_id = s.student_id
            WHERE i.intervention_id = $1
        """
        result = await execute_one(query, intervention_id)
        if not result:
            return None

        # Parse notes to extract title, description, priority
        notes = result.get("notes")
        if notes and isinstance(notes, str):
            try:
                notes = json.loads(notes)
            except:
                notes = {}
        elif not isinstance(notes, dict):
            notes = {}

        result["title"] = notes.get("title", "")
        result["description"] = notes.get("description", "")
        result["priority"] = notes.get("priority", 1)
        result["next_action"] = None
        return result

    async def get_advisor_interventions(
        self, advisor_id: str, status: Optional[InterventionStatus] = None, limit: int = 50
    ) -> List[Dict]:
        conditions = ["a.advisor_id::text = $1"]
        params = [advisor_id]
        if status:
            conditions.append("i.status = $2")
            params.append(status.value)

        query = f"""
            SELECT i.intervention_id, a.advisor_id::text, a.student_id, s.student_nm as student_name,
                   i.intervention_type, i.notes, i.status, i.scheduled_at,
                   i.completed_at, i.outcome, i.follow_up_required as follow_up_needed,
                   i.follow_up_date, i.ins_dt as created_at
            FROM tb_advisor_intervention i
            JOIN tb_advisor_assignment a ON i.assignment_id = a.assignment_id
            JOIN tb_student s ON a.student_id = s.student_id
            WHERE {" AND ".join(conditions)}
            ORDER BY i.scheduled_at NULLS LAST
            LIMIT {limit}
        """
        rows = await execute_query(query, *params)

        # Parse notes for each row
        for row in rows:
            notes = row.get("notes")
            if notes and isinstance(notes, str):
                try:
                    notes = json.loads(notes)
                except:
                    notes = {}
            elif not isinstance(notes, dict):
                notes = {}
            row["title"] = notes.get("title", "")
            row["description"] = notes.get("description", "")
            row["priority"] = notes.get("priority", 1)
            row["next_action"] = None
        return rows

    async def update_intervention(self, intervention_id: UUID, data: InterventionUpdate) -> Optional[Dict]:
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_intervention(intervention_id)

        if "status" in update_data and update_data["status"]:
            update_data["status"] = update_data["status"].value

        # Map field names to actual schema columns
        field_mapping = {
            "follow_up_needed": "follow_up_required",
        }

        set_clauses = []
        params = []
        for idx, (key, value) in enumerate(update_data.items(), 1):
            actual_key = field_mapping.get(key, key)
            # Skip fields that don't exist in schema (title, description, priority, next_action)
            if actual_key in ("title", "description", "priority", "next_action"):
                continue
            set_clauses.append(f"{actual_key} = ${idx}")
            params.append(value)

        if set_clauses:
            params.append(intervention_id)
            query = f"""
                UPDATE tb_advisor_intervention
                SET {", ".join(set_clauses)}
                WHERE intervention_id = ${len(params)}
            """
            await execute_command(query, *params)
        return await self.get_intervention(intervention_id)

    # ============================================
    # Advisor Notes
    # ============================================

    async def create_note(self, data: AdvisorNoteCreate) -> Dict:
        # First get or create assignment
        assignment = await execute_one("""
            SELECT assignment_id FROM tb_advisor_assignment
            WHERE advisor_id::text = $1 AND student_id = $2
        """, data.advisor_id, data.student_id)

        if not assignment:
            # Create assignment if it doesn't exist
            assignment = await execute_one("""
                INSERT INTO tb_advisor_assignment (advisor_id, student_id, is_primary, status)
                VALUES ($1::uuid, $2, true, 'active')
                RETURNING assignment_id
            """, data.advisor_id, data.student_id)

        # Store tags in content as JSON prefix (since tags column doesn't exist)
        content_with_tags = data.content
        if data.tags:
            content_with_tags = json.dumps({"tags": data.tags}) + "\n---\n" + data.content

        query = """
            INSERT INTO tb_advisor_note (assignment_id, note_type, content, is_private)
            VALUES ($1, $2, $3, $4)
            RETURNING note_id, assignment_id, note_type, content,
                      is_private, created_at, ins_dt as updated_at
        """
        result = await execute_one(
            query, assignment["assignment_id"], data.note_type,
            content_with_tags, data.is_private
        )

        result["advisor_id"] = data.advisor_id
        result["student_id"] = data.student_id
        result["tags"] = data.tags

        student = await execute_one("SELECT student_nm FROM tb_student WHERE student_id = $1", data.student_id)
        if student:
            result["student_name"] = student["student_nm"]
        return result

    async def get_student_notes(self, student_id: str, advisor_id: Optional[str] = None) -> List[Dict]:
        conditions = ["a.student_id = $1"]
        params = [student_id]
        if advisor_id:
            conditions.append("(a.advisor_id::text = $2 OR n.is_private = FALSE)")
            params.append(advisor_id)
        else:
            conditions.append("n.is_private = FALSE")

        query = f"""
            SELECT n.note_id, a.advisor_id::text, a.student_id, s.student_nm as student_name,
                   n.note_type, n.content, n.is_private, n.created_at, n.ins_dt as updated_at
            FROM tb_advisor_note n
            JOIN tb_advisor_assignment a ON n.assignment_id = a.assignment_id
            JOIN tb_student s ON a.student_id = s.student_id
            WHERE {" AND ".join(conditions)}
            ORDER BY n.created_at DESC
        """
        rows = await execute_query(query, *params)

        # Extract tags from content if stored there
        for row in rows:
            content = row.get("content", "")
            tags = []
            if content and "\n---\n" in content:
                try:
                    header, actual_content = content.split("\n---\n", 1)
                    header_data = json.loads(header)
                    tags = header_data.get("tags", [])
                    row["content"] = actual_content
                except:
                    pass
            row["tags"] = tags
        return rows

    # ============================================
    # Cohort Analytics
    # ============================================

    async def get_cohort_analytics(self, advisor_id: str) -> CohortAnalytics:
        # Get assigned students
        students = await self.get_advisor_students(advisor_id)
        student_ids = [s["student_id"] for s in students]

        if not student_ids:
            return CohortAnalytics(
                total_students=0, by_risk_level={}, by_grade={},
                avg_gpa=0, avg_progress=0, interventions_this_month=0, pending_followups=0
            )

        # Get student details with risk levels
        placeholders = ", ".join(f"${i+1}" for i in range(len(student_ids)))
        query = f"""
            SELECT s.student_id, s.current_grade as grade, 0 as gpa,
                   COALESCE(r.risk_level, 'low') as risk_level
            FROM tb_student s
            LEFT JOIN (
                SELECT DISTINCT ON (student_id) student_id,
                    CASE
                        WHEN severity = 'critical' THEN 'critical'
                        WHEN severity = 'high' THEN 'high'
                        WHEN severity = 'medium' THEN 'medium'
                        ELSE 'low'
                    END as risk_level
                FROM tb_risk_alert
                WHERE status = 'active'
                ORDER BY student_id, CASE severity WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END
            ) r ON s.student_id = r.student_id
            WHERE s.student_id IN ({placeholders})
        """
        student_data = await execute_query(query, *student_ids)

        by_risk = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        by_grade = {}
        total_gpa = 0

        for s in student_data:
            risk = s.get("risk_level", "low")
            by_risk[risk] = by_risk.get(risk, 0) + 1
            grade = s.get("grade", 1)
            by_grade[grade] = by_grade.get(grade, 0) + 1
            total_gpa += s.get("gpa", 0)

        # Count interventions this month
        interventions_count = await execute_scalar("""
            SELECT COUNT(*) FROM tb_advisor_intervention
            WHERE advisor_id = $1 AND created_at >= DATE_TRUNC('month', NOW())
        """, advisor_id) or 0

        # Count pending followups
        pending = await execute_scalar("""
            SELECT COUNT(*) FROM tb_advisor_intervention
            WHERE advisor_id = $1 AND follow_up_needed = TRUE AND status != 'completed'
        """, advisor_id) or 0

        return CohortAnalytics(
            total_students=len(students),
            by_risk_level=by_risk,
            by_grade=by_grade,
            avg_gpa=total_gpa / len(student_data) if student_data else 0,
            avg_progress=0,  # Would need goal progress data
            interventions_this_month=interventions_count,
            pending_followups=pending,
        )

    async def get_students_needing_attention(self, advisor_id: str, limit: int = 10) -> List[StudentSummary]:
        query = """
            SELECT s.student_id, s.student_nm as student_name, d.department_nm as major,
                   s.current_grade as grade, 0 as gpa,
                   COALESCE(r.alert_count, 0) as active_alerts,
                   COALESCE(r.risk_level, 'low') as risk_level,
                   i.last_interaction
            FROM tb_advisor_assignment a
            JOIN tb_student s ON a.student_id = s.student_id
            LEFT JOIN tb_department d ON s.department_cd = d.department_cd
            LEFT JOIN (
                SELECT student_id, COUNT(*) as alert_count,
                    MAX(CASE severity WHEN 'critical' THEN 'critical' WHEN 'high' THEN 'high' WHEN 'medium' THEN 'medium' ELSE 'low' END) as risk_level
                FROM tb_risk_alert WHERE status = 'active'
                GROUP BY student_id
            ) r ON s.student_id = r.student_id
            LEFT JOIN (
                SELECT aa.student_id, MAX(ai.ins_dt) as last_interaction
                FROM tb_advisor_intervention ai
                JOIN tb_advisor_assignment aa ON ai.assignment_id = aa.assignment_id
                GROUP BY aa.student_id
            ) i ON s.student_id = i.student_id
            WHERE a.advisor_id::text = $1
            ORDER BY
                CASE r.risk_level WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
                r.alert_count DESC NULLS LAST
            LIMIT $2
        """
        rows = await execute_query(query, advisor_id, limit)
        return [
            StudentSummary(
                student_id=r["student_id"], student_name=r["student_name"],
                major=r.get("major"), grade=r["grade"], gpa=r["gpa"],
                risk_level=r.get("risk_level", "low"),
                active_alerts=r.get("active_alerts", 0),
                last_interaction=r.get("last_interaction"),
                needs_attention=r.get("risk_level") in ("high", "critical") or r.get("active_alerts", 0) > 2
            )
            for r in rows
        ]

    async def get_dashboard(self, advisor_id: str) -> CohortDashboard:
        # Get advisor name
        advisor = await execute_one("SELECT user_nm FROM tb_user WHERE user_id = $1", advisor_id)

        # Get analytics
        analytics = await self.get_cohort_analytics(advisor_id)

        # Get students needing attention
        attention_students = await self.get_students_needing_attention(advisor_id)

        # Get recent interventions
        recent = await self.get_advisor_interventions(advisor_id, status=InterventionStatus.COMPLETED, limit=5)

        # Get upcoming interventions
        upcoming = await self.get_advisor_interventions(advisor_id, status=InterventionStatus.PLANNED, limit=5)

        # Get recent notes
        notes_query = """
            SELECT n.note_id, a.advisor_id::text, a.student_id, s.student_nm as student_name,
                   n.note_type, n.content, n.is_private, n.created_at, n.ins_dt as updated_at
            FROM tb_advisor_note n
            JOIN tb_advisor_assignment a ON n.assignment_id = a.assignment_id
            JOIN tb_student s ON a.student_id = s.student_id
            WHERE a.advisor_id::text = $1
            ORDER BY n.created_at DESC
            LIMIT 5
        """
        recent_notes = await execute_query(notes_query, advisor_id)

        # Extract tags from content
        for note in recent_notes:
            content = note.get("content", "")
            tags = []
            if content and "\n---\n" in content:
                try:
                    header, actual_content = content.split("\n---\n", 1)
                    header_data = json.loads(header)
                    tags = header_data.get("tags", [])
                    note["content"] = actual_content
                except:
                    pass
            note["tags"] = tags

        return CohortDashboard(
            advisor_id=advisor_id,
            advisor_name=advisor.get("user_nm") if advisor else None,
            analytics=analytics,
            students_needing_attention=attention_students,
            recent_interventions=[InterventionResponse(**i) for i in recent],
            upcoming_interventions=[InterventionResponse(**i) for i in upcoming],
            recent_notes=[AdvisorNoteResponse(**n) for n in recent_notes],
            generated_at=datetime.now(),
        )

    # ============================================
    # Cohort Snapshots
    # ============================================

    async def create_snapshot(self, advisor_id: str) -> CohortSnapshotResponse:
        analytics = await self.get_cohort_analytics(advisor_id)

        # Get the department_cd for the advisor's students
        department = await execute_one("""
            SELECT DISTINCT s.department_cd
            FROM tb_advisor_assignment a
            JOIN tb_student s ON a.student_id = s.student_id
            WHERE a.advisor_id::text = $1
            LIMIT 1
        """, advisor_id)

        department_cd = department["department_cd"] if department else "UNKNOWN"
        at_risk = analytics.by_risk_level.get("high", 0) + analytics.by_risk_level.get("critical", 0)
        on_track = analytics.by_risk_level.get("medium", 0) + analytics.by_risk_level.get("low", 0)

        query = """
            INSERT INTO tb_cohort_snapshot (
                department_cd, snapshot_date, grade_level, total_students, at_risk_count,
                avg_gpa, avg_completion_rate, risk_distribution, competency_distribution
            ) VALUES ($1, $2, 0, $3, $4, $5, $6, $7, $8)
            RETURNING snapshot_id, department_cd, snapshot_date, total_students, at_risk_count,
                      avg_gpa, avg_completion_rate as avg_progress, risk_distribution, ins_dt as created_at
        """
        result = await execute_one(
            query, department_cd, date.today(), analytics.total_students,
            at_risk, analytics.avg_gpa, analytics.avg_progress,
            json.dumps(analytics.by_risk_level), json.dumps(analytics.by_grade)
        )

        # Map to response format
        return CohortSnapshotResponse(
            snapshot_id=result["snapshot_id"],
            advisor_id=advisor_id,
            snapshot_date=result["snapshot_date"],
            total_students=result["total_students"],
            at_risk_count=result["at_risk_count"],
            on_track_count=on_track,
            excelling_count=0,
            avg_gpa=result["avg_gpa"],
            avg_progress=result["avg_progress"],
            key_metrics={"by_grade": analytics.by_grade, "by_risk": analytics.by_risk_level},
            created_at=result["created_at"]
        )

    async def get_snapshots(self, advisor_id: str, limit: int = 30) -> List[CohortSnapshotResponse]:
        # Get department_cd for the advisor
        department = await execute_one("""
            SELECT DISTINCT s.department_cd
            FROM tb_advisor_assignment a
            JOIN tb_student s ON a.student_id = s.student_id
            WHERE a.advisor_id::text = $1
            LIMIT 1
        """, advisor_id)

        if not department:
            return []

        query = """
            SELECT snapshot_id, department_cd, snapshot_date, total_students, at_risk_count,
                   avg_gpa, avg_completion_rate as avg_progress, risk_distribution, competency_distribution,
                   ins_dt as created_at
            FROM tb_cohort_snapshot
            WHERE department_cd = $1
            ORDER BY snapshot_date DESC
            LIMIT $2
        """
        rows = await execute_query(query, department["department_cd"], limit)

        return [CohortSnapshotResponse(
            snapshot_id=r["snapshot_id"],
            advisor_id=advisor_id,
            snapshot_date=r["snapshot_date"],
            total_students=r["total_students"],
            at_risk_count=r["at_risk_count"],
            on_track_count=0,
            excelling_count=0,
            avg_gpa=r["avg_gpa"],
            avg_progress=r["avg_progress"],
            key_metrics={"risk_distribution": r.get("risk_distribution"), "competency_distribution": r.get("competency_distribution")},
            created_at=r["created_at"]
        ) for r in rows]

    # ============================================
    # Meetings
    # NOTE: tb_advisor_meeting table doesn't exist in the schema
    # These methods return empty results until the table is created
    # ============================================

    async def get_advisor_meetings(self, advisor_id: str, limit: int = 50) -> List[Dict]:
        # Table tb_advisor_meeting doesn't exist
        return []

    async def create_meeting(self, data: MeetingCreate) -> Dict:
        # Table tb_advisor_meeting doesn't exist
        # Return a mock response for now
        return {
            "meeting_id": None,
            "advisor_id": data.advisor_id,
            "student_id": data.student_id,
            "student_name": None,
            "title": data.title,
            "description": data.description,
            "scheduled_at": data.scheduled_at,
            "duration_minutes": data.duration_minutes,
            "location": data.location,
            "meeting_type": data.meeting_type.value,
            "status": "scheduled",
            "notes": None,
            "completed_at": None,
            "created_at": datetime.now(),
            "error": "Table tb_advisor_meeting does not exist in the database"
        }

    async def get_meeting(self, meeting_id: UUID) -> Optional[Dict]:
        # Table tb_advisor_meeting doesn't exist
        return None

    async def complete_meeting(self, meeting_id: UUID, notes: Optional[str] = None) -> Optional[Dict]:
        # Table tb_advisor_meeting doesn't exist
        return None

    async def cancel_meeting(self, meeting_id: UUID) -> Optional[Dict]:
        # Table tb_advisor_meeting doesn't exist
        return None


advisor_service = AdvisorService()
