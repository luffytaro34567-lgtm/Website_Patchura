export type UserRole = 'admin' | 'client'

export interface User {
  id: string
  username: string
  email: string
  role: UserRole
  is_active: boolean
  created_at: string
}

export interface AuthTokensResponse {
  access_token: string
  token_type: string
  expires_in: number
  refresh_token: string
  user: User
}

export interface RegisterData {
  username: string
  email: string
  password: string
  password_confirmation: string
}

export interface LoginData {
  login: string
  password: string
}
