"""create discovery campaigns, leads, outreach templates, drafts, and suppression list tables

Revision ID: 20261024_0008
Revises: 20261024_0007
Create Date: 2026-10-24 20:30:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20261024_0008"
down_revision: Union[str, None] = "20261024_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Table: discovery_campaigns ────────────────────────────────────────────
    op.create_table(
        "discovery_campaigns",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("created_by_admin_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("target_technology", sa.String(length=100), nullable=False, server_default="PHP / Laravel / WordPress"),
        sa.Column("target_industry", sa.String(length=100), nullable=True),
        sa.Column("search_query", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column("rate_limit_per_day", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("discovered_leads_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("contacted_leads_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("converted_leads_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_admin_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_discovery_campaigns_created_by", "discovery_campaigns", ["created_by_admin_id"])
    op.create_index("ix_discovery_campaigns_status", "discovery_campaigns", ["status"])

    # ── Table: leads ──────────────────────────────────────────────────────────
    op.create_table(
        "leads",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("campaign_id", sa.String(length=36), nullable=True),
        sa.Column("company_name", sa.String(length=150), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("website_url", sa.String(length=500), nullable=False),
        sa.Column("contact_name", sa.String(length=150), nullable=True),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("contact_title", sa.String(length=100), nullable=True),
        sa.Column("contact_source", sa.String(length=50), nullable=False, server_default="manual_entry"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="new"),
        sa.Column("qualification_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("technology_stack", sa.String(length=255), nullable=True),
        sa.Column("php2shell_risk_level", sa.String(length=30), nullable=False, server_default="unknown"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("attributed_client_id", sa.String(length=36), nullable=True),
        sa.Column("attributed_website_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["discovery_campaigns.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["attributed_client_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["attributed_website_id"], ["websites.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_leads_domain", "leads", ["domain"])
    op.create_index("ix_leads_contact_email", "leads", ["contact_email"])
    op.create_index("ix_leads_status", "leads", ["status"])
    op.create_index("ix_leads_php2shell_risk", "leads", ["php2shell_risk_level"])

    # ── Table: outreach_templates ─────────────────────────────────────────────
    op.create_table(
        "outreach_templates",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False, server_default="responsible_disclosure"),
        sa.Column("subject_template", sa.String(length=255), nullable=False),
        sa.Column("body_template", sa.Text(), nullable=False),
        sa.Column("is_approved_by_admin", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── Table: outreach_drafts ────────────────────────────────────────────────
    op.create_table(
        "outreach_drafts",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("lead_id", sa.String(length=36), nullable=False),
        sa.Column("template_id", sa.String(length=36), nullable=True),
        sa.Column("created_by_admin_id", sa.String(length=36), nullable=False),
        sa.Column("recipient_email", sa.String(length=255), nullable=False),
        sa.Column("recipient_name", sa.String(length=150), nullable=False, server_default="Security Team"),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivery_provider", sa.String(length=50), nullable=False, server_default="sandbox_logger"),
        sa.Column("delivery_message_id", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_id"], ["outreach_templates.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_admin_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_outreach_drafts_lead_id", "outreach_drafts", ["lead_id"])
    op.create_index("ix_outreach_drafts_status", "outreach_drafts", ["status"])

    # ── Table: suppression_list ───────────────────────────────────────────────
    op.create_table(
        "suppression_list",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("domain_or_email", sa.String(length=255), unique=True, nullable=False),
        sa.Column("entry_type", sa.String(length=20), nullable=False, server_default="domain"),
        sa.Column("reason", sa.String(length=255), nullable=False, server_default="do_not_contact_request"),
        sa.Column("opted_out_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_suppression_list_target", "suppression_list", ["domain_or_email"])

    # ── Table: lead_audit_logs ────────────────────────────────────────────────
    op.create_table(
        "lead_audit_logs",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("lead_id", sa.String(length=36), nullable=True),
        sa.Column("admin_id", sa.String(length=36), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["admin_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_lead_audit_logs_lead_id", "lead_audit_logs", ["lead_id"])


def downgrade() -> None:
    op.drop_table("lead_audit_logs")
    op.drop_table("suppression_list")
    op.drop_table("outreach_drafts")
    op.drop_table("outreach_templates")
    op.drop_table("leads")
    op.drop_table("discovery_campaigns")
