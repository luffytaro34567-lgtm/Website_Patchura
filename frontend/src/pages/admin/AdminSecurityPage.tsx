import React from 'react'
import { AlertOctagon, ShieldCheck, Lock, CheckCircle2, Shield } from 'lucide-react'

export function AdminSecurityPage() {
  return (
    <div className="space-y-6">
      <div className="border-b border-slate-200 dark:border-dark-700 pb-6">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
          Security Controls & CVE Protection
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Active vulnerability shields, zero-day mitigation protocols, and cryptographic policies
        </p>
      </div>

      {/* PHP2Shell Spotlight */}
      <div className="card p-6 border-rose-200 dark:border-rose-900 bg-rose-50/40 dark:bg-rose-950/20 space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-rose-100 dark:bg-rose-900/50 text-rose-600 dark:text-rose-400">
            <AlertOctagon className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-slate-900 dark:text-white text-base">
                PHP2Shell Zero-Day Protection Status
              </h3>
              <span className="text-xs px-2 py-0.5 rounded bg-rose-600 text-white font-mono uppercase font-semibold">
                Permanent Mandate Active
              </span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
              CVE-2026-109618 & CVE-2026-109619 • Unauthenticated Remote Code Execution Prevention (CVSS 9.2)
            </p>
          </div>
        </div>

        <div className="grid sm:grid-cols-3 gap-4 pt-2 text-xs">
          <div className="p-3 rounded-lg bg-white dark:bg-dark-900 border border-slate-200 dark:border-dark-700">
            <span className="text-slate-400 block mb-1">Target PHP Versions</span>
            <span className="font-semibold text-slate-800 dark:text-slate-200 font-mono">
              PHP 5.4 through 8.5
            </span>
          </div>
          <div className="p-3 rounded-lg bg-white dark:bg-dark-900 border border-slate-200 dark:border-dark-700">
            <span className="text-slate-400 block mb-1">Defensive Re-entrancy Locks</span>
            <span className="font-semibold text-emerald-600 dark:text-emerald-400 font-mono">
              ENGAGED (Re-entrant Guard)
            </span>
          </div>
          <div className="p-3 rounded-lg bg-white dark:bg-dark-900 border border-slate-200 dark:border-dark-700">
            <span className="text-slate-400 block mb-1">Zend Error Buffer Protection</span>
            <span className="font-semibold text-emerald-600 dark:text-emerald-400 font-mono">
              display_errors Off Enforced
            </span>
          </div>
        </div>
      </div>

      {/* Account Security Standards */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="card p-6 space-y-3">
          <div className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white border-b border-slate-100 dark:border-dark-700 pb-3">
            <Lock className="w-4 h-4 text-purple-500" />
            <h3>Token & Session Security</h3>
          </div>
          <ul className="space-y-2 text-xs text-slate-600 dark:text-slate-400">
            <li className="flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
              <span>Short-lived Access Tokens (15-minute expiration)</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
              <span>RFC 6749 Rotating Refresh Tokens with Family Invalidation</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
              <span>Refresh tokens stored strictly as SHA-256 hashes (never plaintext)</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
              <span>Token Replay & Reuse Detection with automatic family revocation</span>
            </li>
          </ul>
        </div>

        <div className="card p-6 space-y-3">
          <div className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white border-b border-slate-100 dark:border-dark-700 pb-3">
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
            <h3>Password Policy & Enumeration Defense</h3>
          </div>
          <ul className="space-y-2 text-xs text-slate-600 dark:text-slate-400">
            <li className="flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
              <span>Passlib with bcrypt (adaptive work factor 12)</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
              <span>Dummy hash timing-attack equalization during login failures</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
              <span>Uniform error messages preventing username/email enumeration</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
              <span>Mandatory password complexity (8+ chars, upper, lower, digit, symbol)</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}
