import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ThemeProvider } from '@/theme/ThemeContext'
import { AuthProvider } from '@/context/AuthContext'
import { Navbar } from '@/components/shared/Navbar'

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

describe('Navbar', () => {
  it('renders the brand name', () => {
    renderWithProviders(<Navbar />)
    expect(screen.getByText(/PATCHORA/i)).toBeInTheDocument()
  })

  it('renders navigation links', () => {
    renderWithProviders(<Navbar />)
    expect(screen.getByText('Features')).toBeInTheDocument()
    expect(screen.getByText('How It Works')).toBeInTheDocument()
  })

  it('renders login and get started links when unauthenticated', () => {
    renderWithProviders(<Navbar />)
    const loginLinks = screen.getAllByText(/Log in/i)
    expect(loginLinks.length).toBeGreaterThan(0)
    const getStartedLinks = screen.getAllByText(/Get Started/i)
    expect(getStartedLinks.length).toBeGreaterThan(0)
  })

  it('has accessible nav landmark', () => {
    renderWithProviders(<Navbar />)
    expect(screen.getByRole('navigation')).toBeInTheDocument()
  })
})
