import React, { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Logo } from '@/components/shared/Logo'
import { Shield, Lock, User as UserIcon, Eye, EyeOff, AlertCircle, KeyRound, CheckCircle2 } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { recoverPassword, resetPasswordWithToken } from '@/api/auth'

export function LoginPage() {
  const { login, isAuthenticated, isAdmin } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  // Redirect if user is already authenticated
  React.useEffect(() => {
    if (isAuthenticated) {
      const fromPath = (location.state as any)?.from?.pathname
      const defaultTarget = isAdmin ? '/admin/dashboard' : '/dashboard'
      const target = fromPath && fromPath !== '/login' ? fromPath : defaultTarget
      navigate(target, { replace: true })
    }
  }, [isAuthenticated, isAdmin, navigate, location.state])

  const [form, setForm] = useState({ login: '', password: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Password Recovery Modal State
  const [showRecoveryModal, setShowRecoveryModal] = useState(false)
  const [recoveryEmail, setRecoveryEmail] = useState('')
  const [recoveryStep, setRecoveryStep] = useState<'request' | 'reset'>('request')
  const [recoveryToken, setRecoveryToken] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [newPasswordConfirm, setNewPasswordConfirm] = useState('')
  const [recoveryMsg, setRecoveryMsg] = useState<string | null>(null)
  const [recoveryError, setRecoveryError] = useState<string | null>(null)
  const [recoveryLoading, setRecoveryLoading] = useState(false)

  const handleRequestRecovery = async (e: React.FormEvent) => {
    e.preventDefault()
    setRecoveryError(null)
    setRecoveryMsg(null)
    try {
      setRecoveryLoading(true)
      const res = await recoverPassword(recoveryEmail)
      setRecoveryMsg(res.message)
      if (res.recovery_token) {
        setRecoveryToken(res.recovery_token)
        setRecoveryStep('reset')
      }
    } catch (err: any) {
      setRecoveryError(err?.response?.data?.error?.message || 'Failed to initiate recovery.')
    } finally {
      setRecoveryLoading(false)
    }
  }

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setRecoveryError(null)
    setRecoveryMsg(null)
    if (newPassword !== newPasswordConfirm) {
      setRecoveryError('Passwords do not match.')
      return
    }
    try {
      setRecoveryLoading(true)
      const res = await resetPasswordWithToken(recoveryToken, newPassword, newPasswordConfirm)
      setRecoveryMsg(res.message)
      setTimeout(() => {
        setShowRecoveryModal(false)
        setRecoveryStep('request')
        setRecoveryMsg(null)
      }, 3000)
    } catch (err: any) {
      setRecoveryError(err?.response?.data?.error?.message || 'Failed to reset password.')
    } finally {
      setRecoveryLoading(false)
    }
  }

  const from = (location.state as any)?.from?.pathname || '/dashboard'

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!form.login.trim() || !form.password) {
      setError('Please provide your username/email and password.')
      return
    }

    try {
      setIsSubmitting(true)
      const loggedUser = await login(form)
      const fromPath = (location.state as any)?.from?.pathname
      const defaultTarget = loggedUser.role === 'admin' ? '/admin/dashboard' : '/dashboard'
      const target = fromPath && fromPath !== '/login' ? fromPath : defaultTarget
      navigate(target, { replace: true })
    } catch (err: any) {
      setError(err?.userMessage || 'Invalid credentials or account inactive.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-[85vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8">
        {/* Header */}
        <div className="text-center">
          <Link to="/" className="inline-block mb-3" aria-label="PATCHORA Home">
            <Logo variant="symbol" size="xl" className="mx-auto" />
          </Link>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Log in to <span className="gradient-text">PATCHORA</span>
          </h1>
          <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
            Access your vulnerability assessments and AI remediation dashboard
          </p>
        </div>

        {/* Form card */}
        <div className="card shadow-lg p-5 sm:p-8">
          {error && (
            <div
              role="alert"
              className="mb-6 p-4 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 flex items-start gap-3 text-sm text-rose-700 dark:text-rose-300"
            >
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-rose-500" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5" noValidate>
            <div>
              <label
                htmlFor="login"
                className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5"
              >
                Username or Email
              </label>
              <div className="relative">
                <input
                  id="login"
                  type="text"
                  autoComplete="username"
                  required
                  value={form.login}
                  onChange={e => setForm({ ...form, login: e.target.value })}
                  placeholder="admin or security_lead@company.com"
                  className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 dark:border-dark-600 bg-white dark:bg-dark-900 text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-primary-500 text-sm transition-colors min-h-[44px]"
                />
                <UserIcon className="w-4 h-4 text-slate-400 absolute right-3.5 top-3.5" aria-hidden />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label
                  htmlFor="password"
                  className="block text-sm font-medium text-slate-700 dark:text-slate-300"
                >
                  Password
                </label>
                <button
                  type="button"
                  onClick={() => {
                    setShowRecoveryModal(true)
                    setRecoveryStep('request')
                    setRecoveryError(null)
                    setRecoveryMsg(null)
                  }}
                  className="text-xs text-primary-600 dark:text-primary-400 hover:underline font-medium min-h-[32px] flex items-center"
                >
                  Forgot password?
                </button>
              </div>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  value={form.password}
                  onChange={e => setForm({ ...form, password: e.target.value })}
                  placeholder="••••••••••••"
                  className="w-full px-3.5 py-2.5 pr-11 rounded-lg border border-slate-300 dark:border-dark-600 bg-white dark:bg-dark-900 text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-primary-500 text-sm transition-colors min-h-[44px]"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(v => !v)}
                  className="absolute right-1.5 top-0.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 min-h-[44px] min-w-[44px] flex items-center justify-center rounded focus-visible:outline-primary-500"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="btn-primary w-full py-2.5 min-h-[44px] text-sm font-semibold justify-center"
            >
              {isSubmitting ? (
                <span className="flex items-center gap-2">
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Authenticating...
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  <Lock className="w-4 h-4" />
                  Sign In
                </span>
              )}
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-slate-100 dark:border-dark-700 text-center text-sm text-slate-500 dark:text-slate-400">
            Don't have an account yet?{' '}
            <Link
              to="/get-started"
              className="font-medium text-primary-600 dark:text-primary-400 hover:underline"
            >
              Register here
            </Link>
          </div>
        </div>
      </div>

      {/* Password Recovery Modal */}
      {showRecoveryModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-sm overflow-y-auto">
          <div className="bg-white dark:bg-dark-800 rounded-2xl max-w-md w-full p-4 sm:p-6 shadow-2xl border border-slate-200 dark:border-dark-700 space-y-4 max-h-[90vh] overflow-y-auto my-auto">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-dark-700 pb-3">
              <h3 className="text-base sm:text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <KeyRound className="w-5 h-5 text-primary-500" />
                Password Recovery
              </h3>
              <button
                onClick={() => setShowRecoveryModal(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg text-sm font-bold"
                aria-label="Close recovery dialog"
              >
                ✕
              </button>
            </div>

            {recoveryError && (
              <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-rose-500 flex-shrink-0" />
                <span>{recoveryError}</span>
              </div>
            )}

            {recoveryMsg && (
              <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 text-emerald-700 dark:text-emerald-300 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                <span>{recoveryMsg}</span>
              </div>
            )}

            {recoveryStep === 'request' ? (
              <form onSubmit={handleRequestRecovery} className="space-y-4 text-xs">
                <p className="text-slate-500 dark:text-slate-400">
                  Enter your registered account email address. We will verify your credentials and issue a recovery token.
                </p>
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Email Address
                  </label>
                  <input
                    type="email"
                    required
                    value={recoveryEmail}
                    onChange={(e) => setRecoveryEmail(e.target.value)}
                    placeholder="user@example.com"
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-dark-600 bg-white dark:bg-dark-900 text-slate-900 dark:text-white text-xs"
                  />
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowRecoveryModal(false)}
                    className="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-dark-600 text-slate-600 dark:text-slate-300"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={recoveryLoading}
                    className="px-4 py-1.5 rounded-lg bg-primary-600 text-white font-semibold hover:bg-primary-700 transition"
                  >
                    {recoveryLoading ? 'Processing...' : 'Send Recovery Token'}
                  </button>
                </div>
              </form>
            ) : (
              <form onSubmit={handleResetPassword} className="space-y-3 text-xs">
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Recovery Token
                  </label>
                  <input
                    type="text"
                    required
                    value={recoveryToken}
                    onChange={(e) => setRecoveryToken(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-dark-600 bg-white dark:bg-dark-900 text-slate-900 dark:text-white text-xs font-mono"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    New Password (min. 8 characters)
                  </label>
                  <input
                    type="password"
                    required
                    minLength={8}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-dark-600 bg-white dark:bg-dark-900 text-slate-900 dark:text-white text-xs"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Confirm New Password
                  </label>
                  <input
                    type="password"
                    required
                    minLength={8}
                    value={newPasswordConfirm}
                    onChange={(e) => setNewPasswordConfirm(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-dark-600 bg-white dark:bg-dark-900 text-slate-900 dark:text-white text-xs"
                  />
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setRecoveryStep('request')}
                    className="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-dark-600 text-slate-600 dark:text-slate-300"
                  >
                    Back
                  </button>
                  <button
                    type="submit"
                    disabled={recoveryLoading}
                    className="px-4 py-1.5 rounded-lg bg-emerald-600 text-white font-semibold hover:bg-emerald-700 transition"
                  >
                    {recoveryLoading ? 'Updating...' : 'Set New Password'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
