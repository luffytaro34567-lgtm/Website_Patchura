import React, { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  FileText,
  ArrowLeft,
  Lock,
  Unlock,
  ShieldCheck,
  ShieldAlert,
  Download,
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  FileCode,
  AlertOctagon,
  RefreshCw,
  CreditCard,
} from 'lucide-react'
import {
  completeReportOrder,
  createReportOrder,
  downloadReportHtml,
  getDetailedReport,
  getReportStatus,
} from '@/api/reports'
import { DetailedReport, ReportEntitlementStatus, ReportOrder } from '@/types/report'
import { ScanFinding } from '@/types/scan'
import clsx from 'clsx'

export function DetailedReportPage() {
  const { scanId } = useParams<{ scanId: string }>()

  const [statusData, setStatusData] = useState<ReportEntitlementStatus | null>(null)
  const [report, setReport] = useState<DetailedReport | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Checkout modal
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false)
  const [simulateOutcome, setSimulateOutcome] = useState<'completed' | 'failed' | 'cancelled'>('completed')
  const [isProcessingOrder, setIsProcessingOrder] = useState(false)
  const [orderError, setOrderError] = useState<string | null>(null)
  const [orderResult, setOrderResult] = useState<ReportOrder | null>(null)

  // Filters
  const [severityFilter, setSeverityFilter] = useState('all')
  const [search, setSearch] = useState('')
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [isDownloading, setIsDownloading] = useState(false)

  const loadData = async () => {
    if (!scanId) return
    try {
      setIsLoading(true)
      setError(null)
      const st = await getReportStatus(scanId)
      setStatusData(st)

      if (st.has_entitlement) {
        const rep = await getDetailedReport(scanId)
        setReport(rep)
      }
    } catch (err: any) {
      setError(err?.userMessage || 'Failed to load report.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [scanId])

  const handleCheckout = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!scanId) return

    try {
      setIsProcessingOrder(true)
      setOrderError(null)

      // 1. Initiate order
      const order = await createReportOrder(scanId, 'dev_checkout')

      // 2. Complete order with requested simulation outcome
      const completedOrder = await completeReportOrder(order.id, simulateOutcome)
      setOrderResult(completedOrder)

      if (completedOrder.status === 'completed') {
        // Reload full report data
        await loadData()
        setIsCheckoutOpen(false)
      } else {
        setOrderError(
          completedOrder.failure_reason || `Order ended with status: ${completedOrder.status}`
        )
      }
    } catch (err: any) {
      setOrderError(err?.userMessage || 'Failed to process report order.')
    } finally {
      setIsProcessingOrder(false)
    }
  }

  const handleDownload = async () => {
    if (!scanId || !report) return
    try {
      setIsDownloading(true)
      await downloadReportHtml(scanId, report.target_domain)
    } catch (err: any) {
      alert(err?.userMessage || 'Failed to download report HTML.')
    } finally {
      setIsDownloading(false)
    }
  }

  const handleCopyEvidence = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  if (isLoading) {
    return <div className="card p-12 text-center text-slate-400">Loading vulnerability report...</div>
  }

  if (error || !statusData) {
    return (
      <div className="card p-8 text-center space-y-4">
        <div className="text-rose-500 font-semibold">{error || 'Report not found.'}</div>
        <Link to="/dashboard/reports" className="btn btn-secondary inline-flex items-center gap-2 text-sm">
          <ArrowLeft className="w-4 h-4" /> Back to Reports
        </Link>
      </div>
    )
  }

  // ── Render Locked / Unpurchased State ───────────────────────────────────────
  if (!statusData.has_entitlement) {
    return (
      <div className="space-y-6">
        <Link
          to="/dashboard/reports"
          className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-slate-900 dark:hover:text-white"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Reports
        </Link>

        {/* Lock Banner & Pricing */}
        <div className="card p-8 border-primary-500/30 space-y-8">
          <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
            <div className="space-y-3 max-w-2xl">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 flex items-center gap-1.5">
                  <Lock className="w-3.5 h-3.5" /> Detailed Report Locked
                </span>
                <span className="text-xs text-slate-400">Free Summary Active</span>
              </div>

              <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                Comprehensive Vulnerability & Remediation Report
              </h1>
              <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                {statusData.pricing.description}
              </p>
            </div>

            <div className="p-5 rounded-xl bg-slate-50 dark:bg-dark-750 border border-slate-200 dark:border-dark-700 text-center space-y-3 min-w-[220px]">
              <div className="text-xs text-slate-400 uppercase font-semibold">Report Access Fee</div>
              <div className="text-3xl font-extrabold text-slate-900 dark:text-white">
                ${statusData.pricing.price.toFixed(2)}
                <span className="text-xs font-normal text-slate-400 ml-1">{statusData.pricing.currency}</span>
              </div>
              <button
                onClick={() => {
                  setOrderError(null)
                  setIsCheckoutOpen(true)
                }}
                className="btn btn-primary w-full text-sm flex items-center justify-center gap-2"
              >
                <Unlock className="w-4 h-4" /> Unlock Report
              </button>
            </div>
          </div>

          {/* Included Features */}
          <div className="space-y-3 pt-6 border-t border-slate-200 dark:border-dark-700">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-primary-500" />
              What is included in this detailed report:
            </h3>
            <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-3">
              {statusData.pricing.features.map(feat => (
                <div
                  key={feat}
                  className="p-3 rounded-lg bg-slate-50 dark:bg-dark-750 border border-slate-200 dark:border-dark-700 text-xs text-slate-700 dark:text-slate-300 flex items-center gap-2"
                >
                  <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                  <span>{feat}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Checkout Modal */}
        {isCheckoutOpen && (
          <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4 overflow-y-auto">
            <div className="card w-full max-w-lg p-4 sm:p-6 space-y-4 sm:space-y-6 max-h-[90vh] overflow-y-auto my-auto">
              <div className="flex items-center justify-between border-b border-slate-200 dark:border-dark-700 pb-3">
                <div className="flex items-center gap-2">
                  <CreditCard className="w-5 h-5 text-primary-500" />
                  <h2 className="text-base sm:text-lg font-bold text-slate-900 dark:text-white">Report Access Checkout</h2>
                </div>
                <button
                  onClick={() => setIsCheckoutOpen(false)}
                  className="text-slate-400 hover:text-slate-200 min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg"
                  aria-label="Close checkout"
                >
                  ✕
                </button>
              </div>

              {orderError && (
                <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-400 text-xs flex items-center gap-2">
                  <XCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{orderError}</span>
                </div>
              )}

              <form onSubmit={handleCheckout} className="space-y-4">
                <div className="p-4 rounded-lg bg-slate-50 dark:bg-dark-750 border border-slate-200 dark:border-dark-700 text-xs space-y-2">
                  <div className="flex justify-between font-semibold text-slate-900 dark:text-white">
                    <span>{statusData.pricing.product_name}</span>
                    <span>${statusData.pricing.price.toFixed(2)} USD</span>
                  </div>
                  <p className="text-slate-400">
                    One-time access entitlement for this scan report. Includes continuous access, printable HTML download, and proof evidence.
                  </p>
                </div>

                {/* Workflow Simulation Options */}
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Payment Gateway Verification Workflow
                  </label>
                  <p className="text-[11px] text-slate-400">
                    Phase 6 enforces real entitlement access controls. Select test outcome to verify lifecycle behavior:
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1">
                    {[
                      { id: 'completed', label: 'Success (Authorize & Unlock)' },
                      { id: 'failed', label: 'Simulate Payment Failure' },
                      { id: 'cancelled', label: 'Cancel Checkout' },
                    ].map(opt => (
                      <button
                        type="button"
                        key={opt.id}
                        onClick={() => setSimulateOutcome(opt.id as any)}
                        className={clsx(
                          'p-2.5 rounded-lg border text-[11px] font-medium text-center transition-all',
                          simulateOutcome === opt.id
                            ? 'border-primary-500 bg-primary-50 dark:bg-primary-950 text-primary-700 dark:text-primary-300'
                            : 'border-slate-200 dark:border-dark-700 hover:bg-slate-50 dark:hover:bg-dark-750 text-slate-600 dark:text-slate-400'
                        )}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200 dark:border-dark-700">
                  <button
                    type="button"
                    onClick={() => setIsCheckoutOpen(false)}
                    className="btn btn-secondary text-xs"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isProcessingOrder}
                    className="btn btn-primary text-xs flex items-center gap-1.5"
                  >
                    {isProcessingOrder ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        Processing Order...
                      </>
                    ) : (
                      <>
                        <Unlock className="w-3.5 h-3.5" />
                        Confirm & Unlock (${statusData.pricing.price.toFixed(2)})
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

  // ── Render Unlocked / Entitled Detailed Report ──────────────────────────────
  if (!report) {
    return <div className="card p-12 text-center text-slate-400">Generating report document...</div>
  }

  const findings = report.findings || []
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
      {/* Top Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <Link
          to="/dashboard/reports"
          className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-slate-900 dark:hover:text-white"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Reports Directory
        </Link>

        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 flex items-center gap-1.5">
            <Unlock className="w-3.5 h-3.5" /> Entitlement Active
          </span>

          <button
            onClick={handleDownload}
            disabled={isDownloading}
            className="btn btn-primary text-xs flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5" />
            {isDownloading ? 'Downloading...' : 'Download Printable Report (HTML)'}
          </button>
        </div>
      </div>

      {/* Executive Risk Card */}
      <div className="card p-6 space-y-6">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div className="space-y-2">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
              {report.title}
            </h1>
            <a
              href={report.target_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-slate-400 font-mono hover:text-primary-500 inline-flex items-center gap-1"
            >
              {report.target_url} <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          {/* Risk Score Pill */}
          <div className="p-4 rounded-xl bg-slate-900 text-white dark:bg-dark-750 text-center min-w-[180px] space-y-1">
            <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">Overall Risk Score</div>
            <div className="text-3xl font-extrabold text-rose-400">
              {report.overall_risk_score} <span className="text-xs text-slate-400">/ 10.0</span>
            </div>
            <div className="text-[10px] font-bold text-amber-300 tracking-wider uppercase">
              {report.overall_posture}
            </div>
          </div>
        </div>

        {/* Executive Summary */}
        <div className="p-4 rounded-lg bg-slate-50 dark:bg-dark-750 border-l-4 border-primary-500 text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
          <strong>Executive Summary:</strong> {report.executive_summary}
        </div>

        {/* PHP2Shell Zero-Day Posture Callout */}
        <div
          className={clsx(
            'p-4 rounded-lg border text-xs space-y-1',
            report.has_php2shell_finding
              ? 'bg-purple-950/20 border-purple-800 text-purple-300'
              : 'bg-emerald-950/20 border-emerald-800 text-emerald-300'
          )}
        >
          <div className="font-bold flex items-center gap-1.5 uppercase tracking-wider text-[11px]">
            <ShieldCheck className="w-4 h-4 text-purple-400" />
            PHP2Shell Zero-Day Posture (CVE-2026-109618 / CVE-2026-109619)
          </div>
          <p>{report.php2shell_posture}</p>
        </div>

        {/* Severity Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-2 border-t border-slate-200 dark:border-dark-700">
          {[
            { label: 'Critical', count: report.severity_breakdown['critical'] || 0, color: 'text-rose-500' },
            { label: 'High', count: report.severity_breakdown['high'] || 0, color: 'text-orange-500' },
            { label: 'Medium', count: report.severity_breakdown['medium'] || 0, color: 'text-amber-500' },
            { label: 'Low', count: report.severity_breakdown['low'] || 0, color: 'text-blue-500' },
            { label: 'Info', count: report.severity_breakdown['info'] || 0, color: 'text-slate-400' },
          ].map(s => (
            <div key={s.label} className="p-3 rounded-lg bg-slate-50 dark:bg-dark-750 text-center">
              <div className="text-[10px] text-slate-400 uppercase font-mono">{s.label}</div>
              <div className={clsx('text-xl font-bold font-mono', s.color)}>{s.count}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Findings Section */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-primary-500" />
            Detailed Technical Findings & Remediation ({filteredFindings.length})
          </h2>
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search findings title or CWE..."
            className="input text-xs w-full sm:w-64"
          />
        </div>

        {/* Severity Filters */}
        <div className="flex flex-wrap gap-2">
          {['all', 'critical', 'high', 'medium', 'low', 'info'].map(sev => (
            <button
              key={sev}
              onClick={() => setSeverityFilter(sev)}
              className={clsx(
                'px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors',
                severityFilter === sev
                  ? 'bg-primary-600 text-white'
                  : 'bg-slate-100 dark:bg-dark-750 text-slate-600 dark:text-slate-300'
              )}
            >
              {sev}
            </button>
          ))}
        </div>

        {filteredFindings.map((finding, idx) => (
          <DetailedFindingCard
            key={finding.id}
            finding={finding}
            index={idx + 1}
            copiedId={copiedId}
            onCopy={handleCopyEvidence}
          />
        ))}
      </div>
    </div>
  )
}

function DetailedFindingCard({
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

  return (
    <div className="card p-5 space-y-4 border border-slate-200 dark:border-dark-700">
      <div className="flex items-start justify-between gap-3">
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
          </div>

          <h3 className="text-sm sm:text-base font-bold text-slate-900 dark:text-white">
            #{index} {finding.title}
          </h3>
          <div className="text-xs text-slate-400 font-mono break-all">{finding.target_url}</div>
        </div>

        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-slate-400 hover:text-slate-200 min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg self-start"
          aria-label={isExpanded ? 'Collapse finding' : 'Expand finding'}
        >
          {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </button>
      </div>

      {isExpanded && (
        <div className="space-y-4 pt-3 border-t border-slate-200 dark:border-dark-700 text-xs">
          <div className="space-y-1">
            <div className="font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider text-[11px]">
              Vulnerability Description
            </div>
            <p className="text-slate-600 dark:text-slate-400 leading-relaxed">{finding.description}</p>
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                <FileCode className="w-3.5 h-3.5 text-primary-500" /> Stored Proof & Evidence
              </span>
              <button
                onClick={() => onCopy(finding.evidence, finding.id)}
                className="text-[11px] text-slate-400 hover:text-slate-200 inline-flex items-center gap-1"
              >
                {copiedId === finding.id ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                {copiedId === finding.id ? 'Copied' : 'Copy Evidence'}
              </button>
            </div>
            <pre className="p-3 rounded-lg bg-slate-900 text-emerald-400 font-mono text-xs overflow-x-auto whitespace-pre-wrap leading-snug">
              {finding.evidence}
            </pre>
          </div>

          <div className="p-3.5 rounded-lg bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200/80 dark:border-emerald-900/60 space-y-1.5">
            <div className="font-bold text-emerald-800 dark:text-emerald-300 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-500" /> Remediation Playbook
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
