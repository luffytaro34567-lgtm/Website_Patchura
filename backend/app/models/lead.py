"""SQLAlchemy models for Client Finder Automation, Lead Discovery, Outreach, and Suppression."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class LeadStatus(str, enum.Enum):
    NEW = "new"
    QUALIFIED = "qualified"
    CONTACTED = "contacted"
    REPLIED = "replied"
    INTERESTED = "interested"
    CONVERTED = "converted"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class CampaignStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OutreachStatus(str, enum.Enum):
    DRAFT = "draft"
    APPROVED_PENDING_SEND = "approved_pending_send"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"
    OPTED_OUT = "opted_out"


class RiskLevel(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    UNKNOWN = "unknown"


class DiscoveryCampaign(Base):
    __tablename__ = "discovery_campaigns"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    created_by_admin_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    target_technology: Mapped[str] = mapped_column(
        String(100),
        default="PHP / Laravel / WordPress",
        nullable=False,
    )
    target_industry: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    search_query: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default=CampaignStatus.ACTIVE.value,
        index=True,
        nullable=False,
    )
    rate_limit_per_day: Mapped[int] = mapped_column(
        Integer,
        default=50,
        nullable=False,
    )
    discovered_leads_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    contacted_leads_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    converted_leads_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    leads: Mapped[List["Lead"]] = relationship("Lead", back_populates="campaign", cascade="all, delete-orphan")


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    campaign_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("discovery_campaigns.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    company_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    domain: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
    )
    website_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    contact_name: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
    )
    contact_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        index=True,
        nullable=True,
    )
    contact_title: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    contact_source: Mapped[str] = mapped_column(
        String(50),
        default="manual_entry",  # manual_entry | security_txt | public_dns | whois_contact
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default=LeadStatus.NEW.value,
        index=True,
        nullable=False,
    )
    qualification_score: Mapped[int] = mapped_column(
        Integer,
        default=50,
        nullable=False,
    )
    technology_stack: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    php2shell_risk_level: Mapped[str] = mapped_column(
        String(30),
        default=RiskLevel.UNKNOWN.value,
        index=True,
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    attributed_client_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    attributed_website_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("websites.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    campaign: Mapped[Optional["DiscoveryCampaign"]] = relationship("DiscoveryCampaign", back_populates="leads")
    outreach_drafts: Mapped[List["OutreachDraft"]] = relationship("OutreachDraft", back_populates="lead", cascade="all, delete-orphan")
    audit_logs: Mapped[List["LeadAuditLog"]] = relationship("LeadAuditLog", back_populates="lead", cascade="all, delete-orphan")


class OutreachTemplate(Base):
    __tablename__ = "outreach_templates"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        String(50),
        default="responsible_disclosure",
        nullable=False,
    )
    subject_template: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    body_template: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    is_approved_by_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class OutreachDraft(Base):
    __tablename__ = "outreach_drafts"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    lead_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("leads.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    template_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("outreach_templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by_admin_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    recipient_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    recipient_name: Mapped[str] = mapped_column(
        String(150),
        default="Security Team",
        nullable=False,
    )
    subject: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default=OutreachStatus.DRAFT.value,
        index=True,
        nullable=False,
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    delivery_provider: Mapped[str] = mapped_column(
        String(50),
        default="sandbox_logger",
        nullable=False,
    )
    delivery_message_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    lead: Mapped["Lead"] = relationship("Lead", back_populates="outreach_drafts")


class SuppressionList(Base):
    __tablename__ = "suppression_list"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    domain_or_email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    entry_type: Mapped[str] = mapped_column(
        String(20),  # "email" | "domain"
        default="domain",
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(
        String(255),
        default="do_not_contact_request",
        nullable=False,
    )
    opted_out_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class LeadAuditLog(Base):
    __tablename__ = "lead_audit_logs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    lead_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("leads.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    admin_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    details: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    lead: Mapped[Optional["Lead"]] = relationship("Lead", back_populates="audit_logs")
