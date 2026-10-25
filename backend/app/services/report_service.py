"""
Report generation and entitlement verification service.
Generates comprehensive executive & technical vulnerability assessment reports.
Incorporate PHP2Shell (CVE-2026-109618 & CVE-2026-109619) defense-in-depth posture.
"""
from __future__ import annotations

from datetime import datetime, timezone
import html
from typing import List, Optional, Tuple

import structlog
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.report import (
    OrderStatus,
    ReportAccessLog,
    ReportDocument,
    ReportEntitlement,
    ReportOrder,
    ReportPricingConfig,
)
from app.models.scan import FindingSeverity, Scan, ScanFinding, ScanStatus
from app.models.user import User
from app.models.website import Website

logger = structlog.get_logger(__name__)

DEFAULT_PRODUCT_NAME = "Comprehensive Vulnerability & Remediation Report"
DEFAULT_PRODUCT_PRICE = 49.00
DEFAULT_CURRENCY = "USD"
DEFAULT_PRODUCT_DESCRIPTION = (
    "Executive and developer-ready vulnerability assessment report. "
    "Includes CVSS v3.1 scoring, concrete proof evidence, actionable code patches, "
    "compliance posture, and PHP2Shell (CVE-2026-109618 / 19) defensive audit."
)
DEFAULT_FEATURES = [
    "Executive Risk Summary & Scoring",
    "CVSS v3.1 Impact Prioritization",
    "Concrete Stored Evidence Proofs",
    "Developer Remediation Playbooks",
    "PHP2Shell Zero-Day Defensive Posture",
    "Printable & Archivable HTML/PDF Report Format",
]


class ReportService:
    @staticmethod
    async def get_or_create_pricing(db: AsyncSession) -> ReportPricingConfig:
        stmt = select(ReportPricingConfig).where(ReportPricingConfig.is_active == True)
        res = await db.execute(stmt)
        config = res.scalar_one_or_none()
        if not config:
            config = ReportPricingConfig(
                product_name=DEFAULT_PRODUCT_NAME,
                price=DEFAULT_PRODUCT_PRICE,
                currency=DEFAULT_CURRENCY,
                description=DEFAULT_PRODUCT_DESCRIPTION,
                features_list=",".join(DEFAULT_FEATURES),
                is_active=True,
            )
            db.add(config)
            await db.commit()
            await db.refresh(config)
        return config

    @staticmethod
    async def has_active_entitlement(
        db: AsyncSession,
        user: User,
        scan_id: str,
    ) -> bool:
        """Admins always have entitlement; clients must hold an active ReportEntitlement."""
        if user.is_admin():
            return True

        stmt = (
            select(ReportEntitlement)
            .where(
                ReportEntitlement.scan_id == scan_id,
                ReportEntitlement.user_id == user.id,
                ReportEntitlement.is_active == True,
            )
        )
        res = await db.execute(stmt)
        ent = res.scalar_one_or_none()
        if not ent:
            return False

        if ent.expires_at and ent.expires_at < datetime.now(timezone.utc):
            return False

        return True

    @staticmethod
    async def get_entitlement_for_scan(
        db: AsyncSession,
        user: User,
        scan_id: str,
    ) -> Optional[ReportEntitlement]:
        stmt = select(ReportEntitlement).where(
            ReportEntitlement.scan_id == scan_id,
            ReportEntitlement.user_id == user.id,
            ReportEntitlement.is_active == True,
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def record_access(
        db: AsyncSession,
        user_id: str,
        scan_id: str,
        access_type: str = "web_view",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        log = ReportAccessLog(
            scan_id=scan_id,
            user_id=user_id,
            access_type=access_type,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(log)

        # Increment access count on entitlement
        stmt = select(ReportEntitlement).where(ReportEntitlement.scan_id == scan_id)
        res = await db.execute(stmt)
        ent = res.scalar_one_or_none()
        if ent:
            ent.access_count += 1
            ent.last_accessed_at = datetime.now(timezone.utc)

        await db.commit()

    @staticmethod
    async def generate_or_get_report_document(
        db: AsyncSession,
        scan: Scan,
    ) -> ReportDocument:
        """Build or retrieve cached report document."""
        stmt = (
            select(ReportDocument)
            .where(ReportDocument.scan_id == scan.id)
        )
        res = await db.execute(stmt)
        doc = res.scalar_one_or_none()
        if doc:
            return doc

        # Calculate risk score & posture
        findings_stmt = select(ScanFinding).where(ScanFinding.scan_id == scan.id)
        f_res = await db.execute(findings_stmt)
        findings = f_res.scalars().all()

        score = (
            (scan.critical_count * 3.0)
            + (scan.high_count * 2.0)
            + (scan.medium_count * 1.0)
            + (scan.low_count * 0.3)
        )
        overall_risk_score = min(round(score, 1), 10.0)

        if overall_risk_score >= 8.0:
            overall_posture = "CRITICAL RISK (IMMEDIATE REMEDIATION REQUIRED)"
        elif overall_risk_score >= 5.0:
            overall_posture = "ELEVATED RISK"
        elif overall_risk_score >= 2.0:
            overall_posture = "MODERATE RISK"
        elif overall_risk_score > 0.0:
            overall_posture = "LOW RISK"
        else:
            overall_posture = "HARDENED POSTURE"

        has_php2shell = any(
            f.category == "PHP2Shell Protection" or "109618" in (f.cwe_id or "") or "PHP2Shell" in f.title
            for f in findings
        )

        php2shell_posture = (
            "CRITICAL: Unhandled Memory Fault Exposure (CVE-2026-109618 / 19)"
            if has_php2shell
            else "PROTECTED: Zero-Day Error Handling Defense Verified"
        )

        title = f"Vulnerability Assessment & Security Audit — {scan.target_domain}"

        exec_summary = (
            f"This comprehensive vulnerability assessment was conducted for target {scan.target_domain} "
            f"under assessment profile '{scan.profile}'. A total of {len(findings)} security findings were identified "
            f"yielding an overall risk score of {overall_risk_score}/10.0 ({overall_posture}). "
            f"Vulnerability distribution consists of {scan.critical_count} critical, {scan.high_count} high, "
            f"{scan.medium_count} medium, {scan.low_count} low, and {scan.info_count} informational issues. "
            f"Zero-day posture for PHP2Shell (CVE-2026-109618 & CVE-2026-109619) was evaluated as: {php2shell_posture}."
        )

        html_content = ReportService._build_html_report(
            scan=scan,
            findings=findings,
            overall_risk_score=overall_risk_score,
            overall_posture=overall_posture,
            has_php2shell=has_php2shell,
            php2shell_posture=php2shell_posture,
            exec_summary=exec_summary,
        )

        doc = ReportDocument(
            scan_id=scan.id,
            website_id=scan.website_id,
            title=title,
            executive_summary=exec_summary,
            overall_risk_score=overall_risk_score,
            overall_posture=overall_posture,
            has_php2shell_finding=has_php2shell,
            php2shell_posture=php2shell_posture,
            html_content=html_content,
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        return doc

    @staticmethod
    def _build_html_report(
        scan: Scan,
        findings: List[ScanFinding],
        overall_risk_score: float,
        overall_posture: str,
        has_php2shell: bool,
        php2shell_posture: str,
        exec_summary: str,
    ) -> str:
        findings_html = ""
        for i, f in enumerate(findings, 1):
            sev_color = {
                "critical": "#dc2626",
                "high": "#ea580c",
                "medium": "#d97706",
                "low": "#2563eb",
                "info": "#475569",
            }.get(f.severity.lower(), "#475569")

            # XSS defense: HTML-escape all user-controlled / target-derived finding strings
            f_title = html.escape(f.title, quote=True)
            f_severity = html.escape(f.severity, quote=True)
            f_category = html.escape(f.category, quote=True)
            f_cwe = html.escape(f.cwe_id or "N/A", quote=True)
            f_cvss = html.escape(str(f.cvss_score) if f.cvss_score is not None else "N/A", quote=True)
            f_desc = html.escape(f.description, quote=True)
            f_evidence = html.escape(f.evidence, quote=True)
            f_remediation = html.escape(f.remediation, quote=True).replace("\n", "<br/>")

            findings_html += f"""
            <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin-bottom: 20px; page-break-inside: avoid;">
                <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 10px;">
                    <h3 style="margin: 0; color: #0f172a; font-size: 16px;">#{i}. {f_title}</h3>
                    <span style="background-color: {sev_color}; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; text-transform: uppercase;">
                        {f_severity}
                    </span>
                </div>
                <div style="color: #64748b; font-size: 12px; margin-bottom: 12px; font-family: monospace;">
                    Category: {f_category} | CWE: {f_cwe} | CVSS: {f_cvss}
                </div>
                <div style="margin-bottom: 14px; font-size: 13px; color: #334155; line-height: 1.5;">
                    <strong>Description:</strong> {f_desc}
                </div>
                <div style="margin-bottom: 14px;">
                    <strong style="font-size: 12px; color: #0f172a;">Stored Proof & Evidence:</strong>
                    <pre style="background: #0f172a; color: #34d399; padding: 12px; border-radius: 6px; font-family: monospace; font-size: 11px; overflow-x: auto; white-space: pre-wrap; margin-top: 6px;">{f_evidence}</pre>
                </div>
                <div style="background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 6px; padding: 12px; font-size: 12px; color: #065f46;">
                    <strong>Remediation Guidance:</strong><br/>
                    {f_remediation}
                </div>
            </div>
            """

        safe_target_domain = html.escape(scan.target_domain, quote=True)
        safe_scan_id = html.escape(scan.id[:12], quote=True)
        safe_exec_summary = html.escape(exec_summary, quote=True)
        safe_php2shell_posture = html.escape(php2shell_posture, quote=True)

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; font-src 'none'; img-src data:; script-src 'none'; frame-ancestors 'none';">
    <meta http-equiv="X-Content-Type-Options" content="nosniff">
    <title>PATCHORA Security Report — {safe_target_domain}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; color: #0f172a; line-height: 1.6; margin: 0; padding: 40px; }}
        .header {{ border-bottom: 3px solid #0f172a; padding-bottom: 20px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: flex-end; }}
        .badge {{ font-size: 12px; font-weight: bold; padding: 6px 12px; border-radius: 4px; }}
        .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 30px; }}
        .card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; text-align: center; }}
        .card-num {{ font-size: 24px; font-weight: bold; margin-top: 5px; }}
        .section-title {{ font-size: 18px; font-weight: bold; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; margin-top: 30px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <div style="font-weight: 800; font-size: 24px; color: #0f172a; letter-spacing: -0.5px;">PATCHORA</div>
            <div style="color: #64748b; font-size: 13px;">Official Vulnerability Assessment & Technical Remediation Report</div>
        </div>
        <div style="text-align: right; font-size: 12px; color: #64748b;">
            <div>Target: <strong>{safe_target_domain}</strong></div>
            <div>Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</div>
            <div>Scan ID: {safe_scan_id}</div>
        </div>
    </div>

    <div class="section-title">Executive Risk Overview</div>
    <div style="background: #f1f5f9; border-left: 4px solid #6366f1; padding: 16px; border-radius: 0 8px 8px 0; font-size: 14px; margin-bottom: 25px;">
        {safe_exec_summary}
    </div>

    <div class="grid">
        <div class="card">
            <div style="font-size: 11px; color: #64748b; text-transform: uppercase;">Overall Risk Score</div>
            <div class="card-num" style="color: #dc2626;">{overall_risk_score} / 10</div>
        </div>
        <div class="card">
            <div style="font-size: 11px; color: #64748b; text-transform: uppercase;">Critical Findings</div>
            <div class="card-num" style="color: #dc2626;">{scan.critical_count}</div>
        </div>
        <div class="card">
            <div style="font-size: 11px; color: #64748b; text-transform: uppercase;">High Findings</div>
            <div class="card-num" style="color: #ea580c;">{scan.high_count}</div>
        </div>
        <div class="card">
            <div style="font-size: 11px; color: #64748b; text-transform: uppercase;">Total Findings</div>
            <div class="card-num" style="color: #0f172a;">{len(findings)}</div>
        </div>
    </div>

    <div style="background: #faf5ff; border: 1px solid #d8b4fe; border-radius: 8px; padding: 15px; margin-bottom: 30px; font-size: 13px;">
        <strong style="color: #6b21a8;">PHP2Shell Zero-Day Posture (CVE-2026-109618 / 19):</strong>
        <div style="color: #581c87; margin-top: 4px;">{safe_php2shell_posture}</div>
    </div>

    <div class="section-title">Detailed Vulnerability Findings & Proofs</div>
    {findings_html if findings else '<div style="color: #64748b; font-style: italic;">No vulnerabilities were discovered. Target environment is hardened.</div>'}

    <div style="margin-top: 50px; border-top: 1px solid #e2e8f0; padding-top: 20px; font-size: 11px; color: #94a3b8; text-align: center;">
        PATCHORA — Confidential Assessment Report. Generated under explicit authorization.
    </div>
</body>
</html>"""
        return html_content
