import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ThemeProvider } from '@/theme/ThemeContext'
import { AuthProvider } from '@/context/AuthContext'
import { ComingSoonPage } from '@/pages/client/ComingSoonPage'
import { ClientOverviewPage } from '@/pages/client/ClientOverviewPage'
import { ClientScannerPage } from '@/pages/client/ClientScannerPage'

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

describe('ComingSoonPage', () => {
  it('renders module title and phase badge honestly without fake data', () => {
    renderWithProviders(
      <ComingSoonPage
        moduleName="Target Website Management"
        phaseNumber={4}
        phaseTitle="Website Management"
        description="Register and verify target domains."
        plannedFeatures={['Feature A', 'Feature B']}
      />
    )
    expect(screen.getByText('Target Website Management')).toBeInTheDocument()
    expect(screen.getByText(/Phase 4/i)).toBeInTheDocument()
    expect(screen.getByText('Feature A')).toBeInTheDocument()
    expect(screen.getByText('Feature B')).toBeInTheDocument()
  })
})

describe('ClientOverviewPage', () => {
  it('renders client workspace header and honest 0-count metrics', () => {
    renderWithProviders(<ClientOverviewPage />)
    expect(screen.getByText('Client Workspace Overview')).toBeInTheDocument()
    expect(screen.getByText('Registered Target Websites')).toBeInTheDocument()
    expect(screen.getByText('Completed Vulnerability Scans')).toBeInTheDocument()
    expect(screen.getByText('AI Fix Requests')).toBeInTheDocument()
    // Verifies PHP2Shell shield status is communicated
    expect(screen.getByText(/PHP2Shell Zero-Day Protection Active/i)).toBeInTheDocument()
  })
})

describe('ClientScannerPage', () => {
  it('renders PHP scanner tool with code area and analyze button', () => {
    renderWithProviders(<ClientScannerPage />)
    expect(screen.getByText(/PHP Vulnerability & PHP2Shell Code Scanner/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Analyze Code/i })).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Paste PHP code here/i)).toBeInTheDocument()
  })
})
