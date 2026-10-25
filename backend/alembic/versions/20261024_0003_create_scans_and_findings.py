"""create scans and scan_findings tables

Revision ID: 20261024_0003
Revises: 20261024_0002
Create Date: 2026-10-24 16:30:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20261024_0003"
down_revision: Union[str, None] = "20261024_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Table: scans ──────────────────────────────────────────────────────────
    op.create_table(
        "scans",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("profile", sa.String(length=30), nullable=False, server_default="standard"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="queued"),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("target_url", sa.String(length=500), nullable=False),
        sa.Column("target_domain", sa.String(length=255), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("is_cancelled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("cancelled_by", sa.String(length=50), nullable=True),
        sa.Column("total_findings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("critical_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("high_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("medium_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("low_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("info_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_scans_website_id", "scans", ["website_id"])
    op.create_index("ix_scans_user_id", "scans", ["user_id"])
    op.create_index("ix_scans_status", "scans", ["status"])
    op.create_index("ix_scans_target_domain", "scans", ["target_domain"])

    # ── Table: scan_findings ──────────────────────────────────────────────────
    op.create_table(
        "scan_findings",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("scan_id", sa.String(length=36), nullable=False),
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("remediation", sa.Text(), nullable=False),
        sa.Column("cwe_id", sa.String(length=50), nullable=True),
        sa.Column("cvss_score", sa.Float(), nullable=True),
        sa.Column("target_url", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["scan_id"], ["scans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_scan_findings_scan_id", "scan_findings", ["scan_id"])
    op.create_index("ix_scan_findings_website_id", "scan_findings", ["website_id"])
    op.create_index("ix_scan_findings_severity", "scan_findings", ["severity"])
    op.create_index("ix_scan_findings_category", "scan_findings", ["category"])


def downgrade() -> None:
    op.drop_table("scan_findings")
    op.drop_table("scans")
