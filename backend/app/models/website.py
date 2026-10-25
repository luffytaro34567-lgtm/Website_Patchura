"""SQLAlchemy models for Website Targets, Ownership Verification, and Scan Authorization."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func, desc
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class VerificationMethod(str, enum.Enum):
    FILE = "file"           # /.well-known/patchora-verification.txt (or legacy bughunter-verification.txt)
    META_TAG = "meta_tag"   # <meta name="patchora-verification" content="..."> (or legacy bughunter-verification)
    DNS_TXT = "dns_txt"     # _patchora-challenge.example.com TXT record (or legacy _bughunter-challenge)


class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"


class Website(Base):
    __tablename__ = "websites"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    target_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    domain: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
    )
    verification_method: Mapped[str] = mapped_column(
        String(30),
        default=VerificationMethod.FILE.value,
        nullable=False,
    )
    verification_token: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        default=lambda: f"bh_verify_{uuid.uuid4().hex}",
    )
    verification_status: Mapped[str] = mapped_column(
        String(30),
        default=VerificationStatus.PENDING.value,
        nullable=False,
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_verification_attempt: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    verification_error: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    is_suspended_by_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    suspension_reason: Mapped[Optional[str]] = mapped_column(
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

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="websites",
    )
    authorization: Mapped[Optional["ScanAuthorization"]] = relationship(
        "ScanAuthorization",
        back_populates="website",
        uselist=False,
        cascade="all, delete-orphan",
    )
    scans: Mapped[List["Scan"]] = relationship(
        "Scan",
        back_populates="website",
        cascade="all, delete-orphan",
        order_by="desc(Scan.created_at)",
    )
    findings: Mapped[List["ScanFinding"]] = relationship(
        "ScanFinding",
        back_populates="website",
        cascade="all, delete-orphan",
        order_by="desc(ScanFinding.created_at)",
    )


class ScanAuthorization(Base):
    __tablename__ = "scan_authorizations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    website_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("websites.id", ondelete="CASCADE"),
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
    is_authorized: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    authorized_by_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    authorized_by_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    legal_confirmation: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    allowed_scan_types: Mapped[str] = mapped_column(
        String(255),
        default="passive,owasp_standard",
        nullable=False,
    )
    authorized_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    revocation_reason: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationship
    website: Mapped["Website"] = relationship(
        "Website",
        back_populates="authorization",
    )
