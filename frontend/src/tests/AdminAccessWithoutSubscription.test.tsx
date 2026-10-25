import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { AdminRoute } from '@/router/ProtectedRoute'
import { ClientBillingPage } from '@/pages/client/ClientBillingPage'
import { LoginPage } from '@/pages/LoginPage'
import { AuthProvider } from '@/context/AuthContext'
import { ThemeProvider } from '@/theme/ThemeContext'
import { PlanTierInfo, Subscription } from '@/types/billing'

const mockAdminUser = {
  id: 'admin-id-123',
  username: 'sec_admin',
  email: 'sec_admin@patchora.io',
  role: 'admin',
  is_active: true,
  created_at: '2026-10-24T12:00:00Z',
}

const mockClientUser = {
  id: 'client-id-456',
  username: 'regular_client',
  email: 'client@example.com',
  role: 'client',
  is_active: true,
  created_at: '2026-10-24T12:00:00Z',
}

const { mockSub, mockPlans } = vi.hoisted(() => {
  const sub: Subscription = {
    id: 'sub-admin-1',
    user_id: 'admin-id-123',
    plan_tier: 'admin',
    billing_interval: 'year',
    status: 'active',
    price_cents: 0,
    currency: 'USD',
    current_period_start: '2026-10-24T12:00:00Z',
    cancel_at_period_end: false,
    provider: 'system_admin',
    max_target_websites: 999999,
    monthly_scan_limit: 999999,
    reports_included_per_month: 999999,
    current_target_count: 3,
    scans_used_this_month: 12,
  }

  const plans: PlanTierInfo[] = [
    {
      tier: 'free',
      name: 'Community Free',
      tag: 'Starter',
      monthly_price_cents: 0,
      annual_price_cents: 0,
      currency: 'USD',
      max_target_websites: 1,
      monthly_scan_limit: 3,
      reports_included_per_month: 0,
      features: ['1 Target Website', '3 Monthly Scans'],
    },
    {
      tier: 'pro',
      name: 'Pro Security',
      tag: 'Popular',
      monthly_price_cents: 7900,
      annual_price_cents: 79000,
      currency: 'USD',
      max_target_websites: 10,
      monthly_scan_limit: 999999,
      reports_included_per_month: 5,
      features: ['10 Target Websites', 'Unlimited Scans', '5 Reports/mo'],
    },
  ]

  return { mockSub: sub, mockPlans: plans }
})

vi.mock('@/api/billing', () => ({
  getMySubscription: vi.fn().mockResolvedValue(mockSub),
  listPlans: vi.fn().mockResolvedValue(mockPlans),
  listMyInvoices: vi.fn().mockResolvedValue([]),
  createCheckoutSession: vi.fn(),
  simulateCheckoutCompletion: vi.fn(),
  cancelSubscription: vi.fn(),
  downloadInvoiceHtml: vi.fn(),
}))

let currentAuthUser: any = mockAdminUser

vi.mock('@/api/auth', () => ({
  loginUser: vi.fn().mockImplementation(async () => ({
    user: currentAuthUser,
    access_token: 'fake-jwt-token',
    refresh_token: 'fake-refresh-token',
  })),
  logoutUser: vi.fn().mockResolvedValue({ success: true }),
  rotateRefreshToken: vi.fn().mockImplementation(async () => ({
    user: currentAuthUser,
    access_token: 'fake-jwt-token',
    refresh_token: 'fake-refresh-token',
  })),
  registerClient: vi.fn(),
  recoverPassword: vi.fn(),
  resetPasswordWithToken: vi.fn(),
}))

describe('Prompt 20: Admin Access Without Subscription', () => {
  it('AdminRoute permits administrator without subscription check', async () => {
    currentAuthUser = mockAdminUser
    localStorage.setItem('bh_refresh_token', 'valid-token')

    render(
      <MemoryRouter initialEntries={['/admin/dashboard']}>
        <ThemeProvider>
          <AuthProvider>
            <Routes>
              <Route element={<AdminRoute />}>
                <Route path="/admin/dashboard" element={<div data-testid="admin-content">Admin Dashboard Unlocked</div>} />
              </Route>
            </Routes>
          </AuthProvider>
        </ThemeProvider>
      </MemoryRouter>
    )

    expect(await screen.findByTestId('admin-content')).toBeInTheDocument()
    expect(screen.getByText('Admin Dashboard Unlocked')).toBeInTheDocument()
  })

  it('AdminRoute blocks regular client user even if they attempt direct URL navigation', async () => {
    currentAuthUser = mockClientUser
    localStorage.setItem('bh_refresh_token', 'valid-token')

    render(
      <MemoryRouter initialEntries={['/admin/dashboard']}>
        <ThemeProvider>
          <AuthProvider>
            <Routes>
              <Route element={<AdminRoute />}>
                <Route path="/admin/dashboard" element={<div data-testid="admin-content">Admin Dashboard Unlocked</div>} />
              </Route>
            </Routes>
          </AuthProvider>
        </ThemeProvider>
      </MemoryRouter>
    )

    expect(await screen.findByText('Access Restricted')).toBeInTheDocument()
    expect(screen.getByText(/requires verified Administrator privileges/i)).toBeInTheDocument()
    expect(screen.queryByTestId('admin-content')).not.toBeInTheDocument()
  })

  it('ClientBillingPage displays Administrator Exemption banner and unlocked status for admins', async () => {
    currentAuthUser = mockAdminUser
    localStorage.setItem('bh_refresh_token', 'valid-token')

    render(
      <MemoryRouter initialEntries={['/dashboard/billing']}>
        <ThemeProvider>
          <AuthProvider>
            <ClientBillingPage />
          </AuthProvider>
        </ThemeProvider>
      </MemoryRouter>
    )

    expect(await screen.findByText(/Administrator Exemption:/i)).toBeInTheDocument()
    expect(
      screen.getByText(/full administrative privileges and unrestricted platform access/i)
    ).toBeInTheDocument()
    expect(screen.getAllByText('Admin Access Granted').length).toBeGreaterThan(0)
  })
})
