"""create activity logs and security alerts tables, add user status and security columns

Revision ID: 20261024_0009
Revises: 20261024_0008
Create Date: 2026-10-24 21:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20261024_0009"
down_revision: Union[str, None] = "20261024_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Add security & client management columns to users table ───────────────
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column("account_status", sa.String(length=20), nullable=False, server_default="active")
        )
        batch_op.add_column(
            sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0")
        )
        batch_op.add_column(
            sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column("force_password_reset", sa.Boolean(), nullable=False, server_default="0")
        )
        batch_op.add_column(
            sa.Column("recovery_token", sa.String(length=128), nullable=True)
        )
        batch_op.add_column(
            sa.Column("recovery_token_expires_at", sa.DateTime(timezone=True), nullable=True)
        )

    # ── Table: activity_logs ──────────────────────────────────────────────────
    op.create_table(
        "activity_logs",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("event_category", sa.String(length=50), nullable=False),
        sa.Column("event_name", sa.String(length=100), nullable=False),
        sa.Column("actor_type", sa.String(length=30), nullable=False, server_default="user"),
        sa.Column("actor_id", sa.String(length=36), nullable=True),
        sa.Column("actor_email", sa.String(length=255), nullable=True),
        sa.Column("target_type", sa.String(length=50), nullable=True),
        sa.Column("target_id", sa.String(length=64), nullable=True),
        sa.Column("target_identifier", sa.String(length=255), nullable=True),
        sa.Column("outcome", sa.String(length=20), nullable=False, server_default="success"),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="info"),
        sa.Column("source_module", sa.String(length=50), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("requires_review", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("is_reviewed", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("reviewed_by_admin_id", sa.String(length=36), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_activity_logs_timestamp", "activity_logs", ["timestamp"])
    op.create_index("ix_activity_logs_event_category", "activity_logs", ["event_category"])
    op.create_index("ix_activity_logs_event_name", "activity_logs", ["event_name"])
    op.create_index("ix_activity_logs_actor_id", "activity_logs", ["actor_id"])
    op.create_index("ix_activity_logs_target_type", "activity_logs", ["target_type"])
    op.create_index("ix_activity_logs_target_id", "activity_logs", ["target_id"])
    op.create_index("ix_activity_logs_source_module", "activity_logs", ["source_module"])
    op.create_index("ix_activity_logs_requires_review", "activity_logs", ["requires_review"])

    # ── Table: security_alerts ────────────────────────────────────────────────
    op.create_table(
        "security_alerts",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("alert_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="high"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("source_module", sa.String(length=50), nullable=False),
        sa.Column("target_entity_type", sa.String(length=50), nullable=True),
        sa.Column("target_entity_id", sa.String(length=64), nullable=True),
        sa.Column("cve_id", sa.String(length=50), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("assigned_admin_id", sa.String(length=36), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_security_alerts_created_at", "security_alerts", ["created_at"])
    op.create_index("ix_security_alerts_alert_type", "security_alerts", ["alert_type"])
    op.create_index("ix_security_alerts_severity", "security_alerts", ["severity"])
    op.create_index("ix_security_alerts_status", "security_alerts", ["status"])
    op.create_index("ix_security_alerts_source_module", "security_alerts", ["source_module"])


def downgrade() -> None:
    op.drop_table("security_alerts")
    op.drop_table("activity_logs")
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("recovery_token_expires_at")
        batch_op.drop_column("recovery_token")
        batch_op.drop_column("force_password_reset")
        batch_op.drop_column("last_login_at")
        batch_op.drop_column("locked_until")
        batch_op.drop_column("failed_login_attempts")
        batch_op.drop_column("account_status")
