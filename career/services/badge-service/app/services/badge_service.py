from typing import Optional, List, Dict
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import hashlib
import json

from ..database import execute_query, execute_one, execute_scalar, execute_command
from ..schemas import (
    BadgeCategory,
    BadgeLevel,
    BadgeCreate,
    BadgeResponse,
    StudentBadgeResponse,
    SkillPassportResponse,
    SkillCredential,
    PassportShareResponse,
)


class BadgeService:
    # ============================================
    # Badge CRUD
    # ============================================

    async def get_all_badges(
        self, category: Optional[BadgeCategory] = None, is_active: bool = True
    ) -> List[Dict]:
        conditions = ["use_fg = $1"]
        params = ['Y' if is_active else 'N']
        if category:
            conditions.append("category = $2")
            params.append(category.value)

        query = f"""
            SELECT badge_id, badge_cd, badge_nm, description, category,
                   level, icon_url, criteria, points,
                   criteria->>'skill_cd' as related_skill_cd, use_fg = 'Y' as is_active, ins_dt as created_at
            FROM tb_badge WHERE {" AND ".join(conditions)}
            ORDER BY points DESC
        """
        return await execute_query(query, *params)

    async def get_badge(self, badge_cd: str) -> Optional[Dict]:
        query = """
            SELECT badge_id, badge_cd, badge_nm, description, category,
                   level, icon_url, criteria, points,
                   criteria->>'skill_cd' as related_skill_cd, use_fg = 'Y' as is_active, ins_dt as created_at
            FROM tb_badge WHERE badge_cd = $1
        """
        return await execute_one(query, badge_cd)

    async def create_badge(self, data: BadgeCreate) -> Dict:
        query = """
            INSERT INTO tb_badge (
                badge_cd, badge_nm, description, category, level,
                icon_url, criteria, points, use_fg
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING badge_id, badge_cd, badge_nm, description, category, level,
                      icon_url, criteria, points, use_fg = 'Y' as is_active, ins_dt as created_at
        """
        return await execute_one(
            query, data.badge_cd, data.badge_nm, data.description,
            data.category.value, data.level.value, data.icon_url,
            data.criteria, data.points, 'Y' if data.is_active else 'N'
        )

    # ============================================
    # Student Badges
    # ============================================

    async def award_badge(
        self, student_id: str, badge_cd: str, issued_by: Optional[str] = None,
        evidence_url: Optional[str] = None, is_public: bool = True
    ) -> Optional[Dict]:
        badge = await self.get_badge(badge_cd)
        if not badge:
            return None

        # Generate verification hash and store in evidence JSONB
        verification_data = f"{student_id}:{badge_cd}:{datetime.now().isoformat()}"
        verification_hash = hashlib.sha256(verification_data.encode()).hexdigest()[:32]
        evidence = {"url": evidence_url, "verification_hash": verification_hash, "is_public": is_public}

        query = """
            INSERT INTO tb_student_badge (
                student_id, badge_id, verified_by, evidence
            ) VALUES ($1, $2, $3, $4)
            ON CONFLICT (student_id, badge_id, earned_level) DO NOTHING
            RETURNING student_badge_id, student_id, badge_id, earned_at,
                      verified_by as issued_by, evidence->>'url' as evidence_url,
                      evidence->>'verification_hash' as verification_hash,
                      COALESCE((evidence->>'is_public')::boolean, true) as is_public
        """
        result = await execute_one(
            query, student_id, badge["badge_id"], issued_by, json.dumps(evidence)
        )

        if result:
            result["badge"] = BadgeResponse(**badge)

        return result

    async def get_student_badges(self, student_id: str, is_public: Optional[bool] = None) -> List[Dict]:
        conditions = ["sb.student_id = $1"]
        params = [student_id]
        if is_public is not None:
            conditions.append("COALESCE((sb.evidence->>'is_public')::boolean, true) = $2")
            params.append(is_public)

        query = f"""
            SELECT sb.student_badge_id, sb.student_id, sb.badge_id,
                   sb.earned_at, sb.verified_by as issued_by,
                   sb.evidence->>'url' as evidence_url,
                   sb.evidence->>'verification_hash' as verification_hash,
                   COALESCE((sb.evidence->>'is_public')::boolean, true) as is_public,
                   b.badge_cd, b.badge_nm, b.description, b.category, b.level,
                   b.icon_url, b.criteria, b.points, b.criteria->>'skill_cd' as related_skill_cd, b.use_fg = 'Y' as is_active, b.ins_dt as created_at
            FROM tb_student_badge sb
            JOIN tb_badge b ON sb.badge_id = b.badge_id
            WHERE {" AND ".join(conditions)}
            ORDER BY sb.earned_at DESC
        """
        rows = await execute_query(query, *params)

        for row in rows:
            row["badge"] = BadgeResponse(
                badge_id=row["badge_id"], badge_cd=row["badge_cd"], badge_nm=row["badge_nm"],
                description=row["description"], category=row["category"], level=row["level"],
                icon_url=row["icon_url"], criteria=row["criteria"], points=row["points"],
                related_skill_cd=row["related_skill_cd"], is_active=row["is_active"],
                created_at=row["created_at"]
            )
        return rows

    async def get_student_badge_stats(self, student_id: str) -> Dict:
        query = """
            SELECT
                COUNT(*) as total_badges,
                COALESCE(SUM(b.points), 0) as total_points,
                COUNT(*) FILTER (WHERE b.level = 'platinum') as platinum,
                COUNT(*) FILTER (WHERE b.level = 'gold') as gold,
                COUNT(*) FILTER (WHERE b.level = 'silver') as silver,
                COUNT(*) FILTER (WHERE b.level = 'bronze') as bronze
            FROM tb_student_badge sb
            JOIN tb_badge b ON sb.badge_id = b.badge_id
            WHERE sb.student_id = $1
        """
        return await execute_one(query, student_id)

    # ============================================
    # Student Credentials
    # ============================================

    async def get_student_credentials(self, student_id: str) -> List[Dict]:
        """학생의 자격증, 면허, 수상 목록 조회 - tb_achievement 테이블 사용"""
        query = """
            SELECT
                a.achievement_id as credential_id, a.student_id,
                a.achievement_type as credential_type,
                a.title as credential_nm, a.issuer as issuing_org,
                a.issue_date, a.expire_date as expiry_date,
                NULL as credential_number, NULL as verification_url,
                a.verified = 'Y' as verified,
                a.competency_contributions->>'primary_skill_cd' as related_skill_cd, a.ins_dt as created_at
            FROM tb_achievement a
            WHERE a.student_id = $1
            ORDER BY a.issue_date DESC
        """
        result = await execute_query(query, student_id)
        return result if result else []

    # ============================================
    # Skill Passport
    # ============================================

    async def get_skill_passport(self, student_id: str) -> Optional[SkillPassportResponse]:
        # Get student info
        student = await execute_one(
            "SELECT student_id, student_nm as std_nm FROM tb_student WHERE student_id = $1", student_id
        )
        if not student:
            return None

        # Get or create passport
        passport = await execute_one(
            "SELECT * FROM tb_skill_passport WHERE student_id = $1", student_id
        )
        if not passport:
            passport = await execute_one("""
                INSERT INTO tb_skill_passport (student_id, is_public) VALUES ($1, false)
                RETURNING passport_id, student_id, ins_dt as issued_at, last_updated as updated_at, is_public
            """, student_id)

        # Get skills
        skills_query = """
            SELECT ss.skill_cd, s.skill_nm, ss.current_level as level,
                   ss.verification_source, ss.last_verified_date as verified_at,
                   CASE WHEN ss.verification_source IS NOT NULL THEN true ELSE false END as verified
            FROM tb_student_skill ss
            JOIN tb_skill s ON ss.skill_cd = s.skill_cd
            WHERE ss.student_id = $1
            ORDER BY ss.current_level DESC
        """
        skills_data = await execute_query(skills_query, student_id)

        # Get badges
        badges_data = await self.get_student_badges(student_id, is_public=True)
        stats = await self.get_student_badge_stats(student_id)

        # Build skill credentials
        skills = []
        for s in skills_data:
            related_badges = [
                b["badge"]["badge_nm"] for b in badges_data
                if b["badge"].related_skill_cd == s["skill_cd"]
            ]
            skills.append(SkillCredential(
                skill_cd=s["skill_cd"], skill_nm=s["skill_nm"], level=s["level"],
                verified=s["verified"], verification_source=s.get("verification_source"),
                verified_at=s.get("verified_at"), related_badges=related_badges
            ))

        # Generate passport hash
        passport_data = {
            "student_id": student_id,
            "skills": [s.model_dump() for s in skills],
            "badges": [str(b["badge_id"]) for b in badges_data],
            "generated_at": datetime.now().isoformat()
        }
        passport_hash = hashlib.sha256(json.dumps(passport_data, default=str).encode()).hexdigest()[:32]

        # Update passport
        await execute_command("""
            UPDATE tb_skill_passport
            SET last_updated = NOW()
            WHERE student_id = $1
        """, student_id)

        return SkillPassportResponse(
            passport_id=passport["passport_id"],
            student_id=student_id,
            student_name=student.get("std_nm"),
            issued_at=passport.get("issued_at") or passport.get("ins_dt"),
            updated_at=datetime.now(),
            total_skills=len(skills),
            verified_skills=len([s for s in skills if s.verified]),
            total_badges=stats["total_badges"],
            total_points=stats["total_points"],
            skills=skills,
            badges=[StudentBadgeResponse(**b) for b in badges_data],
            passport_hash=passport_hash,
            is_valid=True
        )

    async def create_share_link(
        self, student_id: str, expiry_days: int = 30, include_skills: bool = True,
        include_badges: bool = True, recipient_email: Optional[str] = None
    ) -> PassportShareResponse:
        share_id = uuid4()
        expires_at = datetime.now() + timedelta(days=expiry_days)
        share_url = f"/passport/shared/{share_id}"

        # Store share info (would need a share table in production)
        # For now, return mock response
        return PassportShareResponse(
            share_id=share_id,
            share_url=share_url,
            expires_at=expires_at,
            access_count=0,
            created_at=datetime.now()
        )

    async def verify_badge(self, verification_hash: str) -> Optional[Dict]:
        query = """
            SELECT sb.*, b.badge_cd, b.badge_nm, s.student_nm as std_nm
            FROM tb_student_badge sb
            JOIN tb_badge b ON sb.badge_id = b.badge_id
            JOIN tb_student s ON sb.student_id = s.student_id
            WHERE sb.evidence->>'verification_hash' = $1
        """
        return await execute_one(query, verification_hash)


badge_service = BadgeService()
