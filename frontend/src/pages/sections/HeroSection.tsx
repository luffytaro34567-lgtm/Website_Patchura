import { Link } from 'react-router-dom'
import { ArrowRight, ShieldCheck, Zap } from 'lucide-react'

export function HeroSection() {
  return (
    <section
      className="relative min-h-screen flex items-center pt-16 overflow-hidden bg-white dark:bg-dark-900"
      aria-labelledby="hero-heading"
    >
      {/* Background grid */}
      <div
        className="absolute inset-0 bg-grid-pattern dark:bg-grid-pattern-dark"
        aria-hidden
      />

      {/* Radial glow — decorative only */}
      <div
        className="absolute -top-32 left-1/2 -translate-x-1/2 w-[700px] h-[700px] bg-primary-500/10 dark:bg-primary-500/5 rounded-full blur-3xl pointer-events-none"
        aria-hidden
      />

      <div className="section-container relative z-10 py-24 lg:py-32">
        <div className="max-w-4xl mx-auto text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-primary-200 dark:border-primary-800 bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 text-xs font-medium mb-8 animate-fade-in">
            <Zap className="w-3 h-3" aria-hidden />
            AI-Powered Security Assessment Platform
          </div>

          {/* Heading */}
          <h1
            id="hero-heading"
            className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-900 dark:text-white leading-tight mb-6 animate-slide-up"
          >
            Find & Fix Website{' '}
            <span className="gradient-text">Vulnerabilities</span>{' '}
            with AI
          </h1>

          {/* Description */}
          <p className="text-lg sm:text-xl text-slate-600 dark:text-slate-400 max-w-2xl mx-auto mb-10 animate-slide-up">
            PATCHORA delivers AI-assisted vulnerability assessment, security remediation, and secure patch delivery for modern web applications.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center animate-slide-up w-full max-w-xs sm:max-w-none mx-auto">
            <Link
              to="/get-started"
              className="btn-primary px-8 py-3.5 text-base min-h-[48px] justify-center"
            >
              Get Started Free
              <ArrowRight className="w-4 h-4" aria-hidden />
            </Link>
            <Link
              to="/login"
              className="btn-secondary px-8 py-3.5 text-base min-h-[48px] justify-center"
            >
              Log In
            </Link>
          </div>

          {/* Trust line — no fabricated stats */}
          <div className="mt-12 flex flex-wrap items-center justify-center gap-6 text-sm text-slate-500 dark:text-slate-400">
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-primary-500" aria-hidden />
              No scan data is fabricated
            </span>
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-primary-500" aria-hidden />
              Assessments run only on your authorised targets
            </span>
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-primary-500" aria-hidden />
              Results are always real
            </span>
          </div>
        </div>

        {/* Hero visual — terminal / code style (no fake data) */}
        <div className="mt-20 max-w-3xl mx-auto">
          <div className="card shadow-2xl dark:shadow-dark-900/50 overflow-hidden">
            {/* Terminal chrome */}
            <div className="flex items-center gap-1.5 mb-4 -mx-6 -mt-6 px-6 py-3 bg-slate-100 dark:bg-dark-700 border-b border-slate-200 dark:border-dark-600">
              <span className="w-3 h-3 rounded-full bg-red-400" aria-hidden />
              <span className="w-3 h-3 rounded-full bg-yellow-400" aria-hidden />
              <span className="w-3 h-3 rounded-full bg-green-400" aria-hidden />
              <span className="ml-3 text-xs text-slate-400 dark:text-slate-500 font-mono">
                patchora — assessment engine
              </span>
            </div>

            <div className="font-mono text-xs sm:text-sm space-y-2 text-slate-700 dark:text-slate-300 overflow-x-auto break-words">
              <p>
                <span className="text-primary-500">$</span>{' '}
                <span className="text-slate-400">
                  # Assessments run against your authorised targets only
                </span>
              </p>
              <p className="break-all sm:break-normal">
                <span className="text-primary-500">$</span>{' '}
                patchora scan --target https://your-app.example.com
              </p>
              <p className="text-slate-400">
                &nbsp;&nbsp;Initialising assessment engine&nbsp;
                <span className="text-primary-400">v0.1.0</span>&nbsp;…
              </p>
              <p className="text-slate-400">
                &nbsp;&nbsp;Waiting for scan results — real findings only
              </p>
              <p className="text-slate-400">
                &nbsp;&nbsp;<span className="text-yellow-400">⚠</span>&nbsp;
                No scan has been run in this demo. Start a real assessment above.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
