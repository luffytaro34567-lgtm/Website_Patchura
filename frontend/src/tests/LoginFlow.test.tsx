import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route, useLocation } from 'react-router-dom'
import { AuthProvider, useAuth } from '@/context/AuthContext'
import { LoginPage } from '@/pages/LoginPage'
import * as authApi from '@/api/auth'
import { getApiAccessToken } from '@/api/client'
import { User } from '@/types/auth'

// Helper component to display current path for routing verification
function LocationDisplay() {
  const location = useLocation()
  return <div data-testid="location-display">{location.pathname}</div>
}

function DummyDashboard() {
  return (
    <div>
      <LocationDisplay />
      <h1>Client Dashboard</h1>
    </div>
  )
}

function DummyAdminDashboard() {
  return (
    <div>
      <LocationDisplay />
      <h1>Admin Dashboard</h1>
    </div>
  )
}

function DummyScanPage() {
  return (
    <div>
      <LocationDisplay />
      <h1>Scan Details</h1>
    </div>
  )
}

describe('Login Flow End-to-End Regression Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('successful client login sets token, localStorage, and redirects to /dashboard', async () => {
    const mockUser: User = {
      id: 'client-1',
      username: 'client_eva',
      email: 'eva@example.com',
      role: 'client',
      is_active: true,
      created_at: new Date().toISOString(),
    }

    vi.spyOn(authApi, 'loginUser').mockResolvedValueOnce({
      access_token: 'mock-client-access-token',
      refresh_token: 'mock-client-refresh-token',
      token_type: 'bearer',
      expires_in: 900,
      user: mockUser,
    })

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/login']}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/dashboard" element={<DummyDashboard />} />
            <Route path="/admin/dashboard" element={<DummyAdminDashboard />} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    )

    fireEvent.change(screen.getByLabelText(/Username or Email/i), {
      target: { value: 'client_eva' },
    })
    fireEvent.change(screen.getByLabelText(/^Password$/i), {
      target: { value: 'Password123!' },
    })
    fireEvent.click(screen.getByRole('button', { name: /Sign In/i }))

    await waitFor(() => {
      expect(screen.getByTestId('location-display')).toHaveTextContent('/dashboard')
    })

    expect(getApiAccessToken()).toBe('mock-client-access-token')
    expect(localStorage.getItem('bh_refresh_token')).toBe('mock-client-refresh-token')
  })

  it('successful admin login redirects to /admin/dashboard', async () => {
    const mockAdmin: User = {
      id: 'admin-1',
      username: 'admin_root',
      email: 'admin@patchora.com',
      role: 'admin',
      is_active: true,
      created_at: new Date().toISOString(),
    }

    vi.spyOn(authApi, 'loginUser').mockResolvedValueOnce({
      access_token: 'mock-admin-access-token',
      refresh_token: 'mock-admin-refresh-token',
      token_type: 'bearer',
      expires_in: 900,
      user: mockAdmin,
    })

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/login']}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/dashboard" element={<DummyDashboard />} />
            <Route path="/admin/dashboard" element={<DummyAdminDashboard />} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    )

    fireEvent.change(screen.getByLabelText(/Username or Email/i), {
      target: { value: 'admin_root' },
    })
    fireEvent.change(screen.getByLabelText(/^Password$/i), {
      target: { value: 'AdminPass123!' },
    })
    fireEvent.click(screen.getByRole('button', { name: /Sign In/i }))

    await waitFor(() => {
      expect(screen.getByTestId('location-display')).toHaveTextContent('/admin/dashboard')
    })
  })

  it('redirects to original target path when coming from protected route', async () => {
    const mockUser: User = {
      id: 'client-2',
      username: 'client_david',
      email: 'david@example.com',
      role: 'client',
      is_active: true,
      created_at: new Date().toISOString(),
    }

    vi.spyOn(authApi, 'loginUser').mockResolvedValueOnce({
      access_token: 'mock-token',
      refresh_token: 'mock-refresh',
      token_type: 'bearer',
      expires_in: 900,
      user: mockUser,
    })

    render(
      <AuthProvider>
        <MemoryRouter
          initialEntries={[
            { pathname: '/login', state: { from: { pathname: '/scans/scan-xyz' } } },
          ]}
        >
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/scans/scan-xyz" element={<DummyScanPage />} />
            <Route path="/dashboard" element={<DummyDashboard />} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    )

    fireEvent.change(screen.getByLabelText(/Username or Email/i), {
      target: { value: 'client_david' },
    })
    fireEvent.change(screen.getByLabelText(/^Password$/i), {
      target: { value: 'Password123!' },
    })
    fireEvent.click(screen.getByRole('button', { name: /Sign In/i }))

    await waitFor(() => {
      expect(screen.getByTestId('location-display')).toHaveTextContent('/scans/scan-xyz')
    })
  })

  it('displays safe error message when credentials are invalid and stays on /login', async () => {
    const err: any = new Error('Request failed with status code 401')
    err.userMessage = 'Invalid username/email or password.'
    vi.spyOn(authApi, 'loginUser').mockRejectedValueOnce(err)

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/login']}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/dashboard" element={<DummyDashboard />} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    )

    fireEvent.change(screen.getByLabelText(/Username or Email/i), {
      target: { value: 'unknown_user' },
    })
    fireEvent.change(screen.getByLabelText(/^Password$/i), {
      target: { value: 'WrongPassword123!' },
    })
    fireEvent.click(screen.getByRole('button', { name: /Sign In/i }))

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('Invalid username/email or password.')
    expect(screen.queryByTestId('location-display')).not.toBeInTheDocument()
  })

  it('displays friendly message when network connection fails or Render sleeps', async () => {
    const netErr: any = new Error('Network Error')
    netErr.userMessage =
      'Unable to connect to server. The backend may be starting up or sleeping on Render. Please retry shortly.'
    vi.spyOn(authApi, 'loginUser').mockRejectedValueOnce(netErr)

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/login']}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    )

    fireEvent.change(screen.getByLabelText(/Username or Email/i), {
      target: { value: 'any_user' },
    })
    fireEvent.change(screen.getByLabelText(/^Password$/i), {
      target: { value: 'Password123!' },
    })
    fireEvent.click(screen.getByRole('button', { name: /Sign In/i }))

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent(/Unable to connect to server/i)
  })

  it('displays rate limit error message when 429 occurs', async () => {
    const rateLimitErr: any = new Error('Rate limit exceeded')
    rateLimitErr.userMessage = 'Too many requests. Please wait a moment before trying again.'
    vi.spyOn(authApi, 'loginUser').mockRejectedValueOnce(rateLimitErr)

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/login']}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    )

    fireEvent.change(screen.getByLabelText(/Username or Email/i), {
      target: { value: 'rate_limited_user' },
    })
    fireEvent.change(screen.getByLabelText(/^Password$/i), {
      target: { value: 'Password123!' },
    })
    fireEvent.click(screen.getByRole('button', { name: /Sign In/i }))

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent(/Too many requests/i)
  })
})
