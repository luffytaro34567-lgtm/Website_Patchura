"""Pydantic schemas for AI Bug-Fixing Engine, Patch Generation, and Approvals."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CreateRemediationRequest(BaseModel):
    finding_id: str = Field(..., description="Target vulnerability scan finding ID")
    input_method: str = Field(default="snippet", description="'snippet' or 'file_upload'")
    target_filename: str = Field(..., min_length=1, max_length=255, description="Filename being remediated (e.g., index.php, server.py)")
    language: str = Field(default="php", description="Programming language: 'php', 'python', 'javascript', 'html', etc.")
    source_code: str = Field(..., min_length=5, max_length=1000000, description="Raw source code content to remediate")
    consent_acknowledged: bool = Field(..., description="Must explicitly consent to code security analysis and remediation processing")


class RunTestRequest(BaseModel):
    isolated_timeout_seconds: Optional[int] = Field(default=30, ge=5, le=120)


class TestResultResponse(BaseModel):
    session_id: str
    test_status: str  # passed | failed | syntax_error
    passed: bool
    diagnostics: str
    tested_at: datetime


class ApprovePatchRequest(BaseModel):
    approval_notes: Optional[str] = Field(default=None, max_length=1000, description="Optional sign-off notes or review remarks")


class RejectPatchRequest(BaseModel):
    rejection_reason: str = Field(..., min_length=3, max_length=1000, description="Reason for rejecting the proposed patch")


class RemediationAuditLogResponse(BaseModel):
    id: str
    action: str
    details: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RemediationSessionResponse(BaseModel):
    id: str
    finding_id: str
    scan_id: str
    website_id: str
    user_id: str
    input_method: str
    target_filename: str
    language: str
    original_code: str
    status: str
    ai_provider: str
    proposed_diff: Optional[str] = None
    patched_code: Optional[str] = None
    explanation: Optional[str] = None
    security_warnings: Optional[str] = None
    php2shell_mitigation_notes: Optional[str] = None
    confidence_score: Optional[float] = None
    test_status: str
    test_output: Optional[str] = None
    tested_at: Optional[datetime] = None
    approval_status: str
    approval_notes: Optional[str] = None
    approved_at: Optional[datetime] = None
    client_consent_given: bool
    created_at: datetime
    updated_at: datetime

    # Associated finding details for UI context
    finding_title: Optional[str] = None
    finding_severity: Optional[str] = None
    finding_category: Optional[str] = None
    cwe_id: Optional[str] = None
    website_domain: Optional[str] = None

    model_config = {"from_attributes": True}


class RemediationSessionSummary(BaseModel):
    id: str
    finding_id: str
    finding_title: str
    finding_severity: str
    website_domain: str
    target_filename: str
    language: str
    status: str
    ai_provider: str
    test_status: str
    approval_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminRemediationStatsResponse(BaseModel):
    total_remediations: int
    approved_patches: int
    rejected_patches: int
    tests_passed: int
    tests_failed: int
    pending_approval: int
    ai_provider_active: str
