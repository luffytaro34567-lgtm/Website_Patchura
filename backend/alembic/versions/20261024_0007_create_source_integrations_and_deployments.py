"""create repository connections, deployment targets, and deployment records tables

Revision ID: 20261024_0007
Revises: 20261024_0006
Create Date: 2026-10-24 19:30:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20261024_0007"
down_revision: Union[str, None] = "20261024_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Table: repository_connections ─────────────────────────────────────────
    op.create_table(
        "repository_connections",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("website_id", sa.String(length=36), nullable=True),
        sa.Column("provider", sa.String(length=50), nullable=False, server_default="github"),
        sa.Column("repo_name", sa.String(length=255), nullable=False),
        sa.Column("default_branch", sa.String(length=100), nullable=False, server_default="main"),
        sa.Column("masked_token", sa.String(length=100), nullable=False),
        sa.Column("encrypted_token", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_repository_connections_user_id", "repository_connections", ["user_id"])
    op.create_index("ix_repository_connections_website_id", "repository_connections", ["website_id"])

    # ── Table: deployment_targets ─────────────────────────────────────────────
    op.create_table(
        "deployment_targets",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("environment", sa.String(length=30), nullable=False, server_default="staging"),
        sa.Column("target_type", sa.String(length=50), nullable=False, server_default="github_pr"),
        sa.Column("endpoint_url", sa.String(length=500), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("health_check_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_deployment_targets_user_id", "deployment_targets", ["user_id"])
    op.create_index("ix_deployment_targets_website_id", "deployment_targets", ["website_id"])

    # ── Table: deployment_records ─────────────────────────────────────────────
    op.create_table(
        "deployment_records",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("target_id", sa.String(length=36), nullable=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("environment", sa.String(length=30), nullable=False, server_default="staging"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("git_branch", sa.String(length=255), nullable=False),
        sa.Column("git_commit_sha", sa.String(length=64), nullable=True),
        sa.Column("pull_request_url", sa.String(length=500), nullable=True),
        sa.Column("pull_request_number", sa.Integer(), nullable=True),
        sa.Column("pre_deployment_test_status", sa.String(length=30), nullable=False, server_default="passed"),
        sa.Column("client_approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_notes", sa.Text(), nullable=True),
        sa.Column("deployed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rollback_snapshot", sa.Text(), nullable=True),
        sa.Column("rollback_executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rollback_reason", sa.Text(), nullable=True),
        sa.Column("audit_trail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["remediation_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_id"], ["deployment_targets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_deployment_records_session_id", "deployment_records", ["session_id"])
    op.create_index("ix_deployment_records_user_id", "deployment_records", ["user_id"])
    op.create_index("ix_deployment_records_website_id", "deployment_records", ["website_id"])
    op.create_index("ix_deployment_records_status", "deployment_records", ["status"])


def downgrade() -> None:
    op.drop_table("deployment_records")
    op.drop_table("deployment_targets")
    op.drop_table("repository_connections")
