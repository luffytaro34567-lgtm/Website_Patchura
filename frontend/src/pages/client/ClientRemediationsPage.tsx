import React, { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  approvePatch,
  createRemediation,
  downloadPatchFile,
  downloadPatchedCodeFile,
  getRemediation,
  listMyRemediations,
  rejectPatch,
  testPatch,
} from '@/api/remediations'
import { getScan } from '@/api/scans'
import { listWebsites } from '@/api/websites'
import { RemediationSession, RemediationSessionSummary } from '@/types/remediation'
import { ScanFinding } from '@/types/scan'

export const ClientRemediationsPage: React.FC = () => {
  const [searchParams] = useSearchParams()
  const initialFindingId = searchParams.get('finding_id') || ''

  const [sessions, setSessions] = useState<RemediationSessionSummary[]>([])
  const [activeSession, setActiveSession] = useState<RemediationSession | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [actionLoading, setActionLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // New Remediation Modal state
  const [showModal, setShowModal] = useState<boolean>(false)
  const [findingId, setFindingId] = useState<string>(initialFindingId)
  const [targetFilename, setTargetFilename] = useState<string>('index.php')
  const [language, setLanguage] = useState<string>('php')
  const [inputMethod, setInputMethod] = useState<'snippet' | 'file_upload'>('snippet')
  const [sourceCode, setSourceCode] = useState<string>('')
  const [consentAcknowledged, setConsentAcknowledged] = useState<boolean>(true)

  // Approval / Rejection modal state
  const [approvalNotes, setApprovalNotes] = useState<string>('')
  const [rejectionReason, setRejectionReason] = useState<string>('')
  const [showApproveDialog, setShowApproveDialog] = useState<boolean>(false)
  const [showRejectDialog, setShowRejectDialog] = useState<boolean>(false)
  const [showDiagnostics, setShowDiagnostics] = useState<boolean>(false)
  const [activeTab, setActiveTab] = useState<'diff' | 'sideBySide' | 'explanation'>('diff')

  useEffect(() => {
    loadSessions()
    if (initialFindingId) {
      setFindingId(initialFindingId)
      setShowModal(true)
    }
  }, [initialFindingId])

  const loadSessions = async () => {
    try {
      setLoading(true)
      const data = await listMyRemediations()
      setSessions(data)
      if (data.length > 0 && !activeSession) {
        loadSessionDetails(data[0].id)
      }
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Failed to load remediation sessions.')
    } finally {
      setLoading(false)
    }
  }

  const loadSessionDetails = async (sessionId: string) => {
    try {
      setActionLoading(true)
      const data = await getRemediation(sessionId)
      setActiveSession(data)
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Failed to load remediation details.')
    } finally {
      setActionLoading(false)
    }
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setTargetFilename(file.name)
    const reader = new FileReader()
    reader.onload = (event) => {
      if (typeof event.target?.result === 'string') {
        setSourceCode(event.target.result)
      }
    }
    reader.readAsText(file)
  }

  const handleCreateRemediation = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!findingId.trim()) {
      setError('Please provide a valid Finding ID.')
      return
    }
    if (!sourceCode.trim()) {
      setError('Please provide source code content to remediate.')
      return
    }
    if (!consentAcknowledged) {
      setError('You must acknowledge and consent to code analysis.')
      return
    }

    try {
      setActionLoading(true)
      setError(null)
      const newSession = await createRemediation({
        finding_id: findingId,
        input_method: inputMethod,
        target_filename: targetFilename,
        language,
        source_code: sourceCode,
        consent_acknowledged: consentAcknowledged,
      })
      setActiveSession(newSession)
      setShowModal(false)
      setSuccessMsg(`Proposed patch generated successfully for ${targetFilename}!`)
      loadSessions()
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Failed to generate remediation patch.')
    } finally {
      setActionLoading(false)
    }
  }

  const handleReRunTest = async () => {
    if (!activeSession) return
    try {
      setActionLoading(true)
      setError(null)
      const testRes = await testPatch(activeSession.id)
      setActiveSession({
        ...activeSession,
        test_status: testRes.test_status,
        test_output: testRes.diagnostics,
        tested_at: testRes.tested_at,
        status: testRes.passed ? 'test_passed' : 'test_failed',
      })
      setSuccessMsg(`Isolated sandbox verification completed: ${testRes.test_status.toUpperCase()}`)
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Failed to run isolated verification test.')
    } finally {
      setActionLoading(false)
    }
  }

  const handleApprove = async () => {
    if (!activeSession) return
    try {
      setActionLoading(true)
      const updated = await approvePatch(activeSession.id, approvalNotes)
      setActiveSession(updated)
      setShowApproveDialog(false)
      setSuccessMsg('Patch has been explicitly approved by client.')
      loadSessions()
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Failed to approve patch.')
    } finally {
      setActionLoading(false)
    }
  }

  const handleReject = async () => {
    if (!activeSession || !rejectionReason.trim()) return
    try {
      setActionLoading(true)
      const updated = await rejectPatch(activeSession.id, rejectionReason)
      setActiveSession(updated)
      setShowRejectDialog(false)
      setSuccessMsg('Patch proposal has been rejected.')
      loadSessions()
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Failed to reject patch.')
    } finally {
      setActionLoading(false)
    }
  }

  const handleDownloadPatch = async () => {
    if (!activeSession) return
    try {
      await downloadPatchFile(activeSession.id, `${activeSession.target_filename}_fix.patch`)
    } catch (err: any) {
      setError('Failed to download patch file.')
    }
  }

  const handleDownloadPatchedFile = async () => {
    if (!activeSession) return
    try {
      await downloadPatchedCodeFile(activeSession.id, `patched_${activeSession.target_filename}`)
    } catch (err: any) {
      setError('Failed to download patched code file.')
    }
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-gray-200 dark:border-gray-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              AI Bug-Fixing & Remediation Engine
            </h1>
            <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-cyan-100 text-cyan-800 dark:bg-cyan-950/60 dark:text-cyan-400 border border-cyan-300 dark:border-cyan-800">
              Phase 8 Complete
            </span>
          </div>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Generate verifiable security patches, run isolated static AST sandbox tests, and review unified code diffs before explicit approval.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-cyan-600 hover:bg-cyan-700 dark:bg-cyan-500 dark:hover:bg-cyan-600 transition"
          >
            + Request AI Fix
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-red-500 hover:text-red-700 text-xs font-bold">
            Dismiss
          </button>
        </div>
      )}

      {successMsg && (
        <div className="p-4 rounded-lg bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300 text-sm flex items-center justify-between">
          <span>{successMsg}</span>
          <button onClick={() => setSuccessMsg(null)} className="text-emerald-500 hover:text-emerald-700 text-xs font-bold">
            Dismiss
          </button>
        </div>
      )}

      {/* Main Grid: Sidebar List & Detail View */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Sessions List */}
        <div className="lg:col-span-4 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-gray-900 dark:text-white">Remediation Sessions</h2>
            <span className="text-xs text-gray-500 dark:text-gray-400">{sessions.length} recorded</span>
          </div>

          {loading ? (
            <div className="p-8 text-center text-sm text-gray-500 dark:text-gray-400">Loading sessions...</div>
          ) : sessions.length === 0 ? (
            <div className="p-8 text-center rounded-xl border border-dashed border-gray-300 dark:border-gray-800 bg-white dark:bg-gray-900/40">
              <p className="text-sm text-gray-500 dark:text-gray-400">No remediation requests submitted yet.</p>
              <button
                onClick={() => setShowModal(true)}
                className="mt-3 text-xs font-medium text-cyan-600 dark:text-cyan-400 hover:underline"
              >
                Create your first fix request
              </button>
            </div>
          ) : (
            <div className="space-y-3 max-h-[700px] overflow-y-auto pr-1">
              {sessions.map((s) => {
                const isSelected = activeSession?.id === s.id
                return (
                  <div
                    key={s.id}
                    onClick={() => loadSessionDetails(s.id)}
                    className={`p-4 rounded-xl border cursor-pointer transition ${
                      isSelected
                        ? 'border-cyan-500 bg-cyan-50/40 dark:bg-cyan-950/20 shadow-sm'
                        : 'border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 hover:border-gray-300 dark:hover:border-gray-700'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="text-xs font-mono text-cyan-600 dark:text-cyan-400 font-semibold truncate">
                        {s.target_filename}
                      </span>
                      <span
                        className={`px-2 py-0.5 text-[10px] font-semibold rounded-full uppercase ${
                          s.approval_status === 'approved'
                            ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-400'
                            : s.approval_status === 'rejected'
                            ? 'bg-red-100 text-red-800 dark:bg-red-950/60 dark:text-red-400'
                            : 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-400'
                        }`}
                      >
                        {s.approval_status}
                      </span>
                    </div>
                    <p className="mt-1 text-xs font-medium text-gray-900 dark:text-white line-clamp-1">
                      {s.finding_title}
                    </p>
                    <div className="mt-2 flex items-center justify-between text-[11px] text-gray-500 dark:text-gray-400">
                      <span>{s.website_domain}</span>
                      <span className="capitalize font-mono">Test: {s.test_status}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Right Column: Interactive Patch Reviewer */}
        <div className="lg:col-span-8">
          {activeSession ? (
            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6 shadow-sm space-y-6">
              {/* Session Header */}
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 border-b border-gray-200 dark:border-gray-800 pb-5">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 uppercase">
                      {activeSession.language}
                    </span>
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                      {activeSession.target_filename}
                    </h3>
                  </div>
                  <p className="mt-1 text-sm font-medium text-gray-700 dark:text-gray-300">
                    Fixing: {activeSession.finding_title || 'Identified Finding'}
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <div className="px-3 py-1 rounded-full text-xs font-semibold bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 flex items-center gap-1.5 border border-gray-300 dark:border-gray-700">
                    <span className="w-2 h-2 rounded-full bg-cyan-500"></span>
                    <span>Provider: {activeSession.ai_provider}</span>
                  </div>
                  <span
                    className={`px-3 py-1 text-xs font-semibold rounded-full uppercase ${
                      activeSession.approval_status === 'approved'
                        ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-300 dark:border-emerald-800'
                        : activeSession.approval_status === 'rejected'
                        ? 'bg-red-100 text-red-800 dark:bg-red-950/60 dark:text-red-400 border border-red-300 dark:border-red-800'
                        : 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-400 border border-amber-300 dark:border-amber-800'
                    }`}
                  >
                    Approval: {activeSession.approval_status}
                  </span>
                </div>
              </div>

              {/* PHP2Shell Zero-Day Alert banner if applicable */}
              {activeSession.php2shell_mitigation_notes && (
                <div className="p-4 rounded-xl bg-purple-50 dark:bg-purple-950/40 border border-purple-200 dark:border-purple-800 text-sm">
                  <div className="flex items-center gap-2 font-bold text-purple-900 dark:text-purple-300">
                    <span>🛡️ PHP2Shell (CVE-2026-109618 / 19) Memory Corruption Mitigation Active</span>
                  </div>
                  <p className="mt-1 text-xs text-purple-800 dark:text-purple-300">
                    {activeSession.php2shell_mitigation_notes}
                  </p>
                </div>
              )}

              {/* Isolated Sandbox Verification Status Card */}
              <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-950/50 border border-gray-200 dark:border-gray-800">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-3 h-3 rounded-full flex-shrink-0 ${
                        activeSession.test_status === 'passed' ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'
                      }`}
                    />
                    <div>
                      <h4 className="text-sm font-semibold text-gray-900 dark:text-white">
                        Isolated Static Sandbox Verification: {activeSession.test_status.toUpperCase()}
                      </h4>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        Zero Host Execution — Tested AST syntax, anti-malware patterns, and vulnerability regression.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-start sm:self-auto flex-wrap">
                    <button
                      onClick={() => setShowDiagnostics(!showDiagnostics)}
                      className="px-2.5 py-1.5 min-h-[36px] text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                    >
                      {showDiagnostics ? 'Hide Logs' : 'View Test Diagnostics'}
                    </button>
                    <button
                      onClick={handleReRunTest}
                      disabled={actionLoading}
                      className="px-3 py-1.5 min-h-[36px] text-xs font-medium rounded-lg bg-cyan-600 text-white hover:bg-cyan-700 disabled:opacity-50"
                    >
                      {actionLoading ? 'Testing...' : 'Re-Run Test'}
                    </button>
                  </div>
                </div>

                {showDiagnostics && activeSession.test_output && (
                  <div className="mt-3 p-3 rounded-lg bg-gray-900 text-gray-200 font-mono text-xs overflow-x-auto whitespace-pre-wrap max-h-60 border border-gray-800">
                    {activeSession.test_output}
                  </div>
                )}
              </div>

              {/* Code Review Tabs */}
              <div className="border-b border-gray-200 dark:border-gray-800">
                <nav className="flex space-x-6 text-sm font-medium">
                  <button
                    onClick={() => setActiveTab('diff')}
                    className={`pb-3 border-b-2 transition ${
                      activeTab === 'diff'
                        ? 'border-cyan-500 text-cyan-600 dark:text-cyan-400'
                        : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
                    }`}
                  >
                    Unified Diff (.patch)
                  </button>
                  <button
                    onClick={() => setActiveTab('sideBySide')}
                    className={`pb-3 border-b-2 transition ${
                      activeTab === 'sideBySide'
                        ? 'border-cyan-500 text-cyan-600 dark:text-cyan-400'
                        : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
                    }`}
                  >
                    Patched Full Source
                  </button>
                  <button
                    onClick={() => setActiveTab('explanation')}
                    className={`pb-3 border-b-2 transition ${
                      activeTab === 'explanation'
                        ? 'border-cyan-500 text-cyan-600 dark:text-cyan-400'
                        : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
                    }`}
                  >
                    Security Explanation & Warnings
                  </button>
                </nav>
              </div>

              {/* Tab Content */}
              {activeTab === 'diff' && (
                <div className="bg-gray-950 text-gray-200 font-mono text-xs p-4 rounded-xl overflow-x-auto border border-gray-800 max-h-[450px]">
                  {activeSession.proposed_diff ? (
                    activeSession.proposed_diff.split('\n').map((line, idx) => {
                      let colorClass = 'text-gray-300'
                      let bgClass = ''
                      if (line.startsWith('+') && !line.startsWith('+++')) {
                        colorClass = 'text-emerald-400 font-medium'
                        bgClass = 'bg-emerald-950/40'
                      } else if (line.startsWith('-') && !line.startsWith('---')) {
                        colorClass = 'text-red-400 font-medium'
                        bgClass = 'bg-red-950/40'
                      } else if (line.startsWith('@@')) {
                        colorClass = 'text-cyan-400'
                        bgClass = 'bg-cyan-950/30'
                      }
                      return (
                        <div key={idx} className={`px-2 py-0.5 rounded ${bgClass} ${colorClass}`}>
                          {line}
                        </div>
                      )
                    })
                  ) : (
                    <span className="text-gray-500">No diff generated.</span>
                  )}
                </div>
              )}

              {activeTab === 'sideBySide' && (
                <div className="bg-gray-950 text-gray-200 font-mono text-xs p-4 rounded-xl overflow-x-auto border border-gray-800 max-h-[450px] whitespace-pre">
                  {activeSession.patched_code || '// No patched code available.'}
                </div>
              )}

              {activeTab === 'explanation' && (
                <div className="space-y-4 text-sm text-gray-700 dark:text-gray-300">
                  <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-800/40 border border-gray-200 dark:border-gray-800">
                    <h5 className="font-semibold text-gray-900 dark:text-white">Technical Remediation Rationale</h5>
                    <p className="mt-1 text-xs text-gray-600 dark:text-gray-400">
                      {activeSession.explanation || 'No explanation provided.'}
                    </p>
                  </div>

                  {activeSession.security_warnings && (
                    <div className="p-4 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800">
                      <h5 className="font-semibold text-amber-900 dark:text-amber-300">Operational Warnings</h5>
                      <p className="mt-1 text-xs text-amber-800 dark:text-amber-400 whitespace-pre-wrap">
                        {activeSession.security_warnings}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Human-in-the-Loop Explicit Approval & Download Controls */}
              <div className="flex flex-wrap items-center justify-between gap-4 pt-4 border-t border-gray-200 dark:border-gray-800">
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleDownloadPatch}
                    className="px-3.5 py-2 text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition"
                  >
                    ⬇️ Download .patch File
                  </button>
                  <button
                    onClick={handleDownloadPatchedFile}
                    className="px-3.5 py-2 text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition"
                  >
                    ⬇️ Download Full Source
                  </button>
                </div>

                <div className="flex items-center gap-3">
                  {activeSession.approval_status === 'pending' ? (
                    <>
                      <button
                        onClick={() => setShowRejectDialog(true)}
                        className="px-4 py-2 text-xs font-semibold rounded-lg bg-red-100 text-red-700 hover:bg-red-200 dark:bg-red-950/60 dark:text-red-300 transition"
                      >
                        Reject Patch
                      </button>
                      <button
                        onClick={() => setShowApproveDialog(true)}
                        className="px-5 py-2 text-xs font-semibold rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 transition shadow-sm"
                      >
                        ✓ Explicitly Approve Patch
                      </button>
                    </>
                  ) : activeSession.approval_status === 'approved' ? (
                    <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                      <span>✓ Approved by Client</span>
                      {activeSession.approved_at && (
                        <span className="text-gray-500">
                          ({new Date(activeSession.approved_at).toLocaleDateString()})
                        </span>
                      )}
                    </span>
                  ) : (
                    <span className="text-xs font-semibold text-red-600 dark:text-red-400">
                      ✗ Rejected: {activeSession.approval_notes}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-12 text-center text-gray-500 dark:text-gray-400">
              Select a remediation session from the left or request a new AI fix.
            </div>
          )}
        </div>
      </div>

      {/* New Remediation Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-2xl w-full border border-gray-200 dark:border-gray-800 p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-800 pb-4">
              <div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                  Request AI Security Remediation
                </h3>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  Input target source code to generate an isolated, verifiable security patch.
                </p>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="text-gray-400 hover:text-gray-500 font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateRemediation} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">
                  Target Finding ID
                </label>
                <input
                  type="text"
                  value={findingId}
                  onChange={(e) => setFindingId(e.target.value)}
                  placeholder="e.g. 3fa85f64-5717-4562-b3fc-2c963f66afa6"
                  required
                  className="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">
                    Filename / Path
                  </label>
                  <input
                    type="text"
                    value={targetFilename}
                    onChange={(e) => setTargetFilename(e.target.value)}
                    placeholder="index.php"
                    required
                    className="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">
                    Language
                  </label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white"
                  >
                    <option value="php">PHP</option>
                    <option value="python">Python</option>
                    <option value="javascript">JavaScript</option>
                    <option value="typescript">TypeScript</option>
                    <option value="html">HTML</option>
                    <option value="nginx">Nginx Config</option>
                  </select>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs font-medium text-gray-700 dark:text-gray-300">
                    Source Code Input
                  </label>
                  <div className="flex items-center gap-4 text-xs">
                    <label className="flex items-center gap-1 cursor-pointer">
                      <input
                        type="radio"
                        checked={inputMethod === 'snippet'}
                        onChange={() => setInputMethod('snippet')}
                      />
                      <span>Paste Code</span>
                    </label>
                    <label className="flex items-center gap-1 cursor-pointer">
                      <input
                        type="radio"
                        checked={inputMethod === 'file_upload'}
                        onChange={() => setInputMethod('file_upload')}
                      />
                      <span>Upload File</span>
                    </label>
                  </div>
                </div>

                {inputMethod === 'file_upload' ? (
                  <div className="mt-1 border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg p-6 text-center">
                    <input
                      type="file"
                      onChange={handleFileUpload}
                      className="text-xs text-gray-500"
                    />
                    <p className="mt-1 text-xs text-gray-400">
                      Supports .php, .py, .js, .ts, .conf, .html (Max 1MB)
                    </p>
                  </div>
                ) : (
                  <textarea
                    rows={8}
                    value={sourceCode}
                    onChange={(e) => setSourceCode(e.target.value)}
                    placeholder="Paste vulnerable source code snippet here..."
                    required
                    className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-gray-950 text-gray-200 font-mono text-xs p-3"
                  />
                )}
              </div>

              <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-800/40 border border-gray-200 dark:border-gray-800">
                <label className="flex items-start gap-2.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={consentAcknowledged}
                    onChange={(e) => setConsentAcknowledged(e.target.checked)}
                    className="mt-0.5 rounded text-cyan-600 focus:ring-cyan-500"
                  />
                  <span className="text-xs text-gray-600 dark:text-gray-400">
                    I explicitly consent to static code vulnerability remediation analysis. I understand patches
                    are tested in an isolated AST sandbox and will never be deployed automatically without my explicit approval.
                  </span>
                </label>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-gray-200 dark:border-gray-800">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-xs font-medium rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-5 py-2 text-xs font-semibold rounded-lg bg-cyan-600 text-white hover:bg-cyan-700 disabled:opacity-50"
                >
                  {actionLoading ? 'Analyzing & Patching...' : 'Generate Patch'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Explicit Approval Dialog */}
      {showApproveDialog && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-900 rounded-xl max-w-md w-full p-6 border border-gray-200 dark:border-gray-800 space-y-4">
            <h4 className="text-base font-bold text-gray-900 dark:text-white">
              Explicit Client Approval Sign-Off
            </h4>
            <p className="text-xs text-gray-600 dark:text-gray-400">
              Confirm that you have reviewed the unified diff and test diagnostics. Approved patches can be downloaded for your deployment pipeline.
            </p>
            <textarea
              rows={3}
              value={approvalNotes}
              onChange={(e) => setApprovalNotes(e.target.value)}
              placeholder="Optional sign-off notes (e.g. Verified for staging deployment)..."
              className="w-full text-xs rounded-lg border border-gray-300 dark:border-gray-700 p-2.5 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setShowApproveDialog(false)}
                className="px-3 py-1.5 text-xs text-gray-600 dark:text-gray-400"
              >
                Cancel
              </button>
              <button
                onClick={handleApprove}
                disabled={actionLoading}
                className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-emerald-600 text-white hover:bg-emerald-700"
              >
                Confirm Approval
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Rejection Dialog */}
      {showRejectDialog && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-900 rounded-xl max-w-md w-full p-6 border border-gray-200 dark:border-gray-800 space-y-4">
            <h4 className="text-base font-bold text-gray-900 dark:text-white">Reject Patch Proposal</h4>
            <p className="text-xs text-gray-600 dark:text-gray-400">
              Please specify the reason for rejecting this proposed patch:
            </p>
            <textarea
              rows={3}
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              placeholder="e.g. Incompatible with legacy routing framework..."
              required
              className="w-full text-xs rounded-lg border border-gray-300 dark:border-gray-700 p-2.5 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setShowRejectDialog(false)}
                className="px-3 py-1.5 text-xs text-gray-600 dark:text-gray-400"
              >
                Cancel
              </button>
              <button
                onClick={handleReject}
                disabled={actionLoading || !rejectionReason.trim()}
                className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-50"
              >
                Confirm Rejection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
export default ClientRemediationsPage
