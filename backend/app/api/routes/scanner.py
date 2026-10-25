"""
Vulnerability scanning and static analysis endpoints.
"""
from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.security.rate_limiter import RateLimit
from app.schemas.scanner import (
    ScanPhpRequest,
    ScanPhpResponse,
    RuleSummaryResponse,
    FindingResponse,
)
from app.services.scanner.php_analyzer import (
    analyze_php_code,
    PHP_RULES,
    get_php2shell_mitigation_plan,
)

router = APIRouter(prefix="/scan", tags=["Vulnerability Scanner"])


@router.post(
    "/php/analyze",
    response_model=ScanPhpResponse,
    summary="Static security analysis of PHP source code",
    description="Analyzes PHP code for vulnerabilities, including PHP2Shell (CVE-2026-109618, CVE-2026-109619) and OWASP Top 10 flaws.",
    dependencies=[Depends(RateLimit(max_requests=30, window_seconds=60, scope="scanner_php"))],
)
async def analyze_php(payload: ScanPhpRequest) -> ScanPhpResponse:
    if not payload.source_code.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Source code cannot be empty.",
        )

    if len(payload.source_code) > 500_000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source code exceeds maximum permitted buffer size (500 KB).",
        )

    result = analyze_php_code(payload.source_code)
    
    findings_data = [
        FindingResponse(
            rule_id=f.rule_id,
            title=f.title,
            severity=f.severity.value,
            owasp=f.owasp,
            cwe=f.cwe,
            line_number=f.line_number,
            line_content=f.line_content,
            description=f.description,
            remediation=f.remediation,
            cve=f.cve,
            cvss_score=f.cvss_score,
            suggested_fix=f.suggested_fix,
        )
        for f in result.findings
    ]

    return ScanPhpResponse(
        total_lines=result.total_lines,
        findings=findings_data,
        has_php2shell_vulnerability=result.has_php2shell_vulnerability,
        summary=result.summary,
        remediation_guidance=result.remediation_guidance,
    )


@router.get(
    "/php/rules",
    response_model=List[RuleSummaryResponse],
    summary="List active PHP vulnerability detection rules",
)
async def list_php_rules() -> List[RuleSummaryResponse]:
    return [
        RuleSummaryResponse(
            rule_id=r.rule_id,
            title=r.title,
            severity=r.severity.value,
            owasp=r.owasp.value,
            cwe=r.cwe,
            cve=r.cve,
            cvss_score=r.cvss_score,
            description=r.description,
        )
        for r in PHP_RULES
    ]


@router.get(
    "/php/php2shell-mitigation",
    summary="Get standard PHP2Shell (CVE-2026-109618 & CVE-2026-109619) remediation blueprint",
)
async def get_php2shell_blueprint():
    return get_php2shell_mitigation_plan()
