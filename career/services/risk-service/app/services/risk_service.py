from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from uuid import UUID

from ..database import execute_query, execute_one, execute_scalar, execute_command
from ..schemas import (
    RiskSeverity,
    RiskCategory,
    AlertStatus,
    RiskAlertCreate,
    RiskAlertUpdate,
    RiskAlertResponse,
    ConstraintCheckResponse,
    PrerequisiteRuleResponse,
    StudentRiskProfile,
    RiskRecommendation,
    RiskAnalysisResponse,
)
from ..config import get_settings


class RiskService:
    """위험 알림 서비스"""

    def __init__(self):
        self.settings = get_settings()

    # ============================================
    # Risk Alert CRUD
    # ============================================

    async def create_alert(self, data: RiskAlertCreate) -> Dict:
        """위험 알림 생성"""
        query = """
            INSERT INTO tb_risk_alert (
                student_id, risk_type, severity, title, description,
                related_entity_type, related_entity_id, status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, 'active')
            RETURNING
                alert_id, student_id, CASE risk_type
                    WHEN 'gpa_warning' THEN 'gpa' WHEN 'gpa_drop' THEN 'gpa' WHEN 'academic' THEN 'gpa'
                    WHEN 'credit_shortage' THEN 'credits' WHEN 'competency' THEN 'skill_gap'
                    WHEN 'graduation_delay' THEN 'graduation' WHEN 'prerequisite_missing' THEN 'prerequisite'
                    ELSE risk_type
                END as category, severity, title,
                description, NULL::text as recommendation, related_entity_type, related_entity_id,
                NULL::date as due_date, status, NULL::timestamp as acknowledged_at, resolved_at, resolution_notes as resolution_note,
                ins_dt as created_at, upd_dt as updated_at
        """
        return await execute_one(
            query,
            data.student_id,
            data.category.value,
            data.severity.value,
            data.title,
            data.description,
            data.related_entity_type,
            data.related_entity_id,
        )

    async def get_alert(self, alert_id: UUID) -> Optional[Dict]:
        """알림 조회"""
        query = """
            SELECT
                alert_id, student_id, CASE risk_type
                    WHEN 'gpa_warning' THEN 'gpa' WHEN 'gpa_drop' THEN 'gpa' WHEN 'academic' THEN 'gpa'
                    WHEN 'credit_shortage' THEN 'credits' WHEN 'competency' THEN 'skill_gap'
                    WHEN 'graduation_delay' THEN 'graduation' WHEN 'prerequisite_missing' THEN 'prerequisite'
                    ELSE risk_type
                END as category, severity, title,
                description, NULL as recommendation, related_entity_type, related_entity_id,
                NULL as due_date, status, NULL as acknowledged_at, resolved_at, resolution_notes as resolution_note,
                ins_dt as created_at, upd_dt as updated_at
            FROM tb_risk_alert
            WHERE alert_id = $1
        """
        return await execute_one(query, alert_id)

    async def get_student_alerts(
        self,
        student_id: str,
        status: Optional[AlertStatus] = None,
        category: Optional[RiskCategory] = None,
        severity: Optional[RiskSeverity] = None,
    ) -> List[Dict]:
        """학생 알림 목록"""
        conditions = ["student_id = $1"]
        params = [student_id]
        param_idx = 2

        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status.value)
            param_idx += 1

        if category:
            conditions.append(f"risk_type = ${param_idx}")
            params.append(category.value)
            param_idx += 1

        if severity:
            conditions.append(f"severity = ${param_idx}")
            params.append(severity.value)
            param_idx += 1

        query = f"""
            SELECT
                alert_id, student_id, CASE risk_type
                    WHEN 'gpa_warning' THEN 'gpa' WHEN 'gpa_drop' THEN 'gpa' WHEN 'academic' THEN 'gpa'
                    WHEN 'credit_shortage' THEN 'credits' WHEN 'competency' THEN 'skill_gap'
                    WHEN 'graduation_delay' THEN 'graduation' WHEN 'prerequisite_missing' THEN 'prerequisite'
                    ELSE risk_type
                END as category, severity, title,
                description, NULL as recommendation, related_entity_type, related_entity_id,
                NULL as due_date, status, NULL as acknowledged_at, resolved_at, resolution_notes as resolution_note,
                ins_dt as created_at, upd_dt as updated_at
            FROM tb_risk_alert
            WHERE {" AND ".join(conditions)}
            ORDER BY
                CASE severity WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
                ins_dt DESC
        """
        return await execute_query(query, *params)

    async def update_alert(self, alert_id: UUID, data: RiskAlertUpdate) -> Optional[Dict]:
        """알림 상태 수정"""
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_alert(alert_id)

        # Convert enum
        if "status" in update_data and update_data["status"]:
            update_data["status"] = update_data["status"].value

            # Auto-set resolved_at timestamp
            if update_data["status"] == "resolved" and "resolved_at" not in update_data:
                update_data["resolved_at"] = datetime.now()

        # Map resolution_note to resolution_notes
        if "resolution_note" in update_data:
            update_data["resolution_notes"] = update_data.pop("resolution_note")

        # Remove unsupported fields
        update_data.pop("acknowledged_at", None)
        update_data.pop("due_date", None)
        update_data.pop("recommendation", None)
        update_data.pop("category", None)  # Can't update category, it's risk_type

        set_clauses = []
        params = []
        for idx, (key, value) in enumerate(update_data.items(), 1):
            set_clauses.append(f"{key} = ${idx}")
            params.append(value)

        if not set_clauses:
            return await self.get_alert(alert_id)

        params.append(alert_id)

        query = f"""
            UPDATE tb_risk_alert
            SET {", ".join(set_clauses)}, upd_dt = NOW()
            WHERE alert_id = ${len(params)}
            RETURNING
                alert_id, student_id, CASE risk_type
                    WHEN 'gpa_warning' THEN 'gpa' WHEN 'gpa_drop' THEN 'gpa' WHEN 'academic' THEN 'gpa'
                    WHEN 'credit_shortage' THEN 'credits' WHEN 'competency' THEN 'skill_gap'
                    WHEN 'graduation_delay' THEN 'graduation' WHEN 'prerequisite_missing' THEN 'prerequisite'
                    ELSE risk_type
                END as category, severity, title,
                description, NULL::text as recommendation, related_entity_type, related_entity_id,
                NULL::date as due_date, status, NULL::timestamp as acknowledged_at, resolved_at, resolution_notes as resolution_note,
                ins_dt as created_at, upd_dt as updated_at
        """
        return await execute_one(query, *params)

    # ============================================
    # Risk Analysis Engine
    # ============================================

    async def get_student_info(self, student_id: str) -> Optional[Dict]:
        """학생 기본 정보 (with calculated GPA from tb_grade)"""
        query = """
            SELECT
                s.student_id as student_id,
                s.student_nm as std_nm,
                s.department_cd as major_cd,
                s.current_grade as grade,
                COALESCE(
                    CASE
                        WHEN SUM(g.credits_earned) > 0
                        THEN ROUND(SUM(g.grade_point * g.credits_earned)::numeric / SUM(g.credits_earned)::numeric, 2)
                        ELSE NULL
                    END,
                    0
                )::float as gpa
            FROM tb_student s
            LEFT JOIN tb_grade g ON s.student_id = g.student_id
                AND g.grade_point IS NOT NULL
                AND g.credits_earned > 0
            WHERE s.student_id = $1
            GROUP BY s.student_id, s.student_nm, s.department_cd, s.current_grade
        """
        return await execute_one(query, student_id)

    async def analyze_gpa_risk(self, student_id: str, gpa: float) -> tuple[float, List[RiskAlertCreate]]:
        """GPA 위험 분석"""
        alerts = []
        risk_score = 0.0

        if gpa < self.settings.GPA_CRITICAL_THRESHOLD:
            risk_score = self.settings.GPA_CRITICAL_RISK_SCORE
            alerts.append(RiskAlertCreate(
                student_id=student_id,
                category=RiskCategory.GPA,
                severity=RiskSeverity.CRITICAL,
                title="학점 위기 - 학사 경고 위험",
                description=f"현재 GPA {gpa:.2f}로 학사 경고 기준({self.settings.GPA_CRITICAL_THRESHOLD}) 미만입니다.",
                recommendation=f"즉시 학업 상담을 받으시고, 다음 학기 수강 계획을 재검토하세요. [학업상담센터]({self.settings.ACADEMIC_COUNSELING_URL})",
            ))
        elif gpa < self.settings.GPA_WARNING_THRESHOLD:
            risk_score = self.settings.GPA_WARNING_RISK_SCORE
            alerts.append(RiskAlertCreate(
                student_id=student_id,
                category=RiskCategory.GPA,
                severity=RiskSeverity.HIGH,
                title="학점 주의 - 개선 필요",
                description=f"현재 GPA {gpa:.2f}로 경고 기준({self.settings.GPA_WARNING_THRESHOLD})에 근접합니다.",
                recommendation=f"학습 전략을 점검하고, 필요시 튜터링을 신청하세요. [튜터링서비스]({self.settings.TUTORING_SERVICE_URL})",
            ))
        elif gpa < self.settings.GPA_MEDIUM_THRESHOLD:
            risk_score = self.settings.GPA_MEDIUM_RISK_SCORE
            alerts.append(RiskAlertCreate(
                student_id=student_id,
                category=RiskCategory.GPA,
                severity=RiskSeverity.MEDIUM,
                title="학점 향상 권장",
                description=f"현재 GPA {gpa:.2f}입니다. 목표 기업/대학원 지원을 위해 향상을 권장합니다.",
                recommendation=f"성적 향상 프로그램 참여를 고려해보세요. [학습지원센터]({self.settings.TUTORING_SERVICE_URL})",
            ))

        return risk_score, alerts

    async def analyze_credit_risk(self, student_id: str) -> tuple[float, List[RiskAlertCreate]]:
        """학점 이수 위험 분석"""
        # Get current credits vs required (using credits_earned from tb_grade for consistency)
        query = """
            SELECT
                COALESCE(SUM(g.credits_earned), 0) as earned_credits,
                s.current_grade as year
            FROM tb_student s
            LEFT JOIN tb_grade g ON s.student_id = g.student_id
                AND g.grade_point IS NOT NULL
                AND g.credits_earned > 0
            WHERE s.student_id = $1
            GROUP BY s.current_grade
        """
        result = await execute_one(query, student_id)

        alerts = []
        risk_score = 0.0

        if result:
            earned = float(result.get("earned_credits", 0))
            year = int(result.get("year", 1))

            # Expected credits based on config
            expected = year * self.settings.CREDITS_PER_YEAR
            gap = expected - earned

            if gap > self.settings.CREDIT_WARNING_THRESHOLD:
                severity = RiskSeverity.HIGH if gap > self.settings.CREDIT_HIGH_THRESHOLD else RiskSeverity.MEDIUM
                risk_score = min(gap * 2, self.settings.CREDIT_MAX_RISK_SCORE)
                alerts.append(RiskAlertCreate(
                    student_id=student_id,
                    category=RiskCategory.CREDITS,
                    severity=severity,
                    title=f"학점 이수 부족 - {gap}학점 미달",
                    description=f"현재 {year}학년으로 예상 이수 학점 {expected}학점 대비 {earned}학점 취득.",
                    recommendation=f"수강 계획을 검토하고, 계절학기 수강을 고려하세요. [학업상담센터]({self.settings.ACADEMIC_COUNSELING_URL})",
                ))

        return risk_score, alerts

    async def analyze_prerequisite_risk(self, student_id: str) -> tuple[float, List[RiskAlertCreate]]:
        """선수과목 위험 분석"""
        # Check if any enrolled courses have missing prerequisites
        query = """
            SELECT p.course_cd, c1.course_nm, p.prerequisite_course_cd as prerequisite_cd, c2.course_nm as prereq_nm
            FROM tb_prerequisite p
            JOIN tb_course c1 ON p.course_cd = c1.course_cd
            JOIN tb_course c2 ON p.prerequisite_course_cd = c2.course_cd
            WHERE p.prerequisite_type = 'required'
            AND p.course_cd IN (
                SELECT course_cd FROM tb_grade
                WHERE student_id = $1 AND term_cd = (SELECT MAX(term_cd) FROM tb_grade WHERE student_id = $1)
            )
            AND p.prerequisite_course_cd NOT IN (
                SELECT course_cd FROM tb_grade
                WHERE student_id = $1 AND grade_letter NOT IN ('F', 'NP', 'W')
            )
        """
        missing = await execute_query(query, student_id)

        alerts = []
        risk_score = 0.0

        if missing:
            risk_score = len(missing) * 20
            for m in missing[:3]:  # Limit to 3 alerts
                alerts.append(RiskAlertCreate(
                    student_id=student_id,
                    category=RiskCategory.PREREQUISITE,
                    severity=RiskSeverity.HIGH,
                    title=f"선수과목 미이수 - {m['course_nm']}",
                    description=f"{m['course_nm']} 수강을 위해 {m['prereq_nm']} 선이수가 필요합니다.",
                    recommendation=f"{m['prereq_nm']}을(를) 먼저 수강하거나, 담당 교수님께 상담하세요.",
                    related_entity_type="course",
                    related_entity_id=m["course_cd"],
                ))

        return min(risk_score, 100), alerts

    async def analyze_graduation_risk(self, student_id: str) -> tuple[float, List[RiskAlertCreate]]:
        """졸업요건 위험 분석"""
        # Simplified graduation check (using credits_earned from tb_grade for consistency)
        required_credits = self.settings.GRADUATION_REQUIRED_CREDITS
        query = f"""
            SELECT
                s.current_grade as year,
                COALESCE(SUM(g.credits_earned), 0) as earned,
                {required_credits} as required
            FROM tb_student s
            LEFT JOIN tb_grade g ON s.student_id = g.student_id
                AND g.grade_point IS NOT NULL
                AND g.credits_earned > 0
            WHERE s.student_id = $1
            GROUP BY s.current_grade
        """
        result = await execute_one(query, student_id)

        alerts = []
        risk_score = 0.0

        if result and result.get("year", 1) >= 3:
            earned = float(result.get("earned", 0))
            required = float(result.get("required", self.settings.GRADUATION_REQUIRED_CREDITS))
            remaining = required - earned
            semesters_left = max(1, (self.settings.TOTAL_SEMESTERS - int(result["year"]) * 2))
            per_semester = remaining / semesters_left

            if per_semester > self.settings.GRADUATION_HIGH_PER_SEMESTER:
                risk_score = self.settings.GRADUATION_HIGH_RISK_SCORE
                alerts.append(RiskAlertCreate(
                    student_id=student_id,
                    category=RiskCategory.GRADUATION,
                    severity=RiskSeverity.HIGH,
                    title="졸업요건 충족 위험",
                    description=f"졸업까지 {remaining}학점 필요. 학기당 {per_semester:.0f}학점 필요.",
                    recommendation=f"졸업요건 상담을 받고, 계절학기 수강 계획을 세우세요. [학업상담센터]({self.settings.ACADEMIC_COUNSELING_URL})",
                ))
            elif per_semester > self.settings.GRADUATION_MEDIUM_PER_SEMESTER:
                risk_score = self.settings.GRADUATION_MEDIUM_RISK_SCORE
                alerts.append(RiskAlertCreate(
                    student_id=student_id,
                    category=RiskCategory.GRADUATION,
                    severity=RiskSeverity.MEDIUM,
                    title="졸업요건 주의",
                    description=f"졸업까지 {remaining}학점 필요. 여유 있는 수강 계획이 필요합니다.",
                    recommendation=f"수강 계획을 미리 세워두세요. [학업상담센터]({self.settings.ACADEMIC_COUNSELING_URL})",
                ))

        return risk_score, alerts

    async def analyze_skill_gap_risk(self, student_id: str) -> tuple[float, List[RiskAlertCreate]]:
        """스킬 갭 위험 분석"""
        # Check skill gap analysis results
        query = """
            SELECT target_role_cd, overall_gap_score, top_priority_skills
            FROM tb_skill_gap_analysis
            WHERE student_id = $1
            ORDER BY analysis_date DESC
            LIMIT 1
        """
        result = await execute_one(query, student_id)

        alerts = []
        risk_score = 0.0

        if result:
            gap_score = float(result.get("overall_gap_score", 0))
            priority_skills = result.get("top_priority_skills", [])

            if gap_score > self.settings.SKILL_GAP_MEDIUM_THRESHOLD:
                risk_score = gap_score * self.settings.SKILL_GAP_RISK_MULTIPLIER
                severity = RiskSeverity.HIGH if gap_score > self.settings.SKILL_GAP_HIGH_THRESHOLD else RiskSeverity.MEDIUM
                alerts.append(RiskAlertCreate(
                    student_id=student_id,
                    category=RiskCategory.SKILL_GAP,
                    severity=severity,
                    title=f"목표 직무 스킬 갭 - {gap_score:.0f}%",
                    description=f"목표 직무 대비 스킬 갭이 큽니다. 우선 개발 필요: {', '.join(priority_skills[:3])}",
                    recommendation=f"스킬 개발 계획을 세우고, 관련 프로젝트/강의를 찾아보세요. [스킬개발센터]({self.settings.SKILL_DEVELOPMENT_URL})",
                ))

        return risk_score, alerts

    async def run_full_analysis(
        self,
        student_id: str,
        categories: Optional[List[RiskCategory]] = None,
        create_alerts: bool = True,
    ) -> RiskAnalysisResponse:
        """전체 위험 분석 실행"""
        student = await self.get_student_info(student_id)
        if not student:
            raise ValueError(f"Student {student_id} not found")

        all_alerts = []
        risk_scores = {}

        # Analyze each category
        if not categories or RiskCategory.GPA in categories:
            gpa = student.get("gpa", 0) or 0
            score, alerts = await self.analyze_gpa_risk(student_id, gpa)
            risk_scores["gpa"] = score
            all_alerts.extend(alerts)

        if not categories or RiskCategory.CREDITS in categories:
            score, alerts = await self.analyze_credit_risk(student_id)
            risk_scores["credits"] = score
            all_alerts.extend(alerts)

        if not categories or RiskCategory.PREREQUISITE in categories:
            score, alerts = await self.analyze_prerequisite_risk(student_id)
            risk_scores["prerequisite"] = score
            all_alerts.extend(alerts)

        if not categories or RiskCategory.GRADUATION in categories:
            score, alerts = await self.analyze_graduation_risk(student_id)
            risk_scores["graduation"] = score
            all_alerts.extend(alerts)

        if not categories or RiskCategory.SKILL_GAP in categories:
            score, alerts = await self.analyze_skill_gap_risk(student_id)
            risk_scores["skill_gap"] = score
            all_alerts.extend(alerts)

        # Calculate overall score (weighted average from config)
        weights = {
            "gpa": self.settings.RISK_WEIGHT_GPA,
            "credits": self.settings.RISK_WEIGHT_CREDITS,
            "prerequisite": self.settings.RISK_WEIGHT_PREREQUISITE,
            "graduation": self.settings.RISK_WEIGHT_GRADUATION,
            "skill_gap": self.settings.RISK_WEIGHT_SKILL_GAP,
        }
        overall_score = sum(risk_scores.get(k, 0) * v for k, v in weights.items())

        # Determine risk level from config thresholds
        if overall_score >= self.settings.RISK_LEVEL_CRITICAL_THRESHOLD:
            risk_level = RiskSeverity.CRITICAL
        elif overall_score >= self.settings.RISK_LEVEL_HIGH_THRESHOLD:
            risk_level = RiskSeverity.HIGH
        elif overall_score >= self.settings.RISK_LEVEL_MEDIUM_THRESHOLD:
            risk_level = RiskSeverity.MEDIUM
        else:
            risk_level = RiskSeverity.LOW

        # Create alerts in database
        created_alerts = []
        if create_alerts and all_alerts:
            for alert_data in all_alerts:
                # Check if similar alert already exists
                existing = await execute_one(
                    """
                    SELECT alert_id FROM tb_risk_alert
                    WHERE student_id = $1 AND risk_type = $2 AND status = 'active'
                    AND ins_dt > NOW() - INTERVAL '7 days'
                    """,
                    student_id,
                    alert_data.category.value,
                )
                if not existing:
                    created = await self.create_alert(alert_data)
                    created_alerts.append(RiskAlertResponse(**created))

        # Build recommendations with proper deadlines and resources
        recommendations = []
        priority = 1
        for alert in sorted(all_alerts, key=lambda x: ["critical", "high", "medium", "low"].index(x.severity.value)):
            # Calculate deadline based on severity
            if alert.severity == RiskSeverity.CRITICAL:
                deadline_days = 7  # 1주일 내
            elif alert.severity == RiskSeverity.HIGH:
                deadline_days = 14  # 2주일 내
            elif alert.severity == RiskSeverity.MEDIUM:
                deadline_days = 30  # 1개월 내
            else:
                deadline_days = 60  # 2개월 내

            calculated_deadline = date.today() + timedelta(days=deadline_days)

            # Map category to resources
            resource_map = {
                RiskCategory.GPA: [self.settings.ACADEMIC_COUNSELING_URL, self.settings.TUTORING_SERVICE_URL],
                RiskCategory.CREDITS: [self.settings.ACADEMIC_COUNSELING_URL],
                RiskCategory.PREREQUISITE: [self.settings.ACADEMIC_COUNSELING_URL],
                RiskCategory.GRADUATION: [self.settings.ACADEMIC_COUNSELING_URL, self.settings.CAREER_CENTER_URL],
                RiskCategory.SKILL_GAP: [self.settings.SKILL_DEVELOPMENT_URL, self.settings.CAREER_CENTER_URL],
            }
            resources = resource_map.get(alert.category, [])

            recommendations.append(RiskRecommendation(
                priority=priority,
                category=alert.category,
                action=alert.title,
                description=alert.recommendation or "",
                deadline=calculated_deadline,
                resources=resources,
            ))
            priority += 1

        # Get all active alerts
        active_alerts = await self.get_student_alerts(student_id, status=AlertStatus.ACTIVE)
        active_alert_responses = [RiskAlertResponse(**a) for a in active_alerts]

        # 기존 active 알림 기반 최소 점수 보정
        alert_min_scores = {"critical": 70, "high": 50, "medium": 30, "low": 15}
        category_map = {
            "gpa": "gpa", "credits": "credits", "prerequisite": "prerequisite",
            "graduation": "graduation", "skill_gap": "skill_gap",
            "career": "skill_gap",
        }
        for alert in active_alerts:
            cat = alert.get("category", "")
            sev = alert.get("severity", "")
            key = category_map.get(cat, cat)
            if key in risk_scores:
                min_score = alert_min_scores.get(sev, 0)
                risk_scores[key] = max(risk_scores[key], min_score)

        # Recalculate overall score after alert-based correction
        overall_score = sum(risk_scores.get(k, 0) * v for k, v in weights.items())

        # Re-determine risk level
        if overall_score >= self.settings.RISK_LEVEL_CRITICAL_THRESHOLD:
            risk_level = RiskSeverity.CRITICAL
        elif overall_score >= self.settings.RISK_LEVEL_HIGH_THRESHOLD:
            risk_level = RiskSeverity.HIGH
        elif overall_score >= self.settings.RISK_LEVEL_MEDIUM_THRESHOLD:
            risk_level = RiskSeverity.MEDIUM
        else:
            risk_level = RiskSeverity.LOW

        profile = StudentRiskProfile(
            student_id=student_id,
            student_name=student.get("std_nm"),
            overall_risk_score=round(overall_score, 1),
            risk_level=risk_level,
            gpa_risk_score=risk_scores.get("gpa", 0),
            credits_risk_score=risk_scores.get("credits", 0),
            prerequisite_risk_score=risk_scores.get("prerequisite", 0),
            graduation_risk_score=risk_scores.get("graduation", 0),
            career_risk_score=risk_scores.get("skill_gap", 0),
            active_alerts=active_alert_responses,
            total_active_alerts=len(active_alert_responses),
            critical_alerts=len([a for a in active_alert_responses if a.severity == RiskSeverity.CRITICAL]),
            high_alerts=len([a for a in active_alert_responses if a.severity == RiskSeverity.HIGH]),
            recommendations=recommendations[:5],
            last_analyzed_at=datetime.now(),
            next_review_date=date.today() + timedelta(days=7),
        )

        # Generate summary
        key_risks = [a.title for a in all_alerts[:3]]
        immediate_actions = [r.action for r in recommendations[:3]]

        summary = f"위험 점수: {overall_score:.0f}/100 ({risk_level.value}). "
        if critical_count := profile.critical_alerts:
            summary += f"긴급 경고 {critical_count}건. "
        if key_risks:
            summary += f"주요 위험: {', '.join(key_risks[:2])}."

        return RiskAnalysisResponse(
            profile=profile,
            analysis_summary=summary,
            key_risks=key_risks,
            immediate_actions=immediate_actions,
            generated_at=datetime.now(),
        )

    # ============================================
    # Constraint Checks
    # ============================================

    async def get_constraint_checks(self, student_id: str) -> List[Dict]:
        """학생 제약조건 체크 결과"""
        query = """
            SELECT
                check_id, student_id as student_id, constraint_type, constraint_name,
                is_satisfied, current_value, required_value, gap_description, checked_at
            FROM tb_constraint_check
            WHERE student_id = $1
            ORDER BY is_satisfied, checked_at DESC
        """
        return await execute_query(query, student_id)

    async def save_constraint_check(
        self,
        student_id: str,
        constraint_type: str,
        constraint_name: str,
        is_satisfied: bool,
        current_value: Optional[str] = None,
        required_value: Optional[str] = None,
        gap_description: Optional[str] = None,
    ) -> Dict:
        """제약조건 체크 결과 저장"""
        query = """
            INSERT INTO tb_constraint_check (
                student_id, constraint_type, constraint_name, is_satisfied,
                current_value, required_value, gap_description
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (student_id, constraint_type, constraint_name)
            DO UPDATE SET
                is_satisfied = EXCLUDED.is_satisfied,
                current_value = EXCLUDED.current_value,
                required_value = EXCLUDED.required_value,
                gap_description = EXCLUDED.gap_description,
                checked_at = NOW()
            RETURNING
                check_id, student_id as student_id, constraint_type, constraint_name,
                is_satisfied, current_value, required_value, gap_description, checked_at
        """
        return await execute_one(
            query,
            student_id,
            constraint_type,
            constraint_name,
            is_satisfied,
            current_value,
            required_value,
            gap_description,
        )

    # ============================================
    # Prerequisite Rules
    # ============================================

    async def get_prerequisite_rules(self, course_cd: Optional[str] = None) -> List[Dict]:
        """선수과목 규칙 조회"""
        if course_cd:
            query = """
                SELECT
                    p.prerequisite_id as rule_id, p.course_cd, c1.course_nm,
                    p.prerequisite_course_cd as prerequisite_cd, c2.course_nm as prerequisite_nm,
                    p.prerequisite_type as rule_type, 'C' as min_grade
                FROM tb_prerequisite p
                JOIN tb_course c1 ON p.course_cd = c1.course_cd
                JOIN tb_course c2 ON p.prerequisite_course_cd = c2.course_cd
                WHERE p.course_cd = $1
                ORDER BY p.prerequisite_type
            """
            return await execute_query(query, course_cd)
        else:
            query = """
                SELECT
                    p.prerequisite_id as rule_id, p.course_cd, c1.course_nm,
                    p.prerequisite_course_cd as prerequisite_cd, c2.course_nm as prerequisite_nm,
                    p.prerequisite_type as rule_type, 'C' as min_grade
                FROM tb_prerequisite p
                JOIN tb_course c1 ON p.course_cd = c1.course_cd
                JOIN tb_course c2 ON p.prerequisite_course_cd = c2.course_cd
                ORDER BY p.course_cd, p.prerequisite_type
                LIMIT 100
            """
            return await execute_query(query)


# Singleton instance
risk_service = RiskService()
