import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ThemeProvider } from '@/theme/ThemeContext'
import { AuthProvider } from '@/context/AuthContext'
import { ClientRemediationsPage } from '@/pages/client/ClientRemediationsPage'
import { AdminRemediationsPage } from '@/pages/admin/AdminRemediationsPage'
import { RemediationSession, RemediationSessionSummary, AdminRemediationStats } from '@/types/remediation'

const mockSummary: RemediationSessionSummary = {
  id: 'sess-123',
  finding_id: 'find-456',
  finding_title: 'Missing Strict-Transport-Security Header',
  finding_severity: 'high',
  website_domain: 'example.com',
  target_filename: 'index.php',
  language: 'php',
  status: 'test_passed',
  ai_provider: 'deterministic_rules',
  test_status: 'passed',
  approval_status: 'pending',
  created_at: '2026-10-24T18:00:00Z',
}

const mockDetail: RemediationSession = {
  ...mockSummary,
  scan_id: 'scan-789',
  website_id: 'web-101',
  user_id: 'usr-1',
  input_method: 'snippet',
  original_code: '<?php echo "Hello"; ?>',
  proposed_diff: '--- a/index.php\n+++ b/index.php\n@@ -1 +1,2 @@\n+header("Strict-Transport-Security: max-age=63072000;");\n <?php echo "Hello"; ?>',
  patched_code: '<?php\nheader("Strict-Transport-Security: max-age=63072000;");\necho "Hello";\n?>',
  explanation: 'Added HSTS header to prevent SSL stripping.',
  security_warnings: 'Ensure HTTPS is active on domain.',
  php2shell_mitigation_notes: null,
  confidence_score: 0.98,
  test_status: 'passed',
  test_output: '=== PATCHORA Isolated Patch Verification Runner ===\nVERIFICATION RESULT: PASSED',
  tested_at: '2026-10-24T18:01:00Z',
  approval_status: 'pending',
  approval_notes: null,
  approved_at: null,
  client_consent_given: true,
  updated_at: '2026-10-24T18:01:00Z',
}

const mockAdminStats: AdminRemediationStats = {
  total_remediations: 12,
  approved_patches: 10,
  rejected_patches: 1,
  tests_passed: 11,
  tests_failed: 1,
  pending_approval: 1,
  ai_provider_active: 'Deterministic Security Rules Engine (AST Analyzer)',
}

vi.mock('@/api/remediations', () => ({
  listMyRemediations: vi.fn().mockResolvedValue([mockSummary]),
  getRemediation: vi.fn().mockResolvedValue(mockDetail),
  createRemediation: vi.fn().mockResolvedValue(mockDetail),
  testPatch: vi.fn().mockResolvedValue({
    session_id: 'sess-123',
    test_status: 'passed',
    passed: true,
    diagnostics: 'VERIFICATION RESULT: PASSED',
    tested_at: '2026-10-24T18:02:00Z',
  }),
  approvePatch: vi.fn().mockResolvedValue({
    ...mockDetail,
    approval_status: 'approved',
    status: 'approved',
    approved_at: '2026-10-24T18:03:00Z',
  }),
  rejectPatch: vi.fn().mockResolvedValue({
    ...mockDetail,
    approval_status: 'rejected',
    status: 'rejected',
  }),
  downloadPatchFile: vi.fn(),
  downloadPatchedCodeFile: vi.fn(),
  adminGetRemediationStats: vi.fn().mockResolvedValue(mockAdminStats),
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

describe('ClientRemediationsPage (Phase 8)', () => {
  it('renders page header, session sidebar, and active patch details', async () => {
    renderWithProviders(<ClientRemediationsPage />)

    expect(screen.getByText(/AI Bug-Fixing & Remediation Engine/i)).toBeInTheDocument()
    expect(await screen.findByText('index.php')).toBeInTheDocument()
    expect(screen.getByText(/Missing Strict-Transport-Security Header/i)).toBeInTheDocument()
    expect(screen.getByText(/Isolated Static Sandbox Verification: PASSED/i)).toBeInTheDocument()
    expect(screen.getByText(/Explicitly Approve Patch/i)).toBeInTheDocument()
  })

  it('renders unified diff view with patch lines', async () => {
    renderWithProviders(<ClientRemediationsPage />)

    expect(await screen.findByText(/Strict-Transport-Security/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Download .patch File/i })).toBeInTheDocument()
  })

  it('opens request AI fix modal when button is clicked', async () => {
    renderWithProviders(<ClientRemediationsPage />)

    const fixBtn = screen.getByRole('button', { name: /\+ Request AI Fix/i })
    fireEvent.click(fixBtn)

    expect(screen.getByText(/Request AI Security Remediation/i)).toBeInTheDocument()
    expect(screen.getByText(/Target Finding ID/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Generate Patch/i })).toBeInTheDocument()
  })
})

describe('AdminRemediationsPage (Phase 8)', () => {
  it('renders admin remediation telemetry and AST sandbox details', async () => {
    renderWithProviders(<AdminRemediationsPage />)

    expect(screen.getByText(/AI Bug-Fixing & Remediation Oversight/i)).toBeInTheDocument()
    expect(await screen.findByText('12')).toBeInTheDocument()
    expect(screen.getByText('10')).toBeInTheDocument()
    expect(screen.getByText(/Zero-Execution Policy/i)).toBeInTheDocument()
  })
})
