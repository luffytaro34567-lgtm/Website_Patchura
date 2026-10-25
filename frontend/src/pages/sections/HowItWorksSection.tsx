import { Globe, ScanSearch, FileSearch, Sparkles } from 'lucide-react'

const STEPS = [
  {
    step: '01',
    icon: Globe,
    title: 'Add your target',
    description:
      'Register the web application you own or have authorisation to assess. We verify scope before any scan begins.',
  },
  {
    step: '02',
    icon: ScanSearch,
    title: 'Run an assessment',
    description:
      'Trigger an automated vulnerability scan. Our engine tests for OWASP Top 10, misconfigurations, exposed secrets, and more.',
  },
  {
    step: '03',
    icon: FileSearch,
    title: 'Review your report',
    description:
      'Receive a structured report with findings ranked by severity, CVSS scoring, and actionable remediation guidance.',
  },
  {
    step: '04',
    icon: Sparkles,
    title: 'Apply AI-assisted fixes',
    description:
      'Our AI analyses the vulnerable code paths and proposes targeted patches you can review and apply directly.',
  },
]

export function HowItWorksSection() {
  return (
    <section
      id="how-it-works"
      className="py-24 lg:py-32 bg-white dark:bg-dark-900"
      aria-labelledby="hiw-heading"
    >
      <div className="section-container">
        <div className="max-w-2xl mx-auto text-center mb-16">
          <span className="text-xs font-semibold uppercase tracking-widest text-primary-500 mb-3 block">
            Workflow
          </span>
          <h2
            id="hiw-heading"
            className="text-3xl sm:text-4xl font-bold text-slate-900 dark:text-white mb-4"
          >
            From zero to secured in four steps
          </h2>
          <p className="text-lg text-slate-600 dark:text-slate-400">
            A straightforward process designed for development teams and security professionals alike.
          </p>
        </div>

        <div className="relative">
          {/* Connector line — desktop */}
          <div
            className="hidden lg:block absolute top-14 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary-200 dark:via-primary-800 to-transparent"
            aria-hidden
          />

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-8">
            {STEPS.map((step, i) => {
              const Icon = step.icon
              return (
                <div key={step.step} className="relative flex flex-col items-center text-center">
                  {/* Step circle */}
                  <div className="relative z-10 flex flex-col items-center mb-5">
                    <div className="w-14 h-14 rounded-full bg-primary-500 text-white flex items-center justify-center shadow-lg shadow-primary-500/20">
                      <Icon className="w-6 h-6" aria-hidden />
                    </div>
                    <span className="absolute -top-2 -right-2 text-xs font-bold text-primary-500 bg-primary-50 dark:bg-primary-900/40 border border-primary-200 dark:border-primary-800 rounded-full w-6 h-6 flex items-center justify-center">
                      {i + 1}
                    </span>
                  </div>

                  <h3 className="font-semibold text-slate-900 dark:text-white mb-2">
                    {step.title}
                  </h3>
                  <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                    {step.description}
                  </p>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </section>
  )
}
