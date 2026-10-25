import { apiClient } from './client'
import {
  CreateWebsiteData,
  ScanAuthorizationData,
  VerificationMethod,
  VerificationResult,
  Website,
} from '@/types/website'

export async function createWebsite(data: CreateWebsiteData): Promise<Website> {
  const res = await apiClient.post<Website>('/api/websites', data)
  return res.data
}

export async function listWebsites(): Promise<Website[]> {
  const res = await apiClient.get<Website[]>('/api/websites')
  return res.data
}

export async function getWebsite(id: string): Promise<Website> {
  const res = await apiClient.get<Website>(`/api/websites/${id}`)
  return res.data
}

export async function updateVerificationMethod(
  id: string,
  method: VerificationMethod
): Promise<Website> {
  const res = await apiClient.patch<Website>(`/api/websites/${id}/verification-method`, {
    verification_method: method,
  })
  return res.data
}

export async function verifyWebsite(id: string): Promise<VerificationResult> {
  const res = await apiClient.post<VerificationResult>(`/api/websites/${id}/verify`)
  return res.data
}

export async function authorizeWebsiteScan(
  id: string,
  data: ScanAuthorizationData
): Promise<Website> {
  const res = await apiClient.post<Website>(`/api/websites/${id}/authorize`, data)
  return res.data
}

export async function revokeWebsiteAuthorization(
  id: string,
  reason?: string
): Promise<Website> {
  const res = await apiClient.post<Website>(`/api/websites/${id}/revoke-authorization`, {
    revocation_reason: reason,
  })
  return res.data
}

export async function deleteWebsite(id: string): Promise<void> {
  await apiClient.delete(`/api/websites/${id}`)
}

// ── Admin Endpoints ──────────────────────────────────────────────────────────

export async function adminListWebsites(): Promise<Website[]> {
  const res = await apiClient.get<Website[]>('/api/admin/websites')
  return res.data
}

export async function adminSuspendWebsite(
  id: string,
  isSuspended: boolean,
  reason?: string
): Promise<Website> {
  const res = await apiClient.patch<Website>(`/api/admin/websites/${id}/suspend`, {
    is_suspended: isSuspended,
    suspension_reason: reason,
  })
  return res.data
}
