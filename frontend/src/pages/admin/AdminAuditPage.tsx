import React, { useEffect, useState } from 'react'
import { FileText, ShieldAlert, Clock, User as UserIcon } from 'lucide-react'
import { AdminAuditResponse, fetchAdminAuditLogs } from '@/api/dashboard'
import clsx from 'clsx'

export function AdminAuditPage() {
  const [data, setData] = useState<AdminAuditResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAdminAuditLogs()
      .then(res => setData(res))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="space-y-6">
      <div className="border-b border-slate-200 dark:border-dark-700 pb-6">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
          Platform Security Audit Log
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Chronological record of authentication, shield engagement, and account lifecycle events
        </p>
      </div>

      <div className="card overflow-hidden">
        {loading ? (
          <div className="py-12 text-center text-slate-400">Loading audit history...</div>
        ) : !data || data.events.length === 0 ? (
          <div className="py-12 text-center text-slate-400">No audit events recorded yet.</div>
        ) : (
          <div className="divide-y divide-slate-100 dark:divide-dark-700">
            {data.events.map(ev => (
              <div key={ev.id} className="p-3.5 sm:p-4 flex flex-col sm:flex-row sm:items-start justify-between gap-2 sm:gap-4 text-xs">
                <div className="space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={clsx(
                        'px-2 py-0.5 rounded font-mono font-semibold text-[10px]',
                        ev.severity === 'critical'
                          ? 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300'
                          : 'bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300'
                      )}
                    >
                      {ev.event_type}
                    </span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">
                      Actor: {ev.actor}
                    </span>
                  </div>
                  <p className="text-slate-600 dark:text-slate-400">
                    {ev.description}
                  </p>
                </div>
                <div className="flex items-center gap-1.5 text-slate-400 font-mono text-[11px] whitespace-nowrap self-start sm:self-auto">
                  <Clock className="w-3.5 h-3.5 flex-shrink-0" />
                  {new Date(ev.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
