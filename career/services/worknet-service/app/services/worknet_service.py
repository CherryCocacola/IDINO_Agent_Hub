"""WorkNet Diagnosis Service - Business Logic"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from ..config import settings
from ..database import get_pool
from ..schemas.worknet import (
    DiagnosisType,
    DiagnosisStatus,
    DiagnosisSessionCreate,
    DiagnosisSessionResponse,
    DiagnosisSessionListResponse,
    DiagnosisResultResponse,
    DiagnosisResultListResponse,
    DiagnosisScoreCategory,
    OccupationMatch,
    CareerRecommendation,
    WorkNetCallbackData,
    WorkNetAuthResponse,
    DiagnosisSummary,
)


class WorkNetService:
    """Service for WorkNet Diagnosis Integration"""

    # Diagnosis type metadata
    DIAGNOSIS_INFO = {
        DiagnosisType.APTITUDE: {
            "name": "직업적성검사",
            "name_en": "Vocational Aptitude Test",
            "duration_minutes": 50,
            "description": "9가지 적성요인을 측정하여 적합 직업 추천",
        },
        DiagnosisType.INTEREST: {
            "name": "직업흥미검사",
            "name_en": "Vocational Interest Test",
            "duration_minutes": 30,
            "description": "Holland 유형 기반 직업흥미 분석",
        },
        DiagnosisType.VALUES: {
            "name": "직업가치관검사",
            "name_en": "Work Values Test",
            "duration_minutes": 25,
            "description": "직업 선택 시 중요하게 생각하는 가치 분석",
        },
        DiagnosisType.PERSONALITY: {
            "name": "성인용 직업성격검사",
            "name_en": "Adult Vocational Personality Test",
            "duration_minutes": 40,
            "description": "MBTI 기반 직업성격 유형 분석",
        },
        DiagnosisType.ENTREPRENEURSHIP: {
            "name": "창업적성검사",
            "name_en": "Entrepreneurship Aptitude Test",
            "duration_minutes": 35,
            "description": "창업 적합성 및 역량 분석",
        },
        DiagnosisType.CAREER_MATURITY: {
            "name": "진로성숙도검사",
            "name_en": "Career Maturity Test",
            "duration_minutes": 30,
            "description": "진로 결정 및 준비도 분석",
        },
    }

    async def create_session(
        self, data: DiagnosisSessionCreate
    ) -> DiagnosisSessionResponse:
        """Create a new diagnosis session"""
        pool = await get_pool()
        session_id = f"WKN-{uuid.uuid4().hex[:12].upper()}"
        now = datetime.now()
        expires_at = now + timedelta(hours=24)  # 24-hour session expiry

        # Generate WorkNet URL (simulated - actual integration would use API)
        worknet_url = self._generate_worknet_url(session_id, data.diagnosis_type)

        async with pool.acquire() as conn:
            await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}")

            # Check for existing active session
            existing = await conn.fetchrow(
                """
                SELECT session_id FROM tb_worknet_sessions
                WHERE student_id = $1
                AND diagnosis_type = $2
                AND status IN ('initiated', 'in_progress')
                AND expires_at > NOW()
                """,
                data.student_id,
                data.diagnosis_type.value,
            )

            if existing:
                # Return existing session
                return await self.get_session(existing["session_id"])

            # Create new session
            await conn.execute(
                """
                INSERT INTO tb_worknet_sessions (
                    session_id, student_id, diagnosis_type, status,
                    worknet_url, callback_url, metadata,
                    expires_at, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                session_id,
                data.student_id,
                data.diagnosis_type.value,
                DiagnosisStatus.INITIATED.value,
                worknet_url,
                data.callback_url,
                str(data.metadata) if data.metadata else None,
                expires_at,
                now,
            )

        return DiagnosisSessionResponse(
            session_id=session_id,
            student_id=data.student_id,
            diagnosis_type=data.diagnosis_type,
            status=DiagnosisStatus.INITIATED,
            worknet_url=worknet_url,
            expires_at=expires_at,
            created_at=now,
            updated_at=None,
            message=f"세션이 생성되었습니다. {self.DIAGNOSIS_INFO[data.diagnosis_type]['name']} 진행을 위해 WorkNet 링크를 클릭하세요.",
        )

    async def get_session(self, session_id: str) -> Optional[DiagnosisSessionResponse]:
        """Get session by ID"""
        pool = await get_pool()

        async with pool.acquire() as conn:
            await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}")

            row = await conn.fetchrow(
                """
                SELECT session_id, student_id, diagnosis_type, status,
                       worknet_url, expires_at, created_at, updated_at
                FROM tb_worknet_sessions
                WHERE session_id = $1
                """,
                session_id,
            )

            if not row:
                return None

            return DiagnosisSessionResponse(
                session_id=row["session_id"],
                student_id=row["student_id"],
                diagnosis_type=DiagnosisType(row["diagnosis_type"]),
                status=DiagnosisStatus(row["status"]),
                worknet_url=row["worknet_url"],
                expires_at=row["expires_at"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                message=None,
            )

    async def get_student_sessions(
        self, student_id: str
    ) -> DiagnosisSessionListResponse:
        """Get all sessions for a student"""
        pool = await get_pool()

        async with pool.acquire() as conn:
            await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}")

            rows = await conn.fetch(
                """
                SELECT session_id, student_id, diagnosis_type, status,
                       worknet_url, expires_at, created_at, updated_at
                FROM tb_worknet_sessions
                WHERE student_id = $1
                ORDER BY created_at DESC
                """,
                student_id,
            )

            sessions = [
                DiagnosisSessionResponse(
                    session_id=row["session_id"],
                    student_id=row["student_id"],
                    diagnosis_type=DiagnosisType(row["diagnosis_type"]),
                    status=DiagnosisStatus(row["status"]),
                    worknet_url=row["worknet_url"],
                    expires_at=row["expires_at"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    message=None,
                )
                for row in rows
            ]

            return DiagnosisSessionListResponse(
                student_id=student_id,
                total_count=len(sessions),
                sessions=sessions,
            )

    async def update_session_status(
        self, session_id: str, status: DiagnosisStatus
    ) -> Optional[DiagnosisSessionResponse]:
        """Update session status"""
        pool = await get_pool()

        async with pool.acquire() as conn:
            await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}")

            await conn.execute(
                """
                UPDATE tb_worknet_sessions
                SET status = $1, updated_at = NOW()
                WHERE session_id = $2
                """,
                status.value,
                session_id,
            )

        return await self.get_session(session_id)

    async def process_callback(
        self, callback_data: WorkNetCallbackData
    ) -> Optional[DiagnosisResultResponse]:
        """Process callback from WorkNet with results"""
        pool = await get_pool()

        # Get session info
        session = await self.get_session(callback_data.session_id)
        if not session:
            return None

        # Update session status
        if callback_data.status == "completed":
            await self.update_session_status(
                callback_data.session_id, DiagnosisStatus.COMPLETED
            )

            # Parse and store results
            if callback_data.result_data:
                return await self._store_result(
                    session, callback_data.result_data, callback_data.completed_at
                )
        elif callback_data.status == "error":
            await self.update_session_status(
                callback_data.session_id, DiagnosisStatus.ERROR
            )

        return None

    async def _store_result(
        self,
        session: DiagnosisSessionResponse,
        result_data: Dict[str, Any],
        completed_at: Optional[datetime],
    ) -> DiagnosisResultResponse:
        """Store diagnosis result in database"""
        pool = await get_pool()
        result_id = f"RES-{uuid.uuid4().hex[:12].upper()}"
        now = completed_at or datetime.now()
        valid_until = now + timedelta(days=settings.RESULT_RETENTION_DAYS)

        # Parse result data (simulated parsing)
        parsed_result = self._parse_worknet_result(
            session.diagnosis_type, result_data
        )

        async with pool.acquire() as conn:
            await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}")

            await conn.execute(
                """
                INSERT INTO tb_worknet_results (
                    result_id, session_id, student_id, diagnosis_type,
                    overall_score, overall_percentile, overall_interpretation,
                    category_scores, occupation_matches, recommendations,
                    raw_data, completed_at, valid_until, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                """,
                result_id,
                session.session_id,
                session.student_id,
                session.diagnosis_type.value,
                parsed_result.get("overall_score"),
                parsed_result.get("overall_percentile"),
                parsed_result.get("overall_interpretation"),
                str(parsed_result.get("category_scores", [])),
                str(parsed_result.get("occupation_matches", [])),
                str(parsed_result.get("recommendations", [])),
                str(result_data),
                now,
                valid_until,
                now,
            )

        return await self.get_result(result_id)

    def _parse_worknet_result(
        self, diagnosis_type: DiagnosisType, raw_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse WorkNet result data into structured format"""
        # This would contain actual parsing logic for WorkNet API response
        # For now, returning structured placeholder
        return {
            "overall_score": raw_data.get("score", 75.0),
            "overall_percentile": raw_data.get("percentile", 65.0),
            "overall_interpretation": raw_data.get(
                "interpretation", "평균 이상의 적성을 보이고 있습니다."
            ),
            "category_scores": raw_data.get("categories", []),
            "occupation_matches": raw_data.get("occupations", []),
            "recommendations": raw_data.get("recommendations", []),
        }

    async def get_result(self, result_id: str) -> Optional[DiagnosisResultResponse]:
        """Get result by ID"""
        pool = await get_pool()

        async with pool.acquire() as conn:
            await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}")

            row = await conn.fetchrow(
                """
                SELECT result_id, session_id, student_id, diagnosis_type,
                       overall_score, overall_percentile, overall_interpretation,
                       category_scores, occupation_matches, recommendations,
                       raw_data, completed_at, valid_until, worknet_result_url
                FROM tb_worknet_results
                WHERE result_id = $1
                """,
                result_id,
            )

            if not row:
                return None

            return self._row_to_result(row)

    async def get_student_results(
        self,
        student_id: str,
        diagnosis_type: Optional[DiagnosisType] = None,
    ) -> DiagnosisResultListResponse:
        """Get all results for a student, optionally filtered by type"""
        pool = await get_pool()

        async with pool.acquire() as conn:
            await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}")

            if diagnosis_type:
                rows = await conn.fetch(
                    """
                    SELECT result_id, session_id, student_id, diagnosis_type,
                           overall_score, overall_percentile, overall_interpretation,
                           category_scores, occupation_matches, recommendations,
                           raw_data, completed_at, valid_until, worknet_result_url
                    FROM tb_worknet_results
                    WHERE student_id = $1 AND diagnosis_type = $2
                    ORDER BY completed_at DESC
                    """,
                    student_id,
                    diagnosis_type.value,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT result_id, session_id, student_id, diagnosis_type,
                           overall_score, overall_percentile, overall_interpretation,
                           category_scores, occupation_matches, recommendations,
                           raw_data, completed_at, valid_until, worknet_result_url
                    FROM tb_worknet_results
                    WHERE student_id = $1
                    ORDER BY completed_at DESC
                    """,
                    student_id,
                )

            results = [self._row_to_result(row) for row in rows]

            return DiagnosisResultListResponse(
                student_id=student_id,
                total_count=len(results),
                results=results,
            )

    async def get_latest_results(
        self, student_id: str
    ) -> Dict[str, DiagnosisResultResponse]:
        """Get latest result for each diagnosis type"""
        pool = await get_pool()
        latest = {}

        async with pool.acquire() as conn:
            await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}")

            for dtype in DiagnosisType:
                row = await conn.fetchrow(
                    """
                    SELECT result_id, session_id, student_id, diagnosis_type,
                           overall_score, overall_percentile, overall_interpretation,
                           category_scores, occupation_matches, recommendations,
                           raw_data, completed_at, valid_until, worknet_result_url
                    FROM tb_worknet_results
                    WHERE student_id = $1 AND diagnosis_type = $2
                    ORDER BY completed_at DESC
                    LIMIT 1
                    """,
                    student_id,
                    dtype.value,
                )
                if row:
                    latest[dtype.value] = self._row_to_result(row)

        return latest

    async def get_diagnosis_summary(self, student_id: str) -> DiagnosisSummary:
        """Get comprehensive diagnosis summary for a student"""
        pool = await get_pool()

        async with pool.acquire() as conn:
            await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}")

            # Get counts
            counts = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed
                FROM tb_worknet_sessions
                WHERE student_id = $1
                """,
                student_id,
            )

        latest_results = await self.get_latest_results(student_id)

        # Aggregate top occupation matches across all results
        all_occupations = []
        all_recommendations = []
        for result in latest_results.values():
            all_occupations.extend(result.occupation_matches[:3])
            all_recommendations.extend(result.recommendations[:2])

        # Sort and deduplicate
        top_occupations = sorted(
            all_occupations, key=lambda x: x.match_score, reverse=True
        )[:5]
        top_recommendations = sorted(
            all_recommendations, key=lambda x: x.priority
        )[:5]

        return DiagnosisSummary(
            student_id=student_id,
            total_tests_taken=counts["total"] or 0,
            completed_tests=counts["completed"] or 0,
            latest_results=latest_results,
            overall_career_profile=self._generate_career_profile(latest_results),
            top_occupation_matches=top_occupations,
            top_recommendations=top_recommendations,
            last_updated=datetime.now(),
        )

    def _generate_career_profile(
        self, results: Dict[str, DiagnosisResultResponse]
    ) -> Dict[str, Any]:
        """Generate overall career profile from multiple diagnosis results"""
        if not results:
            return None

        profile = {
            "strengths": [],
            "areas_for_development": [],
            "preferred_work_environment": [],
            "suitable_industries": [],
        }

        # Aggregate insights from different diagnosis types
        if DiagnosisType.APTITUDE.value in results:
            profile["strengths"].append("적성 분석 완료")

        if DiagnosisType.INTEREST.value in results:
            profile["preferred_work_environment"].append("흥미 분석 완료")

        if DiagnosisType.VALUES.value in results:
            profile["suitable_industries"].append("가치관 분석 완료")

        return profile

    def _row_to_result(self, row) -> DiagnosisResultResponse:
        """Convert database row to result response"""
        # Parse stored JSON strings (simplified)
        category_scores = []
        occupation_matches = []
        recommendations = []

        return DiagnosisResultResponse(
            result_id=row["result_id"],
            session_id=row["session_id"],
            student_id=row["student_id"],
            diagnosis_type=DiagnosisType(row["diagnosis_type"]),
            overall_score=row["overall_score"],
            overall_percentile=row["overall_percentile"],
            overall_interpretation=row["overall_interpretation"],
            category_scores=category_scores,
            occupation_matches=occupation_matches,
            recommendations=recommendations,
            raw_data=None,  # Don't expose raw data in response
            completed_at=row["completed_at"],
            valid_until=row["valid_until"],
            worknet_result_url=row.get("worknet_result_url"),
        )

    def _generate_worknet_url(
        self, session_id: str, diagnosis_type: DiagnosisType
    ) -> str:
        """Generate URL to WorkNet diagnosis page"""
        # This would be the actual WorkNet API integration
        base_url = settings.WORKNET_API_BASE_URL
        return f"{base_url}/test/{diagnosis_type.value}?session={session_id}"

    def get_diagnosis_types_info(self) -> List[Dict[str, Any]]:
        """Get information about all available diagnosis types"""
        return [
            {
                "type": dtype.value,
                "name": info["name"],
                "name_en": info["name_en"],
                "duration_minutes": info["duration_minutes"],
                "description": info["description"],
            }
            for dtype, info in self.DIAGNOSIS_INFO.items()
        ]
