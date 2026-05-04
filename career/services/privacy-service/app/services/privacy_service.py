"""Privacy Service - Data Subject Rights Business Logic"""
import logging
import uuid
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import httpx

from ..config import settings
from ..database import get_db_pool
from ..schemas.privacy import (
    RequestType,
    RequestStatus,
    ConsentType,
    DataSubjectRequestCreate,
    DataSubjectRequestResponse,
    DataSubjectRequestListResponse,
    ConsentCreate,
    ConsentResponse,
    ConsentListResponse,
    DataAccessResponse,
    DataExportResponse,
    ErasureResponse,
)

logger = logging.getLogger(__name__)


class PrivacyService:
    """Service for managing data subject rights (GDPR/PIPA compliance)"""

    # Data categories and their tables
    DATA_CATEGORIES = {
        "personal_info": ["tb_student", "tb_user"],
        "academic_records": ["tb_enrollment", "tb_grade"],
        "competency_data": ["tb_student_competency", "tb_student_skill"],
        "activity_records": ["tb_activity", "tb_achievement"],
        "portfolio": ["tb_portfolio"],
        "coaching_data": ["tb_coaching_goal", "tb_coaching_plan"],
        "simulation_data": ["tb_simulation_scenario"],
        "risk_alerts": ["tb_risk_alert"],
        "badges": ["tb_student_badge"],
        "opportunities": ["tb_opportunity_application"],
    }

    # Data that must be retained for legal/regulatory reasons
    LEGALLY_REQUIRED_DATA = ["tb_enrollment", "tb_grade"]  # Academic records
    RETENTION_REASON = "Academic records must be retained for regulatory compliance (Higher Education Act)"

    # ==================== Data Subject Requests ====================

    async def create_request(
        self,
        data: DataSubjectRequestCreate
    ) -> DataSubjectRequestResponse:
        """Create a new data subject request"""
        pool = await get_db_pool()
        request_id = str(uuid.uuid4())

        async with pool.acquire() as conn:
            await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}")

            # Check if table exists, create if not
            await self._ensure_privacy_tables(conn)

            row = await conn.fetchrow(
                """
                INSERT INTO tb_data_subject_request (
                    request_id, student_id, request_type, status,
                    description, contact_email, ins_user_id, ins_dt
                )
                VALUES ($1, $2, $3, $4, $5, $6, 'SYSTEM', CURRENT_TIMESTAMP)
                RETURNING request_id, student_id, request_type, status,
                          description, ins_dt as created_at, upd_dt as updated_at,
                          completed_at
                """,
                request_id,
                data.student_id,
                data.request_type.value,
                RequestStatus.PENDING.value,
                data.description,
                data.contact_email
            )

            logger.info(f"Created {data.request_type.value} request for student {data.student_id}")

            return DataSubjectRequestResponse(
                request_id=row['request_id'],
                student_id=row['student_id'],
                request_type=RequestType(row['request_type']),
                status=RequestStatus(row['status']),
                description=row['description'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                completed_at=row['completed_at'],
                estimated_completion=datetime.now() + timedelta(days=settings.REQUEST_PROCESSING_DAYS),
                message=f"Your {data.request_type.value} request has been received. Expected processing time: {settings.REQUEST_PROCESSING_DAYS} days."
            )

    async def get_requests(self, student_id: str) -> DataSubjectRequestListResponse:
        """Get all data subject requests for a student"""
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}")
            await self._ensure_privacy_tables(conn)

            rows = await conn.fetch(
                """
                SELECT request_id, student_id, request_type, status,
                       description, ins_dt as created_at, upd_dt as updated_at,
                       completed_at
                FROM tb_data_subject_request
                WHERE student_id = $1
                ORDER BY ins_dt DESC
                """,
                student_id
            )

            requests = [
                DataSubjectRequestResponse(
                    request_id=row['request_id'],
                    student_id=row['student_id'],
                    request_type=RequestType(row['request_type']),
                    status=RequestStatus(row['status']),
                    description=row['description'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    completed_at=row['completed_at'],
                    estimated_completion=None,
                    message=None
                )
                for row in rows
            ]

            return DataSubjectRequestListResponse(
                student_id=student_id,
                total_count=len(requests),
                requests=requests
            )

    async def get_request_status(self, request_id: str) -> Optional[DataSubjectRequestResponse]:
        """Get status of a specific request"""
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}")

            row = await conn.fetchrow(
                """
                SELECT request_id, student_id, request_type, status,
                       description, ins_dt as created_at, upd_dt as updated_at,
                       completed_at
                FROM tb_data_subject_request
                WHERE request_id = $1
                """,
                request_id
            )

            if not row:
                return None

            return DataSubjectRequestResponse(
                request_id=row['request_id'],
                student_id=row['student_id'],
                request_type=RequestType(row['request_type']),
                status=RequestStatus(row['status']),
                description=row['description'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                completed_at=row['completed_at'],
                estimated_completion=None,
                message=None
            )

    # ==================== Right to Access ====================

    async def process_access_request(self, student_id: str, request_id: str) -> DataAccessResponse:
        """Process a data access request - return all personal data"""
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}")

            # Update request status
            await conn.execute(
                """
                UPDATE tb_data_subject_request
                SET status = $1, upd_dt = CURRENT_TIMESTAMP
                WHERE request_id = $2
                """,
                RequestStatus.IN_PROGRESS.value,
                request_id
            )

            # Collect all personal data
            personal_data = {}

            # Student info
            student_row = await conn.fetchrow(
                "SELECT * FROM tb_student WHERE student_id = $1",
                student_id
            )
            if student_row:
                personal_data["student_info"] = dict(student_row)

            # User info (excluding password)
            user_row = await conn.fetchrow(
                """
                SELECT user_id, login_id, email, role_level, mfa_enabled,
                       last_login_dt, ins_dt
                FROM tb_user WHERE login_id = $1
                """,
                student_id
            )
            if user_row:
                personal_data["user_account"] = dict(user_row)

            # Enrollments
            enrollments = await conn.fetch(
                "SELECT * FROM tb_enrollment WHERE student_id = $1",
                student_id
            )
            personal_data["enrollments"] = [dict(r) for r in enrollments]

            # Grades
            grades = await conn.fetch(
                "SELECT * FROM tb_grade WHERE student_id = $1",
                student_id
            )
            personal_data["grades"] = [dict(r) for r in grades]

            # Competencies
            competencies = await conn.fetch(
                "SELECT * FROM tb_student_competency WHERE student_id = $1",
                student_id
            )
            personal_data["competencies"] = [dict(r) for r in competencies]

            # Skills
            skills = await conn.fetch(
                "SELECT * FROM tb_student_skill WHERE student_id = $1",
                student_id
            )
            personal_data["skills"] = [dict(r) for r in skills]

            # Activities
            activities = await conn.fetch(
                "SELECT * FROM tb_activity WHERE student_id = $1",
                student_id
            )
            personal_data["activities"] = [dict(r) for r in activities]

            # Portfolio
            portfolio = await conn.fetch(
                "SELECT * FROM tb_portfolio WHERE student_id = $1",
                student_id
            )
            personal_data["portfolio"] = [dict(r) for r in portfolio]

            # Badges
            badges = await conn.fetch(
                "SELECT * FROM tb_student_badge WHERE student_id = $1",
                student_id
            )
            personal_data["badges"] = [dict(r) for r in badges]

            # Mark request as completed
            await conn.execute(
                """
                UPDATE tb_data_subject_request
                SET status = $1, completed_at = CURRENT_TIMESTAMP, upd_dt = CURRENT_TIMESTAMP
                WHERE request_id = $2
                """,
                RequestStatus.COMPLETED.value,
                request_id
            )

            return DataAccessResponse(
                student_id=student_id,
                request_id=request_id,
                data_categories=list(self.DATA_CATEGORIES.keys()),
                personal_data=self._serialize_data(personal_data),
                processing_purposes=[
                    "Educational services",
                    "Career guidance",
                    "Competency assessment",
                    "Academic record management"
                ],
                data_recipients=["University administration", "Career counselors"],
                retention_period=f"{settings.DATA_RETENTION_DAYS} days",
                data_sources=["Student registration", "Course enrollment", "Activity participation"],
                export_available=True,
                generated_at=datetime.now()
            )

    # ==================== Right to Data Portability ====================

    async def export_data(self, student_id: str, request_id: str, format: str = "json") -> DataExportResponse:
        """Export personal data in portable format"""
        # Get access response first
        access_response = await self.process_access_request(student_id, request_id)

        # Calculate file size (rough estimate)
        data_json = json.dumps(access_response.personal_data, default=str)
        file_size = len(data_json.encode('utf-8'))

        return DataExportResponse(
            student_id=student_id,
            request_id=request_id,
            format=format,
            file_size_bytes=file_size,
            download_url=f"/privacy/export/{request_id}/download",
            expires_at=datetime.now() + timedelta(days=7),
            data_categories=access_response.data_categories,
            generated_at=datetime.now()
        )

    # ==================== Right to Erasure ====================

    async def process_erasure_request(self, student_id: str, request_id: str) -> ErasureResponse:
        """Process a data erasure request (Right to be Forgotten)"""
        pool = await get_db_pool()
        erased_categories = []
        retained_categories = []

        async with pool.acquire() as conn:
            await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}")

            # Update request status
            await conn.execute(
                """
                UPDATE tb_data_subject_request
                SET status = $1, upd_dt = CURRENT_TIMESTAMP
                WHERE request_id = $2
                """,
                RequestStatus.IN_PROGRESS.value,
                request_id
            )

            # Delete data from each category (except legally required)
            for category, tables in self.DATA_CATEGORIES.items():
                for table in tables:
                    if table in self.LEGALLY_REQUIRED_DATA:
                        retained_categories.append(category)
                        continue

                    try:
                        await conn.execute(
                            f"DELETE FROM {table} WHERE student_id = $1",
                            student_id
                        )
                        if category not in erased_categories:
                            erased_categories.append(category)
                    except Exception as e:
                        logger.warning(f"Could not delete from {table}: {e}")

            # Anonymize legally required data
            try:
                await conn.execute(
                    """
                    UPDATE tb_student
                    SET student_nm = 'ANONYMIZED',
                        email = 'anonymized@deleted.com',
                        phone = NULL,
                        address = NULL,
                        upd_dt = CURRENT_TIMESTAMP
                    WHERE student_id = $1
                    """,
                    student_id
                )
            except Exception as e:
                logger.warning(f"Could not anonymize student: {e}")

            # Mark request as completed
            await conn.execute(
                """
                UPDATE tb_data_subject_request
                SET status = $1, completed_at = CURRENT_TIMESTAMP, upd_dt = CURRENT_TIMESTAMP
                WHERE request_id = $2
                """,
                RequestStatus.COMPLETED.value,
                request_id
            )

            return ErasureResponse(
                student_id=student_id,
                request_id=request_id,
                status=RequestStatus.COMPLETED,
                erased_categories=list(set(erased_categories)),
                retained_categories=list(set(retained_categories)),
                retention_reason=self.RETENTION_REASON if retained_categories else None,
                completed_at=datetime.now(),
                message="Data erasure completed. Academic records have been anonymized but retained for regulatory compliance."
            )

    # ==================== Consent Management ====================

    async def record_consent(self, data: ConsentCreate) -> ConsentResponse:
        """Record a consent decision"""
        pool = await get_db_pool()
        consent_id = str(uuid.uuid4())

        async with pool.acquire() as conn:
            await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}")
            await self._ensure_privacy_tables(conn)

            row = await conn.fetchrow(
                """
                INSERT INTO tb_consent_record (
                    consent_id, student_id, consent_type, granted, purpose,
                    granted_at, ins_user_id, ins_dt
                )
                VALUES ($1, $2, $3, $4, $5, $6, 'SYSTEM', CURRENT_TIMESTAMP)
                ON CONFLICT (student_id, consent_type) DO UPDATE SET
                    granted = EXCLUDED.granted,
                    purpose = EXCLUDED.purpose,
                    granted_at = CASE WHEN EXCLUDED.granted THEN CURRENT_TIMESTAMP ELSE tb_consent_record.granted_at END,
                    revoked_at = CASE WHEN NOT EXCLUDED.granted THEN CURRENT_TIMESTAMP ELSE NULL END,
                    upd_dt = CURRENT_TIMESTAMP
                RETURNING consent_id, student_id, consent_type, granted, purpose,
                          granted_at, revoked_at
                """,
                consent_id,
                data.student_id,
                data.consent_type.value,
                data.granted,
                data.purpose,
                datetime.now() if data.granted else None
            )

            logger.info(f"Recorded consent {data.consent_type.value} for student {data.student_id}: {data.granted}")

            return ConsentResponse(
                consent_id=row['consent_id'],
                student_id=row['student_id'],
                consent_type=ConsentType(row['consent_type']),
                granted=row['granted'],
                purpose=row['purpose'],
                granted_at=row['granted_at'],
                revoked_at=row['revoked_at']
            )

    async def get_consents(self, student_id: str) -> ConsentListResponse:
        """Get all consent records for a student"""
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}")
            await self._ensure_privacy_tables(conn)

            rows = await conn.fetch(
                """
                SELECT consent_id, student_id, consent_type, granted, purpose,
                       granted_at, revoked_at
                FROM tb_consent_record
                WHERE student_id = $1
                ORDER BY ins_dt DESC
                """,
                student_id
            )

            consents = [
                ConsentResponse(
                    consent_id=row['consent_id'],
                    student_id=row['student_id'],
                    consent_type=ConsentType(row['consent_type']),
                    granted=row['granted'],
                    purpose=row['purpose'],
                    granted_at=row['granted_at'],
                    revoked_at=row['revoked_at']
                )
                for row in rows
            ]

            all_granted = all(c.granted for c in consents) if consents else False

            return ConsentListResponse(
                student_id=student_id,
                consents=consents,
                all_consents_granted=all_granted
            )

    async def revoke_consent(self, student_id: str, consent_type: ConsentType) -> Optional[ConsentResponse]:
        """Revoke a specific consent"""
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}")

            row = await conn.fetchrow(
                """
                UPDATE tb_consent_record
                SET granted = FALSE, revoked_at = CURRENT_TIMESTAMP, upd_dt = CURRENT_TIMESTAMP
                WHERE student_id = $1 AND consent_type = $2
                RETURNING consent_id, student_id, consent_type, granted, purpose,
                          granted_at, revoked_at
                """,
                student_id,
                consent_type.value
            )

            if not row:
                return None

            logger.info(f"Revoked consent {consent_type.value} for student {student_id}")

            return ConsentResponse(
                consent_id=row['consent_id'],
                student_id=row['student_id'],
                consent_type=ConsentType(row['consent_type']),
                granted=row['granted'],
                purpose=row['purpose'],
                granted_at=row['granted_at'],
                revoked_at=row['revoked_at']
            )

    # ==================== Helper Methods ====================

    async def _ensure_privacy_tables(self, conn):
        """Ensure privacy tables exist"""
        # Data Subject Request table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tb_data_subject_request (
                request_id VARCHAR(50) PRIMARY KEY,
                student_id VARCHAR(20) NOT NULL,
                request_type VARCHAR(50) NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                description TEXT,
                contact_email VARCHAR(200),
                response_data JSONB,
                rejection_reason TEXT,
                completed_at TIMESTAMP,
                ins_user_id VARCHAR(50),
                ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                upd_dt TIMESTAMP
            )
        """)

        # Consent Record table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tb_consent_record (
                consent_id VARCHAR(50) PRIMARY KEY,
                student_id VARCHAR(20) NOT NULL,
                consent_type VARCHAR(50) NOT NULL,
                granted BOOLEAN NOT NULL DEFAULT FALSE,
                purpose TEXT,
                granted_at TIMESTAMP,
                revoked_at TIMESTAMP,
                ip_address VARCHAR(50),
                user_agent TEXT,
                ins_user_id VARCHAR(50),
                ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                upd_dt TIMESTAMP,
                UNIQUE(student_id, consent_type)
            )
        """)

    def _serialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize data for JSON response"""
        result = {}
        for key, value in data.items():
            if isinstance(value, list):
                result[key] = [self._serialize_record(r) for r in value]
            elif isinstance(value, dict):
                result[key] = self._serialize_record(value)
            else:
                result[key] = value
        return result

    def _serialize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize a single record"""
        result = {}
        for key, value in record.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, uuid.UUID):
                result[key] = str(value)
            else:
                result[key] = value
        return result
