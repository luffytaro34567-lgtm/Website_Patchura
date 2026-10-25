import React, { useEffect, useState } from 'react'
import {
  Globe,
  Search,
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Clock,
  ExternalLink,
  AlertCircle,
} from 'lucide-react'
import { adminListWebsites, adminSuspendWebsite } from '@/api/websites'
import { Website } from '@/types/website'
import clsx from 'clsx'

export function AdminWebsitesPage() {
  const [websites, setWebsites] = useState<Website[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [updatingId, setUpdatingId] = useState<string | null>(null)

  const loadWebsites = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await adminListWebsites()
      setWebsites(data)
    } catch (err: any) {
      setError(err?.userMessage || 'Failed to retrieve registered targets.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadWebsites()
  }, [])

  const handleToggleSuspend = async (site: Website) => {
    let reason: string | undefined = undefined
    if (!site.is_suspended_by_admin) {
      const inputReason = window.prompt(
        `Enter administrative reason for suspending assessment access on '${site.domain}':`,
        'Abuse prevention / Policy compliance review'
      )
      if (inputReason === null) return // cancelled
      reason = inputReason.trim() || 'Administrative suspension'
    }

    try {
      setUpdatingId(site.id)
      setError(null)
      const updated = await adminSuspendWebsite(site.id, !site.is_suspended_by_admin, reason)
      setWebsites(prev => prev.map(w => (w.id === updated.id ? updated : w)))
    } catch (err: any) {
      setError(err?.userMessage || 'Failed to update suspension status.')
    } finally {
      setUpdatingId(null)
    }
  }

  const filtered = websites.filter(
    w =>
      w.name.toLowerCase().includes(search.toLowerCase()) ||
      w.domain.toLowerCase().includes(search.toLowerCase()) ||
      w.user_id.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200 dark:border-dark-700">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Globe className="w-6 h-6 text-purple-500" />
            Registered Website Targets Directory
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Global view of all client registered targets, ownership verification statuses, and legal scan authorizations
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-500 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Search */}
      <div className="card p-3 flex items-center gap-2">
        <Search className="w-4 h-4 text-slate-400 ml-1" />
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search targets by domain, name, or owner ID..."
          className="w-full bg-transparent border-0 text-sm focus:ring-0 text-slate-900 dark:text-white placeholder-slate-400"
        />
      </div>

      {/* Targets Table */}
      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="py-12 text-center text-slate-400 text-sm">
            <div className="w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            Loading targets directory...
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-12 text-center text-slate-400 text-sm">
            No registered website targets found.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-600 dark:text-slate-300">
              <thead className="bg-slate-50 dark:bg-dark-900 text-slate-400 uppercase font-mono text-[10px] border-b border-slate-200 dark:border-dark-700">
                <tr>
                  <th className="p-3">Target / Domain</th>
                  <th className="p-3">Owner ID</th>
                  <th className="p-3">Verification</th>
                  <th className="p-3">Scan Authorization</th>
                  <th className="p-3">Authorized Signee</th>
                  <th className="p-3">Registered</th>
                  <th className="p-3 text-right">Admin Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-dark-700">
                {filtered.map(site => {
                  const isVerified = site.verification_status === 'verified'
                  const isAuthorized =
                    site.authorization?.is_authorized && !site.authorization?.is_revoked

                  return (
                    <tr key={site.id} className="hover:bg-slate-50/50 dark:hover:bg-dark-700/50">
                      <td className="p-3">
                        <div className="font-semibold text-slate-900 dark:text-white text-xs">
                          {site.name}
                        </div>
                        <a
                          href={site.target_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-mono text-slate-400 hover:text-purple-500 flex items-center gap-1 text-[11px]"
                        >
                          {site.domain}
                          <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                      </td>
                      <td className="p-3 font-mono text-[10px] text-slate-400">
                        {site.user_id.slice(0, 8)}...
                      </td>
                      <td className="p-3">
                        <span
                          className={clsx(
                            'inline-flex items-center gap-1 px-1.5 py-0.5 rounded font-mono text-[10px] font-semibold',
                            isVerified
                              ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                              : 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                          )}
                        >
                          {isVerified ? (
                            <>
                              <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                              VERIFIED
                            </>
                          ) : (
                            <>
                              <Clock className="w-3 h-3 text-amber-500" />
                              PENDING
                            </>
                          )}
                        </span>
                      </td>
                      <td className="p-3">
                        <span
                          className={clsx(
                            'inline-flex items-center gap-1 px-1.5 py-0.5 rounded font-mono text-[10px] font-semibold',
                            site.is_suspended_by_admin
                              ? 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300'
                              : isAuthorized
                              ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                              : 'bg-slate-100 text-slate-600 dark:bg-dark-700 dark:text-slate-400'
                          )}
                        >
                          {site.is_suspended_by_admin
                            ? 'SUSPENDED'
                            : isAuthorized
                            ? 'AUTHORIZED'
                            : 'UNAUTHORIZED'}
                        </span>
                      </td>
                      <td className="p-3 text-slate-700 dark:text-slate-300">
                        {site.authorization?.authorized_by_name ? (
                          <div>
                            <span className="font-semibold block">{site.authorization.authorized_by_name}</span>
                            <span className="text-[10px] text-slate-400">{site.authorization.authorized_by_email}</span>
                          </div>
                        ) : (
                          <span className="text-slate-400 italic">None</span>
                        )}
                      </td>
                      <td className="p-3 text-slate-400 font-mono text-[11px]">
                        {new Date(site.created_at).toLocaleDateString()}
                      </td>
                      <td className="p-3 text-right">
                        <button
                          onClick={() => handleToggleSuspend(site)}
                          disabled={updatingId === site.id}
                          className={clsx(
                            'btn text-xs px-2.5 py-1 rounded font-medium',
                            site.is_suspended_by_admin
                              ? 'text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800 hover:bg-emerald-50'
                              : 'text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-800 hover:bg-rose-50'
                          )}
                        >
                          {updatingId === site.id
                            ? 'Updating...'
                            : site.is_suspended_by_admin
                            ? 'Reinstate'
                            : 'Suspend Access'}
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
