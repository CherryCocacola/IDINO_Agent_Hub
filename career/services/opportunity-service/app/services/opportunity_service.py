from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
import json

from ..database import execute_query, execute_one, execute_scalar, execute_command
from ..schemas import (
    OpportunityType,
    ApplicationStatus,
    OpportunityCreate,
    OpportunityUpdate,
    OpportunityResponse,
    OpportunityMatchScore,
    OpportunityRecommendationResponse,
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse,
)


class OpportunityService:
    """기회 마켓플레이스 서비스"""

    # ============================================
    # Opportunity CRUD
    # ============================================

    async def get_all_opportunities(
        self,
        opportunity_type: Optional[OpportunityType] = None,
        is_active: bool = True,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Dict], int]:
        """모든 기회 조회"""
        # status 'open' = is_active TRUE (database uses open/closed/filled)
        status_value = 'open' if is_active else 'closed'
        conditions = ["status = $1"]
        params = [status_value]
        param_idx = 2

        if opportunity_type:
            conditions.append(f"opportunity_type = ${param_idx}")
            params.append(opportunity_type.value)
            param_idx += 1

        where_clause = " AND ".join(conditions)
        offset = (page - 1) * page_size

        # Get total count
        count_query = f"""
            SELECT COUNT(*) FROM tb_opportunity
            WHERE {where_clause}
        """
        total_count = await execute_scalar(count_query, *params)

        # Get paginated results - map DB columns to expected response columns
        query = f"""
            SELECT
                opportunity_id, opportunity_type, title, description,
                organization, location, start_date, end_date,
                application_end as application_deadline,
                COALESCE(skill_contributions->>'skills', '[]')::jsonb as required_skills,
                NULL::jsonb as preferred_skills,
                (requirements->>'min_gpa')::float as min_gpa,
                requirements->'eligible_majors' as eligible_majors,
                requirements->'eligible_years' as eligible_years,
                COALESCE(benefits->>'salary', '') as benefits,
                external_url as url,
                (status = 'open') as is_active,
                ins_dt as created_at, upd_dt as updated_at
            FROM tb_opportunity
            WHERE {where_clause}
            ORDER BY application_end ASC NULLS LAST, ins_dt DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([page_size, offset])

        rows = await execute_query(query, *params)
        return rows, total_count

    async def get_opportunity(self, opportunity_id: UUID) -> Optional[Dict]:
        """특정 기회 조회"""
        query = """
            SELECT
                opportunity_id, opportunity_type, title, description,
                organization, location, start_date, end_date,
                application_end as application_deadline,
                COALESCE(skill_contributions->>'skills', '[]')::jsonb as required_skills,
                NULL::jsonb as preferred_skills,
                (requirements->>'min_gpa')::float as min_gpa,
                requirements->'eligible_majors' as eligible_majors,
                requirements->'eligible_years' as eligible_years,
                COALESCE(benefits->>'salary', '') as benefits,
                external_url as url,
                (status = 'open') as is_active,
                ins_dt as created_at, upd_dt as updated_at
            FROM tb_opportunity
            WHERE opportunity_id = $1
        """
        return await execute_one(query, opportunity_id)

    async def create_opportunity(self, data: OpportunityCreate) -> Dict:
        """기회 생성"""
        query = """
            INSERT INTO tb_opportunity (
                opportunity_type, title, description, organization, location,
                start_date, end_date, application_deadline,
                required_skills, preferred_skills, min_gpa,
                eligible_majors, eligible_years, benefits, url, is_active
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
            )
            RETURNING
                opportunity_id, opportunity_type, title, description,
                organization, location, start_date, end_date,
                application_deadline, required_skills, preferred_skills,
                min_gpa, eligible_majors, eligible_years,
                benefits, url, is_active, created_at, updated_at
        """
        return await execute_one(
            query,
            data.opportunity_type.value,
            data.title,
            data.description,
            data.organization,
            data.location,
            data.start_date,
            data.end_date,
            data.application_deadline,
            data.required_skills,
            data.preferred_skills,
            data.min_gpa,
            data.eligible_majors,
            data.eligible_years,
            data.benefits,
            data.url,
            data.is_active,
        )

    async def update_opportunity(
        self, opportunity_id: UUID, data: OpportunityUpdate
    ) -> Optional[Dict]:
        """기회 수정"""
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_opportunity(opportunity_id)

        # Convert enum to value
        if "opportunity_type" in update_data and update_data["opportunity_type"]:
            update_data["opportunity_type"] = update_data["opportunity_type"].value

        set_clauses = []
        params = []
        for idx, (key, value) in enumerate(update_data.items(), 1):
            set_clauses.append(f"{key} = ${idx}")
            params.append(value)

        params.append(opportunity_id)

        query = f"""
            UPDATE tb_opportunity
            SET {", ".join(set_clauses)}, updated_at = NOW()
            WHERE opportunity_id = ${len(params)}
            RETURNING
                opportunity_id, opportunity_type, title, description,
                organization, location, start_date, end_date,
                application_deadline, required_skills, preferred_skills,
                min_gpa, eligible_majors, eligible_years,
                benefits, url, is_active, created_at, updated_at
        """
        return await execute_one(query, *params)

    async def delete_opportunity(self, opportunity_id: UUID) -> bool:
        """기회 삭제 (soft delete)"""
        query = """
            UPDATE tb_opportunity
            SET is_active = FALSE, updated_at = NOW()
            WHERE opportunity_id = $1
        """
        result = await execute_command(query, opportunity_id)
        return "UPDATE 1" in result

    # ============================================
    # Recommendation Engine
    # ============================================

    async def get_student_profile(self, student_id: str) -> Optional[Dict]:
        """학생 프로필 조회 (스킬, 전공, 학년, 관심직업 등)"""
        # Get basic student info - use actual DB column names
        student_query = """
            SELECT
                s.student_id as std_id, s.student_nm as std_nm,
                s.department_cd as major_cd, s.current_grade as grade,
                s.career_goal,
                d.department_nm as major_nm, NULL::float as gpa
            FROM tb_student s
            LEFT JOIN tb_department d ON s.department_cd = d.department_cd
            WHERE s.student_id = $1
        """
        student = await execute_one(student_query, student_id)
        if not student:
            return None

        # Get student skills
        skills_query = """
            SELECT skill_cd, current_level
            FROM tb_student_skill
            WHERE student_id = $1
        """
        skills = await execute_query(skills_query, student_id)
        student["skills"] = {s["skill_cd"]: s["current_level"] for s in skills}

        # Get student interested jobs (from tb_student_interested_job)
        interested_jobs_query = """
            SELECT
                i.job_cd, w.job_nm, w.job_category, w.job_subcategory,
                w.required_skills, w.related_majors,
                i.interest_level
            FROM tb_student_interested_job i
            JOIN tb_worknet_job w ON i.job_cd = w.job_cd
            WHERE i.student_id = $1
            ORDER BY i.interest_level DESC
        """
        interested_jobs = await execute_query(interested_jobs_query, student_id)
        student["interested_jobs"] = interested_jobs

        # Get related role codes from interested jobs
        if interested_jobs:
            job_codes = [j["job_cd"] for j in interested_jobs]
            roles_query = """
                SELECT role_cd, worknet_code
                FROM tb_role
                WHERE worknet_code = ANY($1)
            """
            related_roles = await execute_query(roles_query, job_codes)
            student["interested_role_cds"] = [r["role_cd"] for r in related_roles]
        else:
            student["interested_role_cds"] = []

        return student

    async def calculate_match_score(
        self, student: Dict, opportunity: Dict
    ) -> OpportunityMatchScore:
        """학생-기회 매칭 점수 계산 (전공, 관심직업 포함)"""
        skill_score = 0.0
        eligibility_score = 100.0
        preference_score = 50.0
        career_relevance_score = 50.0  # 새로 추가: 진로 관련성 점수
        match_reasons = []
        gap_skills = []

        student_skills = student.get("skills", {})
        required_skills = opportunity.get("required_skills") or []
        preferred_skills = opportunity.get("preferred_skills") or []
        interested_jobs = student.get("interested_jobs", [])
        student_major = student.get("major_cd")

        # 1. Skill Match Score (30% weight - 조정)
        if required_skills:
            matched_required = sum(1 for s in required_skills if s in student_skills)
            skill_score = (matched_required / len(required_skills)) * 70
            gap_skills = [s for s in required_skills if s not in student_skills]
            if matched_required == len(required_skills):
                match_reasons.append("모든 필수 스킬 보유")
            elif matched_required > 0:
                match_reasons.append(f"필수 스킬 {matched_required}/{len(required_skills)} 보유")
        else:
            skill_score = 70  # No required skills = full base score

        if preferred_skills:
            matched_preferred = sum(1 for s in preferred_skills if s in student_skills)
            skill_score += (matched_preferred / len(preferred_skills)) * 30
            if matched_preferred > 0:
                match_reasons.append(f"우대 스킬 {matched_preferred}개 보유")

        # 2. Eligibility Score (25% weight - 조정)
        # Check GPA
        min_gpa = opportunity.get("min_gpa")
        student_gpa = student.get("gpa", 0)
        if min_gpa and student_gpa:
            if student_gpa >= min_gpa:
                match_reasons.append(f"GPA 요건 충족 ({student_gpa:.2f} >= {min_gpa})")
            else:
                eligibility_score -= 30
                match_reasons.append(f"GPA 미달 ({student_gpa:.2f} < {min_gpa})")

        # Check eligible majors - 전공 매칭 강화
        eligible_majors = opportunity.get("eligible_majors") or []
        if eligible_majors and student_major:
            if student_major in eligible_majors:
                match_reasons.append("전공 요건 충족")
                eligibility_score += 10  # 전공 일치 보너스
            else:
                eligibility_score -= 20

        # Check eligible years
        eligible_years = opportunity.get("eligible_years") or []
        student_year = student.get("grade", 0)
        if eligible_years and student_year:
            if student_year in eligible_years:
                match_reasons.append(f"{student_year}학년 지원 가능")
            else:
                eligibility_score -= 25

        # 3. Career Relevance Score (25% weight - 새로 추가)
        # 관심직업과의 관련성 계산
        opp_type = opportunity.get("opportunity_type", "")
        opp_title = opportunity.get("title", "").lower()
        opp_desc = opportunity.get("description", "").lower() if opportunity.get("description") else ""

        if interested_jobs:
            relevance_found = False
            for job in interested_jobs:
                job_nm = job.get("job_nm", "").lower()
                job_category = job.get("job_category", "").lower()
                job_skills = job.get("required_skills", []) or []
                related_majors = job.get("related_majors", []) or []
                interest_level = job.get("interest_level", 3)

                # 직업명 또는 카테고리가 기회 제목/설명에 포함되는지 확인
                if job_nm in opp_title or job_nm in opp_desc:
                    career_relevance_score = 90 + (interest_level * 2)
                    match_reasons.append(f"관심직업 '{job.get('job_nm')}' 관련 기회")
                    relevance_found = True
                    break
                elif job_category in opp_title or job_category in opp_desc:
                    career_relevance_score = 75 + (interest_level * 2)
                    match_reasons.append(f"관심 분야 '{job_category}' 관련 기회")
                    relevance_found = True
                    break

                # 관심직업 필요 스킬과 기회 필수 스킬 비교
                if required_skills and job_skills:
                    common_skills = set(required_skills) & set(job_skills)
                    if common_skills:
                        career_relevance_score = 70 + len(common_skills) * 5
                        relevance_found = True

                # 전공이 관심직업 관련 전공에 포함되는지 확인
                student_major_nm = student.get("major_nm", "")
                if student_major_nm and related_majors:
                    if any(student_major_nm in m or m in student_major_nm for m in related_majors):
                        career_relevance_score = max(career_relevance_score, 65)
                        if not relevance_found:
                            match_reasons.append("전공-관심직업 연관성 높음")
                            relevance_found = True

            if not relevance_found:
                career_relevance_score = 40  # 관련성 낮음
        else:
            career_relevance_score = 50  # 관심직업 미설정

        # 4. Preference Score (20% weight - 조정)
        # 마감일 기반 + 기회 유형 고려
        deadline = opportunity.get("application_deadline")
        if deadline:
            days_until = (deadline - date.today()).days
            if 0 < days_until <= 7:
                preference_score = 80
                match_reasons.append("마감 임박 (7일 이내)")
            elif 7 < days_until <= 30:
                preference_score = 70
                match_reasons.append("마감 1개월 이내")
            elif days_until > 30:
                preference_score = 60
            else:
                preference_score = 20  # Already expired

        # Calculate overall score (weighted average - 조정된 가중치)
        # skill: 30%, eligibility: 25%, career_relevance: 25%, preference: 20%
        overall_score = (
            (skill_score * 0.30) +
            (eligibility_score * 0.25) +
            (career_relevance_score * 0.25) +
            (preference_score * 0.20)
        )

        return OpportunityMatchScore(
            opportunity_id=opportunity["opportunity_id"],
            skill_match_score=round(skill_score, 1),
            eligibility_score=round(eligibility_score, 1),
            preference_score=round(preference_score, 1),
            overall_score=round(overall_score, 1),
            match_reasons=match_reasons,
            gap_skills=gap_skills,
        )

    async def get_recommendations(
        self,
        student_id: str,
        opportunity_types: Optional[List[OpportunityType]] = None,
        min_score: float = 50.0,
        max_results: int = 10,
        include_expired: bool = False,
    ) -> List[OpportunityRecommendationResponse]:
        """학생 맞춤 기회 추천"""
        # Get student profile
        student = await self.get_student_profile(student_id)
        if not student:
            return []

        # Build opportunity query - use status instead of is_active (database uses open/closed/filled)
        conditions = ["status = 'open'"]
        params = []
        param_idx = 1

        if not include_expired:
            conditions.append(
                f"(application_end IS NULL OR application_end >= ${param_idx})"
            )
            params.append(date.today())
            param_idx += 1

        if opportunity_types:
            type_placeholders = ", ".join(
                f"${i}" for i in range(param_idx, param_idx + len(opportunity_types))
            )
            conditions.append(f"opportunity_type IN ({type_placeholders})")
            params.extend([t.value for t in opportunity_types])
            param_idx += len(opportunity_types)

        # Filter by student's department - only show relevant or universal opportunities
        student_dept = student.get("major_cd") if student else None
        if student_dept:
            conditions.append(
                f"(department_cds IS NULL OR ${param_idx} = ANY(department_cds))"
            )
            params.append(student_dept)
            param_idx += 1

        query = f"""
            SELECT
                opportunity_id, opportunity_type, title, description,
                organization, location, start_date, end_date,
                application_end as application_deadline,
                COALESCE(skill_contributions->>'skills', '[]')::jsonb as required_skills,
                NULL::jsonb as preferred_skills,
                (requirements->>'min_gpa')::float as min_gpa,
                requirements->'eligible_majors' as eligible_majors,
                requirements->'eligible_years' as eligible_years,
                COALESCE(benefits->>'salary', '') as benefits,
                external_url as url,
                (status = 'open') as is_active,
                ins_dt as created_at, upd_dt as updated_at
            FROM tb_opportunity
            WHERE {" AND ".join(conditions)}
            ORDER BY application_end ASC NULLS LAST
        """

        opportunities = await execute_query(query, *params)

        # Calculate match scores
        recommendations = []
        for opp in opportunities:
            match_score = await self.calculate_match_score(student, opp)

            if match_score.overall_score >= min_score:
                # Generate recommended actions
                actions = []
                if match_score.gap_skills:
                    actions.append(f"부족 스킬 학습 필요: {', '.join(match_score.gap_skills[:3])}")
                if match_score.eligibility_score < 100:
                    actions.append("자격 요건 확인 필요")

                deadline = opp.get("application_deadline")
                if deadline:
                    days = (deadline - date.today()).days
                    if 0 < days <= 7:
                        actions.append(f"마감 {days}일 전 - 빠른 지원 권장")
                    elif days > 7:
                        actions.append(f"마감까지 {days}일 - 준비 기간 활용")

                recommendations.append(
                    OpportunityRecommendationResponse(
                        opportunity=OpportunityResponse(**opp),
                        match_score=match_score,
                        recommended_actions=actions,
                    )
                )

        # Sort by overall score descending and limit results
        recommendations.sort(key=lambda x: x.match_score.overall_score, reverse=True)
        return recommendations[:max_results]

    async def save_recommendation(
        self, student_id: str, opportunity_id: UUID, match_score: OpportunityMatchScore
    ) -> Dict:
        """추천 기록 저장"""
        query = """
            INSERT INTO tb_opportunity_recommendation (
                std_id, opportunity_id, match_score, match_reasons, recommended_at
            ) VALUES ($1, $2, $3, $4, NOW())
            ON CONFLICT (std_id, opportunity_id)
            DO UPDATE SET
                match_score = EXCLUDED.match_score,
                match_reasons = EXCLUDED.match_reasons,
                recommended_at = NOW()
            RETURNING recommendation_id, std_id, opportunity_id, match_score, match_reasons, recommended_at
        """
        return await execute_one(
            query,
            student_id,
            opportunity_id,
            match_score.overall_score,
            match_score.match_reasons,
        )

    # ============================================
    # Application Management
    # ============================================

    async def get_student_applications(
        self, student_id: str, status: Optional[ApplicationStatus] = None
    ) -> List[Dict]:
        """학생 지원 목록 조회"""
        conditions = ["a.std_id = $1"]
        params = [student_id]

        if status:
            conditions.append("a.status = $2")
            params.append(status.value)

        query = f"""
            SELECT
                a.application_id, a.std_id as student_id, a.opportunity_id,
                o.title as opportunity_title, o.opportunity_type,
                o.organization, a.status, a.notes,
                a.applied_at, a.result_at, a.created_at, a.updated_at
            FROM tb_opportunity_application a
            JOIN tb_opportunity o ON a.opportunity_id = o.opportunity_id
            WHERE {" AND ".join(conditions)}
            ORDER BY a.created_at DESC
        """
        return await execute_query(query, *params)

    async def get_application(
        self, student_id: str, opportunity_id: UUID
    ) -> Optional[Dict]:
        """특정 지원 조회"""
        query = """
            SELECT
                a.application_id, a.std_id as student_id, a.opportunity_id,
                o.title as opportunity_title, o.opportunity_type,
                o.organization, a.status, a.notes,
                a.applied_at, a.result_at, a.created_at, a.updated_at
            FROM tb_opportunity_application a
            JOIN tb_opportunity o ON a.opportunity_id = o.opportunity_id
            WHERE a.std_id = $1 AND a.opportunity_id = $2
        """
        return await execute_one(query, student_id, opportunity_id)

    async def create_application(self, data: ApplicationCreate) -> Dict:
        """지원 생성"""
        query = """
            INSERT INTO tb_opportunity_application (
                std_id, opportunity_id, status, notes
            ) VALUES ($1, $2, $3, $4)
            RETURNING application_id, std_id as student_id, opportunity_id, status, notes,
                      applied_at, result_at, created_at, updated_at
        """
        result = await execute_one(
            query,
            data.student_id,
            data.opportunity_id,
            data.status.value,
            data.notes,
        )

        # Get opportunity details
        opp = await self.get_opportunity(data.opportunity_id)
        if opp:
            result["opportunity_title"] = opp["title"]
            result["opportunity_type"] = opp["opportunity_type"]
            result["organization"] = opp["organization"]

        return result

    async def update_application(
        self, application_id: UUID, data: ApplicationUpdate
    ) -> Optional[Dict]:
        """지원 상태 수정"""
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return None

        # Convert enum to value
        if "status" in update_data and update_data["status"]:
            update_data["status"] = update_data["status"].value

        set_clauses = []
        params = []
        for idx, (key, value) in enumerate(update_data.items(), 1):
            set_clauses.append(f"{key} = ${idx}")
            params.append(value)

        params.append(application_id)

        query = f"""
            UPDATE tb_opportunity_application
            SET {", ".join(set_clauses)}, updated_at = NOW()
            WHERE application_id = ${len(params)}
            RETURNING application_id, std_id as student_id, opportunity_id, status, notes,
                      applied_at, result_at, created_at, updated_at
        """
        return await execute_one(query, *params)

    async def delete_application(self, application_id: UUID) -> bool:
        """지원 삭제"""
        query = "DELETE FROM tb_opportunity_application WHERE application_id = $1"
        result = await execute_command(query, application_id)
        return "DELETE 1" in result

    # ============================================
    # Search
    # ============================================

    async def search_opportunities(
        self,
        query_text: Optional[str] = None,
        opportunity_types: Optional[List[OpportunityType]] = None,
        skills: Optional[List[str]] = None,
        location: Optional[str] = None,
        min_deadline_days: Optional[int] = None,
        is_active: bool = True,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "deadline",
        sort_order: str = "asc",
    ) -> tuple[List[Dict], int]:
        """기회 검색"""
        conditions = ["is_active = $1"]
        params = [is_active]
        param_idx = 2

        if query_text:
            conditions.append(
                f"(title ILIKE ${param_idx} OR description ILIKE ${param_idx} OR organization ILIKE ${param_idx})"
            )
            params.append(f"%{query_text}%")
            param_idx += 1

        if opportunity_types:
            type_placeholders = ", ".join(
                f"${i}" for i in range(param_idx, param_idx + len(opportunity_types))
            )
            conditions.append(f"opportunity_type IN ({type_placeholders})")
            params.extend([t.value for t in opportunity_types])
            param_idx += len(opportunity_types)

        if skills:
            # Check if any required skill matches
            conditions.append(f"required_skills && ${param_idx}")
            params.append(skills)
            param_idx += 1

        if location:
            conditions.append(f"location ILIKE ${param_idx}")
            params.append(f"%{location}%")
            param_idx += 1

        if min_deadline_days is not None:
            conditions.append(
                f"application_deadline >= ${param_idx}"
            )
            params.append(date.today())
            param_idx += 1

        where_clause = " AND ".join(conditions)

        # Sort mapping
        sort_map = {
            "deadline": "application_deadline",
            "created": "created_at",
            "title": "title",
        }
        sort_column = sort_map.get(sort_by, "application_deadline")
        order = "ASC" if sort_order.lower() == "asc" else "DESC"

        # Get count
        count_query = f"SELECT COUNT(*) FROM tb_opportunity WHERE {where_clause}"
        total_count = await execute_scalar(count_query, *params)

        # Get results
        offset = (page - 1) * page_size
        query = f"""
            SELECT
                opportunity_id, opportunity_type, title, description,
                organization, location, start_date, end_date,
                application_deadline, required_skills, preferred_skills,
                min_gpa, eligible_majors, eligible_years,
                benefits, url, is_active, created_at, updated_at
            FROM tb_opportunity
            WHERE {where_clause}
            ORDER BY {sort_column} {order} NULLS LAST
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([page_size, offset])

        rows = await execute_query(query, *params)
        return rows, total_count


# Singleton instance
opportunity_service = OpportunityService()
