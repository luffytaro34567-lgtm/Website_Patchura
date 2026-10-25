"""create remediation sessions and audit logs tables

Revision ID: 20261024_0006
Revises: 20261024_0005
Create Date: 2026-10-24 18:30:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20261024_0006"
down_revision: Union[str, None] = "20261024_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Table: remediation_sessions ───────────────────────────────────────────
    op.create_table(
        "remediation_sessions",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("finding_id", sa.String(length=36), nullable=False),
        sa.Column("scan_id", sa.String(length=36), nullable=False),
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("input_method", sa.String(length=30), nullable=False, server_default="snippet"),
        sa.Column("target_filename", sa.String(length=255), nullable=False),
        sa.Column("language", sa.String(length=50), nullable=False, server_default="php"),
        sa.Column("original_code", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("ai_provider", sa.String(length=50), nullable=False, server_default="deterministic_rules"),
        sa.Column("proposed_diff", sa.Text(), nullable=True),
        sa.Column("patched_code", sa.Text(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("security_warnings", sa.Text(), nullable=True),
        sa.Column("php2shell_mitigation_notes", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True, server_default="0.95"),
        sa.Column("test_status", sa.String(length=30), nullable=False, server_default="untested"),
        sa.Column("test_output", sa.Text(), nullable=True),
        sa.Column("tested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approval_status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("approval_notes", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_consent_given", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["finding_id"], ["scan_findings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scan_id"], ["scans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_remediation_sessions_finding_id", "remediation_sessions", ["finding_id"])
    op.create_index("ix_remediation_sessions_scan_id", "remediation_sessions", ["scan_id"])
    op.create_index("ix_remediation_sessions_website_id", "remediation_sessions", ["website_id"])
    op.create_index("ix_remediation_sessions_user_id", "remediation_sessions", ["user_id"])
    op.create_index("ix_remediation_sessions_status", "remediation_sessions", ["status"])
    op.create_index("ix_remediation_sessions_approval_status", "remediation_sessions", ["approval_status"])

    # ── Table: remediation_audit_logs ─────────────────────────────────────────
    op.create_table(
        "remediation_audit_logs",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["remediation_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_remediation_audit_logs_session_id", "remediation_audit_logs", ["session_id"])
    op.create_index("ix_remediation_audit_logs_user_id", "remediation_audit_logs", ["user_id"])


def downgrade() -> None:
    op.drop_table("remediation_audit_logs")
    op.drop_table("remediation_sessions")
