"""Initial schema -- create all tables for the Document Utilization System.

Revision ID: 001_initial
Revises: None
Create Date: 2025-01-01 00:00:00.000000

This migration creates the complete initial database schema including:

- tb_organizations, tb_departments
- tb_users
- tb_projects, tb_boards, tb_folders
- tb_documents, tb_document_chunks
- tb_search_scopes
- tb_chat_sessions, tb_chat_messages
- tb_report_templates, tb_generated_reports
- tb_llm_api_keys
- tb_audit_logs
- tb_faq_entries
- tb_search_history

All tables include audit columns: ins_dt, ins_user, ins_ip, upd_dt, upd_user, upd_ip

It also seeds a default organisation and super_admin user.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _audit_columns() -> list:
    """Return the standard audit columns for all tables."""
    return [
        sa.Column("ins_dt", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("ins_user", PG_UUID(as_uuid=True), nullable=True),
        sa.Column("ins_ip", sa.String(45), nullable=True),
        sa.Column("upd_dt", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("upd_user", PG_UUID(as_uuid=True), nullable=True),
        sa.Column("upd_ip", sa.String(45), nullable=True),
    ]


def upgrade() -> None:
    # ------------------------------------------------------------------
    # tb_organizations
    # ------------------------------------------------------------------
    op.create_table(
        "tb_organizations",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("settings", JSONB, nullable=True),
        *_audit_columns(),
    )

    # ------------------------------------------------------------------
    # tb_departments
    # ------------------------------------------------------------------
    op.create_table(
        "tb_departments",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "organization_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "parent_id", PG_UUID(as_uuid=True), sa.ForeignKey("tb_departments.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("depth", sa.Integer, nullable=False, server_default="0"),
        sa.Column("path", sa.String(1024), nullable=True),
        *_audit_columns(),
    )
    op.create_index("idx_tb_departments_organization_id", "tb_departments", ["organization_id"])
    op.create_index("idx_tb_departments_parent_id", "tb_departments", ["parent_id"])

    # ------------------------------------------------------------------
    # tb_users
    # ------------------------------------------------------------------
    op.create_table(
        "tb_users",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "organization_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "department_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("username", sa.String(150), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.String(512), nullable=False),
        sa.Column("role", sa.String(32), nullable=False, server_default="member"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("failed_login_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("language", sa.String(10), nullable=False, server_default="ko"),
        sa.Column("password_reset_token", sa.String(128), nullable=True),
        sa.Column("password_reset_expires_at", sa.DateTime(timezone=True), nullable=True),
        *_audit_columns(),
    )
    op.create_unique_constraint("uq_tb_users_org_username", "tb_users", ["organization_id", "username"])
    op.create_unique_constraint("uq_tb_users_org_email", "tb_users", ["organization_id", "email"])
    op.create_index("idx_tb_users_organization_id", "tb_users", ["organization_id"])
    op.create_index("idx_tb_users_department_id", "tb_users", ["department_id"])
    op.create_index("idx_tb_users_status", "tb_users", ["status"])

    # ------------------------------------------------------------------
    # tb_projects
    # ------------------------------------------------------------------
    op.create_table(
        "tb_projects",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "organization_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("allow_original_download", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_by", PG_UUID(as_uuid=True), sa.ForeignKey("tb_users.id", ondelete="SET NULL"), nullable=False
        ),
        *_audit_columns(),
    )
    op.create_index("idx_tb_projects_organization_id", "tb_projects", ["organization_id"])

    # ------------------------------------------------------------------
    # tb_boards
    # ------------------------------------------------------------------
    op.create_table(
        "tb_boards",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "project_id", PG_UUID(as_uuid=True), sa.ForeignKey("tb_projects.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "created_by", PG_UUID(as_uuid=True), sa.ForeignKey("tb_users.id", ondelete="SET NULL"), nullable=False
        ),
        *_audit_columns(),
    )
    op.create_index("idx_tb_boards_project_id", "tb_boards", ["project_id"])

    # ------------------------------------------------------------------
    # tb_folders
    # ------------------------------------------------------------------
    op.create_table(
        "tb_folders",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("board_id", PG_UUID(as_uuid=True), sa.ForeignKey("tb_boards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "created_by", PG_UUID(as_uuid=True), sa.ForeignKey("tb_users.id", ondelete="SET NULL"), nullable=False
        ),
        *_audit_columns(),
    )
    op.create_index("idx_tb_folders_board_id", "tb_folders", ["board_id"])

    # ------------------------------------------------------------------
    # tb_documents
    # ------------------------------------------------------------------
    op.create_table(
        "tb_documents",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "folder_id", PG_UUID(as_uuid=True), sa.ForeignKey("tb_folders.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "organization_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(512), nullable=False),
        sa.Column("original_filename", sa.String(512), nullable=False),
        sa.Column("format", sa.String(20), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger, nullable=False),
        sa.Column("storage_path", sa.String(1024), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="waiting"),
        sa.Column("processing_error", sa.Text, nullable=True),
        sa.Column("page_count", sa.Integer, nullable=True),
        sa.Column("chunk_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("metadata", JSONB, nullable=True),
        sa.Column("tags", ARRAY(sa.String), nullable=True),
        sa.Column("language", sa.String(10), nullable=False, server_default="ko"),
        sa.Column("checksum_sha256", sa.String(64), nullable=False),
        sa.Column(
            "uploaded_by", PG_UUID(as_uuid=True), sa.ForeignKey("tb_users.id", ondelete="SET NULL"), nullable=False
        ),
        sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processing_completed_at", sa.DateTime(timezone=True), nullable=True),
        *_audit_columns(),
    )
    op.create_index("idx_tb_documents_folder_id", "tb_documents", ["folder_id"])
    op.create_index("idx_tb_documents_organization_id", "tb_documents", ["organization_id"])
    op.create_index("idx_tb_documents_status", "tb_documents", ["status"])
    op.create_index("idx_tb_documents_uploaded_by", "tb_documents", ["uploaded_by"])

    # ------------------------------------------------------------------
    # tb_document_chunks
    # ------------------------------------------------------------------
    op.create_table(
        "tb_document_chunks",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "document_id", PG_UUID(as_uuid=True), sa.ForeignKey("tb_documents.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("chunk_type", sa.String(50), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("content_length", sa.Integer, nullable=False),
        sa.Column("page_number", sa.Integer, nullable=True),
        sa.Column("section_title", sa.String(512), nullable=True),
        sa.Column("metadata", JSONB, nullable=True),
        sa.Column("qdrant_point_id", PG_UUID(as_uuid=True), nullable=True),
        *_audit_columns(),
    )
    op.create_unique_constraint("uq_tb_document_chunks_doc_idx", "tb_document_chunks", ["document_id", "chunk_index"])
    op.create_index("idx_tb_document_chunks_document_id", "tb_document_chunks", ["document_id"])

    # ------------------------------------------------------------------
    # tb_search_scopes
    # ------------------------------------------------------------------
    op.create_table(
        "tb_search_scopes",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "organization_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "project_id", PG_UUID(as_uuid=True), sa.ForeignKey("tb_projects.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("board_id", PG_UUID(as_uuid=True), sa.ForeignKey("tb_boards.id", ondelete="SET NULL"), nullable=True),
        sa.Column(
            "folder_id", PG_UUID(as_uuid=True), sa.ForeignKey("tb_folders.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("location_path", sa.String(1024), nullable=True),
        # Feature toggles
        sa.Column("chatbot_enabled", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("chatbot_faq_template", sa.Text, nullable=True),
        sa.Column("qa_enabled", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("qa_prompt_template", sa.Text, nullable=True),
        sa.Column("qa_llm_model", sa.String(255), nullable=True),
        sa.Column("keyword_search_enabled", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("agent_enabled", sa.Boolean, nullable=False, server_default=sa.text("false")),
        # Chunking / retrieval tuning
        sa.Column("chunk_size", sa.Integer, nullable=False, server_default="512"),
        sa.Column("chunk_overlap", sa.Integer, nullable=False, server_default="64"),
        sa.Column("title_weight", sa.Float, nullable=False, server_default="0.3"),
        sa.Column("keyword_weight", sa.Float, nullable=False, server_default="0.3"),
        sa.Column("content_weight", sa.Float, nullable=False, server_default="0.4"),
        sa.Column("max_results", sa.Integer, nullable=False, server_default="10"),
        sa.Column("similarity_threshold", sa.Float, nullable=False, server_default="0.5"),
        # Ownership
        sa.Column(
            "created_by", PG_UUID(as_uuid=True), sa.ForeignKey("tb_users.id", ondelete="SET NULL"), nullable=False
        ),
        *_audit_columns(),
    )
    op.create_index("idx_tb_search_scopes_organization_id", "tb_search_scopes", ["organization_id"])

    # ------------------------------------------------------------------
    # tb_chat_sessions
    # ------------------------------------------------------------------
    op.create_table(
        "tb_chat_sessions",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", PG_UUID(as_uuid=True), sa.ForeignKey("tb_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "organization_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "search_scope_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_search_scopes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("scoped_document_ids", ARRAY(PG_UUID(as_uuid=True)), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        *_audit_columns(),
    )
    op.create_index("idx_tb_chat_sessions_user_id", "tb_chat_sessions", ["user_id"])
    op.create_index("idx_tb_chat_sessions_organization_id", "tb_chat_sessions", ["organization_id"])

    # ------------------------------------------------------------------
    # tb_chat_messages
    # ------------------------------------------------------------------
    op.create_table(
        "tb_chat_messages",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "session_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_chat_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("citations", JSONB, nullable=True),
        sa.Column("retrieved_chunks", JSONB, nullable=True),
        sa.Column("model_used", sa.String(255), nullable=True),
        sa.Column("token_count_input", sa.Integer, nullable=True),
        sa.Column("token_count_output", sa.Integer, nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column("hallucination_score", sa.Float, nullable=True),
        *_audit_columns(),
    )
    op.create_index("idx_tb_chat_messages_session_id", "tb_chat_messages", ["session_id"])

    # ------------------------------------------------------------------
    # tb_report_templates
    # ------------------------------------------------------------------
    op.create_table(
        "tb_report_templates",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "organization_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("format", sa.String(20), nullable=False),
        sa.Column("template_storage_path", sa.String(1024), nullable=False),
        sa.Column("schema", JSONB, nullable=True),
        sa.Column(
            "created_by", PG_UUID(as_uuid=True), sa.ForeignKey("tb_users.id", ondelete="SET NULL"), nullable=False
        ),
        *_audit_columns(),
    )
    op.create_index("idx_tb_report_templates_organization_id", "tb_report_templates", ["organization_id"])

    # ------------------------------------------------------------------
    # tb_generated_reports
    # ------------------------------------------------------------------
    op.create_table(
        "tb_generated_reports",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "template_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_report_templates.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "organization_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("output_format", sa.String(20), nullable=False),
        sa.Column("output_storage_path", sa.String(1024), nullable=True),
        sa.Column("source_document_ids", ARRAY(PG_UUID(as_uuid=True)), nullable=True),
        sa.Column(
            "source_chat_session_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_chat_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("generation_params", JSONB, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column(
            "generated_by", PG_UUID(as_uuid=True), sa.ForeignKey("tb_users.id", ondelete="SET NULL"), nullable=False
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *_audit_columns(),
    )
    op.create_index("idx_tb_generated_reports_organization_id", "tb_generated_reports", ["organization_id"])
    op.create_index("idx_tb_generated_reports_generated_by", "tb_generated_reports", ["generated_by"])
    op.create_index("idx_tb_generated_reports_status", "tb_generated_reports", ["status"])

    # ------------------------------------------------------------------
    # tb_llm_api_keys
    # ------------------------------------------------------------------
    op.create_table(
        "tb_llm_api_keys",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "organization_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("llm_name", sa.String(255), nullable=False),
        sa.Column("api_key_encrypted", sa.LargeBinary, nullable=False),
        sa.Column("api_key_prefix", sa.String(20), nullable=False),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("registered_by", sa.String(255), nullable=False),
        *_audit_columns(),
    )
    op.create_index("idx_tb_llm_api_keys_organization_id", "tb_llm_api_keys", ["organization_id"])

    # ------------------------------------------------------------------
    # tb_audit_logs
    # ------------------------------------------------------------------
    op.create_table(
        "tb_audit_logs",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", PG_UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", PG_UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", PG_UUID(as_uuid=True), nullable=True),
        sa.Column("details", JSONB, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        *_audit_columns(),
    )
    op.create_index("idx_tb_audit_logs_action", "tb_audit_logs", ["action"])
    op.create_index("idx_tb_audit_logs_resource_type", "tb_audit_logs", ["resource_type"])
    op.create_index("idx_tb_audit_logs_user_id", "tb_audit_logs", ["user_id"])
    op.create_index("idx_tb_audit_logs_organization_id", "tb_audit_logs", ["organization_id"])
    op.create_index("idx_tb_audit_logs_ins_dt", "tb_audit_logs", ["ins_dt"])

    # ------------------------------------------------------------------
    # tb_faq_entries
    # ------------------------------------------------------------------
    op.create_table(
        "tb_faq_entries",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "search_scope_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_search_scopes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "organization_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("answer", sa.Text, nullable=False),
        sa.Column("category", sa.String(255), nullable=True),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        *_audit_columns(),
    )
    op.create_index("idx_tb_faq_entries_organization_id", "tb_faq_entries", ["organization_id"])
    op.create_index("idx_tb_faq_entries_search_scope_id", "tb_faq_entries", ["search_scope_id"])
    op.create_index("idx_tb_faq_entries_category", "tb_faq_entries", ["category"])

    # ------------------------------------------------------------------
    # tb_search_history
    # ------------------------------------------------------------------
    op.create_table(
        "tb_search_history",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", PG_UUID(as_uuid=True), sa.ForeignKey("tb_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column(
            "organization_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("query", sa.Text, nullable=False),
        sa.Column("search_type", sa.String(50), nullable=False),
        sa.Column("result_count", sa.Integer, nullable=False, server_default="0"),
        *_audit_columns(),
    )
    op.create_index("idx_tb_search_history_user_id", "tb_search_history", ["user_id"])
    op.create_index("idx_tb_search_history_organization_id", "tb_search_history", ["organization_id"])

    # ------------------------------------------------------------------
    # Seed data: default organisation + super_admin user
    # ------------------------------------------------------------------
    # Password hash for "admin123!" generated with bcrypt (cost=12).
    _ADMIN_PASSWORD_HASH = "$2b$12$LJ3m4ys3Lk0TSwHOFqMCduYVoPGBMXwEXsCiKZOXCrWbFQ9kWbsuq"

    _DEFAULT_ORG_ID = "00000000-0000-4000-a000-000000000001"
    _ADMIN_USER_ID = "00000000-0000-4000-a000-000000000002"

    op.execute(
        sa.text(
            """
            INSERT INTO tb_organizations (id, name, slug, description)
            VALUES (CAST(:org_id AS UUID), :name, :slug, :description)
            ON CONFLICT DO NOTHING
            """
        ).bindparams(
            org_id=_DEFAULT_ORG_ID,
            name="Default Organization",
            slug="default",
            description="System default organisation created during initial migration.",
        )
    )

    op.execute(
        sa.text(
            """
            INSERT INTO tb_users (id, username, email, password_hash, role, status, organization_id)
            VALUES (CAST(:user_id AS UUID), :username, :email, :password_hash, :role, :status, CAST(:org_id AS UUID))
            ON CONFLICT DO NOTHING
            """
        ).bindparams(
            user_id=_ADMIN_USER_ID,
            username="admin",
            email="admin@docutil.local",
            password_hash=_ADMIN_PASSWORD_HASH,
            role="super_admin",
            status="active",
            org_id=_DEFAULT_ORG_ID,
        )
    )


def downgrade() -> None:
    """Drop all tables in reverse dependency order."""
    op.drop_table("tb_search_history")
    op.drop_table("tb_faq_entries")
    op.drop_table("tb_audit_logs")
    op.drop_table("tb_llm_api_keys")
    op.drop_table("tb_generated_reports")
    op.drop_table("tb_report_templates")
    op.drop_table("tb_chat_messages")
    op.drop_table("tb_chat_sessions")
    op.drop_table("tb_search_scopes")
    op.drop_table("tb_document_chunks")
    op.drop_table("tb_documents")
    op.drop_table("tb_folders")
    op.drop_table("tb_boards")
    op.drop_table("tb_projects")
    op.drop_table("tb_users")
    op.drop_table("tb_departments")
    op.drop_table("tb_organizations")
