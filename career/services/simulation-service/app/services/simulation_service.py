from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
import json
import logging

from openai import AsyncOpenAI

from ..database import execute_query, execute_one, execute_scalar, execute_command
from ..config import get_settings
from ..schemas import (
    ScenarioType,
    ScenarioCreate,
    ScenarioResponse,
    ScenarioVariable,
    SimulationResult,
    ComparisonResponse,
    CareerPathSimulation,
    SkillDevelopmentSimulation,
    CourseSelectionSimulation,
    TimelineSimulation,
    SuggestedScenario,
    ScenarioGuide,
    VariableGuide,
    MetricExplanation,
    AIAnalysis,
)

logger = logging.getLogger(__name__)


def _parse_jsonb(data: Any) -> dict:
    """Safely parse JSONB data that might be returned as dict or string."""
    if data is None:
        return {}
    if isinstance(data, dict):
        return data
    if isinstance(data, str):
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return {}
    return {}


class SimulationService:
    def __init__(self):
        self.settings = get_settings()
        self.openai_client = None
        if self.settings.OPENAI_API_KEY:
            self.openai_client = AsyncOpenAI(api_key=self.settings.OPENAI_API_KEY)
    # ============================================
    # Scenario CRUD
    # ============================================

    async def create_scenario(self, data: ScenarioCreate) -> ScenarioResponse:
        # Run simulation
        results = await self._run_simulation(data)

        # Calculate overall impact using magnitude-weighted voting
        # Each result "votes" based on direction and change magnitude:
        #   positive + high change → 0.6~1.0, negative + high change → 0.0~0.4, neutral → 0.5
        # Cap at 300% to spread scores across typical simulation change ranges (avg ~130%)
        if not results:
            overall_score = 0.50
        else:
            votes = []
            for r in results:
                magnitude = min(abs(r.change_percent) if r.change_percent else 0, 300) / 300
                if r.impact_level == "positive":
                    votes.append(0.6 + magnitude * 0.4)
                elif r.impact_level == "negative":
                    votes.append(0.4 - magnitude * 0.4)
                else:
                    votes.append(0.5)
            overall_score = max(0.0, min(1.0, sum(votes) / len(votes)))

        # Generate AI analysis for detailed insights
        ai_analysis = await self._generate_ai_analysis(data, results, overall_score)

        # Use AI analysis summary as recommendation when available, otherwise template fallback
        if ai_analysis and ai_analysis.get("summary"):
            recommendation = ai_analysis["summary"]
        else:
            recommendation = self._generate_recommendation(results, overall_score)

        # Save to database - store variables in base_state, results in predicted_outcomes
        base_state = {"variables": [v.model_dump() for v in data.variables]}
        predicted_outcomes = {
            "results": [r.model_dump() for r in results],
            "recommendation": recommendation,
            "ai_analysis": ai_analysis,  # Include AI analysis in stored data
        }

        # changes stores the simulated values from variables
        changes = {"simulated_changes": [{"name": v.name, "value": v.simulated_value} for v in data.variables]}

        query = """
            INSERT INTO tb_simulation_scenario (
                student_id, scenario_type, title, description,
                base_state, changes, predicted_outcomes, confidence_level
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING scenario_id, ins_dt as created_at
        """
        result = await execute_one(
            query,
            data.student_id,
            data.scenario_type.value,
            data.name,
            data.description,
            json.dumps(base_state),
            json.dumps(changes),
            json.dumps(predicted_outcomes),
            overall_score,
        )

        return ScenarioResponse(
            scenario_id=result["scenario_id"],
            student_id=data.student_id,
            scenario_type=data.scenario_type,
            name=data.name,
            description=data.description,
            variables=data.variables,
            results=results,
            overall_impact_score=overall_score,
            recommendation=recommendation,
            ai_analysis=ai_analysis,  # Include AI analysis in response
            created_at=result["created_at"],
            is_saved=True,
        )

    async def get_scenario(self, scenario_id: UUID) -> Optional[ScenarioResponse]:
        query = """
            SELECT scenario_id, student_id, scenario_type, title, description,
                   base_state, predicted_outcomes, confidence_level, ins_dt as created_at, is_favorite
            FROM tb_simulation_scenario WHERE scenario_id = $1
        """
        row = await execute_one(query, scenario_id)
        if not row:
            return None

        # Extract variables from base_state JSONB (handle both dict and string)
        base_state = _parse_jsonb(row.get("base_state"))
        variables_data = base_state.get("variables", [])

        # Extract results, recommendation, and AI analysis from predicted_outcomes JSONB
        predicted = _parse_jsonb(row.get("predicted_outcomes"))
        results_data = predicted.get("results", [])
        recommendation = predicted.get("recommendation", "")
        ai_analysis = predicted.get("ai_analysis")

        return ScenarioResponse(
            scenario_id=row["scenario_id"],
            student_id=row["student_id"],
            scenario_type=row["scenario_type"],
            name=row["title"],
            description=row["description"],
            variables=[ScenarioVariable(**v) for v in variables_data],
            results=[SimulationResult(**r) for r in results_data],
            overall_impact_score=row["confidence_level"] or 0,
            recommendation=recommendation,
            ai_analysis=ai_analysis,
            created_at=row["created_at"],
            is_saved=row.get("is_favorite", False),
        )

    async def get_all_scenarios(
        self, student_id: Optional[str] = None, scenario_type: Optional[ScenarioType] = None
    ) -> List[ScenarioResponse]:
        """Get all scenarios with optional filtering by student_id and/or scenario_type."""
        conditions = []
        params = []
        param_idx = 1

        if student_id:
            conditions.append(f"student_id = ${param_idx}")
            params.append(student_id)
            param_idx += 1
        if scenario_type:
            conditions.append(f"scenario_type = ${param_idx}")
            params.append(scenario_type.value)
            param_idx += 1

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        query = f"""
            SELECT scenario_id, student_id, scenario_type, title, description,
                   base_state, predicted_outcomes, confidence_level, ins_dt as created_at, is_favorite
            FROM tb_simulation_scenario
            {where_clause}
            ORDER BY ins_dt DESC
        """
        rows = await execute_query(query, *params) if params else await execute_query(query)

        results = []
        for r in rows:
            # Extract variables from base_state JSONB (handle both dict and string)
            base_state = _parse_jsonb(r.get("base_state"))
            variables_data = base_state.get("variables", [])

            # Extract results, recommendation, and AI analysis from predicted_outcomes JSONB
            predicted = _parse_jsonb(r.get("predicted_outcomes"))
            results_data = predicted.get("results", [])
            recommendation = predicted.get("recommendation", "")
            ai_analysis = predicted.get("ai_analysis")

            results.append(ScenarioResponse(
                scenario_id=r["scenario_id"],
                student_id=r["student_id"],
                scenario_type=r["scenario_type"],
                name=r["title"],
                description=r["description"],
                variables=[ScenarioVariable(**v) for v in variables_data],
                results=[SimulationResult(**res) for res in results_data],
                overall_impact_score=r["confidence_level"] or 0,
                recommendation=recommendation,
                ai_analysis=ai_analysis,
                created_at=r["created_at"],
                is_saved=r.get("is_favorite", False),
            ))
        return results

    async def get_student_scenarios(
        self, student_id: str, scenario_type: Optional[ScenarioType] = None
    ) -> List[ScenarioResponse]:
        """Get scenarios for a specific student (calls get_all_scenarios with student_id)."""
        return await self.get_all_scenarios(student_id=student_id, scenario_type=scenario_type)

    async def delete_scenario(self, scenario_id: UUID) -> bool:
        result = await execute_command(
            "DELETE FROM tb_simulation_scenario WHERE scenario_id = $1", scenario_id
        )
        return "DELETE 1" in result

    # ============================================
    # Simulation Engine
    # ============================================

    async def _run_simulation(self, data: ScenarioCreate) -> List[SimulationResult]:
        results = []

        if data.scenario_type == ScenarioType.CAREER_PATH:
            results = await self._simulate_career_path(data)
        elif data.scenario_type == ScenarioType.SKILL_DEVELOPMENT:
            results = await self._simulate_skill_development(data)
        elif data.scenario_type == ScenarioType.COURSE_SELECTION:
            results = await self._simulate_course_selection(data)
        elif data.scenario_type == ScenarioType.OPPORTUNITY:
            results = await self._simulate_opportunity(data)
        else:
            results = await self._simulate_generic(data)

        return results

    async def _simulate_career_path(self, data: ScenarioCreate) -> List[SimulationResult]:
        results = []
        target_role_cd = None
        student_id = data.student_id

        for var in data.variables:
            if var.name == "target_role":
                target_role_cd = var.simulated_value

        if target_role_cd:
            # 1. 현재 학생의 스킬 레벨 조회
            student_skill_query = """
                SELECT ss.skill_cd, ss.current_level, sk.skill_nm
                FROM tb_student_skill ss
                JOIN tb_skill sk ON ss.skill_cd = sk.skill_cd
                WHERE ss.student_id = $1
            """
            student_skills = await execute_query(student_skill_query, student_id)
            student_skill_map = {r["skill_cd"]: r["current_level"] for r in student_skills}

            # 2. 목표 직무의 요구 스킬 조회
            role_skill_query = """
                SELECT rsm.skill_cd, rsm.required_level, rsm.importance, sk.skill_nm
                FROM tb_role_skill_map rsm
                JOIN tb_skill sk ON rsm.skill_cd = sk.skill_cd
                WHERE rsm.role_cd = $1
            """
            role_requirements = await execute_query(role_skill_query, target_role_cd)

            # 3. 준비도 계산 (학생 역량 / 요구 역량)
            if role_requirements:
                total_required = 0
                total_achieved = 0
                skill_gaps = []

                for req in role_requirements:
                    skill_cd = req["skill_cd"]
                    required_level = req["required_level"]
                    importance = req["importance"]

                    # 가중치 적용
                    weight = {"high": 1.5, "medium": 1.0, "low": 0.5}.get(importance, 1.0)
                    weighted_required = required_level * weight
                    total_required += weighted_required

                    student_level = student_skill_map.get(skill_cd, 0)
                    achieved = min(student_level, required_level) * weight
                    total_achieved += achieved

                    # 부족한 스킬 기록
                    if student_level < required_level:
                        skill_gaps.append({
                            "name": req["skill_nm"],
                            "gap": required_level - student_level,
                            "importance": importance
                        })

                # 현재 준비도 계산
                current_readiness = (total_achieved / total_required * 100) if total_required > 0 else 0

                # 시뮬레이션된 준비도 (향후 성장 예측: 스킬 변수 고려)
                simulated_boost = 0
                for var in data.variables:
                    if var.name.startswith("skill_"):
                        # 스킬 향상이 역량에 미치는 영향 추정
                        try:
                            current_level = float(var.current_value) if var.current_value else 1
                            target_level = float(var.simulated_value) if var.simulated_value else current_level
                            simulated_boost += (target_level - current_level) * 2  # 스킬 레벨당 2% 향상
                        except (ValueError, TypeError):
                            pass

                simulated_readiness = min(100, current_readiness + simulated_boost + 5)  # 기본 5% 향상

                results.append(SimulationResult(
                    metric_name="직무 준비도",
                    current_value=round(current_readiness, 1),
                    simulated_value=round(simulated_readiness, 1),
                    change_percent=round(((simulated_readiness - current_readiness) / max(current_readiness, 1)) * 100, 1),
                    impact_level="positive" if simulated_readiness > current_readiness else "neutral",
                    explanation=f"목표 직무에 대한 현재 준비도 {current_readiness:.1f}% → 예상 {simulated_readiness:.1f}%",
                ))

                # 부족한 역량 메트릭 추가
                if skill_gaps:
                    high_priority_gaps = [g for g in skill_gaps if g["importance"] == "high"][:3]
                    results.append(SimulationResult(
                        metric_name="핵심 부족 역량",
                        current_value=len(high_priority_gaps),
                        simulated_value=max(0, len(high_priority_gaps) - 1),
                        change_percent=-round(100 / max(len(high_priority_gaps), 1), 1) if high_priority_gaps else 0,
                        impact_level="positive" if high_priority_gaps else "neutral",
                        explanation=f"중요도 높은 부족 역량: {', '.join([g['name'] for g in high_priority_gaps]) or '없음'}",
                    ))
            else:
                # 직무 요구사항 데이터가 없는 경우 기본값
                results.append(SimulationResult(
                    metric_name="직무 준비도",
                    current_value=50,
                    simulated_value=60,
                    change_percent=20,
                    impact_level="positive",
                    explanation=f"직무 요구사항 데이터 부족. 일반적인 준비도 예측값입니다.",
                ))

        return results

    async def _simulate_skill_development(self, data: ScenarioCreate) -> List[SimulationResult]:
        results = []
        student_id = data.student_id
        total_hours_needed = 0
        total_competency_boost = 0

        # 학생의 현재 스킬 레벨 조회
        student_skills_query = """
            SELECT ss.skill_cd, ss.current_level, sk.skill_nm, sk.difficulty
            FROM tb_student_skill ss
            JOIN tb_skill sk ON ss.skill_cd = sk.skill_cd
            WHERE ss.student_id = $1
        """
        student_skills = await execute_query(student_skills_query, student_id)
        skill_map = {r["skill_cd"]: r for r in student_skills}

        for var in data.variables:
            if "skill" in var.name.lower():
                skill_cd = var.name.replace("skill_", "")
                skill_info = skill_map.get(skill_cd)

                try:
                    current = float(var.current_value) if var.current_value else 1
                    target = float(var.simulated_value) if var.simulated_value else 3
                except (ValueError, TypeError):
                    current = 1
                    target = 3

                # 스킬 정보가 DB에 있으면 사용, 없으면 기본값
                if skill_info:
                    skill_name = skill_info.get("skill_nm", var.name)
                    difficulty = skill_info.get("difficulty", 3)
                    current = skill_info.get("current_level", current)
                else:
                    skill_name = var.name
                    difficulty = 3

                change = ((target - current) / max(current, 1)) * 100
                level_diff = target - current

                # 난이도 기반 학습 시간 계산 (기본 30시간 * 난이도 * 레벨 차이)
                hours_per_level = 30 * difficulty
                hours_for_skill = hours_per_level * level_diff
                total_hours_needed += max(0, hours_for_skill)

                # 역량 점수 기여도 추정
                competency_boost = level_diff * 3  # 스킬 레벨당 3점 역량 향상
                total_competency_boost += competency_boost

                results.append(SimulationResult(
                    metric_name=f"{skill_name} 레벨",
                    current_value=current,
                    simulated_value=target,
                    change_percent=round(change, 1),
                    impact_level="positive" if change > 0 else "neutral",
                    explanation=f"스킬 레벨 {int(current)} → {int(target)} 향상 (예상 학습시간: {int(hours_for_skill)}시간)",
                ))

        # 예상 소요 시간 메트릭
        if total_hours_needed > 0:
            # 주당 학습 시간 변수가 있으면 사용
            hours_per_week = 10  # 기본값
            for var in data.variables:
                if var.name == "hours_per_week":
                    try:
                        hours_per_week = float(var.simulated_value) if var.simulated_value else 10
                    except (ValueError, TypeError):
                        pass

            weeks_needed = total_hours_needed / max(hours_per_week, 1)

            results.append(SimulationResult(
                metric_name="예상 소요 시간",
                current_value=0,
                simulated_value=round(total_hours_needed),
                change_percent=100,
                impact_level="neutral",
                explanation=f"총 {int(total_hours_needed)}시간 학습 필요 (주 {int(hours_per_week)}시간 기준 약 {int(weeks_needed)}주)",
            ))

        # 역량 점수 향상 예측
        if total_competency_boost > 0:
            results.append(SimulationResult(
                metric_name="예상 역량 점수 증가",
                current_value=0,
                simulated_value=round(total_competency_boost, 1),
                change_percent=round(total_competency_boost, 1),
                impact_level="positive",
                explanation=f"스킬 향상으로 인한 전체 역량 점수 약 {total_competency_boost:.1f}점 증가 예상",
            ))

        return results

    async def _simulate_course_selection(self, data: ScenarioCreate) -> List[SimulationResult]:
        results = []
        student_id = data.student_id

        # 1. 학생의 현재 GPA 및 취득 학점 조회
        current_gpa_query = """
            SELECT
                COUNT(*) as course_count,
                COALESCE(AVG(g.grade_point), 0) as current_gpa,
                COALESCE(SUM(c.credits), 0) as total_credits
            FROM tb_enrollment e
            JOIN tb_course_offering co ON e.course_offering_id = co.offering_id
            JOIN tb_course c ON co.course_cd = c.course_cd
            LEFT JOIN tb_grade g ON e.enrollment_id = g.enrollment_id
            WHERE e.student_id = $1
        """
        current_status = await execute_one(current_gpa_query, student_id)
        current_gpa = float(current_status.get("current_gpa", 0) or 0) if current_status else 0
        current_credits = int(current_status.get("total_credits", 0) or 0) if current_status else 0

        total_new_credits = 0
        total_grade_points = 0
        competency_contributions = {}

        # 학점 변환 맵
        grade_point_map = {
            "A+": 4.5, "A": 4.0, "A0": 4.0,
            "B+": 3.5, "B": 3.0, "B0": 3.0,
            "C+": 2.5, "C": 2.0, "C0": 2.0,
            "D+": 1.5, "D": 1.0, "D0": 1.0,
            "F": 0.0
        }

        for var in data.variables:
            if var.name == "course":
                course_cd = var.current_value
                expected_grade = var.simulated_value or "B"

                # 과목 정보 조회
                course_query = """
                    SELECT course_cd, course_nm, credits
                    FROM tb_course
                    WHERE course_cd = $1
                """
                course_info = await execute_one(course_query, course_cd)

                if course_info:
                    credits = float(course_info.get("credits", 3))
                    grade_point = grade_point_map.get(expected_grade, 3.0)
                    total_new_credits += credits
                    total_grade_points += grade_point * credits

                    # 과목-역량 기여도 조회
                    comp_query = """
                        SELECT ccm.competency_cd, ccm.contribution_weight, c.competency_nm
                        FROM tb_course_competency_map ccm
                        JOIN tb_competency c ON ccm.competency_cd = c.competency_cd
                        WHERE ccm.course_cd = $1
                    """
                    comp_contributions = await execute_query(comp_query, course_cd)
                    for comp in comp_contributions:
                        comp_cd = comp["competency_cd"]
                        weight = float(comp.get("contribution_weight", 0) or 0)
                        # 학점에 비례하여 역량 기여도 가중
                        adjusted_weight = weight * (grade_point / 4.0)  # A 기준 최대 기여
                        competency_contributions[comp_cd] = competency_contributions.get(comp_cd, 0) + adjusted_weight

        # 예상 GPA 계산
        if total_new_credits > 0:
            new_gpa_contribution = total_grade_points / total_new_credits
            total_credits_after = current_credits + total_new_credits
            # 가중 평균으로 새 GPA 계산
            if total_credits_after > 0:
                simulated_gpa = ((current_gpa * current_credits) + total_grade_points) / total_credits_after
            else:
                simulated_gpa = new_gpa_contribution

            gpa_change = simulated_gpa - current_gpa
            gpa_change_percent = (gpa_change / max(current_gpa, 0.01)) * 100

            results.append(SimulationResult(
                metric_name="예상 GPA 변화",
                current_value=round(current_gpa, 2),
                simulated_value=round(simulated_gpa, 2),
                change_percent=round(gpa_change_percent, 1),
                impact_level="positive" if gpa_change > 0 else ("negative" if gpa_change < 0 else "neutral"),
                explanation=f"GPA {current_gpa:.2f} → {simulated_gpa:.2f} (변화: {gpa_change:+.2f})",
            ))

            results.append(SimulationResult(
                metric_name="취득 학점",
                current_value=current_credits,
                simulated_value=current_credits + total_new_credits,
                change_percent=round((total_new_credits / max(current_credits, 1)) * 100, 1),
                impact_level="positive",
                explanation=f"{total_new_credits}학점 추가 취득 (총 {current_credits + total_new_credits}학점)",
            ))

        # 역량 기여도 메트릭
        if competency_contributions:
            top_competencies = sorted(competency_contributions.items(), key=lambda x: x[1], reverse=True)[:3]
            total_contribution = sum(competency_contributions.values())
            results.append(SimulationResult(
                metric_name="역량 기여도",
                current_value=0,
                simulated_value=round(total_contribution, 1),
                change_percent=round(total_contribution, 1),
                impact_level="positive" if total_contribution > 0 else "neutral",
                explanation=f"선택 과목으로 역량 점수 약 {total_contribution:.1f}점 향상 예상",
            ))

        return results

    async def _simulate_opportunity(self, data: ScenarioCreate) -> List[SimulationResult]:
        results = []
        student_id = data.student_id

        # 기회 유형별 예상 점수 기준
        opportunity_scores = {
            "internship": {"career": 25, "portfolio": 30, "network": 15},
            "project": {"career": 15, "portfolio": 25, "network": 10},
            "contest": {"career": 20, "portfolio": 20, "network": 5},
            "certification": {"career": 10, "portfolio": 5, "network": 0},
            "research": {"career": 15, "portfolio": 20, "network": 8},
            "club": {"career": 5, "portfolio": 10, "network": 12},
        }

        # 학생의 현재 활동 점수 조회
        current_activities_query = """
            SELECT COUNT(*) as activity_count,
                   SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count
            FROM tb_activity
            WHERE student_id = $1
        """
        current_activities = await execute_one(current_activities_query, student_id)
        completed_count = int(current_activities.get("completed_count", 0) or 0) if current_activities else 0

        # 기본 경력 점수 (완료한 활동 수 기반)
        current_career_score = completed_count * 10

        total_career_boost = 0
        total_portfolio_boost = 0
        total_network_boost = 0

        for var in data.variables:
            if var.name == "opportunity_type":
                opportunity_type = var.simulated_value.lower() if var.simulated_value else "project"
                scores = opportunity_scores.get(opportunity_type, {"career": 10, "portfolio": 10, "network": 5})

                # 참여 기간 변수가 있으면 점수 조정
                duration_months = 3  # 기본값
                for v in data.variables:
                    if v.name == "duration_months":
                        try:
                            duration_months = int(v.simulated_value) if v.simulated_value else 3
                        except (ValueError, TypeError):
                            pass

                # 기간에 따른 점수 조정 (3개월 기준, 최대 2배)
                duration_multiplier = min(2.0, max(0.5, duration_months / 3))

                total_career_boost += scores["career"] * duration_multiplier
                total_portfolio_boost += scores["portfolio"] * duration_multiplier
                total_network_boost += scores["network"] * duration_multiplier

        # 결과 생성
        if total_career_boost > 0:
            results.append(SimulationResult(
                metric_name="경력 점수 증가",
                current_value=round(current_career_score),
                simulated_value=round(current_career_score + total_career_boost),
                change_percent=round((total_career_boost / max(current_career_score, 1)) * 100, 1),
                impact_level="positive",
                explanation=f"참여로 경력 점수 {total_career_boost:.0f}점 향상 예상",
            ))

        if total_portfolio_boost > 0:
            results.append(SimulationResult(
                metric_name="포트폴리오 가치",
                current_value=completed_count * 10,
                simulated_value=round(completed_count * 10 + total_portfolio_boost),
                change_percent=round(total_portfolio_boost, 1),
                impact_level="positive",
                explanation=f"실무 경험으로 포트폴리오 가치 {total_portfolio_boost:.0f}점 증가",
            ))

        if total_network_boost > 0:
            results.append(SimulationResult(
                metric_name="네트워크 확장",
                current_value=0,
                simulated_value=round(total_network_boost),
                change_percent=round(total_network_boost, 1),
                impact_level="positive" if total_network_boost >= 10 else "neutral",
                explanation=f"예상 새로운 연결: 약 {int(total_network_boost)}명",
            ))

        return results

    async def _simulate_generic(self, data: ScenarioCreate) -> List[SimulationResult]:
        return [
            SimulationResult(
                metric_name="영향도",
                current_value=0,
                simulated_value=50,
                change_percent=100,
                impact_level="neutral",
                explanation="시뮬레이션 결과",
            )
        ]

    def _generate_recommendation(self, results: List[SimulationResult], score: float) -> str:
        # score is 0.0-1.0 scale (not 0-100)
        if score > 0.6:
            return "이 시나리오는 전반적으로 긍정적인 영향을 미칩니다. 진행을 권장합니다."
        elif score > 0.4:
            return "이 시나리오는 혼합된 결과를 보입니다. 장단점을 신중히 검토하세요."
        else:
            return "이 시나리오는 부정적인 영향이 우려됩니다. 대안을 고려해보세요."

    # ============================================
    # Scenario Comparison
    # ============================================

    async def compare_scenarios(self, student_id: str, scenario_ids: List[UUID]) -> ComparisonResponse:
        scenarios = []
        for sid in scenario_ids:
            scenario = await self.get_scenario(sid)
            if scenario and scenario.student_id == student_id:
                scenarios.append(scenario)

        if len(scenarios) < 2:
            raise ValueError("At least 2 valid scenarios required for comparison")

        # Build comparison matrix
        all_metrics = set()
        for s in scenarios:
            for r in s.results:
                all_metrics.add(r.metric_name)

        comparison_matrix = {}
        for metric in all_metrics:
            comparison_matrix[metric] = {}
            for s in scenarios:
                value = next((r.simulated_value for r in s.results if r.metric_name == metric), 0)
                comparison_matrix[metric][str(s.scenario_id)] = value

        # Find best scenario
        best_scenario = max(scenarios, key=lambda s: s.overall_impact_score)

        # Save comparison - use comparison_metrics instead of comparison_matrix, store best_scenario_id in ai_analysis
        comparison_id = uuid4()
        ai_analysis = {"best_scenario_id": str(best_scenario.scenario_id)}
        await execute_command("""
            INSERT INTO tb_scenario_comparison (comparison_id, student_id, scenario_ids, comparison_metrics, recommendation, ai_analysis)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, comparison_id, student_id, [str(s) for s in scenario_ids],
            json.dumps(comparison_matrix), f"분석 결과, '{best_scenario.name}' 시나리오가 가장 유리합니다.",
            json.dumps(ai_analysis))

        return ComparisonResponse(
            comparison_id=comparison_id,
            student_id=student_id,
            scenarios=scenarios,
            comparison_matrix=comparison_matrix,
            best_scenario_id=best_scenario.scenario_id,
            recommendation=f"분석 결과, '{best_scenario.name}' 시나리오가 가장 유리합니다.",
            created_at=datetime.now(),
        )

    # ============================================
    # Specialized Simulations
    # ============================================

    async def simulate_career_path(self, request: CareerPathSimulation) -> ScenarioResponse:
        variables = [
            ScenarioVariable(name="target_role", current_value=None, simulated_value=request.target_role_cd),
        ]
        for skill, level in request.current_skills.items():
            variables.append(ScenarioVariable(name=f"skill_{skill}", current_value=level, simulated_value=level + 1))

        return await self.create_scenario(ScenarioCreate(
            student_id=request.student_id,
            scenario_type=ScenarioType.CAREER_PATH,
            name=f"{request.target_role_cd} 진로 시뮬레이션",
            description=f"{request.timeline_months}개월 내 {request.target_role_cd} 달성 시나리오",
            variables=variables,
        ))

    async def simulate_skill_development(self, request: SkillDevelopmentSimulation) -> ScenarioResponse:
        variables = []
        for skill, target in request.target_skills.items():
            variables.append(ScenarioVariable(name=f"skill_{skill}", current_value=1, simulated_value=target))

        return await self.create_scenario(ScenarioCreate(
            student_id=request.student_id,
            scenario_type=ScenarioType.SKILL_DEVELOPMENT,
            name="스킬 개발 시뮬레이션",
            description=f"주당 {request.available_hours_per_week}시간 학습 기준",
            variables=variables,
        ))

    async def simulate_course_selection(self, request: CourseSelectionSimulation) -> ScenarioResponse:
        """과목 선택 시뮬레이션"""
        variables = []
        for course_cd in request.course_codes:
            expected_grade = request.expected_grades.get(course_cd, "B")
            variables.append(ScenarioVariable(
                name="course",
                current_value=course_cd,
                simulated_value=expected_grade,
                impact_description=f"과목 {course_cd} 수강 (예상 학점: {expected_grade})"
            ))

        semester_desc = f" ({request.semester})" if request.semester else ""
        return await self.create_scenario(ScenarioCreate(
            student_id=request.student_id,
            scenario_type=ScenarioType.COURSE_SELECTION,
            name=f"과목 선택 시뮬레이션{semester_desc}",
            description=f"{len(request.course_codes)}개 과목 수강 시 영향 분석",
            variables=variables,
        ))

    async def simulate_timeline(self, request: TimelineSimulation) -> ScenarioResponse:
        """타임라인 시뮬레이션"""
        variables = [
            ScenarioVariable(
                name="timeline_type",
                current_value=request.timeline_type,
                simulated_value=request.timeline_type,
                impact_description=f"목표 유형: {request.timeline_type}"
            ),
            ScenarioVariable(
                name="target_date",
                current_value=str(datetime.now().date()),
                simulated_value=str(request.target_date),
                impact_description=f"목표 날짜: {request.target_date}"
            ),
        ]

        # Add milestones as variables
        for i, milestone in enumerate(request.milestones):
            variables.append(ScenarioVariable(
                name=f"milestone_{i+1}",
                current_value=milestone.get("current", "미달성"),
                simulated_value=milestone.get("target", "달성"),
                impact_description=milestone.get("description", f"마일스톤 {i+1}")
            ))

        return await self.create_scenario(ScenarioCreate(
            student_id=request.student_id,
            scenario_type=ScenarioType.TIMELINE,
            name=f"타임라인 시뮬레이션 ({request.timeline_type})",
            description=f"{request.target_date}까지 목표 달성 경로 분석",
            variables=variables,
        ))

    async def save_scenario(self, scenario_id: UUID) -> Optional[ScenarioResponse]:
        """시나리오를 즐겨찾기로 저장"""
        result = await execute_command("""
            UPDATE tb_simulation_scenario
            SET is_favorite = true, upd_dt = NOW()
            WHERE scenario_id = $1
        """, scenario_id)

        if "UPDATE 1" in result:
            return await self.get_scenario(scenario_id)
        return None

    async def get_suggested_scenarios(self, student_id: str) -> List[SuggestedScenario]:
        """학년별 맞춤 추천 시나리오 생성 - 실제 취업시장 데이터 기반"""
        # 학생 데이터 조회
        student_data = await self._get_student_data_for_ai(student_id)

        # Debug logging
        logger.info(f"[AI Suggestions] student_id={student_id}")
        logger.info(f"[AI Suggestions] student_data exists: {bool(student_data)}")

        # 학년 정보 추출 (DB에서 가져오기 우선, 없으면 student_id에서 추론)
        current_grade = 3  # 기본값
        if student_data and student_data.get('student'):
            # student_data는 nested 구조: {"student": {...}, "recent_courses": [...], ...}
            db_grade = student_data['student'].get('current_grade')
            if db_grade is not None:
                try:
                    current_grade = int(db_grade)
                except (ValueError, TypeError):
                    current_grade = 3
            logger.info(f"[AI Suggestions] Grade from DB: {current_grade}")
        else:
            # student_id에서 입학년도 추론 (예: 20231001 -> 2023년 입학)
            try:
                if student_id and len(student_id) >= 4:
                    admission_year = int(student_id[:4])
                    current_year = 2025  # 현재 연도
                    current_grade = min(4, max(1, current_year - admission_year + 1))
                    logger.info(f"[AI Suggestions] Inferred grade from student_id: {current_grade}")
            except (ValueError, TypeError):
                pass

        # 항상 학년별 맞춤 시나리오 반환 (실제 취업시장 데이터 기반으로 큐레이션됨)
        logger.info(f"[AI Suggestions] Returning curated scenarios for grade {current_grade}")
        return self._get_default_suggestions(current_grade)

    async def _get_student_data_for_ai(self, student_id: str) -> Dict[str, Any]:
        """AI 분석을 위한 학생 데이터 수집"""
        try:
            # 학생 기본 정보 (gpa, total_credits 컬럼 없음 - 스키마 확인 필요)
            student_query = """
                SELECT s.student_id, s.student_nm, s.career_goal, s.current_grade,
                       d.department_nm, s.current_semester
                FROM tb_student s
                LEFT JOIN tb_department d ON s.department_cd = d.department_cd
                WHERE s.student_id = $1
            """
            student = await execute_one(student_query, student_id)
            if not student:
                return {}

            # 최근 수강 과목 (tb_enrollment.course_offering_id -> tb_course_offering -> tb_course)
            enrollments_query = """
                SELECT c.course_nm, g.grade_letter, c.credits
                FROM tb_enrollment e
                JOIN tb_course_offering co ON e.course_offering_id = co.offering_id
                JOIN tb_course c ON co.course_cd = c.course_cd
                LEFT JOIN tb_grade g ON e.enrollment_id = g.enrollment_id
                WHERE e.student_id = $1
                ORDER BY e.ins_dt DESC
                LIMIT 5
            """
            enrollments = await execute_query(enrollments_query, student_id)

            # 학생 스킬 (current_level 컬럼 사용)
            skills_query = """
                SELECT sk.skill_nm, ss.current_level as skill_level
                FROM tb_student_skill ss
                JOIN tb_skill sk ON ss.skill_cd = sk.skill_cd
                WHERE ss.student_id = $1
                ORDER BY ss.current_level DESC
                LIMIT 5
            """
            skills = await execute_query(skills_query, student_id)

            # 활동 내역
            activities_query = """
                SELECT activity_type, title, status
                FROM tb_activity
                WHERE student_id = $1
                ORDER BY ins_dt DESC
                LIMIT 3
            """
            activities = await execute_query(activities_query, student_id)

            return {
                "student": dict(student) if student else {},
                "recent_courses": [dict(e) for e in enrollments] if enrollments else [],
                "top_skills": [dict(s) for s in skills] if skills else [],
                "recent_activities": [dict(a) for a in activities] if activities else [],
            }
        except Exception as e:
            logger.error(f"Failed to get student data: {e}")
            return {}

    async def _generate_ai_suggestions(
        self, student_id: str, student_data: Dict[str, Any]
    ) -> List[SuggestedScenario]:
        """GPT를 사용하여 맞춤 시나리오 추천 생성"""
        system_prompt = """당신은 대학생 커리어 개발 전문 AI 상담사입니다.
학생의 현재 상황을 분석하여 가장 유용한 시뮬레이션 시나리오를 추천합니다.

다음 JSON 형식으로 정확히 4개의 추천 시나리오를 응답하세요:
[
  {
    "scenario_type": "career_path|skill_development|course_selection|opportunity|timeline",
    "title": "시나리오 제목 (20자 이내)",
    "description": "시나리오 설명 (50자 이내)",
    "reason": "이 시나리오를 추천하는 개인화된 이유 (학생 데이터 기반)",
    "variables": [
      {"name": "변수명", "current_value": "현재값", "simulated_value": "시뮬레이션값"}
    ]
  }
]

시나리오 유형 설명:
- career_path: 진로/직무 준비도 분석
- skill_development: 스킬 향상 효과 예측
- course_selection: 수강 과목 영향 분석
- opportunity: 인턴십/프로젝트/대회 참여 효과
- timeline: 시간별 성장 경로 예측

중요: 학생의 실제 데이터를 분석하여 개인화된 추천을 제공하세요.
- 진로 목표가 있으면 그에 맞는 시나리오 추천
- 부족한 스킬이 있으면 스킬 개발 시나리오 추천
- 학점이 낮으면 과목 선택 시나리오 추천"""

        student = student_data.get("student", {})
        courses = student_data.get("recent_courses", [])
        skills = student_data.get("top_skills", [])
        activities = student_data.get("recent_activities", [])

        user_prompt = f"""학생 정보:
- 이름: {student.get('student_nm', '학생')}
- 학과: {student.get('department_nm', '미정')}
- 학년: {student.get('current_grade', 3)}학년
- 학기: {student.get('current_semester', 1)}학기
- 진로 목표: {student.get('career_goal', '미설정')}

최근 수강 과목:
{json.dumps(courses, ensure_ascii=False, indent=2) if courses else '정보 없음'}

보유 스킬:
{json.dumps(skills, ensure_ascii=False, indent=2) if skills else '정보 없음'}

최근 활동:
{json.dumps(activities, ensure_ascii=False, indent=2) if activities else '정보 없음'}

위 학생에게 가장 유용한 4개의 시뮬레이션 시나리오를 추천해주세요."""

        try:
            response = await self.openai_client.chat.completions.create(
                model=self.settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.settings.TEMPERATURE,
                max_tokens=2000,
            )

            content = response.choices[0].message.content

            # Parse JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            suggestions_data = json.loads(content.strip())

            # Convert to SuggestedScenario objects
            suggestions = []
            for s in suggestions_data:
                try:
                    scenario_type = ScenarioType(s["scenario_type"])
                    variables = [
                        ScenarioVariable(
                            name=v["name"],
                            current_value=v.get("current_value", ""),
                            simulated_value=v.get("simulated_value", ""),
                        )
                        for v in s.get("variables", [])
                    ]
                    suggestions.append(SuggestedScenario(
                        scenario_type=scenario_type,
                        title=s["title"],
                        description=s["description"],
                        reason=s["reason"],
                        variables=variables,
                    ))
                except (KeyError, ValueError) as e:
                    logger.warning(f"Invalid suggestion format: {e}")
                    continue

            logger.info(f"Generated {len(suggestions)} AI suggestions for student {student_id}")
            return suggestions

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT response: {e}")
            return []
        except Exception as e:
            logger.error(f"GPT API call failed: {e}")
            return []

    def _get_default_suggestions(self, grade: int = 3) -> List[SuggestedScenario]:
        """학년별 맞춤 추천 시나리오 (GPT 실패 시 fallback) - 실제 취업시장 데이터 기반"""

        # ============================================
        # 1학년 시나리오 (2025년 입학 - 기초 탐색 단계)
        # ============================================
        grade_1_scenarios = [
            SuggestedScenario(
                scenario_type=ScenarioType.COURSE_SELECTION,
                title="📚 1학년 교양필수 최적 조합 분석",
                description="교양필수 과목 수강 순서와 조합이 GPA에 미치는 영향을 분석합니다. 평균 1학년 GPA 3.2 목표",
                reason="1학년 GPA가 장학금과 향후 취업에 큰 영향을 미칩니다. 전략적인 수강 신청이 필요합니다.",
                variables=[
                    ScenarioVariable(name="course", current_value="글쓰기", simulated_value="A"),
                    ScenarioVariable(name="course", current_value="영어1", simulated_value="B+"),
                    ScenarioVariable(name="course", current_value="보건학개론", simulated_value="A"),
                ]
            ),
            SuggestedScenario(
                scenario_type=ScenarioType.CAREER_PATH,
                title="🔍 보건관리학과 진로 탐색 시뮬레이션",
                description="보건관리학과 졸업 후 가능한 7개 진로(공무원, 공기업, 병원, 연구소 등)를 비교 분석합니다.",
                reason="1학년 때 진로를 탐색하면 남은 3년을 효과적으로 준비할 수 있습니다.",
                variables=[
                    ScenarioVariable(name="interest_area", current_value="미정", simulated_value="보건행정"),
                    ScenarioVariable(name="priority", current_value="미정", simulated_value="안정성"),
                ]
            ),
            SuggestedScenario(
                scenario_type=ScenarioType.OPPORTUNITY,
                title="🤝 1학년 멘토링 프로그램 참여 효과",
                description="선배 멘토링 프로그램 참여가 학업 적응과 진로 설정에 미치는 영향을 분석합니다.",
                reason="멘토링 참여 학생의 평균 GPA가 0.3점 높고, 진로 결정 시기가 1년 빠릅니다.",
                variables=[
                    ScenarioVariable(name="opportunity_type", current_value="없음", simulated_value="mentoring"),
                    ScenarioVariable(name="duration_months", current_value="0", simulated_value="6"),
                ]
            ),
            SuggestedScenario(
                scenario_type=ScenarioType.SKILL_DEVELOPMENT,
                title="💻 기초 컴퓨터 활용 능력 향상",
                description="엑셀, 워드, PPT 등 OA 스킬 향상이 학업과 취업에 미치는 영향을 분석합니다.",
                reason="보건행정 직무의 80%가 문서 작업. 1학년 때 OA 스킬을 익히면 과제 효율이 2배 향상됩니다.",
                variables=[
                    ScenarioVariable(name="skill_excel", current_value="1", simulated_value="3"),
                    ScenarioVariable(name="skill_ppt", current_value="1", simulated_value="3"),
                    ScenarioVariable(name="hours_per_week", current_value="0", simulated_value="5"),
                ]
            ),
            SuggestedScenario(
                scenario_type=ScenarioType.TIMELINE,
                title="📅 1학년 학기별 목표 설정",
                description="1학년 1학기~2학기 동안의 학업/활동/진로탐색 계획을 수립합니다.",
                reason="목표가 있는 1학년은 졸업 시 취업률이 25% 높습니다.",
                variables=[
                    ScenarioVariable(name="timeline_type", current_value="", simulated_value="academic_year"),
                    ScenarioVariable(name="target_gpa", current_value="0", simulated_value="3.5"),
                    ScenarioVariable(name="target_activity", current_value="0", simulated_value="2"),
                ]
            ),
            SuggestedScenario(
                scenario_type=ScenarioType.OPPORTUNITY,
                title="🏫 보건관리학과 학술동아리 가입 효과",
                description="전공 관련 학술동아리 활동이 전공 이해도와 인맥 형성에 미치는 영향을 분석합니다.",
                reason="학술동아리 활동 경험은 자기소개서 핵심 소재가 됩니다. 선배 네트워크도 중요합니다.",
                variables=[
                    ScenarioVariable(name="opportunity_type", current_value="없음", simulated_value="club"),
                    ScenarioVariable(name="club_type", current_value="", simulated_value="academic"),
                    ScenarioVariable(name="participation_level", current_value="", simulated_value="active"),
                ]
            ),
        ]

        # ============================================
        # 2학년 시나리오 (2024년 입학 - 전문성 심화 단계)
        # ============================================
        grade_2_scenarios = [
            SuggestedScenario(
                scenario_type=ScenarioType.COURSE_SELECTION,
                title="📚 2학년 전공심화 과목 선택 전략",
                description="역학, 보건통계학, 보건정책학 등 핵심 전공과목 수강 조합을 분석합니다.",
                reason="2학년 전공과목 성적이 취업 서류 통과의 핵심입니다. 전공 GPA 3.5 이상을 목표로 하세요.",
                variables=[
                    ScenarioVariable(name="course", current_value="역학", simulated_value="A"),
                    ScenarioVariable(name="course", current_value="보건통계학", simulated_value="A"),
                    ScenarioVariable(name="course", current_value="보건정책학", simulated_value="B+"),
                ]
            ),
            SuggestedScenario(
                scenario_type=ScenarioType.SKILL_DEVELOPMENT,
                title="📊 SPSS/R 통계분석 역량 강화",
                description="보건통계 도구(SPSS, R) 습득이 연구/취업 경쟁력에 미치는 영향을 분석합니다.",
                reason="심평원, 질병관리청, 건강보험공단 모두 통계분석 역량을 필수로 요구합니다.",
                variables=[
                    ScenarioVariable(name="skill_spss", current_value="1", simulated_value="4"),
                    ScenarioVariable(name="skill_r", current_value="0", simulated_value="3"),
                    ScenarioVariable(name="hours_per_week", current_value="0", simulated_value="8"),
                ]
            ),
            SuggestedScenario(
                scenario_type=ScenarioType.OPPORTUNITY,
                title="🏥 2학년 여름방학 병원 인턴 체험",
                description="대학병원 원무과/QI팀 인턴 체험이 진로 결정과 취업에 미치는 영향을 분석합니다.",
                reason="병원 인턴 경험자의 의료기관 취업률이 40% 높습니다. 2학년이 적기입니다.",
                variables=[
                    ScenarioVariable(name="opportunity_type", current_value="없음", simulated_value="internship"),
                    ScenarioVariable(name="institution_type", current_value="", simulated_value="hospital"),
                    ScenarioVariable(name="duration_weeks", current_value="0", simulated_value="4"),
                ]
            ),
            SuggestedScenario(
                scenario_type=ScenarioType.CAREER_PATH,
                title="🎯 보건직 공무원 vs 공기업 비교 분석",
                description="보건직 9급 공무원과 건강보험공단/심평원 취업 경로를 비교 분석합니다.",
                reason="2학년 때 목표를 정하면 3학년부터 집중 준비가 가능합니다.",
                variables=[
                    ScenarioVariable(name="path_1", current_value="", simulated_value="보건직공무원"),
                    ScenarioVariable(name="path_2", current_value="", simulated_value="건강보험공단"),
                    ScenarioVariable(name="priority", current_value="", simulated_value="연봉"),
                ]
            ),
            SuggestedScenario(
                scenario_type=ScenarioType.OPPORTUNITY,
                title="📜 보건교육사 3급 자격증 취득 효과",
                description="보건교육사 3급 자격증 취득이 취업 경쟁력에 미치는 영향을 분석합니다.",
                reason="보건교육사는 보건소, 건강증진개발원 취업 시 가산점. 2학년 때 취득하면 여유롭습니다.",
                variables=[
                    ScenarioVariable(name="certification", current_value="없음", simulated_value="보건교육사3급"),
                    ScenarioVariable(name="study_months", current_value="0", simulated_value="6"),
                    ScenarioVariable(name="expected_score", current_value="0", simulated_value="75"),
                ]
            ),
            SuggestedScenario(
                scenario_type=ScenarioType.TIMELINE,
                title="📅 2학년 취업 준비 로드맵",
                description="2학년 동안 갖춰야 할 스펙과 경험의 타임라인을 설계합니다.",
                reason="2학년은 기초→심화 전환기. 체계적인 계획으로 3학년 취업 준비에 앞서가세요.",
                variables=[
                    ScenarioVariable(name="timeline_type", current_value="", simulated_value="preparation"),
                    ScenarioVariable(name="target_cert", current_value="0", simulated_value="1"),
                    ScenarioVariable(name="target_intern", current_value="0", simulated_value="1"),
                ]
            ),
        ]

        # ============================================
        # 3학년 시나리오 (2023년 입학 - 취업 준비 단계)
        # ============================================
        grade_3_scenarios = [
            SuggestedScenario(
                scenario_type=ScenarioType.CAREER_PATH,
                title="🏥 보건직 공무원 준비도 분석",
                description="2026년 보건직 공무원 합격을 위한 현재 준비 상태를 분석합니다. 평균 경쟁률 15:1, 예상 연봉 2,800만원~",
                reason="보건관리학과 졸업생 취업률 1위 직종. 3학년부터 본격 준비가 필요합니다.",
                variables=[
                    ScenarioVariable(name="target_role", current_value="미정", simulated_value="보건직공무원"),
                    ScenarioVariable(name="target_exam", current_value="미응시", simulated_value="9급보건직"),
                    ScenarioVariable(name="study_months", current_value="0", simulated_value="12"),
                ]
            ),
            SuggestedScenario(
                scenario_type=ScenarioType.CAREER_PATH,
                title="🏢 건강보험심사평가원 취업 시뮬레이션",
                description="심평원 신입 공채 합격 가능성을 분석합니다. NCS 기반 채용, 평균 연봉 4,500만원",
                reason="보건행정 분야 최고 대우의 공공기관. 하반기 공채 지원을 목표로 준비하세요.",
                variables=[
                    ScenarioVariable(name="target_role", current_value="미정", simulated_value="심사평가원"),
                    ScenarioVariable(name="ncs_score", current_value="0", simulated_value="80"),
                    ScenarioVariable(name="relevant_cert", current_value="0개", simulated_value="보험심사평가사"),
                ]
            ),
            SuggestedScenario(
                scenario_type=ScenarioType.OPPORTUNITY,
                title="🏭 산업안전보건 인턴십 효과 분석",
                description="대기업 안전보건팀 인턴십 참여 시 취업 경쟁력 변화를 예측합니다.",
                reason="산업안전보건법 강화로 기업 수요 급증. 삼성/SK/현대 모두 채용 확대 중입니다.",
                variables=[
                    ScenarioVariable(name="opportunity_type", current_value="없음", simulated_value="internship"),
                    ScenarioVariable(name="company_type", current_value="", simulated_value="대기업"),
                    ScenarioVariable(name="duration_months", current_value="0", simulated_value="6"),
                ]
            ),
            SuggestedScenario(
                scenario_type=ScenarioType.SKILL_DEVELOPMENT,
                title="📊 보건통계 심화 역량 강화 시뮬레이션",
                description="SPSS/R/Python 통계분석 스킬 고급 과정 이수가 취업에 미치는 영향을 분석합니다.",
                reason="데이터 분석 역량은 공공기관/연구소 취업의 핵심 차별화 요소입니다.",
                variables=[
                    ScenarioVariable(name="skill_statistics", current_value="2", simulated_value="4"),
                    ScenarioVariable(name="skill_python", current_value="1", simulated_value="3"),
                    ScenarioVariable(name="hours_per_week", current_value="0", simulated_value="10"),
                ]
            ),
            SuggestedScenario(
                scenario_type=ScenarioType.COURSE_SELECTION,
                title="📚 3학년 졸업요건 + 취업역량 수강 전략",
                description="남은 전공필수와 취업에 도움되는 과목을 함께 분석합니다.",
                reason="졸업요건 충족과 취업 경쟁력 향상을 동시에 달성해야 합니다.",
                variables=[
                    ScenarioVariable(name="course", current_value="보건프로그램개발및평가", simulated_value="A"),
                    ScenarioVariable(name="course", current_value="보건의료법규", simulated_value="A"),
                    ScenarioVariable(name="course", current_value="캡스톤디자인", simulated_value="A"),
                ]
            ),
            SuggestedScenario(
                scenario_type=ScenarioType.TIMELINE,
                title="🎯 졸업 전 취업 타임라인 설계",
                description="3학년~4학년 동안의 최적 취업 준비 로드맵을 생성합니다.",
                reason="체계적인 준비 계획으로 취업 성공률을 높일 수 있습니다. D-18개월 남았습니다.",
                variables=[
                    ScenarioVariable(name="timeline_type", current_value="", simulated_value="job_ready"),
                    ScenarioVariable(name="target_date", current_value="", simulated_value="2026-08-31"),
                    ScenarioVariable(name="target_role", current_value="", simulated_value="보건직공무원"),
                ]
            ),
        ]

        # ============================================
        # 4학년 시나리오 (취업 마무리 단계)
        # ============================================
        grade_4_scenarios = [
            SuggestedScenario(
                scenario_type=ScenarioType.CAREER_PATH,
                title="🎯 상반기 공채 집중 지원 전략",
                description="건강보험공단, 심평원, 질병관리청 상반기 공채 동시 준비 전략을 분석합니다.",
                reason="4학년 상반기가 마지막 기회입니다. 복수 지원으로 합격 확률을 높이세요.",
                variables=[
                    ScenarioVariable(name="target_1", current_value="", simulated_value="건강보험공단"),
                    ScenarioVariable(name="target_2", current_value="", simulated_value="심평원"),
                    ScenarioVariable(name="target_3", current_value="", simulated_value="질병관리청"),
                ]
            ),
            SuggestedScenario(
                scenario_type=ScenarioType.OPPORTUNITY,
                title="💼 졸업 전 현장실습 취업 연계",
                description="4학년 현장실습이 정규직 전환에 미치는 영향을 분석합니다.",
                reason="현장실습 참여자의 30%가 해당 기관에 정규직 채용됩니다.",
                variables=[
                    ScenarioVariable(name="opportunity_type", current_value="없음", simulated_value="field_training"),
                    ScenarioVariable(name="institution_type", current_value="", simulated_value="public_health"),
                    ScenarioVariable(name="conversion_target", current_value="no", simulated_value="yes"),
                ]
            ),
            SuggestedScenario(
                scenario_type=ScenarioType.SKILL_DEVELOPMENT,
                title="📝 NCS 직업기초능력 집중 향상",
                description="공공기관 NCS 시험 대비 역량 강화 효과를 분석합니다.",
                reason="NCS 점수가 당락을 결정합니다. 의사소통, 수리능력, 문제해결 집중 학습이 필요합니다.",
                variables=[
                    ScenarioVariable(name="skill_ncs", current_value="60", simulated_value="85"),
                    ScenarioVariable(name="study_hours", current_value="0", simulated_value="200"),
                    ScenarioVariable(name="mock_tests", current_value="0", simulated_value="20"),
                ]
            ),
            SuggestedScenario(
                scenario_type=ScenarioType.TIMELINE,
                title="⏰ D-6개월 취업 완료 로드맵",
                description="졸업 전 6개월 동안의 집중 취업 준비 일정을 수립합니다.",
                reason="시간이 촉박합니다. 우선순위를 정하고 효율적으로 준비하세요.",
                variables=[
                    ScenarioVariable(name="timeline_type", current_value="", simulated_value="final_sprint"),
                    ScenarioVariable(name="target_date", current_value="", simulated_value="2026-02-28"),
                    ScenarioVariable(name="applications", current_value="0", simulated_value="10"),
                ]
            ),
            SuggestedScenario(
                scenario_type=ScenarioType.CAREER_PATH,
                title="🏥 민간 병원 취업 대안 분석",
                description="대학병원/종합병원 원무과 취업 가능성과 조건을 분석합니다.",
                reason="공공기관 불합격 시 민간 병원도 좋은 대안입니다. 연봉 3,000~3,500만원.",
                variables=[
                    ScenarioVariable(name="target_role", current_value="", simulated_value="병원원무"),
                    ScenarioVariable(name="hospital_type", current_value="", simulated_value="대학병원"),
                    ScenarioVariable(name="location", current_value="", simulated_value="수도권"),
                ]
            ),
            SuggestedScenario(
                scenario_type=ScenarioType.COURSE_SELECTION,
                title="📚 졸업학점 마무리 전략",
                description="남은 졸업요건 충족과 학점 관리 최종 전략을 분석합니다.",
                reason="졸업학점 미달로 취업이 취소되는 경우가 있습니다. 꼼꼼히 확인하세요.",
                variables=[
                    ScenarioVariable(name="remaining_credits", current_value="15", simulated_value="0"),
                    ScenarioVariable(name="target_gpa", current_value="3.5", simulated_value="3.5"),
                    ScenarioVariable(name="courses_count", current_value="5", simulated_value="5"),
                ]
            ),
        ]

        # 학년에 따라 적절한 시나리오 반환
        grade_scenarios = {
            1: grade_1_scenarios,
            2: grade_2_scenarios,
            3: grade_3_scenarios,
            4: grade_4_scenarios,
        }

        return grade_scenarios.get(grade, grade_3_scenarios)

    # ============================================
    # Scenario Guides (How to use each scenario type)
    # ============================================

    def get_scenario_guide(self, scenario_type: ScenarioType) -> ScenarioGuide:
        """시나리오 유형별 상세 가이드 반환"""
        guides = {
            ScenarioType.CAREER_PATH: ScenarioGuide(
                scenario_type="career_path",
                title="진로 경로 시뮬레이션",
                description="목표 직무에 대한 현재 준비도를 분석하고, 필요한 스킬과 역량을 예측합니다.",
                how_it_works="""
                1. 학생의 현재 스킬, 역량, 수강 이력을 분석합니다.
                2. 목표 직무에 필요한 요구사항과 비교합니다.
                3. 현재 준비도(%)와 부족한 영역을 계산합니다.
                4. AI가 최적의 준비 경로를 제안합니다.
                """,
                steps=[
                    "1단계: 목표 직무 선택",
                    "2단계: 현재 보유 스킬 확인 (자동 로드)",
                    "3단계: 시뮬레이션 실행",
                    "4단계: 결과 분석 및 AI 추천 확인",
                ],
                variables=[
                    VariableGuide(
                        name="target_role",
                        label="목표 직무",
                        description="희망하는 직무/직업을 선택하세요",
                        input_type="select",
                        options=[
                            {"value": "software_engineer", "label": "소프트웨어 엔지니어"},
                            {"value": "data_scientist", "label": "데이터 사이언티스트"},
                            {"value": "product_manager", "label": "프로덕트 매니저"},
                            {"value": "backend_developer", "label": "백엔드 개발자"},
                            {"value": "frontend_developer", "label": "프론트엔드 개발자"},
                            {"value": "devops_engineer", "label": "DevOps 엔지니어"},
                            {"value": "security_analyst", "label": "보안 분석가"},
                        ],
                        required=True,
                    ),
                    VariableGuide(
                        name="timeline_months",
                        label="목표 기간 (개월)",
                        description="목표 달성까지 예상되는 기간",
                        input_type="number",
                        default_value=24,
                        min_value=6,
                        max_value=48,
                        required=False,
                    ),
                ],
                expected_metrics=[
                    MetricExplanation(
                        metric_name="직무 준비도",
                        description="목표 직무에 대한 현재 준비 상태",
                        unit="%",
                        interpretation="높을수록 목표 직무에 가까움. 70% 이상이면 지원 가능 수준",
                        good_threshold=70.0,
                        warning_threshold=40.0,
                    ),
                    MetricExplanation(
                        metric_name="스킬 매칭률",
                        description="필요 스킬 중 보유한 스킬 비율",
                        unit="%",
                        interpretation="목표 직무에 필요한 스킬 중 얼마나 보유했는지",
                        good_threshold=60.0,
                        warning_threshold=30.0,
                    ),
                    MetricExplanation(
                        metric_name="예상 준비 기간",
                        description="목표 달성까지 예상 소요 시간",
                        unit="개월",
                        interpretation="현재 수준에서 목표 도달까지 필요한 시간",
                        good_threshold=12.0,
                        warning_threshold=24.0,
                    ),
                ],
                tips=[
                    "현재 보유 스킬이 정확할수록 시뮬레이션 결과가 정확합니다.",
                    "목표 직무가 명확하지 않다면, 여러 직무로 시뮬레이션을 비교해보세요.",
                    "결과의 '부족한 역량'을 스킬 개발 시나리오와 연계하면 효과적입니다.",
                ],
            ),
            ScenarioType.SKILL_DEVELOPMENT: ScenarioGuide(
                scenario_type="skill_development",
                title="스킬 개발 시뮬레이션",
                description="특정 스킬을 향상시켰을 때 역량 점수 변화와 소요 시간을 예측합니다.",
                how_it_works="""
                1. 현재 스킬 레벨을 확인합니다.
                2. 목표 레벨과의 차이를 분석합니다.
                3. 학습 시간과 난이도를 고려하여 소요 시간을 계산합니다.
                4. 역량 점수 변화를 예측합니다.
                """,
                steps=[
                    "1단계: 향상시킬 스킬 선택",
                    "2단계: 목표 레벨 설정 (1-5)",
                    "3단계: 주당 학습 가능 시간 입력",
                    "4단계: 시뮬레이션 실행",
                ],
                variables=[
                    VariableGuide(
                        name="skill",
                        label="목표 스킬",
                        description="향상시키고 싶은 스킬을 선택하세요",
                        input_type="multi-select",
                        options=[
                            {"value": "python", "label": "Python 프로그래밍"},
                            {"value": "java", "label": "Java 프로그래밍"},
                            {"value": "sql", "label": "SQL/데이터베이스"},
                            {"value": "web_dev", "label": "웹 개발"},
                            {"value": "machine_learning", "label": "머신러닝"},
                            {"value": "cloud", "label": "클라우드 컴퓨팅"},
                            {"value": "project_mgmt", "label": "프로젝트 관리"},
                        ],
                        required=True,
                    ),
                    VariableGuide(
                        name="target_level",
                        label="목표 레벨",
                        description="도달하고자 하는 스킬 레벨 (1: 입문 ~ 5: 전문가)",
                        input_type="select",
                        options=[
                            {"value": 2, "label": "레벨 2 (기초)"},
                            {"value": 3, "label": "레벨 3 (중급)"},
                            {"value": 4, "label": "레벨 4 (고급)"},
                            {"value": 5, "label": "레벨 5 (전문가)"},
                        ],
                        default_value=3,
                        required=True,
                    ),
                    VariableGuide(
                        name="hours_per_week",
                        label="주당 학습 시간",
                        description="스킬 개발에 투자 가능한 주당 시간",
                        input_type="number",
                        default_value=10,
                        min_value=1,
                        max_value=40,
                        required=True,
                    ),
                ],
                expected_metrics=[
                    MetricExplanation(
                        metric_name="스킬 레벨 변화",
                        description="현재 레벨에서 목표 레벨로의 변화",
                        unit="레벨",
                        interpretation="레벨 1 상승당 평균 40시간 학습 필요",
                        good_threshold=2.0,
                        warning_threshold=0.0,
                    ),
                    MetricExplanation(
                        metric_name="예상 소요 시간",
                        description="목표 레벨 도달까지 필요한 총 학습 시간",
                        unit="시간",
                        interpretation="주당 학습 시간으로 나누면 소요 주 계산 가능",
                        good_threshold=80.0,
                        warning_threshold=200.0,
                    ),
                    MetricExplanation(
                        metric_name="역량 점수 증가",
                        description="스킬 향상에 따른 전체 역량 점수 변화",
                        unit="점",
                        interpretation="높을수록 취업/진로에 긍정적 영향",
                        good_threshold=10.0,
                        warning_threshold=3.0,
                    ),
                ],
                tips=[
                    "한 번에 너무 많은 스킬보다 2-3개에 집중하는 것이 효과적입니다.",
                    "현실적인 주당 학습 시간을 입력해야 정확한 예측이 가능합니다.",
                    "목표 직무에 필요한 핵심 스킬을 우선적으로 선택하세요.",
                ],
            ),
            ScenarioType.COURSE_SELECTION: ScenarioGuide(
                scenario_type="course_selection",
                title="수강 과목 시뮬레이션",
                description="특정 과목들을 수강했을 때 학점, 역량, 졸업 요건에 미치는 영향을 분석합니다.",
                how_it_works="""
                1. 선택한 과목들의 정보를 조회합니다.
                2. 예상 학점으로 GPA 변화를 계산합니다.
                3. 과목별 역량 기여도를 분석합니다.
                4. 졸업 요건 충족 현황을 업데이트합니다.
                """,
                steps=[
                    "1단계: 수강 예정 과목 선택",
                    "2단계: 과목별 예상 학점 입력",
                    "3단계: 시뮬레이션 실행",
                    "4단계: GPA 변화 및 역량 영향 확인",
                ],
                variables=[
                    VariableGuide(
                        name="courses",
                        label="수강 과목",
                        description="다음 학기 수강할 과목들을 선택하세요",
                        input_type="multi-select",
                        required=True,
                    ),
                    VariableGuide(
                        name="expected_grade",
                        label="예상 학점",
                        description="각 과목에서 예상되는 학점",
                        input_type="select",
                        options=[
                            {"value": "A+", "label": "A+ (4.5)"},
                            {"value": "A", "label": "A (4.0)"},
                            {"value": "B+", "label": "B+ (3.5)"},
                            {"value": "B", "label": "B (3.0)"},
                            {"value": "C+", "label": "C+ (2.5)"},
                            {"value": "C", "label": "C (2.0)"},
                        ],
                        default_value="B+",
                        required=True,
                    ),
                ],
                expected_metrics=[
                    MetricExplanation(
                        metric_name="예상 GPA 변화",
                        description="수강 후 예상되는 GPA 변화량",
                        unit="점",
                        interpretation="양수면 GPA 상승, 음수면 하락",
                        good_threshold=0.1,
                        warning_threshold=-0.1,
                    ),
                    MetricExplanation(
                        metric_name="총 취득 학점",
                        description="이번 학기 취득 예정 학점 수",
                        unit="학점",
                        interpretation="일반적으로 18학점 내외가 적정",
                        good_threshold=18.0,
                        warning_threshold=12.0,
                    ),
                    MetricExplanation(
                        metric_name="졸업 요건 충족률",
                        description="졸업에 필요한 학점 충족 비율",
                        unit="%",
                        interpretation="100%가 되면 졸업 가능",
                        good_threshold=80.0,
                        warning_threshold=50.0,
                    ),
                ],
                tips=[
                    "전공필수 과목을 우선 확인하세요.",
                    "역량 점수가 부족한 영역의 과목을 선택하면 효과적입니다.",
                    "학점이 낮은 학기에는 중요 과목 수를 조절하세요.",
                ],
            ),
            ScenarioType.OPPORTUNITY: ScenarioGuide(
                scenario_type="opportunity",
                title="기회 참여 시뮬레이션",
                description="인턴십, 프로젝트, 대회 등에 참여했을 때의 경력 개발 효과를 분석합니다.",
                how_it_works="""
                1. 선택한 기회의 유형과 특성을 분석합니다.
                2. 참여 시 얻을 수 있는 경험치를 계산합니다.
                3. 해당 경험이 목표 직무에 미치는 영향을 예측합니다.
                4. 포트폴리오 가치를 평가합니다.
                """,
                steps=[
                    "1단계: 기회 유형 선택 (인턴십/프로젝트/대회)",
                    "2단계: 세부 정보 입력",
                    "3단계: 시뮬레이션 실행",
                    "4단계: 경력 영향도 확인",
                ],
                variables=[
                    VariableGuide(
                        name="opportunity_type",
                        label="기회 유형",
                        description="참여하려는 활동 유형을 선택하세요",
                        input_type="select",
                        options=[
                            {"value": "internship", "label": "인턴십"},
                            {"value": "project", "label": "프로젝트"},
                            {"value": "contest", "label": "공모전/대회"},
                            {"value": "certification", "label": "자격증"},
                            {"value": "research", "label": "연구 참여"},
                            {"value": "club", "label": "동아리 활동"},
                        ],
                        required=True,
                    ),
                    VariableGuide(
                        name="duration_months",
                        label="참여 기간 (개월)",
                        description="예상 참여 기간",
                        input_type="number",
                        default_value=3,
                        min_value=1,
                        max_value=12,
                        required=True,
                    ),
                ],
                expected_metrics=[
                    MetricExplanation(
                        metric_name="경력 점수 증가",
                        description="참여로 인한 경력 점수 변화",
                        unit="점",
                        interpretation="높을수록 취업에 유리",
                        good_threshold=20.0,
                        warning_threshold=5.0,
                    ),
                    MetricExplanation(
                        metric_name="포트폴리오 가치",
                        description="이 경험의 포트폴리오 기여도",
                        unit="점",
                        interpretation="실무 경험일수록 높은 점수",
                        good_threshold=30.0,
                        warning_threshold=10.0,
                    ),
                    MetricExplanation(
                        metric_name="네트워크 확장",
                        description="인맥/네트워크 확장 효과",
                        unit="명",
                        interpretation="예상되는 새로운 연결 수",
                        good_threshold=10.0,
                        warning_threshold=2.0,
                    ),
                ],
                tips=[
                    "목표 직무와 관련된 기회를 선택하면 효과가 더 큽니다.",
                    "인턴십은 정규직 전환 가능성도 고려하세요.",
                    "여러 기회를 비교하여 최적의 선택을 하세요.",
                ],
            ),
            ScenarioType.TIMELINE: ScenarioGuide(
                scenario_type="timeline",
                title="타임라인 시뮬레이션",
                description="특정 목표까지의 시간별 성장 경로를 예측합니다.",
                how_it_works="""
                1. 목표와 달성 기한을 설정합니다.
                2. 현재 상태에서 목표까지의 갭을 분석합니다.
                3. 기간별 마일스톤을 생성합니다.
                4. 달성 가능성을 평가합니다.
                """,
                steps=[
                    "1단계: 목표 유형 선택",
                    "2단계: 목표 날짜 설정",
                    "3단계: 중간 마일스톤 확인",
                    "4단계: 경로 실현 가능성 확인",
                ],
                variables=[
                    VariableGuide(
                        name="goal_type",
                        label="목표 유형",
                        description="달성하려는 목표의 유형",
                        input_type="select",
                        options=[
                            {"value": "graduation", "label": "졸업"},
                            {"value": "job_ready", "label": "취업 준비 완료"},
                            {"value": "skill_master", "label": "특정 스킬 마스터"},
                            {"value": "certification", "label": "자격증 취득"},
                        ],
                        required=True,
                    ),
                    VariableGuide(
                        name="target_date",
                        label="목표 날짜",
                        description="목표 달성 예정일",
                        input_type="date",
                        required=True,
                    ),
                ],
                expected_metrics=[
                    MetricExplanation(
                        metric_name="목표 달성 확률",
                        description="설정된 기간 내 목표 달성 가능성",
                        unit="%",
                        interpretation="80% 이상이면 현실적인 계획",
                        good_threshold=80.0,
                        warning_threshold=50.0,
                    ),
                    MetricExplanation(
                        metric_name="필요 노력량",
                        description="주당 필요한 추가 노력 시간",
                        unit="시간/주",
                        interpretation="현재보다 추가로 필요한 시간",
                        good_threshold=10.0,
                        warning_threshold=20.0,
                    ),
                ],
                tips=[
                    "너무 빠듯한 일정보다는 여유있는 목표를 설정하세요.",
                    "중간 마일스톤을 정기적으로 점검하세요.",
                    "달성 확률이 낮다면 목표 기간을 조정하세요.",
                ],
            ),
        }

        return guides.get(scenario_type, guides[ScenarioType.CAREER_PATH])

    # ============================================
    # AI Analysis for Simulation Results
    # ============================================

    async def _generate_ai_analysis(
        self, data: ScenarioCreate, results: List[SimulationResult], overall_score: float
    ) -> Optional[Dict[str, Any]]:
        """GPT를 사용하여 시뮬레이션 결과에 대한 상세 분석 생성"""
        if not self.openai_client:
            return self._generate_default_analysis(results, overall_score)

        system_prompt = """당신은 대학생 커리어 개발 전문 AI 분석가입니다.
시뮬레이션 결과를 분석하여 학생에게 실질적인 조언을 제공합니다.

다음 JSON 형식으로 정확히 응답하세요:
{
    "summary": "핵심 분석 요약 (2-3문장)",
    "strengths": ["이 시나리오의 장점 3가지"],
    "risks": ["주의해야 할 위험요소 2-3가지"],
    "recommendations": ["구체적인 실행 추천 3-4가지"],
    "next_steps": ["바로 시작할 수 있는 다음 단계 2-3가지"],
    "confidence_reason": "종합점수가 이렇게 산정된 이유 설명"
}

중요:
- 추상적인 조언보다 구체적이고 실행 가능한 조언을 제공하세요
- 학생의 상황을 고려하여 개인화된 분석을 제공하세요
- 부정적인 결과도 솔직하게 전달하되, 개선 방안과 함께 제시하세요"""

        results_text = "\n".join([
            f"- {r.metric_name}: {r.current_value} → {r.simulated_value} ({r.change_percent:+.1f}%, {r.impact_level})"
            for r in results
        ])

        user_prompt = f"""시뮬레이션 분석 요청:

시나리오 유형: {data.scenario_type.value}
시나리오 이름: {data.name}
설명: {data.description or '없음'}

설정된 변수:
{chr(10).join([f"- {v.name}: {v.current_value} → {v.simulated_value}" for v in data.variables])}

시뮬레이션 결과:
{results_text}

종합 영향 점수: {overall_score:.2f} (0-1 스케일, 1이 가장 긍정적)

위 시뮬레이션 결과를 분석해주세요."""

        try:
            response = await self.openai_client.chat.completions.create(
                model=self.settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=1500,
            )

            content = response.choices[0].message.content

            # Parse JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            analysis = json.loads(content.strip())
            logger.info(f"AI analysis generated for scenario: {data.name}")
            return analysis

        except Exception as e:
            logger.error(f"AI analysis generation failed: {e}")
            return self._generate_default_analysis(results, overall_score)

    def _generate_default_analysis(
        self, results: List[SimulationResult], overall_score: float
    ) -> Dict[str, Any]:
        """기본 분석 결과 (AI 실패 시 fallback)"""
        positive_results = [r for r in results if r.impact_level == "positive"]
        negative_results = [r for r in results if r.impact_level == "negative"]

        if overall_score > 0.6:
            summary = "이 시나리오는 전반적으로 긍정적인 결과를 보입니다. 실행을 권장합니다."
            risk_level = "낮음"
        elif overall_score > 0.4:
            summary = "이 시나리오는 긍정적 측면과 주의가 필요한 측면이 혼재합니다."
            risk_level = "중간"
        else:
            summary = "이 시나리오는 신중한 검토가 필요합니다. 대안을 고려해보세요."
            risk_level = "높음"

        return {
            "summary": summary,
            "strengths": [r.explanation or f"{r.metric_name} 향상" for r in positive_results[:3]] or ["긍정적 영향이 예상됩니다"],
            "risks": [r.explanation or f"{r.metric_name} 주의 필요" for r in negative_results[:2]] or [f"전체 위험 수준: {risk_level}"],
            "recommendations": [
                "세부 결과를 검토하여 장단점을 파악하세요",
                "유사한 다른 시나리오와 비교해보세요",
                "실행 전 준비가 필요한 사항을 확인하세요",
            ],
            "next_steps": [
                "결과를 저장하고 다른 시나리오와 비교하세요",
                "관련 스킬 개발 계획을 수립하세요",
            ],
            "confidence_reason": f"긍정적 결과 {len(positive_results)}개, 부정적 결과 {len(negative_results)}개를 기반으로 산정되었습니다.",
        }


simulation_service = SimulationService()
