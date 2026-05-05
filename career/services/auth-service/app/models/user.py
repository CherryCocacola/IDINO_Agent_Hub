"""
User and authentication related database models.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from ..database import Base


class User(Base):
    """User account table."""

    __tablename__ = "tb_user"

    user_id = Column(PGUUID(as_uuid=True), primary_key=True)
    login_id = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    user_nm = Column(String(50), nullable=False)  # 사용자 이름
    user_type = Column(String(20), nullable=False)

    # Foreign keys
    student_id = Column(String(20), ForeignKey("tb_student.student_id"))
    professor_cd = Column(String(20), ForeignKey("tb_professor.professor_cd"))

    # Account status
    status = Column(String(20), default="active")
    email = Column(String(100))
    phone = Column(String(20))

    # 2FA settings
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(64))  # Maps to mfa_secret in DB (from 00_full_ddl.sql)

    # Security
    login_fail_count = Column(Integer, default=0)
    locked_until = Column(DateTime)
    last_login = Column(DateTime)

    # Audit
    ins_user_id = Column(String(50))
    ins_dt = Column(DateTime, default=datetime.utcnow)
    upd_user_id = Column(String(50))
    upd_dt = Column(DateTime)

    # Relationships
    sessions = relationship("AuthSession", back_populates="user", cascade="all, delete-orphan")
    login_history = relationship("LoginHistory", back_populates="user", cascade="all, delete-orphan")


class AuthSession(Base):
    """Session management table."""

    __tablename__ = "tb_auth_session"

    session_id = Column(PGUUID(as_uuid=True), primary_key=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("tb_user.user_id", ondelete="CASCADE"), nullable=False)

    # Token info
    access_token_hash = Column(String(64))
    refresh_token_hash = Column(String(64), unique=True)

    # Device info
    device_id = Column(String(100))
    device_type = Column(String(50))
    device_name = Column(String(100))
    user_agent = Column(Text)
    ip_address = Column(String(50))

    # Status
    is_active = Column(Boolean, default=True)
    mfa_verified = Column(Boolean, default=False)

    # Timestamps
    issued_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    last_activity_at = Column(DateTime)
    revoked_at = Column(DateTime)
    revoked_reason = Column(String(100))

    # Audit
    ins_user_id = Column(String(50))
    ins_dt = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="sessions")


class LoginHistory(Base):
    """Login attempt history table."""

    __tablename__ = "tb_login_history"

    history_id = Column(PGUUID(as_uuid=True), primary_key=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("tb_user.user_id", ondelete="SET NULL"))
    login_id = Column(String(50), nullable=False)

    # Result
    login_result = Column(String(20), nullable=False)
    # NOTE: failure_reason column removed - not in actual DB schema

    # Device info
    ip_address = Column(String(50))
    user_agent = Column(Text)
    device_type = Column(String(50))
    device_fingerprint = Column(String(100))

    # Security
    is_suspicious = Column(Boolean, default=False)
    risk_score = Column(Integer, default=0)

    # Geo
    geo_country = Column(String(50))
    geo_city = Column(String(100))

    # Timestamp
    attempted_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="login_history")
