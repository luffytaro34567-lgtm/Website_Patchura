import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ThemeProvider } from '@/theme/ThemeContext'
import { AuthProvider } from '@/context/AuthContext'
import { LoginPage } from '@/pages/LoginPage'
import { RegisterPage } from '@/pages/RegisterPage'

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

describe('LoginPage', () => {
  it('renders login form with inputs and sign in button', () => {
    renderWithProviders(<LoginPage />)
    expect(screen.getByLabelText(/Username or Email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Sign In/i })).toBeInTheDocument()
  })

  it('renders link to registration', () => {
    renderWithProviders(<LoginPage />)
    expect(screen.getByText(/Register here/i)).toBeInTheDocument()
  })

  it('shows error when submitted empty', async () => {
    renderWithProviders(<LoginPage />)
    const submitBtn = screen.getByRole('button', { name: /Sign In/i })
    fireEvent.click(submitBtn)
    expect(await screen.findByRole('alert')).toBeInTheDocument()
  })
})

describe('RegisterPage', () => {
  it('renders client registration form fields', () => {
    renderWithProviders(<RegisterPage />)
    expect(screen.getByLabelText(/^Username/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Work Email Address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^Password$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Confirm Password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Create Client Account/i })).toBeInTheDocument()
  })

  it('displays the password security policy checklist', () => {
    renderWithProviders(<RegisterPage />)
    expect(screen.getByText(/Password Security Policy:/i)).toBeInTheDocument()
    expect(screen.getByText(/At least 8 characters/i)).toBeInTheDocument()
    expect(screen.getByText(/At least one uppercase letter/i)).toBeInTheDocument()
    expect(screen.getByText(/At least one numeric digit/i)).toBeInTheDocument()
    expect(screen.getByText(/At least one special character/i)).toBeInTheDocument()
    expect(screen.getByText(/Passwords match/i)).toBeInTheDocument()
  })
})
