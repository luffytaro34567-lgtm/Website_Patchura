import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Logo } from '@/components/shared/Logo'
import { Shield, Lock, Mail, User as UserIcon, Check, X, AlertCircle, Eye, EyeOff } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import clsx from 'clsx'

export function RegisterPage() {
  const { register, login } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    password_confirmation: '',
  })
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Password policy live criteria validation
  const criteria = [
    { label: 'At least 8 characters', met: form.password.length >= 8 },
    { label: 'At least one uppercase letter (A-Z)', met: /[A-Z]/.test(form.password) },
    { label: 'At least one lowercase letter (a-z)', met: /[a-z]/.test(form.password) },
    { label: 'At least one numeric digit (0-9)', met: /\d/.test(form.password) },
    { label: 'At least one special character (!@#$%^&*)', met: /[!@#$%^&*()_+\-=[\]{}|;:,.<>?/~`]/.test(form.password) },
    {
      label: 'Passwords match',
      met: form.password.length > 0 && form.password === form.password_confirmation,
    },
  ]

  const isFormValid =
    form.username.trim().length >= 3 &&
    form.email.trim().length >= 5 &&
    criteria.every(c => c.met)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!isFormValid) {
      setError('Please satisfy all password security requirements before submitting.')
      return
    }

    try {
      setIsSubmitting(true)
      // 1. Register client account
      await register(form)
      // 2. Automatically log in to provide seamless onboarding
      await login({ login: form.username, password: form.password })
      navigate('/dashboard', { replace: true })
    } catch (err: any) {
      setError(err?.userMessage || 'Registration failed. Please check your details.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-[85vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-lg space-y-8">
        {/* Header */}
        <div className="text-center">
          <Link to="/" className="inline-block mb-3" aria-label="PATCHORA Home">
            <Logo variant="symbol" size="xl" className="mx-auto" />
          </Link>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Create Client Account
          </h1>
          <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
            Register to initiate vulnerability assessments and AI-assisted remediation
          </p>
        </div>

        {/* Card */}
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

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <div>
              <label
                htmlFor="username"
                className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1"
              >
                Username
              </label>
              <div className="relative">
                <input
                  id="username"
                  type="text"
                  required
                  value={form.username}
                  onChange={e => setForm({ ...form, username: e.target.value })}
                  placeholder="e.g. security_lead"
                  className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 dark:border-dark-600 bg-white dark:bg-dark-900 text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-primary-500 text-sm min-h-[44px]"
                />
                <UserIcon className="w-4 h-4 text-slate-400 absolute right-3.5 top-3.5" />
              </div>
              <p className="mt-1 text-xs text-slate-400">Letters, numbers, underscores, and hyphens.</p>
            </div>

            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1"
              >
                Work Email Address
              </label>
              <div className="relative">
                <input
                  id="email"
                  type="email"
                  required
                  value={form.email}
                  onChange={e => setForm({ ...form, email: e.target.value })}
                  placeholder="analyst@organization.com"
                  className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 dark:border-dark-600 bg-white dark:bg-dark-900 text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-primary-500 text-sm min-h-[44px]"
                />
                <Mail className="w-4 h-4 text-slate-400 absolute right-3.5 top-3.5" />
              </div>
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1"
              >
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={form.password}
                  onChange={e => setForm({ ...form, password: e.target.value })}
                  placeholder="••••••••••••"
                  className="w-full px-3.5 py-2.5 pr-11 rounded-lg border border-slate-300 dark:border-dark-600 bg-white dark:bg-dark-900 text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-primary-500 text-sm min-h-[44px]"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(v => !v)}
                  className="absolute right-1.5 top-0.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 min-h-[44px] min-w-[44px] flex items-center justify-center rounded"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div>
              <label
                htmlFor="password_confirmation"
                className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1"
              >
                Confirm Password
              </label>
              <div className="relative">
                <input
                  id="password_confirmation"
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={form.password_confirmation}
                  onChange={e => setForm({ ...form, password_confirmation: e.target.value })}
                  placeholder="••••••••••••"
                  className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 dark:border-dark-600 bg-white dark:bg-dark-900 text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-primary-500 text-sm min-h-[44px]"
                />
                <Lock className="w-4 h-4 text-slate-400 absolute right-3.5 top-3.5" />
              </div>
            </div>

            {/* Live Password Strength Criteria Checklist */}
            <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-dark-900/60 border border-slate-200 dark:border-dark-700 space-y-1.5 text-xs">
              <span className="font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                Password Security Policy:
              </span>
              {criteria.map(c => (
                <div key={c.label} className="flex items-center gap-2">
                  {c.met ? (
                    <Check className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" />
                  ) : (
                    <span className="w-3.5 h-3.5 rounded-full border border-slate-300 dark:border-dark-600 flex-shrink-0" />
                  )}
                  <span
                    className={clsx(
                      c.met
                        ? 'text-emerald-700 dark:text-emerald-400 font-medium'
                        : 'text-slate-500 dark:text-slate-400'
                    )}
                  >
                    {c.label}
                  </span>
                </div>
              ))}
            </div>

            <button
              type="submit"
              disabled={isSubmitting || !isFormValid}
              className="btn-primary w-full py-2.5 min-h-[44px] text-sm font-semibold justify-center mt-2 disabled:opacity-50"
            >
              {isSubmitting ? (
                <span className="flex items-center gap-2">
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Provisioning Account...
                </span>
              ) : (
                'Create Client Account'
              )}
            </button>
          </form>

          <div className="mt-6 pt-4 border-t border-slate-100 dark:border-dark-700 text-center text-sm text-slate-500 dark:text-slate-400">
            Already have an account?{' '}
            <Link
              to="/login"
              className="font-medium text-primary-600 dark:text-primary-400 hover:underline"
            >
              Sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
