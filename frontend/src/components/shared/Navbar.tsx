import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Shield, Menu, X, Sun, Moon, LogOut, LayoutDashboard } from 'lucide-react'
import { useTheme } from '@/theme/ThemeContext'
import { Logo } from '@/components/shared/Logo'
import { useAuth } from '@/context/AuthContext'
import clsx from 'clsx'

const NAV_LINKS = [
  { label: 'Features', href: '/#features' },
  { label: 'How It Works', href: '/#how-it-works' },
  { label: 'Pricing', href: '/#pricing' },
]

export function Navbar() {
  const { theme, toggleTheme } = useTheme()
  const { user, isAuthenticated, logout } = useAuth()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 16)
    window.addEventListener('scroll', handler, { passive: true })
    return () => window.removeEventListener('scroll', handler)
  }, [])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && mobileOpen) {
        setMobileOpen(false)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [mobileOpen])

  return (
    <header
      className={clsx(
        'fixed top-0 inset-x-0 z-50 transition-all duration-200',
        scrolled
          ? 'bg-white/95 dark:bg-dark-900/95 backdrop-blur border-b border-slate-200 dark:border-dark-700'
          : 'bg-transparent'
      )}
    >
      <div className="section-container">
        <nav
          className="flex items-center justify-between h-16"
          aria-label="Main navigation"
        >
          {/* Logo */}
          <Link
            to="/"
            className="flex items-center focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 rounded"
            aria-label="PATCHORA Home"
          >
            <Logo variant="horizontal" size="md" />
          </Link>

          {/* Desktop nav links */}
          <ul className="hidden md:flex items-center gap-1" role="list">
            {NAV_LINKS.map(link => (
              <li key={link.href}>
                <a
                  href={link.href}
                  className="px-4 py-2 rounded-md text-sm font-medium text-slate-600 dark:text-slate-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-slate-100 dark:hover:bg-dark-700 transition-colors"
                >
                  {link.label}
                </a>
              </li>
            ))}
          </ul>

          {/* Desktop CTA + theme toggle */}
          <div className="hidden md:flex items-center gap-3">
            <ThemeToggle theme={theme} toggleTheme={toggleTheme} />

            {isAuthenticated && user ? (
              <div className="flex items-center gap-3">
                <Link
                  to="/dashboard"
                  className="btn-ghost text-sm flex items-center gap-1.5"
                >
                  <LayoutDashboard className="w-4 h-4 text-primary-500" />
                  <span>Dashboard</span>
                </Link>
                <span className="text-xs font-mono px-2 py-1 rounded bg-slate-100 dark:bg-dark-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-dark-700">
                  {user.username} ({user.role})
                </span>
                <button
                  type="button"
                  onClick={logout}
                  className="btn-ghost p-2 text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 rounded-lg"
                  aria-label="Log out"
                  title="Log out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <>
                <Link
                  to="/login"
                  className="btn-ghost text-sm"
                >
                  Log in
                </Link>
                <Link
                  to="/get-started"
                  className="btn-primary text-sm"
                >
                  Get Started
                </Link>
              </>
            )}
          </div>

          {/* Mobile controls */}
          <div className="flex md:hidden items-center gap-1">
            <ThemeToggle theme={theme} toggleTheme={toggleTheme} />
            <button
              type="button"
              className="btn-ghost p-2 min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg text-slate-700 dark:text-slate-200"
              aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
              aria-expanded={mobileOpen}
              aria-controls="mobile-menu"
              onClick={() => setMobileOpen(o => !o)}
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </nav>

        {/* Mobile menu */}
        {mobileOpen && (
          <div
            id="mobile-menu"
            className="md:hidden border-t border-slate-200 dark:border-dark-700 bg-white/95 dark:bg-dark-900/95 backdrop-blur-md pb-4 pt-1 shadow-xl animate-fade-in"
          >
            <ul className="flex flex-col gap-1 pt-1" role="list">
              {NAV_LINKS.map(link => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    className="flex items-center px-4 py-2.5 min-h-[44px] text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-dark-700 rounded-lg transition-colors"
                    onClick={() => setMobileOpen(false)}
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
            <div className="mt-3 px-2 flex flex-col gap-2">
              {isAuthenticated && user ? (
                <>
                  <Link
                    to="/dashboard"
                    className="btn-primary w-full min-h-[44px] justify-center text-sm"
                    onClick={() => setMobileOpen(false)}
                  >
                    Dashboard ({user.username})
                  </Link>
                  <button
                    type="button"
                    onClick={() => {
                      logout()
                      setMobileOpen(false)
                    }}
                    className="btn-secondary w-full min-h-[44px] justify-center text-sm text-rose-500"
                  >
                    Log Out
                  </button>
                </>
              ) : (
                <>
                  <Link
                    to="/login"
                    className="btn-secondary w-full min-h-[44px] justify-center text-sm"
                    onClick={() => setMobileOpen(false)}
                  >
                    Log in
                  </Link>
                  <Link
                    to="/get-started"
                    className="btn-primary w-full min-h-[44px] justify-center text-sm"
                    onClick={() => setMobileOpen(false)}
                  >
                    Get Started
                  </Link>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </header>
  )
}

function ThemeToggle({
  theme,
  toggleTheme,
}: {
  theme: 'light' | 'dark'
  toggleTheme: () => void
}) {
  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
      className="btn-ghost p-2 min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg"
    >
      {theme === 'dark' ? (
        <Sun className="w-4 h-4" aria-hidden />
      ) : (
        <Moon className="w-4 h-4" aria-hidden />
      )}
    </button>
  )
}
