import React, { useEffect, useState } from 'react'
import { adminGetRemediationStats } from '@/api/remediations'
import { AdminRemediationStats } from '@/types/remediation'

export const AdminRemediationsPage: React.FC = () => {
  const [stats, setStats] = useState<AdminRemediationStats | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      setLoading(true)
      const data = await adminGetRemediationStats()
      setStats(data)
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Failed to load remediation statistics.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-gray-200 dark:border-gray-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              AI Bug-Fixing & Remediation Oversight
            </h1>
            <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800 dark:bg-purple-950/60 dark:text-purple-400 border border-purple-300 dark:border-purple-800">
              Admin Control
            </span>
          </div>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            System-wide telemetry of patch generation requests, isolated sandbox test verdicts, and human approval sign-offs.
          </p>
        </div>

        <button
          onClick={loadStats}
          disabled={loading}
          className="px-4 py-2 text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
        >
          {loading ? 'Refreshing...' : '↻ Refresh Stats'}
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="p-5 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Total Fix Requests</p>
          <p className="mt-2 text-3xl font-extrabold text-gray-900 dark:text-white">
            {stats ? stats.total_remediations : '—'}
          </p>
          <p className="mt-1 text-xs text-cyan-600 dark:text-cyan-400">Across all client tenants</p>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Patches Approved</p>
          <p className="mt-2 text-3xl font-extrabold text-emerald-600 dark:text-emerald-400">
            {stats ? stats.approved_patches : '—'}
          </p>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">Explicit client sign-off</p>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Sandbox Tests Passed</p>
          <p className="mt-2 text-3xl font-extrabold text-cyan-600 dark:text-cyan-400">
            {stats ? stats.tests_passed : '—'}
          </p>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Failed: {stats ? stats.tests_failed : 0}
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Active Engine</p>
          <p className="mt-2 text-sm font-bold text-gray-900 dark:text-white line-clamp-2">
            {stats ? stats.ai_provider_active : 'Deterministic Rules'}
          </p>
          <p className="mt-1 text-xs text-purple-600 dark:text-purple-400">Zero host execution AST sandbox</p>
        </div>
      </div>

      {/* Safety & Isolation Architecture Card */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-gray-900 to-gray-800 text-white border border-gray-700 space-y-4">
        <h3 className="text-base font-bold flex items-center gap-2">
          <span>🛡️ DevSecOps Sandbox Architecture & Zero-Execution Policy</span>
        </h3>
        <p className="text-xs text-gray-300 leading-relaxed">
          PATCHORA strictly isolates all patch generation and validation workflows. Untrusted code is analyzed
          via deterministic lexical tokenizers, structural bracket analyzers, and AST static syntax parsers.
          AI model outputs are never executed directly on the host server, preventing remote code execution,
          unauthorized command execution, and recursive memory corruption (including full mitigation for PHP2Shell CVE-2026-109618 & CVE-2026-109619).
        </p>
      </div>
    </div>
  )
}
export default AdminRemediationsPage
