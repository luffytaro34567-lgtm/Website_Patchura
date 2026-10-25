import React, { useEffect, useState } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  ScanSearch,
  CheckCircle2,
  XCircle,
  Clock,
  ShieldCheck,
  ShieldAlert,
  AlertOctagon,
  Download,
  StopCircle,
  RefreshCw,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  FileCode,
  Tag,
  Check,
  Copy,
} from 'lucide-react'
import { cancelScan, exportScanSummary, getScanDetails } from '@/api/scans'
import { FindingSeverity, Scan, ScanFinding } from '@/types/scan'
import clsx from 'clsx'

export function ScanDetailsPage() {
  const { scanId } = useParams<{ scanId: string }>()
  const navigate = useNavigate()

  const [scan, setScan] = useState<Scan | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [severityFilter, setSeverityFilter] = useState<string>('all')
  const [search, setSearch] = useState('')
  const [isExporting, setIsExporting] = useState(false)
  const [copiedEvidenceId, setCopiedEvidenceId] = useState<string | null>(null)

  const loadScan = async () => {
    if (!scanId) return
    try {
      const data = await getScanDetails(scanId)
      setScan(data)
    } catch (err: any) {
      setError(err?.userMessage || 'Failed to load vulnerability scan details.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadScan()
  }, [scanId])

  // Polling while scan is queued or running
  useEffect(() => {
    if (!scan || (scan.status !== 'queued' && scan.status !== 'running')) return
    const interval = setInterval(async () => {
      try {
        const fresh = await getScanDetails(scan.id)
        setScan(fresh)
      } catch {
        // silent
      }
    }, 2500)
    return () => clearInterval(interval)
  }, [scan])

  const handleCancel = async () => {
    if (!scan || !confirm('Are you sure you want to stop this scan?')) return
    try {
      const updated = await cancelScan(scan.id)
      setScan(updated)
    } catch (err: any) {
      alert(err?.userMessage || 'Failed to cancel scan.')
    }
  }

  const handleExportJson = async () => {
    if (!scan) return
    try {
      setIsExporting(true)
      const exportData = await exportScanSummary(scan.id)
      const jsonBlob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(jsonBlob)
      const a = document.createElement('a')
      a.href = url
      a.download = `patchora-scan-${scan.target_domain}-${scan.id.slice(0, 8)}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err: any) {
      alert(err?.userMessage || 'Failed to export scan findings summary.')
    } finally {
      setIsExporting(false)
    }
  }

  const handleCopyEvidence = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopiedEvidenceId(id)
    setTimeout(() => setCopiedEvidenceId(null), 2000)
  }

  if (isLoading) {
    return <div className="card p-12 text-center text-slate-400">Loading scan assessment results...</div>
  }

  if (error || !scan) {
    return (
      <div className="card p-8 text-center space-y-4">
        <div className="text-rose-500 font-semibold">{error || 'Scan not found.'}</div>
        <Link to="/dashboard/scans" className="btn btn-secondary inline-flex items-center gap-2 text-sm">
          <ArrowLeft className="w-4 h-4" /> Back to Scans
        </Link>
      </div>
    )
  }

  const isRunning = scan.status === 'running' || scan.status === 'queued'
  const findings = scan.findings || []

  const filteredFindings = findings.filter(f => {
    const matchesSev = severityFilter === 'all' || f.severity === severityFilter
    const matchesSearch =
      f.title.toLowerCase().includes(search.toLowerCase()) ||
      f.category.toLowerCase().includes(search.toLowerCase()) ||
      (f.cwe_id && f.cwe_id.toLowerCase().includes(search.toLowerCase()))
    return matchesSev && matchesSearch
  })

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <Link
          to="/dashboard/scans"
          className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-slate-900 dark:hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Vulnerability Scans
        </Link>

        <div className="flex items-center gap-2">
          {isRunning ? (
            <button
              onClick={handleCancel}
              className="btn btn-secondary text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 text-xs flex items-center gap-1.5"
            >
              <StopCircle className="w-4 h-4" />
              Cancel Scan
            </button>
          ) : (
            <button
              onClick={handleExportJson}
              disabled={isExporting}
              className="btn btn-secondary text-xs flex items-center gap-1.5"
            >
              <Download className="w-4 h-4" />
              {isExporting ? 'Exporting...' : 'Export JSON Summary'}
            </button>
          )}

          <button
            onClick={() => loadScan()}
            className="btn btn-secondary text-xs flex items-center gap-1.5"
            title="Refresh"
          >
            <RefreshCw className={clsx('w-3.5 h-3.5', isRunning && 'animate-spin')} />
          </button>
        </div>
      </div>

      {/* Main Scan Banner */}
      <div className="card p-6 space-y-6">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2 flex-wrap">
              <span
                className={clsx(
                  'px-2.5 py-1 rounded-full text-xs font-semibold capitalize flex items-center gap-1.5',
                  scan.status === 'completed' && 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300',
                  scan.status === 'running' && 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300 animate-pulse',
                  scan.status === 'queued' && 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300',
                  scan.status === 'failed' && 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300',
                  scan.status === 'cancelled' && 'bg-slate-100 text-slate-800 dark:bg-dark-700 dark:text-slate-400'
                )}
              >
                {scan.status === 'completed' && <CheckCircle2 className="w-3.5 h-3.5" />}
                {scan.status === 'running' && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                {scan.status === 'failed' && <XCircle className="w-3.5 h-3.5" />}
                {scan.status === 'cancelled' && <StopCircle className="w-3.5 h-3.5" />}
                Scan {scan.status}
              </span>

              <span className="px-2.5 py-1 rounded-full text-xs font-mono font-medium bg-slate-100 dark:bg-dark-700 text-slate-700 dark:text-slate-300 capitalize">
                Profile: {scan.profile.replace('_', ' ')}
              </span>

              {scan.profile === 'php_deep' && (
                <span className="px-2.5 py-1 rounded-full text-xs font-mono font-semibold bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300">
                  PHP2Shell Shield Active
                </span>
              )}
            </div>

            <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
              {scan.target_domain}
            </h1>
            <a
              href={scan.target_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-slate-400 font-mono hover:text-primary-500 inline-flex items-center gap-1 break-all"
            >
              {scan.target_url} <ExternalLink className="w-3 h-3 flex-shrink-0" />
            </a>
          </div>

          {/* Quick Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs font-mono">
            <div className="p-3 rounded-lg bg-slate-50 dark:bg-dark-750 border border-slate-200 dark:border-dark-700">
              <div className="text-slate-400">Total Findings</div>
              <div className="text-xl font-bold text-slate-900 dark:text-white">{scan.total_findings}</div>
            </div>
            <div className="p-3 rounded-lg bg-slate-50 dark:bg-dark-750 border border-slate-200 dark:border-dark-700">
              <div className="text-slate-400">Scan Duration</div>
              <div className="text-xl font-bold text-slate-900 dark:text-white">
                {scan.duration_seconds != null ? `${scan.duration_seconds}s` : isRunning ? 'In flight' : '—'}
              </div>
            </div>
            <div className="col-span-2 sm:col-span-1 p-3 rounded-lg bg-slate-50 dark:bg-dark-750 border border-slate-200 dark:border-dark-700">
              <div className="text-slate-400">Started</div>
              <div className="text-xs font-semibold text-slate-900 dark:text-white mt-1">
                {scan.started_at ? new Date(scan.started_at).toLocaleTimeString() : 'Queued'}
              </div>
            </div>
          </div>
        </div>

        {/* Progress Bar for Active Scans */}
        {isRunning && (
          <div className="space-y-2 pt-2 border-t border-slate-200 dark:border-dark-700">
            <div className="flex justify-between text-xs text-slate-500">
              <span>Security assessment in progress...</span>
              <span className="font-mono">{scan.progress_percent}%</span>
            </div>
            <div className="w-full bg-slate-200 dark:bg-dark-700 h-2 rounded-full overflow-hidden">
              <div
                className="bg-primary-500 h-full transition-all duration-500"
                style={{ width: `${Math.max(scan.progress_percent, 10)}%` }}
              />
            </div>
          </div>
        )}

        {/* Failure Banner */}
        {scan.status === 'failed' && (
          <div className="p-4 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-300 text-xs space-y-1">
            <div className="font-semibold flex items-center gap-1.5">
              <XCircle className="w-4 h-4" /> Scan Failed
            </div>
            <p>{scan.error_message || 'An error occurred while reaching the target.'}</p>
          </div>
        )}

        {/* Severity Distribution Pills */}
        <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-200 dark:border-dark-700">
          <button
            onClick={() => setSeverityFilter('all')}
            className={clsx(
              'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5',
              severityFilter === 'all'
                ? 'bg-slate-900 text-white dark:bg-white dark:text-dark-900'
                : 'bg-slate-100 dark:bg-dark-750 text-slate-600 dark:text-slate-300'
            )}
          >
            All Findings ({scan.total_findings})
          </button>
          <button
            onClick={() => setSeverityFilter('critical')}
            className={clsx(
              'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5',
              severityFilter === 'critical'
                ? 'bg-rose-600 text-white'
                : 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-900'
            )}
          >
            Critical ({scan.critical_count})
          </button>
          <button
            onClick={() => setSeverityFilter('high')}
            className={clsx(
              'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5',
              severityFilter === 'high'
                ? 'bg-orange-600 text-white'
                : 'bg-orange-50 dark:bg-orange-950/40 text-orange-700 dark:text-orange-300 border border-orange-200 dark:border-orange-900'
            )}
          >
            High ({scan.high_count})
          </button>
          <button
            onClick={() => setSeverityFilter('medium')}
            className={clsx(
              'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5',
              severityFilter === 'medium'
                ? 'bg-amber-600 text-white'
                : 'bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-900'
            )}
          >
            Medium ({scan.medium_count})
          </button>
          <button
            onClick={() => setSeverityFilter('low')}
            className={clsx(
              'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5',
              severityFilter === 'low'
                ? 'bg-blue-600 text-white'
                : 'bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-900'
            )}
          >
            Low ({scan.low_count})
          </button>
          <button
            onClick={() => setSeverityFilter('info')}
            className={clsx(
              'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5',
              severityFilter === 'info'
                ? 'bg-slate-600 text-white'
                : 'bg-slate-100 dark:bg-dark-750 text-slate-600 dark:text-slate-300'
            )}
          >
            Informational ({scan.info_count})
          </button>
        </div>
      </div>

      {/* Findings List Section */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-primary-500" />
            Evidence-Based Findings ({filteredFindings.length})
          </h2>
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search findings title or CWE..."
            className="input text-xs w-full sm:w-64"
          />
        </div>

        {filteredFindings.length === 0 ? (
          <div className="card p-12 text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 mx-auto flex items-center justify-center">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-slate-900 dark:text-white">
              {findings.length === 0 ? 'Zero vulnerabilities detected' : 'No findings match filter'}
            </h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              {findings.length === 0
                ? 'All evaluated endpoints, security headers, cookie flags, and PHP handler probes satisfied the safety criteria.'
                : 'Try adjusting your severity filter or search query.'}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredFindings.map((finding, idx) => (
              <FindingCard
                key={finding.id}
                finding={finding}
                index={idx + 1}
                copiedId={copiedEvidenceId}
                onCopy={handleCopyEvidence}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function FindingCard({
  finding,
  index,
  copiedId,
  onCopy,
}: {
  finding: ScanFinding
  index: number
  copiedId: string | null
  onCopy: (text: string, id: string) => void
}) {
  const [isExpanded, setIsExpanded] = useState(true)

  const isPhp2Shell =
    finding.category === 'PHP2Shell Protection' ||
    (finding.cwe_id && finding.cwe_id.includes('109618')) ||
    finding.title.includes('PHP2Shell')

  return (
    <div
      className={clsx(
        'card p-5 space-y-4 border transition-all',
        isPhp2Shell
          ? 'border-purple-300 dark:border-purple-900/80 bg-purple-50/10 dark:bg-purple-950/10'
          : 'border-slate-200 dark:border-dark-700'
      )}
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
        <div className="space-y-1.5 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className={clsx(
                'px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider',
                finding.severity === 'critical' && 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300',
                finding.severity === 'high' && 'bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-300',
                finding.severity === 'medium' && 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300',
                finding.severity === 'low' && 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300',
                finding.severity === 'info' && 'bg-slate-100 text-slate-700 dark:bg-dark-700 dark:text-slate-300'
              )}
            >
              {finding.severity}
            </span>

            <span className="px-2 py-0.5 rounded text-xs font-medium bg-slate-100 dark:bg-dark-700 text-slate-600 dark:text-slate-300">
              {finding.category}
            </span>

            {finding.cwe_id && (
              <span className="px-2 py-0.5 rounded text-xs font-mono font-semibold bg-slate-100 dark:bg-dark-700 text-slate-700 dark:text-slate-300">
                {finding.cwe_id}
              </span>
            )}

            {finding.cvss_score != null && (
              <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-slate-900 text-white dark:bg-white dark:text-dark-900">
                CVSS {finding.cvss_score}
              </span>
            )}

            {isPhp2Shell && (
              <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-purple-600 text-white">
                CVE-2026-109618 / 19
              </span>
            )}
          </div>

          <h3 className="text-sm sm:text-base font-bold text-slate-900 dark:text-white">
            #{index} {finding.title}
          </h3>
          <div className="text-xs text-slate-400 font-mono break-all">{finding.target_url}</div>
        </div>

        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 self-start p-1.5 min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg"
          aria-label={isExpanded ? 'Collapse finding details' : 'Expand finding details'}
        >
          {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </button>
      </div>

      {isExpanded && (
        <div className="space-y-4 pt-3 border-t border-slate-200 dark:border-dark-700 text-xs">
          {/* Description */}
          <div className="space-y-1">
            <div className="font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider text-[11px]">
              Vulnerability Description
            </div>
            <p className="text-slate-600 dark:text-slate-400 leading-relaxed">{finding.description}</p>
          </div>

          {/* Concrete Evidence Proof */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                <FileCode className="w-3.5 h-3.5 text-primary-500" /> Stored Proof & Evidence
              </span>
              <button
                onClick={() => onCopy(finding.evidence, finding.id)}
                className="text-[11px] text-slate-400 hover:text-slate-200 inline-flex items-center gap-1 min-h-[36px] px-2 rounded"
              >
                {copiedId === finding.id ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                {copiedId === finding.id ? 'Copied' : 'Copy Evidence'}
              </button>
            </div>
            <pre className="p-3 rounded-lg bg-slate-900 text-emerald-400 font-mono text-xs overflow-x-auto whitespace-pre-wrap break-all leading-snug">
              {finding.evidence}
            </pre>
          </div>

          {/* Actionable Remediation */}
          <div className="p-3.5 rounded-lg bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200/80 dark:border-emerald-900/60 space-y-2">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="font-bold text-emerald-800 dark:text-emerald-300 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-500 flex-shrink-0" /> Remediation Guidance
              </div>
              <Link
                to={`/dashboard/remediations?finding_id=${finding.id}`}
                className="inline-flex items-center justify-center gap-1 px-3 py-2 text-xs font-semibold rounded bg-cyan-600 text-white hover:bg-cyan-700 transition shadow-sm min-h-[36px] self-start sm:self-auto"
              >
                ⚡ Request AI Fix
              </Link>
            </div>
            <p className="text-emerald-950 dark:text-emerald-200 whitespace-pre-line leading-relaxed">
              {finding.remediation}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
