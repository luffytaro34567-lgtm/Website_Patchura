import React, { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  ScanSearch,
  Play,
  ShieldCheck,
  ShieldAlert,
  Clock,
  CheckCircle2,
  XCircle,
  AlertOctagon,
  RefreshCw,
  Search,
  ExternalLink,
  ChevronRight,
  Download,
  StopCircle,
  Zap,
} from 'lucide-react'
import { cancelScan, createScan, listScans } from '@/api/scans'
import { listWebsites } from '@/api/websites'
import { Scan, ScanProfile, ScanStatus } from '@/types/scan'
import { Website } from '@/types/website'
import clsx from 'clsx'

const PROFILES: {
  id: ScanProfile
  name: string
  tag: string
  description: string
  checks: string[]
}[] = [
  {
    id: 'standard',
    name: 'Standard Web Application Assessment',
    tag: 'Recommended',
    description: 'Thorough evaluation of HTTP transport, cookie flags, CORS reflections, and sensitive directory exposure.',
    checks: ['HSTS & CSP headers', 'Secure / HttpOnly cookie flags', 'CORS origin wildcards', 'Sensitive .env/.git paths'],
  },
  {
    id: 'php_deep',
    name: 'Targeted PHP & PHP2Shell Assessment',
    tag: 'Zero-Day Shield',
    description: 'Deep audit for PHP stack disclosure and memory corruption in custom error handlers (CVE-2026-109618 / 19).',
    checks: ['PHP2Shell memory fault detection', 'Verbose display_errors leakage', 'X-Powered-By header analysis', 'phpinfo.php exposure'],
  },
  {
    id: 'passive',
    name: 'Passive Transport & Header Audit',
    tag: 'Fast & Non-Intrusive',
    description: 'Lightweight passive inspection analyzing TLS configurations, clickjacking headers, and version banners.',
    checks: ['Strict-Transport-Security', 'X-Frame-Options clickjacking', 'X-Content-Type-Options', 'Referrer-Policy'],
  },
]

export function ClientScansPage() {
  const navigate = useNavigate()
  const [scans, setScans] = useState<Scan[]>([])
  const [websites, setWebsites] = useState<Website[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [search, setSearch] = useState('')

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedWebsiteId, setSelectedWebsiteId] = useState<string>('')
  const [selectedProfile, setSelectedProfile] = useState<ScanProfile>('standard')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [modalError, setModalError] = useState<string | null>(null)

  const loadData = async () => {
    try {
      const [scansData, websitesData] = await Promise.all([
        listScans(),
        listWebsites(),
      ])
      setScans(scansData)
      setWebsites(websitesData)
    } catch (err: any) {
      setError(err?.userMessage || 'Failed to load scans data.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  // Auto-refresh when any scan is queued or running
  useEffect(() => {
    const hasActive = scans.some(s => s.status === 'queued' || s.status === 'running')
    if (!hasActive) return

    const interval = setInterval(async () => {
      try {
        const fresh = await listScans()
        setScans(fresh)
      } catch {
        // silent polling failure
      }
    }, 3000)

    return () => clearInterval(interval)
  }, [scans])

  const handleStartScan = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedWebsiteId) {
      setModalError('Please select a target website.')
      return
    }

    try {
      setIsSubmitting(true)
      setModalError(null)
      const newScan = await createScan({
        website_id: selectedWebsiteId,
        profile: selectedProfile,
      })
      setIsModalOpen(false)
      setScans(prev => [newScan, ...prev])
      navigate(`/dashboard/scans/${newScan.id}`)
    } catch (err: any) {
      setModalError(err?.userMessage || 'Failed to initiate vulnerability scan.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCancelScan = async (scanId: string) => {
    if (!confirm('Are you sure you want to cancel this in-progress scan?')) return
    try {
      const updated = await cancelScan(scanId)
      setScans(prev => prev.map(s => (s.id === scanId ? updated : s)))
    } catch (err: any) {
      alert(err?.userMessage || 'Failed to cancel scan.')
    }
  }

  const filteredScans = scans.filter(s => {
    const matchesStatus = statusFilter === 'all' || s.status === statusFilter
    const matchesSearch =
      s.target_url.toLowerCase().includes(search.toLowerCase()) ||
      s.target_domain.toLowerCase().includes(search.toLowerCase())
    return matchesStatus && matchesSearch
  })

  const eligibleWebsites = websites.filter(
    w => w.verification_status === 'verified' && w.authorization?.is_authorized && !w.authorization?.is_revoked && !w.is_suspended_by_admin
  )

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-slate-200 dark:border-dark-700 pb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <ScanSearch className="w-6 h-6 text-primary-500" />
            Vulnerability Scans
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Execute safe, authorized security assessments and track evidence-based findings
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => loadData()}
            className="btn btn-secondary flex items-center gap-2 text-sm"
            title="Refresh scan history"
          >
            <RefreshCw className={clsx('w-4 h-4', isLoading && 'animate-spin')} />
            Refresh
          </button>
          <button
            onClick={() => {
              setModalError(null)
              setSelectedWebsiteId(eligibleWebsites[0]?.id || '')
              setIsModalOpen(true)
            }}
            className="btn btn-primary flex items-center gap-2 text-sm"
          >
            <Play className="w-4 h-4" />
            Start Authorized Scan
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-400 text-sm flex items-center gap-2">
          <XCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Filters & Search */}
      <div className="card p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search target URL or domain..."
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

      {/* Scans Table / List */}
      {isLoading ? (
        <div className="card p-12 text-center text-slate-400">Loading vulnerability scan history...</div>
      ) : filteredScans.length === 0 ? (
        <div className="card p-12 text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-primary-100 dark:bg-primary-950 text-primary-600 dark:text-primary-400 mx-auto flex items-center justify-center">
            <ScanSearch className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-slate-900 dark:text-white">No scans found</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 max-w-sm mx-auto">
              {scans.length === 0
                ? 'Select a verified target website with active authorization to launch your first security assessment.'
                : 'No vulnerability scans match your current filter criteria.'}
            </p>
          </div>
          {scans.length === 0 && (
            <button
              onClick={() => {
                setSelectedWebsiteId(eligibleWebsites[0]?.id || '')
                setIsModalOpen(true)
              }}
              className="btn btn-primary text-sm inline-flex items-center gap-2"
            >
              <Play className="w-4 h-4" />
              Configure & Run Scan
            </button>
          )}
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 dark:bg-dark-700/50 text-slate-600 dark:text-slate-400 text-xs font-semibold uppercase tracking-wider border-b border-slate-200 dark:border-dark-700">
                <tr>
                  <th className="px-6 py-3.5">Target Website</th>
                  <th className="px-6 py-3.5">Profile</th>
                  <th className="px-6 py-3.5">Status & Progress</th>
                  <th className="px-6 py-3.5">Findings Summary</th>
                  <th className="px-6 py-3.5">Duration</th>
                  <th className="px-6 py-3.5">Executed</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-dark-700">
                {filteredScans.map(scan => {
                  const isRunning = scan.status === 'running' || scan.status === 'queued'

                  return (
                    <tr key={scan.id} className="hover:bg-slate-50/50 dark:hover:bg-dark-750/50 transition-colors">
                      <td className="px-6 py-4">
                        <div className="font-medium text-slate-900 dark:text-white">{scan.target_domain}</div>
                        <div className="text-xs text-slate-400 truncate max-w-xs">{scan.target_url}</div>
                      </td>

                      <td className="px-6 py-4">
                        <span className="capitalize font-mono text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-dark-700 text-slate-700 dark:text-slate-300">
                          {scan.profile.replace('_', ' ')}
                        </span>
                      </td>

                      <td className="px-6 py-4">
                        <div className="space-y-1.5">
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
                            {scan.status === 'running' && <RefreshCw className="w-3 h-3 animate-spin" />}
                            {scan.status === 'completed' && <CheckCircle2 className="w-3 h-3" />}
                            {scan.status === 'failed' && <XCircle className="w-3 h-3" />}
                            {scan.status === 'cancelled' && <StopCircle className="w-3 h-3" />}
                            {scan.status}
                          </span>

                          {isRunning && (
                            <div className="w-24 bg-slate-200 dark:bg-dark-700 h-1.5 rounded-full overflow-hidden">
                              <div
                                className="bg-primary-500 h-full transition-all duration-500"
                                style={{ width: `${Math.max(scan.progress_percent, 10)}%` }}
                              />
                            </div>
                          )}
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        {scan.status === 'completed' ? (
                          <div className="flex items-center gap-1.5 text-xs font-mono">
                            {scan.critical_count > 0 && (
                              <span className="px-1.5 py-0.5 rounded bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300 font-bold">
                                {scan.critical_count} Crit
                              </span>
                            )}
                            {scan.high_count > 0 && (
                              <span className="px-1.5 py-0.5 rounded bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-300 font-bold">
                                {scan.high_count} High
                              </span>
                            )}
                            {scan.medium_count > 0 && (
                              <span className="px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">
                                {scan.medium_count} Med
                              </span>
                            )}
                            {scan.low_count > 0 && (
                              <span className="px-1.5 py-0.5 rounded bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300">
                                {scan.low_count} Low
                              </span>
                            )}
                            {scan.total_findings === 0 && (
                              <span className="text-emerald-600 dark:text-emerald-400 font-semibold">0 findings</span>
                            )}
                          </div>
                        ) : scan.status === 'failed' ? (
                          <span className="text-xs text-rose-500 truncate max-w-xs block" title={scan.error_message || ''}>
                            {scan.error_message || 'Scan failed'}
                          </span>
                        ) : (
                          <span className="text-xs text-slate-400">Assessing...</span>
                        )}
                      </td>

                      <td className="px-6 py-4 text-xs font-mono text-slate-500">
                        {scan.duration_seconds != null ? `${scan.duration_seconds}s` : '—'}
                      </td>

                      <td className="px-6 py-4 text-xs text-slate-500">
                        {new Date(scan.created_at).toLocaleDateString()}{' '}
                        {new Date(scan.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </td>

                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          {isRunning ? (
                            <button
                              onClick={() => handleCancelScan(scan.id)}
                              className="text-xs px-2.5 py-1 rounded bg-rose-50 text-rose-600 hover:bg-rose-100 dark:bg-rose-950/50 dark:hover:bg-rose-900 transition-colors"
                            >
                              Cancel
                            </button>
                          ) : null}
                          <Link
                            to={`/dashboard/scans/${scan.id}`}
                            className="btn btn-secondary text-xs px-2.5 py-1 inline-flex items-center gap-1"
                          >
                            Details <ChevronRight className="w-3.5 h-3.5" />
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

      {/* Start Scan Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="card w-full max-w-2xl p-6 space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-dark-700 pb-4">
              <div className="flex items-center gap-2">
                <div className="w-9 h-9 rounded-lg bg-primary-100 dark:bg-primary-950 text-primary-600 dark:text-primary-400 flex items-center justify-center">
                  <Play className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white">Launch Authorized Scan</h2>
                  <p className="text-xs text-slate-500">Verify targets and select safety-compliant profile</p>
                </div>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg"
                aria-label="Close modal"
              >
                ✕
              </button>
            </div>

            {modalError && (
              <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-400 text-xs flex items-center gap-2">
                <XCircle className="w-4 h-4 flex-shrink-0" />
                <span>{modalError}</span>
              </div>
            )}

            <form onSubmit={handleStartScan} className="space-y-6">
              {/* Target Website Selection */}
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-900 dark:text-white flex items-center justify-between">
                  <span>1. Select Verified Target Website</span>
                  <Link to="/dashboard/websites" className="text-xs text-primary-600 hover:underline">
                    Manage Targets →
                  </Link>
                </label>

                {eligibleWebsites.length === 0 ? (
                  <div className="p-4 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-amber-800 dark:text-amber-300 text-xs space-y-2">
                    <p className="font-semibold flex items-center gap-1.5">
                      <AlertOctagon className="w-4 h-4" />
                      No eligible target websites available
                    </p>
                    <p>
                      To prevent unauthorized testing, scans can only run on targets with verified domain control and an active scan authorization warrant.
                    </p>
                    <Link
                      to="/dashboard/websites"
                      className="btn btn-secondary text-xs inline-flex items-center gap-1 mt-1"
                    >
                      Verify or Authorize a Website
                    </Link>
                  </div>
                ) : (
                  <div className="grid gap-2">
                    {eligibleWebsites.map(ws => (
                      <label
                        key={ws.id}
                        className={clsx(
                          'p-3.5 rounded-lg border text-sm flex items-center justify-between cursor-pointer transition-colors',
                          selectedWebsiteId === ws.id
                            ? 'border-primary-500 bg-primary-50/50 dark:bg-primary-950/20'
                            : 'border-slate-200 dark:border-dark-700 hover:bg-slate-50 dark:hover:bg-dark-750'
                        )}
                      >
                        <div className="flex items-center gap-3">
                          <input
                            type="radio"
                            name="website"
                            value={ws.id}
                            checked={selectedWebsiteId === ws.id}
                            onChange={() => setSelectedWebsiteId(ws.id)}
                            className="text-primary-600 focus:ring-primary-500"
                          />
                          <div>
                            <div className="font-medium text-slate-900 dark:text-white">{ws.name}</div>
                            <div className="text-xs text-slate-400 font-mono">{ws.target_url}</div>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                            Verified
                          </span>
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300">
                            Authorized
                          </span>
                        </div>
                      </label>
                    ))}
                  </div>
                )}
              </div>

              {/* Scan Profile Selection */}
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-900 dark:text-white">
                  2. Select Assessment Profile
                </label>
                <div className="grid gap-3">
                  {PROFILES.map(prof => (
                    <div
                      key={prof.id}
                      onClick={() => setSelectedProfile(prof.id)}
                      className={clsx(
                        'p-4 rounded-lg border text-left cursor-pointer transition-all space-y-2',
                        selectedProfile === prof.id
                          ? 'border-primary-500 bg-primary-50/30 dark:bg-primary-950/20 ring-1 ring-primary-500'
                          : 'border-slate-200 dark:border-dark-700 hover:bg-slate-50 dark:hover:bg-dark-750'
                      )}
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div className="font-semibold text-slate-900 dark:text-white text-xs sm:text-sm flex flex-wrap items-center gap-1.5 sm:gap-2">
                          <span>{prof.name}</span>
                          <span className="text-[10px] px-2 py-0.5 rounded font-mono font-semibold bg-primary-100 text-primary-800 dark:bg-primary-950 dark:text-primary-300">
                            {prof.tag}
                          </span>
                        </div>
                        <input
                          type="radio"
                          name="profile"
                          value={prof.id}
                          checked={selectedProfile === prof.id}
                          onChange={() => setSelectedProfile(prof.id)}
                          className="text-primary-600 focus:ring-primary-500 self-end sm:self-center"
                        />
                      </div>
                      <p className="text-xs text-slate-500 dark:text-slate-400">{prof.description}</p>
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {prof.checks.map(c => (
                          <span
                            key={c}
                            className="text-[10px] px-2 py-0.5 rounded bg-slate-100 dark:bg-dark-700 text-slate-600 dark:text-slate-300"
                          >
                            ✓ {c}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Safe Scan Disclaimer */}
              <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-dark-750 border border-slate-200 dark:border-dark-700 text-xs text-slate-500 dark:text-slate-400 space-y-1">
                <div className="font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-emerald-500" />
                  Non-Destructive Scanning Policy
                </div>
                <p>
                  Scans use non-destructive GET/HEAD queries with rate-limiting and strictly honor SSRF prevention boundaries. No denial of service or exploit payload injection is ever performed.
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200 dark:border-dark-700">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="btn btn-secondary text-sm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || eligibleWebsites.length === 0}
                  className="btn btn-primary text-sm flex items-center gap-2"
                >
                  {isSubmitting ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Dispatching Scan...
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4" />
                      Start Assessment
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
