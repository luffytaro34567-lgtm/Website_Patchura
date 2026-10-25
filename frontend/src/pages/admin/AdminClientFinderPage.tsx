import React, { useEffect, useState } from 'react'
import {
  addSuppression,
  convertLead,
  createCampaign,
  createLead,
  draftOutreach,
  getClientFinderStats,
  listCampaigns,
  listLeads,
  listOutreachTemplates,
  listSuppressionList,
  runCampaignDiscovery,
  sendOutreach,
  updateLead,
} from '@/api/leads'
import {
  ClientFinderStats,
  DiscoveryCampaign,
  Lead,
  OutreachDraft,
  OutreachTemplate,
  SuppressionEntry,
} from '@/types/lead'

export const AdminClientFinderPage: React.FC = () => {
  const [stats, setStats] = useState<ClientFinderStats | null>(null)
  const [leads, setLeads] = useState<Lead[]>([])
  const [campaigns, setCampaigns] = useState<DiscoveryCampaign[]>([])
  const [templates, setTemplates] = useState<OutreachTemplate[]>([])
  const [suppressionList, setSuppressionList] = useState<SuppressionEntry[]>([])

  const [activeTab, setActiveTab] = useState<'leads' | 'campaigns' | 'outreach' | 'suppression'>('leads')
  const [loading, setLoading] = useState<boolean>(true)
  const [actionLoading, setActionLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [riskFilter, setRiskFilter] = useState<string>('')
  const [searchTerm, setSearchTerm] = useState<string>('')

  // Modals
  const [showAddLeadModal, setShowAddLeadModal] = useState<boolean>(false)
  const [showCampaignModal, setShowCampaignModal] = useState<boolean>(false)
  const [showOutreachModal, setShowOutreachModal] = useState<boolean>(false)
  const [showSuppressionModal, setShowSuppressionModal] = useState<boolean>(false)

  // Forms
  const [newCompanyName, setNewCompanyName] = useState<string>('')
  const [newDomain, setNewDomain] = useState<string>('')
  const [newContactEmail, setNewContactEmail] = useState<string>('')
  const [newContactName, setNewContactName] = useState<string>('')
  const [newTechStack, setNewTechStack] = useState<string>('PHP 8.2, Laravel')
  const [newRiskLevel, setNewRiskLevel] = useState<string>('high')

  const [campaignName, setCampaignName] = useState<string>('')
  const [campaignTech, setCampaignTech] = useState<string>('PHP / Laravel / WordPress')
  const [campaignQuery, setCampaignQuery] = useState<string>('php error disclosure')

  const [selectedLead, setSelectedLead] = useState<Lead | null>(null)
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('')
  const [activeDraft, setActiveDraft] = useState<OutreachDraft | null>(null)

  const [suppressTarget, setSuppressTarget] = useState<string>('')
  const [suppressReason, setSuppressReason] = useState<string>('manual_admin_suppression')

  useEffect(() => {
    loadAll()
  }, [statusFilter, riskFilter])

  const loadAll = async () => {
    try {
      setLoading(true)
      const [sData, lData, cData, tData, supData] = await Promise.all([
        getClientFinderStats(),
        listLeads({
          status: statusFilter || undefined,
          php2shell_risk: riskFilter || undefined,
          search: searchTerm || undefined,
        }),
        listCampaigns(),
        listOutreachTemplates(),
        listSuppressionList(),
      ])
      setStats(sData)
      setLeads(lData)
      setCampaigns(cData)
      setTemplates(tData)
      setSuppressionList(supData)
      if (tData.length > 0) setSelectedTemplateId(tData[0].id)
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Failed to load Client Finder data.')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateLead = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setActionLoading(true)
      setError(null)
      await createLead({
        company_name: newCompanyName,
        domain: newDomain,
        website_url: `https://${newDomain.replace(/^https?:\/\//, '')}`,
        contact_name: newContactName || undefined,
        contact_email: newContactEmail || undefined,
        technology_stack: newTechStack,
        php2shell_risk_level: newRiskLevel,
      })
      setShowAddLeadModal(false)
      setNewCompanyName('')
      setNewDomain('')
      setNewContactEmail('')
      setNewContactName('')
      setSuccessMsg(`Lead '${newDomain}' added successfully!`)
      loadAll()
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Failed to create lead.')
    } finally {
      setActionLoading(false)
    }
  }

  const handleRunDiscovery = async (campaignId: string) => {
    try {
      setActionLoading(true)
      setError(null)
      const found = await runCampaignDiscovery(campaignId)
      setSuccessMsg(`Discovery completed: Ingested ${found.length} candidate leads.`)
      loadAll()
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Failed to execute discovery job.')
    } finally {
      setActionLoading(false)
    }
  }

  const handleCreateCampaign = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setActionLoading(true)
      setError(null)
      await createCampaign({
        name: campaignName,
        target_technology: campaignTech,
        search_query: campaignQuery,
      })
      setShowCampaignModal(false)
      setCampaignName('')
      setSuccessMsg('Discovery campaign initialized successfully!')
      loadAll()
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Failed to create campaign.')
    } finally {
      setActionLoading(false)
    }
  }

  const handleOpenDraftOutreach = async (lead: Lead) => {
    setSelectedLead(lead)
    try {
      setActionLoading(true)
      setError(null)
      const draft = await draftOutreach(lead.id, {
        template_id: selectedTemplateId || undefined,
      })
      setActiveDraft(draft)
      setShowOutreachModal(true)
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Failed to prepare outreach draft.')
    } finally {
      setActionLoading(false)
    }
  }

  const handleSendOutreach = async () => {
    if (!activeDraft) return
    try {
      setActionLoading(true)
      setError(null)
      await sendOutreach(activeDraft.id)
      setShowOutreachModal(false)
      setActiveDraft(null)
      setSuccessMsg(`Outreach delivered to ${activeDraft.recipient_email}!`)
      loadAll()
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Failed to dispatch outreach.')
    } finally {
      setActionLoading(false)
    }
  }

  const handleConvertLead = async (leadId: string) => {
    try {
      setActionLoading(true)
      setError(null)
      const res = await convertLead(leadId)
      setSuccessMsg(`Lead '${res.domain}' converted to active website target assessment!`)
      loadAll()
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Failed to convert lead.')
    } finally {
      setActionLoading(false)
    }
  }

  const handleQualifyLead = async (leadId: string) => {
    try {
      await updateLead(leadId, { status: 'qualified', qualification_score: 90 })
      setSuccessMsg('Lead marked as qualified.')
      loadAll()
    } catch (err: any) {
      setError('Failed to update lead status.')
    }
  }

  const handleAddSuppression = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setActionLoading(true)
      setError(null)
      await addSuppression(suppressTarget, suppressReason)
      setShowSuppressionModal(false)
      setSuppressTarget('')
      setSuccessMsg(`Target '${suppressTarget}' added to suppression list.`)
      loadAll()
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Failed to add to suppression list.')
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
              Client Finder Automation & Lead Management
            </h1>
            <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800 dark:bg-purple-950/60 dark:text-purple-400 border border-purple-300 dark:border-purple-800">
              Admin Exclusive
            </span>
          </div>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Discover prospective business clients, benchmark PHP2Shell vulnerabilities, prepare compliant outreach, and convert prospects to verified assessments.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowAddLeadModal(true)}
            className="px-4 py-2 text-sm font-semibold rounded-lg bg-cyan-600 text-white hover:bg-cyan-700 transition"
          >
            + Add Lead
          </button>
          <button
            onClick={loadAll}
            disabled={loading}
            className="px-3.5 py-2 text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            {loading ? 'Refreshing...' : '↻ Refresh'}
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

      {/* Overview Metrics Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="p-4 rounded-xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm">
          <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">Total Leads</p>
          <p className="mt-1 text-2xl font-extrabold text-gray-900 dark:text-white">
            {stats ? stats.total_leads : '—'}
          </p>
          <p className="text-[11px] text-cyan-600 dark:text-cyan-400 font-medium">Pipeline Base</p>
        </div>

        <div className="p-4 rounded-xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm">
          <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">Awaiting Review</p>
          <p className="mt-1 text-2xl font-extrabold text-amber-600 dark:text-amber-400">
            {stats ? stats.new_leads : '—'}
          </p>
          <p className="text-[11px] text-gray-400">Status: New</p>
        </div>

        <div className="p-4 rounded-xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm">
          <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">Qualified Leads</p>
          <p className="mt-1 text-2xl font-extrabold text-cyan-600 dark:text-cyan-400">
            {stats ? stats.qualified_leads : '—'}
          </p>
          <p className="text-[11px] text-gray-400">Score &ge; 70</p>
        </div>

        <div className="p-4 rounded-xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm">
          <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">Contacted Leads</p>
          <p className="mt-1 text-2xl font-extrabold text-purple-600 dark:text-purple-400">
            {stats ? stats.contacted_leads : '—'}
          </p>
          <p className="text-[11px] text-gray-400">Outreach Sent</p>
        </div>

        <div className="p-4 rounded-xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm">
          <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">Converted</p>
          <p className="mt-1 text-2xl font-extrabold text-emerald-600 dark:text-emerald-400">
            {stats ? stats.converted_clients : '—'}
          </p>
          <p className="text-[11px] text-emerald-600 font-medium">Active Clients</p>
        </div>

        <div className="p-4 rounded-xl bg-purple-50 dark:bg-purple-950/40 border border-purple-200 dark:border-purple-800 shadow-sm">
          <p className="text-xs text-purple-800 dark:text-purple-300 font-medium">PHP2Shell Risk</p>
          <p className="mt-1 text-2xl font-extrabold text-purple-900 dark:text-purple-200">
            {stats ? stats.php2shell_high_risk_leads : '—'}
          </p>
          <p className="text-[11px] text-purple-700 dark:text-purple-400 font-bold">CVE-2026-109618</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-800">
        <nav className="flex space-x-8 text-sm font-medium">
          <button
            onClick={() => setActiveTab('leads')}
            className={`pb-3 border-b-2 transition ${
              activeTab === 'leads'
                ? 'border-cyan-500 text-cyan-600 dark:text-cyan-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
            }`}
          >
            Leads Pipeline ({leads.length})
          </button>
          <button
            onClick={() => setActiveTab('campaigns')}
            className={`pb-3 border-b-2 transition ${
              activeTab === 'campaigns'
                ? 'border-cyan-500 text-cyan-600 dark:text-cyan-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
            }`}
          >
            Discovery Campaigns ({campaigns.length})
          </button>
          <button
            onClick={() => setActiveTab('outreach')}
            className={`pb-3 border-b-2 transition ${
              activeTab === 'outreach'
                ? 'border-cyan-500 text-cyan-600 dark:text-cyan-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
            }`}
          >
            Compliant Outreach & Templates ({templates.length})
          </button>
          <button
            onClick={() => setActiveTab('suppression')}
            className={`pb-3 border-b-2 transition ${
              activeTab === 'suppression'
                ? 'border-cyan-500 text-cyan-600 dark:text-cyan-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
            }`}
          >
            Suppression List ({suppressionList.length})
          </button>
        </nav>
      </div>

      {/* Tab 1: Leads Pipeline */}
      {activeTab === 'leads' && (
        <div className="space-y-4">
          {/* Filters Bar */}
          <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800">
            <div className="flex flex-wrap items-center gap-3">
              <input
                type="text"
                placeholder="Search domain, company, contact..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && loadAll()}
                className="text-xs rounded-lg border border-gray-300 dark:border-gray-700 px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-white w-64"
              />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="text-xs rounded-lg border border-gray-300 dark:border-gray-700 px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              >
                <option value="">All Statuses</option>
                <option value="new">New</option>
                <option value="qualified">Qualified</option>
                <option value="contacted">Contacted</option>
                <option value="interested">Interested</option>
                <option value="converted">Converted</option>
              </select>
              <select
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value)}
                className="text-xs rounded-lg border border-gray-300 dark:border-gray-700 px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              >
                <option value="">All Risk Levels</option>
                <option value="critical">Critical Risk</option>
                <option value="high">High Risk</option>
                <option value="moderate">Moderate Risk</option>
              </select>
            </div>
            <button
              onClick={loadAll}
              className="text-xs px-3 py-2 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 font-semibold"
            >
              Filter
            </button>
          </div>

          {/* Table */}
          <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden shadow-sm">
            {leads.length === 0 ? (
              <div className="p-8 text-center text-sm text-gray-500">
                No prospective leads found matching criteria. Run a discovery campaign or add manual leads.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-gray-50 dark:bg-gray-800/60 text-gray-700 dark:text-gray-300 font-semibold border-b border-gray-200 dark:border-gray-800">
                    <tr>
                      <th className="py-3 px-4">Company & Domain</th>
                      <th className="py-3 px-4">Contact</th>
                      <th className="py-3 px-4">Technology Stack</th>
                      <th className="py-3 px-4">PHP2Shell Risk</th>
                      <th className="py-3 px-4">Score</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
                    {leads.map((l) => (
                      <tr key={l.id} className="hover:bg-gray-50/50 dark:hover:bg-gray-800/40">
                        <td className="py-3 px-4">
                          <div className="font-bold text-gray-900 dark:text-white">{l.company_name}</div>
                          <a
                            href={l.website_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-mono text-cyan-600 dark:text-cyan-400 hover:underline"
                          >
                            {l.domain}
                          </a>
                        </td>
                        <td className="py-3 px-4">
                          <div className="text-gray-900 dark:text-white font-medium">
                            {l.contact_name || 'Security Team'}
                          </div>
                          <div className="text-gray-400 font-mono text-[11px]">{l.contact_email || '—'}</div>
                        </td>
                        <td className="py-3 px-4 text-gray-600 dark:text-gray-300">
                          {l.technology_stack || 'Web Application'}
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                              l.php2shell_risk_level === 'critical'
                                ? 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-400'
                                : l.php2shell_risk_level === 'high'
                                ? 'bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-400'
                                : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
                            }`}
                          >
                            {l.php2shell_risk_level}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-mono font-bold text-gray-900 dark:text-white">
                          {l.qualification_score}/100
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${
                              l.status === 'converted'
                                ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-400'
                                : l.status === 'contacted'
                                ? 'bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-400'
                                : l.status === 'qualified'
                                ? 'bg-cyan-100 text-cyan-800 dark:bg-cyan-950 dark:text-cyan-400'
                                : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
                            }`}
                          >
                            {l.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right space-x-2">
                          {l.status === 'new' && (
                            <button
                              onClick={() => handleQualifyLead(l.id)}
                              className="text-xs font-semibold text-cyan-600 hover:text-cyan-700"
                            >
                              Qualify
                            </button>
                          )}
                          {l.status !== 'converted' && (
                            <button
                              onClick={() => handleOpenDraftOutreach(l)}
                              className="text-xs font-semibold text-purple-600 hover:text-purple-700"
                            >
                              Outreach
                            </button>
                          )}
                          {l.status !== 'converted' ? (
                            <button
                              onClick={() => handleConvertLead(l.id)}
                              className="text-xs font-semibold text-emerald-600 hover:text-emerald-700"
                            >
                              Convert
                            </button>
                          ) : (
                            <span className="text-[11px] text-emerald-600 font-bold">✓ Converted</span>
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
      )}

      {/* Tab 2: Discovery Campaigns */}
      {activeTab === 'campaigns' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-base font-semibold text-gray-900 dark:text-white">Active Campaigns</h3>
            <button
              onClick={() => setShowCampaignModal(true)}
              className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-cyan-600 text-white hover:bg-cyan-700"
            >
              + Create Campaign
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {campaigns.map((c) => (
              <div
                key={c.id}
                className="p-5 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 space-y-3"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="text-sm font-bold text-gray-900 dark:text-white">{c.name}</h4>
                    <p className="text-xs font-mono text-cyan-600 dark:text-cyan-400 mt-0.5">
                      Target: {c.target_technology}
                    </p>
                  </div>
                  <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-400 uppercase">
                    {c.status}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 pt-2 border-t border-gray-100 dark:border-gray-800 text-center font-mono text-xs">
                  <div>
                    <div className="text-gray-400 text-[10px]">Discovered</div>
                    <div className="font-bold text-gray-900 dark:text-white">{c.discovered_leads_count}</div>
                  </div>
                  <div>
                    <div className="text-gray-400 text-[10px]">Contacted</div>
                    <div className="font-bold text-gray-900 dark:text-white">{c.contacted_leads_count}</div>
                  </div>
                  <div>
                    <div className="text-gray-400 text-[10px]">Converted</div>
                    <div className="font-bold text-emerald-600">{c.converted_leads_count}</div>
                  </div>
                </div>

                <div className="pt-2">
                  <button
                    onClick={() => handleRunDiscovery(c.id)}
                    disabled={actionLoading}
                    className="w-full py-2 text-xs font-semibold rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-cyan-50 dark:hover:bg-cyan-950/40 text-cyan-600 dark:text-cyan-400 border border-gray-200 dark:border-gray-700 transition"
                  >
                    ⚡ Run Automated Discovery Job
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 3: Outreach Templates & Compliance */}
      {activeTab === 'outreach' && (
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 space-y-2">
            <h3 className="text-sm font-bold text-gray-900 dark:text-white">
              🛡️ CAN-SPAM & GDPR Regulatory Outreach Policy
            </h3>
            <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
              PATCHORA strictly enforces ethical, compliant disclosure. All outreach messages automatically incorporate:
              (1) Clear sender identity and physical business address, (2) Legitimate security assessment justification,
              (3) A cryptographic one-click unsubscribe token that instantly suppresses the recipient domain from all future communications.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {templates.map((tpl) => (
              <div
                key={tpl.id}
                className="p-5 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 space-y-3"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-gray-900 dark:text-white">{tpl.name}</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 uppercase">
                    {tpl.category}
                  </span>
                </div>
                <div className="text-xs text-cyan-600 dark:text-cyan-400 font-mono font-medium truncate">
                  Subject: {tpl.subject_template}
                </div>
                <div className="p-3 rounded bg-gray-950 text-gray-300 font-mono text-[11px] max-h-40 overflow-y-auto whitespace-pre-wrap">
                  {tpl.body_template}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 4: Suppression List */}
      {activeTab === 'suppression' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-gray-900 dark:text-white">
              Suppressed Domains & Emails ({suppressionList.length})
            </h3>
            <button
              onClick={() => setShowSuppressionModal(true)}
              className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-red-600 text-white hover:bg-red-700"
            >
              + Add to Suppression List
            </button>
          </div>

          <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
            {suppressionList.length === 0 ? (
              <div className="p-8 text-center text-sm text-gray-500">
                No suppression entries. Unsubscribe requests will automatically appear here.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 font-semibold border-b border-gray-200 dark:border-gray-800">
                    <tr>
                      <th className="py-3 px-4">Domain or Email</th>
                      <th className="py-3 px-4">Type</th>
                      <th className="py-3 px-4">Reason</th>
                      <th className="py-3 px-4">Opted Out Date</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
                    {suppressionList.map((sup) => (
                      <tr key={sup.id}>
                        <td className="py-3 px-4 font-mono font-bold text-gray-900 dark:text-white">
                          {sup.domain_or_email}
                        </td>
                        <td className="py-3 px-4 uppercase text-[10px] font-semibold text-gray-500">
                          {sup.entry_type}
                        </td>
                        <td className="py-3 px-4 text-gray-600 dark:text-gray-400">{sup.reason}</td>
                        <td className="py-3 px-4 text-gray-500">
                          {new Date(sup.opted_out_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Add Lead Modal */}
      {showAddLeadModal && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-3 sm:p-4 overflow-y-auto">
          <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-md w-full p-4 sm:p-6 border border-gray-200 dark:border-gray-800 space-y-4 max-h-[90vh] overflow-y-auto my-auto">
            <h3 className="text-base font-bold text-gray-900 dark:text-white">Manually Add Prospective Lead</h3>
            <form onSubmit={handleCreateLead} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">Company Name</label>
                <input
                  type="text"
                  value={newCompanyName}
                  onChange={(e) => setNewCompanyName(e.target.value)}
                  placeholder="Apex Logistics Inc."
                  required
                  className="mt-1 w-full text-xs rounded-lg border border-gray-300 dark:border-gray-700 p-2.5 bg-white dark:bg-gray-800 text-gray-900 dark:text-white min-h-[40px]"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">Target Domain</label>
                <input
                  type="text"
                  value={newDomain}
                  onChange={(e) => setNewDomain(e.target.value)}
                  placeholder="apex-logistics.com"
                  required
                  className="mt-1 w-full text-xs rounded-lg border border-gray-300 dark:border-gray-700 p-2.5 bg-white dark:bg-gray-800 text-gray-900 dark:text-white font-mono min-h-[40px]"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">Contact Name</label>
                  <input
                    type="text"
                    value={newContactName}
                    onChange={(e) => setNewContactName(e.target.value)}
                    placeholder="David Martinez"
                    className="mt-1 w-full text-xs rounded-lg border border-gray-300 dark:border-gray-700 p-2.5 bg-white dark:bg-gray-800 text-gray-900 dark:text-white min-h-[40px]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">Contact Email</label>
                  <input
                    type="email"
                    value={newContactEmail}
                    onChange={(e) => setNewContactEmail(e.target.value)}
                    placeholder="security@apex.com"
                    className="mt-1 w-full text-xs rounded-lg border border-gray-300 dark:border-gray-700 p-2.5 bg-white dark:bg-gray-800 text-gray-900 dark:text-white font-mono min-h-[40px]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">Tech Stack</label>
                  <input
                    type="text"
                    value={newTechStack}
                    onChange={(e) => setNewTechStack(e.target.value)}
                    className="mt-1 w-full text-xs rounded-lg border border-gray-300 dark:border-gray-700 p-2.5 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">PHP2Shell Risk</label>
                  <select
                    value={newRiskLevel}
                    onChange={(e) => setNewRiskLevel(e.target.value)}
                    className="mt-1 w-full text-xs rounded-lg border border-gray-300 dark:border-gray-700 p-2.5 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                  >
                    <option value="critical">Critical Risk</option>
                    <option value="high">High Risk</option>
                    <option value="moderate">Moderate Risk</option>
                    <option value="low">Low Risk</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-gray-200 dark:border-gray-800">
                <button
                  type="button"
                  onClick={() => setShowAddLeadModal(false)}
                  className="px-3 py-1.5 text-xs text-gray-600 dark:text-gray-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-cyan-600 text-white hover:bg-cyan-700"
                >
                  Save Lead
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Outreach Draft & Send Modal */}
      {showOutreachModal && activeDraft && selectedLead && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-3 sm:p-4 overflow-y-auto">
          <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-2xl w-full p-4 sm:p-6 border border-gray-200 dark:border-gray-800 space-y-4 max-h-[90vh] overflow-y-auto my-auto">
            <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-gray-900 dark:text-white">
                  Review Compliant Outreach Draft
                </h3>
                <p className="text-xs text-gray-400">
                  Recipient: {activeDraft.recipient_email} ({selectedLead.company_name})
                </p>
              </div>
              <button
                onClick={() => setShowOutreachModal(false)}
                className="text-gray-400 font-bold min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg"
                aria-label="Close outreach modal"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-gray-700 dark:text-gray-300">Subject</label>
                <div className="text-xs font-mono font-bold text-gray-900 dark:text-white p-2 rounded bg-gray-100 dark:bg-gray-800">
                  {activeDraft.subject}
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-gray-700 dark:text-gray-300">Message Body</label>
                <pre className="p-4 rounded-xl bg-gray-950 text-gray-200 font-mono text-xs overflow-y-auto whitespace-pre-wrap max-h-72 border border-gray-800 leading-relaxed">
                  {activeDraft.body}
                </pre>
              </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-gray-200 dark:border-gray-800">
              <span className="text-[11px] text-gray-400 font-mono">
                Provider: Sandbox Safe Dispatcher
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setShowOutreachModal(false)}
                  className="px-3 py-1.5 text-xs text-gray-600 dark:text-gray-400"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSendOutreach}
                  disabled={actionLoading}
                  className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-purple-600 text-white hover:bg-purple-700"
                >
                  Approve & Dispatch Outreach
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Manual Suppression Modal */}
      {showSuppressionModal && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-3 sm:p-4 overflow-y-auto">
          <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-md w-full p-4 sm:p-6 border border-gray-200 dark:border-gray-800 space-y-4 max-h-[90vh] overflow-y-auto my-auto">
            <h3 className="text-base font-bold text-gray-900 dark:text-white">Add to Suppression List</h3>
            <form onSubmit={handleAddSuppression} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">
                  Domain or Email
                </label>
                <input
                  type="text"
                  value={suppressTarget}
                  onChange={(e) => setSuppressTarget(e.target.value)}
                  placeholder="target-domain.com or user@domain.com"
                  required
                  className="mt-1 w-full text-xs rounded-lg border border-gray-300 dark:border-gray-700 p-2.5 bg-white dark:bg-gray-800 text-gray-900 dark:text-white font-mono min-h-[40px]"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">Reason</label>
                <input
                  type="text"
                  value={suppressReason}
                  onChange={(e) => setSuppressReason(e.target.value)}
                  placeholder="Explicit do-not-contact request"
                  required
                  className="mt-1 w-full text-xs rounded-lg border border-gray-300 dark:border-gray-700 p-2.5 bg-white dark:bg-gray-800 text-gray-900 dark:text-white min-h-[40px]"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowSuppressionModal(false)}
                  className="px-3.5 py-2 text-xs text-gray-600 dark:text-gray-400 min-h-[40px]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-2 text-xs font-semibold rounded-lg bg-red-600 text-white hover:bg-red-700 min-h-[40px]"
                >
                  Add to Suppression
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Campaign Modal */}
      {showCampaignModal && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-3 sm:p-4 overflow-y-auto">
          <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-md w-full p-4 sm:p-6 border border-gray-200 dark:border-gray-800 space-y-4 max-h-[90vh] overflow-y-auto my-auto">
            <h3 className="text-base font-bold text-gray-900 dark:text-white">Create Discovery Campaign</h3>
            <form onSubmit={handleCreateCampaign} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">
                  Campaign Title
                </label>
                <input
                  type="text"
                  value={campaignName}
                  onChange={(e) => setCampaignName(e.target.value)}
                  placeholder="PHP2Shell Remediation Awareness"
                  required
                  className="mt-1 w-full text-xs rounded-lg border border-gray-300 dark:border-gray-700 p-2.5 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">
                  Target Technology
                </label>
                <input
                  type="text"
                  value={campaignTech}
                  onChange={(e) => setCampaignTech(e.target.value)}
                  placeholder="PHP / Laravel / WordPress"
                  required
                  className="mt-1 w-full text-xs rounded-lg border border-gray-300 dark:border-gray-700 p-2.5 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">
                  Search Query
                </label>
                <input
                  type="text"
                  value={campaignQuery}
                  onChange={(e) => setCampaignQuery(e.target.value)}
                  placeholder="php error disclosure custom handler"
                  required
                  className="mt-1 w-full text-xs rounded-lg border border-gray-300 dark:border-gray-700 p-2.5 bg-white dark:bg-gray-800 text-gray-900 dark:text-white font-mono"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCampaignModal(false)}
                  className="px-3 py-1.5 text-xs text-gray-600 dark:text-gray-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-cyan-600 text-white hover:bg-cyan-700"
                >
                  Save Campaign
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
export default AdminClientFinderPage
