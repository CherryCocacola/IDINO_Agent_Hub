"""Roadmap Service - Business Logic with DB Integration"""
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import date
import httpx
import json

from ..config import settings
from ..database import execute_raw_query, DatabasePool
from ..schemas.roadmap import (
    RoadmapItemResponse,
    GradeRoadmapResponse,
    SemesterRoadmap,
    RoadmapGenerateRequest,
    RoadmapGenerateResponse,
    RoadmapItemCreate,
    ItemType,
    ItemStatus,
)
import uuid

logger = logging.getLogger(__name__)


class RoadmapService:
    """Service for generating and managing student career roadmaps"""

    GRADE_NAMES = {
        1: "1학년",
        2: "2학년",
        3: "3학년",
        4: "4학년"
    }

    # Default competency targets by grade
    DEFAULT_COMPETENCY_TARGETS = {
        1: {"COMP01": 60, "COMP02": 55, "COMP03": 50, "COMP04": 55, "COMP05": 45, "COMP06": 50},
        2: {"COMP01": 70, "COMP02": 65, "COMP03": 60, "COMP04": 65, "COMP05": 55, "COMP06": 60},
        3: {"COMP01": 80, "COMP02": 75, "COMP03": 70, "COMP04": 75, "COMP05": 65, "COMP06": 70},
        4: {"COMP01": 90, "COMP02": 85, "COMP03": 80, "COMP04": 85, "COMP05": 75, "COMP06": 80},
    }

    # Key milestones by grade/semester (한글 - 전공 무관 범용)
    KEY_MILESTONES = {
        (1, 1): ["전공 기초과목 이수", "학습 습관 형성"],
        (1, 2): ["교양 필수 이수", "학과 활동 참여"],
        (2, 1): ["전공 심화과목 이수", "학생 단체 가입"],
        (2, 2): ["전공 역량 강화", "인턴십 탐색 준비"],
        (3, 1): ["인턴십/현장실습 확보", "자격증 취득 도전"],
        (3, 2): ["실무 프로젝트 수행", "전문가 네트워크 구축"],
        (4, 1): ["졸업 프로젝트 완료", "취업 준비 본격화"],
        (4, 2): ["성공적인 졸업", "취업 확정"],
    }

    def __init__(self, db_pool=None):
        self.db_pool = db_pool

    async def get_student_info(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Fetch student information from student service"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{settings.STUDENT_SERVICE_URL}/students/{student_id}"
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.warning(f"Failed to fetch student info: {e}")
        return None

    async def get_student_competencies(self, student_id: str) -> List[Dict[str, Any]]:
        """Fetch student competencies from competency service"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{settings.COMPETENCY_SERVICE_URL}/competency/{student_id}/scores"
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.warning(f"Failed to fetch competencies: {e}")
        return []

    async def get_student_skills(self, student_id: str) -> List[Dict[str, Any]]:
        """Fetch student skills from skill service"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{settings.SKILL_SERVICE_URL}/skills/student/{student_id}"
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.warning(f"Failed to fetch skills: {e}")
        return []

    async def get_grade_roadmap(
        self,
        student_id: str,
        grade_level: int
    ) -> GradeRoadmapResponse:
        """Get roadmap for a specific grade level"""
        # Get student info
        student = await self.get_student_info(student_id)
        current_grade = student.get("current_grade", 1) if student else 1
        career_goal = student.get("career_goal") if student else None
        department_cd = student.get("department_cd") if student else None

        # Build semester roadmaps
        semesters = []
        for sem in [1, 2]:
            items = await self._generate_semester_items(
                student_id, grade_level, sem, current_grade, department_cd
            )
            semester_roadmap = SemesterRoadmap(
                semester=sem,
                items=items,
                total_credits=sum(
                    item.credits if hasattr(item, 'credits') and item.credits else 3
                    for item in items if item.item_type == ItemType.COURSE
                ),
                target_gpa=3.5 + (0.1 * (grade_level - 1)),
                key_milestones=self._get_key_milestones(grade_level, sem)
            )
            semesters.append(semester_roadmap)

        # Calculate completion rate (IN_PROGRESS counts as 50%)
        all_items = [item for sem in semesters for item in sem.items]
        if all_items:
            weighted = sum(
                1.0 if item.status == ItemStatus.COMPLETED else
                0.5 if item.status == ItemStatus.IN_PROGRESS else
                0.0
                for item in all_items
            )
            completion_rate = weighted / len(all_items) * 100
        elif grade_level < current_grade:
            completion_rate = 100.0
        elif grade_level == current_grade:
            completion_rate = 50.0
        else:
            completion_rate = 0.0

        return GradeRoadmapResponse(
            student_id=student_id,
            grade_level=grade_level,
            grade_name=self.GRADE_NAMES.get(grade_level, f"{grade_level}학년"),
            semesters=semesters,
            competency_targets=self.DEFAULT_COMPETENCY_TARGETS.get(grade_level, {}),
            skill_targets=self._get_skill_targets(grade_level),
            career_path=career_goal,
            completion_rate=completion_rate
        )

    async def _generate_semester_items(
        self,
        student_id: str,
        grade_level: int,
        semester: int,
        current_grade: int,
        department_cd: Optional[str] = None
    ) -> List[RoadmapItemResponse]:
        """Generate roadmap items for a semester from DB"""
        items = []

        # Get student's actual completed courses
        completed_courses = await self._get_student_completed_courses(student_id)

        # Determine status based on actual enrollment or current grade fallback
        def get_course_status(course_cd: str, target_grade: int, target_sem: int) -> ItemStatus:
            # Check if student has actually taken this course
            if course_cd in completed_courses:
                enrollment = completed_courses[course_cd]
                status_cd = enrollment.get('status_cd', '')
                grade_letter = enrollment.get('grade_letter')

                # If has grade or status is completed/passed
                if grade_letter or status_cd in ('completed', 'passed', 'COMPLETED', 'PASSED'):
                    return ItemStatus.COMPLETED
                elif status_cd in ('enrolled', 'in_progress', 'ENROLLED', 'IN_PROGRESS'):
                    return ItemStatus.IN_PROGRESS

            # Fallback: grade-based estimation when no enrollment record found
            if target_grade < current_grade:
                return ItemStatus.COMPLETED
            elif target_grade == current_grade:
                if target_sem == 1:
                    return ItemStatus.COMPLETED
                else:
                    return ItemStatus.IN_PROGRESS
            return ItemStatus.PLANNED

        # Get courses from DB
        courses = await self._get_courses_from_db(grade_level, department_cd)
        for i, course in enumerate(courses):
            course_cd = course.get('course_cd', '')

            # Parse competency contributions - must be a dict for Pydantic
            competency_contributions = {}
            if course.get('competency_contributions'):
                try:
                    raw_contributions = course['competency_contributions']
                    # Parse JSON string if needed
                    if isinstance(raw_contributions, str):
                        raw_contributions = json.loads(raw_contributions)
                    # Convert list to dict
                    if isinstance(raw_contributions, list):
                        for contrib in raw_contributions:
                            if isinstance(contrib, dict) and contrib.get('competency_cd'):
                                competency_contributions[contrib['competency_cd']] = contrib.get('contribution_weight', 0.2)
                    elif isinstance(raw_contributions, dict):
                        competency_contributions = raw_contributions
                except Exception as e:
                    logger.warning(f"Failed to parse competency_contributions: {e}")
                    competency_contributions = {}

            # Determine priority based on course type (support Korean, English, and numeric)
            required_types = ('전공필수', '교양필수', 'major_required', 'general_required', '1', '3')
            course_type_str = str(course.get('course_type', ''))
            priority = 1 if course_type_str in required_types else 2

            # Get actual status for this specific course
            course_status = get_course_status(course_cd, grade_level, semester)

            # Get grade info if completed
            grade_info = None
            if course_cd in completed_courses:
                enrollment = completed_courses[course_cd]
                if enrollment.get('grade_letter'):
                    grade_info = f"{enrollment['grade_letter']} ({enrollment.get('term_nm', '')})"

            items.append(RoadmapItemResponse(
                item_id=f"CRS_{grade_level}_{semester}_{i+1}",
                item_type=ItemType.COURSE,
                title=course.get('course_nm', ''),
                description=grade_info or course.get('description'),
                grade_level=grade_level,
                semester=semester,
                status=course_status,
                priority=priority,
                competency_contributions=competency_contributions if competency_contributions else None,
                skill_contributions=None,
                is_ai_recommended=False
            ))

        # Get activities/programs from DB
        programs = await self._get_programs_from_db(grade_level, department_cd)

        # Determine default status for programs based on grade
        def get_program_status(target_grade: int) -> ItemStatus:
            if target_grade < current_grade:
                return ItemStatus.COMPLETED
            elif target_grade == current_grade:
                return ItemStatus.IN_PROGRESS
            return ItemStatus.PLANNED

        program_status = get_program_status(grade_level)

        for i, program in enumerate(programs):
            # Map program_type to ItemType
            type_mapping = {
                'internship': ItemType.INTERNSHIP,
                'certificate': ItemType.CERTIFICATE,
                'contest': ItemType.PROJECT,
                'project': ItemType.PROJECT,
                'club': ItemType.ACTIVITY,
                'volunteer': ItemType.ACTIVITY,
                'seminar': ItemType.ACTIVITY,
                'bootcamp': ItemType.ACTIVITY,
            }
            item_type = type_mapping.get(program.get('program_type', ''), ItemType.ACTIVITY)

            # Generate recommendation reason in Korean
            reason = self._generate_program_reason(program.get('program_type', ''), grade_level)

            items.append(RoadmapItemResponse(
                item_id=f"ACT_{grade_level}_{semester}_{i+1}",
                item_type=item_type,
                title=program.get('program_nm', ''),
                description=program.get('description'),
                grade_level=grade_level,
                semester=semester,
                status=program_status,
                priority=2 if program.get('program_type') == 'internship' else 3,
                is_ai_recommended=True,
                recommendation_reason=reason
            ))

        return items

    async def _get_courses_from_db(
        self,
        grade_level: int,
        department_cd: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get courses from database for the given grade level"""
        sql = """
            SELECT
                c.course_cd,
                c.course_nm,
                c.course_nm_en,
                c.credits,
                c.course_type,
                c.course_category,
                c.grade_level,
                c.description,
                COALESCE(
                    json_agg(
                        json_build_object(
                            'competency_cd', ccm.competency_cd,
                            'contribution_weight', ccm.contribution_weight
                        )
                    ) FILTER (WHERE ccm.competency_cd IS NOT NULL),
                    '[]'
                ) as competency_contributions
            FROM tb_course c
            LEFT JOIN tb_course_competency_map ccm ON c.course_cd = ccm.course_cd
            WHERE c.use_fg = 'Y'
              AND c.grade_level = $1
              AND (
                c.department_cd = $2
                OR (c.department_cd IS NULL AND c.course_type::text IN (
                    '교양필수', '교양선택', 'general_required', 'general_elective',
                    '3', '4'
                ))
              )
            GROUP BY c.course_cd, c.course_nm, c.course_nm_en, c.credits,
                     c.course_type, c.course_category, c.grade_level, c.description
            ORDER BY
                CASE c.course_type::text
                    WHEN '전공필수' THEN 1
                    WHEN 'major_required' THEN 1
                    WHEN '1' THEN 1
                    WHEN '전공선택' THEN 2
                    WHEN 'major_elective' THEN 2
                    WHEN '2' THEN 2
                    WHEN '교양필수' THEN 3
                    WHEN 'general_required' THEN 3
                    WHEN '3' THEN 3
                    WHEN '교양선택' THEN 4
                    WHEN 'general_elective' THEN 4
                    WHEN '4' THEN 4
                    ELSE 5
                END,
                c.course_nm
            LIMIT 12
        """
        try:
            if department_cd is None:
                logger.warning(f"No department_cd for grade {grade_level}, skipping course lookup")
                return []
            results = await execute_raw_query(sql, [grade_level, department_cd])
            return results
        except Exception as e:
            logger.error(f"Failed to get courses from DB: {e}")
            return []

    async def _map_department_to_dept_codes(self, department_cd: Optional[str]) -> List[str]:
        """학과 코드를 DEPT 카테고리 코드로 매핑"""
        if not department_cd:
            return []

        sql = """SELECT department_nm FROM tb_department WHERE department_cd = $1"""
        try:
            rows = await execute_raw_query(sql, [department_cd])
            dept_nm = rows[0].get('department_nm', '') if rows else ''
        except Exception:
            return []

        mapping = {
            'IT': ['DEPT001', 'DEPT002', 'DEPT013'],
            '공학': ['DEPT003', 'DEPT004', 'DEPT005', 'DEPT006', 'DEPT007', 'DEPT008'],
            '자연과학': ['DEPT009', 'DEPT010', 'DEPT011', 'DEPT012'],
            '경영': ['DEPT014', 'DEPT015', 'DEPT016', 'DEPT017'],
            '외국어': ['DEPT018', 'DEPT019'],
            '인문': ['DEPT020', 'DEPT021'],
            '사회과학': ['DEPT022', 'DEPT023', 'DEPT024'],
            '예술': ['DEPT025', 'DEPT026', 'DEPT027'],
            '보건의료': ['DEPT028', 'DEPT029'],
            '교육': ['DEPT030'],
        }
        # Order matters: specific patterns must be checked before generic ones
        # e.g. '보건의료' (제약, 약학) must come before '공학' to avoid '제약공학과' → 공학
        ordered_patterns = [
            ('보건의료', r'제약|약학|의예|의학|간호|보건|치료|병리|방사선|헬스케어|스포츠|체육|운동|동물|응급|치위생|치기공'),
            ('IT', r'소프트웨어|컴퓨터|AI|게임|반도체|전자공학|정보통신'),
            ('교육', r'교육|사범'),
            ('예술', r'음악|예술|미디어|디자인|영상|웹툰|멀티미디어|공연|애니메이션'),
            ('경영', r'경영|경제|비즈니스|회계|무역|통상|금융|세무'),
            ('사회과학', r'사회|법학|행정|공공|복지|경찰|심리|정치'),
            ('외국어', r'국제|어문|외국어|영어영문'),
            ('인문', r'인문|철학|문학|역사|문화콘텐츠|문화유산'),
            ('자연과학', r'식품|화학|물리|생명|수학|통계|바이오|신소재'),
            ('공학', r'공학|건축|나노|환경|기계|전기|로봇|소방|배터리|스마트물류'),
        ]
        for category, pattern in ordered_patterns:
            if re.search(pattern, dept_nm):
                return mapping[category]
        return []

    async def _get_programs_from_db(self, grade_level: int, department_cd: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recommended programs from database, filtered by department"""
        # Map grade to recommended program types
        grade_program_types = {
            1: ['certificate', 'club', 'project'],
            2: ['club', 'project', 'contest'],
            3: ['internship', 'certificate', 'contest'],
            4: ['internship', 'project'],
        }

        recommended_types = grade_program_types.get(grade_level, ['project'])

        # Map department_cd to DEPT codes for array overlap matching
        dept_codes = await self._map_department_to_dept_codes(department_cd)

        # UNION approach: department-specific first, then common programs only for empty slots
        sql = """
            WITH dept_programs AS (
                SELECT
                    p.program_cd,
                    p.program_nm,
                    p.program_type,
                    p.organizer,
                    p.description,
                    p.competency_contributions,
                    0 as priority_group
                FROM tb_program p
                WHERE p.use_fg = 'Y'
                  AND p.program_type = ANY($1::varchar[])
                  AND p.department_cds IS NOT NULL
                  AND p.department_cds && $2::varchar[]
            ),
            common_programs AS (
                SELECT
                    p.program_cd,
                    p.program_nm,
                    p.program_type,
                    p.organizer,
                    p.description,
                    p.competency_contributions,
                    1 as priority_group
                FROM tb_program p
                WHERE p.use_fg = 'Y'
                  AND p.program_type = ANY($1::varchar[])
                  AND p.department_cds IS NULL
                  AND (SELECT COUNT(*) FROM dept_programs) < 3
            ),
            combined AS (
                SELECT * FROM dept_programs
                UNION ALL
                SELECT * FROM common_programs
            )
            SELECT program_cd, program_nm, program_type, organizer, description, competency_contributions
            FROM combined
            ORDER BY
                priority_group,
                CASE program_type
                    WHEN 'internship' THEN 1
                    WHEN 'certificate' THEN 2
                    WHEN 'contest' THEN 3
                    ELSE 4
                END
            LIMIT 3
        """
        try:
            results = await execute_raw_query(sql, [recommended_types, dept_codes])
            return results
        except Exception as e:
            logger.error(f"Failed to get programs from DB: {e}")
            return []

    async def _get_student_completed_courses(self, student_id: str) -> Dict[str, Dict[str, Any]]:
        """Get student's completed/enrolled courses from tb_enrollment"""
        sql = """
            SELECT
                c.course_cd,
                c.course_nm,
                e.status_cd,
                g.grade_letter,
                g.grade_point,
                t.term_cd,
                t.term_nm
            FROM tb_enrollment e
            JOIN tb_course_offering co ON e.course_offering_id = co.offering_id
            JOIN tb_course c ON co.course_cd = c.course_cd
            JOIN tb_term t ON co.term_cd = t.term_cd
            LEFT JOIN tb_grade g ON e.enrollment_id = g.enrollment_id
            WHERE e.student_id = $1
        """
        try:
            results = await execute_raw_query(sql, [student_id])
            # Return dict keyed by course_cd for easy lookup
            return {
                r['course_cd']: {
                    'status_cd': r.get('status_cd'),
                    'grade_letter': r.get('grade_letter'),
                    'grade_point': r.get('grade_point'),
                    'term_cd': r.get('term_cd'),
                    'term_nm': r.get('term_nm'),
                }
                for r in results
            }
        except Exception as e:
            logger.error(f"Failed to get student completed courses: {e}")
            return {}

    def _generate_program_reason(self, program_type: str, grade_level: int) -> str:
        """Generate Korean recommendation reason for program"""
        reasons = {
            'internship': {
                3: "커리어 개발에 매우 중요한 현장 경험 기회입니다",
                4: "정규직 전환 기회가 있는 중요한 인턴십입니다"
            },
            'certificate': {
                1: "취업에 필수적인 기초 자격증입니다",
                2: "전공 역량을 증명할 수 있는 자격증입니다",
                3: "산업계 수요가 높은 전문 자격증입니다",
                4: "취업 경쟁력을 높이는 자격증입니다"
            },
            'contest': {
                2: "실무 경험과 포트폴리오를 쌓을 수 있습니다",
                3: "전공 역량을 검증받을 수 있는 기회입니다"
            },
            'club': {
                1: "팀워크 및 네트워킹 역량을 개발할 수 있습니다",
                2: "전공 관련 프로젝트 경험을 쌓을 수 있습니다"
            },
            'project': {
                1: "기술 역량 기초 구축에 도움이 됩니다",
                2: "실무 코딩 경험을 획득할 수 있습니다",
                4: "포트폴리오 완성에 필수적인 프로젝트입니다"
            },
            'volunteer': {
                1: "글로벌 역량과 리더십을 개발할 수 있습니다"
            },
            'bootcamp': {
                2: "집중적인 기술 역량 향상 기회입니다"
            }
        }

        type_reasons = reasons.get(program_type, {})
        return type_reasons.get(grade_level, "커리어 개발에 도움이 됩니다")

    def _get_key_milestones(self, grade: int, semester: int) -> List[str]:
        """Get key milestones for a semester"""
        return self.KEY_MILESTONES.get((grade, semester), [])

    def _get_skill_targets(self, grade: int) -> Dict[str, int]:
        """Get skill level targets by grade"""
        targets = {
            1: {"SK01": 2, "SK03": 1, "SK07": 2},
            2: {"SK01": 3, "SK02": 2, "SK03": 2, "SK10": 2},
            3: {"SK01": 4, "SK04": 3, "SK06": 3, "SK09": 2},
            4: {"SK01": 4, "SK04": 4, "SK06": 3, "SK12": 2},
        }
        return targets.get(grade, {})

    async def get_full_roadmap(self, student_id: str) -> List[GradeRoadmapResponse]:
        """Get complete 4-year roadmap for a student"""
        roadmaps = []
        for grade in range(1, 5):
            roadmap = await self.get_grade_roadmap(student_id, grade)
            roadmaps.append(roadmap)
        return roadmaps

    async def _call_ai_service_for_roadmap(
        self,
        student_id: str,
        target_role: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Call AI service (GPT) for roadmap summary and recommendations via tool calling."""
        task_description = "학생의 프로필, 역량, 졸업생 패턴을 분석하여 맞춤형 커리어 로드맵 요약과 추천을 생성해주세요"
        if target_role:
            task_description += f" (목표 직무: {target_role})"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.AI_SERVICE_URL}/ai/recommendations/tools",
                    json={
                        "student_id": student_id,
                        "task": task_description,
                        "max_tool_calls": 3,
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    logger.info(
                        f"AI roadmap generated for {student_id}, "
                        f"tool_calls_made={data.get('tool_calls_made', 0)}"
                    )
                    return data
                else:
                    logger.warning(
                        f"AI service returned {response.status_code}: {response.text[:200]}"
                    )
        except Exception as e:
            logger.warning(f"AI service call failed for roadmap: {e}")
        return None

    async def generate_ai_roadmap(
        self,
        request: RoadmapGenerateRequest
    ) -> RoadmapGenerateResponse:
        """Generate AI-optimized roadmap based on student goals"""
        # Get basic roadmap
        roadmaps = await self.get_full_roadmap(request.student_id)

        # Get current student data
        student = await self.get_student_info(request.student_id)
        competencies = await self.get_student_competencies(request.student_id)
        skills = await self.get_student_skills(request.student_id)

        # Try AI service (GPT) for summary and recommendations
        ai_result = await self._call_ai_service_for_roadmap(
            request.student_id, request.target_role
        )

        if ai_result and ai_result.get("summary"):
            # Use GPT-generated summary and recommendations
            ai_summary = ai_result["summary"]
            raw_recs = ai_result.get("recommendations", [])
            recommendations = [
                r.get("title", "") + ": " + r.get("description", "")
                if isinstance(r, dict) else str(r)
                for r in raw_recs[:5]
            ]
            if not recommendations:
                recommendations = self._generate_recommendations(
                    student, competencies, skills, request.target_role
                )
            confidence_score = 0.92
        else:
            # Fallback to template-based summary and recommendations
            ai_summary = self._generate_ai_summary(
                student, competencies, skills, request.target_role
            )
            recommendations = self._generate_recommendations(
                student, competencies, skills, request.target_role
            )
            confidence_score = 0.85

        return RoadmapGenerateResponse(
            student_id=request.student_id,
            roadmaps=roadmaps,
            ai_summary=ai_summary,
            key_recommendations=recommendations,
            alternative_paths=[],
            confidence_score=confidence_score
        )

    def _generate_ai_summary(
        self,
        student: Optional[Dict],
        competencies: List[Dict],
        skills: List[Dict],
        target_role: Optional[str]
    ) -> str:
        """Generate AI summary for the roadmap (Korean)"""
        if not student:
            return "학생 데이터가 없어 맞춤형 요약을 생성할 수 없습니다."

        name = student.get("student_nm", "학생")
        grade = student.get("current_grade", 1)
        goal = target_role or student.get("career_goal", "미정")

        return (
            f"{name}님은 현재 {grade}학년으로, '{goal}'을(를) 목표로 하고 있습니다. "
            f"본 로드맵은 커리어 준비를 위한 체계적인 경로를 제공합니다. "
            f"기술 역량 강화와 함께 리더십 및 커뮤니케이션 능력 개발에 집중하시기 바랍니다."
        )

    # Department-specific recommendation templates
    DEPARTMENT_RECOMMENDATIONS = {
        '의예': [
            "국가고시 준비를 체계적으로 시작하세요",
            "임상실습 경험을 최대한 활용하세요",
            "의료 관련 자격증 및 면허 취득을 준비하세요",
            "전문의 수련 분야를 탐색하세요",
            "학술 논문 작성 및 연구 활동에 참여하세요"
        ],
        '간호': [
            "간호사 국가고시 준비를 체계적으로 시작하세요",
            "임상실습에서 다양한 간호 영역을 경험하세요",
            "BLS/ACLS 자격을 취득하세요",
            "전문간호사 과정을 탐색하세요",
            "병원 인턴십을 통해 실무 역량을 강화하세요"
        ],
        '약학': [
            "약사 국가고시 준비를 체계적으로 시작하세요",
            "조제 실습 경험을 충분히 쌓으세요",
            "임상약학 분야를 심화 학습하세요",
            "제약회사 인턴십을 탐색하세요",
            "약물 상호작용 및 약리학 지식을 강화하세요"
        ],
        '물리치료': [
            "물리치료사 국가고시를 준비하세요",
            "재활병원 실습 경험을 충분히 쌓으세요",
            "도수치료, 운동치료 등 전문 분야를 탐색하세요",
            "스포츠재활 관련 자격을 취득하세요",
            "환자 사례 관리 경험을 쌓으세요"
        ],
        '스포츠': [
            "운동처방사 또는 스포츠트레이너 자격을 취득하세요",
            "현장 실습(스포츠센터, 재활센터)을 경험하세요",
            "운동생리학 및 체력측정 역량을 강화하세요",
            "스포츠 관련 대회 및 봉사활동에 참여하세요",
            "관련 자격증(생활체육지도사, 건강운동관리사)을 취득하세요"
        ],
        '교육': [
            "교원임용시험 준비를 체계적으로 시작하세요",
            "교육실습에서 수업 지도 역량을 키우세요",
            "교육봉사 활동을 통해 현장 경험을 쌓으세요",
            "학습지도안 작성 및 교과 연구를 꾸준히 하세요",
            "다양한 교수법과 교육 기술을 학습하세요"
        ],
        '경영': [
            "전문 자격증(CPA, 경영지도사 등)을 준비하세요",
            "기업 인턴십을 통해 실무 경험을 쌓으세요",
            "재무분석 및 마케팅 역량을 강화하세요",
            "비즈니스 공모전에 참가하세요",
            "산업 동향 분석과 사례 연구를 꾸준히 하세요"
        ],
        '디자인': [
            "포트폴리오를 체계적으로 구축하세요",
            "디자인 공모전 및 전시에 참가하세요",
            "그래픽/영상 관련 자격증을 취득하세요",
            "에이전시 또는 스튜디오 인턴십을 경험하세요",
            "최신 디자인 트렌드와 도구를 학습하세요"
        ],
        '공학': [
            "기사 자격증(기계, 전기, 토목 등)을 취득하세요",
            "현장실습 및 산학협력 프로젝트에 참여하세요",
            "CAD/CAM 등 설계 도구 활용 능력을 키우세요",
            "안전관리 및 품질관리 역량을 강화하세요",
            "졸업 프로젝트에서 실무형 과제를 수행하세요"
        ],
        '사회': [
            "관련 자격증(사회복지사, 상담심리사 등)을 취득하세요",
            "현장실습을 통해 실무 경험을 쌓으세요",
            "봉사활동과 사회 참여를 꾸준히 하세요",
            "사례관리 및 상담 역량을 강화하세요",
            "공무원 시험 등 진로 경로를 탐색하세요"
        ],
        '인문': [
            "어학 자격증(TOEIC, TOEFL 등)을 취득하세요",
            "관련 분야 인턴십 및 현장실습을 경험하세요",
            "학술 논문 작성 및 연구 활동에 참여하세요",
            "대학원 진학 여부를 검토하세요",
            "전문 자격증을 통해 취업 경쟁력을 높이세요"
        ],
        'IT': [
            "초기 학기에 핵심 프로그래밍 과목을 우선 이수하세요",
            "2학년부터 인턴십 기회를 탐색하세요",
            "개인 프로젝트 포트폴리오를 구축하세요",
            "팀 프로젝트와 발표를 통해 소프트 스킬을 개발하세요",
            "세미나와 행사를 통해 산업계 전문가와 네트워킹하세요"
        ],
    }

    def _get_department_category(self, department_nm: Optional[str]) -> str:
        """Map department name to recommendation category."""
        if not department_nm:
            return 'IT'

        nm = department_nm
        if any(k in nm for k in ['의예', '의학', '의생명']):
            return '의예'
        if '간호' in nm:
            return '간호'
        if any(k in nm for k in ['약학', '제약']):
            return '약학'
        if '물리치료' in nm:
            return '물리치료'
        if any(k in nm for k in ['스포츠', '헬스케어', '체육', '운동']):
            return '스포츠'
        if any(k in nm for k in ['교육', '사범']):
            return '교육'
        if any(k in nm for k in ['경영', '경제', '회계', '금융', '무역', '통상']):
            return '경영'
        if any(k in nm for k in ['디자인', '미술', '영상', '미디어', '애니메이션', '음악', '공연']):
            return '디자인'
        if any(k in nm for k in ['기계', '전기', '토목', '건축', '건설', '로봇', '화공', '재료', '소방', '나노', '산업']):
            return '공학'
        if any(k in nm for k in ['사회복지', '심리', '행정', '정치', '법학', '경찰']):
            return '사회'
        if any(k in nm for k in ['어문', '인문', '역사', '문화', '영어', '통일', '철학']):
            return '인문'
        if any(k in nm for k in ['컴퓨터', '소프트웨어', '정보', 'AI', '반도체', '전자', '게임', '멀티미디어', '정보통신']):
            return 'IT'
        if any(k in nm for k in ['보건', '임상', '치위생', '방사선', '치기공', '응급']):
            return '간호'  # medical category
        if any(k in nm for k in ['생명', '화학', '환경', '바이오', '통계']):
            return '공학'

        return 'IT'  # default fallback

    def _generate_recommendations(
        self,
        student: Optional[Dict],
        competencies: List[Dict],
        skills: List[Dict],
        target_role: Optional[str]
    ) -> List[str]:
        """Generate department-specific key recommendations (Korean)"""
        # Determine department name
        department_nm = None
        if student:
            dept = student.get('department', {})
            if isinstance(dept, dict):
                department_nm = dept.get('department_nm')
            if not department_nm:
                department_nm = student.get('department_nm')

        # Get department-specific recommendations
        category = self._get_department_category(department_nm)
        recommendations = list(self.DEPARTMENT_RECOMMENDATIONS.get(
            category,
            self.DEPARTMENT_RECOMMENDATIONS['IT']
        ))

        # Add role-specific recommendations if target_role specified
        if target_role:
            role_lower = target_role.lower()
            if "데이터" in role_lower or "data" in role_lower:
                recommendations.insert(0, "통계학과 머신러닝 과목에 집중하세요")
            elif "웹" in role_lower or "web" in role_lower:
                recommendations.insert(0, "웹 개발과 UX 디자인 과목을 우선 이수하세요")
            elif "백엔드" in role_lower or "backend" in role_lower:
                recommendations.insert(0, "데이터베이스와 서버 아키텍처 과목을 집중 이수하세요")
            elif "프론트엔드" in role_lower or "frontend" in role_lower:
                recommendations.insert(0, "UI/UX와 프론트엔드 프레임워크 학습에 집중하세요")

        return recommendations[:5]

    async def create_roadmap_item(
        self,
        item: RoadmapItemCreate
    ) -> RoadmapItemResponse:
        """Create a new roadmap item for a student"""
        # Generate unique item ID
        item_id = f"CUSTOM_{item.student_id}_{uuid.uuid4().hex[:8]}"

        # Create response object
        return RoadmapItemResponse(
            item_id=item_id,
            item_type=item.item_type,
            title=item.title,
            description=item.description,
            grade_level=item.grade_level,
            semester=item.semester,
            status=item.status,
            priority=item.priority,
            is_ai_recommended=item.is_ai_recommended,
            recommendation_reason=item.recommendation_reason,
        )
