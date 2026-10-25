"""create websites and scan_authorizations tables

Revision ID: 20261024_0002
Revises: 20261024_0001
Create Date: 2026-10-24 16:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20261024_0002"
down_revision: Union[str, None] = "20261024_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Table: websites ───────────────────────────────────────────────────────
    op.create_table(
        "websites",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("target_url", sa.String(length=500), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("verification_method", sa.String(length=30), nullable=False, server_default="file"),
        sa.Column("verification_token", sa.String(length=64), nullable=False),
        sa.Column("verification_status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_verification_attempt", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_error", sa.String(length=500), nullable=True),
        sa.Column("is_suspended_by_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("suspension_reason", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_websites_user_id", "websites", ["user_id"])
    op.create_index("ix_websites_domain", "websites", ["domain"])
    op.create_index("ix_websites_verification_token", "websites", ["verification_token"], unique=True)

    # ── Table: scan_authorizations ────────────────────────────────────────────
    op.create_table(
        "scan_authorizations",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("is_authorized", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("authorized_by_name", sa.String(length=100), nullable=False),
        sa.Column("authorized_by_email", sa.String(length=255), nullable=False),
        sa.Column("legal_confirmation", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("allowed_scan_types", sa.String(length=255), nullable=False, server_default="passive,owasp_standard"),
        sa.Column("authorized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revocation_reason", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_scan_authorizations_website_id", "scan_authorizations", ["website_id"], unique=True)
    op.create_index("ix_scan_authorizations_user_id", "scan_authorizations", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_scan_authorizations_user_id", table_name="scan_authorizations")
    op.drop_index("ix_scan_authorizations_website_id", table_name="scan_authorizations")
    op.drop_table("scan_authorizations")

    op.drop_index("ix_websites_verification_token", table_name="websites")
    op.drop_index("ix_websites_domain", table_name="websites")
    op.drop_index("ix_websites_user_id", table_name="websites")
    op.drop_table("websites")
