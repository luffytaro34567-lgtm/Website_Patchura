import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ThemeProvider } from '@/theme/ThemeContext'
import { AuthProvider } from '@/context/AuthContext'
import { ClientDeploymentsPage } from '@/pages/client/ClientDeploymentsPage'
import { AdminDeploymentsPage } from '@/pages/admin/AdminDeploymentsPage'
import {
  AdminDeploymentOverview,
  CliInstructions,
  DeploymentRecord,
  DeploymentTarget,
  RepositoryConnection,
} from '@/types/deployment'
import { RemediationSessionSummary } from '@/types/remediation'

const mockRepo: RepositoryConnection = {
  id: 'repo-1',
  provider: 'github',
  repo_name: 'acme/storefront',
  default_branch: 'main',
  masked_token: 'ghp_***4a2b',
  is_active: true,
  created_at: '2026-10-24T18:00:00Z',
  updated_at: '2026-10-24T18:00:00Z',
}

const mockApprovedSession: RemediationSessionSummary = {
  id: 'sess-1',
  finding_id: 'find-1',
  finding_title: 'Insecure PHP Error Disclosure',
  finding_severity: 'high',
  website_domain: 'store.acme.com',
  target_filename: 'error_handler.php',
  language: 'php',
  status: 'approved',
  ai_provider: 'deterministic_rules',
  test_status: 'passed',
  approval_status: 'approved',
  created_at: '2026-10-24T18:00:00Z',
}

const mockHistory: DeploymentRecord = {
  id: 'dep-1',
  session_id: 'sess-1',
  website_id: 'web-1',
  environment: 'staging',
  status: 'staged',
  git_branch: 'patchora/staging-sess-1',
  git_commit_sha: 'a1b2c3d4e5f6',
  pull_request_url: 'https://github.com/acme/storefront/pull/42',
  pull_request_number: 42,
  pre_deployment_test_status: 'passed',
  created_at: '2026-10-24T18:15:00Z',
}

const mockAdminOverview: AdminDeploymentOverview = {
  total_connected_repositories: 5,
  total_pull_requests_dispatched: 14,
  total_staging_deployments: 12,
  total_production_deployments: 2,
  production_deployments_enabled: false,
  total_rollbacks_executed: 1,
}

const mockCli: CliInstructions = {
  session_id: 'sess-1',
  target_filename: 'error_handler.php',
  patch_filename: 'error_handler.php_security_fix.patch',
  branch_name: 'patchora/patch-sess-1',
  cli_commands: ['git apply fix.patch'],
  git_apply_script: 'git fetch origin\ngit checkout -b patchora/patch-sess-1\ngit apply fix.patch',
  rollback_script: 'git checkout error_handler.php',
  security_notice: 'Always test in staging first.',
}

vi.mock('@/api/deployment', () => ({
  listRepositories: vi.fn().mockResolvedValue([mockRepo]),
  connectRepository: vi.fn().mockResolvedValue(mockRepo),
  disconnectRepository: vi.fn().mockResolvedValue(undefined),
  listDeploymentTargets: vi.fn().mockResolvedValue([]),
  createDeploymentTarget: vi.fn(),
  getDeploymentHistory: vi.fn().mockResolvedValue([mockHistory]),
  createPullRequest: vi.fn().mockResolvedValue(mockHistory),
  deployToStaging: vi.fn().mockResolvedValue(mockHistory),
  deployToProduction: vi.fn().mockResolvedValue({ ...mockHistory, environment: 'production', status: 'deployed' }),
  rollbackDeployment: vi.fn().mockResolvedValue({ ...mockHistory, status: 'rolled_back' }),
  getCliInstructions: vi.fn().mockResolvedValue(mockCli),
  adminGetDeploymentOverview: vi.fn().mockResolvedValue(mockAdminOverview),
}))

vi.mock('@/api/remediations', () => ({
  listMyRemediations: vi.fn().mockResolvedValue([mockApprovedSession]),
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

describe('ClientDeploymentsPage (Phase 9)', () => {
  it('renders page header, approved patch cards, and connected repo', async () => {
    renderWithProviders(<ClientDeploymentsPage />)

    expect(screen.getByText(/Source-Code Integration & Deployment/i)).toBeInTheDocument()
    expect(await screen.findByText('error_handler.php')).toBeInTheDocument()
    expect(screen.getByText('Insecure PHP Error Disclosure')).toBeInTheDocument()
    expect(screen.getByText('acme/storefront')).toBeInTheDocument()
    expect(screen.getByText('ghp_***4a2b')).toBeInTheDocument()
  })

  it('renders deployment history table with PR link and rollback button', async () => {
    renderWithProviders(<ClientDeploymentsPage />)

    expect(await screen.findByText('PR #42')).toBeInTheDocument()
    expect(screen.getByText('a1b2c3d')).toBeInTheDocument()
    expect(screen.getByText('↺ Rollback')).toBeInTheDocument()
  })

  it('opens connect repo modal when button is clicked', async () => {
    renderWithProviders(<ClientDeploymentsPage />)

    const connectBtn = screen.getByRole('button', { name: /\+ Connect GitHub Repository/i })
    fireEvent.click(connectBtn)

    expect(screen.getByText(/Connect GitHub Repository/i)).toBeInTheDocument()
    expect(screen.getByText(/GitHub Personal Access Token/i)).toBeInTheDocument()
  })
})

describe('AdminDeploymentsPage (Phase 9)', () => {
  it('renders admin deployment telemetry and branch protection policy', async () => {
    renderWithProviders(<AdminDeploymentsPage />)

    expect(screen.getByText(/DevSecOps Deployments & Git Integration Oversight/i)).toBeInTheDocument()
    expect(await screen.findByText('14')).toBeInTheDocument() // PRs
    expect(screen.getByText('12')).toBeInTheDocument() // Staging
    expect(screen.getByText(/Protected Default Branch/i)).toBeInTheDocument()
  })
})
