import { apiClient } from './client'

export interface HealthResponse {
  status: 'healthy' | 'degraded'
  version: string
  environment: string
  uptime_seconds: number
  database: {
    connected: boolean
    error?: string
  }
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await apiClient.get<HealthResponse>('/api/health')
  return res.data
}
