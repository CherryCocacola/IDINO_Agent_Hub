"""Department-Project restructure: visibility, M2M tables, access control.

Revision ID: 002_dept_proj_restructure
Revises: 001_initial
Create Date: 2026-03-19 00:00:00.000000

This migration adds:

- head_user_id to tb_departments (부서장)
- tb_project_departments M2M table (프로젝트-부서 연결)
- tb_project_members table (프로젝트 구성원)
- visibility, department_id, project_id to tb_documents
- Makes tb_documents.folder_id nullable
- tb_document_access table (비밀 문서 접근 권한)
- Appropriate indexes for new columns and tables
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_dept_proj_restructure"
down_revision: str | None = "001_initial"
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
    # 1. Add head_user_id to tb_departments
    # ------------------------------------------------------------------
    op.add_column(
        "tb_departments",
        sa.Column(
            "head_user_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_users.id", ondelete="SET NULL"),
            nullable=True,
            comment="부서장 사용자 ID",
        ),
    )
    op.create_index(
        "idx_tb_departments_head_user_id",
        "tb_departments",
        ["head_user_id"],
    )

    # ------------------------------------------------------------------
    # 2. Create tb_project_departments (M2M: project <-> department)
    # ------------------------------------------------------------------
    op.create_table(
        "tb_project_departments",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "project_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "department_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_departments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        *_audit_columns(),
        sa.UniqueConstraint("project_id", "department_id", name="uq_tb_project_departments_proj_dept"),
    )
    op.create_index(
        "idx_tb_project_departments_project_id",
        "tb_project_departments",
        ["project_id"],
    )
    op.create_index(
        "idx_tb_project_departments_department_id",
        "tb_project_departments",
        ["department_id"],
    )

    # ------------------------------------------------------------------
    # 3. Create tb_project_members (project membership with roles)
    # ------------------------------------------------------------------
    op.create_table(
        "tb_project_members",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "project_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(20), nullable=False, server_default="member", comment="'manager' or 'member'"),
        *_audit_columns(),
        sa.UniqueConstraint("project_id", "user_id", name="uq_tb_project_members_proj_user"),
    )
    op.create_index(
        "idx_tb_project_members_project_id",
        "tb_project_members",
        ["project_id"],
    )
    op.create_index(
        "idx_tb_project_members_user_id",
        "tb_project_members",
        ["user_id"],
    )

    # ------------------------------------------------------------------
    # 4. Add visibility, department_id, project_id to tb_documents
    #    and make folder_id nullable
    # ------------------------------------------------------------------
    op.alter_column(
        "tb_documents",
        "folder_id",
        existing_type=PG_UUID(as_uuid=True),
        nullable=True,
    )

    op.add_column(
        "tb_documents",
        sa.Column(
            "visibility",
            sa.String(20),
            nullable=False,
            server_default="department_only",
            comment="문서 공개 범위: public, all_departments, department_only, project_only, confidential, hidden",
        ),
    )
    op.add_column(
        "tb_documents",
        sa.Column(
            "department_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_departments.id", ondelete="SET NULL"),
            nullable=True,
            comment="문서 소속 부서",
        ),
    )
    op.add_column(
        "tb_documents",
        sa.Column(
            "project_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_projects.id", ondelete="SET NULL"),
            nullable=True,
            comment="문서 소속 프로젝트",
        ),
    )
    op.create_index(
        "idx_tb_documents_visibility",
        "tb_documents",
        ["visibility"],
    )
    op.create_index(
        "idx_tb_documents_department_id",
        "tb_documents",
        ["department_id"],
    )
    op.create_index(
        "idx_tb_documents_project_id",
        "tb_documents",
        ["project_id"],
    )

    # ------------------------------------------------------------------
    # 5. Create tb_document_access (confidential document access)
    # ------------------------------------------------------------------
    op.create_table(
        "tb_document_access",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "document_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        *_audit_columns(),
        sa.UniqueConstraint("document_id", "user_id", name="uq_tb_document_access_doc_user"),
    )
    op.create_index(
        "idx_tb_document_access_document_id",
        "tb_document_access",
        ["document_id"],
    )
    op.create_index(
        "idx_tb_document_access_user_id",
        "tb_document_access",
        ["user_id"],
    )


def downgrade() -> None:
    # ------------------------------------------------------------------
    # Reverse all changes in reverse order
    # ------------------------------------------------------------------

    # 5. Drop tb_document_access
    op.drop_index("idx_tb_document_access_user_id", table_name="tb_document_access")
    op.drop_index("idx_tb_document_access_document_id", table_name="tb_document_access")
    op.drop_table("tb_document_access")

    # 4. Remove new columns from tb_documents and make folder_id non-nullable
    op.drop_index("idx_tb_documents_project_id", table_name="tb_documents")
    op.drop_index("idx_tb_documents_department_id", table_name="tb_documents")
    op.drop_index("idx_tb_documents_visibility", table_name="tb_documents")
    op.drop_column("tb_documents", "project_id")
    op.drop_column("tb_documents", "department_id")
    op.drop_column("tb_documents", "visibility")
    op.alter_column(
        "tb_documents",
        "folder_id",
        existing_type=PG_UUID(as_uuid=True),
        nullable=False,
    )

    # 3. Drop tb_project_members
    op.drop_index("idx_tb_project_members_user_id", table_name="tb_project_members")
    op.drop_index("idx_tb_project_members_project_id", table_name="tb_project_members")
    op.drop_table("tb_project_members")

    # 2. Drop tb_project_departments
    op.drop_index("idx_tb_project_departments_department_id", table_name="tb_project_departments")
    op.drop_index("idx_tb_project_departments_project_id", table_name="tb_project_departments")
    op.drop_table("tb_project_departments")

    # 1. Remove head_user_id from tb_departments
    op.drop_index("idx_tb_departments_head_user_id", table_name="tb_departments")
    op.drop_column("tb_departments", "head_user_id")
