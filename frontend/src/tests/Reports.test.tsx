import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { ThemeProvider } from '@/theme/ThemeContext'
import { AuthProvider } from '@/context/AuthContext'
import { ReportsListPage } from '@/pages/client/ReportsListPage'
import { DetailedReportPage } from '@/pages/client/DetailedReportPage'
import { AdminReportsPage } from '@/pages/admin/AdminReportsPage'
import { DetailedReport, ReportEntitlementStatus } from '@/types/report'

const mockLockedStatus: ReportEntitlementStatus = {
  scan_id: 'scan-locked-1',
  has_entitlement: false,
  can_purchase: true,
  pricing: {
    product_name: 'Comprehensive Vulnerability & Remediation Report',
    price: 49.0,
    currency: 'USD',
    description: 'Executive and developer-ready vulnerability assessment report.',
    features: ['Executive Risk Summary', 'CVSS v3.1 Matrix', 'Stored Evidence Proofs'],
  },
  entitlement: null,
  active_order: null,
}

const mockUnlockedReport: DetailedReport = {
  id: 'doc-123',
  scan_id: 'scan-unlocked-1',
  website_id: 'site-1',
  title: 'Vulnerability Assessment & Security Audit — secure.company.com',
  target_url: 'https://secure.company.com',
  target_domain: 'secure.company.com',
  profile: 'php_deep',
  executive_summary: 'Comprehensive audit revealing 1 critical zero-day vulnerability.',
  overall_risk_score: 9.2,
  overall_posture: 'CRITICAL RISK (IMMEDIATE REMEDIATION REQUIRED)',
  has_php2shell_finding: true,
  php2shell_posture: 'CRITICAL: Unhandled Memory Fault Exposure (CVE-2026-109618 / 19)',
  generated_at: '2026-10-24T16:00:00Z',
  version: 1,
  total_findings: 1,
  severity_breakdown: { critical: 1, high: 0, medium: 0, low: 0, info: 0 },
  findings: [
    {
      id: 'f-1',
      scan_id: 'scan-unlocked-1',
      website_id: 'site-1',
      title: 'PHP2Shell Memory Corruption Exposure Risk',
      severity: 'critical',
      category: 'PHP2Shell Protection',
      description: 'Verbose error handler leaking corrupt memory structures.',
      evidence: 'X-Powered-By: PHP/8.1.0\nFatal error: memory fault in zend_error_cb',
      remediation: 'Disable display_errors and apply security patches for CVE-2026-109618.',
      cwe_id: 'CWE-209',
      cvss_score: 9.2,
      target_url: 'https://secure.company.com/?__bh_test_probe_array[]=1',
      created_at: '2026-10-24T16:00:04Z',
    },
  ],
  html_content: '<html><body>Mock HTML Report</body></html>',
}

vi.mock('@/api/reports', () => ({
  listMyReports: vi.fn().mockResolvedValue([]),
  getReportStatus: vi.fn().mockImplementation((scanId: string) => {
    if (scanId === 'scan-unlocked-1') {
      return Promise.resolve({
        scan_id: scanId,
        has_entitlement: true,
        can_purchase: false,
        pricing: mockLockedStatus.pricing,
        entitlement: { is_active: true, granted_by: 'order_checkout' },
      })
    }
    return Promise.resolve(mockLockedStatus)
  }),
  getDetailedReport: vi.fn().mockResolvedValue(mockUnlockedReport),
  createReportOrder: vi.fn().mockResolvedValue({
    id: 'ord-123',
    status: 'pending',
    amount: 49.0,
    currency: 'USD',
  }),
  completeReportOrder: vi.fn().mockResolvedValue({
    id: 'ord-123',
    status: 'completed',
  }),
  downloadReportHtml: vi.fn(),
  adminListReportOrders: vi.fn().mockResolvedValue([
    {
      id: 'ord-123',
      scan_id: 'scan-locked-1',
      user_id: 'user-456',
      product_name: 'Comprehensive Vulnerability & Remediation Report',
      amount: 49.0,
      currency: 'USD',
      status: 'completed',
      payment_method: 'dev_checkout',
      transaction_reference: 'ORD-BH-TEST1234',
      created_at: '2026-10-24T16:00:00Z',
    },
  ]),
  adminGrantEntitlement: vi.fn().mockResolvedValue({ is_active: true }),
}))

vi.mock('@/api/scans', () => ({
  listScans: vi.fn().mockResolvedValue([
    {
      id: 'scan-locked-1',
      target_domain: 'example.com',
      target_url: 'https://example.com',
      profile: 'standard',
      status: 'completed',
      critical_count: 1,
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

describe('ReportsListPage (Phase 6)', () => {
  it('renders reports directory and $49 pricing teaser', async () => {
    renderWithProviders(<ReportsListPage />)

    expect(screen.getByText(/Security & Vulnerability Reports/i)).toBeInTheDocument()
    expect(screen.getByText(/Unlock Comprehensive Executive & Technical Reports/i)).toBeInTheDocument()
    expect(await screen.findByText('example.com')).toBeInTheDocument()
    expect(screen.getByText(/Report Available \(\$49\)/i)).toBeInTheDocument()
  })
})

describe('DetailedReportPage Locked View (Phase 6)', () => {
  it('renders locked banner, price card, and opens checkout modal', async () => {
    render(
      <ThemeProvider>
        <AuthProvider>
          <MemoryRouter initialEntries={['/dashboard/reports/scan-locked-1']}>
            <Routes>
              <Route path="/dashboard/reports/:scanId" element={<DetailedReportPage />} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      </ThemeProvider>
    )

    expect(await screen.findByText(/Detailed Report Locked/i)).toBeInTheDocument()
    expect(screen.getByText('$49.00')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Unlock Report/i })).toBeInTheDocument()

    // Click Unlock Report
    fireEvent.click(screen.getByRole('button', { name: /Unlock Report/i }))
    expect(screen.getByText('Report Access Checkout')).toBeInTheDocument()
    expect(screen.getByText(/Payment Gateway Verification Workflow/i)).toBeInTheDocument()
  })
})

describe('DetailedReportPage Entitled View (Phase 6)', () => {
  it('renders executive summary, risk score, posture, and findings evidence', async () => {
    render(
      <ThemeProvider>
        <AuthProvider>
          <MemoryRouter initialEntries={['/dashboard/reports/scan-unlocked-1']}>
            <Routes>
              <Route path="/dashboard/reports/:scanId" element={<DetailedReportPage />} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      </ThemeProvider>
    )

    expect(await screen.findByText(/Entitlement Active/i)).toBeInTheDocument()
    expect(screen.getByText(/Overall Risk Score/i)).toBeInTheDocument()
    expect(screen.getByText('9.2')).toBeInTheDocument()
    expect(screen.getByText(/PHP2Shell Zero-Day Posture/i)).toBeInTheDocument()
    expect(screen.getByText(/PHP2Shell Memory Corruption Exposure Risk/i)).toBeInTheDocument()
    expect(screen.getByText(/Stored Proof & Evidence/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Download Printable Report/i })).toBeInTheDocument()
  })
})

describe('AdminReportsPage (Phase 6)', () => {
  it('renders admin report orders and reference IDs', async () => {
    renderWithProviders(<AdminReportsPage />)

    expect(screen.getByText(/Report Orders & Entitlement Administration/i)).toBeInTheDocument()
    expect(await screen.findByText('ORD-BH-TEST1234')).toBeInTheDocument()
    expect(screen.getByText('$49.00 USD')).toBeInTheDocument()
  })
})
