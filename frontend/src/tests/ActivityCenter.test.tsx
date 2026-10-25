import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ThemeProvider } from '@/theme/ThemeContext'
import { AuthProvider } from '@/context/AuthContext'
import { AdminActivityCenterPage } from '@/pages/admin/AdminActivityCenterPage'
import {
  ActivityLog,
  ActivitySummaryMetrics,
  BackgroundJobStatus,
  SecurityAlert,
} from '@/types/activity'

const mockMetrics: ActivitySummaryMetrics = {
  timeframe: '24h',
  total_clients: 24,
  active_clients: 22,
  suspended_clients: 2,
  terminated_clients: 0,
  recent_successful_logins: 45,
  recent_failed_logins: 3,
  pending_recovery_requests: 1,
  open_security_alerts: 4,
  critical_security_alerts: 2,
  php2shell_alerts_count: 3,
  website_verification_events: 12,
  scans_running: 2,
  scans_completed: 18,
  scans_failed_or_blocked: 1,
  report_access_events: 8,
  payments_successful: 5,
  payments_failed: 0,
  remediations_approved: 7,
  deployments_staging: 6,
  deployments_production: 1,
  client_finder_outreach_sent: 14,
  background_jobs_attention_required: 0,
}

const mockTimeline: ActivityLog[] = [
  {
    id: 'log-1',
    timestamp: '2026-10-24T18:00:00Z',
    event_category: 'authentication',
    event_name: 'user_login_success',
    actor_type: 'user',
    actor_email: 'client@acme.com',
    target_identifier: 'client@acme.com',
    outcome: 'success',
    severity: 'info',
    source_module: 'auth',
    requires_review: false,
    is_reviewed: false,
  },
  {
    id: 'log-2',
    timestamp: '2026-10-24T18:15:00Z',
    event_category: 'vulnerability_scanning',
    event_name: 'scan_completed',
    actor_type: 'system',
    target_identifier: 'store.acme.com',
    outcome: 'success',
    severity: 'critical',
    source_module: 'scanner',
    requires_review: true,
    is_reviewed: false,
  },
]

const mockAlerts: SecurityAlert[] = [
  {
    id: 'alert-1',
    created_at: '2026-10-24T18:15:00Z',
    updated_at: '2026-10-24T18:15:00Z',
    alert_type: 'php2shell_high_risk_detected',
    title: 'PHP2Shell Memory Corruption detected on store.acme.com',
    description: 'Critical unhandled PHP error display and stack leak observed.',
    severity: 'critical',
    status: 'open',
    source_module: 'scanner',
    cve_id: 'CVE-2026-109618, CVE-2026-109619',
  },
]

const mockJobs: BackgroundJobStatus[] = [
  {
    name: 'Vulnerability Scanner Dispatcher',
    status: 'healthy',
    category: 'scans',
    details: 'Worker pool active with safe authorization checks.',
    requires_attention: false,
    last_run: '2026-10-24T18:25:00Z',
  },
  {
    name: 'PHP2Shell Memory Defense & AST Engine',
    status: 'operational',
    category: 'security',
    details: 'Zero-day AST mitigation patterns active.',
    requires_attention: false,
    last_run: '2026-10-24T18:25:00Z',
  },
]

vi.mock('@/api/activity', () => ({
  fetchActivityMetrics: vi.fn().mockResolvedValue(mockMetrics),
  fetchActivityTimeline: vi.fn().mockResolvedValue(mockTimeline),
  reviewActivityLog: vi.fn().mockImplementation((id) =>
    Promise.resolve({
      ...mockTimeline[1],
      is_reviewed: true,
    })
  ),
  fetchSecurityAlerts: vi.fn().mockResolvedValue(mockAlerts),
  triageSecurityAlert: vi.fn().mockImplementation((id, status, notes) =>
    Promise.resolve({
      ...mockAlerts[0],
      status,
      resolution_notes: notes,
      resolved_at: '2026-10-24T18:30:00Z',
    })
  ),
  fetchBackgroundJobs: vi.fn().mockResolvedValue(mockJobs),
  fetchClientProfile: vi.fn().mockResolvedValue({
    id: 'client-uuid-1',
    username: 'client_acme',
    email: 'client@acme.com',
    role: 'client',
    is_active: true,
    account_status: 'active',
    failed_login_attempts: 0,
    created_at: '2026-10-24T16:00:00Z',
    updated_at: '2026-10-24T16:00:00Z',
    websites_count: 3,
    scans_count: 5,
    reports_count: 2,
    active_plan: 'pro',
    remediations_count: 1,
    deployments_count: 1,
    force_password_reset: false,
  }),
  setClientAccountStatus: vi.fn().mockResolvedValue({ is_active: false }),
  unlockClientAccount: vi.fn().mockResolvedValue({ is_active: true, failed_login_attempts: 0 }),
  forceClientPasswordReset: vi.fn().mockResolvedValue({
    success: true,
    message: 'Password reset forced',
    recovery_token: 'rec-tok-test-1234',
    expires_in_hours: 24,
  }),
}))

function renderWithProviders(ui: React.ReactElement) {
  return render(
    <ThemeProvider>
      <AuthProvider>
        <MemoryRouter>{ui}</MemoryRouter>
      </AuthProvider>
    </ThemeProvider>
  )
}

describe('AdminActivityCenterPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders activity center title and summary KPI metrics from database', async () => {
    renderWithProviders(<AdminActivityCenterPage />)

    expect(await screen.findByText('Activity & Security Center')).toBeInTheDocument()
    expect(screen.getByText('Admin Real-Time Telemetry')).toBeInTheDocument()

    // KPI values
    expect(await screen.findByText('24')).toBeInTheDocument() // Total clients
    expect(screen.getByText('45')).toBeInTheDocument() // Logins
    expect(screen.getByText('4')).toBeInTheDocument() // Open alerts
  })

  it('renders timeline table with events, severity badges, and review triggers', async () => {
    renderWithProviders(<AdminActivityCenterPage />)

    expect(await screen.findByText('user_login_success')).toBeInTheDocument()
    expect(screen.getByText('client@acme.com')).toBeInTheDocument()
    expect(screen.getByText('scan_completed')).toBeInTheDocument()
    expect(screen.getByText('store.acme.com')).toBeInTheDocument()
  })

  it('supports tab navigation to Security Alerts and triage interaction', async () => {
    renderWithProviders(<AdminActivityCenterPage />)

    // Switch to Security Alerts tab
    const alertsTab = await screen.findByRole('button', { name: /Security Alerts/i })
    fireEvent.click(alertsTab)

    expect(await screen.findByText(/PHP2Shell Memory Corruption detected on store.acme.com/i)).toBeInTheDocument()
    expect(screen.getByText('CVE-2026-109618, CVE-2026-109619')).toBeInTheDocument()

    // Open Triage Modal
    const triageBtn = screen.getByText('Triage / Update')
    fireEvent.click(triageBtn)

    expect(await screen.findByText('Triage Security Alert')).toBeInTheDocument()
    expect(screen.getByText('Save Triage Decision')).toBeInTheDocument()
  })

  it('supports tab navigation to Background Workers & Engines', async () => {
    renderWithProviders(<AdminActivityCenterPage />)

    const workersTab = await screen.findByRole('button', { name: /Background Workers & Engines/i })
    fireEvent.click(workersTab)

    expect(await screen.findByText('Vulnerability Scanner Dispatcher')).toBeInTheDocument()
    expect(screen.getByText('PHP2Shell Memory Defense & AST Engine')).toBeInTheDocument()
  })
})
