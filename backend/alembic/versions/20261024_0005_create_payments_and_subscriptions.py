"""create payments, subscriptions, transactions, invoices, and webhook tables

Revision ID: 20261024_0005
Revises: 20261024_0004
Create Date: 2026-10-24 17:30:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20261024_0005"
down_revision: Union[str, None] = "20261024_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Table: subscriptions ──────────────────────────────────────────────────
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), unique=True, nullable=False),
        sa.Column("plan_tier", sa.String(length=30), nullable=False, server_default="free"),
        sa.Column("billing_interval", sa.String(length=20), nullable=False, server_default="month"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column("price_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("current_period_start", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provider", sa.String(length=50), nullable=False, server_default="sandbox"),
        sa.Column("provider_subscription_id", sa.String(length=100), nullable=True),
        sa.Column("provider_customer_id", sa.String(length=100), nullable=True),
        sa.Column("max_target_websites", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("monthly_scan_limit", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("reports_included_per_month", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"], unique=True)
    op.create_index("ix_subscriptions_plan_tier", "subscriptions", ["plan_tier"])
    op.create_index("ix_subscriptions_status", "subscriptions", ["status"])

    # ── Table: payment_transactions ───────────────────────────────────────────
    op.create_table(
        "payment_transactions",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("subscription_id", sa.String(length=36), nullable=True),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("payment_type", sa.String(length=50), nullable=False),
        sa.Column("reference_id", sa.String(length=100), nullable=True),
        sa.Column("provider", sa.String(length=50), nullable=False, server_default="dev_sandbox"),
        sa.Column("provider_payment_id", sa.String(length=100), nullable=True),
        sa.Column("idempotency_key", sa.String(length=100), unique=True, nullable=False),
        sa.Column("receipt_url", sa.String(length=500), nullable=True),
        sa.Column("failure_message", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_payment_transactions_user_id", "payment_transactions", ["user_id"])
    op.create_index("ix_payment_transactions_status", "payment_transactions", ["status"])
    op.create_index("ix_payment_transactions_idempotency_key", "payment_transactions", ["idempotency_key"], unique=True)

    # ── Table: invoices ───────────────────────────────────────────────────────
    op.create_table(
        "invoices",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("subscription_id", sa.String(length=36), nullable=True),
        sa.Column("invoice_number", sa.String(length=64), unique=True, nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="paid"),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("billing_name", sa.String(length=150), nullable=False),
        sa.Column("billing_email", sa.String(length=255), nullable=False),
        sa.Column("pdf_html_content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_invoices_user_id", "invoices", ["user_id"])
    op.create_index("ix_invoices_invoice_number", "invoices", ["invoice_number"], unique=True)
    op.create_index("ix_invoices_status", "invoices", ["status"])

    # ── Table: payment_webhook_events ─────────────────────────────────────────
    op.create_table(
        "payment_webhook_events",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("event_id", sa.String(length=100), unique=True, nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False, server_default="stripe"),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_payment_webhook_events_event_id", "payment_webhook_events", ["event_id"], unique=True)
    op.create_index("ix_payment_webhook_events_event_type", "payment_webhook_events", ["event_type"])


def downgrade() -> None:
    op.drop_table("payment_webhook_events")
    op.drop_table("invoices")
    op.drop_table("payment_transactions")
    op.drop_table("subscriptions")
