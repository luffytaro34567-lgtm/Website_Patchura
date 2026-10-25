"""
Pydantic Schemas for Centralized Activity Monitoring, Security Alerts, and Client Administration.
Prompt 11: Activity & Security Center.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ActivityLogResponse(BaseModel):
    id: str
    timestamp: datetime
    event_category: str
    event_name: str
    actor_type: str
    actor_id: Optional[str] = None
    actor_email: Optional[str] = None
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    target_identifier: Optional[str] = None
    outcome: str
    severity: str
    source_module: str
    metadata_json: Optional[str] = None
    request_id: Optional[str] = None
    requires_review: bool = False
    is_reviewed: bool = False
    reviewed_by_admin_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReviewActivityRequest(BaseModel):
    is_reviewed: bool = True
    review_notes: Optional[str] = None


class SecurityAlertResponse(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime
    alert_type: str
    title: str
    description: str
    severity: str
    status: str
    source_module: str
    target_entity_type: Optional[str] = None
    target_entity_id: Optional[str] = None
    cve_id: Optional[str] = None
    metadata_json: Optional[str] = None
    assigned_admin_id: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TriageAlertRequest(BaseModel):
    status: str = Field(..., description="Target status: acknowledged, resolved, dismissed, false_positive")
    resolution_notes: Optional[str] = Field(None, description="Detailed triage remarks or mitigation justification")


class ActivitySummaryMetrics(BaseModel):
    timeframe: str  # 24h, 7d, 30d, custom
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    # Client account metrics
    total_clients: int
    active_clients: int
    suspended_clients: int
    terminated_clients: int
    # Login & Recovery metrics
    recent_successful_logins: int
    recent_failed_logins: int
    pending_recovery_requests: int
    # Security alerts
    open_security_alerts: int
    critical_security_alerts: int
    php2shell_alerts_count: int
    # Operational module event counts
    website_verification_events: int
    scans_running: int
    scans_completed: int
    scans_failed_or_blocked: int
    report_access_events: int
    payments_successful: int
    payments_failed: int
    remediations_approved: int
    deployments_staging: int
    deployments_production: int
    client_finder_outreach_sent: int
    background_jobs_attention_required: int


class ClientProfileExtendedResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    is_active: bool
    account_status: str
    failed_login_attempts: int
    locked_until: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    force_password_reset: bool = False
    recovery_token_expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    # Linked domain, scan, and billing counts
    websites_count: int
    scans_count: int
    reports_count: int
    active_plan: str
    remediations_count: int
    deployments_count: int

    class Config:
        from_attributes = True


class UpdateClientStatusRequest(BaseModel):
    account_status: str = Field(..., description="active | suspended | terminated")
    reason: Optional[str] = Field(None, description="Administrative justification")


class AdminPasswordResetRequest(BaseModel):
    temporary_password: Optional[str] = Field(None, min_length=8, description="Optional temporary password to set")
    force_change_on_login: bool = Field(True, description="Require password change at next login")


class BackgroundJobStatus(BaseModel):
    name: str
    status: str  # "healthy" | "operational" | "degraded" | "attention_required"
    category: str
    details: str
    requires_attention: bool
    last_run: Optional[datetime] = None
