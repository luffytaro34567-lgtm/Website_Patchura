import React, { useState } from 'react'
import { Settings, Lock, CheckCircle2, AlertCircle } from 'lucide-react'
import { changePassword } from '@/api/dashboard'

export function AdminSettingsPage() {
  const [passForm, setPassForm] = useState({
    current_password: '',
    new_password: '',
    new_password_confirmation: '',
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [success, setSuccess] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)

    if (passForm.new_password !== passForm.new_password_confirmation) {
      setError('New password confirmation does not match.')
      return
    }

    try {
      setIsSubmitting(true)
      await changePassword(passForm)
      setSuccess('Administrator password updated successfully.')
      setPassForm({
        current_password: '',
        new_password: '',
        new_password_confirmation: '',
      })
    } catch (err: any) {
      setError(err?.userMessage || 'Failed to update password.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="border-b border-slate-200 dark:border-dark-700 pb-6">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
          Administrator Account Settings
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Update credential parameters and security credentials
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-500 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="p-4 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 text-emerald-700 dark:text-emerald-300 text-sm flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
          <span>{success}</span>
        </div>
      )}

      <div className="card p-4 sm:p-6 space-y-4">
        <div className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white border-b border-slate-100 dark:border-dark-700 pb-3">
          <Lock className="w-4 h-4 text-purple-500" />
          <h3>Change Administrator Password</h3>
        </div>

        <form onSubmit={handlePasswordSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Current Password
            </label>
            <input
              type="password"
              required
              value={passForm.current_password}
              onChange={e => setPassForm({ ...passForm, current_password: e.target.value })}
              className="w-full px-3.5 py-2.5 min-h-[44px] rounded-lg border border-slate-300 dark:border-dark-600 bg-white dark:bg-dark-900 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              New Secure Password
            </label>
            <input
              type="password"
              required
              value={passForm.new_password}
              onChange={e => setPassForm({ ...passForm, new_password: e.target.value })}
              className="w-full px-3.5 py-2.5 min-h-[44px] rounded-lg border border-slate-300 dark:border-dark-600 bg-white dark:bg-dark-900 text-sm"
            />
            <p className="text-[11px] text-slate-400 mt-1">Must be 8+ chars with upper, lower, digit, and symbol.</p>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Confirm New Password
            </label>
            <input
              type="password"
              required
              value={passForm.new_password_confirmation}
              onChange={e => setPassForm({ ...passForm, new_password_confirmation: e.target.value })}
              className="w-full px-3.5 py-2.5 min-h-[44px] rounded-lg border border-slate-300 dark:border-dark-600 bg-white dark:bg-dark-900 text-sm"
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="btn-primary text-xs bg-purple-600 hover:bg-purple-700 min-h-[44px] w-full sm:w-auto px-5"
          >
            {isSubmitting ? 'Updating...' : 'Update Password'}
          </button>
        </form>
      </div>
    </div>
  )
}
