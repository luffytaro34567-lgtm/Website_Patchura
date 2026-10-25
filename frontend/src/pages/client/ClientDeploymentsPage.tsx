import React, { useEffect, useState } from 'react'
import {
  connectRepository,
  createDeploymentTarget,
  createPullRequest,
  deployToProduction,
  deployToStaging,
  disconnectRepository,
  getCliInstructions,
  getDeploymentHistory,
  listDeploymentTargets,
  listRepositories,
  rollbackDeployment,
} from '@/api/deployment'
import { listMyRemediations } from '@/api/remediations'
import {
  CliInstructions,
  DeploymentRecord,
  DeploymentTarget,
  RepositoryConnection,
} from '@/types/deployment'
import { RemediationSessionSummary } from '@/types/remediation'

export const ClientDeploymentsPage: React.FC = () => {
  const [repositories, setRepositories] = useState<RepositoryConnection[]>([])
  const [targets, setTargets] = useState<DeploymentTarget[]>([])
  const [approvedSessions, setApprovedSessions] = useState<RemediationSessionSummary[]>([])
  const [history, setHistory] = useState<DeploymentRecord[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [actionLoading, setActionLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Modals
  const [showRepoModal, setShowRepoModal] = useState<boolean>(false)
  const [showPrModal, setShowPrModal] = useState<boolean>(false)
  const [showProdModal, setShowProdModal] = useState<boolean>(false)
  const [showCliModal, setShowCliModal] = useState<boolean>(false)
  const [showRollbackModal, setShowRollbackModal] = useState<boolean>(false)

  // Modal form states
  const [repoName, setRepoName] = useState<string>('')
  const [accessToken, setAccessToken] = useState<string>('')
  const [defaultBranch, setDefaultBranch] = useState<string>('main')

  const [selectedSessionId, setSelectedSessionId] = useState<string>('')
  const [selectedRepoId, setSelectedRepoId] = useState<string>('')
  const [customBranch, setCustomBranch] = useState<string>('')
  const [prTitle, setPrTitle] = useState<string>('')

  const [selectedTargetId, setSelectedTargetId] = useState<string>('')
  const [prodConfirmation, setProdConfirmation] = useState<string>('')
  const [prodNotes, setProdNotes] = useState<string>('')

  const [rollbackDeploymentId, setRollbackDeploymentId] = useState<string>('')
  const [rollbackReason, setRollbackReason] = useState<string>('')

  const [cliData, setCliData] = useState<CliInstructions | null>(null)

  useEffect(() => {
    loadAllData()
  }, [])

  const loadAllData = async () => {
    try {
      setLoading(true)
      const [repos, tgts, rems, hist] = await Promise.all([
        listRepositories(),
        listDeploymentTargets(),
        listMyRemediations(),
        getDeploymentHistory(),
      ])
      setRepositories(repos)
      setTargets(tgts)
      // Filter sessions that have been explicitly approved
      const approved = rems.filter((s) => s.approval_status === 'approved')
      setApprovedSessions(approved)
      setHistory(hist)

      if (repos.length > 0) setSelectedRepoId(repos[0].id)
      if (tgts.length > 0) setSelectedTargetId(tgts[0].id)
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Failed to load deployment data.')
    } finally {
      setLoading(false)
    }
  }

  const handleConnectRepo = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setActionLoading(true)
      setError(null)
      await connectRepository({
        repo_name: repoName,
        access_token: accessToken,
        default_branch: defaultBranch,
      })
      setShowRepoModal(false)
      setRepoName('')
      setAccessToken('')
      setSuccessMsg('GitHub repository connected successfully!')
      loadAllData()
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Failed to connect repository.')
    } finally {
      setActionLoading(false)
    }
  }

  const handleDisconnectRepo = async (repoId: string) => {
    try {
      await disconnectRepository(repoId)
      setSuccessMsg('Repository disconnected.')
      loadAllData()
    } catch (err: any) {
      setError('Failed to disconnect repository.')
    }
  }

  const handleCreatePr = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedSessionId || !selectedRepoId) {
      setError('Please select an approved patch and a target repository.')
      return
    }

    try {
      setActionLoading(true)
      setError(null)
      const rec = await createPullRequest({
        session_id: selectedSessionId,
        repository_id: selectedRepoId,
        branch_name: customBranch || undefined,
        pr_title: prTitle || undefined,
      })
      setShowPrModal(false)
      setSuccessMsg(`Pull Request dispatched: ${rec.pull_request_url || rec.git_branch}`)
      loadAllData()
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Failed to dispatch Pull Request.')
    } finally {
      setActionLoading(false)
    }
  }

  const handleDeployStaging = async (sessionId: string) => {
    try {
      setActionLoading(true)
      setError(null)
      const rec = await deployToStaging({ session_id: sessionId })
      setSuccessMsg(`Patch deployed to staging branch '${rec.git_branch}'.`)
      loadAllData()
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Failed to deploy to staging.')
    } finally {
      setActionLoading(false)
    }
  }

  const handleDeployProd = async (e: React.FormEvent) => {
    e.preventDefault()
    if (prodConfirmation.trim() !== 'DEPLOY PRODUCTION') {
      setError("You must type 'DEPLOY PRODUCTION' exactly to satisfy the safety gate.")
      return
    }

    try {
      setActionLoading(true)
      setError(null)
      const rec = await deployToProduction({
        session_id: selectedSessionId,
        target_id: selectedTargetId,
        confirmation_token: prodConfirmation,
        client_notes: prodNotes,
      })
      setShowProdModal(false)
      setProdConfirmation('')
      setSuccessMsg(`Production deployment completed! Branch: ${rec.git_branch}`)
      loadAllData()
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Production deployment failed or is disabled.')
    } finally {
      setActionLoading(false)
    }
  }

  const handleRollback = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!rollbackReason.trim()) return

    try {
      setActionLoading(true)
      setError(null)
      await rollbackDeployment(rollbackDeploymentId, { reason: rollbackReason })
      setShowRollbackModal(false)
      setRollbackReason('')
      setSuccessMsg('Deployment successfully rolled back to previous snapshot.')
      loadAllData()
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Failed to execute rollback.')
    } finally {
      setActionLoading(false)
    }
  }

  const handleViewCli = async (sessionId: string) => {
    try {
      setActionLoading(true)
      const data = await getCliInstructions(sessionId)
      setCliData(data)
      setShowCliModal(true)
    } catch (err: any) {
      setError('Failed to load manual CLI instructions.')
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
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Source-Code Integration & Deployment
            </h1>
            <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-cyan-100 text-cyan-800 dark:bg-cyan-950/60 dark:text-cyan-400 border border-cyan-300 dark:border-cyan-800">
              Phase 9 DevSecOps
            </span>
          </div>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Transfer verified, approved security patches into GitHub repositories via Pull Requests, staging clusters, or manual CLI patch commands.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowRepoModal(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-cyan-600 hover:bg-cyan-700 dark:bg-cyan-500 transition"
          >
            + Connect GitHub Repository
          </button>
        </div>
      </div>

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

      {/* Section 1: Approved Patches Ready for Transfer */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <span>Approved Patches Ready for Deployment</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-400 font-normal">
              {approvedSessions.length} available
            </span>
          </h2>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            Requires explicit human approval from Phase 8
          </span>
        </div>

        {approvedSessions.length === 0 ? (
          <div className="p-6 rounded-xl border border-dashed border-gray-300 dark:border-gray-800 bg-white dark:bg-gray-900/40 text-center text-sm text-gray-500">
            No approved patches ready for transfer. Review and approve proposed fixes in the{' '}
            <a href="/dashboard/remediations" className="text-cyan-600 dark:text-cyan-400 hover:underline">
              AI Bug Fixes Dashboard
            </a>
            .
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {approvedSessions.map((sess) => (
              <div
                key={sess.id}
                className="p-5 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm space-y-4"
              >
                <div className="flex items-start justify-between">
                  <span className="text-xs font-mono font-bold text-cyan-600 dark:text-cyan-400 bg-cyan-50 dark:bg-cyan-950/40 px-2 py-0.5 rounded">
                    {sess.target_filename}
                  </span>
                  <span className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded-full">
                    ✓ Approved
                  </span>
                </div>

                <div>
                  <h4 className="text-sm font-bold text-gray-900 dark:text-white line-clamp-1">
                    {sess.finding_title}
                  </h4>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{sess.website_domain}</p>
                </div>

                <div className="pt-3 border-t border-gray-100 dark:border-gray-800 flex flex-wrap gap-2 text-xs">
                  <button
                    onClick={() => {
                      setSelectedSessionId(sess.id)
                      setShowPrModal(true)
                    }}
                    className="flex-1 py-1.5 px-3 font-semibold rounded bg-cyan-600 text-white hover:bg-cyan-700 transition"
                  >
                    🚀 Create PR
                  </button>
                  <button
                    onClick={() => handleDeployStaging(sess.id)}
                    className="py-1.5 px-3 font-medium rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                  >
                    Staging
                  </button>
                  <button
                    onClick={() => {
                      setSelectedSessionId(sess.id)
                      setShowProdModal(true)
                    }}
                    className="py-1.5 px-3 font-medium rounded border border-red-200 dark:border-red-900/60 bg-red-50/50 dark:bg-red-950/20 text-red-600 dark:text-red-400 hover:bg-red-100"
                  >
                    Prod
                  </button>
                  <button
                    onClick={() => handleViewCli(sess.id)}
                    className="py-1.5 px-2 font-medium rounded border border-gray-300 dark:border-gray-700 text-gray-600 dark:text-gray-400"
                    title="Manual CLI Commands"
                  >
                    💻 CLI
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Section 2: Connected Git Repositories */}
      <div className="space-y-4">
        <h2 className="text-base font-semibold text-gray-900 dark:text-white">
          Connected Git Repositories
        </h2>

        {repositories.length === 0 ? (
          <div className="p-6 rounded-xl border border-dashed border-gray-300 dark:border-gray-800 bg-white dark:bg-gray-900/40 text-center text-sm text-gray-500">
            No repositories connected. Connect your GitHub or Git repo to enable Pull Request dispatch.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {repositories.map((repo) => (
              <div
                key={repo.id}
                className="p-4 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 flex items-center justify-between"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-gray-900 dark:text-white">{repo.repo_name}</span>
                    <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
                      {repo.default_branch}
                    </span>
                  </div>
                  <p className="text-xs font-mono text-gray-400 mt-1">Token: {repo.masked_token}</p>
                </div>
                <button
                  onClick={() => handleDisconnectRepo(repo.id)}
                  className="text-xs text-red-500 hover:text-red-700 font-semibold"
                >
                  Disconnect
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Section 3: Deployment & Rollback History */}
      <div className="space-y-4">
        <h2 className="text-base font-semibold text-gray-900 dark:text-white">
          Deployment & Transfer Audit Log
        </h2>

        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden shadow-sm">
          {history.length === 0 ? (
            <div className="p-8 text-center text-sm text-gray-500 dark:text-gray-400">
              No deployments or Pull Requests dispatched yet.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-gray-50 dark:bg-gray-800/60 text-gray-700 dark:text-gray-300 font-semibold border-b border-gray-200 dark:border-gray-800">
                  <tr>
                    <th className="py-3 px-4">Environment</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Branch / PR</th>
                    <th className="py-3 px-4">Commit SHA</th>
                    <th className="py-3 px-4">Dispatched At</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
                  {history.map((rec) => (
                    <tr key={rec.id} className="hover:bg-gray-50/50 dark:hover:bg-gray-800/40">
                      <td className="py-3 px-4 uppercase font-bold text-gray-900 dark:text-white">
                        {rec.environment}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${
                            rec.status === 'deployed' || rec.status === 'staged' || rec.status === 'pr_created'
                              ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-400'
                              : rec.status === 'rolled_back'
                              ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-400'
                              : 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-400'
                          }`}
                        >
                          {rec.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono text-cyan-600 dark:text-cyan-400">
                        {rec.pull_request_url ? (
                          <a
                            href={rec.pull_request_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="underline flex items-center gap-1"
                          >
                            PR #{rec.pull_request_number || 'View'}
                          </a>
                        ) : (
                          rec.git_branch
                        )}
                      </td>
                      <td className="py-3 px-4 font-mono text-gray-500">
                        {rec.git_commit_sha ? rec.git_commit_sha.slice(0, 7) : '—'}
                      </td>
                      <td className="py-3 px-4 text-gray-500">
                        {new Date(rec.created_at).toLocaleString()}
                      </td>
                      <td className="py-3 px-4 text-right">
                        {rec.status !== 'rolled_back' ? (
                          <button
                            onClick={() => {
                              setRollbackDeploymentId(rec.id)
                              setShowRollbackModal(true)
                            }}
                            className="text-xs font-semibold text-amber-600 hover:text-amber-700 dark:text-amber-400"
                          >
                            ↺ Rollback
                          </button>
                        ) : (
                          <span className="text-[11px] text-gray-400">Reverted</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Connect Repo Modal */}
      {showRepoModal && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-3 sm:p-4 overflow-y-auto">
          <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-md w-full p-4 sm:p-6 border border-gray-200 dark:border-gray-800 space-y-4 max-h-[90vh] overflow-y-auto my-auto">
            <h3 className="text-base font-bold text-gray-900 dark:text-white">
              Connect GitHub Repository
            </h3>
            <form onSubmit={handleConnectRepo} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">
                  Repository Name (owner/repo)
                </label>
                <input
                  type="text"
                  value={repoName}
                  onChange={(e) => setRepoName(e.target.value)}
                  placeholder="acme-inc/storefront"
                  required
                  className="mt-1 w-full text-xs rounded-lg border border-gray-300 dark:border-gray-700 p-2.5 bg-white dark:bg-gray-800 text-gray-900 dark:text-white min-h-[40px]"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">
                  Default Base Branch
                </label>
                <input
                  type="text"
                  value={defaultBranch}
                  onChange={(e) => setDefaultBranch(e.target.value)}
                  placeholder="main"
                  required
                  className="mt-1 w-full text-xs rounded-lg border border-gray-300 dark:border-gray-700 p-2.5 bg-white dark:bg-gray-800 text-gray-900 dark:text-white font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">
                  GitHub Personal Access Token (repo scope)
                </label>
                <input
                  type="password"
                  value={accessToken}
                  onChange={(e) => setAccessToken(e.target.value)}
                  placeholder="ghp_************************"
                  required
                  className="mt-1 w-full text-xs rounded-lg border border-gray-300 dark:border-gray-700 p-2.5 bg-white dark:bg-gray-800 text-gray-900 dark:text-white font-mono"
                />
                <p className="mt-1 text-[11px] text-gray-400">
                  Token is securely masked and never displayed in cleartext.
                </p>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowRepoModal(false)}
                  className="px-3 py-1.5 text-xs text-gray-600 dark:text-gray-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-cyan-600 text-white hover:bg-cyan-700"
                >
                  Save Connection
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create PR Modal */}
      {showPrModal && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-3 sm:p-4 overflow-y-auto">
          <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-md w-full p-4 sm:p-6 border border-gray-200 dark:border-gray-800 space-y-4 max-h-[90vh] overflow-y-auto my-auto">
            <h3 className="text-base font-bold text-gray-900 dark:text-white">
              Dispatch Pull Request to GitHub
            </h3>
            <form onSubmit={handleCreatePr} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">
                  Target Repository
                </label>
                <select
                  value={selectedRepoId}
                  onChange={(e) => setSelectedRepoId(e.target.value)}
                  className="mt-1 w-full text-xs rounded-lg border border-gray-300 dark:border-gray-700 p-2.5 bg-white dark:bg-gray-800 text-gray-900 dark:text-white min-h-[40px]"
                >
                  {repositories.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.repo_name} ({r.default_branch})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">
                  Custom Branch Name (Optional)
                </label>
                <input
                  type="text"
                  value={customBranch}
                  onChange={(e) => setCustomBranch(e.target.value)}
                  placeholder="patchora/patch-security-fix"
                  className="mt-1 w-full text-xs rounded-lg border border-gray-300 dark:border-gray-700 p-2.5 bg-white dark:bg-gray-800 text-gray-900 dark:text-white font-mono min-h-[40px]"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowPrModal(false)}
                  className="px-3.5 py-2 text-xs text-gray-600 dark:text-gray-400 min-h-[40px]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-2 text-xs font-semibold rounded-lg bg-cyan-600 text-white hover:bg-cyan-700 min-h-[40px]"
                >
                  Dispatch PR
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Production Deployment Confirmation Modal */}
      {showProdModal && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-3 sm:p-4 overflow-y-auto">
          <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-lg w-full p-4 sm:p-6 border border-red-300 dark:border-red-900 space-y-4 shadow-2xl max-h-[90vh] overflow-y-auto my-auto">
            <div className="flex items-center gap-2 text-red-600 dark:text-red-400 font-bold text-base">
              <span>⚠️ Critical Safety Gate: Production Deployment</span>
            </div>
            <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
              Production deployment directly modifies live production servers or release tags.
              This requires explicit authorization. To satisfy the safety gate, type{' '}
              <strong className="text-red-600 dark:text-red-400 font-mono">DEPLOY PRODUCTION</strong> below:
            </p>

            <form onSubmit={handleDeployProd} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">
                  Safety Confirmation Code
                </label>
                <input
                  type="text"
                  value={prodConfirmation}
                  onChange={(e) => setProdConfirmation(e.target.value)}
                  placeholder="DEPLOY PRODUCTION"
                  required
                  className="mt-1 w-full text-xs rounded-lg border border-red-300 dark:border-red-800 p-2.5 bg-red-50/40 dark:bg-red-950/30 text-gray-900 dark:text-white font-mono font-bold min-h-[40px]"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">
                  Release Notes
                </label>
                <textarea
                  rows={2}
                  value={prodNotes}
                  onChange={(e) => setProdNotes(e.target.value)}
                  placeholder="Security hotfix verified on staging..."
                  className="mt-1 w-full text-xs rounded-lg border border-gray-300 dark:border-gray-700 p-2.5 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowProdModal(false)}
                  className="px-3.5 py-2 text-xs text-gray-600 dark:text-gray-400 min-h-[40px]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading || prodConfirmation.trim() !== 'DEPLOY PRODUCTION'}
                  className="px-4 py-2 text-xs font-semibold rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 min-h-[40px]"
                >
                  Authorize Production Rollout
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Manual CLI Instructions Modal */}
      {showCliModal && cliData && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-3 sm:p-4 overflow-y-auto">
          <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-2xl w-full p-4 sm:p-6 border border-gray-200 dark:border-gray-800 space-y-4 max-h-[90vh] overflow-y-auto my-auto">
            <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-800 pb-3">
              <h3 className="text-base font-bold text-gray-900 dark:text-white">
                Manual Git CLI Patch Application
              </h3>
              <button
                onClick={() => setShowCliModal(false)}
                className="text-gray-400 font-bold min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg"
                aria-label="Close CLI modal"
              >
                ✕
              </button>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Run these commands in your local repository terminal to apply and verify the patch cleanly:
            </p>
            <pre className="p-4 rounded-xl bg-gray-950 text-emerald-400 font-mono text-xs overflow-x-auto whitespace-pre leading-relaxed border border-gray-800 max-h-80">
              {cliData.git_apply_script}
            </pre>
            <div className="flex justify-end">
              <button
                onClick={() => setShowCliModal(false)}
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-gray-200 dark:bg-gray-800 text-gray-800 dark:text-gray-200 min-h-[40px]"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Rollback Modal */}
      {showRollbackModal && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-3 sm:p-4 overflow-y-auto">
          <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-md w-full p-4 sm:p-6 border border-gray-200 dark:border-gray-800 space-y-4 max-h-[90vh] overflow-y-auto my-auto">
            <h3 className="text-base font-bold text-gray-900 dark:text-white">
              Execute Deployment Rollback
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Document the reason for reverting this deployment:
            </p>
            <form onSubmit={handleRollback} className="space-y-4">
              <textarea
                rows={3}
                value={rollbackReason}
                onChange={(e) => setRollbackReason(e.target.value)}
                placeholder="Reason for rollback (e.g., unexpected regression in legacy API)..."
                required
                className="w-full text-xs rounded-lg border border-gray-300 dark:border-gray-700 p-2.5 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              />
              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowRollbackModal(false)}
                  className="px-3.5 py-2 text-xs text-gray-600 dark:text-gray-400 min-h-[40px]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading || !rollbackReason.trim()}
                  className="px-4 py-2 text-xs font-semibold rounded-lg bg-amber-600 text-white hover:bg-amber-700 disabled:opacity-50 min-h-[40px]"
                >
                  Execute Rollback
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
export default ClientDeploymentsPage
