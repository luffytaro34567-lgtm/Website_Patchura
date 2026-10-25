"""Pydantic schemas for vulnerability scanning execution and findings."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.scan import FindingSeverity, ScanProfile, ScanStatus


class CreateScanRequest(BaseModel):
    website_id: str = Field(..., description="Target website ID to scan")
    profile: ScanProfile = Field(
        default=ScanProfile.STANDARD,
        description="Scan profile: passive (headers/TLS), standard (web app hygiene), or php_deep (PHP2Shell & PHP audit)",
    )


class ScanFindingResponse(BaseModel):
    id: str
    scan_id: str
    website_id: str
    title: str
    severity: str
    category: str
    description: str
    evidence: str
    remediation: str
    cwe_id: Optional[str] = None
    cvss_score: Optional[float] = None
    target_url: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ScanResponse(BaseModel):
    id: str
    website_id: str
    user_id: str
    profile: str
    status: str
    progress_percent: int
    target_url: str
    target_domain: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    is_cancelled: bool = False
    cancelled_by: Optional[str] = None
    total_findings: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    created_at: datetime
    findings: Optional[List[ScanFindingResponse]] = None

    model_config = {"from_attributes": True}


class ScanSummaryExport(BaseModel):
    scan_id: str
    target_url: str
    target_domain: str
    profile: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    total_findings: int
    severity_breakdown: Dict[str, int]
    findings: List[ScanFindingResponse]
    exported_at: datetime
    platform: str = "PATCHORA"
    php2shell_shield_evaluated: bool = True
    disclaimer: str = (
        "This automated security summary is provided for authorized vulnerability assessment purposes only. "
        "All scanning activity was conducted under explicit customer authorization."
    )
