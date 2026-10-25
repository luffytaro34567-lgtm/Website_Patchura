import React, { useEffect, useState } from 'react'
import {
  Users,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Shield,
  UserCheck,
} from 'lucide-react'
import { fetchAdminUsers, updateUserStatus } from '@/api/dashboard'
import {
  fetchClientProfile,
  forceClientPasswordReset,
  setClientAccountStatus,
  unlockClientAccount,
} from '@/api/activity'
import { ClientProfileExtended } from '@/types/activity'
import { useAuth } from '@/context/AuthContext'
import { User } from '@/types/auth'
import clsx from 'clsx'

export function AdminUsersPage() {
  const { user: currentAdmin } = useAuth()
  const [users, setUsers] = useState<User[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Filter states
  const [searchQuery, setSearchQuery] = useState('')
  const [roleFilter, setRoleFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [updatingId, setUpdatingId] = useState<string | null>(null)

  // Extended Client Profile Modal
  const [selectedClientProfile, setSelectedClientProfile] = useState<ClientProfileExtended | null>(null)
  const [profileLoading, setProfileLoading] = useState(false)
  const [newAccountStatus, setNewAccountStatus] = useState<string>('active')
  const [statusReason, setStatusReason] = useState<string>('')
  const [resetTokenInfo, setResetTokenInfo] = useState<string | null>(null)

  const handleOpenClientProfile = async (userId: string) => {
    try {
      setProfileLoading(true)
      const prof = await fetchClientProfile(userId)
      setSelectedClientProfile(prof)
      setNewAccountStatus(prof.account_status || (prof.is_active ? 'active' : 'suspended'))
      setResetTokenInfo(null)
    } catch (err: any) {
      setError(err?.userMessage || 'Failed to fetch client profile details.')
    } finally {
      setProfileLoading(false)
    }
  }

  const handleUpdateAccountStatus = async () => {
    if (!selectedClientProfile) return
    try {
      setUpdatingId(selectedClientProfile.id)
      await setClientAccountStatus(selectedClientProfile.id, newAccountStatus, statusReason)
      setSuccessMsg(`Account status updated to ${newAccountStatus.toUpperCase()}.`)
      loadUsers()
      const prof = await fetchClientProfile(selectedClientProfile.id)
      setSelectedClientProfile(prof)
    } catch (err: any) {
      setError('Failed to update client status.')
    } finally {
      setUpdatingId(null)
    }
  }

  const handleUnlockAccount = async () => {
    if (!selectedClientProfile) return
    try {
      setUpdatingId(selectedClientProfile.id)
      await unlockClientAccount(selectedClientProfile.id)
      setSuccessMsg('Client account unlocked and failed login counter reset.')
      loadUsers()
      const prof = await fetchClientProfile(selectedClientProfile.id)
      setSelectedClientProfile(prof)
    } catch (err: any) {
      setError('Failed to unlock account.')
    } finally {
      setUpdatingId(null)
    }
  }

  const handleForcePasswordReset = async () => {
    if (!selectedClientProfile) return
    try {
      setUpdatingId(selectedClientProfile.id)
      const res = await forceClientPasswordReset(selectedClientProfile.id)
      setResetTokenInfo(`Recovery Token: ${res.recovery_token} (Valid for 24h)`)
      setSuccessMsg(res.message)
      const prof = await fetchClientProfile(selectedClientProfile.id)
      setSelectedClientProfile(prof)
    } catch (err: any) {
      setError('Failed to force password reset.')
    } finally {
      setUpdatingId(null)
    }
  }

  const loadUsers = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await fetchAdminUsers({
        q: searchQuery || undefined,
        role: roleFilter || undefined,
        is_active: statusFilter === '' ? undefined : statusFilter === 'active',
      })
      setUsers(data)
    } catch (err: any) {
      setError(err?.userMessage || 'Failed to retrieve user accounts.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    const timer = setTimeout(() => {
      loadUsers()
    }, 250)
    return () => clearTimeout(timer)
  }, [searchQuery, roleFilter, statusFilter])

  const handleToggleStatus = async (targetUser: User) => {
    if (targetUser.id === currentAdmin?.id && targetUser.is_active) {
      setError('You cannot suspend your own administrative account to prevent lockout.')
      return
    }

    try {
      setUpdatingId(targetUser.id)
      setError(null)
      const updated = await updateUserStatus(targetUser.id, !targetUser.is_active)
      setUsers(prev => prev.map(u => (u.id === updated.id ? updated : u)))
      setSuccessMsg(
        `Account '${updated.username}' is now ${updated.is_active ? 'ACTIVE' : 'SUSPENDED'}.`
      )
      setTimeout(() => setSuccessMsg(null), 4000)
    } catch (err: any) {
      setError(err?.userMessage || 'Failed to update account status.')
    } finally {
      setUpdatingId(null)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200 dark:border-dark-700">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            User & Client Directory
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Manage authenticated Client and Administrator accounts across the platform
          </p>
        </div>
      </div>

      {/* Notifications */}
      {error && (
        <div
          role="alert"
          className="p-4 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-sm flex items-center gap-2"
        >
          <AlertCircle className="w-4 h-4 text-rose-500 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div
          role="status"
          className="p-4 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 text-emerald-700 dark:text-emerald-300 text-sm flex items-center gap-2"
        >
          <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="card p-4 flex flex-col md:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <input
            type="text"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Search accounts by username or email..."
            className="w-full pl-9 pr-3.5 py-2 rounded-lg border border-slate-300 dark:border-dark-600 bg-white dark:bg-dark-900 text-slate-900 dark:text-white text-sm"
          />
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto">
          <select
            value={roleFilter}
            onChange={e => setRoleFilter(e.target.value)}
            className="px-3 py-2 rounded-lg border border-slate-300 dark:border-dark-600 bg-white dark:bg-dark-900 text-slate-900 dark:text-white text-sm w-full md:w-auto"
          >
            <option value="">All Roles</option>
            <option value="client">Clients Only</option>
            <option value="admin">Administrators Only</option>
          </select>

          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="px-3 py-2 rounded-lg border border-slate-300 dark:border-dark-600 bg-white dark:bg-dark-900 text-slate-900 dark:text-white text-sm w-full md:w-auto"
          >
            <option value="">All Statuses</option>
            <option value="active">Active Only</option>
            <option value="suspended">Suspended Only</option>
          </select>
        </div>
      </div>

      {/* Users Table */}
      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="py-12 text-center text-slate-400 text-sm">
            <div className="w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            Loading accounts...
          </div>
        ) : users.length === 0 ? (
          <div className="py-12 text-center text-slate-400 text-sm">
            No accounts matched your search criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
              <thead className="bg-slate-50 dark:bg-dark-900 text-slate-400 uppercase font-mono text-[11px] border-b border-slate-200 dark:border-dark-700">
                <tr>
                  <th className="p-3.5">Account / Username</th>
                  <th className="p-3.5">Email Address</th>
                  <th className="p-3.5">Role</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5">Registered On</th>
                  <th className="p-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-dark-700 font-sans">
                {users.map(u => (
                  <tr key={u.id} className="hover:bg-slate-50/50 dark:hover:bg-dark-700/50">
                    <td className="p-3.5 font-medium text-slate-900 dark:text-white">
                      <div className="flex items-center gap-2">
                        {u.role === 'admin' ? (
                          <Shield className="w-4 h-4 text-purple-500" />
                        ) : (
                          <UserCheck className="w-4 h-4 text-primary-500" />
                        )}
                        <span>{u.username}</span>
                      </div>
                    </td>
                    <td className="p-3.5 font-mono text-xs text-slate-500 dark:text-slate-400">
                      {u.email}
                    </td>
                    <td className="p-3.5">
                      <span
                        className={clsx(
                          'px-2 py-0.5 rounded text-xs font-semibold uppercase font-mono',
                          u.role === 'admin'
                            ? 'bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300 border border-purple-200 dark:border-purple-800'
                            : 'bg-primary-50 text-primary-700 dark:bg-primary-950 dark:text-primary-300 border border-primary-200 dark:border-primary-800'
                        )}
                      >
                        {u.role}
                      </span>
                    </td>
                    <td className="p-3.5">
                      <span
                        className={clsx(
                          'inline-flex items-center gap-1.5 text-xs font-medium',
                          u.is_active
                            ? 'text-emerald-600 dark:text-emerald-400'
                            : 'text-rose-600 dark:text-rose-400'
                        )}
                      >
                        {u.is_active ? (
                          <>
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            Active
                          </>
                        ) : (
                          <>
                            <XCircle className="w-3.5 h-3.5" />
                            Suspended
                          </>
                        )}
                      </span>
                    </td>
                    <td className="p-3.5 text-xs text-slate-400 font-mono">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td className="p-3.5 text-right space-x-2">
                      <button
                        onClick={() => handleOpenClientProfile(u.id)}
                        className="btn text-xs px-2.5 py-1 rounded font-medium text-cyan-600 dark:text-cyan-400 border border-cyan-200 dark:border-cyan-800 hover:bg-cyan-50 dark:hover:bg-cyan-950/40"
                      >
                        Controls
                      </button>

                      {u.id === currentAdmin?.id ? (
                        <span className="text-xs text-slate-400 italic">Self (Admin)</span>
                      ) : (
                        <button
                          onClick={() => handleToggleStatus(u)}
                          disabled={updatingId === u.id}
                          className={clsx(
                            'btn text-xs px-2.5 py-1 rounded font-medium',
                            u.is_active
                              ? 'text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-900 hover:bg-rose-50 dark:hover:bg-rose-950/40'
                              : 'text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900 hover:bg-emerald-50 dark:hover:bg-emerald-950/40'
                          )}
                        >
                          {updatingId === u.id
                            ? 'Updating...'
                            : u.is_active
                            ? 'Suspend'
                            : 'Activate'}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Extended Client Profile & Administrative Controls Modal */}
      {selectedClientProfile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-sm overflow-y-auto">
          <div className="bg-white dark:bg-dark-800 rounded-2xl max-w-xl w-full p-4 sm:p-6 shadow-2xl border border-slate-200 dark:border-dark-700 space-y-4 sm:space-y-5 max-h-[90vh] overflow-y-auto my-auto">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-dark-700 pb-3">
              <div>
                <h3 className="text-base sm:text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <UserCheck className="w-5 h-5 text-cyan-600" />
                  Client Account & Security Controls
                </h3>
                <p className="text-xs text-slate-500 font-mono mt-0.5 break-all">
                  {selectedClientProfile.username} ({selectedClientProfile.email})
                </p>
              </div>
              <button
                onClick={() => setSelectedClientProfile(null)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg"
                aria-label="Close client profile"
              >
                ✕
              </button>
            </div>

            {/* Linked Resource Metrics Grid */}
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 text-center text-xs">
              <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-dark-900 border border-slate-100 dark:border-dark-700">
                <span className="text-[10px] text-slate-400 uppercase font-mono">Websites</span>
                <p className="text-base font-bold text-slate-900 dark:text-white">{selectedClientProfile.websites_count}</p>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-dark-900 border border-slate-100 dark:border-dark-700">
                <span className="text-[10px] text-slate-400 uppercase font-mono">Scans</span>
                <p className="text-base font-bold text-slate-900 dark:text-white">{selectedClientProfile.scans_count}</p>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-dark-900 border border-slate-100 dark:border-dark-700">
                <span className="text-[10px] text-slate-400 uppercase font-mono">Reports</span>
                <p className="text-base font-bold text-slate-900 dark:text-white">{selectedClientProfile.reports_count}</p>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-dark-900 border border-slate-100 dark:border-dark-700">
                <span className="text-[10px] text-slate-400 uppercase font-mono">Plan</span>
                <p className="text-xs font-bold text-cyan-600 uppercase mt-1">{selectedClientProfile.active_plan}</p>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-dark-900 border border-slate-100 dark:border-dark-700">
                <span className="text-[10px] text-slate-400 uppercase font-mono">Fixes</span>
                <p className="text-base font-bold text-slate-900 dark:text-white">{selectedClientProfile.remediations_count}</p>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-dark-900 border border-slate-100 dark:border-dark-700">
                <span className="text-[10px] text-slate-400 uppercase font-mono">Deploys</span>
                <p className="text-base font-bold text-slate-900 dark:text-white">{selectedClientProfile.deployments_count}</p>
              </div>
            </div>

            {/* Account Status Form */}
            <div className="space-y-3 pt-2">
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                Set Account Status:
              </label>
              <div className="flex flex-col sm:flex-row gap-2">
                <select
                  value={newAccountStatus}
                  onChange={(e) => setNewAccountStatus(e.target.value)}
                  className="text-xs rounded-lg border border-slate-300 dark:border-dark-600 px-3 py-2.5 min-h-[40px] bg-white dark:bg-dark-900 text-slate-900 dark:text-white flex-1"
                >
                  <option value="active">Active (Full Access)</option>
                  <option value="suspended">Suspended (Blocked Access)</option>
                  <option value="terminated">Terminated (Account Disabled)</option>
                </select>
                <button
                  onClick={handleUpdateAccountStatus}
                  disabled={updatingId === selectedClientProfile.id}
                  className="px-4 py-2.5 min-h-[40px] bg-cyan-600 hover:bg-cyan-700 text-white font-semibold rounded-lg text-xs transition"
                >
                  Apply Status
                </button>
              </div>

              <input
                type="text"
                placeholder="Reason / Administrative note..."
                value={statusReason}
                onChange={(e) => setStatusReason(e.target.value)}
                className="w-full text-xs rounded-lg border border-slate-300 dark:border-dark-600 px-3 py-2 bg-white dark:bg-dark-900 text-slate-900 dark:text-white"
              />
            </div>

            {/* Security Actions: Unlock and Force Password Reset */}
            <div className="border-t border-slate-100 dark:border-dark-700 pt-4 space-y-3">
              <span className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                Security Threat Remediation & Account Recovery
              </span>

              <div className="flex flex-wrap items-center gap-3">
                <button
                  onClick={handleUnlockAccount}
                  disabled={updatingId === selectedClientProfile.id}
                  className="px-3 py-2 rounded-lg border border-slate-300 dark:border-dark-600 hover:bg-slate-50 dark:hover:bg-dark-700 text-slate-700 dark:text-slate-300 text-xs font-semibold"
                >
                  🔓 Unlock Account ({selectedClientProfile.failed_login_attempts} failed attempts)
                </button>

                <button
                  onClick={handleForcePasswordReset}
                  disabled={updatingId === selectedClientProfile.id}
                  className="px-3 py-2 rounded-lg bg-purple-600 hover:bg-purple-700 text-white text-xs font-semibold"
                >
                  ⚡ Force Password Reset (Issue 24h Token)
                </button>
              </div>

              {resetTokenInfo && (
                <div className="p-3 rounded-lg bg-purple-50 dark:bg-purple-950/40 border border-purple-200 dark:border-purple-800 text-purple-800 dark:text-purple-300 font-mono text-xs break-all">
                  {resetTokenInfo}
                </div>
              )}
            </div>

            <div className="flex justify-end pt-2 border-t border-slate-100 dark:border-dark-700">
              <button
                onClick={() => setSelectedClientProfile(null)}
                className="px-4 py-2 bg-slate-100 dark:bg-dark-700 text-slate-700 dark:text-slate-300 rounded-lg text-xs font-semibold hover:bg-slate-200"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
