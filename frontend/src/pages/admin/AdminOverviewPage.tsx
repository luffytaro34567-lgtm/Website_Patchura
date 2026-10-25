import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Users,
  Shield,
  Server,
  AlertOctagon,
  CheckCircle2,
  AlertTriangle,
  UserCheck,
  UserX,
  ArrowRight,
} from 'lucide-react'
import { AdminOverview, fetchAdminOverview } from '@/api/dashboard'
import clsx from 'clsx'

export function AdminOverviewPage() {
  const [data, setData] = useState<AdminOverview | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchAdminOverview()
      .then(res => setData(res))
      .catch(err => setError(err.userMessage || 'Failed to load admin metrics'))
      .finally(() => setIsLoading(false))
  }, [])

  if (isLoading) {
    return (
      <div className="py-20 flex flex-col items-center justify-center">
        <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mb-3" />
        <p className="text-sm text-slate-400">Loading platform metrics...</p>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="card p-6 border-rose-200 dark:border-rose-900 bg-rose-50 dark:bg-rose-950/20 text-rose-700 dark:text-rose-300">
        <div className="flex items-center gap-2 font-semibold">
          <AlertTriangle className="w-5 h-5 text-rose-500" />
          <span>Error loading administrative metrics</span>
        </div>
        <p className="text-sm mt-1">{error}</p>
      </div>
    )
  }

  const statCards = [
    {
      title: 'Total Registered Accounts',
      value: data.total_users,
      icon: Users,
      color: 'text-purple-600 bg-purple-50 dark:bg-purple-950/50',
    },
    {
      title: 'Client Accounts',
      value: data.total_clients,
      icon: UserCheck,
      color: 'text-primary-600 bg-primary-50 dark:bg-primary-950/50',
    },
    {
      title: 'Administrator Accounts',
      value: data.total_admins,
      icon: Shield,
      color: 'text-indigo-600 bg-indigo-50 dark:bg-indigo-950/50',
    },
    {
      title: 'Active Accounts',
      value: data.active_users,
      icon: CheckCircle2,
      color: 'text-emerald-600 bg-emerald-50 dark:bg-emerald-950/50',
    },
    {
      title: 'Suspended Accounts',
      value: data.disabled_users,
      icon: UserX,
      color: 'text-rose-600 bg-rose-50 dark:bg-rose-950/50',
    },
  ]

  return (
    <div className="space-y-8">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200 dark:border-dark-700">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Platform Overview & Operations
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Real-time multi-tenant account stats and active security posture
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link to="/admin/users" className="btn-primary text-xs bg-purple-600 hover:bg-purple-700">
            Manage Clients
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* Real Statistics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 sm:gap-4">
        {statCards.map(card => {
          const Icon = card.icon
          return (
            <div key={card.title} className="card p-4 sm:p-5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                  {card.title}
                </span>
                <div className={clsx('p-1.5 rounded-lg flex-shrink-0', card.color)}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <div className="text-xl sm:text-2xl font-bold font-mono text-slate-900 dark:text-white">
                {card.value}
              </div>
            </div>
          )
        })}
      </div>

      {/* Security Shield Banner */}
      <div className="card p-6 border-rose-200 dark:border-rose-900/50 bg-rose-50/50 dark:bg-rose-950/10">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2.5 rounded-lg bg-rose-100 dark:bg-rose-900/40 text-rose-600 dark:text-rose-400">
              <AlertOctagon className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-slate-900 dark:text-white text-base">
                  PHP2Shell Active Shield Engaged
                </h3>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-rose-600 text-white font-semibold uppercase">
                  CVSS 9.2 Critical
                </span>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 max-w-2xl leading-relaxed">
                Platform-wide detection and defensive re-entrancy locks active for CVE-2026-109618 & CVE-2026-109619.
                Protected PHP range: 5.4 through 8.5.
              </p>
            </div>
          </div>
          <Link
            to="/admin/security"
            className="btn-ghost text-xs self-start md:self-auto text-rose-600 dark:text-rose-400 hover:bg-rose-100 dark:hover:bg-rose-950/40"
          >
            Review Shield Rules →
          </Link>
        </div>
      </div>

      {/* Platform Infrastructure Status Table */}
      <div className="card p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 dark:border-dark-700 pb-3">
          <div className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
            <Server className="w-4 h-4 text-purple-500" />
            <h3>Platform Services & Integrations</h3>
          </div>
          <span className="text-xs font-mono text-slate-400">
            System Overall: {data.system_status.toUpperCase()}
          </span>
        </div>

        <div className="divide-y divide-slate-100 dark:divide-dark-700">
          {data.services.map(svc => (
            <div key={svc.name} className="py-3 flex items-center justify-between text-sm">
              <div>
                <span className="font-semibold text-slate-800 dark:text-slate-200 block">
                  {svc.name}
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  {svc.details}
                </span>
              </div>
              <div>
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
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
