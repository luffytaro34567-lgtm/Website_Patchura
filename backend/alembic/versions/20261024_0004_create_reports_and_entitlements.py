"""create reports, orders, entitlements, and access logs tables

Revision ID: 20261024_0004
Revises: 20261024_0003
Create Date: 2026-10-24 17:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20261024_0004"
down_revision: Union[str, None] = "20261024_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Table: report_orders ──────────────────────────────────────────────────
    op.create_table(
        "report_orders",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("scan_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("product_name", sa.String(length=150), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False, server_default="49.00"),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("payment_method", sa.String(length=50), nullable=False, server_default="dev_checkout"),
        sa.Column("transaction_reference", sa.String(length=64), unique=True, nullable=False),
        sa.Column("failure_reason", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["scan_id"], ["scans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_report_orders_scan_id", "report_orders", ["scan_id"])
    op.create_index("ix_report_orders_user_id", "report_orders", ["user_id"])
    op.create_index("ix_report_orders_status", "report_orders", ["status"])
    op.create_index("ix_report_orders_transaction_reference", "report_orders", ["transaction_reference"], unique=True)

    # ── Table: report_entitlements ────────────────────────────────────────────
    op.create_table(
        "report_entitlements",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("scan_id", sa.String(length=36), unique=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("order_id", sa.String(length=36), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("granted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("granted_by", sa.String(length=50), nullable=False, server_default="order_checkout"),
        sa.Column("access_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["scan_id"], ["scans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["order_id"], ["report_orders.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_report_entitlements_scan_id", "report_entitlements", ["scan_id"], unique=True)
    op.create_index("ix_report_entitlements_user_id", "report_entitlements", ["user_id"])

    # ── Table: report_documents ───────────────────────────────────────────────
    op.create_table(
        "report_documents",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("scan_id", sa.String(length=36), unique=True, nullable=False),
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("executive_summary", sa.Text(), nullable=False),
        sa.Column("overall_risk_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("overall_posture", sa.String(length=50), nullable=False, server_default="MODERATE RISK"),
        sa.Column("has_php2shell_finding", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("php2shell_posture", sa.String(length=100), nullable=False, server_default="Protected"),
        sa.Column("html_content", sa.Text(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["scan_id"], ["scans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_report_documents_scan_id", "report_documents", ["scan_id"], unique=True)
    op.create_index("ix_report_documents_website_id", "report_documents", ["website_id"])

    # ── Table: report_access_logs ─────────────────────────────────────────────
    op.create_table(
        "report_access_logs",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("scan_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("access_type", sa.String(length=30), nullable=False, server_default="web_view"),
        sa.Column("accessed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("ip_address", sa.String(length=50), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["scan_id"], ["scans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_report_access_logs_scan_id", "report_access_logs", ["scan_id"])
    op.create_index("ix_report_access_logs_user_id", "report_access_logs", ["user_id"])

    # ── Table: report_pricing_configs ─────────────────────────────────────────
    op.create_table(
        "report_pricing_configs",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("product_name", sa.String(length=150), nullable=False),
        sa.Column("price", sa.Float(), nullable=False, server_default="49.00"),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("features_list", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("report_pricing_configs")
    op.drop_table("report_access_logs")
    op.drop_table("report_documents")
    op.drop_table("report_entitlements")
    op.drop_table("report_orders")
