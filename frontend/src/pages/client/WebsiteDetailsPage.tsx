import React, { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import {
  Globe,
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Clock,
  ShieldCheck,
  ShieldAlert,
  AlertCircle,
  Copy,
  Check,
  RefreshCw,
  FileCode,
  Tag,
  Network,
  Trash2,
} from 'lucide-react'
import {
  authorizeWebsiteScan,
  deleteWebsite,
  getWebsite,
  revokeWebsiteAuthorization,
  updateVerificationMethod,
  verifyWebsite,
} from '@/api/websites'
import { VerificationMethod, Website } from '@/types/website'
import clsx from 'clsx'

export function WebsiteDetailsPage() {
  const { websiteId } = useParams<{ websiteId: string }>()
  const navigate = useNavigate()

  const [website, setWebsite] = useState<Website | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [copiedKey, setCopiedKey] = useState<string | null>(null)

  // Verification state
  const [isVerifying, setIsVerifying] = useState(false)

  // Authorization Form state
  const [authForm, setAuthForm] = useState({
    authorized_by_name: '',
    authorized_by_email: '',
    legal_confirmation: false,
    allowed_scan_types: 'passive,owasp_standard',
  })
  const [isAuthorizing, setIsAuthorizing] = useState(false)
  const [isRevoking, setIsRevoking] = useState(false)

  // Active Tab: 'verify' | 'authorize' | 'danger'
  const [activeTab, setActiveTab] = useState<'verify' | 'authorize' | 'danger'>('verify')

  const loadWebsite = async () => {
    if (!websiteId) return
    setIsLoading(true)
    setError(null)
    try {
      const data = await getWebsite(websiteId)
      setWebsite(data)
      if (data.authorization) {
        setAuthForm({
          authorized_by_name: data.authorization.authorized_by_name,
          authorized_by_email: data.authorization.authorized_by_email,
          legal_confirmation: data.authorization.legal_confirmation,
          allowed_scan_types: data.authorization.allowed_scan_types,
        })
      }
    } catch (err: any) {
      setError(err?.userMessage || 'Failed to load website target.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadWebsite()
  }, [websiteId])

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text)
    setCopiedKey(key)
    setTimeout(() => setCopiedKey(null), 2000)
  }

  const handleSwitchMethod = async (method: VerificationMethod) => {
    if (!website) return
    try {
      setError(null)
      const updated = await updateVerificationMethod(website.id, method)
      setWebsite(updated)
    } catch (err: any) {
      setError(err?.userMessage || 'Failed to update verification method.')
    }
  }

  const handleVerify = async () => {
    if (!website) return
    setIsVerifying(true)
    setError(null)
    setSuccessMsg(null)
    try {
      const result = await verifyWebsite(website.id)
      if (result.is_verified) {
        setSuccessMsg(result.message)
        loadWebsite()
      } else {
        setError(result.message)
        loadWebsite()
      }
    } catch (err: any) {
      setError(err?.userMessage || 'Verification request failed.')
    } finally {
      setIsVerifying(false)
    }
  }

  const handleAuthorize = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!website) return
    setIsAuthorizing(true)
    setError(null)
    try {
      const updated = await authorizeWebsiteScan(website.id, authForm)
      setWebsite(updated)
      setSuccessMsg('Explicit scan authorization has been granted successfully.')
    } catch (err: any) {
      setError(err?.userMessage || 'Failed to grant scan authorization.')
    } finally {
      setIsAuthorizing(false)
    }
  }

  const handleRevoke = async () => {
    if (!website) return
    const confirm = window.confirm(
      'Are you sure you want to revoke scan authorization? Scans will be immediately disabled for this target.'
    )
    if (!confirm) return

    setIsRevoking(true)
    setError(null)
    try {
      const updated = await revokeWebsiteAuthorization(website.id, 'Revoked by authorized client.')
      setWebsite(updated)
      setSuccessMsg('Scan authorization revoked successfully.')
    } catch (err: any) {
      setError(err?.userMessage || 'Failed to revoke authorization.')
    } finally {
      setIsRevoking(false)
    }
  }

  const handleDelete = async () => {
    if (!website) return
    const confirm = window.confirm(
      `Are you sure you want to remove '${website.name}'? All verification and authorization records will be permanently deleted.`
    )
    if (!confirm) return

    try {
      await deleteWebsite(website.id)
      navigate('/dashboard/websites')
    } catch (err: any) {
      setError(err?.userMessage || 'Failed to delete website.')
    }
  }

  if (isLoading) {
    return (
      <div className="py-20 text-center text-slate-400 text-sm">
        <div className="w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
        Loading target details...
      </div>
    )
  }

  if (!website) {
    return (
      <div className="card p-6 text-center space-y-4">
        <p className="text-sm text-slate-400">Target website not found.</p>
        <Link to="/dashboard/websites" className="btn-primary text-xs mx-auto">
          Back to Websites List
        </Link>
      </div>
    )
  }

  const isVerified = website.verification_status === 'verified'
  const isAuthorized =
    website.authorization?.is_authorized && !website.authorization?.is_revoked

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Back Link */}
      <Link
        to="/dashboard/websites"
        className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-primary-500 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Target Websites
      </Link>

      {/* Target Title Card */}
      <div className="card p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                {website.name}
              </h1>
              <a
                href={website.target_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs font-mono text-primary-600 dark:text-primary-400 hover:underline"
              >
                {website.domain}
              </a>
            </div>
            <p className="text-xs text-slate-400 mt-1 font-mono">
              Base URL: {website.target_url} • Target ID: {website.id}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span
              className={clsx(
                'inline-flex items-center gap-1 text-xs font-mono font-semibold px-2.5 py-1 rounded',
                isVerified
                  ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800'
                  : 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 border border-amber-300 dark:border-amber-800'
              )}
            >
              {isVerified ? (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                  Ownership Verified
                </>
              ) : (
                <>
                  <Clock className="w-3.5 h-3.5 text-amber-500" />
                  Verification Required
                </>
              )}
            </span>

            <span
              className={clsx(
                'inline-flex items-center gap-1 text-xs font-mono font-semibold px-2.5 py-1 rounded',
                website.is_suspended_by_admin
                  ? 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300 border border-rose-300'
                  : isAuthorized
                  ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-300'
                  : 'bg-slate-100 text-slate-600 dark:bg-dark-700 dark:text-slate-400'
              )}
            >
              {website.is_suspended_by_admin ? (
                <>
                  <ShieldAlert className="w-3.5 h-3.5 text-rose-500" />
                  Suspended by Admin
                </>
              ) : isAuthorized ? (
                <>
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                  Scan Authorized
                </>
              ) : (
                'Authorization Required'
              )}
            </span>
          </div>
        </div>

        {/* Admin Suspension Notice */}
        {website.is_suspended_by_admin && (
          <div className="p-4 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-300 text-xs flex items-start gap-2.5">
            <ShieldAlert className="w-4 h-4 text-rose-500 flex-shrink-0 mt-0.5" />
            <div>
              <strong className="block font-semibold">Target Assessment Suspended by Administrator</strong>
              <span>Reason: {website.suspension_reason || 'Policy compliance review required.'}</span>
            </div>
          </div>
        )}
      </div>

      {/* Notifications */}
      {error && (
        <div className="p-4 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-500 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div className="p-4 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 text-emerald-700 dark:text-emerald-300 text-sm flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-slate-200 dark:border-dark-700 flex gap-2 sm:gap-4 text-xs sm:text-sm font-medium overflow-x-auto whitespace-nowrap pb-1">
        <button
          onClick={() => setActiveTab('verify')}
          className={clsx(
            'pb-2.5 px-1 relative transition-colors min-h-[44px] flex items-center',
            activeTab === 'verify'
              ? 'text-primary-600 dark:text-primary-400 font-bold border-b-2 border-primary-500'
              : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
          )}
        >
          1. Ownership Verification
        </button>

        <button
          onClick={() => setActiveTab('authorize')}
          className={clsx(
            'pb-2.5 px-1 relative transition-colors min-h-[44px] flex items-center',
            activeTab === 'authorize'
              ? 'text-primary-600 dark:text-primary-400 font-bold border-b-2 border-primary-500'
              : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
          )}
        >
          2. Explicit Scan Authorization
        </button>

        <button
          onClick={() => setActiveTab('danger')}
          className={clsx(
            'pb-2.5 px-1 relative transition-colors text-slate-400 hover:text-rose-500 min-h-[44px] flex items-center',
            activeTab === 'danger' && 'text-rose-600 dark:text-rose-400 font-bold border-b-2 border-rose-500'
          )}
        >
          Target Settings
        </button>
      </div>

      {/* Tab 1: Ownership Verification */}
      {activeTab === 'verify' && (
        <div className="card p-6 space-y-6">
          <div>
            <h3 className="font-bold text-slate-900 dark:text-white text-base">
              Prove Ownership or Control
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Select one of the three non-invasive verification mechanisms below to confirm you control this domain.
            </p>
          </div>

          {/* Verification Method Chooser */}
          <div className="grid sm:grid-cols-3 gap-3">
            {[
              { id: 'file', label: 'HTTP File Token', icon: FileCode, desc: 'Upload file to webroot' },
              { id: 'meta_tag', label: 'HTML Meta Tag', icon: Tag, desc: 'Add tag to <head>' },
              { id: 'dns_txt', label: 'DNS TXT Record', icon: Network, desc: 'Add DNS challenge record' },
            ].map(m => {
              const Icon = m.icon
              const isSelected = website.verification_method === m.id
              return (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => handleSwitchMethod(m.id as VerificationMethod)}
                  className={clsx(
                    'p-3.5 rounded-lg border text-left transition-colors flex items-start gap-3',
                    isSelected
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-950/60 text-primary-800 dark:text-primary-200 font-semibold'
                      : 'border-slate-200 dark:border-dark-700 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-dark-800'
                  )}
                >
                  <Icon className="w-4 h-4 text-primary-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <div className="text-xs font-medium">{m.label}</div>
                    <div className="text-[10px] text-slate-400">{m.desc}</div>
                  </div>
                </button>
              )
            })}
          </div>

          {/* Instructions Box depending on method */}
          <div className="p-5 rounded-lg bg-slate-50 dark:bg-dark-900 border border-slate-200 dark:border-dark-700 space-y-4">
            {website.verification_method === 'file' && (
              <div className="space-y-3 text-xs">
                <span className="font-bold text-slate-800 dark:text-slate-200 block">
                  Step 1: Upload Verification File
                </span>
                <p className="text-slate-600 dark:text-slate-400">
                  Create a plain-text file on your server accessible at the following URL:
                </p>
                <div className="flex items-center justify-between p-2.5 bg-slate-900 rounded font-mono text-emerald-400 text-xs">
                  <span className="break-all mr-2">{website.target_url}/.well-known/patchora-verification.txt</span>
                  <button
                    onClick={() => handleCopy(`${website.target_url}/.well-known/patchora-verification.txt`, 'path')}
                    className="text-slate-400 hover:text-white min-h-[36px] min-w-[36px] flex items-center justify-center flex-shrink-0"
                  >
                    {copiedKey === 'path' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>

                <span className="font-bold text-slate-800 dark:text-slate-200 block pt-1">
                  Step 2: File Content
                </span>
                <p className="text-slate-600 dark:text-slate-400">
                  The file must contain exactly this string:
                </p>
                <div className="flex items-center justify-between p-2.5 bg-slate-900 rounded font-mono text-emerald-400 text-xs">
                  <span className="break-all mr-2">patchora-site-verification={website.verification_token}</span>
                  <button
                    onClick={() => handleCopy(`patchora-site-verification=${website.verification_token}`, 'token')}
                    className="text-slate-400 hover:text-white min-h-[36px] min-w-[36px] flex items-center justify-center flex-shrink-0"
                  >
                    {copiedKey === 'token' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>
            )}

            {website.verification_method === 'meta_tag' && (
              <div className="space-y-3 text-xs">
                <span className="font-bold text-slate-800 dark:text-slate-200 block">
                  Add HTML Meta Tag to Homepage
                </span>
                <p className="text-slate-600 dark:text-slate-400">
                  Insert the following tag inside the <code className="font-mono text-primary-500">&lt;head&gt;</code> section of {website.target_url}:
                </p>
                <div className="flex items-center justify-between p-2.5 bg-slate-900 rounded font-mono text-emerald-400 text-xs">
                  <span className="break-all mr-2">&lt;meta name="patchora-verification" content="{website.verification_token}"&gt;</span>
                  <button
                    onClick={() => handleCopy(`<meta name="patchora-verification" content="${website.verification_token}">`, 'meta')}
                    className="text-slate-400 hover:text-white min-h-[36px] min-w-[36px] flex items-center justify-center flex-shrink-0"
                  >
                    {copiedKey === 'meta' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>
            )}

            {website.verification_method === 'dns_txt' && (
              <div className="space-y-3 text-xs">
                <span className="font-bold text-slate-800 dark:text-slate-200 block">
                  Configure DNS TXT Record
                </span>
                <p className="text-slate-600 dark:text-slate-400">
                  Add a TXT record to your domain's DNS configuration:
                </p>
                <div className="grid sm:grid-cols-2 gap-2">
                  <div className="p-2.5 bg-slate-900 rounded font-mono text-emerald-400 text-xs">
                    <span className="text-slate-500 block text-[10px]">HOST / NAME:</span>
                    <span className="break-all">_patchora-challenge.{website.domain}</span>
                  </div>
                  <div className="p-2.5 bg-slate-900 rounded font-mono text-emerald-400 text-xs">
                    <span className="text-slate-500 block text-[10px]">VALUE / DATA:</span>
                    <span className="break-all">patchora-site-verification={website.verification_token}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Action Button */}
          <div className="flex items-center justify-between pt-2">
            <span className="text-xs text-slate-400">
              {website.last_verification_attempt && (
                <>Last attempt: {new Date(website.last_verification_attempt).toLocaleTimeString()}</>
              )}
            </span>
            <button
              onClick={handleVerify}
              disabled={isVerifying || website.is_suspended_by_admin}
              className="btn-primary text-xs flex items-center gap-2"
            >
              {isVerifying ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  Testing Verification Token...
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Verify Ownership Now
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Tab 2: Explicit Scan Authorization */}
      {activeTab === 'authorize' && (
        <div className="card p-6 space-y-6">
          <div>
            <h3 className="font-bold text-slate-900 dark:text-white text-base">
              Explicit Scan Authorization Agreement
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Federal and international cybersecurity compliance requires verified written authorization before conducting vulnerability assessments.
            </p>
          </div>

          {!isVerified ? (
            <div className="p-5 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900 text-amber-800 dark:text-amber-300 text-xs space-y-2">
              <div className="flex items-center gap-2 font-bold">
                <Clock className="w-4 h-4 text-amber-500" />
                Ownership Verification Required First
              </div>
              <p>
                You must complete ownership verification on Tab 1 before granting explicit scan authorization for '{website.domain}'.
              </p>
              <button
                onClick={() => setActiveTab('verify')}
                className="btn-secondary text-xs mt-2 border-amber-300 text-amber-800 dark:text-amber-300"
              >
                Go to Verification Tab →
              </button>
            </div>
          ) : isAuthorized ? (
            <div className="p-5 rounded-lg bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-300 dark:border-emerald-800 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-emerald-700 dark:text-emerald-300 font-bold text-sm">
                  <ShieldCheck className="w-5 h-5 text-emerald-500" />
                  Explicit Scan Authorization Active
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-600 text-white font-semibold">
                  VALIDATED
                </span>
              </div>

              <div className="grid sm:grid-cols-3 gap-4 text-xs pt-1">
                <div>
                  <span className="text-slate-400 block mb-0.5">Authorized Signee</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">
                    {website.authorization?.authorized_by_name}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block mb-0.5">Contact Email</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">
                    {website.authorization?.authorized_by_email}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block mb-0.5">Authorization Window</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">
                    90 Days (Expires: {website.authorization?.expires_at ? new Date(website.authorization.expires_at).toLocaleDateString() : 'N/A'})
                  </span>
                </div>
              </div>

              <div className="pt-3 border-t border-emerald-200 dark:border-emerald-900 flex justify-end">
                <button
                  onClick={handleRevoke}
                  disabled={isRevoking}
                  className="btn-ghost text-xs text-rose-600 dark:text-rose-400 hover:bg-rose-100 dark:hover:bg-rose-950/40"
                >
                  {isRevoking ? 'Revoking...' : 'Revoke Scan Authorization'}
                </button>
              </div>
            </div>
          ) : (
            <form onSubmit={handleAuthorize} className="space-y-4">
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Signee Full Legal Name
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Jane Doe (CISO / Asset Owner)"
                    value={authForm.authorized_by_name}
                    onChange={e => setAuthForm({ ...authForm, authorized_by_name: e.target.value })}
                    className="w-full px-3.5 py-2 rounded-lg border border-slate-300 dark:border-dark-600 bg-white dark:bg-dark-900 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Authorizing Contact Email
                  </label>
                  <input
                    type="email"
                    required
                    placeholder="security@example.com"
                    value={authForm.authorized_by_email}
                    onChange={e => setAuthForm({ ...authForm, authorized_by_email: e.target.value })}
                    className="w-full px-3.5 py-2 rounded-lg border border-slate-300 dark:border-dark-600 bg-white dark:bg-dark-900 text-sm"
                  />
                </div>
              </div>

              <div className="p-4 rounded-lg bg-slate-50 dark:bg-dark-900 border border-slate-200 dark:border-dark-700 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    required
                    checked={authForm.legal_confirmation}
                    onChange={e => setAuthForm({ ...authForm, legal_confirmation: e.target.checked })}
                    className="mt-0.5 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span>
                    <strong className="text-slate-800 dark:text-slate-200 block mb-0.5">
                      Legal Warrant & Authorization Agreement:
                    </strong>
                    I hereby certify and warrant that I am the authorized owner or have obtained explicit written legal permission to conduct security vulnerability assessments against <code className="font-mono text-primary-500">{website.domain}</code>. I authorize PATCHORA to perform passive and standard OWASP assessment tests.
                  </span>
                </label>
              </div>

              <div className="flex justify-end pt-2">
                <button
                  type="submit"
                  disabled={isAuthorizing || !authForm.legal_confirmation}
                  className="btn-primary text-xs"
                >
                  {isAuthorizing ? 'Authorizing...' : 'Grant Explicit Scan Authorization'}
                </button>
              </div>
            </form>
          )}
        </div>
      )}

      {/* Tab 3: Danger Zone */}
      {activeTab === 'danger' && (
        <div className="card p-6 border-rose-200 dark:border-rose-900 space-y-4">
          <div className="border-b border-rose-100 dark:border-rose-950 pb-3">
            <h3 className="font-bold text-rose-600 dark:text-rose-400 text-sm flex items-center gap-2">
              <Trash2 className="w-4 h-4" />
              Target Management & Removal
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              Remove this registered target from your workspace.
            </p>
          </div>

          <div className="flex items-center justify-between pt-2">
            <div>
              <span className="font-semibold text-slate-800 dark:text-slate-200 text-xs block">
                Delete Target Website
              </span>
              <span className="text-xs text-slate-400">
                Permanently delete this target, its verification token, and authorization history.
              </span>
            </div>
            <button
              onClick={handleDelete}
              className="btn text-xs bg-rose-600 hover:bg-rose-700 text-white"
            >
              Remove Target
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
