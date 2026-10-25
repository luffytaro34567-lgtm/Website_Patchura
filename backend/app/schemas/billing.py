"""Pydantic schemas for Payments, Subscriptions, Invoices, and Billing operations."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class PlanTierInfo(BaseModel):
    tier: str
    name: str
    tag: str
    monthly_price_cents: int
    annual_price_cents: int
    currency: str
    max_target_websites: int
    monthly_scan_limit: int
    reports_included_per_month: int
    features: List[str]


class SubscriptionResponse(BaseModel):
    id: str
    user_id: str
    plan_tier: str
    billing_interval: str
    status: str
    price_cents: int
    currency: str
    current_period_start: datetime
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool
    provider: str
    max_target_websites: int
    monthly_scan_limit: int
    reports_included_per_month: int
    current_target_count: int = 0
    scans_used_this_month: int = 0

    model_config = {"from_attributes": True}


class CreateCheckoutSessionRequest(BaseModel):
    plan_tier: str = Field(..., description="Target plan tier: 'pro' or 'enterprise'")
    billing_interval: str = Field(default="month", description="'month' or 'year'")
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CheckoutSessionResponse(BaseModel):
    session_id: str
    checkout_url: str
    provider: str
    amount_cents: int
    currency: str
    plan_tier: str
    billing_interval: str


class SimulateCheckoutCompletionRequest(BaseModel):
    session_id: str
    outcome: str = Field(default="succeeded", description="'succeeded' or 'failed'")
    plan_tier: Optional[str] = None
    billing_interval: Optional[str] = None


class CreateOneTimeCheckoutRequest(BaseModel):
    product_name: str = Field(..., description="Name of the item being purchased")
    amount_cents: int = Field(..., ge=100, description="Price in minor-unit cents")
    reference_id: str = Field(..., description="Identifier for item, e.g. report order reference or scan ID")
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class OneTimeCheckoutResponse(BaseModel):
    session_id: str
    checkout_url: str
    provider: str
    amount_cents: int
    currency: str
    reference_id: str


class InvoiceResponse(BaseModel):
    id: str
    invoice_number: str
    amount_cents: int
    currency: str
    status: str
    description: str
    paid_at: Optional[datetime] = None
    billing_name: str
    billing_email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionResponse(BaseModel):
    id: str
    user_id: str
    amount_cents: int
    currency: str
    status: str
    payment_type: str
    reference_id: Optional[str] = None
    provider: str
    idempotency_key: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminBillingStatsResponse(BaseModel):
    total_revenue_cents: int
    active_subscriptions_count: int
    pro_subscriptions_count: int
    enterprise_subscriptions_count: int
    total_transactions_count: int
