"""SQLAlchemy models for Paid Detailed Vulnerability Reports, Entitlements, and Access Logs."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class ReportOrderStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReportEntitlement(Base):
    __tablename__ = "report_entitlements"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    scan_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("scans.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    order_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("report_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    granted_by: Mapped[str] = mapped_column(
        String(50),
        default="order_checkout",
        nullable=False,
    )
    access_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    scan: Mapped["Scan"] = relationship("Scan", back_populates="entitlement")
    user: Mapped["User"] = relationship("User", back_populates="report_entitlements")
    order: Mapped[Optional["ReportOrder"]] = relationship("ReportOrder", back_populates="entitlement")


class ReportOrder(Base):
    __tablename__ = "report_orders"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    scan_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("scans.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    product_name: Mapped[str] = mapped_column(
        String(150),
        default="Detailed Vulnerability & Remediation Report",
        nullable=False,
    )
    amount: Mapped[float] = mapped_column(
        Float,
        default=49.00,
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        default="USD",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default=OrderStatus.PENDING.value,
        index=True,
        nullable=False,
    )
    payment_method: Mapped[str] = mapped_column(
        String(50),
        default="dev_checkout",
        nullable=False,
    )
    transaction_reference: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        default=lambda: f"ORD-BH-{uuid.uuid4().hex[:12].upper()}",
        nullable=False,
    )
    failure_reason: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    scan: Mapped["Scan"] = relationship("Scan", back_populates="orders")
    user: Mapped["User"] = relationship("User", back_populates="report_orders")
    entitlement: Mapped[Optional["ReportEntitlement"]] = relationship(
        "ReportEntitlement",
        back_populates="order",
        uselist=False,
    )


class ReportDocument(Base):
    __tablename__ = "report_documents"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    scan_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("scans.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    website_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("websites.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    executive_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    overall_risk_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    overall_posture: Mapped[str] = mapped_column(
        String(50),
        default="MODERATE RISK",
        nullable=False,
    )
    has_php2shell_finding: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    php2shell_posture: Mapped[str] = mapped_column(
        String(100),
        default="Protected (Zero-Day Shield Active)",
        nullable=False,
    )
    html_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    # Relationships
    scan: Mapped["Scan"] = relationship("Scan", back_populates="document")
    website: Mapped["Website"] = relationship("Website")


class ReportAccessLog(Base):
    __tablename__ = "report_access_logs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    scan_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("scans.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    access_type: Mapped[str] = mapped_column(
        String(30),
        default="web_view",
        nullable=False,
    )
    accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )


class ReportPricingConfig(Base):
    __tablename__ = "report_pricing_configs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    product_name: Mapped[str] = mapped_column(
        String(150),
        default="Comprehensive Vulnerability & Remediation Report",
        nullable=False,
    )
    price: Mapped[float] = mapped_column(
        Float,
        default=49.00,
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        default="USD",
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        default=(
            "Executive and developer-ready vulnerability assessment report. "
            "Includes CVSS v3.1 scoring, concrete proof evidence, actionable code patches, "
            "compliance posture, and PHP2Shell (CVE-2026-109618 / 19) defensive audit."
        ),
        nullable=False,
    )
    features_list: Mapped[str] = mapped_column(
        Text,
        default="Executive Risk Summary,CVSS v3.1 Matrix,Concrete Stored Evidence,Developer Code Remediation,PHP2Shell Zero-Day Posture,Printable HTML & PDF Export",
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
