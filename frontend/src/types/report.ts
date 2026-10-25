import { ScanFinding } from './scan'

export interface ReportPricing {
  product_name: string
  price: number
  currency: string
  description: string
  features: string[]
}

export interface ReportOrder {
  id: string
  scan_id: string
  user_id: string
  product_name: string
  amount: number
  currency: string
  status: 'pending' | 'completed' | 'failed' | 'cancelled'
  payment_method: string
  transaction_reference: string
  failure_reason?: string | null
  created_at: string
  completed_at?: string | null
}

export interface ReportEntitlement {
  id: string
  scan_id: string
  user_id: string
  is_active: boolean
  granted_at: string
  expires_at?: string | null
  granted_by: string
  access_count: number
  last_accessed_at?: string | null
}

export interface ReportEntitlementStatus {
  scan_id: string
  has_entitlement: boolean
  can_purchase: boolean
  pricing: ReportPricing
  entitlement?: ReportEntitlement | null
  active_order?: ReportOrder | null
}

export interface DetailedReport {
  id: string
  scan_id: string
  website_id: string
  title: string
  target_url: string
  target_domain: string
  profile: string
  executive_summary: string
  overall_risk_score: number
  overall_posture: string
  has_php2shell_finding: boolean
  php2shell_posture: string
  generated_at: string
  version: number
  total_findings: number
  severity_breakdown: Record<string, number>
  findings: ScanFinding[]
  html_content: string
}
