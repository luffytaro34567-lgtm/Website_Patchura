import React from 'react'
import { Link } from 'react-router-dom'
import { Clock, Shield, ArrowLeft } from 'lucide-react'

interface ComingSoonProps {
  moduleName: string
  phaseNumber: number
  phaseTitle: string
  description: string
  plannedFeatures: string[]
}

export function ComingSoonPage({
  moduleName,
  phaseNumber,
  phaseTitle,
  description,
  plannedFeatures,
}: ComingSoonProps) {
  return (
    <div className="max-w-3xl mx-auto py-12 space-y-8">
      <Link
        to="/dashboard"
        className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-primary-500 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Return to Account Overview
      </Link>

      <div className="card p-8 text-center space-y-4">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-primary-50 dark:bg-primary-950 text-primary-500 border border-primary-200 dark:border-primary-800">
          <Clock className="w-6 h-6" />
        </div>

        <div>
          <span className="text-xs font-mono uppercase px-2.5 py-1 rounded bg-primary-100 dark:bg-primary-950 text-primary-700 dark:text-primary-300 font-semibold border border-primary-200 dark:border-primary-800">
            Roadmap Deliverable: Phase {phaseNumber} ({phaseTitle})
          </span>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white mt-3">
            {moduleName}
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 max-w-xl mx-auto mt-2 leading-relaxed">
            {description}
          </p>
        </div>

        {/* Feature roadmap checklist */}
        <div className="text-left pt-6 border-t border-slate-100 dark:border-dark-700 max-w-md mx-auto space-y-2">
          <span className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider block">
            Scheduled Phase Capabilities:
          </span>
          <ul className="space-y-1.5 text-xs text-slate-600 dark:text-slate-400">
            {plannedFeatures.map(f => (
              <li key={f} className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-primary-500" />
                <span>{f}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="pt-4 text-xs text-slate-400">
          In the meantime, you can explore the functional{' '}
          <Link to="/dashboard/scanner" className="text-primary-500 font-medium hover:underline">
            PHP Vulnerability & PHP2Shell Scanner
          </Link>.
        </div>
      </div>
    </div>
  )
}
