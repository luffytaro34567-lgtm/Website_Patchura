import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ThemeProvider } from '@/theme/ThemeContext'
import { AuthProvider } from '@/context/AuthContext'
import { AdminClientFinderPage } from '@/pages/admin/AdminClientFinderPage'
import {
  ClientFinderStats,
  DiscoveryCampaign,
  Lead,
  OutreachDraft,
  OutreachTemplate,
  SuppressionEntry,
} from '@/types/lead'

const mockStats: ClientFinderStats = {
  total_leads: 18,
  new_leads: 7,
  qualified_leads: 5,
  contacted_leads: 3,
  replied_leads: 2,
  interested_leads: 1,
  converted_clients: 1,
  converted_assessments: 1,
  outreach_pending_approval: 4,
  outreach_sent_today: 3,
  active_campaigns: 2,
  php2shell_high_risk_leads: 12,
}

const mockLeads: Lead[] = [
  {
    id: 'lead-1',
    company_name: 'Acme Logistics',
    domain: 'acme-logistics.com',
    website_url: 'https://acme-logistics.com',
    contact_name: 'Alice Smith',
    contact_email: 'alice@acme-logistics.com',
    contact_title: 'CTO',
    contact_source: 'automated_discovery',
    status: 'new',
    qualification_score: 85,
    technology_stack: 'PHP 8.1, Laravel 9, Nginx',
    php2shell_risk_level: 'high',
    notes: 'Exposed error traces detected on auth endpoint',
    created_at: '2026-10-24T18:00:00Z',
    updated_at: '2026-10-24T18:00:00Z',
  },
  {
    id: 'lead-2',
    company_name: 'Beta Retail',
    domain: 'beta-retail.shop',
    website_url: 'https://beta-retail.shop',
    contact_name: 'Bob Jones',
    contact_email: 'bob@beta-retail.shop',
    contact_title: 'Head of Engineering',
    contact_source: 'manual_entry',
    status: 'qualified',
    qualification_score: 95,
    technology_stack: 'PHP 8.0, WooCommerce',
    php2shell_risk_level: 'critical',
    notes: 'Unpatched PHP parser memory exposure',
    created_at: '2026-10-24T18:10:00Z',
    updated_at: '2026-10-24T18:10:00Z',
  },
]

const mockCampaigns: DiscoveryCampaign[] = [
  {
    id: 'camp-1',
    created_by_admin_id: 'admin-uuid-1',
    name: 'PHP2Shell Q4 Outreach',
    target_technology: 'PHP / Laravel / WordPress',
    target_industry: 'E-commerce & Logistics',
    search_query: 'php error disclosure stack trace',
    status: 'active',
    rate_limit_per_day: 50,
    discovered_leads_count: 14,
    contacted_leads_count: 5,
    converted_leads_count: 2,
    created_at: '2026-10-24T17:00:00Z',
    updated_at: '2026-10-24T17:00:00Z',
  },
]

const mockTemplates: OutreachTemplate[] = [
  {
    id: 'tmpl-1',
    name: 'PHP2Shell Proactive Security Advisory',
    category: 'vulnerability_alert',
    subject_template: 'URGENT: Proactive Security Assessment for {{company_name}}',
    body_template: 'Hello {{contact_name}}, PATCHORA detected vulnerability risks on {{domain}}.',
    is_approved_by_admin: true,
    created_at: '2026-10-24T17:00:00Z',
    updated_at: '2026-10-24T17:00:00Z',
  },
]

const mockDraft: OutreachDraft = {
  id: 'draft-1',
  lead_id: 'lead-1',
  template_id: 'tmpl-1',
  recipient_email: 'alice@acme-logistics.com',
  recipient_name: 'Alice Smith',
  subject: 'URGENT: Proactive Security Assessment for Acme Logistics',
  body: 'Hello Alice Smith, PATCHORA detected vulnerability risks on acme-logistics.com.\n\nTo opt out: https://patchora.io/api/leads/opt-out?token=test_tok',
  status: 'draft',
  delivery_provider: 'mock_outreach_delivery',
  created_at: '2026-10-24T18:05:00Z',
}

const mockSuppression: SuppressionEntry[] = [
  {
    id: 'sup-1',
    domain_or_email: 'optout-vendor.org',
    entry_type: 'domain',
    reason: 'CAN-SPAM unsubscribe request',
    opted_out_at: '2026-10-24T16:00:00Z',
  },
]

vi.mock('@/api/leads', () => ({
  getClientFinderStats: vi.fn().mockResolvedValue(mockStats),
  listLeads: vi.fn().mockResolvedValue(mockLeads),
  createLead: vi.fn().mockImplementation((payload) =>
    Promise.resolve({
      id: 'lead-new',
      ...payload,
      status: 'new',
      qualification_score: 50,
      php2shell_risk_level: payload.php2shell_risk_level || 'high',
      created_at: '2026-10-24T18:30:00Z',
      updated_at: '2026-10-24T18:30:00Z',
    })
  ),
  getLead: vi.fn().mockImplementation((id) => Promise.resolve(mockLeads.find((l) => l.id === id) || mockLeads[0])),
  updateLead: vi.fn().mockImplementation((id, payload) =>
    Promise.resolve({
      ...mockLeads[0],
      ...payload,
    })
  ),
  convertLead: vi.fn().mockImplementation((id) =>
    Promise.resolve({
      ...mockLeads[0],
      status: 'converted',
      attributed_website_id: 'web-converted-1',
    })
  ),
  listCampaigns: vi.fn().mockResolvedValue(mockCampaigns),
  createCampaign: vi.fn().mockImplementation((payload) =>
    Promise.resolve({
      id: 'camp-new',
      ...payload,
      status: 'active',
      discovered_leads_count: 0,
      contacted_leads_count: 0,
      converted_leads_count: 0,
      created_at: '2026-10-24T18:30:00Z',
      updated_at: '2026-10-24T18:30:00Z',
    })
  ),
  runCampaignDiscovery: vi.fn().mockResolvedValue(mockLeads),
  listOutreachTemplates: vi.fn().mockResolvedValue(mockTemplates),
  draftOutreach: vi.fn().mockResolvedValue(mockDraft),
  sendOutreach: vi.fn().mockResolvedValue({ ...mockDraft, status: 'sent', sent_at: '2026-10-24T18:35:00Z' }),
  listSuppressionList: vi.fn().mockResolvedValue(mockSuppression),
  addSuppression: vi.fn().mockImplementation((target, reason) =>
    Promise.resolve({
      id: 'sup-new',
      domain_or_email: target,
      entry_type: target.includes('@') ? 'email' : 'domain',
      reason: reason || 'manual_admin_suppression',
      opted_out_at: '2026-10-24T18:35:00Z',
    })
  ),
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

describe('AdminClientFinderPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders client finder header and real database overview metrics', async () => {
    renderWithProviders(<AdminClientFinderPage />)

    expect(await screen.findByText('Client Finder Automation & Lead Management')).toBeInTheDocument()
    expect(screen.getByText('Admin Exclusive')).toBeInTheDocument()

    // Metric numbers from mockStats
    expect(await screen.findByText('18')).toBeInTheDocument() // Total leads
    expect(screen.getByText('7')).toBeInTheDocument() // New leads
    expect(screen.getByText('12')).toBeInTheDocument() // PHP2Shell Risk
  })

  it('renders leads pipeline table with leads, scores, and status badges', async () => {
    renderWithProviders(<AdminClientFinderPage />)

    expect(await screen.findByText('Acme Logistics')).toBeInTheDocument()
    expect(screen.getByText('acme-logistics.com')).toBeInTheDocument()
    expect(screen.getByText('Beta Retail')).toBeInTheDocument()
    expect(screen.getByText('beta-retail.shop')).toBeInTheDocument()

    // Risk levels
    expect(screen.getByText('critical')).toBeInTheDocument()

    // Conversion button
    expect(screen.getAllByText('Convert').length).toBeGreaterThan(0)
  })

  it('supports tab navigation to Discovery Campaigns, Outreach, and Suppression List', async () => {
    renderWithProviders(<AdminClientFinderPage />)

    // Tab 2: Discovery Campaigns
    const campaignsTab = await screen.findByRole('button', { name: /Discovery Campaigns/i })
    fireEvent.click(campaignsTab)
    expect(await screen.findByText('PHP2Shell Q4 Outreach')).toBeInTheDocument()
    expect(screen.getByText('Run Discovery Job')).toBeInTheDocument()

    // Tab 3: Compliant Outreach & Templates
    const outreachTab = screen.getByRole('button', { name: /Compliant Outreach & Templates/i })
    fireEvent.click(outreachTab)
    expect(await screen.findByText('PHP2Shell Proactive Security Advisory')).toBeInTheDocument()
    expect(screen.getByText('CAN-SPAM & GDPR Enforcement')).toBeInTheDocument()

    // Tab 4: Suppression List
    const suppressionTab = screen.getByRole('button', { name: /Suppression List/i })
    fireEvent.click(suppressionTab)
    expect(await screen.findByText('optout-vendor.org')).toBeInTheDocument()
    expect(screen.getByText('CAN-SPAM unsubscribe request')).toBeInTheDocument()
  })

  it('converts an eligible lead into an active website target assessment', async () => {
    renderWithProviders(<AdminClientFinderPage />)

    expect(await screen.findByText('Acme Logistics')).toBeInTheDocument()

    const convertButtons = screen.getAllByText('Convert')
    fireEvent.click(convertButtons[0])

    await waitFor(() => {
      expect(screen.getByText(/converted to active website target assessment/i)).toBeInTheDocument()
    })
  })
})
