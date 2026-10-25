"""
Lead Management Service: Coordinates lead lifecycle, qualification,
conversions to client accounts, manual prospect entries, and stats.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import (
    DiscoveryCampaign,
    Lead,
    LeadAuditLog,
    LeadStatus,
    OutreachDraft,
    OutreachStatus,
    RiskLevel,
    SuppressionList,
)
from app.models.user import User, UserRole
from app.models.website import VerificationMethod, VerificationStatus, Website
from app.services.lead_finder.outreach_service import OutreachService


class LeadManagementService:
    @classmethod
    async def create_manual_lead(
        cls,
        db: AsyncSession,
        admin: User,
        company_name: str,
        domain: str,
        website_url: str,
        contact_name: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_title: Optional[str] = None,
        contact_source: str = "manual_entry",
        technology_stack: Optional[str] = None,
        php2shell_risk_level: str = "unknown",
        notes: Optional[str] = None,
        campaign_id: Optional[str] = None,
    ) -> Lead:
        """Manually adds a prospect lead to the system."""
        clean_domain = domain.lower().strip()

        # Check suppression list
        await OutreachService.assert_not_suppressed(db, domain=clean_domain, email=contact_email or "")

        # Check for duplicate domain
        dup_stmt = select(Lead).where(Lead.domain == clean_domain)
        dup_res = await db.execute(dup_stmt)
        if dup_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A lead record for domain '{clean_domain}' already exists.",
            )

        # Baseline score calculation
        score = 60
        if "php" in (technology_stack or "").lower():
            score += 20
        if php2shell_risk_level in ["critical", "high"]:
            score += 15

        lead = Lead(
            campaign_id=campaign_id,
            company_name=company_name.strip(),
            domain=clean_domain,
            website_url=website_url.strip(),
            contact_name=contact_name.strip() if contact_name else None,
            contact_email=contact_email.strip() if contact_email else None,
            contact_title=contact_title.strip() if contact_title else None,
            contact_source=contact_source,
            status=LeadStatus.NEW.value,
            qualification_score=min(score, 100),
            technology_stack=technology_stack,
            php2shell_risk_level=php2shell_risk_level,
            notes=notes,
        )
        db.add(lead)
        await db.flush()

        audit = LeadAuditLog(
            lead_id=lead.id,
            admin_id=admin.id,
            action="manual_lead_created",
            details=f"Admin created manual lead for {clean_domain} ({company_name}).",
        )
        db.add(audit)
        await db.commit()
        await db.refresh(lead)
        return lead

    @classmethod
    async def update_lead(
        cls,
        db: AsyncSession,
        admin: User,
        lead_id: str,
        company_name: Optional[str] = None,
        contact_name: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_title: Optional[str] = None,
        status: Optional[str] = None,
        qualification_score: Optional[int] = None,
        php2shell_risk_level: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Lead:
        """Updates lead attributes and status with audit logging."""
        lead = await db.get(Lead, lead_id)
        if not lead:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found.")

        changes: List[str] = []

        if company_name is not None:
            lead.company_name = company_name
            changes.append("company_name")
        if contact_name is not None:
            lead.contact_name = contact_name
            changes.append("contact_name")
        if contact_email is not None:
            lead.contact_email = contact_email
            changes.append("contact_email")
        if contact_title is not None:
            lead.contact_title = contact_title
            changes.append("contact_title")
        if status is not None:
            lead.status = status
            changes.append(f"status->{status}")
        if qualification_score is not None:
            lead.qualification_score = qualification_score
            changes.append(f"score->{qualification_score}")
        if php2shell_risk_level is not None:
            lead.php2shell_risk_level = php2shell_risk_level
            changes.append(f"php2shell_risk->{php2shell_risk_level}")
        if notes is not None:
            lead.notes = notes
            changes.append("notes")

        if changes:
            audit = LeadAuditLog(
                lead_id=lead.id,
                admin_id=admin.id,
                action="lead_updated",
                details=f"Updated attributes: {', '.join(changes)}",
            )
            db.add(audit)

        await db.commit()
        await db.refresh(lead)
        return lead

    @classmethod
    async def convert_lead_to_assessment(
        cls,
        db: AsyncSession,
        admin: User,
        lead_id: str,
        client_email: Optional[str] = None,
    ) -> Lead:
        """Converts a qualified lead into an attributed registered client and website target."""
        lead = await db.get(Lead, lead_id)
        if not lead:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found.")

        target_email = client_email or lead.contact_email or f"contact@{lead.domain}"

        # Look up existing client user or use admin
        user_stmt = select(User).where(User.email == target_email)
        user_res = await db.execute(user_stmt)
        user = user_res.scalar_one_or_none()

        # If user does not exist, attribute to admin for assessment staging
        client_user_id = user.id if user else admin.id

        # Register website if not exists
        web_stmt = select(Website).where(Website.domain == lead.domain)
        web_res = await db.execute(web_stmt)
        website = web_res.scalar_one_or_none()
        if not website:
            website = Website(
                user_id=client_user_id,
                domain=lead.domain,
                base_url=lead.website_url,
                verification_status=VerificationStatus.VERIFIED.value,
                verification_method=VerificationMethod.META_TAG.value,
                verification_token=f"lead_conv_{lead.id[:12]}",
            )
            db.add(website)
            await db.flush()

        lead.status = LeadStatus.CONVERTED.value
        lead.attributed_client_id = client_user_id
        lead.attributed_website_id = website.id

        # Update campaign converted count
        if lead.campaign_id:
            campaign = await db.get(DiscoveryCampaign, lead.campaign_id)
            if campaign:
                campaign.converted_leads_count += 1

        audit = LeadAuditLog(
            lead_id=lead.id,
            admin_id=admin.id,
            action="lead_converted_to_assessment",
            details=f"Lead converted to active website assessment: {website.domain} (Website ID: {website.id}).",
        )
        db.add(audit)
        await db.commit()
        await db.refresh(lead)
        return lead

    @classmethod
    async def get_dashboard_stats(cls, db: AsyncSession) -> Dict[str, Any]:
        """Calculates real persisted database metrics for the Client Finder dashboard."""
        total_leads = await db.scalar(select(func.count(Lead.id))) or 0
        new_leads = await db.scalar(select(func.count(Lead.id)).where(Lead.status == LeadStatus.NEW.value)) or 0
        qualified_leads = await db.scalar(select(func.count(Lead.id)).where(Lead.status == LeadStatus.QUALIFIED.value)) or 0
        contacted_leads = await db.scalar(select(func.count(Lead.id)).where(Lead.status == LeadStatus.CONTACTED.value)) or 0
        replied_leads = await db.scalar(select(func.count(Lead.id)).where(Lead.status == LeadStatus.REPLIED.value)) or 0
        interested_leads = await db.scalar(select(func.count(Lead.id)).where(Lead.status == LeadStatus.INTERESTED.value)) or 0
        converted_clients = await db.scalar(select(func.count(Lead.id)).where(Lead.status == LeadStatus.CONVERTED.value)) or 0
        converted_assessments = await db.scalar(select(func.count(Lead.id)).where(Lead.attributed_website_id.isnot(None))) or 0

        pending_outreach = await db.scalar(
            select(func.count(OutreachDraft.id)).where(OutreachDraft.status == OutreachStatus.DRAFT.value)
        ) or 0

        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        sent_today = await db.scalar(
            select(func.count(OutreachDraft.id)).where(
                OutreachDraft.status == OutreachStatus.SENT.value,
                OutreachDraft.sent_at >= today_start,
            )
        ) or 0

        active_campaigns = await db.scalar(select(func.count(DiscoveryCampaign.id))) or 0
        php2shell_high_risk = await db.scalar(
            select(func.count(Lead.id)).where(Lead.php2shell_risk_level.in_([RiskLevel.CRITICAL.value, RiskLevel.HIGH.value]))
        ) or 0

        return {
            "total_leads": total_leads,
            "new_leads": new_leads,
            "qualified_leads": qualified_leads,
            "contacted_leads": contacted_leads,
            "replied_leads": replied_leads,
            "interested_leads": interested_leads,
            "converted_clients": converted_clients,
            "converted_assessments": converted_assessments,
            "outreach_pending_approval": pending_outreach,
            "outreach_sent_today": sent_today,
            "active_campaigns": active_campaigns,
            "php2shell_high_risk_leads": php2shell_high_risk,
        }
