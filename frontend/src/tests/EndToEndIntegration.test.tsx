import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ThemeProvider } from '@/theme/ThemeContext'
import { AuthProvider } from '@/context/AuthContext'
import { LoginPage } from '@/pages/LoginPage'
import { ClientOverviewPage } from '@/pages/client/ClientOverviewPage'
import { AdminOverviewPage } from '@/pages/admin/AdminOverviewPage'
import { AdminActivityCenterPage } from '@/pages/admin/AdminActivityCenterPage'

vi.mock('@/api/auth', () => ({
  loginUser: vi.fn().mockResolvedValue({
    access_token: 'mock-access-token',
    refresh_token: 'mock-refresh-token',
    expires_in: 900,
    user: {
      id: 'client-1',
      username: 'enterprise_user',
      email: 'user@enterprise.io',
      role: 'client',
      is_active: true,
      created_at: '2026-10-24T12:00:00Z',
    },
  }),
  recoverPassword: vi.fn().mockResolvedValue({
    success: true,
    message: 'Recovery instructions sent.',
    recovery_token: 'rec-tok-mock-12345',
  }),
  resetPasswordWithToken: vi.fn().mockResolvedValue({
    success: true,
    message: 'Password reset successfully.',
    username: 'enterprise_user',
  }),
  fetchCurrentUser: vi.fn().mockResolvedValue({
    id: 'client-1',
    username: 'enterprise_user',
    email: 'user@enterprise.io',
    role: 'client',
    is_active: true,
    created_at: '2026-10-24T12:00:00Z',
  }),
  logoutUser: vi.fn().mockResolvedValue(undefined),
}))

vi.mock('@/api/dashboard', () => ({
  fetchClientOverview: vi.fn().mockResolvedValue({
    user: {
      id: 'client-1',
      username: 'enterprise_user',
      email: 'user@enterprise.io',
      role: 'client',
      is_active: true,
      created_at: '2026-10-24T12:00:00Z',
    },
    active_subscription_tier: 'Enterprise Shield',
    total_scans_run: 15,
    pending_fixes: 2,
    target_websites_registered: 3,
    security_posture: {
      php2shell_shield_active: true,
      cves_mitigated: ['CVE-2026-109618', 'CVE-2026-109619'],
      overall_risk_score: 9.4,
    },
    recent_scans: [],
    recent_remediations: [],
  }),
  fetchAdminOverview: vi.fn().mockResolvedValue({
    total_users: 150,
    total_clients: 142,
    total_admins: 8,
    active_users: 148,
    disabled_users: 2,
    system_status: 'healthy',
    services: [
      { name: 'PostgreSQL Database Engine', status: 'healthy', details: 'Operational', is_operational: true },
      { name: 'PHP2Shell Shield Engine', status: 'active', details: 'CVE-2026-109618/19 Loaded', is_operational: true },
    ],
    security_shields: {
      php2shell: { status: 'active', cvss_score: 9.2 },
    },
  }),
}))

vi.mock('@/api/activity', () => ({
  fetchActivityMetrics: vi.fn().mockResolvedValue({
    timeframe: '24h',
    total_clients: 142,
    active_clients: 140,
    suspended_clients: 2,
    terminated_clients: 0,
    recent_successful_logins: 210,
    recent_failed_logins: 4,
    pending_recovery_requests: 1,
    open_security_alerts: 3,
    critical_security_alerts: 1,
    php2shell_alerts_count: 2,
    website_verification_events: 18,
    scans_running: 1,
    scans_completed: 42,
    scans_failed_or_blocked: 0,
    report_access_events: 15,
    payments_successful: 8,
    payments_failed: 0,
    remediations_approved: 12,
    deployments_staging: 9,
    deployments_production: 2,
    client_finder_outreach_sent: 35,
    background_jobs_attention_required: 0,
  }),
  fetchActivityTimeline: vi.fn().mockResolvedValue([]),
  fetchSecurityAlerts: vi.fn().mockResolvedValue([]),
  fetchBackgroundJobs: vi.fn().mockResolvedValue([]),
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

describe('End-to-End Cross-Module Integration Suite', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('handles client login and renders personalized client overview with PHP2Shell shield posture', async () => {
    renderWithProviders(<ClientOverviewPage />)

    expect(await screen.findByText('Security Posture Overview')).toBeInTheDocument()
    expect(screen.getByText('Enterprise Shield')).toBeInTheDocument()
    expect(screen.getByText('PHP2Shell Shield')).toBeInTheDocument()
  })

  it('renders password recovery workflow from login page', async () => {
    renderWithProviders(<LoginPage />)

    const forgotBtn = screen.getByRole('button', { name: /Forgot password\?/i })
    fireEvent.click(forgotBtn)

    expect(await screen.findByText('Password Recovery')).toBeInTheDocument()
    expect(screen.getByText('Send Recovery Token')).toBeInTheDocument()
  })

  it('renders admin overview with live system services and PHP2Shell shield status', async () => {
    renderWithProviders(<AdminOverviewPage />)

    expect(await screen.findByText('Platform Overview & Health')).toBeInTheDocument()
    expect(screen.getByText('142')).toBeInTheDocument() // Clients
    expect(screen.getByText('148')).toBeInTheDocument() // Active users
    expect(screen.getByText('PHP2Shell Shield Engine')).toBeInTheDocument()
  })

  it('renders administrative activity center metrics and real-time telemetry', async () => {
    renderWithProviders(<AdminActivityCenterPage />)

    expect(await screen.findByText('Activity & Security Center')).toBeInTheDocument()
    expect(await screen.findByText('210')).toBeInTheDocument() // Successful logins
  })
})
