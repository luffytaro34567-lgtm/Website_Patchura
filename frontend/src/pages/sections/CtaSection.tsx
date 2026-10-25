import { Link } from 'react-router-dom'
import { ArrowRight, Shield } from 'lucide-react'

export function CtaSection() {
  return (
    <section
      id="pricing"
      className="py-24 lg:py-32 bg-slate-50 dark:bg-dark-800/50"
      aria-labelledby="cta-heading"
    >
      <div className="section-container">
        <div className="relative max-w-3xl mx-auto text-center overflow-hidden rounded-2xl bg-gradient-to-br from-primary-600 to-primary-800 dark:from-primary-700 dark:to-primary-900 p-6 sm:p-12 shadow-2xl">
          {/* Decorative background */}
          <div
            className="absolute inset-0 bg-grid-pattern opacity-10"
            aria-hidden
          />
          <div
            className="absolute -right-16 -top-16 w-64 h-64 rounded-full bg-white/5"
            aria-hidden
          />
          <div
            className="absolute -left-16 -bottom-16 w-64 h-64 rounded-full bg-white/5"
            aria-hidden
          />

          <div className="relative z-10">
            <Shield className="w-12 h-12 text-white/80 mx-auto mb-6" aria-hidden />
            <h2
              id="cta-heading"
              className="text-3xl sm:text-4xl font-bold text-white mb-4"
            >
              Ready to secure your application?
            </h2>
            <p className="text-lg text-primary-100 mb-8 max-w-xl mx-auto">
              Start with a free assessment. No credit card required. Pricing plans will be announced when the platform launches.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center w-full max-w-xs sm:max-w-none mx-auto">
              <Link
                to="/get-started"
                className="inline-flex items-center justify-center gap-2 px-8 py-3.5 min-h-[48px] rounded-lg font-semibold text-primary-700 bg-white hover:bg-primary-50 transition-colors"
              >
                Get Started Free
                <ArrowRight className="w-4 h-4" aria-hidden />
              </Link>
              <Link
                to="/login"
                className="inline-flex items-center justify-center gap-2 px-8 py-3.5 min-h-[48px] rounded-lg font-semibold text-white border border-white/30 hover:bg-white/10 transition-colors"
              >
                Log In
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
