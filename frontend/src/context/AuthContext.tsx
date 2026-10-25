import React, { createContext, useContext, useEffect, useState } from 'react'
import {
  fetchCurrentUser,
  loginUser,
  logoutUser,
  registerClient,
  rotateRefreshToken,
} from '@/api/auth'
import { setApiAccessToken } from '@/api/client'
import { LoginData, RegisterData, User } from '@/types/auth'

const REFRESH_TOKEN_KEY = 'bh_refresh_token'

interface AuthContextValue {
  user: User | null
  accessToken: string | null
  isLoading: boolean
  isAuthenticated: boolean
  isAdmin: boolean
  login: (data: LoginData) => Promise<User>
  register: (data: RegisterData) => Promise<User>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)

  // Initialize session from stored refresh token on mount
  useEffect(() => {
    let isMounted = true

    async function restoreSession() {
      const storedRefreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
      if (!storedRefreshToken) {
        if (isMounted) setIsLoading(false)
        return
      }

      try {
        const tokens = await rotateRefreshToken(storedRefreshToken)
        if (isMounted) {
          setAccessToken(tokens.access_token)
          setApiAccessToken(tokens.access_token)
          setUser(tokens.user)
          localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token)
        }
      } catch (err) {
        // Token invalid, expired, or revoked
        localStorage.removeItem(REFRESH_TOKEN_KEY)
        setApiAccessToken(null)
        if (isMounted) {
          setUser(null)
          setAccessToken(null)
        }
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    restoreSession()

    return () => {
      isMounted = false
    }
  }, [])

  const login = async (data: LoginData): Promise<User> => {
    const tokens = await loginUser(data)
    setAccessToken(tokens.access_token)
    setApiAccessToken(tokens.access_token)
    setUser(tokens.user)
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token)
    return tokens.user
  }

  const register = async (data: RegisterData): Promise<User> => {
    return await registerClient(data)
  }

  const logout = async (): Promise<void> => {
    const storedRefreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
    if (storedRefreshToken) {
      try {
        await logoutUser(storedRefreshToken)
      } catch (err) {
        // Silently continue clearing local state
      }
    }
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    setApiAccessToken(null)
    setAccessToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        isLoading,
        isAuthenticated: !!user,
        isAdmin: user?.role === 'admin',
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
