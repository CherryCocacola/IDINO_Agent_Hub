from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
import json

from ..database import execute_query, execute_one, execute_scalar
from ..schemas import (
    SkillResponse,
    StudentSkillResponse,
    RoleSkillMapResponse,
    SkillNode,
    SkillEdge,
    SkillGraphResponse,
    SkillGapItem,
    GapAnalysisResponse,
    SkillRelationResponse,
    RoleRequirementResponse,
)


class SkillService:
    """Service for Skill Graph & Gap Analysis (Phase 7)"""

    # ============================================
    # Role Data
    # ============================================

    async def get_all_roles(self) -> List[dict]:
        """Get all available roles"""
        query = """
            SELECT role_cd, role_nm, role_nm_en, category
            FROM tb_role
            WHERE use_fg = 'Y'
            ORDER BY role_nm
        """
        rows = await execute_query(query)
        return [dict(row) for row in rows]

    async def get_roles_for_student(self, student_id: str) -> List[dict]:
        """학생 학과에 맞는 역할만 반환"""
        query = """
            WITH dept_cat AS (
                SELECT
                    CASE
                        WHEN d.department_nm ~ '스포츠|헬스케어|체육|운동' THEN 'Sports'
                        WHEN d.department_nm ~ '의예|의학|의생명|의공학' THEN 'Medical'
                        WHEN d.department_nm ~ '간호' THEN 'Medical'
                        WHEN d.department_nm ~ '약학|제약' THEN 'Medical'
                        WHEN d.department_nm ~ '물리치료|임상병리|작업치료|응급구조|보건|방사선|치위생|치기공' THEN 'Medical'
                        WHEN d.department_nm ~ '컴퓨터|AI|소프트웨어|정보|반도체|전자|게임|멀티미디어|정보통신' THEN 'IT'
                        WHEN d.department_nm ~ '전기|기계|산업|건축|건설|로봇|나노|화공|재료|배터리|소방|스마트물류' THEN 'Engineering'
                        WHEN d.department_nm ~ '경영|통상|경제|회계|무역|물류|마케팅|금융|세무' THEN 'Business'
                        WHEN d.department_nm ~ '디자인|미디어|시각|영상|애니메이션|방송|음악|공연|웹툰|멀티미디어' THEN 'Arts'
                        WHEN d.department_nm ~ '교육|상담|사회복지|발달|특수교육|유아' THEN 'Education'
                        WHEN d.department_nm ~ '법학|경찰|행정' THEN 'Social'
                        WHEN d.department_nm ~ '어문|인문|역사|문화콘텐츠|문화유산|영어영문|통일' THEN 'Humanities'
                        WHEN d.department_nm ~ '생명과학|화학|통계|환경|신소재|바이오' THEN 'Science'
                        ELSE 'General'
                    END as category
                FROM tb_student s
                JOIN tb_department d ON s.department_cd = d.department_cd
                WHERE s.student_id = $1
            ),
            category_roles(category, role_codes) AS (
                VALUES
                    ('IT', ARRAY['ROLE01','ROLE02','ROLE03','ROLE07','ROLE08']),
                    ('Engineering', ARRAY['ROLE01','ROLE02','ROLE06','ROLE07','ROLE08']),
                    ('Medical', ARRAY['ROLE101','ROLE102','ROLE103','ROLE104','ROLE105']),
                    ('Sports', ARRAY['ROLE104','ROLE103','ROLE105','ROLE101','ROLE102']),
                    ('Education', ARRAY['ROLE201','ROLE202','ROLE203','ROLE204','ROLE205']),
                    ('Arts', ARRAY['ROLE301','ROLE302','ROLE303','ROLE011','ROLE306']),
                    ('Business', ARRAY['ROLE009','ROLE010','ROLE012','ROLE404','ROLE405']),
                    ('Social', ARRAY['ROLE401','ROLE251','ROLE403','ROLE009','ROLE406']),
                    ('Humanities', ARRAY['ROLE009','ROLE010','ROLE401','ROLE205','ROLE304']),
                    ('Science', ARRAY['ROLE501','ROLE502','ROLE503','ROLE504','ROLE03']),
                    ('General', ARRAY['ROLE009','ROLE010','ROLE012','ROLE401','ROLE406'])
            )
            SELECT r.role_cd, r.role_nm, r.role_nm_en, r.category
            FROM tb_role r
            JOIN category_roles cr ON r.role_cd = ANY(cr.role_codes)
            JOIN dept_cat dc ON cr.category = dc.category
            WHERE r.use_fg = 'Y'
            ORDER BY r.role_nm
        """
        rows = await execute_query(query, student_id)
        if not rows:
            return await self.get_all_roles()
        return [dict(row) for row in rows]

    # ============================================
    # Skill Master Data
    # ============================================

    async def get_all_skills(self, category: Optional[str] = None) -> List[SkillResponse]:
        """Get all skills, optionally filtered by category"""
        if category:
            query = """
                SELECT skill_cd, skill_nm, skill_nm_en, synonyms, category, difficulty
                FROM tb_skill
                WHERE use_fg = 'Y' AND category = $1
                ORDER BY skill_nm
            """
            rows = await execute_query(query, category)
        else:
            query = """
                SELECT skill_cd, skill_nm, skill_nm_en, synonyms, category, difficulty
                FROM tb_skill
                WHERE use_fg = 'Y'
                ORDER BY skill_nm
            """
            rows = await execute_query(query)

        return [SkillResponse(**dict(row)) for row in rows]

    async def get_skill(self, skill_cd: str) -> Optional[SkillResponse]:
        """Get a single skill by code"""
        query = """
            SELECT skill_cd, skill_nm, skill_nm_en, synonyms, category, difficulty
            FROM tb_skill
            WHERE skill_cd = $1 AND use_fg = 'Y'
        """
        row = await execute_one(query, skill_cd)
        return SkillResponse(**dict(row)) if row else None

    # ============================================
    # Student Skills
    # ============================================

    async def get_student_skills(self, student_id: str) -> List[StudentSkillResponse]:
        """Get all skills for a student"""
        query = """
            SELECT
                ss.student_skill_id,
                ss.skill_cd,
                s.skill_nm,
                ss.current_level,
                ss.target_level,
                ss.evidence_count,
                ss.last_verified_date,
                ss.verification_source,
                ss.trend,
                (ss.target_level - ss.current_level) as gap
            FROM tb_student_skill ss
            JOIN tb_skill s ON ss.skill_cd = s.skill_cd
            WHERE ss.student_id = $1
            ORDER BY (ss.target_level - ss.current_level) DESC, s.skill_nm
        """
        rows = await execute_query(query, student_id)
        return [StudentSkillResponse(**dict(row)) for row in rows]

    async def get_student_skill(self, student_id: str, skill_cd: str) -> Optional[StudentSkillResponse]:
        """Get a specific skill for a student"""
        query = """
            SELECT
                ss.student_skill_id,
                ss.skill_cd,
                s.skill_nm,
                ss.current_level,
                ss.target_level,
                ss.evidence_count,
                ss.last_verified_date,
                ss.verification_source,
                ss.trend,
                (ss.target_level - ss.current_level) as gap
            FROM tb_student_skill ss
            JOIN tb_skill s ON ss.skill_cd = s.skill_cd
            WHERE ss.student_id = $1 AND ss.skill_cd = $2
        """
        row = await execute_one(query, student_id, skill_cd)
        return StudentSkillResponse(**dict(row)) if row else None

    async def update_student_skill(
        self,
        student_id: str,
        skill_cd: str,
        current_level: Optional[int] = None,
        target_level: Optional[int] = None,
        verification_source: Optional[str] = None
    ) -> Optional[StudentSkillResponse]:
        """Update or create a student skill record"""
        # Check if record exists
        existing = await self.get_student_skill(student_id, skill_cd)

        if existing:
            # Update existing
            updates = []
            params = [student_id, skill_cd]
            param_idx = 3

            if current_level is not None:
                updates.append(f"current_level = ${param_idx}")
                params.append(current_level)
                param_idx += 1

            if target_level is not None:
                updates.append(f"target_level = ${param_idx}")
                params.append(target_level)
                param_idx += 1

            if verification_source is not None:
                updates.append(f"verification_source = ${param_idx}")
                updates.append(f"last_verified_date = CURRENT_DATE")
                params.append(verification_source)
                param_idx += 1

            if updates:
                updates.append("upd_dt = CURRENT_TIMESTAMP")
                query = f"""
                    UPDATE tb_student_skill
                    SET {', '.join(updates)}
                    WHERE student_id = $1 AND skill_cd = $2
                """
                await execute_query(query, *params)
        else:
            # Insert new
            query = """
                INSERT INTO tb_student_skill (
                    student_id, skill_cd, current_level, target_level,
                    verification_source, last_verified_date
                )
                VALUES ($1, $2, $3, $4, $5, CURRENT_DATE)
            """
            await execute_query(
                query,
                student_id,
                skill_cd,
                current_level or 1,
                target_level or 3,
                verification_source
            )

        return await self.get_student_skill(student_id, skill_cd)

    # ============================================
    # Role-Skill Mapping
    # ============================================

    async def get_role_skills(self, role_cd: str) -> List[RoleSkillMapResponse]:
        """Get all skills required for a role"""
        query = """
            SELECT
                rsm.role_cd,
                r.role_nm,
                rsm.skill_cd,
                s.skill_nm,
                rsm.required_level,
                rsm.importance,
                rsm.market_demand_score,
                rsm.growth_trend
            FROM tb_role_skill_map rsm
            JOIN tb_role r ON rsm.role_cd = r.role_cd
            JOIN tb_skill s ON rsm.skill_cd = s.skill_cd
            WHERE rsm.role_cd = $1
            ORDER BY
                CASE rsm.importance
                    WHEN 'critical' THEN 1
                    WHEN 'important' THEN 2
                    ELSE 3
                END,
                rsm.required_level DESC
        """
        rows = await execute_query(query, role_cd)
        return [RoleSkillMapResponse(**dict(row)) for row in rows]

    async def get_role_requirements(self, role_cd: str) -> Optional[RoleRequirementResponse]:
        """Get complete role requirements with skills"""
        # Get role info
        role_query = """
            SELECT role_cd, role_nm, role_nm_en, category
            FROM tb_role
            WHERE role_cd = $1 AND use_fg = 'Y'
        """
        role_row = await execute_one(role_query, role_cd)
        if not role_row:
            return None

        # Get skills
        skills = await self.get_role_skills(role_cd)

        # Calculate stats
        critical_count = sum(1 for s in skills if s.importance == 'critical')
        avg_level = sum(s.required_level for s in skills) / len(skills) if skills else 0

        return RoleRequirementResponse(
            role_cd=role_row['role_cd'],
            role_nm=role_row['role_nm'],
            role_nm_en=role_row['role_nm_en'],
            industry=role_row.get('category'),
            required_skills=skills,
            total_skills=len(skills),
            critical_skills=critical_count,
            average_required_level=round(avg_level, 2)
        )

    # ============================================
    # Skill Graph
    # ============================================

    async def get_skill_graph(
        self,
        student_id: Optional[str] = None,
        role_cd: Optional[str] = None
    ) -> SkillGraphResponse:
        """Get skill graph for visualization"""
        nodes = []
        edges = []

        # Get all skills with relations
        if role_cd:
            # Get skills required for the role
            skills_query = """
                SELECT DISTINCT
                    s.skill_cd as id,
                    s.skill_nm as name,
                    s.category,
                    s.difficulty,
                    rsm.required_level,
                    rsm.importance
                FROM tb_skill s
                JOIN tb_role_skill_map rsm ON s.skill_cd = rsm.skill_cd
                WHERE rsm.role_cd = $1 AND s.use_fg = 'Y'
            """
            skill_rows = await execute_query(skills_query, role_cd)

            # Get role name
            role_row = await execute_one(
                "SELECT role_nm FROM tb_role WHERE role_cd = $1",
                role_cd
            )
            role_nm = role_row['role_nm'] if role_row else None
        else:
            # Get all skills
            skills_query = """
                SELECT
                    skill_cd as id,
                    skill_nm as name,
                    category,
                    difficulty,
                    NULL as required_level,
                    NULL as importance
                FROM tb_skill
                WHERE use_fg = 'Y'
            """
            skill_rows = await execute_query(skills_query)
            role_nm = None

        # Get student skill levels if student_id provided
        student_skills = {}
        if student_id:
            student_query = """
                SELECT skill_cd, current_level
                FROM tb_student_skill
                WHERE student_id = $1
            """
            student_rows = await execute_query(student_query, student_id)
            student_skills = {row['skill_cd']: row['current_level'] for row in student_rows}

        # Build nodes
        for row in skill_rows:
            student_level = student_skills.get(row['id'])
            required_level = row['required_level']
            gap = None
            if student_level is not None and required_level is not None:
                gap = max(0, required_level - student_level)

            nodes.append(SkillNode(
                id=row['id'],
                name=row['name'],
                category=row['category'],
                difficulty=row['difficulty'],
                student_level=student_level,
                required_level=required_level,
                gap=gap,
                importance=row['importance']
            ))

        # Get edges (skill relations)
        skill_ids = [n.id for n in nodes]
        if skill_ids:
            # Create placeholders for asyncpg - each IN clause needs separate placeholder numbers
            n = len(skill_ids)
            placeholders1 = ', '.join(f"${i+1}" for i in range(n))
            placeholders2 = ', '.join(f"${i+1+n}" for i in range(n))
            edges_query = f"""
                SELECT
                    skill_cd_from as source,
                    skill_cd_to as target,
                    relation_type,
                    strength
                FROM tb_skill_relation
                WHERE skill_cd_from IN ({placeholders1})
                   OR skill_cd_to IN ({placeholders2})
            """
            edge_rows = await execute_query(edges_query, *skill_ids, *skill_ids)

            for row in edge_rows:
                if row['source'] in skill_ids and row['target'] in skill_ids:
                    edges.append(SkillEdge(
                        source=row['source'],
                        target=row['target'],
                        relation_type=row['relation_type'],
                        strength=float(row['strength']) if row['strength'] else 1.0
                    ))

        return SkillGraphResponse(
            nodes=nodes,
            edges=edges,
            role_cd=role_cd,
            role_nm=role_nm
        )

    # ============================================
    # Gap Analysis
    # ============================================

    async def analyze_skill_gap(
        self,
        student_id: str,
        target_role_cd: str,
        include_recommendations: bool = True
    ) -> GapAnalysisResponse:
        """Analyze skill gaps between student and target role"""

        # Get role info
        role_row = await execute_one(
            "SELECT role_nm FROM tb_role WHERE role_cd = $1",
            target_role_cd
        )
        role_nm = role_row['role_nm'] if role_row else None

        # Get required skills for role
        role_skills = await self.get_role_skills(target_role_cd)

        # Get student skills
        student_skills_query = """
            SELECT skill_cd, current_level
            FROM tb_student_skill
            WHERE student_id = $1
        """
        student_rows = await execute_query(student_skills_query, student_id)
        student_skill_map = {row['skill_cd']: row['current_level'] for row in student_rows}

        # Calculate gaps
        skill_gaps = []
        strengths = []
        total_gap = 0
        max_possible_gap = 0

        for idx, rs in enumerate(role_skills):
            current_level = student_skill_map.get(rs.skill_cd, 0)
            gap = max(0, rs.required_level - current_level)

            if gap > 0:
                # Weight by importance
                weight = 3 if rs.importance == 'critical' else (2 if rs.importance == 'important' else 1)
                total_gap += gap * weight

                # Generate recommendations
                recommendations = []
                if include_recommendations:
                    if gap >= 3:
                        recommendations.append(f"{rs.skill_nm} 기초 과정 수강 필요")
                        recommendations.append("관련 온라인 강의 추천")
                    elif gap >= 2:
                        recommendations.append(f"{rs.skill_nm} 중급 프로젝트 참여 권장")
                    else:
                        recommendations.append(f"{rs.skill_nm} 실습 강화 필요")

                skill_gaps.append(SkillGapItem(
                    skill_cd=rs.skill_cd,
                    skill_nm=rs.skill_nm or rs.skill_cd,
                    current_level=current_level,
                    required_level=rs.required_level,
                    gap=gap,
                    importance=rs.importance,
                    priority_rank=idx + 1,
                    recommended_actions=recommendations
                ))
            else:
                strengths.append(rs.skill_nm or rs.skill_cd)

            # Calculate max possible gap for percentage
            importance_weight = 3 if rs.importance == 'critical' else (2 if rs.importance == 'important' else 1)
            max_possible_gap += 5 * importance_weight  # Max level is 5

        # Sort by gap and importance
        skill_gaps.sort(
            key=lambda x: (
                -({'critical': 3, 'important': 2, 'nice_to_have': 1}.get(x.importance, 0)),
                -x.gap
            )
        )

        # Update priority ranks after sorting
        for idx, gap in enumerate(skill_gaps):
            gap.priority_rank = idx + 1

        # Calculate scores
        overall_gap_score = (total_gap / max_possible_gap * 100) if max_possible_gap > 0 else 0
        readiness_percentage = 100 - overall_gap_score

        # Top priority skills (use skill names instead of codes for readability)
        top_priority = [g.skill_nm for g in skill_gaps[:5]]

        # Generate summary
        if overall_gap_score < 20:
            summary = f"'{role_nm}'에 대한 준비도가 매우 높습니다. 약간의 보완만 필요합니다."
        elif overall_gap_score < 40:
            summary = f"'{role_nm}'에 대한 기본 역량은 갖추고 있습니다. {len(skill_gaps)}개 스킬 개발이 필요합니다."
        elif overall_gap_score < 60:
            summary = f"'{role_nm}'을 위해 체계적인 스킬 개발 계획이 필요합니다."
        else:
            summary = f"'{role_nm}'까지 상당한 스킬 개발이 필요합니다. 핵심 스킬부터 집중적으로 학습하세요."

        # Save analysis result
        analysis_id = await self._save_gap_analysis(
            student_id=student_id,
            target_role_cd=target_role_cd,
            overall_gap_score=overall_gap_score,
            gap_details=skill_gaps,
            top_priority_skills=top_priority
        )

        return GapAnalysisResponse(
            analysis_id=analysis_id,
            student_id=student_id,
            target_role_cd=target_role_cd,
            target_role_nm=role_nm,
            analysis_date=datetime.now(),
            overall_gap_score=round(overall_gap_score, 2),
            readiness_percentage=round(readiness_percentage, 2),
            skill_gaps=skill_gaps,
            top_priority_skills=top_priority,
            strengths=strengths,
            summary=summary
        )

    async def _save_gap_analysis(
        self,
        student_id: str,
        target_role_cd: str,
        overall_gap_score: float,
        gap_details: List[SkillGapItem],
        top_priority_skills: List[str]
    ) -> UUID:
        """Save gap analysis result to database"""
        query = """
            INSERT INTO tb_skill_gap_analysis (
                student_id, target_role_cd, overall_gap_score,
                gap_details, top_priority_skills
            )
            VALUES ($1, $2, $3, $4, $5)
            RETURNING analysis_id
        """
        gap_details_json = json.dumps([g.model_dump() for g in gap_details])
        result = await execute_scalar(
            query,
            student_id,
            target_role_cd,
            overall_gap_score,
            gap_details_json,
            top_priority_skills
        )
        return result

    # ============================================
    # Skill Relations
    # ============================================

    async def get_skill_relations(self, skill_cd: str) -> List[SkillRelationResponse]:
        """Get all relations for a skill"""
        query = """
            SELECT
                sr.skill_cd_from,
                s1.skill_nm as skill_nm_from,
                sr.skill_cd_to,
                s2.skill_nm as skill_nm_to,
                sr.relation_type,
                sr.strength
            FROM tb_skill_relation sr
            JOIN tb_skill s1 ON sr.skill_cd_from = s1.skill_cd
            JOIN tb_skill s2 ON sr.skill_cd_to = s2.skill_cd
            WHERE sr.skill_cd_from = $1 OR sr.skill_cd_to = $1
        """
        rows = await execute_query(query, skill_cd)
        return [SkillRelationResponse(**dict(row)) for row in rows]

    async def get_prerequisite_skills(self, skill_cd: str) -> List[SkillResponse]:
        """Get prerequisite skills for a skill"""
        query = """
            SELECT s.skill_cd, s.skill_nm, s.skill_nm_en, s.synonyms, s.category, s.difficulty
            FROM tb_skill s
            JOIN tb_skill_relation sr ON s.skill_cd = sr.skill_cd_from
            WHERE sr.skill_cd_to = $1 AND sr.relation_type = 'prerequisite'
        """
        rows = await execute_query(query, skill_cd)
        return [SkillResponse(**dict(row)) for row in rows]

    async def get_next_skills(self, skill_cd: str) -> List[SkillResponse]:
        """Get skills that build on a given skill"""
        query = """
            SELECT s.skill_cd, s.skill_nm, s.skill_nm_en, s.synonyms, s.category, s.difficulty
            FROM tb_skill s
            JOIN tb_skill_relation sr ON s.skill_cd = sr.skill_cd_to
            WHERE sr.skill_cd_from = $1 AND sr.relation_type IN ('builds_on', 'prerequisite')
        """
        rows = await execute_query(query, skill_cd)
        return [SkillResponse(**dict(row)) for row in rows]


# Singleton instance
skill_service = SkillService()
