import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Globe,
  Plus,
  ShieldCheck,
  ShieldAlert,
  Clock,
  AlertCircle,
  ExternalLink,
  CheckCircle2,
  XCircle,
  Search,
} from 'lucide-react'
import { createWebsite, listWebsites } from '@/api/websites'
import { VerificationMethod, Website } from '@/types/website'
import clsx from 'clsx'

export function WebsitesListPage() {
  const [websites, setWebsites] = useState<Website[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')

  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [createForm, setCreateForm] = useState({
    name: '',
    target_url: '',
    verification_method: 'file' as VerificationMethod,
  })
  const [modalError, setModalError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const loadWebsites = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await listWebsites()
      setWebsites(data)
    } catch (err: any) {
      setError(err?.userMessage || 'Failed to load target websites.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadWebsites()
  }, [])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setModalError(null)

    if (!createForm.name.trim() || !createForm.target_url.trim()) {
      setModalError('Target name and URL are required.')
      return
    }

    try {
      setIsSubmitting(true)
      const newSite = await createWebsite(createForm)
      setWebsites(prev => [newSite, ...prev])
      setIsModalOpen(false)
      setCreateForm({ name: '', target_url: '', verification_method: 'file' })
    } catch (err: any) {
      setModalError(err?.userMessage || 'Failed to register target website.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const filtered = websites.filter(
    w =>
      w.name.toLowerCase().includes(search.toLowerCase()) ||
      w.domain.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200 dark:border-dark-700">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Globe className="w-6 h-6 text-primary-500" />
            Target Websites & Scope Management
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Register, verify ownership, and explicitly authorize vulnerability assessments on your web properties
          </p>
        </div>

        <button
          onClick={() => {
            setModalError(null)
            setIsModalOpen(true)
          }}
          className="btn-primary text-xs flex items-center gap-1.5 self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          Add Target Website
        </button>
      </div>

      {/* Safety Notice */}
      <div className="p-4 rounded-lg bg-primary-50/50 dark:bg-primary-950/20 border border-primary-200 dark:border-primary-800 text-xs text-primary-800 dark:text-primary-300 flex items-start gap-2.5">
        <ShieldCheck className="w-4 h-4 text-primary-500 flex-shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <strong className="font-semibold block mb-0.5">Explicit Authorization Policy:</strong>
          A registered URL <span className="underline font-bold">never automatically triggers a scan</span>.
          Ownership verification and explicit signed authorization are strictly required before any testing.
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-500 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Search Bar */}
      <div className="card p-3 flex items-center gap-2">
        <Search className="w-4 h-4 text-slate-400 ml-1" />
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Filter targets by name or domain..."
          className="w-full bg-transparent border-0 text-sm focus:ring-0 text-slate-900 dark:text-white placeholder-slate-400"
        />
      </div>

      {/* Websites List */}
      {isLoading ? (
        <div className="py-16 text-center text-slate-400 text-sm">
          <div className="w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          Loading target websites...
        </div>
      ) : filtered.length === 0 ? (
        <div className="card p-12 text-center space-y-4">
          <div className="w-12 h-12 rounded-xl bg-slate-100 dark:bg-dark-700 text-slate-400 flex items-center justify-center mx-auto">
            <Globe className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-900 dark:text-white">
              No target websites registered yet
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-sm mx-auto">
              Add a web application you own or have explicit authorization to assess to begin the verification process.
            </p>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="btn-primary text-xs mx-auto"
          >
            <Plus className="w-3.5 h-3.5 mr-1" />
            Add First Website Target
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {filtered.map(site => {
            const isVerified = site.verification_status === 'verified'
            const isAuthorized = site.authorization?.is_authorized && !site.authorization?.is_revoked

            return (
              <div
                key={site.id}
                className="card p-5 hover:border-slate-300 dark:hover:border-dark-600 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="space-y-1.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-bold text-slate-900 dark:text-white text-base">
                      {site.name}
                    </span>
                    <a
                      href={site.target_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-slate-400 hover:text-primary-500 font-mono flex items-center gap-1"
                    >
                      {site.target_url}
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>

                  <div className="flex flex-wrap items-center gap-2 pt-1">
                    {/* Verification Status Badge */}
                    <span
                      className={clsx(
                        'inline-flex items-center gap-1 text-[11px] font-mono font-medium px-2 py-0.5 rounded',
                        isVerified
                          ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800'
                          : site.verification_status === 'failed'
                          ? 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300 border border-rose-300 dark:border-rose-800'
                          : 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 border border-amber-300 dark:border-amber-800'
                      )}
                    >
                      {isVerified ? (
                        <>
                          <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                          Ownership Verified
                        </>
                      ) : site.verification_status === 'failed' ? (
                        <>
                          <XCircle className="w-3 h-3 text-rose-500" />
                          Verification Failed
                        </>
                      ) : (
                        <>
                          <Clock className="w-3 h-3 text-amber-500" />
                          Pending Verification
                        </>
                      )}
                    </span>

                    {/* Authorization Badge */}
                    <span
                      className={clsx(
                        'inline-flex items-center gap-1 text-[11px] font-mono font-medium px-2 py-0.5 rounded',
                        site.is_suspended_by_admin
                          ? 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300 border border-rose-300'
                          : isAuthorized
                          ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-300'
                          : 'bg-slate-100 text-slate-600 dark:bg-dark-700 dark:text-slate-400'
                      )}
                    >
                      {site.is_suspended_by_admin ? (
                        <>
                          <ShieldAlert className="w-3 h-3 text-rose-500" />
                          Suspended by Admin
                        </>
                      ) : isAuthorized ? (
                        <>
                          <ShieldCheck className="w-3 h-3 text-emerald-500" />
                          Scan Authorized
                        </>
                      ) : (
                        'Scan Authorization Required'
                      )}
                    </span>

                    <span className="text-[11px] text-slate-400 font-mono ml-1">
                      Method: {site.verification_method.toUpperCase()}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2 self-start md:self-auto">
                  <Link
                    to={`/dashboard/websites/${site.id}`}
                    className="btn-primary text-xs"
                  >
                    Manage & Verify →
                  </Link>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Add Website Target Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="card max-w-lg w-full p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-dark-700 pb-3">
              <h3 className="font-bold text-slate-900 dark:text-white text-base flex items-center gap-2">
                <Globe className="w-5 h-5 text-primary-500" />
                Register Target Website
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-sm p-1"
              >
                ✕
              </button>
            </div>

            {modalError && (
              <div className="p-3.5 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-500" />
                <span>{modalError}</span>
              </div>
            )}

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label htmlFor="target-name" className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Friendly Target Name
                </label>
                <input
                  id="target-name"
                  type="text"
                  required
                  placeholder="e.g. Production Web Portal"
                  value={createForm.name}
                  onChange={e => setCreateForm({ ...createForm, name: e.target.value })}
                  className="w-full px-3.5 py-2 rounded-lg border border-slate-300 dark:border-dark-600 bg-white dark:bg-dark-900 text-sm"
                />
              </div>

              <div>
                <label htmlFor="target-url" className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Target URL
                </label>
                <input
                  id="target-url"
                  type="text"
                  required
                  placeholder="https://example.com"
                  value={createForm.target_url}
                  onChange={e => setCreateForm({ ...createForm, target_url: e.target.value })}
                  className="w-full px-3.5 py-2 rounded-lg border border-slate-300 dark:border-dark-600 bg-white dark:bg-dark-900 text-sm font-mono text-xs"
                />
                <p className="text-[11px] text-slate-400 mt-1">
                  Must be public HTTP/HTTPS URL. Localhost, 127.0.0.1, private RFC-1918, and cloud metadata targets are prohibited (SSRF prevention).
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                  Initial Ownership Verification Method
                </label>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  {[
                    { id: 'file', label: 'HTTP File Token', desc: '.well-known/...' },
                    { id: 'meta_tag', label: 'HTML Meta Tag', desc: '<meta ...>' },
                    { id: 'dns_txt', label: 'DNS TXT Record', desc: '_patchora...' },
                  ].map(m => (
                    <button
                      key={m.id}
                      type="button"
                      onClick={() =>
                        setCreateForm({
                          ...createForm,
                          verification_method: m.id as VerificationMethod,
                        })
                      }
                      className={clsx(
                        'p-2.5 rounded-lg border text-left transition-colors',
                        createForm.verification_method === m.id
                          ? 'border-primary-500 bg-primary-50 dark:bg-primary-950/60 text-primary-700 dark:text-primary-300 font-semibold'
                          : 'border-slate-200 dark:border-dark-700 text-slate-600 dark:text-slate-400'
                      )}
                    >
                      <div className="font-medium">{m.label}</div>
                      <div className="text-[10px] text-slate-400 font-mono">{m.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="pt-2 flex items-center justify-end gap-2 border-t border-slate-100 dark:border-dark-700">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="btn-ghost text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="btn-primary text-xs"
                >
                  {isSubmitting ? 'Registering...' : 'Register Target'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
