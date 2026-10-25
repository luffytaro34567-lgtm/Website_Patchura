import { apiClient } from './client'

export interface Finding {
  rule_id: string
  title: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  owasp: string
  cwe: string
  line_number: number
  line_content: string
  description: string
  remediation: string
  cve?: string
  cvss_score?: number
  suggested_fix?: string
}

export interface RecommendedAction {
  layer: string
  priority: string
  step: string
  configuration_snippet?: string
  code_snippet?: string
}

export interface MitigationPlan {
  vulnerability: string
  cves: string[]
  cvss_score: number
  impact: string
  affected_versions: string
  recommended_actions: RecommendedAction[]
}

export interface ScanPhpResponse {
  total_lines: number
  findings: Finding[]
  has_php2shell_vulnerability: boolean
  summary: {
    total_findings: number
    by_severity: Record<string, number>
    cves_detected: string[]
    php2shell_affected: boolean
  }
  remediation_guidance?: MitigationPlan
}

export async function analyzePhpCode(sourceCode: string, fileName = 'index.php'): Promise<ScanPhpResponse> {
  const res = await apiClient.post<ScanPhpResponse>('/api/scan/php/analyze', {
    source_code: sourceCode,
    file_name: fileName,
  })
  return res.data
}

export async function getPhp2ShellMitigation(): Promise<MitigationPlan> {
  const res = await apiClient.get<MitigationPlan>('/api/scan/php/php2shell-mitigation')
  return res.data
}
