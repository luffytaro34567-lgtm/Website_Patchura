import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield,
  Code2,
  Globe,
  ScanSearch,
  Wrench,
  CheckCircle2,
  AlertOctagon,
  ArrowRight,
  Info,
} from 'lucide-react'
import { ClientOverview, fetchClientOverview } from '@/api/dashboard'
import { useAuth } from '@/context/AuthContext'

export function ClientOverviewPage() {
  const { user } = useAuth()
  const [data, setData] = useState<ClientOverview | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchClientOverview()
      .then(res => setData(res))
      .catch(() => {})
      .finally(() => setIsLoading(false))
  }, [])

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200 dark:border-dark-700">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
              Client Workspace Overview
            </h1>
            <span className="text-xs font-mono uppercase bg-primary-100 dark:bg-primary-950 text-primary-700 dark:text-primary-300 px-2 py-0.5 rounded border border-primary-200 dark:border-primary-800">
              Role: Client
            </span>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Logged in as <span className="font-semibold text-slate-700 dark:text-slate-200">{user?.username}</span> ({user?.email})
          </p>
        </div>

        <Link to="/dashboard/scanner" className="btn-primary text-xs">
          <Code2 className="w-3.5 h-3.5" />
          Test PHP Code Scanner
        </Link>
      </div>

      {/* Security Status Card */}
      <div className="card p-6 border-emerald-200 dark:border-emerald-900/60 bg-emerald-50/40 dark:bg-emerald-950/20">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2.5 rounded-lg bg-emerald-100 dark:bg-emerald-900/50 text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 dark:text-white text-base">
                PHP2Shell Zero-Day Protection Active
              </h3>
              <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 max-w-2xl leading-relaxed">
                Your workspace is actively shielded against PHP2Shell (CVE-2026-109618 & CVE-2026-109619) memory corruption during error handling. Use our scanner to inspect your applications.
              </p>
            </div>
          </div>
          <Link
            to="/dashboard/scanner"
            className="btn-secondary text-xs self-start md:self-auto border-emerald-300 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300"
          >
            Launch Scanner →
          </Link>
        </div>
      </div>

      {/* Honest Module Metric Cards — Zero counts for unlaunched modules */}
      <div className="grid sm:grid-cols-3 gap-6">
        <div className="card p-5 space-y-3 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
              Registered Target Websites
            </span>
            <div className="p-1.5 rounded-lg bg-slate-100 dark:bg-dark-700 text-slate-600 dark:text-slate-300">
              <Globe className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-bold font-mono text-slate-900 dark:text-white">
            0
          </div>
          <p className="text-[11px] text-slate-400 flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-primary-500 flex-shrink-0" />
            Target management introduces in Phase 4.
          </p>
        </div>

        <div className="card p-5 space-y-3 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
              Completed Vulnerability Scans
            </span>
            <div className="p-1.5 rounded-lg bg-slate-100 dark:bg-dark-700 text-slate-600 dark:text-slate-300">
              <ScanSearch className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-bold font-mono text-slate-900 dark:text-white">
            0
          </div>
          <p className="text-[11px] text-slate-400 flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-primary-500 flex-shrink-0" />
            Full scan queue introduces in Phase 5.
          </p>
        </div>

        <div className="card p-5 space-y-3 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
              AI Fix Requests
            </span>
            <div className="p-1.5 rounded-lg bg-slate-100 dark:bg-dark-700 text-slate-600 dark:text-slate-300">
              <Wrench className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-bold font-mono text-slate-900 dark:text-white">
            0
          </div>
          <p className="text-[11px] text-slate-400 flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-primary-500 flex-shrink-0" />
            AI patch generator introduces in Phase 7.
          </p>
        </div>
      </div>

      {/* Account Details & Session Info */}
      <div className="card p-6 space-y-4">
        <h3 className="font-semibold text-slate-900 dark:text-white text-sm border-b border-slate-100 dark:border-dark-700 pb-3">
          Account Credentials & Session Security
        </h3>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div>
            <span className="text-slate-400 block mb-0.5">Account ID</span>
            <code className="font-mono text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-dark-900 px-2 py-0.5 rounded text-[11px]">
              {user?.id}
            </code>
          </div>
          <div>
            <span className="text-slate-400 block mb-0.5">Assigned Role</span>
            <span className="font-mono font-semibold text-primary-600 dark:text-primary-400">
              ROLE_CLIENT
            </span>
          </div>
          <div>
            <span className="text-slate-400 block mb-0.5">Account Status</span>
            <span className="font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" /> Active & Verified
            </span>
          </div>
          <div>
            <span className="text-slate-400 block mb-0.5">Session Refresh Policy</span>
            <span className="font-mono text-slate-600 dark:text-slate-400">
              RFC 6749 Token Rotation
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
