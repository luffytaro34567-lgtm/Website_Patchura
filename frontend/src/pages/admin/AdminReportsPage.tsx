import React, { useEffect, useState } from 'react'
import {
  FileText,
  Search,
  CheckCircle2,
  XCircle,
  Clock,
  Unlock,
  RefreshCw,
  Plus,
} from 'lucide-react'
import { adminGrantEntitlement, adminListReportOrders } from '@/api/reports'
import { ReportOrder } from '@/types/report'
import clsx from 'clsx'

export function AdminReportsPage() {
  const [orders, setOrders] = useState<ReportOrder[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')

  // Manual grant modal
  const [isGrantOpen, setIsGrantOpen] = useState(false)
  const [grantScanId, setGrantScanId] = useState('')
  const [grantReason, setGrantReason] = useState('')
  const [isGranting, setIsGranting] = useState(false)
  const [grantMessage, setGrantMessage] = useState<string | null>(null)

  const loadOrders = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const data = await adminListReportOrders()
      setOrders(data)
    } catch (err: any) {
      setError(err?.userMessage || 'Failed to load report orders.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadOrders()
  }, [])

  const handleGrant = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!grantScanId.trim() || !grantReason.trim()) return

    try {
      setIsGranting(true)
      setGrantMessage(null)
      await adminGrantEntitlement(grantScanId.trim(), grantReason.trim())
      setGrantMessage('Entitlement granted successfully.')
      setGrantScanId('')
      setGrantReason('')
      setTimeout(() => {
        setIsGrantOpen(false)
        setGrantMessage(null)
        loadOrders()
      }, 1500)
    } catch (err: any) {
      setGrantMessage(err?.userMessage || 'Failed to grant entitlement.')
    } finally {
      setIsGranting(false)
    }
  }

  const filteredOrders = orders.filter(
    o =>
      o.transaction_reference.toLowerCase().includes(search.toLowerCase()) ||
      o.scan_id.toLowerCase().includes(search.toLowerCase()) ||
      o.user_id.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-slate-200 dark:border-dark-700 pb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <FileText className="w-6 h-6 text-primary-500" />
            Report Orders & Entitlement Administration
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Audit paid report purchase orders, inspect fulfillment states, and manage administrative entitlement grants
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadOrders}
            className="btn btn-secondary flex items-center gap-2 text-sm"
          >
            <RefreshCw className={clsx('w-4 h-4', isLoading && 'animate-spin')} />
            Refresh
          </button>
          <button
            onClick={() => {
              setGrantMessage(null)
              setIsGrantOpen(true)
            }}
            className="btn btn-primary flex items-center gap-2 text-sm"
          >
            <Plus className="w-4 h-4" />
            Manual Grant Entitlement
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-400 text-sm">
          {error}
        </div>
      )}

      {/* Filter and Search */}
      <div className="card p-4">
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search transaction ref, scan ID, or user ID..."
            className="input pl-9 text-sm w-full"
          />
        </div>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="card p-12 text-center text-slate-400">Loading report orders...</div>
      ) : filteredOrders.length === 0 ? (
        <div className="card p-12 text-center text-slate-400 space-y-2">
          <p>No report orders match your query.</p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 dark:bg-dark-700/50 text-slate-600 dark:text-slate-400 text-xs font-semibold uppercase tracking-wider border-b border-slate-200 dark:border-dark-700">
                <tr>
                  <th className="px-6 py-3.5">Reference</th>
                  <th className="px-6 py-3.5">Scan ID</th>
                  <th className="px-6 py-3.5">Client User</th>
                  <th className="px-6 py-3.5">Amount</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5">Payment Method</th>
                  <th className="px-6 py-3.5">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-dark-700">
                {filteredOrders.map(order => (
                  <tr key={order.id} className="hover:bg-slate-50/50 dark:hover:bg-dark-750/50 transition-colors">
                    <td className="px-6 py-4 font-mono font-bold text-xs text-slate-900 dark:text-white">
                      {order.transaction_reference}
                    </td>

                    <td className="px-6 py-4 text-xs font-mono text-slate-500">
                      {order.scan_id.slice(0, 10)}...
                    </td>

                    <td className="px-6 py-4 text-xs font-mono text-slate-500">
                      {order.user_id.slice(0, 8)}...
                    </td>

                    <td className="px-6 py-4 text-xs font-mono font-semibold text-slate-900 dark:text-white">
                      ${order.amount.toFixed(2)} {order.currency}
                    </td>

                    <td className="px-6 py-4">
                      <span
                        className={clsx(
                          'px-2 py-0.5 rounded text-xs font-medium capitalize',
                          order.status === 'completed' && 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300',
                          order.status === 'pending' && 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300',
                          order.status === 'failed' && 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300',
                          order.status === 'cancelled' && 'bg-slate-100 text-slate-800 dark:bg-dark-700 dark:text-slate-400'
                        )}
                      >
                        {order.status}
                      </span>
                    </td>

                    <td className="px-6 py-4 text-xs text-slate-500 font-mono">
                      {order.payment_method}
                    </td>

                    <td className="px-6 py-4 text-xs text-slate-500">
                      {new Date(order.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Manual Grant Modal */}
      {isGrantOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="card w-full max-w-md p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-dark-700 pb-3">
              <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Unlock className="w-4 h-4 text-primary-500" />
                Administrative Entitlement Grant
              </h2>
              <button onClick={() => setIsGrantOpen(false)} className="text-slate-400 hover:text-slate-200">
                ✕
              </button>
            </div>

            {grantMessage && (
              <div className="p-3 rounded-lg bg-emerald-50 text-emerald-800 text-xs">
                {grantMessage}
              </div>
            )}

            <form onSubmit={handleGrant} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Scan ID</label>
                <input
                  type="text"
                  value={grantScanId}
                  onChange={e => setGrantScanId(e.target.value)}
                  placeholder="Paste scan UUID..."
                  required
                  className="input text-xs w-full font-mono"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Audit Justification</label>
                <textarea
                  value={grantReason}
                  onChange={e => setGrantReason(e.target.value)}
                  placeholder="e.g. VIP onboarding, customer support override..."
                  required
                  className="input text-xs w-full h-20"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-200 dark:border-dark-700">
                <button
                  type="button"
                  onClick={() => setIsGrantOpen(false)}
                  className="btn btn-secondary text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isGranting}
                  className="btn btn-primary text-xs"
                >
                  {isGranting ? 'Granting...' : 'Confirm Grant'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
