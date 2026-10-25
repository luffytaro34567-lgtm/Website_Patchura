export type RemediationStatus =
  | 'pending'
  | 'generating'
  | 'patch_ready'
  | 'testing'
  | 'test_passed'
  | 'test_failed'
  | 'approved'
  | 'rejected'
  | 'failed'

export type TestStatus = 'untested' | 'passed' | 'failed' | 'syntax_error'

export type ApprovalStatus = 'pending' | 'approved' | 'rejected'

export interface RemediationSession {
  id: string
  finding_id: string
  scan_id: string
  website_id: string
  user_id: string
  input_method: 'snippet' | 'file_upload'
  target_filename: string
  language: string
  original_code: string
  status: RemediationStatus
  ai_provider: string
  proposed_diff?: string | null
  patched_code?: string | null
  explanation?: string | null
  security_warnings?: string | null
  php2shell_mitigation_notes?: string | null
  confidence_score?: number | null
  test_status: TestStatus
  test_output?: string | null
  tested_at?: string | null
  approval_status: ApprovalStatus
  approval_notes?: string | null
  approved_at?: string | null
  client_consent_given: boolean
  created_at: string
  updated_at: string

  // UI context decorations
  finding_title?: string
  finding_severity?: string
  finding_category?: string
  cwe_id?: string
  website_domain?: string
}

export interface RemediationSessionSummary {
  id: string
  finding_id: string
  finding_title: string
  finding_severity: string
  website_domain: string
  target_filename: string
  language: string
  status: RemediationStatus
  ai_provider: string
  test_status: TestStatus
  approval_status: ApprovalStatus
  created_at: string
}

export interface CreateRemediationRequest {
  finding_id: string
  input_method: 'snippet' | 'file_upload'
  target_filename: string
  language: string
  source_code: string
  consent_acknowledged: boolean
}

export interface TestResult {
  session_id: string
  test_status: TestStatus
  passed: boolean
  diagnostics: string
  tested_at: string
}

export interface AdminRemediationStats {
  total_remediations: number
  approved_patches: number
  rejected_patches: number
  tests_passed: number
  tests_failed: number
  pending_approval: number
  ai_provider_active: string
}
