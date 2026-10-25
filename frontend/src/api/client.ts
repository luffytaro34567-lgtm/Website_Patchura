/**
 * PATCHORA — Centralized Axios API Client
 *
 * Configured with normalized base URL resolution, bearer token injection,
 * and standard error response parsing.
 */
import axios from 'axios'

export const PRODUCTION_API_BASE_URL = 'https://patchura-backend.onrender.com'

/**
 * Normalizes an API base URL by:
 * - Trimming whitespace
 * - Removing trailing slashes
 * - Stripping a redundant trailing '/api' prefix (since individual route paths declare '/api/...')
 */
export function normalizeApiBaseUrl(rawUrl?: string | null): string {
  if (!rawUrl || typeof rawUrl !== 'string') {
    return ''
  }
  let cleaned = rawUrl.trim().replace(/\/+$/, '')
  if (cleaned.endsWith('/api')) {
    cleaned = cleaned.slice(0, -4).replace(/\/+$/, '')
  }
  return cleaned
}

/**
 * Resolves the active API base URL:
 * 1. Explicit VITE_API_BASE_URL (if non-empty)
 * 2. If running in production (import.meta.env.PROD), falls back to PRODUCTION_API_BASE_URL
 * 3. In development (import.meta.env.DEV), defaults to '' (to utilize Vite's /api proxy)
 */
export function resolveApiBaseUrl(): string {
  const envUrl = import.meta.env.VITE_API_BASE_URL
  if (typeof envUrl === 'string' && envUrl.trim().length > 0) {
    return normalizeApiBaseUrl(envUrl)
  }
  if (import.meta.env.PROD) {
    return PRODUCTION_API_BASE_URL
  }
  return ''
}

export const BASE_URL = resolveApiBaseUrl()

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30_000, // 30s to accommodate Render free-tier cold starts
})

let currentAccessToken: string | null = null

export function setApiAccessToken(token: string | null) {
  currentAccessToken = token
}

export function getApiAccessToken(): string | null {
  return currentAccessToken
}

// Request interceptor — normalize endpoint path and inject Bearer token
apiClient.interceptors.request.use(config => {
  // Prevent duplicate slashes and duplicate /api/api prefixes
  if (config.url) {
    let cleanUrl = config.url.replace(/\/{2,}/g, '/')
    if (cleanUrl.startsWith('/api/api/')) {
      cleanUrl = cleanUrl.replace(/^\/api\/api\//, '/api/')
    }
    config.url = cleanUrl
  }

  if (currentAccessToken && config.headers) {
    config.headers.Authorization = `Bearer ${currentAccessToken}`
  }
  return config
})

// Response interceptor — normalize errors with clear messages for network & cold starts
apiClient.interceptors.response.use(
  response => response,
  error => {
    let message = 'An unexpected error occurred'
    if (error?.response?.data?.error?.message) {
      message = error.response.data.error.message
    } else if (typeof error?.response?.data?.detail === 'string') {
      message = error.response.data.detail
    } else if (Array.isArray(error?.response?.data?.detail)) {
      message = error.response.data.detail.map((d: any) => d.msg || d.message).join(', ')
    } else if (error?.code === 'ECONNABORTED' || (error?.message && error.message.toLowerCase().includes('timeout'))) {
      message = 'Connection timed out. The server may be waking up, please try again in a moment.'
    } else if (error?.code === 'ERR_NETWORK' || error?.message === 'Network Error') {
      message = 'Unable to connect to server. The backend may be starting up or sleeping on Render. Please retry shortly.'
    } else if (error?.response?.status === 429) {
      message = 'Too many requests. Please wait a moment before trying again.'
    } else if (error?.response?.status >= 500) {
      message = 'Service temporarily unavailable. Please try again shortly.'
    } else if (error?.message) {
      message = error.message
    }
    error.userMessage = message
    return Promise.reject(error)
  }
)
