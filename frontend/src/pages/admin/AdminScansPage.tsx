import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ScanSearch,
  Search,
  CheckCircle2,
  XCircle,
  StopCircle,
  RefreshCw,
  ExternalLink,
  AlertOctagon,
  ChevronRight,
} from 'lucide-react'
import { adminCancelScan, adminListScans } from '@/api/scans'
import { Scan } from '@/types/scan'
import clsx from 'clsx'

export function AdminScansPage() {
  const [scans, setScans] = useState<Scan[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState('all')
  const [search, setSearch] = useState('')
  const [cancellingId, setCancellingId] = useState<string | null>(null)

  const loadScans = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const data = await adminListScans()
      setScans(data)
    } catch (err: any) {
      setError(err?.userMessage || 'Failed to load global scan operations.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadScans()
  }, [])

  const handleCancelScan = async (scanId: string) => {
    if (!confirm('Are you sure you want to administratively cancel this scan?')) return
    try {
      setCancellingId(scanId)
      const updated = await adminCancelScan(scanId)
      setScans(prev => prev.map(s => (s.id === scanId ? updated : s)))
    } catch (err: any) {
      alert(err?.userMessage || 'Failed to cancel scan.')
    } finally {
      setCancellingId(null)
    }
  }

  const filteredScans = scans.filter(s => {
    const matchesStatus = statusFilter === 'all' || s.status === statusFilter
    const matchesSearch =
      s.target_url.toLowerCase().includes(search.toLowerCase()) ||
      s.target_domain.toLowerCase().includes(search.toLowerCase()) ||
      s.user_id.toLowerCase().includes(search.toLowerCase()) ||
      s.id.toLowerCase().includes(search.toLowerCase())
    return matchesStatus && matchesSearch
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-slate-200 dark:border-dark-700 pb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <ScanSearch className="w-6 h-6 text-primary-500" />
            Global Scan Operations & Oversight
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Audit, inspect, and cancel active vulnerability scans across all tenant clients
          </p>
        </div>
        <button
          onClick={loadScans}
          className="btn btn-secondary flex items-center gap-2 text-sm self-start sm:self-auto"
        >
          <RefreshCw className={clsx('w-4 h-4', isLoading && 'animate-spin')} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-400 text-sm flex items-center gap-2">
          <XCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Filter and Search */}
      <div className="card p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search domain, scan ID, or user ID..."
            className="input pl-9 text-sm w-full"
          />
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto">
          {['all', 'queued', 'running', 'completed', 'failed', 'cancelled'].map(st => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={clsx(
                'px-3 py-1.5 rounded-lg text-xs font-medium capitalize whitespace-nowrap transition-colors',
                statusFilter === st
                  ? 'bg-primary-600 text-white'
                  : 'bg-slate-100 dark:bg-dark-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-dark-600'
              )}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="card p-12 text-center text-slate-400">Loading global scan history...</div>
      ) : filteredScans.length === 0 ? (
        <div className="card p-12 text-center text-slate-400 space-y-2">
          <p>No scans match your current filter.</p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 dark:bg-dark-700/50 text-slate-600 dark:text-slate-400 text-xs font-semibold uppercase tracking-wider border-b border-slate-200 dark:border-dark-700">
                <tr>
                  <th className="px-6 py-3.5">Target Domain & URL</th>
                  <th className="px-6 py-3.5">Client User</th>
                  <th className="px-6 py-3.5">Profile</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5">Findings</th>
                  <th className="px-6 py-3.5">Duration</th>
                  <th className="px-6 py-3.5">Executed</th>
                  <th className="px-6 py-3.5 text-right">Admin Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-dark-700">
                {filteredScans.map(scan => {
                  const isRunning = scan.status === 'running' || scan.status === 'queued'

                  return (
                    <tr key={scan.id} className="hover:bg-slate-50/50 dark:hover:bg-dark-750/50 transition-colors">
                      <td className="px-6 py-4">
                        <div className="font-semibold text-slate-900 dark:text-white">{scan.target_domain}</div>
                        <div className="text-xs text-slate-400 font-mono truncate max-w-xs">{scan.target_url}</div>
                      </td>

                      <td className="px-6 py-4 text-xs font-mono text-slate-500">
                        {scan.user_id.slice(0, 8)}...
                      </td>

                      <td className="px-6 py-4">
                        <span className="capitalize font-mono text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-dark-700 text-slate-700 dark:text-slate-300">
                          {scan.profile.replace('_', ' ')}
                        </span>
                      </td>

                      <td className="px-6 py-4">
                        <span
                          className={clsx(
                            'inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium capitalize',
                            scan.status === 'completed' && 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300',
                            scan.status === 'running' && 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300 animate-pulse',
                            scan.status === 'queued' && 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300',
                            scan.status === 'failed' && 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300',
                            scan.status === 'cancelled' && 'bg-slate-100 text-slate-800 dark:bg-dark-700 dark:text-slate-400'
                          )}
                        >
                          {scan.status === 'completed' && <CheckCircle2 className="w-3 h-3" />}
                          {scan.status === 'running' && <RefreshCw className="w-3 h-3 animate-spin" />}
                          {scan.status === 'failed' && <XCircle className="w-3 h-3" />}
                          {scan.status === 'cancelled' && <StopCircle className="w-3 h-3" />}
                          {scan.status}
                        </span>
                      </td>

                      <td className="px-6 py-4 text-xs font-mono">
                        {scan.total_findings > 0 ? (
                          <div className="flex items-center gap-1">
                            {scan.critical_count > 0 && (
                              <span className="px-1.5 py-0.5 rounded bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300 font-bold">
                                {scan.critical_count}C
                              </span>
                            )}
                            {scan.high_count > 0 && (
                              <span className="px-1.5 py-0.5 rounded bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-300 font-bold">
                                {scan.high_count}H
                              </span>
                            )}
                            <span className="text-slate-500">({scan.total_findings})</span>
                          </div>
                        ) : (
                          <span className="text-slate-400">0</span>
                        )}
                      </td>

                      <td className="px-6 py-4 text-xs font-mono text-slate-500">
                        {scan.duration_seconds != null ? `${scan.duration_seconds}s` : '—'}
                      </td>

                      <td className="px-6 py-4 text-xs text-slate-500">
                        {new Date(scan.created_at).toLocaleDateString()}
                      </td>

                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          {isRunning && (
                            <button
                              onClick={() => handleCancelScan(scan.id)}
                              disabled={cancellingId === scan.id}
                              className="text-xs px-2.5 py-1 rounded bg-rose-50 text-rose-600 hover:bg-rose-100 dark:bg-rose-950/50 dark:hover:bg-rose-900 transition-colors"
                            >
                              {cancellingId === scan.id ? 'Cancelling...' : 'Cancel'}
                            </button>
                          )}
                          <Link
                            to={`/dashboard/scans/${scan.id}`}
                            className="btn btn-secondary text-xs px-2.5 py-1 inline-flex items-center gap-1"
                          >
                            Inspect <ChevronRight className="w-3.5 h-3.5" />
                          </Link>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
