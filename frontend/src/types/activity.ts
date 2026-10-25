export type EventOutcome = 'success' | 'failure' | 'blocked' | 'pending'
export type EventSeverity = 'info' | 'warning' | 'critical'
export type AlertSeverity = 'critical' | 'high' | 'medium' | 'low'
export type AlertStatus = 'open' | 'acknowledged' | 'resolved' | 'dismissed' | 'false_positive'

export interface ActivityLog {
  id: string
  timestamp: string
  event_category: string
  event_name: string
  actor_type: string
  actor_id?: string | null
  actor_email?: string | null
  target_type?: string | null
  target_id?: string | null
  target_identifier?: string | null
  outcome: EventOutcome
  severity: EventSeverity
  source_module: string
  metadata_json?: string | null
  request_id?: string | null
  requires_review: boolean
  is_reviewed: boolean
  reviewed_by_admin_id?: string | null
  reviewed_at?: string | null
}

export interface SecurityAlert {
  id: string
  created_at: string
  updated_at: string
  alert_type: string
  title: string
  description: string
  severity: AlertSeverity
  status: AlertStatus
  source_module: string
  target_entity_type?: string | null
  target_entity_id?: string | null
  cve_id?: string | null
  metadata_json?: string | null
  assigned_admin_id?: string | null
  resolution_notes?: string | null
  resolved_at?: string | null
}

export interface ActivitySummaryMetrics {
  timeframe: string
  from_date?: string | null
  to_date?: string | null
  total_clients: number
  active_clients: number
  suspended_clients: number
  terminated_clients: number
  recent_successful_logins: number
  recent_failed_logins: number
  pending_recovery_requests: number
  open_security_alerts: number
  critical_security_alerts: number
  php2shell_alerts_count: number
  website_verification_events: number
  scans_running: number
  scans_completed: number
  scans_failed_or_blocked: number
  report_access_events: number
  payments_successful: number
  payments_failed: number
  remediations_approved: number
  deployments_staging: number
  deployments_production: number
  client_finder_outreach_sent: number
  background_jobs_attention_required: number
}

export interface ClientProfileExtended {
  id: string
  username: string
  email: string
  role: string
  is_active: boolean
  account_status: string
  failed_login_attempts: number
  locked_until?: string | null
  last_login_at?: string | null
  force_password_reset: boolean
  recovery_token_expires_at?: string | null
  created_at: string
  updated_at: string
  websites_count: number
  scans_count: number
  reports_count: number
  active_plan: string
  remediations_count: number
  deployments_count: number
}

export interface BackgroundJobStatus {
  name: string
  status: 'healthy' | 'operational' | 'degraded' | 'attention_required'
  category: string
  details: string
  requires_attention: boolean
  last_run?: string | null
}
