import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  FileText,
  ShieldCheck,
  Lock,
  Unlock,
  CheckCircle2,
  Clock,
  ExternalLink,
  ChevronRight,
  RefreshCw,
  Search,
  Sparkles,
} from 'lucide-react'
import { listScans } from '@/api/scans'
import { listMyReports } from '@/api/reports'
import { Scan } from '@/types/scan'
import { ReportEntitlement } from '@/types/report'
import clsx from 'clsx'

export function ReportsListPage() {
  const [scans, setScans] = useState<Scan[]>([])
  const [entitlements, setEntitlements] = useState<ReportEntitlement[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')

  const loadData = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const [allScans, myEntitlements] = await Promise.all([
        listScans(undefined, 'completed'),
        listMyReports(),
      ])
      setScans(allScans)
      setEntitlements(myEntitlements)
    } catch (err: any) {
      setError(err?.userMessage || 'Failed to load reports directory.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const entitlementMap = new Map(entitlements.map(e => [e.scan_id, e]))

  const filteredScans = scans.filter(s =>
    s.target_domain.toLowerCase().includes(search.toLowerCase()) ||
    s.target_url.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-slate-200 dark:border-dark-700 pb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <FileText className="w-6 h-6 text-primary-500" />
            Security & Vulnerability Reports
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Access executive vulnerability assessments, CVSS impact breakdowns, and developer remediation playbooks
          </p>
        </div>
        <button
          onClick={loadData}
          className="btn btn-secondary flex items-center gap-2 text-sm self-start sm:self-auto"
        >
          <RefreshCw className={clsx('w-4 h-4', isLoading && 'animate-spin')} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-400 text-sm">
          {error}
        </div>
      )}

      {/* Pricing Teaser Card */}
      <div className="card p-6 bg-gradient-to-r from-primary-900/10 via-purple-900/10 to-transparent border-primary-500/20">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-primary-100 text-primary-800 dark:bg-primary-950 dark:text-primary-300">
                PAID REPORT TIER
              </span>
              <span className="text-xs text-slate-500 dark:text-slate-400">Fixed $49.00 USD per scan</span>
            </div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Unlock Comprehensive Executive & Technical Reports
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-xl">
              Includes full executive risk scoring, unredacted concrete proof blocks, CVSS v3.1 impact matrices,
              compliance mapping, and zero-day defense verification for PHP2Shell (CVE-2026-109618 / 19).
            </p>
          </div>
          <div className="text-xs text-slate-400 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
            <span>Free basic severity count summaries included for all scans</span>
          </div>
        </div>
      </div>

      {/* Filter and Search */}
      <div className="card p-4">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search report by domain or URL..."
            className="input pl-9 text-sm w-full"
          />
        </div>
      </div>

      {/* Reports Directory */}
      {isLoading ? (
        <div className="card p-12 text-center text-slate-400">Loading reports directory...</div>
      ) : filteredScans.length === 0 ? (
        <div className="card p-12 text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-primary-100 dark:bg-primary-950 text-primary-600 dark:text-primary-400 mx-auto flex items-center justify-center">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-slate-900 dark:text-white">No completed scans yet</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 max-w-sm mx-auto">
              Run an authorized vulnerability scan on your verified website first. Reports become available once a scan completes.
            </p>
          </div>
          <Link to="/dashboard/scans" className="btn btn-primary text-sm inline-flex items-center gap-2">
            Go to Vulnerability Scans
          </Link>
        </div>
      ) : (
        <div className="grid gap-4">
          {filteredScans.map(scan => {
            const hasEntitlement = entitlementMap.has(scan.id)

            return (
              <div
                key={scan.id}
                className="card p-5 hover:border-primary-500/50 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="space-y-1.5 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    {hasEntitlement ? (
                      <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 flex items-center gap-1">
                        <Unlock className="w-3 h-3" /> Report Unlocked
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300 flex items-center gap-1">
                        <Lock className="w-3 h-3" /> Report Available ($49)
                      </span>
                    )}

                    <span className="px-2 py-0.5 rounded text-xs font-mono bg-slate-100 dark:bg-dark-700 text-slate-600 dark:text-slate-300 capitalize">
                      {scan.profile.replace('_', ' ')}
                    </span>

                    {scan.critical_count > 0 && (
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300">
                        {scan.critical_count} Critical
                      </span>
                    )}
                  </div>

                  <h3 className="text-base font-bold text-slate-900 dark:text-white">
                    {scan.target_domain}
                  </h3>
                  <div className="text-xs text-slate-400 font-mono truncate">{scan.target_url}</div>
                </div>

                <div className="flex flex-col sm:flex-row sm:items-center gap-4 text-xs font-mono text-slate-500">
                  <div className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5" />
                    <span>
                      {new Date(scan.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  <Link
                    to={`/dashboard/reports/${scan.id}`}
                    className={clsx(
                      'btn text-xs px-3 py-1.5 inline-flex items-center gap-1.5 whitespace-nowrap',
                      hasEntitlement ? 'btn-primary' : 'btn-secondary'
                    )}
                  >
                    {hasEntitlement ? 'View Detailed Report' : 'Unlock Report ($49)'}
                    <ChevronRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
