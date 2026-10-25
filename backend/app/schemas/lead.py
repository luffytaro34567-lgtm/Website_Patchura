"""Pydantic schemas for Client Finder Automation, Lead Management, and Compliant Outreach."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CreateLeadRequest(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=150)
    domain: str = Field(..., min_length=3, max_length=255)
    website_url: str = Field(..., min_length=4, max_length=500)
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_title: Optional[str] = None
    contact_source: str = Field(default="manual_entry")
    technology_stack: Optional[str] = None
    php2shell_risk_level: str = Field(default="unknown")
    notes: Optional[str] = None
    campaign_id: Optional[str] = None


class UpdateLeadRequest(BaseModel):
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_title: Optional[str] = None
    status: Optional[str] = None
    qualification_score: Optional[int] = Field(default=None, ge=0, le=100)
    php2shell_risk_level: Optional[str] = None
    notes: Optional[str] = None


class ConvertLeadRequest(BaseModel):
    user_email: Optional[str] = None
    create_invitation_token: bool = Field(default=True)


class LeadResponse(BaseModel):
    id: str
    campaign_id: Optional[str] = None
    company_name: str
    domain: str
    website_url: str
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_title: Optional[str] = None
    contact_source: str
    status: str
    qualification_score: int
    technology_stack: Optional[str] = None
    php2shell_risk_level: str
    notes: Optional[str] = None
    attributed_client_id: Optional[str] = None
    attributed_website_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CreateCampaignRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=150)
    target_technology: str = Field(default="PHP / Laravel / WordPress")
    target_industry: Optional[str] = None
    search_query: str = Field(..., min_length=3, max_length=255)
    rate_limit_per_day: int = Field(default=50, ge=1, le=500)


class CampaignResponse(BaseModel):
    id: str
    created_by_admin_id: str
    name: str
    target_technology: str
    target_industry: Optional[str] = None
    search_query: str
    status: str
    rate_limit_per_day: int
    discovered_leads_count: int
    contacted_leads_count: int
    converted_leads_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CreateTemplateRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=150)
    category: str = Field(default="responsible_disclosure")
    subject_template: str = Field(..., min_length=5, max_length=255)
    body_template: str = Field(..., min_length=20)


class TemplateResponse(BaseModel):
    id: str
    name: str
    category: str
    subject_template: str
    body_template: str
    is_approved_by_admin: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DraftOutreachRequest(BaseModel):
    template_id: Optional[str] = None
    custom_subject: Optional[str] = None
    custom_body: Optional[str] = None


class OutreachDraftResponse(BaseModel):
    id: str
    lead_id: str
    template_id: Optional[str] = None
    recipient_email: str
    recipient_name: str
    subject: str
    body: str
    status: str
    sent_at: Optional[datetime] = None
    delivery_provider: str
    delivery_message_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AddSuppressionRequest(BaseModel):
    domain_or_email: str = Field(..., min_length=3, max_length=255)
    reason: str = Field(default="manual_admin_suppression")


class SuppressionResponse(BaseModel):
    id: str
    domain_or_email: str
    entry_type: str
    reason: str
    opted_out_at: datetime

    model_config = {"from_attributes": True}


class PublicOptOutRequest(BaseModel):
    target: str = Field(..., min_length=3, max_length=255, description="Email or domain to unsubscribe")
    token: Optional[str] = None


class ClientFinderStatsResponse(BaseModel):
    total_leads: int
    new_leads: int
    qualified_leads: int
    contacted_leads: int
    replied_leads: int
    interested_leads: int
    converted_clients: int
    converted_assessments: int
    outreach_pending_approval: int
    outreach_sent_today: int
    active_campaigns: int
    php2shell_high_risk_leads: int
