import { apiClient } from './client'
import { User } from '@/types/auth'

export interface SystemServiceStatus {
  name: string
  status: string
  details: string
  is_operational: boolean
}

export interface AdminOverview {
  total_users: number
  total_clients: number
  total_admins: number
  active_users: number
  disabled_users: number
  system_status: 'healthy' | 'degraded'
  services: SystemServiceStatus[]
  security_shields: {
    php2shell?: {
      status: string
      cves: string[]
      cvss_score: number
      error_handler_reentrancy_guard: string
    }
  }
}

export interface AuditEvent {
  id: string
  event_type: string
  description: string
  severity: 'info' | 'warning' | 'critical'
  actor: string
  timestamp: string
}

export interface AdminAuditResponse {
  total_events: number
  events: AuditEvent[]
}

export interface ClientOverview {
  user_id: string
  username: string
  email: string
  role: string
  is_active: boolean
  created_at: string
  active_targets_count: number
  scans_completed_count: number
  pending_fixes_count: number
  security_shield_status: string
  php2shell_protected: boolean
  notice: string
}

export async function fetchAdminOverview(): Promise<AdminOverview> {
  const res = await apiClient.get<AdminOverview>('/api/admin/overview')
  return res.data
}

export async function fetchAdminUsers(params?: {
  q?: string
  role?: string
  is_active?: boolean
}): Promise<User[]> {
  const res = await apiClient.get<User[]>('/api/admin/users', { params })
  return res.data
}

export async function updateUserStatus(userId: string, isActive: boolean): Promise<User> {
  const res = await apiClient.patch<User>(`/api/admin/users/${userId}/status`, {
    is_active: isActive,
  })
  return res.data
}

export async function fetchAdminAuditLogs(): Promise<AdminAuditResponse> {
  const res = await apiClient.get<AdminAuditResponse>('/api/admin/audit-logs')
  return res.data
}

export async function fetchClientOverview(): Promise<ClientOverview> {
  const res = await apiClient.get<ClientOverview>('/api/client/overview')
  return res.data
}

export async function changePassword(payload: {
  current_password: string
  new_password: string
  new_password_confirmation: string
}): Promise<void> {
  await apiClient.post('/api/client/change-password', payload)
}
