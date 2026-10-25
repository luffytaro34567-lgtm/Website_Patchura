import { Shield, FileText, Wrench, Bell, Lock, BarChart3, Terminal, AlertOctagon } from 'lucide-react'
import clsx from 'clsx'

const FEATURES = [
  {
    icon: AlertOctagon,
    title: 'PHP2Shell & Critical CVE Mitigation',
    description:
      'Detects memory corruption during error handling (CVE-2026-109618 & CVE-2026-109619, CVSS 9.2) across PHP 5.4–8.5 with automated defense-in-depth code and configuration patches.',
    accent: 'text-rose-500 bg-rose-50 dark:bg-rose-900/20 border-rose-200 dark:border-rose-800/40',
    badge: 'PHP 5.4 - 8.5 Shield',
  },
  {
    icon: Shield,
    title: 'Vulnerability Assessment',
    description:
      'Automated scanning identifies OWASP Top 10 vulnerabilities, misconfigurations, and security weaknesses across your web applications.',
    accent: 'text-red-500 bg-red-50 dark:bg-red-900/20',
  },
  {
    icon: Wrench,
    title: 'AI-Assisted Fixes & Patching',
    description:
      'Our AI analyses your codebase and suggests targeted, verified patches for detected issues, reducing mean time to remediation.',
    accent: 'text-primary-500 bg-primary-50 dark:bg-primary-900/20',
  },
  {
    icon: FileText,
    title: 'Detailed Security Reports',
    description:
      'Receive comprehensive, prioritised reports with CVSS scores, remediation guidance, and executive summaries — generated from real findings.',
    accent: 'text-blue-500 bg-blue-50 dark:bg-blue-900/20',
  },
  {
    icon: Lock,
    title: 'Continuous Monitoring',
    description:
      'Schedule recurring assessments to catch regressions and new vulnerabilities introduced during development.',
    accent: 'text-purple-500 bg-purple-50 dark:bg-purple-900/20',
  },
  {
    icon: BarChart3,
    title: 'Security Posture Tracking',
    description:
      'Track your security score over time, measure remediation progress, and demonstrate compliance improvements.',
    accent: 'text-green-500 bg-green-50 dark:bg-green-900/20',
  },
]

const SUPPORTED_STACKS = [
  { name: 'PHP (5.4 - 8.5)', highlight: true, note: 'PHP2Shell Protected' },
  { name: 'Python / FastAPI', highlight: false },
  { name: 'Node.js / Express', highlight: false },
  { name: 'React / Next.js', highlight: false },
  { name: 'Nginx / Apache', highlight: false },
]

export function FeaturesSection() {
  return (
    <section
      id="features"
      className="py-24 lg:py-32 bg-slate-50 dark:bg-dark-800/50"
      aria-labelledby="features-heading"
    >
      <div className="section-container">
        {/* Heading */}
        <div className="max-w-3xl mx-auto text-center mb-16">
          <span className="text-xs font-semibold uppercase tracking-widest text-primary-500 mb-3 block">
            Platform Capabilities
          </span>
          <h2
            id="features-heading"
            className="text-3xl sm:text-4xl font-bold text-slate-900 dark:text-white mb-4"
          >
            Full-Spectrum Vulnerability Assessment & Automated Fixes
          </h2>
          <p className="text-lg text-slate-600 dark:text-slate-400">
            From modern zero-days like PHP2Shell RCE to OWASP Top 10 weaknesses, PATCHORA delivers
            precise detection, CVSS analysis, and drop-in code fixes.
          </p>

          {/* Supported tech tags */}
          <div className="mt-6 flex flex-wrap justify-center items-center gap-2">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400 mr-1">
              Coverage:
            </span>
            {SUPPORTED_STACKS.map(stack => (
              <span
                key={stack.name}
                className={clsx(
                  'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold',
                  stack.highlight
                    ? 'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300 border border-rose-300 dark:border-rose-800'
                    : 'bg-slate-200/80 text-slate-700 dark:bg-dark-700 dark:text-slate-300'
                )}
              >
                {stack.name}
                {stack.note && (
                  <span className="text-[10px] px-1 py-0.5 rounded bg-rose-600 text-white font-mono uppercase">
                    {stack.note}
                  </span>
                )}
              </span>
            ))}
          </div>
        </div>

        {/* Feature grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map(feature => {
            const Icon = feature.icon
            return (
              <div
                key={feature.title}
                className="card hover:shadow-md dark:hover:shadow-dark-900/30 transition-shadow duration-200 group relative flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div
                      className={clsx(
                        'inline-flex items-center justify-center w-10 h-10 rounded-lg',
                        feature.accent
                      )}
                    >
                      <Icon className="w-5 h-5" aria-hidden />
                    </div>
                    {feature.badge && (
                      <span className="text-[11px] font-semibold tracking-wide text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800 px-2 py-0.5 rounded">
                        {feature.badge}
                      </span>
                    )}
                  </div>
                  <h3 className="font-semibold text-slate-900 dark:text-white mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
