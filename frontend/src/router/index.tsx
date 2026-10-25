import { createBrowserRouter, Navigate } from 'react-router-dom'
import { RootLayout } from '@/components/layout/RootLayout'
import { AdminLayout } from '@/components/layout/AdminLayout'
import { ClientLayout } from '@/components/layout/ClientLayout'
import { LandingPage } from '@/pages/LandingPage'
import { LoginPage } from '@/pages/LoginPage'
import { RegisterPage } from '@/pages/RegisterPage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { ProtectedRoute, AdminRoute } from '@/router/ProtectedRoute'

// Admin Pages
import { AdminOverviewPage } from '@/pages/admin/AdminOverviewPage'
import { AdminActivityCenterPage } from '@/pages/admin/AdminActivityCenterPage'
import { AdminUsersPage } from '@/pages/admin/AdminUsersPage'
import { AdminWebsitesPage } from '@/pages/admin/AdminWebsitesPage'
import { AdminScansPage } from '@/pages/admin/AdminScansPage'
import { AdminReportsPage } from '@/pages/admin/AdminReportsPage'
import { AdminBillingPage } from '@/pages/admin/AdminBillingPage'
import { AdminRemediationsPage } from '@/pages/admin/AdminRemediationsPage'
import { AdminDeploymentsPage } from '@/pages/admin/AdminDeploymentsPage'
import { AdminClientFinderPage } from '@/pages/admin/AdminClientFinderPage'
import { AdminSecurityPage } from '@/pages/admin/AdminSecurityPage'
import { AdminServicesPage } from '@/pages/admin/AdminServicesPage'
import { AdminAuditPage } from '@/pages/admin/AdminAuditPage'
import { AdminSettingsPage } from '@/pages/admin/AdminSettingsPage'

// Client Pages
import { ClientOverviewPage } from '@/pages/client/ClientOverviewPage'
import { ClientScannerPage } from '@/pages/client/ClientScannerPage'
import { WebsitesListPage } from '@/pages/client/WebsitesListPage'
import { WebsiteDetailsPage } from '@/pages/client/WebsiteDetailsPage'
import { ClientScansPage } from '@/pages/client/ClientScansPage'
import { ScanDetailsPage } from '@/pages/client/ScanDetailsPage'
import { ReportsListPage } from '@/pages/client/ReportsListPage'
import { DetailedReportPage } from '@/pages/client/DetailedReportPage'
import { ClientBillingPage } from '@/pages/client/ClientBillingPage'
import { ClientRemediationsPage } from '@/pages/client/ClientRemediationsPage'
import { ClientDeploymentsPage } from '@/pages/client/ClientDeploymentsPage'
import { ClientSettingsPage } from '@/pages/client/ClientSettingsPage'
import { ComingSoonPage } from '@/pages/client/ComingSoonPage'

export const router = createBrowserRouter([
  // Public Routes (RootLayout: Navbar + Content + Footer)
  {
    path: '/',
    element: <RootLayout />,
    children: [
      {
        index: true,
        element: <LandingPage />,
      },
      {
        path: 'login',
        element: <LoginPage />,
      },
      {
        path: 'register',
        element: <RegisterPage />,
      },
      {
        path: 'get-started',
        element: <RegisterPage />,
      },
    ],
  },

  // Client Panel (ProtectedRoute -> ClientLayout)
  {
    path: '/dashboard',
    element: <ProtectedRoute />,
    children: [
      {
        element: <ClientLayout />,
        children: [
          {
            index: true,
            element: <ClientOverviewPage />,
          },
          {
            path: 'scanner',
            element: <ClientScannerPage />,
          },
          {
            path: 'websites',
            element: <WebsitesListPage />,
          },
          {
            path: 'websites/:websiteId',
            element: <WebsiteDetailsPage />,
          },
          {
            path: 'scans',
            element: <ClientScansPage />,
          },
          {
            path: 'scans/:scanId',
            element: <ScanDetailsPage />,
          },
          {
            path: 'reports',
            element: <ReportsListPage />,
          },
          {
            path: 'reports/:scanId',
            element: <DetailedReportPage />,
          },
          {
            path: 'remediations',
            element: <ClientRemediationsPage />,
          },
          {
            path: 'fixes',
            element: <ClientRemediationsPage />,
          },
          {
            path: 'deployments',
            element: <ClientDeploymentsPage />,
          },
          {
            path: 'billing',
            element: <ClientBillingPage />,
          },
          {
            path: 'notifications',
            element: (
              <ComingSoonPage
                moduleName="Security Alerts & Webhooks"
                phaseNumber={8}
                phaseTitle="Notifications & Client Discovery"
                description="Configure multi-channel security alerts via email, Slack, Discord, and outbound webhooks."
                plannedFeatures={[
                  'Instant email alerts on critical CVE discoveries',
                  'Slack and Discord webhook notifications',
                  'Customizable severity triage thresholds',
                  'Weekly executive security digests',
                ]}
              />
            ),
          },
          {
            path: 'settings',
            element: <ClientSettingsPage />,
          },
        ],
      },
    ],
  },

  // Admin Panel (AdminRoute -> AdminLayout)
  {
    path: '/admin',
    element: <AdminRoute />,
    children: [
      {
        element: <AdminLayout />,
        children: [
          {
            index: true,
            element: <Navigate to="/admin/dashboard" replace />,
          },
          {
            path: 'dashboard',
            element: <AdminOverviewPage />,
          },
          {
            path: 'activity',
            element: <AdminActivityCenterPage />,
          },
          {
            path: 'users',
            element: <AdminUsersPage />,
          },
          {
            path: 'websites',
            element: <AdminWebsitesPage />,
          },
          {
            path: 'scans',
            element: <AdminScansPage />,
          },
          {
            path: 'reports',
            element: <AdminReportsPage />,
          },
          {
            path: 'billing',
            element: <AdminBillingPage />,
          },
          {
            path: 'remediations',
            element: <AdminRemediationsPage />,
          },
          {
            path: 'deployments',
            element: <AdminDeploymentsPage />,
          },
          {
            path: 'client-finder',
            element: <AdminClientFinderPage />,
          },
          {
            path: 'leads',
            element: <AdminClientFinderPage />,
          },
          {
            path: 'security',
            element: <AdminSecurityPage />,
          },
          {
            path: 'services',
            element: <AdminServicesPage />,
          },
          {
            path: 'audit',
            element: <AdminAuditPage />,
          },
          {
            path: 'settings',
            element: <AdminSettingsPage />,
          },
        ],
      },
    ],
  },

  // Fallback 404
  {
    path: '*',
    element: <NotFoundPage />,
  },
])
