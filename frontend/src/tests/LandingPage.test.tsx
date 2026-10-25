import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ThemeProvider } from '@/theme/ThemeContext'
import { LandingPage } from '@/pages/LandingPage'

function renderPage() {
  return render(
    <ThemeProvider>
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>
    </ThemeProvider>
  )
}

describe('LandingPage', () => {
  it('renders the hero heading', () => {
    renderPage()
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
  })

  it('renders the features section', () => {
    renderPage()
    expect(screen.getByText('Platform Capabilities')).toBeInTheDocument()
  })

  it('renders PHP2Shell critical vulnerability coverage', () => {
    renderPage()
    expect(screen.getByText(/PHP2Shell & Critical CVE Mitigation/i)).toBeInTheDocument()
    expect(screen.getByText(/PHP 5.4 - 8.5/i)).toBeInTheDocument()
  })

  it('renders the how it works section', () => {
    renderPage()
    expect(screen.getByText('Workflow')).toBeInTheDocument()
  })

  it('does not display any fabricated scan results', () => {
    renderPage()
    // The page must not claim a scan has completed
    const bodyText = document.body.textContent || ''
    expect(bodyText).not.toMatch(/scan complete/i)
    expect(bodyText).not.toMatch(/vulnerabilities found: \d+/i)
  })

  it('renders Get Started links', () => {
    renderPage()
    const links = screen.getAllByText(/Get Started/i)
    expect(links.length).toBeGreaterThan(0)
  })
})
