import { apiClient } from './client'
import {
  ClientFinderStats,
  CreateCampaignRequest,
  CreateLeadRequest,
  DiscoveryCampaign,
  Lead,
  OutreachDraft,
  OutreachTemplate,
  SuppressionEntry,
} from '@/types/lead'

export async function getClientFinderStats(): Promise<ClientFinderStats> {
  const res = await apiClient.get<ClientFinderStats>('/api/leads/stats')
  return res.data
}

export async function listLeads(params?: {
  status?: string
  php2shell_risk?: string
  campaign_id?: string
  search?: string
  limit?: number
  offset?: number
}): Promise<Lead[]> {
  const res = await apiClient.get<Lead[]>('/api/leads', { params })
  return res.data
}

export async function createLead(payload: CreateLeadRequest): Promise<Lead> {
  const res = await apiClient.post<Lead>('/api/leads', payload)
  return res.data
}

export async function getLead(leadId: string): Promise<Lead> {
  const res = await apiClient.get<Lead>(`/api/leads/${leadId}`)
  return res.data
}

export async function updateLead(leadId: string, payload: Partial<Lead>): Promise<Lead> {
  const res = await apiClient.patch<Lead>(`/api/leads/${leadId}`, payload)
  return res.data
}

export async function convertLead(leadId: string, clientEmail?: string): Promise<Lead> {
  const res = await apiClient.post<Lead>(`/api/leads/${leadId}/convert`, {
    user_email: clientEmail,
  })
  return res.data
}

export async function listCampaigns(): Promise<DiscoveryCampaign[]> {
  const res = await apiClient.get<DiscoveryCampaign[]>('/api/leads/campaigns/list')
  return res.data
}

export async function createCampaign(payload: CreateCampaignRequest): Promise<DiscoveryCampaign> {
  const res = await apiClient.post<DiscoveryCampaign>('/api/leads/campaigns', payload)
  return res.data
}

export async function runCampaignDiscovery(campaignId: string): Promise<Lead[]> {
  const res = await apiClient.post<Lead[]>(`/api/leads/campaigns/${campaignId}/run`, {})
  return res.data
}

export async function listOutreachTemplates(): Promise<OutreachTemplate[]> {
  const res = await apiClient.get<OutreachTemplate[]>('/api/leads/templates/list')
  return res.data
}

export async function draftOutreach(
  leadId: string,
  payload: { template_id?: string; custom_subject?: string; custom_body?: string }
): Promise<OutreachDraft> {
  const res = await apiClient.post<OutreachDraft>(`/api/leads/${leadId}/draft-outreach`, payload)
  return res.data
}

export async function sendOutreach(draftId: string): Promise<OutreachDraft> {
  const res = await apiClient.post<OutreachDraft>(`/api/leads/outreach/${draftId}/send`, {})
  return res.data
}

export async function listSuppressionList(): Promise<SuppressionEntry[]> {
  const res = await apiClient.get<SuppressionEntry[]>('/api/leads/suppression/list')
  return res.data
}

export async function addSuppression(domainOrEmail: string, reason?: string): Promise<SuppressionEntry> {
  const res = await apiClient.post<SuppressionEntry>('/api/leads/suppression', {
    domain_or_email: domainOrEmail,
    reason: reason || 'manual_admin_suppression',
  })
  return res.data
}
