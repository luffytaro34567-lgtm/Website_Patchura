import { apiClient } from './client'
import {
  ActivityLog,
  ActivitySummaryMetrics,
  BackgroundJobStatus,
  ClientProfileExtended,
  SecurityAlert,
} from '@/types/activity'
import { User } from '@/types/auth'

export async function fetchActivityMetrics(params?: {
  timeframe?: string
  from_date?: string
  to_date?: string
}): Promise<ActivitySummaryMetrics> {
  const res = await apiClient.get<ActivitySummaryMetrics>('/api/admin/activity/metrics', { params })
  return res.data
}

export async function fetchActivityTimeline(params?: {
  search?: string
  category?: string
  severity?: string
  outcome?: string
  requires_review?: boolean
  from_date?: string
  to_date?: string
  limit?: number
  offset?: number
}): Promise<ActivityLog[]> {
  const res = await apiClient.get<ActivityLog[]>('/api/admin/activity/timeline', { params })
  return res.data
}

export async function reviewActivityLog(logId: string, isReviewed: boolean = true): Promise<ActivityLog> {
  const res = await apiClient.post<ActivityLog>(`/api/admin/activity/${logId}/review`, {
    is_reviewed: isReviewed,
  })
  return res.data
}

export async function fetchSecurityAlerts(params?: {
  status?: string
  severity?: string
  limit?: number
  offset?: number
}): Promise<SecurityAlert[]> {
  const res = await apiClient.get<SecurityAlert[]>('/api/admin/alerts', { params })
  return res.data
}

export async function triageSecurityAlert(
  alertId: string,
  newStatus: string,
  resolutionNotes?: string
): Promise<SecurityAlert> {
  const res = await apiClient.patch<SecurityAlert>(`/api/admin/alerts/${alertId}/triage`, {
    status: newStatus,
    resolution_notes: resolutionNotes,
  })
  return res.data
}

export async function fetchClientProfile(clientId: string): Promise<ClientProfileExtended> {
  const res = await apiClient.get<ClientProfileExtended>(`/api/admin/clients/${clientId}/profile`)
  return res.data
}

export async function setClientAccountStatus(
  clientId: string,
  accountStatus: string,
  reason?: string
): Promise<User> {
  const res = await apiClient.post<User>(`/api/admin/clients/${clientId}/set-status`, {
    account_status: accountStatus,
    reason,
  })
  return res.data
}

export async function unlockClientAccount(clientId: string): Promise<User> {
  const res = await apiClient.post<User>(`/api/admin/clients/${clientId}/unlock`, {})
  return res.data
}

export async function forceClientPasswordReset(clientId: string): Promise<{
  success: boolean
  message: string
  client_id: string
  recovery_token: string
  expires_in_hours: number
}> {
  const res = await apiClient.post<{
    success: boolean
    message: string
    client_id: string
    recovery_token: string
    expires_in_hours: number
  }>(`/api/admin/clients/${clientId}/force-reset`, {})
  return res.data
}

export async function fetchBackgroundJobs(): Promise<BackgroundJobStatus[]> {
  const res = await apiClient.get<BackgroundJobStatus[]>('/api/admin/system/jobs-status')
  return res.data
}
