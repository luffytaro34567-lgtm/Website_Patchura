import React, { useEffect, useState } from 'react'
import {
  CreditCard,
  CheckCircle2,
  XCircle,
  Clock,
  Download,
  ShieldCheck,
  Zap,
  RefreshCw,
  Sparkles,
  ArrowRight,
  AlertCircle,
  FileText,
} from 'lucide-react'
import {
  cancelSubscription,
  createCheckoutSession,
  downloadInvoiceHtml,
  getMySubscription,
  listMyInvoices,
  listPlans,
  simulateCheckoutCompletion,
} from '@/api/billing'
import { BillingInterval, CheckoutSession, Invoice, PlanTier, PlanTierInfo, Subscription } from '@/types/billing'
import { useAuth } from '@/context/AuthContext'
import clsx from 'clsx'

export function ClientBillingPage() {
  const { user, isAdmin } = useAuth()
  const [subscription, setSubscription] = useState<Subscription | null>(null)
  const [plans, setPlans] = useState<PlanTierInfo[]>([])
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Billing interval toggle
  const [billingInterval, setBillingInterval] = useState<BillingInterval>('month')

  // Checkout modal
  const [activeSession, setActiveSession] = useState<CheckoutSession | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [checkoutOutcome, setCheckoutOutcome] = useState<'succeeded' | 'failed'>('succeeded')
  const [checkoutError, setCheckoutError] = useState<string | null>(null)
  const [isCancelling, setIsCancelling] = useState(false)

  const loadData = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const [sub, planList, invList] = await Promise.all([
        getMySubscription(),
        listPlans(),
        listMyInvoices(),
      ])
      setSubscription(sub)
      setPlans(planList)
      setInvoices(invList)
    } catch (err: any) {
      setError(err?.userMessage || 'Failed to load billing details.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleStartCheckout = async (planTier: PlanTier) => {
    try {
      setCheckoutError(null)
      setIsProcessing(true)
      const session = await createCheckoutSession(planTier, billingInterval)
      setActiveSession(session)
    } catch (err: any) {
      alert(err?.userMessage || 'Failed to start checkout session.')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleCompleteCheckout = async () => {
    if (!activeSession) return
    try {
      setIsProcessing(true)
      setCheckoutError(null)
      const updatedSub = await simulateCheckoutCompletion(activeSession.session_id, checkoutOutcome)
      setSubscription(updatedSub)
      setActiveSession(null)
      await loadData()
    } catch (err: any) {
      setCheckoutError(err?.userMessage || 'Payment authorization declined.')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleCancelSubscription = async () => {
    if (!confirm('Are you sure you want to cancel your plan renewal?')) return
    try {
      setIsCancelling(true)
      const updated = await cancelSubscription()
      setSubscription(updated)
    } catch (err: any) {
      alert(err?.userMessage || 'Failed to cancel subscription.')
    } finally {
      setIsCancelling(false)
    }
  }

  const handleDownloadInvoice = async (invoice: Invoice) => {
    try {
      await downloadInvoiceHtml(invoice.id, invoice.invoice_number)
    } catch (err: any) {
      alert(err?.userMessage || 'Failed to download invoice.')
    }
  }

  if (isLoading) {
    return <div className="card p-12 text-center text-slate-400">Loading subscription and billing data...</div>
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="border-b border-slate-200 dark:border-dark-700 pb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <CreditCard className="w-6 h-6 text-primary-500" />
            Subscription & Billing
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Manage your SaaS plan tier, target domain quotas, scan allowances, and billing history
          </p>
        </div>

        <button
          onClick={loadData}
          className="btn btn-secondary flex items-center gap-2 text-sm self-start sm:self-auto"
        >
          <RefreshCw className={clsx('w-4 h-4', isLoading && 'animate-spin')} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-400 text-sm">
          {error}
        </div>
      )}

      {isAdmin && (
        <div className="card p-4 bg-purple-50/70 dark:bg-purple-950/30 border-purple-200 dark:border-purple-800 flex items-start sm:items-center gap-3">
          <ShieldCheck className="w-5 h-5 text-purple-600 dark:text-purple-400 flex-shrink-0 mt-0.5 sm:mt-0" />
          <div className="text-sm">
            <span className="font-semibold text-purple-900 dark:text-purple-200">Administrator Exemption: </span>
            <span className="text-purple-800 dark:text-purple-300">
              Your account has full administrative privileges and unrestricted platform access. No active paid subscription, renewal, or payment history is required.
            </span>
          </div>
        </div>
      )}

      {/* Current Active Plan Overview Card */}
      {subscription && (
        <div className="card p-6 space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-dark-700 pb-6">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-primary-100 text-primary-800 dark:bg-primary-950 dark:text-primary-300">
                  {subscription.plan_tier} Plan
                </span>
                <span
                  className={clsx(
                    'px-2 py-0.5 rounded text-xs font-medium capitalize',
                    subscription.status === 'active' && 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                  )}
                >
                  {subscription.status}
                </span>
              </div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white capitalize">
                PATCHORA {subscription.plan_tier} Edition
              </h2>
              <p className="text-xs text-slate-400 font-mono">
                {subscription.price_cents > 0
                  ? `$${(subscription.price_cents / 100).toFixed(2)} USD / ${subscription.billing_interval}`
                  : 'Free community plan'}
              </p>
            </div>

            {subscription.plan_tier !== 'free' && (
              <div className="flex items-center gap-3">
                {subscription.cancel_at_period_end ? (
                  <span className="text-xs text-amber-500 font-semibold">
                    Cancels at period end ({subscription.current_period_end ? new Date(subscription.current_period_end).toLocaleDateString() : 'N/A'})
                  </span>
                ) : (
                  <button
                    onClick={handleCancelSubscription}
                    disabled={isCancelling}
                    className="btn btn-secondary text-xs text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40"
                  >
                    {isCancelling ? 'Cancelling...' : 'Cancel Renewal'}
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Quota Meters */}
          <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-4">
            {/* Target Websites Meter */}
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-dark-750 border border-slate-200 dark:border-dark-700 space-y-2">
              <div className="flex justify-between text-xs text-slate-500">
                <span className="font-semibold text-slate-700 dark:text-slate-300">Registered Targets</span>
                <span className="font-mono">
                  {subscription.current_target_count} / {subscription.max_target_websites >= 999999 ? 'Unlimited' : subscription.max_target_websites}
                </span>
              </div>
              <div className="w-full bg-slate-200 dark:bg-dark-700 h-2 rounded-full overflow-hidden">
                <div
                  className={clsx(
                    'h-full transition-all duration-500',
                    subscription.current_target_count >= subscription.max_target_websites ? 'bg-amber-500' : 'bg-primary-500'
                  )}
                  style={{
                    width: `${Math.min(
                      (subscription.current_target_count / (subscription.max_target_websites || 1)) * 100,
                      100
                    )}%`,
                  }}
                />
              </div>
              <p className="text-[11px] text-slate-400">
                {subscription.max_target_websites - subscription.current_target_count > 0
                  ? `${subscription.max_target_websites - subscription.current_target_count} slots remaining`
                  : 'Target limit reached. Upgrade to add domains.'}
              </p>
            </div>

            {/* Monthly Scans Meter */}
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-dark-750 border border-slate-200 dark:border-dark-700 space-y-2">
              <div className="flex justify-between text-xs text-slate-500">
                <span className="font-semibold text-slate-700 dark:text-slate-300">Monthly Scans Used</span>
                <span className="font-mono">
                  {subscription.scans_used_this_month} / {subscription.monthly_scan_limit >= 999999 ? 'Unlimited' : subscription.monthly_scan_limit}
                </span>
              </div>
              <div className="w-full bg-slate-200 dark:bg-dark-700 h-2 rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary-500 transition-all duration-500"
                  style={{
                    width: `${Math.min(
                      (subscription.scans_used_this_month / (subscription.monthly_scan_limit || 1)) * 100,
                      100
                    )}%`,
                  }}
                />
              </div>
              <p className="text-[11px] text-slate-400">
                {subscription.monthly_scan_limit >= 999999 ? 'Unlimited scans included' : 'Resets at start of each month'}
              </p>
            </div>

            {/* Included Detailed Reports */}
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-dark-750 border border-slate-200 dark:border-dark-700 space-y-2 sm:col-span-2 md:col-span-1">
              <span className="font-semibold text-slate-700 dark:text-slate-300 text-xs block">
                Reports Allowance
              </span>
              <div className="text-xl font-bold font-mono text-slate-900 dark:text-white">
                {subscription.reports_included_per_month >= 999999
                  ? 'Unlimited'
                  : `${subscription.reports_included_per_month} / mo`}
              </div>
              <p className="text-[11px] text-slate-400">
                {subscription.reports_included_per_month === 0
                  ? 'Detailed reports available per scan ($49)'
                  : 'Included with Pro/Enterprise'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Plan Comparison Grid */}
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">Compare Plan Tiers</h2>
            <p className="text-xs text-slate-500">Transparent pricing. Upgrade or downgrade anytime.</p>
          </div>

          {/* Monthly / Annual Switcher */}
          <div className="flex items-center p-1 rounded-xl bg-slate-100 dark:bg-dark-750 border border-slate-200 dark:border-dark-700 self-start sm:self-auto text-xs font-semibold">
            <button
              onClick={() => setBillingInterval('month')}
              className={clsx(
                'px-3 py-1.5 rounded-lg transition-all',
                billingInterval === 'month' ? 'bg-white dark:bg-dark-800 text-slate-900 dark:text-white shadow-sm' : 'text-slate-500'
              )}
            >
              Monthly Billing
            </button>
            <button
              onClick={() => setBillingInterval('year')}
              className={clsx(
                'px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5',
                billingInterval === 'year' ? 'bg-white dark:bg-dark-800 text-slate-900 dark:text-white shadow-sm' : 'text-slate-500'
              )}
            >
              <span>Annual Billing</span>
              <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                2 Mo Free
              </span>
            </button>
          </div>
        </div>

        {/* Plan Cards */}
        <div className="grid md:grid-cols-3 gap-6">
          {plans.map(plan => {
            const isCurrent = subscription?.plan_tier === plan.tier
            const priceCents = billingInterval === 'year' ? plan.annual_price_cents : plan.monthly_price_cents
            const priceDollars = (priceCents / 100).toFixed(2)

            return (
              <div
                key={plan.tier}
                className={clsx(
                  'card p-6 flex flex-col justify-between space-y-6 border transition-all',
                  isCurrent
                    ? 'border-primary-500 ring-1 ring-primary-500 shadow-md'
                    : 'border-slate-200 dark:border-dark-700 hover:border-slate-300'
                )}
              >
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-bold text-slate-900 dark:text-white text-lg">{plan.name}</h3>
                      <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-100 dark:bg-dark-700 text-slate-700 dark:text-slate-300">
                        {plan.tag}
                      </span>
                    </div>
                    {isCurrent && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                        Current Plan
                      </span>
                    )}
                  </div>

                  <div className="pt-2">
                    <span className="text-3xl font-extrabold text-slate-900 dark:text-white">${priceDollars}</span>
                    <span className="text-xs text-slate-400 font-mono ml-1">
                      {plan.monthly_price_cents === 0 ? '' : `/${billingInterval}`}
                    </span>
                  </div>

                  <div className="space-y-2.5 pt-4 border-t border-slate-200 dark:border-dark-700 text-xs">
                    {plan.features.map(feat => (
                      <div key={feat} className="flex items-start gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                        <span className="text-slate-600 dark:text-slate-300">{feat}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="pt-4 border-t border-slate-200 dark:border-dark-700">
                  {isAdmin ? (
                    <button disabled className="btn btn-secondary w-full text-xs font-semibold text-purple-700 dark:text-purple-300 bg-purple-50 dark:bg-purple-950/40 border-purple-200 dark:border-purple-800 cursor-default">
                      Admin Access Granted
                    </button>
                  ) : isCurrent ? (
                    <button disabled className="btn btn-secondary w-full text-xs opacity-60">
                      Active Plan
                    </button>
                  ) : plan.tier === 'free' ? (
                    <button disabled className="btn btn-secondary w-full text-xs opacity-50">
                      Included by Default
                    </button>
                  ) : (
                    <button
                      onClick={() => handleStartCheckout(plan.tier)}
                      className="btn btn-primary w-full text-xs flex items-center justify-center gap-1.5"
                    >
                      <span>Upgrade to {plan.name}</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Invoices History Table */}
      <div className="card p-6 space-y-4">
        <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <FileText className="w-5 h-5 text-primary-500" />
          Billing Invoices & Receipts
        </h3>

        {invoices.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-400">
            No invoices generated yet. Invoices appear here automatically when subscriptions or detailed reports are purchased.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-dark-700/50 text-slate-600 dark:text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-200 dark:border-dark-700">
                <tr>
                  <th className="px-4 py-3">Invoice #</th>
                  <th className="px-4 py-3">Date</th>
                  <th className="px-4 py-3">Description</th>
                  <th className="px-4 py-3">Amount</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Receipt</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-dark-700">
                {invoices.map(inv => (
                  <tr key={inv.id} className="hover:bg-slate-50/50 dark:hover:bg-dark-750/50">
                    <td className="px-4 py-3 font-mono font-bold text-slate-900 dark:text-white">
                      {inv.invoice_number}
                    </td>
                    <td className="px-4 py-3 text-slate-500 font-mono">
                      {new Date(inv.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-slate-700 dark:text-slate-300 font-medium">
                      {inv.description}
                    </td>
                    <td className="px-4 py-3 font-mono font-bold text-slate-900 dark:text-white">
                      ${(inv.amount_cents / 100).toFixed(2)} {inv.currency}
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                        {inv.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => handleDownloadInvoice(inv)}
                        className="btn btn-secondary text-xs px-2.5 py-1 inline-flex items-center gap-1"
                      >
                        <Download className="w-3.5 h-3.5" />
                        Download
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Checkout Simulation Modal */}
      {activeSession && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4 overflow-y-auto">
          <div className="card w-full max-w-lg p-4 sm:p-6 space-y-4 sm:space-y-6 max-h-[90vh] overflow-y-auto my-auto">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-dark-700 pb-3">
              <div className="flex items-center gap-2">
                <CreditCard className="w-5 h-5 text-primary-500" />
                <h3 className="text-sm sm:text-base font-bold text-slate-900 dark:text-white">
                  Payment Checkout — {activeSession.plan_tier.toUpperCase()} Plan
                </h3>
              </div>
              <button
                onClick={() => setActiveSession(null)}
                className="text-slate-400 hover:text-slate-200 min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg"
                aria-label="Close checkout"
              >
                ✕
              </button>
            </div>

            {checkoutError && (
              <div className="p-3 rounded-lg bg-rose-50 text-rose-700 text-xs flex items-center gap-2">
                <XCircle className="w-4 h-4 flex-shrink-0" />
                <span>{checkoutError}</span>
              </div>
            )}

            <div className="p-4 rounded-lg bg-slate-50 dark:bg-dark-750 border border-slate-200 dark:border-dark-700 text-xs space-y-2">
              <div className="flex justify-between font-bold text-slate-900 dark:text-white text-sm">
                <span>PATCHORA {activeSession.plan_tier.toUpperCase()} Edition</span>
                <span>${(activeSession.amount_cents / 100).toFixed(2)} {activeSession.currency}</span>
              </div>
              <p className="text-slate-400">
                Session ID: <span className="font-mono break-all">{activeSession.session_id.slice(0, 16)}...</span>
              </p>
            </div>

            {/* Verification options */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Gateway Authorization Workflow
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setCheckoutOutcome('succeeded')}
                  className={clsx(
                    'p-3 rounded-lg border text-xs font-semibold transition-all min-h-[44px] flex items-center justify-center',
                    checkoutOutcome === 'succeeded'
                      ? 'border-emerald-500 bg-emerald-50 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                      : 'border-slate-200 dark:border-dark-700 text-slate-600'
                  )}
                >
                  ✓ Authorize Payment (Success)
                </button>
                <button
                  type="button"
                  onClick={() => setCheckoutOutcome('failed')}
                  className={clsx(
                    'p-3 rounded-lg border text-xs font-semibold transition-all min-h-[44px] flex items-center justify-center',
                    checkoutOutcome === 'failed'
                      ? 'border-rose-500 bg-rose-50 text-rose-800 dark:bg-rose-950 dark:text-rose-300'
                      : 'border-slate-200 dark:border-dark-700 text-slate-600'
                  )}
                >
                  ✕ Simulate Payment Failure
                </button>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-200 dark:border-dark-700">
              <button
                type="button"
                onClick={() => setActiveSession(null)}
                className="btn btn-secondary text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleCompleteCheckout}
                disabled={isProcessing}
                className="btn btn-primary text-xs flex items-center gap-1.5"
              >
                {isProcessing ? 'Processing Payment...' : 'Confirm Subscription'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
