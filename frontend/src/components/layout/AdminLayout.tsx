import React, { useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { Logo } from '@/components/shared/Logo'
import {
  Shield,
  Users,
  AlertOctagon,
  Globe,
  ScanSearch,
  Server,
  FileText,
  CreditCard,
  Wrench,
  GitPullRequest,
  Settings,
  LogOut,
  Menu,
  X,
  Sun,
  Moon,
  LayoutDashboard,
  ExternalLink,
  Target,
  Activity,
} from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { useTheme } from '@/theme/ThemeContext'
import clsx from 'clsx'

const ADMIN_NAV = [
  { label: 'Platform Overview', path: '/admin/dashboard', icon: LayoutDashboard },
  { label: 'Activity & Security Center', path: '/admin/activity', icon: Activity },
  { label: 'User & Client Management', path: '/admin/users', icon: Users },
  { label: 'Target Websites Directory', path: '/admin/websites', icon: Globe },
  { label: 'Scan Operations', path: '/admin/scans', icon: ScanSearch },
  { label: 'Report Orders & Grants', path: '/admin/reports', icon: FileText },
  { label: 'Billing & Revenue', path: '/admin/billing', icon: CreditCard },
  { label: 'AI Fixes & Patches', path: '/admin/remediations', icon: Wrench },
  { label: 'DevSecOps Deployments', path: '/admin/deployments', icon: GitPullRequest },
  { label: 'Client Finder Automation', path: '/admin/client-finder', icon: Target },
  { label: 'Security & PHP2Shell Shield', path: '/admin/security', icon: AlertOctagon },
  { label: 'System Services', path: '/admin/services', icon: Server },
  { label: 'Audit Events', path: '/admin/audit', icon: FileText },
  { label: 'Admin Settings', path: '/admin/settings', icon: Settings },
]

export function AdminLayout() {
  const { user, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)

  // Close mobile navigation on Escape key or window resize
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && mobileOpen) {
        setMobileOpen(false)
      }
    }
    const handleResize = () => {
      if (window.innerWidth >= 768 && mobileOpen) {
        setMobileOpen(false)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    window.addEventListener('resize', handleResize)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('resize', handleResize)
    }
  }, [mobileOpen])

  // Prevent background scrolling when mobile drawer is open
  React.useEffect(() => {
    if (mobileOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [mobileOpen])

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-dark-900 flex flex-col md:flex-row overflow-x-hidden">
      {/* Mobile Top Header */}
      <div className="md:hidden flex items-center justify-between px-3 sm:px-4 py-2.5 bg-white dark:bg-dark-800 border-b border-slate-200 dark:border-dark-700 sticky top-0 z-30">
        <Link to="/admin/dashboard" className="flex items-center gap-2 font-bold text-slate-900 dark:text-white min-h-[44px]">
          <Logo variant="symbol" size="sm" />
          <span className="font-extrabold tracking-tight text-sm sm:text-base flex items-center gap-1.5">
            <span className="text-slate-900 dark:text-white">PATCH</span><span className="text-cyan-500">ORA</span>
            <span className="text-purple-600 dark:text-purple-400 font-mono text-[10px] uppercase px-1.5 py-0.5 rounded bg-purple-100 dark:bg-purple-950 border border-purple-200 dark:border-purple-800">Admin</span>
          </span>
        </Link>
        <div className="flex items-center gap-1">
          <button
            onClick={toggleTheme}
            aria-label="Toggle theme"
            className="btn-ghost p-2 min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg"
          >
            {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label={mobileOpen ? 'Close navigation' : 'Open navigation'}
            aria-expanded={mobileOpen}
            className="btn-ghost p-2 min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg text-slate-700 dark:text-slate-200"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Backdrop overlay for mobile drawer */}
      <div
        className={clsx(
          'fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-40 transition-opacity duration-200 md:hidden',
          mobileOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        )}
        onClick={() => setMobileOpen(false)}
        aria-hidden="true"
      />

      {/* Sidebar Navigation */}
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-50 w-72 max-w-[85vw] bg-white dark:bg-dark-800 border-r border-slate-200 dark:border-dark-700 flex flex-col justify-between transition-transform duration-200 ease-in-out md:translate-x-0 md:static md:h-screen md:w-64',
          mobileOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full'
        )}
      >
        <div>
          {/* Brand */}
          <div className="h-16 flex items-center px-4 border-b border-slate-100 dark:border-dark-700">
            <Link to="/admin/dashboard" className="flex items-center gap-1.5 font-bold text-slate-900 dark:text-white">
              <Logo variant="horizontal" size="sm" />
              <span className="text-[10px] font-mono uppercase bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300 px-1.5 py-0.5 rounded border border-purple-200 dark:border-purple-800">
                Admin
              </span>
            </Link>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-1.5" aria-label="Admin Navigation">
            <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider px-3 mb-2 block">
              Administration
            </span>
            {ADMIN_NAV.map(item => {
              const Icon = item.icon
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileOpen(false)}
                  className={({ isActive }) =>
                    clsx(
                      'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-purple-50 dark:bg-purple-950/50 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800/60'
                        : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-dark-700'
                    )
                  }
                >
                  <Icon className="w-4 h-4 flex-shrink-0" />
                  <span>{item.label}</span>
                </NavLink>
              )
            })}
          </nav>
        </div>

        {/* User Card & Switcher */}
        <div className="p-4 border-t border-slate-100 dark:border-dark-700 space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Theme</span>
            <button
              onClick={toggleTheme}
              className="flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-300 hover:text-primary-500"
            >
              {theme === 'dark' ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
              <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
            </button>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 dark:bg-dark-900 border border-slate-200 dark:border-dark-700">
            <div className="text-xs font-semibold text-slate-900 dark:text-white truncate">
              {user?.username}
            </div>
            <div className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
              {user?.email}
            </div>
            <span className="inline-block mt-1 text-[10px] uppercase font-mono px-1.5 py-0.2 rounded bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300">
              Role: Admin
            </span>
          </div>

          <div className="flex flex-col gap-1.5 pt-1">
            <Link
              to="/dashboard"
              className="btn-ghost text-xs w-full justify-start text-slate-600 dark:text-slate-400 hover:text-primary-500"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              View Client View
            </Link>

            <button
              onClick={handleLogout}
              className="btn-ghost text-xs w-full justify-start text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30"
            >
              <LogOut className="w-3.5 h-3.5" />
              Sign Out
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <header className="hidden md:flex h-16 items-center justify-between px-8 border-b border-slate-200 dark:border-dark-700 bg-white/80 dark:bg-dark-800/80 backdrop-blur sticky top-0 z-30">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs font-medium text-slate-600 dark:text-slate-300 font-mono">
              Admin Gateway Connected • Production Isolation
            </span>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right">
              <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 block">
                {user?.username}
              </span>
              <span className="text-[10px] text-slate-400 block font-mono">
                Administrator
              </span>
            </div>
          </div>
        </header>

        <div className="flex-1 p-3.5 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto min-w-0">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
