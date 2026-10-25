/**
 * Axios-based API client configured with the backend base URL.
 * Automatically injects the bearer authentication token if present.
 */
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15_000,
})

let currentAccessToken: string | null = null

export function setApiAccessToken(token: string | null) {
  currentAccessToken = token
}

// Request interceptor — inject Bearer token
apiClient.interceptors.request.use(config => {
  if (currentAccessToken && config.headers) {
    config.headers.Authorization = `Bearer ${currentAccessToken}`
  }
  return config
})

// Response interceptor — normalise errors
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
    } else if (error?.message) {
      message = error.message
    }
    error.userMessage = message
    return Promise.reject(error)
  }
)
