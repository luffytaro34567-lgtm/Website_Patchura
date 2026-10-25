import { apiClient } from './client'
import { AuthTokensResponse, LoginData, RegisterData, User } from '../types/auth'

export async function registerClient(data: RegisterData): Promise<User> {
  const res = await apiClient.post<User>('/api/auth/register', data)
  return res.data
}

export async function loginUser(data: LoginData): Promise<AuthTokensResponse> {
  const res = await apiClient.post<AuthTokensResponse>('/api/auth/login', data)
  return res.data
}

export async function rotateRefreshToken(refreshToken: string): Promise<AuthTokensResponse> {
  const res = await apiClient.post<AuthTokensResponse>('/api/auth/refresh', {
    refresh_token: refreshToken,
  })
  return res.data
}

export async function logoutUser(refreshToken: string): Promise<void> {
  await apiClient.post('/api/auth/logout', {
    refresh_token: refreshToken,
  })
}

export async function fetchCurrentUser(): Promise<User> {
  const res = await apiClient.get<User>('/api/auth/me')
  return res.data
}

export async function listAllUsers(): Promise<User[]> {
  const res = await apiClient.get<User[]>('/api/auth/admin/users')
  return res.data
}

export async function recoverPassword(email: string): Promise<{ success: boolean; message: string; recovery_token?: string }> {
  const res = await apiClient.post<{ success: boolean; message: string; recovery_token?: string }>('/api/auth/recover-password', {
    email,
  })
  return res.data
}

export async function resetPasswordWithToken(
  token: string,
  newPassword: string,
  confirmation: string
): Promise<{ success: boolean; message: string; username?: string }> {
  const res = await apiClient.post<{ success: boolean; message: string; username?: string }>('/api/auth/reset-password', {
    token,
    new_password: newPassword,
    new_password_confirmation: confirmation,
  })
  return res.data
}
