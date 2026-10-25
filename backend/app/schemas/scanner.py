"""
Pydantic schemas for vulnerability scanning and analysis requests/responses.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ScanPhpRequest(BaseModel):
    source_code: str = Field(..., min_length=1, max_length=500_000, description="PHP code or configuration content to analyze")
    file_name: Optional[str] = Field("index.php", description="Optional file name reference")


class FindingResponse(BaseModel):
    rule_id: str
    title: str
    severity: str
    owasp: str
    cwe: str
    line_number: int
    line_content: str
    description: str
    remediation: str
    cve: Optional[str] = None
    cvss_score: Optional[float] = None
    suggested_fix: Optional[str] = None


class RecommendedAction(BaseModel):
    layer: str
    priority: str
    step: str
    configuration_snippet: Optional[str] = None
    code_snippet: Optional[str] = None


class MitigationPlanResponse(BaseModel):
    vulnerability: str
    cves: List[str]
    cvss_score: float
    impact: str
    affected_versions: str
    recommended_actions: List[RecommendedAction]


class ScanPhpResponse(BaseModel):
    total_lines: int
    findings: List[FindingResponse]
    has_php2shell_vulnerability: bool
    summary: Dict[str, Any]
    remediation_guidance: Optional[MitigationPlanResponse] = None


class RuleSummaryResponse(BaseModel):
    rule_id: str
    title: str
    severity: str
    owasp: str
    cwe: str
    cve: Optional[str] = None
    cvss_score: Optional[float] = None
    description: str
