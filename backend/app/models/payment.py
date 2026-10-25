"""
SQLAlchemy models for Payment Gateway, Subscriptions, Invoices, Transactions, and Webhooks.
Financial operations strictly utilize integer minor-units (cents) to eliminate binary floating-point inaccuracies.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class BillingInterval(str, enum.Enum):
    MONTH = "month"
    YEAR = "year"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class InvoiceStatus(str, enum.Enum):
    PAID = "paid"
    OPEN = "open"
    VOID = "void"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    plan_tier: Mapped[str] = mapped_column(
        String(30),
        default=SubscriptionTier.FREE.value,
        index=True,
        nullable=False,
    )
    billing_interval: Mapped[str] = mapped_column(
        String(20),
        default=BillingInterval.MONTH.value,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default=SubscriptionStatus.ACTIVE.value,
        index=True,
        nullable=False,
    )
    price_cents: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        default="USD",
        nullable=False,
    )
    current_period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    current_period_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(
        String(50),
        default="sandbox",
        nullable=False,
    )
    provider_subscription_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    provider_customer_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Quota Limits
    max_target_websites: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    monthly_scan_limit: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
    )
    reports_included_per_month: Mapped[int] = mapped_column(
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
    user: Mapped["User"] = relationship("User", back_populates="subscription")
    invoices: Mapped[List["Invoice"]] = relationship(
        "Invoice",
        back_populates="subscription",
        cascade="all, delete-orphan",
        order_by="desc(Invoice.created_at)",
    )


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

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
    subscription_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
    )
    amount_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        default="USD",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default=TransactionStatus.PENDING.value,
        index=True,
        nullable=False,
    )
    payment_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    reference_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    provider: Mapped[str] = mapped_column(
        String(50),
        default="dev_sandbox",
        nullable=False,
    )
    provider_payment_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    receipt_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    failure_message: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="transactions")


class Invoice(Base):
    __tablename__ = "invoices"

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
    subscription_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
    )
    invoice_number: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        default=lambda: f"INV-2026-{uuid.uuid4().hex[:8].upper()}",
        nullable=False,
    )
    amount_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        default="USD",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default=InvoiceStatus.PAID.value,
        index=True,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    billing_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    billing_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    pdf_html_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="invoices")
    subscription: Mapped[Optional["Subscription"]] = relationship("Subscription", back_populates="invoices")


class PaymentWebhookEvent(Base):
    __tablename__ = "payment_webhook_events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    event_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(
        String(50),
        default="stripe",
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )
    payload_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    processed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
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
