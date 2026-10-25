import { Shield } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Logo } from '@/components/shared/Logo'

const FOOTER_LINKS = {
  Product: [
    { label: 'Features', href: '#features' },
    { label: 'How It Works', href: '#how-it-works' },
    { label: 'Pricing', href: '#pricing' },
  ],
  Company: [
    { label: 'About', href: '#' },
    { label: 'Blog', href: '#' },
    { label: 'Careers', href: '#' },
  ],
  Legal: [
    { label: 'Privacy Policy', href: '#' },
    { label: 'Terms of Service', href: '#' },
    { label: 'Security', href: '#' },
  ],
  Support: [
    { label: 'Documentation', href: '#' },
    { label: 'Contact', href: '#' },
    { label: 'Status', href: '#' },
  ],
}

export function Footer() {
  return (
    <footer className="bg-slate-50 dark:bg-dark-900 border-t border-slate-200 dark:border-dark-700">
      <div className="section-container py-12 lg:py-16">
        {/* Top: brand + link columns */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 lg:gap-12">
          {/* Brand */}
          <div className="col-span-2 md:col-span-1">
            <Link
              to="/"
              className="inline-block"
              aria-label="PATCHORA Home"
            >
              <Logo variant="horizontal" size="md" />
            </Link>
            <p className="mt-3 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
              AI-assisted vulnerability assessment, security remediation, and secure patch delivery.
            </p>
          </div>

          {/* Link columns */}
          {Object.entries(FOOTER_LINKS).map(([section, links]) => (
            <div key={section}>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-3">
                {section}
              </h3>
              <ul className="space-y-2" role="list">
                {links.map(link => (
                  <li key={link.label}>
                    <a
                      href={link.href}
                      className="text-sm text-slate-600 dark:text-slate-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="mt-12 pt-6 border-t border-slate-200 dark:border-dark-700 flex flex-col sm:flex-row justify-between items-center gap-3">
          <p className="text-sm text-slate-500 dark:text-slate-400">
            &copy; {new Date().getFullYear()} PATCHORA. All rights reserved.
          </p>
          <p className="text-xs text-slate-400 dark:text-slate-500">
            Built for security professionals.
          </p>
        </div>
      </div>
    </footer>
  )
}
