import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ThemeProvider } from '@/theme/ThemeContext'
import { AuthProvider } from '@/context/AuthContext'
import { ClientBillingPage } from '@/pages/client/ClientBillingPage'
import { AdminBillingPage } from '@/pages/admin/AdminBillingPage'
import { AdminBillingStats, PlanTierInfo, Subscription } from '@/types/billing'

const { mockSub, mockPlans, mockAdminStats } = vi.hoisted(() => {
  const sub: Subscription = {
    id: 'sub-1',
    user_id: 'usr-1',
    plan_tier: 'free',
    billing_interval: 'month',
    status: 'active',
    price_cents: 0,
    currency: 'USD',
    current_period_start: '2026-10-24T16:00:00Z',
    cancel_at_period_end: false,
    provider: 'sandbox',
    max_target_websites: 1,
    monthly_scan_limit: 3,
    reports_included_per_month: 0,
    current_target_count: 1,
    scans_used_this_month: 1,
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
    {
      tier: 'enterprise',
      name: 'Enterprise Shield',
      tag: 'Mission Critical',
      monthly_price_cents: 29900,
      annual_price_cents: 299000,
      currency: 'USD',
      max_target_websites: 999999,
      monthly_scan_limit: 999999,
      reports_included_per_month: 999999,
      features: ['Unlimited Targets', 'Continuous Audits'],
    },
  ]

  const stats: AdminBillingStats = {
    total_revenue_cents: 15800,
    active_subscriptions_count: 2,
    pro_subscriptions_count: 2,
    enterprise_subscriptions_count: 0,
    total_transactions_count: 2,
  }

  return { mockSub: sub, mockPlans: plans, mockAdminStats: stats }
})

vi.mock('@/api/billing', () => ({
  getMySubscription: vi.fn().mockResolvedValue(mockSub),
  listPlans: vi.fn().mockResolvedValue(mockPlans),
  listMyInvoices: vi.fn().mockResolvedValue([
    {
      id: 'inv-1',
      invoice_number: 'INV-2026-BH-TEST123',
      amount_cents: 7900,
      currency: 'USD',
      status: 'paid',
      description: 'Pro Security Subscription',
      billing_name: 'Test Customer',
      billing_email: 'customer@test.com',
      created_at: '2026-10-24T16:00:00Z',
    },
  ]),
  createCheckoutSession: vi.fn().mockResolvedValue({
    session_id: 'cs_sandbox_test123',
    checkout_url: '/dashboard/billing?session_id=cs_sandbox_test123',
    provider: 'dev_sandbox',
    amount_cents: 7900,
    currency: 'USD',
    plan_tier: 'pro',
    billing_interval: 'month',
  }),
  simulateCheckoutCompletion: vi.fn().mockResolvedValue({
    ...mockSub,
    plan_tier: 'pro',
    max_target_websites: 10,
  }),
  cancelSubscription: vi.fn().mockResolvedValue({ ...mockSub, cancel_at_period_end: true }),
  downloadInvoiceHtml: vi.fn(),
  adminGetBillingStats: vi.fn().mockResolvedValue(mockAdminStats),
  adminListTransactions: vi.fn().mockResolvedValue([
    {
      id: 'tx-1',
      user_id: 'usr-1',
      amount_cents: 7900,
      currency: 'USD',
      status: 'succeeded',
      payment_type: 'subscription',
      provider: 'dev_sandbox',
      idempotency_key: 'idem-1',
      created_at: '2026-10-24T16:00:00Z',
    },
  ]),
}))

function renderWithProviders(ui: React.ReactElement) {
  return render(
    <ThemeProvider>
      <AuthProvider>
        <MemoryRouter>
          {ui}
        </MemoryRouter>
      </AuthProvider>
    </ThemeProvider>
  )
}

describe('ClientBillingPage (Phase 7)', () => {
  it('renders billing header, active plan card, and quota meters', async () => {
    renderWithProviders(<ClientBillingPage />)

    expect(await screen.findByText(/Subscription & Billing/i)).toBeInTheDocument()
    expect(await screen.findByText(/PATCHORA free Edition/i)).toBeInTheDocument()
    expect(screen.getByText(/Registered Targets/i)).toBeInTheDocument()
    expect(screen.getByText(/Monthly Scans Used/i)).toBeInTheDocument()
    expect(screen.getByText('1 / 1')).toBeInTheDocument()
  })

  it('renders plan cards with monthly prices and opens checkout modal', async () => {
    renderWithProviders(<ClientBillingPage />)

    expect(await screen.findByText('Pro Security')).toBeInTheDocument()
    expect(screen.getByText('$79.00')).toBeInTheDocument()
    expect(screen.getByText('$299.00')).toBeInTheDocument()

    const upgradeBtn = screen.getByRole('button', { name: /Upgrade to Pro Security/i })
    fireEvent.click(upgradeBtn)

    expect(await screen.findByText(/Payment Checkout — PRO Plan/i)).toBeInTheDocument()
    expect(screen.getByText(/Gateway Authorization Workflow/i)).toBeInTheDocument()
    expect(screen.getByText(/Authorize Payment \(Success\)/i)).toBeInTheDocument()
  })
})

describe('AdminBillingPage (Phase 7)', () => {
  it('renders platform revenue stats and global transactions', async () => {
    renderWithProviders(<AdminBillingPage />)

    expect(screen.getByText(/Billing & Revenue Administration/i)).toBeInTheDocument()
    expect(await screen.findByText('$158.00')).toBeInTheDocument()
    expect(screen.getByText('Pro Plan Seats')).toBeInTheDocument()
    expect(screen.getByText(/Global Payment Transactions/i)).toBeInTheDocument()
  })
})
