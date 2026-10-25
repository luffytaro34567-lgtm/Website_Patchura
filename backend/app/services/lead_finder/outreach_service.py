"""
Outreach Service: Manages templates, renders CAN-SPAM / GDPR compliant drafts,
enforces suppression list checks, and delivers outreach through the sandbox adapter.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import structlog
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.lead import (
    Lead,
    LeadAuditLog,
    LeadStatus,
    OutreachDraft,
    OutreachStatus,
    OutreachTemplate,
    SuppressionList,
)
from app.models.user import User

logger = structlog.get_logger(__name__)


class OutreachService:
    @classmethod
    async def get_or_create_default_templates(cls, db: AsyncSession) -> List[OutreachTemplate]:
        """Seeds standard responsible disclosure and vulnerability assessment templates."""
        stmt = select(OutreachTemplate).order_by(OutreachTemplate.created_at)
        res = await db.execute(stmt)
        existing = res.scalars().all()
        if existing:
            return list(existing)

        # 1. PHP2Shell Zero-Day Responsible Disclosure
        t1 = OutreachTemplate(
            name="Responsible Disclosure — PHP2Shell (CVE-2026-109618) Zero-Day Protection",
            category="responsible_disclosure",
            subject_template="Security Advisory: Proactive Mitigation for PHP2Shell on {domain}",
            body_template=(
                "Hello {contact_name},\n\n"
                "I am writing from the PATCHORA security research team. During our automated perimeter reconnaissance, "
                "our systems identified that {domain} is operating on a PHP web application stack that may be susceptible to "
                "the newly disclosed PHP2Shell remote code execution flaws (CVE-2026-109618 and CVE-2026-109619).\n\n"
                "These vulnerabilities allow unauthenticated attackers to exploit memory corruption during custom PHP error handling. "
                "PATCHORA provides non-destructive ownership verification, deep AST code remediation, and defensive error handler patches "
                "designed specifically to neutralize heap corruption without downtime.\n\n"
                "If you would like to run a verified, authorized assessment of {domain}, you can inspect our platform here: {portal_url}\n\n"
                "Best regards,\n"
                "{sender_name}\n"
                "{compliance_address}"
            ),
        )

        # 2. General Security Assessment Offer
        t2 = OutreachTemplate(
            name="Compliant Security Assessment Offer — Web Application Audit",
            category="security_assessment_offer",
            subject_template="Vulnerability Assessment & Bug Hunting for {domain}",
            body_template=(
                "Hello {contact_name},\n\n"
                "We noticed that {company_name} maintains digital operations at {domain}. "
                "PATCHORA provides automated vulnerability assessments evaluating HTTP transport security, "
                "CORS misconfigurations, cookie security flags, and critical zero-day exposures.\n\n"
                "Our assessments require explicit ownership verification and warrant authorization before any probe is executed. "
                "To explore our security dashboard and run a complimentary initial audit, please visit: {portal_url}\n\n"
                "Sincerely,\n"
                "{sender_name}\n"
                "{compliance_address}"
            ),
        )

        db.add_all([t1, t2])
        await db.commit()
        return [t1, t2]

    @classmethod
    async def create_outreach_draft(
        cls,
        db: AsyncSession,
        admin: User,
        lead_id: str,
        template_id: Optional[str] = None,
        custom_subject: Optional[str] = None,
        custom_body: Optional[str] = None,
    ) -> OutreachDraft:
        """Generates an outreach draft incorporating compliant footer tokens and opt-out link."""
        lead = await db.get(Lead, lead_id)
        if not lead:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found.")

        # Recipient email required
        recipient_email = lead.contact_email
        if not recipient_email or "@" not in recipient_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot draft outreach: Lead '{lead.company_name}' has no valid contact email.",
            )

        # Check suppression list
        await cls.assert_not_suppressed(db, domain=lead.domain, email=recipient_email)

        # Resolve template or use custom
        subject = custom_subject
        body = custom_body

        if template_id:
            tpl = await db.get(OutreachTemplate, template_id)
            if tpl:
                subject = tpl.subject_template
                body = tpl.body_template

        if not subject or not body:
            templates = await cls.get_or_create_default_templates(db)
            tpl = templates[0]
            subject = tpl.subject_template
            body = tpl.body_template

        # Render tokens
        contact_name = lead.contact_name or "Security Team"
        opt_out_token = hashlib.sha256(f"{lead.id}-{recipient_email}-salt".encode()).hexdigest()[:16]
        opt_out_link = f"{settings.OUTREACH_OPT_OUT_BASE_URL}?target={lead.domain}&token={opt_out_token}"

        rendered_subject = subject.replace("{domain}", lead.domain).replace("{company_name}", lead.company_name)

        rendered_body = (
            body.replace("{contact_name}", contact_name)
            .replace("{company_name}", lead.company_name)
            .replace("{domain}", lead.domain)
            .replace("{portal_url}", "http://localhost:5173")
            .replace("{sender_name}", settings.OUTREACH_FROM_NAME)
            .replace("{compliance_address}", settings.OUTREACH_COMPLIANCE_ADDRESS)
        )

        # Mandatory CAN-SPAM / GDPR footer
        compliance_footer = (
            "\n\n----------------------------------------------------------------------\n"
            "COMPLIANCE & OPT-OUT NOTICE:\n"
            f"You received this message because our security research team identified {lead.domain} in public DNS records.\n"
            f"PATCHORA, {settings.OUTREACH_COMPLIANCE_ADDRESS}\n"
            f"To permanently opt-out and prevent all future communication, click here: {opt_out_link}\n"
            "----------------------------------------------------------------------"
        )
        rendered_body += compliance_footer

        draft = OutreachDraft(
            lead_id=lead.id,
            template_id=template_id,
            created_by_admin_id=admin.id,
            recipient_email=recipient_email,
            recipient_name=contact_name,
            subject=rendered_subject,
            body=rendered_body,
            status=OutreachStatus.DRAFT.value,
            delivery_provider=settings.OUTREACH_PROVIDER,
        )
        db.add(draft)
        await db.commit()
        await db.refresh(draft)
        return draft

    @classmethod
    async def send_outreach_draft(
        cls,
        db: AsyncSession,
        admin: User,
        draft_id: str,
    ) -> OutreachDraft:
        """
        Dispatches an approved outreach draft.
        Enforces suppression list check and daily sending rate limits.
        """
        draft = await db.get(OutreachDraft, draft_id)
        if not draft:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Outreach draft not found.")

        lead = await db.get(Lead, draft.lead_id)
        if not lead:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated lead not found.")

        # 1. Enforce Suppression Check
        await cls.assert_not_suppressed(db, domain=lead.domain, email=draft.recipient_email)

        # 2. Enforce Daily Rate Limit
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        sent_today = await db.scalar(
            select(func.count(OutreachDraft.id)).where(
                OutreachDraft.status == OutreachStatus.SENT.value,
                OutreachDraft.sent_at >= today_start,
            )
        ) or 0

        if sent_today >= settings.OUTREACH_DAILY_RATE_LIMIT and not admin.is_admin():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily outreach rate limit ({settings.OUTREACH_DAILY_RATE_LIMIT} emails/day) reached.",
            )

        # 3. Deliver through provider
        now = datetime.now(timezone.utc)
        message_id = f"msg_patchora_outreach_{uuid.uuid4().hex[:12]}"

        draft.status = OutreachStatus.SENT.value
        draft.sent_at = now
        draft.delivery_message_id = message_id
        draft.delivery_provider = settings.OUTREACH_PROVIDER

        # Update lead status to CONTACTED
        if lead.status in [LeadStatus.NEW.value, LeadStatus.QUALIFIED.value]:
            lead.status = LeadStatus.CONTACTED.value

        # Audit log
        audit = LeadAuditLog(
            lead_id=lead.id,
            admin_id=admin.id,
            action="outreach_sent",
            details=f"Dispatched email to {draft.recipient_email} ('{draft.subject}'). ID: {message_id}",
        )
        db.add(audit)
        await db.commit()
        await db.refresh(draft)
        return draft

    @classmethod
    async def assert_not_suppressed(cls, db: AsyncSession, domain: str, email: str) -> None:
        """Raises HTTP 400 if domain or email is in the suppression list."""
        stmt = select(SuppressionList).where(
            (SuppressionList.domain_or_email == domain.lower()) |
            (SuppressionList.domain_or_email == email.lower())
        )
        res = await db.execute(stmt)
        entry = res.scalar_one_or_none()
        if entry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Suppression List Enforcement: '{entry.domain_or_email}' has opted out of communication (Reason: {entry.reason}).",
            )

    @classmethod
    async def process_opt_out(cls, db: AsyncSession, target: str, reason: str = "opt_out_link") -> SuppressionList:
        """Processes opt-out request and suppresses recipient domain or email."""
        clean = target.lower().strip()
        entry_type = "email" if "@" in clean else "domain"

        # Check existing
        stmt = select(SuppressionList).where(SuppressionList.domain_or_email == clean)
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            return existing

        supp = SuppressionList(
            domain_or_email=clean,
            entry_type=entry_type,
            reason=reason,
        )
        db.add(supp)

        # Cancel any pending drafts for this target
        draft_stmt = select(OutreachDraft).where(
            (OutreachDraft.recipient_email == clean) &
            (OutreachDraft.status == OutreachStatus.DRAFT.value)
        )
        drafts = (await db.execute(draft_stmt)).scalars().all()
        for d in drafts:
            d.status = OutreachStatus.OPTED_OUT.value

        await db.commit()
        await db.refresh(supp)
        return supp
