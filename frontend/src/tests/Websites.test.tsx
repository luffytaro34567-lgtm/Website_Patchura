import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ThemeProvider } from '@/theme/ThemeContext'
import { AuthProvider } from '@/context/AuthContext'
import { WebsitesListPage } from '@/pages/client/WebsitesListPage'
import { AdminWebsitesPage } from '@/pages/admin/AdminWebsitesPage'

// Mock api/websites to avoid network calls
vi.mock('@/api/websites', () => ({
  listWebsites: vi.fn().mockResolvedValue([]),
  createWebsite: vi.fn(),
  getWebsite: vi.fn(),
  verifyWebsite: vi.fn(),
  authorizeWebsiteScan: vi.fn(),
  revokeWebsiteAuthorization: vi.fn(),
  updateVerificationMethod: vi.fn(),
  deleteWebsite: vi.fn(),
  adminListWebsites: vi.fn().mockResolvedValue([]),
  adminSuspendWebsite: vi.fn(),
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

describe('WebsitesListPage (Phase 4)', () => {
  it('renders target websites header and register target button', async () => {
    renderWithProviders(<WebsitesListPage />)
    
    expect(screen.getByText('Target Websites')).toBeInTheDocument()
    expect(screen.getByText(/Register, verify ownership, and explicitly authorize vulnerability scans/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Register Target/i })).toBeInTheDocument()
  })

  it('opens registration modal with SSRF policy notice when button is clicked', async () => {
    renderWithProviders(<WebsitesListPage />)
    
    const registerBtn = screen.getByRole('button', { name: /Register Target/i })
    fireEvent.click(registerBtn)

    expect(screen.getByText('Register New Target Website')).toBeInTheDocument()
    expect(screen.getByText(/Restricted Target Policy \(SSRF Prevention\)/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Website Name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Target URL/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Verification Method/i)).toBeInTheDocument()
  })
})

describe('AdminWebsitesPage (Phase 4)', () => {
  it('renders admin target directory and audit notice', async () => {
    renderWithProviders(<AdminWebsitesPage />)
    
    expect(screen.getByText('Target Websites Directory')).toBeInTheDocument()
    expect(screen.getByText(/Audit and manage all registered client target domains/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Search target URL or client email/i)).toBeInTheDocument()
  })
})
