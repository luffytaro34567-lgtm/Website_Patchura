import React, { useEffect, useState } from 'react'
import {
  fetchActivityMetrics,
  fetchActivityTimeline,
  fetchBackgroundJobs,
  fetchSecurityAlerts,
  reviewActivityLog,
  triageSecurityAlert,
} from '@/api/activity'
import {
  ActivityLog,
  ActivitySummaryMetrics,
  BackgroundJobStatus,
  SecurityAlert,
} from '@/types/activity'
import {
  Activity,
  AlertOctagon,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Filter,
  RefreshCw,
  Search,
  Server,
  Shield,
  ShieldAlert,
  UserCheck,
  Users,
  XCircle,
  Eye,
  FileText,
  CreditCard,
  Wrench,
  GitPullRequest,
  Send,
} from 'lucide-react'
import clsx from 'clsx'

export const AdminActivityCenterPage: React.FC = () => {
  const [metrics, setMetrics] = useState<ActivitySummaryMetrics | null>(null)
  const [timeline, setTimeline] = useState<ActivityLog[]>([])
  const [alerts, setAlerts] = useState<SecurityAlert[]>([])
  const [jobs, setJobs] = useState<BackgroundJobStatus[]>([])

  const [activeTab, setActiveTab] = useState<'timeline' | 'alerts' | 'jobs'>('timeline')
  const [timeframe, setTimeframe] = useState<string>('24h')
  const [fromDate, setFromDate] = useState<string>('')
  const [toDate, setToDate] = useState<string>('')

  // Timeline Filters
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [categoryFilter, setCategoryFilter] = useState<string>('')
  const [severityFilter, setSeverityFilter] = useState<string>('')
  const [outcomeFilter, setOutcomeFilter] = useState<string>('')
  const [requiresReviewFilter, setRequiresReviewFilter] = useState<boolean>(false)

  // Alerts Filters
  const [alertStatusFilter, setAlertStatusFilter] = useState<string>('')
  const [alertSeverityFilter, setAlertSeverityFilter] = useState<string>('')

  // Triage Modal
  const [selectedAlert, setSelectedAlert] = useState<SecurityAlert | null>(null)
  const [triageStatus, setTriageStatus] = useState<string>('resolved')
  const [resolutionNotes, setResolutionNotes] = useState<string>('')
  const [expandedLogId, setExpandedLogId] = useState<string | null>(null)

  const [loading, setLoading] = useState<boolean>(true)
  const [actionLoading, setActionLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  useEffect(() => {
    loadAll()
  }, [timeframe, fromDate, toDate, categoryFilter, severityFilter, outcomeFilter, requiresReviewFilter, alertStatusFilter, alertSeverityFilter])

  const loadAll = async () => {
    try {
      setLoading(true)
      const [mRes, tRes, aRes, jRes] = await Promise.all([
        fetchActivityMetrics({
          timeframe,
          from_date: timeframe === 'custom' && fromDate ? fromDate : undefined,
          to_date: timeframe === 'custom' && toDate ? toDate : undefined,
        }),
        fetchActivityTimeline({
          search: searchQuery || undefined,
          category: categoryFilter || undefined,
          severity: severityFilter || undefined,
          outcome: outcomeFilter || undefined,
          requires_review: requiresReviewFilter ? true : undefined,
          from_date: timeframe === 'custom' && fromDate ? fromDate : undefined,
          to_date: timeframe === 'custom' && toDate ? toDate : undefined,
        }),
        fetchSecurityAlerts({
          status: alertStatusFilter || undefined,
          severity: alertSeverityFilter || undefined,
        }),
        fetchBackgroundJobs(),
      ])
      setMetrics(mRes)
      setTimeline(tRes)
      setAlerts(aRes)
      setJobs(jRes)
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Failed to load activity monitoring data.')
    } finally {
      setLoading(false)
    }
  }

  const handleReviewLog = async (logId: string) => {
    try {
      setActionLoading(true)
      await reviewActivityLog(logId, true)
      setSuccessMsg('Activity item marked as reviewed.')
      setTimeline(prev => prev.map(l => (l.id === logId ? { ...l, is_reviewed: true } : l)))
    } catch (err: any) {
      setError('Failed to mark event as reviewed.')
    } finally {
      setActionLoading(false)
    }
  }

  const handleTriageAlert = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedAlert) return
    try {
      setActionLoading(true)
      const updated = await triageSecurityAlert(selectedAlert.id, triageStatus, resolutionNotes)
      setSuccessMsg(`Alert '${updated.title}' updated to ${updated.status}.`)
      setSelectedAlert(null)
      setResolutionNotes('')
      loadAll()
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Failed to triage alert.')
    } finally {
      setActionLoading(false)
    }
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-gray-200 dark:border-gray-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2.5">
              <Activity className="w-6 h-6 text-cyan-600 dark:text-cyan-400" />
              Activity & Security Center
            </h1>
            <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-cyan-100 text-cyan-800 dark:bg-cyan-950/60 dark:text-cyan-300 border border-cyan-300 dark:border-cyan-800">
              Admin Real-Time Telemetry
            </span>
          </div>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Persisted operational timeline, security alerts, client account lifecycle, and PHP2Shell zero-day posture.
          </p>
        </div>

        {/* Timeframe Filter Bar */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center rounded-lg border border-gray-300 dark:border-gray-700 p-0.5 bg-gray-50 dark:bg-gray-800 text-xs">
            {['24h', '7d', '30d', 'custom'].map((tf) => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={clsx(
                  'px-3 py-1.5 rounded-md font-semibold transition',
                  timeframe === tf
                    ? 'bg-white dark:bg-gray-700 text-cyan-600 dark:text-cyan-400 shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                )}
              >
                {tf === '24h' ? 'Last 24h' : tf === '7d' ? 'Last 7d' : tf === '30d' ? 'Last 30d' : 'Custom'}
              </button>
            ))}
          </div>

          <button
            onClick={loadAll}
            disabled={loading}
            className="px-3 py-1.5 text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-1.5"
          >
            <RefreshCw className={clsx('w-3.5 h-3.5', loading && 'animate-spin')} />
            Refresh
          </button>
        </div>
      </div>

      {timeframe === 'custom' && (
        <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 flex flex-wrap items-center gap-4 text-xs">
          <span className="font-semibold text-gray-700 dark:text-gray-300">Custom Date Range:</span>
          <div className="flex items-center gap-2">
            <label className="text-gray-500">From:</label>
            <input
              type="datetime-local"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
              className="px-2 py-1 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-gray-500">To:</label>
            <input
              type="datetime-local"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
              className="px-2 py-1 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
          </div>
          <button
            onClick={loadAll}
            className="px-3 py-1 bg-cyan-600 text-white rounded font-medium hover:bg-cyan-700 transition"
          >
            Apply Range
          </button>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-lg bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-red-500 font-bold text-xs">
            Dismiss
          </button>
        </div>
      )}

      {successMsg && (
        <div className="p-4 rounded-lg bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300 text-sm flex items-center justify-between">
          <span>{successMsg}</span>
          <button onClick={() => setSuccessMsg(null)} className="text-emerald-500 font-bold text-xs">
            Dismiss
          </button>
        </div>
      )}

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        {/* Card 1: Clients */}
        <div className="p-4 rounded-xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm">
          <div className="flex items-center justify-between text-gray-500 dark:text-gray-400">
            <span className="text-xs font-medium">Clients</span>
            <Users className="w-4 h-4 text-blue-500" />
          </div>
          <p className="mt-2 text-2xl font-extrabold text-gray-900 dark:text-white">
            {metrics ? metrics.total_clients : '—'}
          </p>
          <div className="mt-1 flex items-center gap-1.5 text-[11px] text-gray-500">
            <span className="text-emerald-600 dark:text-emerald-400 font-semibold">{metrics?.active_clients ?? 0} active</span>
            <span>•</span>
            <span className="text-amber-600 dark:text-amber-400 font-semibold">{metrics?.suspended_clients ?? 0} susp.</span>
          </div>
        </div>

        {/* Card 2: Logins & Auth */}
        <div className="p-4 rounded-xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm">
          <div className="flex items-center justify-between text-gray-500 dark:text-gray-400">
            <span className="text-xs font-medium">Logins ({timeframe})</span>
            <UserCheck className="w-4 h-4 text-emerald-500" />
          </div>
          <p className="mt-2 text-2xl font-extrabold text-gray-900 dark:text-white">
            {metrics ? metrics.recent_successful_logins : '—'}
          </p>
          <div className="mt-1 flex items-center gap-1.5 text-[11px]">
            <span className={clsx(metrics && metrics.recent_failed_logins > 0 ? 'text-rose-500 font-bold' : 'text-gray-400')}>
              {metrics?.recent_failed_logins ?? 0} failed
            </span>
            <span>•</span>
            <span className="text-gray-500">{metrics?.pending_recovery_requests ?? 0} recov.</span>
          </div>
        </div>

        {/* Card 3: Security Alerts */}
        <div className="p-4 rounded-xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm">
          <div className="flex items-center justify-between text-gray-500 dark:text-gray-400">
            <span className="text-xs font-medium">Open Alerts</span>
            <ShieldAlert className="w-4 h-4 text-rose-500" />
          </div>
          <p className="mt-2 text-2xl font-extrabold text-rose-600 dark:text-rose-400">
            {metrics ? metrics.open_security_alerts : '—'}
          </p>
          <div className="mt-1 flex items-center gap-1.5 text-[11px] text-gray-500">
            <span className="text-rose-500 font-semibold">{metrics?.critical_security_alerts ?? 0} critical</span>
            <span>•</span>
            <span className="text-purple-600 dark:text-purple-400 font-semibold">{metrics?.php2shell_alerts_count ?? 0} PHP2Shell</span>
          </div>
        </div>

        {/* Card 4: Scans Operations */}
        <div className="p-4 rounded-xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm">
          <div className="flex items-center justify-between text-gray-500 dark:text-gray-400">
            <span className="text-xs font-medium">Scans ({timeframe})</span>
            <Shield className="w-4 h-4 text-cyan-500" />
          </div>
          <p className="mt-2 text-2xl font-extrabold text-gray-900 dark:text-white">
            {metrics ? metrics.scans_completed : '—'}
          </p>
          <div className="mt-1 flex items-center gap-1.5 text-[11px] text-gray-500">
            <span className="text-cyan-600 dark:text-cyan-400 font-semibold">{metrics?.scans_running ?? 0} running</span>
            <span>•</span>
            <span className={clsx(metrics && metrics.scans_failed_or_blocked > 0 ? 'text-amber-500 font-bold' : 'text-gray-400')}>
              {metrics?.scans_failed_or_blocked ?? 0} failed
            </span>
          </div>
        </div>

        {/* Card 5: Remediation & DevSecOps */}
        <div className="p-4 rounded-xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm">
          <div className="flex items-center justify-between text-gray-500 dark:text-gray-400">
            <span className="text-xs font-medium">Fixes & Deploy</span>
            <Wrench className="w-4 h-4 text-purple-500" />
          </div>
          <p className="mt-2 text-2xl font-extrabold text-gray-900 dark:text-white">
            {metrics ? metrics.remediations_approved : '—'}
          </p>
          <div className="mt-1 flex items-center gap-1.5 text-[11px] text-gray-500">
            <span className="text-purple-600 dark:text-purple-400 font-semibold">{metrics?.deployments_staging ?? 0} staging</span>
            <span>•</span>
            <span className="text-indigo-600 dark:text-indigo-400 font-semibold">{metrics?.deployments_production ?? 0} prod</span>
          </div>
        </div>

        {/* Card 6: Workers & Background Jobs */}
        <div className="p-4 rounded-xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm">
          <div className="flex items-center justify-between text-gray-500 dark:text-gray-400">
            <span className="text-xs font-medium">System Workers</span>
            <Server className="w-4 h-4 text-emerald-500" />
          </div>
          <p className="mt-2 text-2xl font-extrabold text-emerald-600 dark:text-emerald-400">
            {jobs.length} Active
          </p>
          <div className="mt-1 text-[11px] text-gray-500">
            {metrics && metrics.background_jobs_attention_required > 0 ? (
              <span className="text-rose-500 font-bold">{metrics.background_jobs_attention_required} attention required</span>
            ) : (
              <span className="text-emerald-600 dark:text-emerald-400 font-semibold">All Queues Healthy</span>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-800">
        <nav className="flex space-x-8 text-sm font-semibold">
          <button
            onClick={() => setActiveTab('timeline')}
            className={clsx(
              'pb-3 border-b-2 transition flex items-center gap-2',
              activeTab === 'timeline'
                ? 'border-cyan-500 text-cyan-600 dark:text-cyan-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
            )}
          >
            <Activity className="w-4 h-4" />
            Activity Timeline ({timeline.length})
          </button>

          <button
            onClick={() => setActiveTab('alerts')}
            className={clsx(
              'pb-3 border-b-2 transition flex items-center gap-2',
              activeTab === 'alerts'
                ? 'border-cyan-500 text-cyan-600 dark:text-cyan-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
            )}
          >
            <AlertOctagon className="w-4 h-4" />
            Security Alerts ({alerts.filter((a) => a.status === 'open' || a.status === 'acknowledged').length} Open)
          </button>

          <button
            onClick={() => setActiveTab('jobs')}
            className={clsx(
              'pb-3 border-b-2 transition flex items-center gap-2',
              activeTab === 'jobs'
                ? 'border-cyan-500 text-cyan-600 dark:text-cyan-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
            )}
          >
            <Server className="w-4 h-4" />
            Background Workers & Engines ({jobs.length})
          </button>
        </nav>
      </div>

      {/* Tab 1: Activity Timeline */}
      {activeTab === 'timeline' && (
        <div className="space-y-4">
          {/* Timeline Filters */}
          <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800">
            <div className="flex flex-wrap items-center gap-3">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-3 top-3 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search events, actors, domains..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && loadAll()}
                  className="pl-8 text-xs rounded-lg border border-gray-300 dark:border-gray-700 px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-white w-64"
                />
              </div>

              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="text-xs rounded-lg border border-gray-300 dark:border-gray-700 px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              >
                <option value="">All Categories</option>
                <option value="authentication">Authentication</option>
                <option value="account_security">Account Security</option>
                <option value="client_management">Client Management</option>
                <option value="website_registration">Website Target</option>
                <option value="ownership_verification">Verification</option>
                <option value="vulnerability_scanning">Scanning</option>
                <option value="ai_remediation">AI Remediation</option>
                <option value="staging_deployment">Deployments</option>
                <option value="client_finder">Client Finder</option>
                <option value="security_alert">Security Alert</option>
              </select>

              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="text-xs rounded-lg border border-gray-300 dark:border-gray-700 px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              >
                <option value="">All Severities</option>
                <option value="info">Info</option>
                <option value="warning">Warning</option>
                <option value="critical">Critical</option>
              </select>

              <select
                value={outcomeFilter}
                onChange={(e) => setOutcomeFilter(e.target.value)}
                className="text-xs rounded-lg border border-gray-300 dark:border-gray-700 px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              >
                <option value="">All Outcomes</option>
                <option value="success">Success</option>
                <option value="failure">Failure</option>
                <option value="blocked">Blocked</option>
              </select>

              <label className="flex items-center gap-1.5 text-xs text-gray-700 dark:text-gray-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={requiresReviewFilter}
                  onChange={(e) => setRequiresReviewFilter(e.target.checked)}
                  className="rounded text-cyan-600 focus:ring-cyan-500"
                />
                Requires Review Only
              </label>
            </div>

            <button
              onClick={loadAll}
              className="text-xs px-3 py-2 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 font-semibold"
            >
              Filter
            </button>
          </div>

          {/* Timeline Table */}
          <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden shadow-sm">
            {timeline.length === 0 ? (
              <div className="p-8 text-center text-sm text-gray-500">
                No activity events found matching criteria.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-gray-50 dark:bg-gray-800/60 text-gray-700 dark:text-gray-300 font-semibold border-b border-gray-200 dark:border-gray-800">
                    <tr>
                      <th className="py-3 px-4">Timestamp</th>
                      <th className="py-3 px-4">Category & Event</th>
                      <th className="py-3 px-4">Actor</th>
                      <th className="py-3 px-4">Target Entity</th>
                      <th className="py-3 px-4">Outcome</th>
                      <th className="py-3 px-4">Severity</th>
                      <th className="py-3 px-4 text-right">Review Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                    {timeline.map((item) => (
                      <React.Fragment key={item.id}>
                        <tr className={clsx('hover:bg-gray-50/50 dark:hover:bg-gray-800/40 transition', item.requires_review && !item.is_reviewed && 'bg-amber-50/30 dark:bg-amber-950/20')}>
                          <td className="py-3 px-4 font-mono text-gray-500 whitespace-nowrap">
                            {new Date(item.timestamp).toLocaleString([], {
                              month: 'short',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit',
                              second: '2-digit',
                            })}
                          </td>
                          <td className="py-3 px-4">
                            <div className="font-semibold text-gray-900 dark:text-white">
                              {item.event_name}
                            </div>
                            <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
                              {item.event_category}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-gray-600 dark:text-gray-300">
                            {item.actor_email || item.actor_id || item.actor_type}
                          </td>
                          <td className="py-3 px-4 font-mono text-gray-700 dark:text-gray-300">
                            {item.target_identifier || item.target_type || '—'}
                          </td>
                          <td className="py-3 px-4">
                            <span
                              className={clsx(
                                'px-2 py-0.5 text-[10px] font-bold uppercase rounded-full',
                                item.outcome === 'success'
                                  ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300'
                                  : item.outcome === 'failure'
                                  ? 'bg-red-100 text-red-800 dark:bg-red-950/60 dark:text-red-300'
                                  : 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300'
                              )}
                            >
                              {item.outcome}
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            <span
                              className={clsx(
                                'px-2 py-0.5 text-[10px] font-bold uppercase rounded-full',
                                item.severity === 'critical'
                                  ? 'bg-rose-100 text-rose-800 dark:bg-rose-950/80 dark:text-rose-300'
                                  : item.severity === 'warning'
                                  ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300'
                                  : 'bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300'
                              )}
                            >
                              {item.severity}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-right space-x-2">
                            {item.metadata_json && (
                              <button
                                onClick={() => setExpandedLogId(expandedLogId === item.id ? null : item.id)}
                                className="px-2 py-1 rounded border border-gray-300 dark:border-gray-700 text-[11px] text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800"
                              >
                                {expandedLogId === item.id ? 'Hide Meta' : 'View Meta'}
                              </button>
                            )}
                            {item.requires_review && !item.is_reviewed ? (
                              <button
                                onClick={() => handleReviewLog(item.id)}
                                disabled={actionLoading}
                                className="px-2.5 py-1 text-[11px] font-semibold rounded bg-amber-500 hover:bg-amber-600 text-white transition"
                              >
                                Review
                              </button>
                            ) : item.is_reviewed ? (
                              <span className="text-emerald-600 dark:text-emerald-400 font-semibold text-[11px] inline-flex items-center gap-1">
                                <CheckCircle2 className="w-3 h-3" /> Reviewed
                              </span>
                            ) : null}
                          </td>
                        </tr>
                        {expandedLogId === item.id && item.metadata_json && (
                          <tr className="bg-gray-50 dark:bg-gray-800/80">
                            <td colSpan={7} className="p-3 text-[11px] font-mono text-gray-700 dark:text-gray-300">
                              <pre className="p-2 rounded bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 overflow-x-auto whitespace-pre-wrap">
                                {JSON.stringify(JSON.parse(item.metadata_json), null, 2)}
                              </pre>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Security Alerts & Threat Triage */}
      {activeTab === 'alerts' && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800">
            <div className="flex flex-wrap items-center gap-3">
              <select
                value={alertStatusFilter}
                onChange={(e) => setAlertStatusFilter(e.target.value)}
                className="text-xs rounded-lg border border-gray-300 dark:border-gray-700 px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              >
                <option value="">All Alert Statuses</option>
                <option value="open">Open</option>
                <option value="acknowledged">Acknowledged</option>
                <option value="resolved">Resolved</option>
                <option value="dismissed">Dismissed</option>
                <option value="false_positive">False Positive</option>
              </select>

              <select
                value={alertSeverityFilter}
                onChange={(e) => setAlertSeverityFilter(e.target.value)}
                className="text-xs rounded-lg border border-gray-300 dark:border-gray-700 px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              >
                <option value="">All Alert Severities</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
            <button
              onClick={loadAll}
              className="text-xs px-3 py-2 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 font-semibold"
            >
              Filter
            </button>
          </div>

          <div className="space-y-3">
            {alerts.length === 0 ? (
              <div className="p-8 text-center text-sm text-gray-500 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800">
                No security alerts found matching filter criteria.
              </div>
            ) : (
              alerts.map((alert) => (
                <div
                  key={alert.id}
                  className="p-5 rounded-xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                  <div className="space-y-1.5 max-w-3xl">
                    <div className="flex flex-wrap items-center gap-2">
                      <span
                        className={clsx(
                          'px-2 py-0.5 text-[10px] font-bold uppercase rounded-full',
                          alert.severity === 'critical'
                            ? 'bg-rose-100 text-rose-800 dark:bg-rose-950/80 dark:text-rose-300'
                            : 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300'
                        )}
                      >
                        {alert.severity}
                      </span>

                      <span
                        className={clsx(
                          'px-2 py-0.5 text-[10px] font-semibold uppercase rounded-full',
                          alert.status === 'open'
                            ? 'bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-400 border border-red-300 dark:border-red-800'
                            : alert.status === 'acknowledged'
                            ? 'bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-400 border border-blue-300 dark:border-blue-800'
                            : 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 border border-emerald-300 dark:border-emerald-800'
                        )}
                      >
                        {alert.status}
                      </span>

                      {alert.cve_id && (
                        <span className="px-2 py-0.5 text-[10px] font-mono font-semibold rounded bg-purple-100 text-purple-800 dark:bg-purple-950/80 dark:text-purple-300 border border-purple-200 dark:border-purple-800">
                          {alert.cve_id}
                        </span>
                      )}

                      <span className="text-xs text-gray-400 font-mono">
                        {new Date(alert.created_at).toLocaleString()}
                      </span>
                    </div>

                    <h3 className="text-base font-bold text-gray-900 dark:text-white">
                      {alert.title}
                    </h3>
                    <p className="text-xs text-gray-600 dark:text-gray-400">
                      {alert.description}
                    </p>

                    {alert.resolution_notes && (
                      <div className="mt-2 p-2.5 rounded bg-gray-50 dark:bg-gray-800/60 text-xs border border-gray-200 dark:border-gray-700">
                        <span className="font-semibold text-gray-700 dark:text-gray-300">Resolution Remarks:</span>{' '}
                        <span className="text-gray-600 dark:text-gray-400">{alert.resolution_notes}</span>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button
                      onClick={() => {
                        setSelectedAlert(alert)
                        setTriageStatus(alert.status === 'open' ? 'acknowledged' : 'resolved')
                      }}
                      className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-cyan-600 text-white hover:bg-cyan-700 transition"
                    >
                      Triage / Update
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Tab 3: Background Workers & Engines */}
      {activeTab === 'jobs' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {jobs.map((job, idx) => (
            <div
              key={idx}
              className="p-5 rounded-xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 font-bold">
                    {job.category}
                  </span>
                  <span
                    className={clsx(
                      'px-2 py-0.5 text-[10px] font-bold uppercase rounded-full',
                      job.status === 'healthy' || job.status === 'operational'
                        ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300'
                        : 'bg-amber-100 text-amber-800 dark:bg-amber-950/80 dark:text-amber-300'
                    )}
                  >
                    {job.status}
                  </span>
                </div>

                <h3 className="mt-3 text-sm font-bold text-gray-900 dark:text-white">
                  {job.name}
                </h3>
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  {job.details}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-gray-100 dark:border-gray-800 flex items-center justify-between text-[11px] text-gray-400 font-mono">
                <span>Heartbeat Active</span>
                <span>{job.last_run ? new Date(job.last_run).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Continuous'}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Alert Triage Modal */}
      {selectedAlert && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-sm overflow-y-auto">
          <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-lg w-full p-4 sm:p-6 shadow-2xl border border-gray-200 dark:border-gray-800 space-y-4 max-h-[90vh] overflow-y-auto my-auto">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">
              Triage Security Alert
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {selectedAlert.title}
            </p>

            <form onSubmit={handleTriageAlert} className="space-y-4 text-xs">
              <div>
                <label className="block text-gray-700 dark:text-gray-300 font-semibold mb-1">
                  Target Status
                </label>
                <select
                  value={triageStatus}
                  onChange={(e) => setTriageStatus(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-700 px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                >
                  <option value="acknowledged">Acknowledged (Investigating)</option>
                  <option value="resolved">Resolved (Mitigated / Hardened)</option>
                  <option value="dismissed">Dismissed (Accepted Risk)</option>
                  <option value="false_positive">False Positive</option>
                </select>
              </div>

              <div>
                <label className="block text-gray-700 dark:text-gray-300 font-semibold mb-1">
                  Resolution Notes & Remarks
                </label>
                <textarea
                  rows={3}
                  placeholder="Document mitigation steps, verified patches, or justification..."
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-700 px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedAlert(null)}
                  className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-2 rounded-lg bg-cyan-600 text-white font-semibold hover:bg-cyan-700 transition"
                >
                  {actionLoading ? 'Saving...' : 'Save Triage Decision'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
