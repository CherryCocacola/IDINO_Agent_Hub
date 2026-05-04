from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from uuid import UUID
from enum import Enum


class BadgeCategory(str, Enum):
    SKILL = "skill"             # 스킬 마스터리
    ACHIEVEMENT = "achievement" # 성취
    COURSE = "course"           # 강의 수료
    PROJECT = "project"         # 프로젝트 완료
    CERTIFICATION = "certification"  # 자격증
    COMPETITION = "competition" # 공모전
    COMMUNITY = "community"     # 커뮤니티 기여
    COMPETENCY = "competency"   # 역량
    MILESTONE = "milestone"     # 마일스톤


class BadgeLevel(str, Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class BadgeBase(BaseModel):
    badge_cd: str
    badge_nm: str
    description: Optional[str] = None
    category: BadgeCategory
    level: BadgeLevel = BadgeLevel.BRONZE
    icon_url: Optional[str] = None
    criteria: Optional[Dict[str, Any]] = None
    points: int = 10
    related_skill_cd: Optional[str] = None
    is_active: bool = True


class BadgeCreate(BadgeBase):
    pass


class BadgeResponse(BadgeBase):
    badge_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class StudentBadgeResponse(BaseModel):
    student_badge_id: UUID
    student_id: str
    badge_id: UUID
    badge: BadgeResponse
    earned_at: datetime
    issued_by: Optional[str] = None
    evidence_url: Optional[str] = None
    verification_hash: Optional[str] = None
    is_public: bool = True

    class Config:
        from_attributes = True


class BadgeAwardRequest(BaseModel):
    student_id: str
    badge_cd: str
    issued_by: Optional[str] = None
    evidence_url: Optional[str] = None
    is_public: bool = True


class SkillCredential(BaseModel):
    skill_cd: str
    skill_nm: str
    level: int
    verified: bool = False
    verification_source: Optional[str] = None
    verified_at: Optional[datetime] = None
    related_badges: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)


class SkillPassportResponse(BaseModel):
    passport_id: UUID
    student_id: str
    student_name: Optional[str] = None
    issued_at: datetime
    updated_at: datetime

    # Summary
    total_skills: int = 0
    verified_skills: int = 0
    total_badges: int = 0
    total_points: int = 0

    # Credentials
    skills: List[SkillCredential] = Field(default_factory=list)
    badges: List[StudentBadgeResponse] = Field(default_factory=list)

    # Verification
    passport_hash: Optional[str] = None
    is_valid: bool = True
    share_url: Optional[str] = None

    class Config:
        from_attributes = True


class PassportShareRequest(BaseModel):
    student_id: str
    include_skills: bool = True
    include_badges: bool = True
    expiry_days: int = Field(default=30, ge=1, le=365)
    recipient_email: Optional[str] = None


class PassportShareResponse(BaseModel):
    share_id: UUID
    share_url: str
    expires_at: datetime
    access_count: int = 0
    created_at: datetime


class CredentialType(str, Enum):
    CERTIFICATION = "certification"  # 자격증
    CERTIFICATE = "certificate"      # 자격증 (alternate)
    LICENSE = "license"              # 면허
    AWARD = "award"                  # 수상
    COMPLETION = "completion"        # 수료
    PUBLICATION = "publication"      # 논문/출판물
    SCHOLARSHIP = "scholarship"      # 장학금
    PATENT = "patent"                # 특허
    LANGUAGE = "language"            # 어학


class CredentialResponse(BaseModel):
    credential_id: UUID
    student_id: str
    credential_type: CredentialType
    credential_nm: str
    issuing_org: str
    issue_date: date
    expiry_date: Optional[date] = None
    credential_number: Optional[str] = None
    verification_url: Optional[str] = None
    verified: bool = False
    related_skill_cd: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
