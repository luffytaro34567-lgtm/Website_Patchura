export type ScanProfile = 'passive' | 'standard' | 'php_deep'

export type ScanStatus = 'queued' | 'running' | 'completed' | 'failed' | 'cancelled'

export type FindingSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info'

export interface ScanFinding {
  id: string
  scan_id: string
  website_id: string
  title: string
  severity: FindingSeverity
  category: string
  description: string
  evidence: string
  remediation: string
  cwe_id?: string | null
  cvss_score?: number | null
  target_url: string
  created_at: string
}

export interface Scan {
  id: string
  website_id: string
  user_id: string
  profile: ScanProfile
  status: ScanStatus
  progress_percent: number
  target_url: string
  target_domain: string
  started_at?: string | null
  completed_at?: string | null
  duration_seconds?: number | null
  error_message?: string | null
  is_cancelled: boolean
  cancelled_by?: string | null
  total_findings: number
  critical_count: number
  high_count: number
  medium_count: number
  low_count: number
  info_count: number
  created_at: string
  findings?: ScanFinding[]
}

export interface CreateScanPayload {
  website_id: string
  profile: ScanProfile
}

export interface ScanSummaryExport {
  scan_id: string
  target_url: string
  target_domain: string
  profile: string
  status: string
  started_at?: string | null
  completed_at?: string | null
  duration_seconds?: number | null
  total_findings: number
  severity_breakdown: Record<FindingSeverity, number>
  findings: ScanFinding[]
  exported_at: string
  platform: string
  php2shell_shield_evaluated: boolean
  disclaimer: string
}
