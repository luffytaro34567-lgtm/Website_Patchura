import React, { useEffect, useState } from 'react'
import { Server, Database, Cpu, CheckCircle2, AlertTriangle } from 'lucide-react'
import { AdminOverview, fetchAdminOverview } from '@/api/dashboard'
import clsx from 'clsx'

export function AdminServicesPage() {
  const [data, setData] = useState<AdminOverview | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAdminOverview()
      .then(res => setData(res))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="space-y-6">
      <div className="border-b border-slate-200 dark:border-dark-700 pb-6">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
          System Infrastructure & Services
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Active operational status of database engines, API nodes, and queue processors
        </p>
      </div>

      {loading ? (
        <div className="py-12 text-center text-slate-400">Loading infrastructure data...</div>
      ) : data ? (
        <div className="grid md:grid-cols-2 gap-6">
          {data.services.map(svc => (
            <div key={svc.name} className="card p-6 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
                  <Server className="w-5 h-5 text-purple-500" />
                  <h3>{svc.name}</h3>
                </div>
                <span
                  className={clsx(
                    'px-2 py-0.5 rounded text-xs font-mono font-medium',
                    svc.is_operational
                      ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                      : svc.status === 'planned'
                      ? 'bg-slate-100 text-slate-600 dark:bg-dark-700 dark:text-slate-400'
                      : 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300'
                  )}
                >
                  {svc.status.toUpperCase()}
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                {svc.details}
              </p>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  )
}
