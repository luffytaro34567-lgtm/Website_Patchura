import { apiClient } from './client'
import { CreateScanPayload, Scan, ScanSummaryExport } from '@/types/scan'

export async function createScan(data: CreateScanPayload): Promise<Scan> {
  const res = await apiClient.post<Scan>('/api/scans', data)
  return res.data
}

export async function listScans(websiteId?: string, status?: string): Promise<Scan[]> {
  const params: Record<string, string> = {}
  if (websiteId) params.website_id = websiteId
  if (status) params.status = status
  const res = await apiClient.get<Scan[]>('/api/scans', { params })
  return res.data
}

export async function getScanDetails(scanId: string): Promise<Scan> {
  const res = await apiClient.get<Scan>(`/api/scans/${scanId}`)
  return res.data
}
export const getScan = getScanDetails

export async function cancelScan(scanId: string): Promise<Scan> {
  const res = await apiClient.post<Scan>(`/api/scans/${scanId}/cancel`)
  return res.data
}

export async function exportScanSummary(scanId: string): Promise<ScanSummaryExport> {
  const res = await apiClient.get<ScanSummaryExport>(`/api/scans/${scanId}/export`)
  return res.data
}

export async function adminListScans(status?: string): Promise<Scan[]> {
  const params: Record<string, string> = {}
  if (status) params.status = status
  const res = await apiClient.get<Scan[]>('/api/admin/scans', { params })
  return res.data
}

export async function adminCancelScan(scanId: string): Promise<Scan> {
  const res = await apiClient.post<Scan>(`/api/admin/scans/${scanId}/cancel`)
  return res.data
}
