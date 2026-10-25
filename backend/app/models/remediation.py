"""SQLAlchemy models for AI Bug-Fixing Engine, Patch Generation, Isolated Testing, and Human Approval."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class RemediationStatus(str, enum.Enum):
    PENDING = "pending"
    GENERATING = "generating"
    PATCH_READY = "patch_ready"
    TESTING = "testing"
    TEST_PASSED = "test_passed"
    TEST_FAILED = "test_failed"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"


class TestStatus(str, enum.Enum):
    UNTESTED = "untested"
    PASSED = "passed"
    FAILED = "failed"
    SYNTAX_ERROR = "syntax_error"


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class RemediationSession(Base):
    __tablename__ = "remediation_sessions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    finding_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("scan_findings.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
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
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Input code details
    input_method: Mapped[str] = mapped_column(
        String(30),
        default="snippet",  # snippet | file_upload
        nullable=False,
    )
    target_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    language: Mapped[str] = mapped_column(
        String(50),
        default="php",
        nullable=False,
    )
    original_code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Lifecycle & status
    status: Mapped[str] = mapped_column(
        String(30),
        default=RemediationStatus.PENDING.value,
        index=True,
        nullable=False,
    )
    ai_provider: Mapped[str] = mapped_column(
        String(50),
        default="deterministic_rules",
        nullable=False,
    )

    # Proposed Patch Artifacts
    proposed_diff: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    patched_code: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    explanation: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    security_warnings: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    php2shell_mitigation_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Float,
        default=0.95,
        nullable=True,
    )

    # Isolated Sandbox Test Verification
    test_status: Mapped[str] = mapped_column(
        String(30),
        default=TestStatus.UNTESTED.value,
        nullable=False,
    )
    test_output: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    tested_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Human-in-the-Loop Explicit Approval
    approval_status: Mapped[str] = mapped_column(
        String(30),
        default=ApprovalStatus.PENDING.value,
        index=True,
        nullable=False,
    )
    approval_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Client consent & audit
    client_consent_given: Mapped[bool] = mapped_column(
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

    # Relationships
    finding: Mapped["ScanFinding"] = relationship("ScanFinding", backref="remediation_sessions")
    scan: Mapped["Scan"] = relationship("Scan", backref="remediation_sessions")
    website: Mapped["Website"] = relationship("Website", backref="remediation_sessions")
    user: Mapped["User"] = relationship("User", backref="remediation_sessions")
    audit_logs: Mapped[List["RemediationAuditLog"]] = relationship(
        "RemediationAuditLog",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="desc(RemediationAuditLog.created_at)",
    )


class RemediationAuditLog(Base):
    __tablename__ = "remediation_audit_logs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("remediation_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
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
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    session: Mapped["RemediationSession"] = relationship("RemediationSession", back_populates="audit_logs")
