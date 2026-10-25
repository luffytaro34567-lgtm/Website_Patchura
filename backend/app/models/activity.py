"""
SQLAlchemy models for Centralized Activity Monitoring, Security Alerts, and Audit Logging.
Prompt 11: Activity & Security Center, Timeline, and Alert Triage.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class EventOutcome(str, enum.Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    BLOCKED = "blocked"
    PENDING = "pending"


class EventSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertSeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AlertStatus(str, enum.Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    FALSE_POSITIVE = "false_positive"


class ActivityLog(Base):
    """
    Centralized, immutable activity audit log table recording all significant
    operational, administrative, security, and client actions across PATCHORA.
    """
    __tablename__ = "activity_logs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        nullable=False,
    )
    event_category: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
    )
    event_name: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )
    actor_type: Mapped[str] = mapped_column(
        String(30),
        default="user",
        nullable=False,
    )
    actor_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        index=True,
        nullable=True,
    )
    actor_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    target_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        index=True,
        nullable=True,
    )
    target_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        index=True,
        nullable=True,
    )
    target_identifier: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    outcome: Mapped[str] = mapped_column(
        String(20),
        default=EventOutcome.SUCCESS.value,
        nullable=False,
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        default=EventSeverity.INFO.value,
        nullable=False,
    )
    source_module: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
    )
    metadata_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    request_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )
    requires_review: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
        nullable=False,
    )
    is_reviewed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    reviewed_by_admin_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class SecurityAlert(Base):
    """
    Security Alert table for real-time triage, threat tracking, and administrative review.
    Specifically tracks PHP2Shell zero-day detections, repeated brute force, unauthorized actions,
    and operational failures.
    """
    __tablename__ = "security_alerts"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    alert_type: Mapped[str] = mapped_column(
        String(64),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        default=AlertSeverity.HIGH.value,
        index=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=AlertStatus.OPEN.value,
        index=True,
        nullable=False,
    )
    source_module: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
    )
    target_entity_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    target_entity_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )
    cve_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    metadata_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    assigned_admin_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
