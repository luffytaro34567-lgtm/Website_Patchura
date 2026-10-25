export type LeadStatus =
  | 'new'
  | 'qualified'
  | 'contacted'
  | 'replied'
  | 'interested'
  | 'converted'
  | 'rejected'
  | 'archived'

export type CampaignStatus = 'active' | 'paused' | 'completed' | 'cancelled'

export type OutreachStatus =
  | 'draft'
  | 'approved_pending_send'
  | 'sent'
  | 'failed'
  | 'bounced'
  | 'opted_out'

export type RiskLevel = 'critical' | 'high' | 'moderate' | 'low' | 'unknown'

export interface Lead {
  id: string
  campaign_id?: string | null
  company_name: string
  domain: string
  website_url: string
  contact_name?: string | null
  contact_email?: string | null
  contact_title?: string | null
  contact_source: string
  status: LeadStatus
  qualification_score: number
  technology_stack?: string | null
  php2shell_risk_level: RiskLevel
  notes?: string | null
  attributed_client_id?: string | null
  attributed_website_id?: string | null
  created_at: string
  updated_at: string
}

export interface DiscoveryCampaign {
  id: string
  created_by_admin_id: string
  name: string
  target_technology: string
  target_industry?: string | null
  search_query: string
  status: CampaignStatus
  rate_limit_per_day: number
  discovered_leads_count: number
  contacted_leads_count: number
  converted_leads_count: number
  created_at: string
  updated_at: string
}

export interface OutreachTemplate {
  id: string
  name: string
  category: string
  subject_template: string
  body_template: string
  is_approved_by_admin: boolean
  created_at: string
  updated_at: string
}

export interface OutreachDraft {
  id: string
  lead_id: string
  template_id?: string | null
  recipient_email: string
  recipient_name: string
  subject: string
  body: string
  status: OutreachStatus
  sent_at?: string | null
  delivery_provider: string
  delivery_message_id?: string | null
  error_message?: string | null
  created_at: string
}

export interface SuppressionEntry {
  id: string
  domain_or_email: string
  entry_type: 'email' | 'domain'
  reason: string
  opted_out_at: string
}

export interface ClientFinderStats {
  total_leads: number
  new_leads: number
  qualified_leads: number
  contacted_leads: number
  replied_leads: number
  interested_leads: number
  converted_clients: number
  converted_assessments: number
  outreach_pending_approval: number
  outreach_sent_today: number
  active_campaigns: number
  php2shell_high_risk_leads: number
}

export interface CreateLeadRequest {
  company_name: string
  domain: string
  website_url: string
  contact_name?: string
  contact_email?: string
  contact_title?: string
  contact_source?: string
  technology_stack?: string
  php2shell_risk_level?: string
  notes?: string
  campaign_id?: string
}

export interface CreateCampaignRequest {
  name: string
  target_technology?: string
  target_industry?: string
  search_query: string
  rate_limit_per_day?: number
}
