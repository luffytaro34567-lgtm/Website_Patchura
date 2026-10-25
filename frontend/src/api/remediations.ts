import { apiClient } from './client'
import {
  AdminRemediationStats,
  CreateRemediationRequest,
  RemediationSession,
  RemediationSessionSummary,
  TestResult,
} from '@/types/remediation'

export async function createRemediation(payload: CreateRemediationRequest): Promise<RemediationSession> {
  const res = await apiClient.post<RemediationSession>('/api/remediations/request', payload)
  return res.data
}

export async function listMyRemediations(limit = 50, offset = 0): Promise<RemediationSessionSummary[]> {
  const res = await apiClient.get<RemediationSessionSummary[]>('/api/remediations', {
    params: { limit, offset },
  })
  return res.data
}

export async function getRemediation(sessionId: string): Promise<RemediationSession> {
  const res = await apiClient.get<RemediationSession>(`/api/remediations/${sessionId}`)
  return res.data
}

export async function getRemediationsForFinding(findingId: string): Promise<RemediationSession[]> {
  const res = await apiClient.get<RemediationSession[]>(`/api/remediations/finding/${findingId}`)
  return res.data
}

export async function testPatch(sessionId: string): Promise<TestResult> {
  const res = await apiClient.post<TestResult>(`/api/remediations/${sessionId}/test`, {})
  return res.data
}

export async function approvePatch(sessionId: string, approvalNotes?: string): Promise<RemediationSession> {
  const res = await apiClient.post<RemediationSession>(`/api/remediations/${sessionId}/approve`, {
    approval_notes: approvalNotes,
  })
  return res.data
}

export async function rejectPatch(sessionId: string, rejectionReason: string): Promise<RemediationSession> {
  const res = await apiClient.post<RemediationSession>(`/api/remediations/${sessionId}/reject`, {
    rejection_reason: rejectionReason,
  })
  return res.data
}

export async function downloadPatchFile(sessionId: string, filename = 'patch.diff'): Promise<void> {
  const res = await apiClient.get(`/api/remediations/${sessionId}/download/patch`, {
    responseType: 'blob',
  })
  const blob = new Blob([res.data], { type: 'text/x-diff' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export async function downloadPatchedCodeFile(sessionId: string, filename = 'patched_code.txt'): Promise<void> {
  const res = await apiClient.get(`/api/remediations/${sessionId}/download/file`, {
    responseType: 'blob',
  })
  const blob = new Blob([res.data], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export async function adminGetRemediationStats(): Promise<AdminRemediationStats> {
  const res = await apiClient.get<AdminRemediationStats>('/api/remediations/admin/stats')
  return res.data
}
