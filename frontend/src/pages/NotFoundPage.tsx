import { Link } from 'react-router-dom'
import { AlertTriangle } from 'lucide-react'

export function NotFoundPage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <AlertTriangle className="w-16 h-16 text-yellow-500 mx-auto mb-6" aria-hidden />
        <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-3">404</h1>
        <p className="text-xl font-medium text-slate-700 dark:text-slate-300 mb-2">
          Page not found
        </p>
        <p className="text-slate-500 dark:text-slate-400 mb-8">
          The page you are looking for does not exist or has been moved.
        </p>
        <Link to="/" className="btn-primary">
          Return to Home
        </Link>
      </div>
    </div>
  )
}
