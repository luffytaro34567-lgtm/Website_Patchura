import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  apiClient,
  normalizeApiBaseUrl,
  resolveApiBaseUrl,
  setApiAccessToken,
  getApiAccessToken,
  PRODUCTION_API_BASE_URL,
} from '@/api/client'
import { loginUser } from '@/api/auth'

describe('API URL Construction & Normalization', () => {
  it('normalizes URLs by stripping trailing slashes', () => {
    expect(normalizeApiBaseUrl('https://patchura-backend.onrender.com/')).toBe(
      'https://patchura-backend.onrender.com'
    )
    expect(normalizeApiBaseUrl('https://patchura-backend.onrender.com///')).toBe(
      'https://patchura-backend.onrender.com'
    )
    expect(normalizeApiBaseUrl('http://localhost:8000/')).toBe('http://localhost:8000')
  })

  it('normalizes URLs by stripping redundant trailing /api prefixes', () => {
    expect(normalizeApiBaseUrl('https://patchura-backend.onrender.com/api')).toBe(
      'https://patchura-backend.onrender.com'
    )
    expect(normalizeApiBaseUrl('https://patchura-backend.onrender.com/api/')).toBe(
      'https://patchura-backend.onrender.com'
    )
  })

  it('handles empty, null, and whitespace inputs safely', () => {
    expect(normalizeApiBaseUrl('')).toBe('')
    expect(normalizeApiBaseUrl(null)).toBe('')
    expect(normalizeApiBaseUrl(undefined)).toBe('')
    expect(normalizeApiBaseUrl('   ')).toBe('')
  })

  it('verifies production base URL constant points to Render backend', () => {
    expect(PRODUCTION_API_BASE_URL).toBe('https://patchura-backend.onrender.com')
  })
})

describe('API Client Request Interceptor & Token Injection', () => {
  beforeEach(() => {
    setApiAccessToken(null)
  })

  it('tracks access token state via setApiAccessToken', () => {
    expect(getApiAccessToken()).toBeNull()
    setApiAccessToken('mock-jwt-token-123')
    expect(getApiAccessToken()).toBe('mock-jwt-token-123')
    setApiAccessToken(null)
    expect(getApiAccessToken()).toBeNull()
  })

  it('injects Bearer token into request Authorization header when token is present', async () => {
    setApiAccessToken('test-bearer-token-abc')

    // Spy on internal axios request handlers
    let capturedConfig: any = null
    const interceptor = (apiClient.interceptors.request as any).handlers[0].fulfilled
    capturedConfig = interceptor({
      headers: {},
      url: '/api/auth/me',
    })

    expect(capturedConfig.headers.Authorization).toBe('Bearer test-bearer-token-abc')
  })

  it('cleans redundant duplicate slashes and duplicate /api prefixes in request URLs', () => {
    const interceptor = (apiClient.interceptors.request as any).handlers[0].fulfilled

    const doubleSlashConfig = interceptor({
      headers: {},
      url: '//api//auth//login',
    })
    expect(doubleSlashConfig.url).toBe('/api/auth/login')

    const duplicateApiConfig = interceptor({
      headers: {},
      url: '/api/api/scans',
    })
    expect(duplicateApiConfig.url).toBe('/api/scans')
  })
})

describe('Login Request Handling Contract', () => {
  it('dispatches POST /api/auth/login with expected JSON payload format', async () => {
    const mockResponseData = {
      access_token: 'test-jwt-token',
      token_type: 'bearer',
      expires_in: 900,
      refresh_token: 'test-refresh-token',
      user: {
        id: 'usr-1',
        username: 'alice',
        email: 'alice@patchora.io',
        role: 'client' as const,
        is_active: true,
        created_at: '2026-10-25T12:00:00Z',
      },
    }

    const postSpy = vi.spyOn(apiClient, 'post').mockResolvedValueOnce({
      data: mockResponseData,
      status: 200,
      statusText: 'OK',
      headers: {},
      config: {} as any,
    })

    const result = await loginUser({
      login: 'alice@patchora.io',
      password: 'SecurePassword123!',
    })

    expect(postSpy).toHaveBeenCalledTimes(1)
    expect(postSpy).toHaveBeenCalledWith('/api/auth/login', {
      login: 'alice@patchora.io',
      password: 'SecurePassword123!',
    })
    expect(result.access_token).toBe('test-jwt-token')
    expect(result.user.username).toBe('alice')

    postSpy.mockRestore()
  })
})
