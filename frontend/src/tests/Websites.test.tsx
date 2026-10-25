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
    
    expect(screen.getByRole('heading', { name: /Target Websites & Scope Management/i })).toBeInTheDocument()
    expect(screen.getByText(/Register, verify ownership, and explicitly authorize/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Add Target Website/i })).toBeInTheDocument()
  })

  it('opens registration modal with SSRF policy notice when button is clicked', async () => {
    renderWithProviders(<WebsitesListPage />)
    
    const registerBtn = screen.getByRole('button', { name: /Add Target Website/i })
    fireEvent.click(registerBtn)

    expect(screen.getByText('Register Target Website')).toBeInTheDocument()
    expect(screen.getByText(/SSRF prevention/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Friendly Target Name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Target URL/i)).toBeInTheDocument()
    expect(screen.getByText(/Initial Ownership Verification Method/i)).toBeInTheDocument()
  })
})

describe('AdminWebsitesPage (Phase 4)', () => {
  it('renders admin target directory and audit notice', async () => {
    renderWithProviders(<AdminWebsitesPage />)
    
    expect(screen.getByText(/Registered Website Targets Directory/i)).toBeInTheDocument()
    expect(screen.getByText(/Global view of all client registered targets/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Search targets by domain, name, or owner ID/i)).toBeInTheDocument()
  })
})
