"""
FastAPI router for Client Finder Automation, Lead Management,
Campaign Discovery, Compliant Outreach, and Suppression Enforcement.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.lead import (
    DiscoveryCampaign,
    Lead,
    LeadStatus,
    OutreachDraft,
    OutreachTemplate,
    SuppressionList,
)
from app.models.user import User
from app.schemas.lead import (
    AddSuppressionRequest,
    CampaignResponse,
    ClientFinderStatsResponse,
    ConvertLeadRequest,
    CreateCampaignRequest,
    CreateLeadRequest,
    CreateTemplateRequest,
    DraftOutreachRequest,
    LeadResponse,
    OutreachDraftResponse,
    PublicOptOutRequest,
    SuppressionResponse,
    TemplateResponse,
    UpdateLeadRequest,
)
from app.security.dependencies import get_current_user, require_admin
from app.security.rate_limiter import RateLimit
from app.security.sql_sanitizer import sanitize_search_query
from app.services.lead_finder.lead_discovery_engine import LeadDiscoveryEngine
from app.services.lead_finder.lead_management_service import LeadManagementService
from app.services.lead_finder.outreach_service import OutreachService

router = APIRouter(prefix="/leads", tags=["Client Finder Automation & Leads"])


# ──────────────────────────────────────────────────────────────────────────────
# Admin Only: Metrics & Dashboard Overview
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/stats",
    response_model=ClientFinderStatsResponse,
    summary="Get real database metrics for Client Finder dashboard",
    dependencies=[Depends(require_admin)],
)
async def get_client_finder_stats(
    db: AsyncSession = Depends(get_db),
) -> ClientFinderStatsResponse:
    stats_data = await LeadManagementService.get_dashboard_stats(db)
    return ClientFinderStatsResponse(**stats_data)


# ──────────────────────────────────────────────────────────────────────────────
# Admin Only: Lead Management CRUD
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=List[LeadResponse],
    summary="List and filter prospective client leads",
    dependencies=[Depends(require_admin)],
)
async def list_leads(
    status: Optional[str] = Query(None),
    php2shell_risk: Optional[str] = Query(None),
    campaign_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> List[LeadResponse]:
    stmt = select(Lead)
    if status:
        stmt = stmt.where(Lead.status == status)
    if php2shell_risk:
        stmt = stmt.where(Lead.php2shell_risk_level == php2shell_risk)
    if campaign_id:
        stmt = stmt.where(Lead.campaign_id == campaign_id)
    if search:
        term = f"%{sanitize_search_query(search).lower()}%"
        stmt = stmt.where(
            (func.lower(Lead.company_name).like(term)) |
            (func.lower(Lead.domain).like(term)) |
            (func.lower(Lead.contact_name).like(term))
        )
    stmt = stmt.order_by(desc(Lead.created_at)).limit(limit).offset(offset)

    res = await db.execute(stmt)
    leads = res.scalars().all()
    return [LeadResponse.model_validate(l) for l in leads]


@router.post(
    "",
    response_model=LeadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Manually create a prospective lead",
    dependencies=[Depends(require_admin)],
)
async def create_manual_lead(
    payload: CreateLeadRequest,
    current_admin: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LeadResponse:
    lead = await LeadManagementService.create_manual_lead(
        db=db,
        admin=current_admin,
        company_name=payload.company_name,
        domain=payload.domain,
        website_url=payload.website_url,
        contact_name=payload.contact_name,
        contact_email=payload.contact_email,
        contact_title=payload.contact_title,
        contact_source=payload.contact_source,
        technology_stack=payload.technology_stack,
        php2shell_risk_level=payload.php2shell_risk_level,
        notes=payload.notes,
        campaign_id=payload.campaign_id,
    )
    return LeadResponse.model_validate(lead)


@router.get(
    "/{lead_id}",
    response_model=LeadResponse,
    summary="Get detailed prospective lead profile",
    dependencies=[Depends(require_admin)],
)
async def get_lead_details(
    lead_id: str,
    db: AsyncSession = Depends(get_db),
) -> LeadResponse:
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found.")
    return LeadResponse.model_validate(lead)


@router.patch(
    "/{lead_id}",
    response_model=LeadResponse,
    summary="Update lead qualification status, notes, or score",
    dependencies=[Depends(require_admin)],
)
async def update_lead(
    lead_id: str,
    payload: UpdateLeadRequest,
    current_admin: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LeadResponse:
    lead = await LeadManagementService.update_lead(
        db=db,
        admin=current_admin,
        lead_id=lead_id,
        company_name=payload.company_name,
        contact_name=payload.contact_name,
        contact_email=payload.contact_email,
        contact_title=payload.contact_title,
        status=payload.status,
        qualification_score=payload.qualification_score,
        php2shell_risk_level=payload.php2shell_risk_level,
        notes=payload.notes,
    )
    return LeadResponse.model_validate(lead)


@router.post(
    "/{lead_id}/convert",
    response_model=LeadResponse,
    summary="Convert lead into registered client and target website assessment",
    dependencies=[Depends(require_admin)],
)
async def convert_lead(
    lead_id: str,
    payload: ConvertLeadRequest,
    current_admin: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LeadResponse:
    lead = await LeadManagementService.convert_lead_to_assessment(
        db=db,
        admin=current_admin,
        lead_id=lead_id,
        client_email=payload.user_email,
    )
    return LeadResponse.model_validate(lead)


# ──────────────────────────────────────────────────────────────────────────────
# Admin Only: Discovery Campaigns
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/campaigns/list",
    response_model=List[CampaignResponse],
    summary="List lead discovery campaigns",
    dependencies=[Depends(require_admin)],
)
async def list_campaigns(
    db: AsyncSession = Depends(get_db),
) -> List[CampaignResponse]:
    stmt = select(DiscoveryCampaign).order_by(desc(DiscoveryCampaign.created_at))
    res = await db.execute(stmt)
    campaigns = res.scalars().all()
    return [CampaignResponse.model_validate(c) for c in campaigns]


@router.post(
    "/campaigns",
    response_model=CampaignResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new lead discovery campaign",
    dependencies=[Depends(require_admin)],
)
async def create_campaign(
    payload: CreateCampaignRequest,
    current_admin: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    camp = DiscoveryCampaign(
        created_by_admin_id=current_admin.id,
        name=payload.name,
        target_technology=payload.target_technology,
        target_industry=payload.target_industry,
        search_query=payload.search_query,
        rate_limit_per_day=payload.rate_limit_per_day,
    )
    db.add(camp)
    await db.commit()
    await db.refresh(camp)
    return CampaignResponse.model_validate(camp)


@router.post(
    "/campaigns/{campaign_id}/run",
    response_model=List[LeadResponse],
    summary="Run automated lead discovery job for a campaign",
    dependencies=[Depends(require_admin)],
)
async def run_campaign_discovery(
    campaign_id: str,
    current_admin: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[LeadResponse]:
    discovered = await LeadDiscoveryEngine.run_discovery_for_campaign(
        db=db,
        admin=current_admin,
        campaign_id=campaign_id,
    )
    return [LeadResponse.model_validate(l) for l in discovered]


# ──────────────────────────────────────────────────────────────────────────────
# Admin Only: Outreach Templates & Compliant Drafts
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/templates/list",
    response_model=List[TemplateResponse],
    summary="List outreach email templates",
    dependencies=[Depends(require_admin)],
)
async def list_templates(
    db: AsyncSession = Depends(get_db),
) -> List[TemplateResponse]:
    templates = await OutreachService.get_or_create_default_templates(db)
    return [TemplateResponse.model_validate(t) for t in templates]


@router.post(
    "/templates",
    response_model=TemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a custom outreach template",
    dependencies=[Depends(require_admin)],
)
async def create_template(
    payload: CreateTemplateRequest,
    db: AsyncSession = Depends(get_db),
) -> TemplateResponse:
    tpl = OutreachTemplate(
        name=payload.name,
        category=payload.category,
        subject_template=payload.subject_template,
        body_template=payload.body_template,
    )
    db.add(tpl)
    await db.commit()
    await db.refresh(tpl)
    return TemplateResponse.model_validate(tpl)


@router.post(
    "/{lead_id}/draft-outreach",
    response_model=OutreachDraftResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Draft a compliant outreach message for a lead",
    dependencies=[Depends(require_admin)],
)
async def draft_outreach(
    lead_id: str,
    payload: DraftOutreachRequest,
    current_admin: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OutreachDraftResponse:
    draft = await OutreachService.create_outreach_draft(
        db=db,
        admin=current_admin,
        lead_id=lead_id,
        template_id=payload.template_id,
        custom_subject=payload.custom_subject,
        custom_body=payload.custom_body,
    )
    return OutreachDraftResponse.model_validate(draft)


@router.post(
    "/outreach/{draft_id}/send",
    response_model=OutreachDraftResponse,
    summary="Approve and send outreach draft (Enforces suppression list and rate limits)",
    dependencies=[Depends(require_admin)],
)
async def send_outreach(
    draft_id: str,
    current_admin: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OutreachDraftResponse:
    sent = await OutreachService.send_outreach_draft(
        db=db,
        admin=current_admin,
        draft_id=draft_id,
    )
    return OutreachDraftResponse.model_validate(sent)


# ──────────────────────────────────────────────────────────────────────────────
# Admin Only: Suppression List Management
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/suppression/list",
    response_model=List[SuppressionResponse],
    summary="List suppressed domains and emails",
    dependencies=[Depends(require_admin)],
)
async def list_suppression(
    db: AsyncSession = Depends(get_db),
) -> List[SuppressionResponse]:
    stmt = select(SuppressionList).order_by(desc(SuppressionList.opted_out_at))
    res = await db.execute(stmt)
    entries = res.scalars().all()
    return [SuppressionResponse.model_validate(s) for s in entries]


@router.post(
    "/suppression",
    response_model=SuppressionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Manually add domain or email to suppression list",
    dependencies=[Depends(require_admin)],
)
async def add_suppression(
    payload: AddSuppressionRequest,
    db: AsyncSession = Depends(get_db),
) -> SuppressionResponse:
    entry = await OutreachService.process_opt_out(
        db=db,
        target=payload.domain_or_email,
        reason=payload.reason,
    )
    return SuppressionResponse.model_validate(entry)


# ──────────────────────────────────────────────────────────────────────────────
# Public Endpoint: One-Click Unsubscribe / Opt-Out
# ──────────────────────────────────────────────────────────────────────────────

@router.post(
    "/opt-out",
    response_model=SuppressionResponse,
    summary="Public one-click unsubscribe endpoint for outreach recipients",
    dependencies=[Depends(RateLimit(max_requests=20, window_seconds=60, scope="leads_optout"))],
)
async def public_opt_out(
    payload: PublicOptOutRequest,
    db: AsyncSession = Depends(get_db),
) -> SuppressionResponse:
    supp = await OutreachService.process_opt_out(
        db=db,
        target=payload.target,
        reason="public_opt_out_link",
    )
    return SuppressionResponse.model_validate(supp)
