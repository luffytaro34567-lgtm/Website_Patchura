import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { ThemeProvider } from '@/theme/ThemeContext'
import { AuthProvider } from '@/context/AuthContext'
import { ClientScansPage } from '@/pages/client/ClientScansPage'
import { ScanDetailsPage } from '@/pages/client/ScanDetailsPage'
import { AdminScansPage } from '@/pages/admin/AdminScansPage'
import { Scan } from '@/types/scan'

const mockScan: Scan = {
  id: 'scan-1234',
  website_id: 'site-5678',
  user_id: 'user-9999',
  profile: 'php_deep',
  status: 'completed',
  progress_percent: 100,
  target_url: 'https://test-target.com',
  target_domain: 'test-target.com',
  started_at: '2026-10-24T16:00:00Z',
  completed_at: '2026-10-24T16:00:05Z',
  duration_seconds: 5.2,
  is_cancelled: false,
  total_findings: 1,
  critical_count: 1,
  high_count: 0,
  medium_count: 0,
  low_count: 0,
  info_count: 0,
  created_at: '2026-10-24T16:00:00Z',
  findings: [
    {
      id: 'finding-001',
      scan_id: 'scan-1234',
      website_id: 'site-5678',
      title: 'PHP2Shell Memory Corruption Exposure Risk',
      severity: 'critical',
      category: 'PHP2Shell Protection',
      description: 'Verbose error handler leaking corrupt memory structures.',
      evidence: 'X-Powered-By: PHP/8.1.0\nFatal error: memory fault in zend_error_cb',
      remediation: 'Disable display_errors and apply security patches for CVE-2026-109618.',
      cwe_id: 'CWE-209',
      cvss_score: 9.2,
      target_url: 'https://test-target.com/?__bh_test_probe_array[]=1',
      created_at: '2026-10-24T16:00:04Z',
    },
  ],
}

vi.mock('@/api/scans', () => ({
  listScans: vi.fn().mockResolvedValue([mockScan]),
  createScan: vi.fn().mockResolvedValue(mockScan),
  getScanDetails: vi.fn().mockResolvedValue(mockScan),
  cancelScan: vi.fn(),
  exportScanSummary: vi.fn(),
  adminListScans: vi.fn().mockResolvedValue([mockScan]),
  adminCancelScan: vi.fn(),
}))

vi.mock('@/api/websites', () => ({
  listWebsites: vi.fn().mockResolvedValue([
    {
      id: 'site-5678',
      name: 'Test Target Site',
      target_url: 'https://test-target.com',
      domain: 'test-target.com',
      verification_status: 'verified',
      authorization: {
        is_authorized: true,
        is_revoked: false,
      },
      is_suspended_by_admin: false,
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

describe('ClientScansPage (Phase 5)', () => {
  it('renders scans page header and Start Authorized Scan button', async () => {
    renderWithProviders(<ClientScansPage />)

    expect(screen.getByText('Vulnerability Scans')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Start Authorized Scan/i })).toBeInTheDocument()
  })

  it('opens start scan modal with profile selection when clicked', async () => {
    renderWithProviders(<ClientScansPage />)

    const btn = screen.getByRole('button', { name: /Start Authorized Scan/i })
    fireEvent.click(btn)

    expect(screen.getByText('Launch Authorized Scan')).toBeInTheDocument()
    expect(screen.getByText(/1\. Select Verified Target Website/i)).toBeInTheDocument()
    expect(screen.getByText(/Standard Web Application Assessment/i)).toBeInTheDocument()
    expect(screen.getByText(/Targeted PHP & PHP2Shell Assessment/i)).toBeInTheDocument()
    expect(screen.getByText(/Non-Destructive Scanning Policy/i)).toBeInTheDocument()
  })
})

describe('ScanDetailsPage (Phase 5)', () => {
  it('renders scan findings and concrete evidence', async () => {
    render(
      <ThemeProvider>
        <AuthProvider>
          <MemoryRouter initialEntries={['/dashboard/scans/scan-1234']}>
            <Routes>
              <Route path="/dashboard/scans/:scanId" element={<ScanDetailsPage />} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      </ThemeProvider>
    )

    // Wait for mock data
    expect(await screen.findByText('test-target.com')).toBeInTheDocument()
    expect(screen.getByText(/PHP2Shell Memory Corruption Exposure Risk/i)).toBeInTheDocument()
    expect(screen.getByText(/Stored Proof & Evidence/i)).toBeInTheDocument()
    expect(screen.getByText(/CVSS 9.2/i)).toBeInTheDocument()
    expect(screen.getByText(/CVE-2026-109618 \/ 19/i)).toBeInTheDocument()
  })
})

describe('AdminScansPage (Phase 5)', () => {
  it('renders admin scan oversight table', async () => {
    renderWithProviders(<AdminScansPage />)

    expect(screen.getByText('Global Scan Operations & Oversight')).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Search domain, scan ID, or user ID/i)).toBeInTheDocument()
  })
})
