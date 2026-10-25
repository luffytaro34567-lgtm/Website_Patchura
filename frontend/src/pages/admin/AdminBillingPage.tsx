import React, { useEffect, useState } from 'react'
import {
  CreditCard,
  DollarSign,
  TrendingUp,
  Users,
  ShieldCheck,
  Search,
  RefreshCw,
} from 'lucide-react'
import { adminGetBillingStats, adminListTransactions } from '@/api/billing'
import { AdminBillingStats, Transaction } from '@/types/billing'
import clsx from 'clsx'

export function AdminBillingPage() {
  const [stats, setStats] = useState<AdminBillingStats | null>(null)
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')

  const loadData = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const [s, txs] = await Promise.all([
        adminGetBillingStats(),
        adminListTransactions(),
      ])
      setStats(s)
      setTransactions(txs)
    } catch (err: any) {
      setError(err?.userMessage || 'Failed to load billing metrics.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const filteredTxs = transactions.filter(
    t =>
      t.id.toLowerCase().includes(search.toLowerCase()) ||
      t.user_id.toLowerCase().includes(search.toLowerCase()) ||
      (t.reference_id && t.reference_id.toLowerCase().includes(search.toLowerCase()))
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-slate-200 dark:border-dark-700 pb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <CreditCard className="w-6 h-6 text-primary-500" />
            Billing & Revenue Administration
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Track SaaS subscription metrics, platform transaction revenue, and customer financial activity
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
        <div className="p-4 rounded-lg bg-rose-50 text-rose-700 text-sm">
          {error}
        </div>
      )}

      {/* Revenue Metric Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="card p-5 space-y-1">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
              <span>Total Revenue</span>
              <DollarSign className="w-4 h-4 text-emerald-500" />
            </div>
            <div className="text-2xl font-extrabold font-mono text-slate-900 dark:text-white">
              ${(stats.total_revenue_cents / 100).toFixed(2)}
            </div>
            <div className="text-[11px] text-slate-400">Total settled payments</div>
          </div>

          <div className="card p-5 space-y-1">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
              <span>Active Subscriptions</span>
              <TrendingUp className="w-4 h-4 text-primary-500" />
            </div>
            <div className="text-2xl font-extrabold font-mono text-slate-900 dark:text-white">
              {stats.active_subscriptions_count}
            </div>
            <div className="text-[11px] text-slate-400">Paid customer accounts</div>
          </div>

          <div className="card p-5 space-y-1">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
              <span>Pro Plan Seats</span>
              <Users className="w-4 h-4 text-blue-500" />
            </div>
            <div className="text-2xl font-extrabold font-mono text-slate-900 dark:text-white">
              {stats.pro_subscriptions_count}
            </div>
            <div className="text-[11px] text-slate-400">$79/mo subscription seats</div>
          </div>

          <div className="card p-5 space-y-1">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
              <span>Enterprise Seats</span>
              <ShieldCheck className="w-4 h-4 text-purple-500" />
            </div>
            <div className="text-2xl font-extrabold font-mono text-slate-900 dark:text-white">
              {stats.enterprise_subscriptions_count}
            </div>
            <div className="text-[11px] text-slate-400">$299/mo subscription seats</div>
          </div>
        </div>
      )}

      {/* Transactions Search and Table */}
      <div className="card p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <h3 className="font-bold text-slate-900 dark:text-white text-base">
            Global Payment Transactions ({filteredTxs.length})
          </h3>
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search user ID or ref..."
              className="input pl-9 text-xs w-full"
            />
          </div>
        </div>

        {filteredTxs.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-400">No transactions recorded yet.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-dark-700/50 text-slate-600 dark:text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-200 dark:border-dark-700">
                <tr>
                  <th className="px-4 py-3">Transaction ID</th>
                  <th className="px-4 py-3">Client User</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Amount</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Provider</th>
                  <th className="px-4 py-3 text-right">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-dark-700">
                {filteredTxs.map(tx => (
                  <tr key={tx.id} className="hover:bg-slate-50/50 dark:hover:bg-dark-750/50">
                    <td className="px-4 py-3 font-mono text-slate-900 dark:text-white font-semibold">
                      {tx.id.slice(0, 10)}...
                    </td>
                    <td className="px-4 py-3 font-mono text-slate-500">
                      {tx.user_id.slice(0, 8)}...
                    </td>
                    <td className="px-4 py-3 capitalize text-slate-700 dark:text-slate-300">
                      {tx.payment_type}
                    </td>
                    <td className="px-4 py-3 font-mono font-bold text-slate-900 dark:text-white">
                      ${(tx.amount_cents / 100).toFixed(2)} {tx.currency}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={clsx(
                          'px-2 py-0.5 rounded text-[10px] font-bold uppercase',
                          tx.status === 'succeeded' && 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300',
                          tx.status === 'failed' && 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300',
                          tx.status === 'pending' && 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                        )}
                      >
                        {tx.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-slate-500">
                      {tx.provider}
                    </td>
                    <td className="px-4 py-3 text-right text-slate-500 font-mono">
                      {new Date(tx.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
