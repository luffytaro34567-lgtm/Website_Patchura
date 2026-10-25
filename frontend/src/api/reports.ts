import { apiClient } from './client'
import {
  DetailedReport,
  ReportEntitlement,
  ReportEntitlementStatus,
  ReportOrder,
  ReportPricing,
} from '@/types/report'

export async function getReportPricing(): Promise<ReportPricing> {
  const res = await apiClient.get<ReportPricing>('/api/reports/pricing')
  return res.data
}

export async function getReportStatus(scanId: string): Promise<ReportEntitlementStatus> {
  const res = await apiClient.get<ReportEntitlementStatus>(`/api/reports/scan/${scanId}/status`)
  return res.data
}

export async function createReportOrder(
  scanId: string,
  paymentMethod: string = 'dev_checkout'
): Promise<ReportOrder> {
  const res = await apiClient.post<ReportOrder>(`/api/reports/scan/${scanId}/order`, {
    scan_id: scanId,
    payment_method: paymentMethod,
  })
  return res.data
}

export async function completeReportOrder(
  orderId: string,
  simulateStatus: string = 'completed'
): Promise<ReportOrder> {
  const res = await apiClient.post<ReportOrder>(`/api/reports/orders/${orderId}/complete`, {
    simulate_status: simulateStatus,
  })
  return res.data
}

export async function getDetailedReport(scanId: string): Promise<DetailedReport> {
  const res = await apiClient.get<DetailedReport>(`/api/reports/scan/${scanId}/details`)
  return res.data
}

export async function downloadReportHtml(scanId: string, domain: string): Promise<void> {
  const res = await apiClient.get(`/api/reports/scan/${scanId}/download-html`, {
    responseType: 'blob',
  })
  const blob = new Blob([res.data], { type: 'text/html' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `patchora-report-${domain}-${scanId.slice(0, 8)}.html`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export async function listMyReports(): Promise<ReportEntitlement[]> {
  const res = await apiClient.get<ReportEntitlement[]>('/api/reports/my-reports')
  return res.data
}

export async function adminListReportOrders(): Promise<ReportOrder[]> {
  const res = await apiClient.get<ReportOrder[]>('/api/reports/admin/orders')
  return res.data
}

export async function adminGrantEntitlement(
  scanId: string,
  reason: string
): Promise<ReportEntitlement> {
  const res = await apiClient.post<ReportEntitlement>('/api/reports/admin/grant-entitlement', {
    scan_id: scanId,
    reason,
  })
  return res.data
}
