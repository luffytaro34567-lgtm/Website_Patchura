"""Pydantic schemas for Paid Detailed Reports, Entitlements, and Purchases."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.scan import ScanFindingResponse


class ReportPricingResponse(BaseModel):
    product_name: str
    price: float
    currency: str
    description: str
    features: List[str]


class ReportOrderResponse(BaseModel):
    id: str
    scan_id: str
    user_id: str
    product_name: str
    amount: float
    currency: str
    status: str
    payment_method: str
    transaction_reference: str
    failure_reason: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ReportEntitlementResponse(BaseModel):
    id: str
    scan_id: str
    user_id: str
    is_active: bool
    granted_at: datetime
    expires_at: Optional[datetime] = None
    granted_by: str
    access_count: int
    last_accessed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ReportEntitlementStatusResponse(BaseModel):
    scan_id: str
    has_entitlement: bool
    can_purchase: bool
    pricing: ReportPricingResponse
    entitlement: Optional[ReportEntitlementResponse] = None
    active_order: Optional[ReportOrderResponse] = None


class CreateReportOrderRequest(BaseModel):
    scan_id: str = Field(..., description="Target completed scan ID")
    payment_method: str = Field(
        default="dev_checkout",
        description="Checkout method ('dev_checkout', 'admin_grant')",
    )


class CompleteReportOrderRequest(BaseModel):
    simulate_status: str = Field(
        default="completed",
        description="Simulate outcome: 'completed', 'failed', or 'cancelled'",
    )


class AdminGrantEntitlementRequest(BaseModel):
    scan_id: str
    reason: str = Field(..., min_length=3, max_length=500)


class DetailedReportResponse(BaseModel):
    id: str
    scan_id: str
    website_id: str
    title: str
    target_url: str
    target_domain: str
    profile: str
    executive_summary: str
    overall_risk_score: float
    overall_posture: str
    has_php2shell_finding: bool
    php2shell_posture: str
    generated_at: datetime
    version: int
    total_findings: int
    severity_breakdown: Dict[str, int]
    findings: List[ScanFindingResponse]
    html_content: str

    model_config = {"from_attributes": True}
