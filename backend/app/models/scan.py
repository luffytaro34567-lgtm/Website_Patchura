"""SQLAlchemy models for Vulnerability Scans and Scan Findings."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ScanProfile(str, enum.Enum):
    PASSIVE = "passive"       # Safe passive inspection: TLS, security headers, server disclosure
    STANDARD = "standard"     # Standard web assessment: headers, cookie flags, CORS, sensitive paths
    PHP_DEEP = "php_deep"     # Targeted PHP inspection: PHP2Shell RCE error disclosure, server banner, PHP files


class ScanStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FindingSeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    website_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("websites.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    profile: Mapped[str] = mapped_column(
        String(30),
        default=ScanProfile.STANDARD.value,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default=ScanStatus.QUEUED.value,
        index=True,
        nullable=False,
    )
    progress_percent: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    target_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    target_domain: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    duration_seconds: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    is_cancelled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    cancelled_by: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    # Severity and finding counts
    total_findings: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    critical_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    high_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    medium_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    low_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    info_count: Mapped[int] = mapped_column(
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

    # Relationships
    website: Mapped["Website"] = relationship(
        "Website",
        back_populates="scans",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="scans",
    )
    findings: Mapped[List["ScanFinding"]] = relationship(
        "ScanFinding",
        back_populates="scan",
        cascade="all, delete-orphan",
        order_by="ScanFinding.created_at",
    )
    entitlement: Mapped[Optional["ReportEntitlement"]] = relationship(
        "ReportEntitlement",
        back_populates="scan",
        uselist=False,
        cascade="all, delete-orphan",
    )
    orders: Mapped[List["ReportOrder"]] = relationship(
        "ReportOrder",
        back_populates="scan",
        cascade="all, delete-orphan",
    )
    document: Mapped[Optional["ReportDocument"]] = relationship(
        "ReportDocument",
        back_populates="scan",
        uselist=False,
        cascade="all, delete-orphan",
    )


class ScanFinding(Base):
    __tablename__ = "scan_findings"

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
    severity: Mapped[str] = mapped_column(
        String(20),
        index=True,
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    evidence: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    remediation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    cwe_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    cvss_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    target_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    scan: Mapped["Scan"] = relationship(
        "Scan",
        back_populates="findings",
    )
    website: Mapped["Website"] = relationship(
        "Website",
        back_populates="findings",
    )
