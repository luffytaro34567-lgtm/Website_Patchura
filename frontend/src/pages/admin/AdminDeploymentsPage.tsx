import React, { useEffect, useState } from 'react'
import { adminGetDeploymentOverview } from '@/api/deployment'
import { AdminDeploymentOverview } from '@/types/deployment'

export const AdminDeploymentsPage: React.FC = () => {
  const [overview, setOverview] = useState<AdminDeploymentOverview | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadOverview()
  }, [])

  const loadOverview = async () => {
    try {
      setLoading(true)
      const data = await adminGetDeploymentOverview()
      setOverview(data)
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Failed to load deployment overview.')
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
              DevSecOps Deployments & Git Integration Oversight
            </h1>
            <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800 dark:bg-purple-950/60 dark:text-purple-400 border border-purple-300 dark:border-purple-800">
              Admin Control
            </span>
          </div>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            System-wide telemetry of connected Git repositories, Pull Requests dispatched, staging rollouts, and production safety gate compliance.
          </p>
        </div>

        <button
          onClick={loadOverview}
          disabled={loading}
          className="px-4 py-2 text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
        >
          {loading ? 'Refreshing...' : '↻ Refresh Telemetry'}
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="p-5 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Connected Repositories</p>
          <p className="mt-2 text-3xl font-extrabold text-gray-900 dark:text-white">
            {overview ? overview.total_connected_repositories : '—'}
          </p>
          <p className="mt-1 text-xs text-cyan-600 dark:text-cyan-400">GitHub & GitLab links</p>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Pull Requests Dispatched</p>
          <p className="mt-2 text-3xl font-extrabold text-cyan-600 dark:text-cyan-400">
            {overview ? overview.total_pull_requests_dispatched : '—'}
          </p>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">Isolated feature branches</p>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Staging Deployments</p>
          <p className="mt-2 text-3xl font-extrabold text-emerald-600 dark:text-emerald-400">
            {overview ? overview.total_staging_deployments : '—'}
          </p>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Production: {overview ? overview.total_production_deployments : 0}
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Rollbacks Executed</p>
          <p className="mt-2 text-3xl font-extrabold text-amber-600 dark:text-amber-400">
            {overview ? overview.total_rollbacks_executed : '—'}
          </p>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">Defensive snapshot rollbacks</p>
        </div>
      </div>

      {/* Safety Compliance & Zero-Default-Branch Policy */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-gray-900 to-gray-800 text-white border border-gray-700 space-y-4">
        <h3 className="text-base font-bold flex items-center gap-2">
          <span>🛡️ DevSecOps Safety Governance & Branch Protection Policy</span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-gray-300">
          <div className="p-3 rounded-lg bg-gray-800/80 border border-gray-700">
            <span className="font-bold text-white block mb-1">Protected Default Branch</span>
            Commits directly to default branches (main/master) are strictly barred. All patches are delivered via dedicated branches (`patchora/patch-...`) and reviewed via Pull Requests.
          </div>
          <div className="p-3 rounded-lg bg-gray-800/80 border border-gray-700">
            <span className="font-bold text-white block mb-1">Production Disabled by Default</span>
            Production deployment targets are disabled by default (`is_enabled: false`). Enabling requires explicit multi-factor confirmation and typing &apos;DEPLOY PRODUCTION&apos;.
          </div>
          <div className="p-3 rounded-lg bg-gray-800/80 border border-gray-700">
            <span className="font-bold text-white block mb-1">Mandatory Rollback Snapshot</span>
            Before any patch is deployed to staging or production, a clean rollback snapshot of the original source code is preserved for 1-click rollback execution.
          </div>
        </div>
      </div>
    </div>
  )
}
export default AdminDeploymentsPage
