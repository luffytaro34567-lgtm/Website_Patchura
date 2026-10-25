import { apiClient } from './client'
import {
  AdminBillingStats,
  BillingInterval,
  CheckoutSession,
  Invoice,
  OneTimeCheckoutSession,
  PlanTierInfo,
  Subscription,
  Transaction,
} from '@/types/billing'

export async function listPlans(): Promise<PlanTierInfo[]> {
  const res = await apiClient.get<PlanTierInfo[]>('/api/billing/plans')
  return res.data
}

export async function getMySubscription(): Promise<Subscription> {
  const res = await apiClient.get<Subscription>('/api/billing/subscription')
  return res.data
}

export async function createCheckoutSession(
  planTier: string,
  billingInterval: BillingInterval = 'month'
): Promise<CheckoutSession> {
  const res = await apiClient.post<CheckoutSession>('/api/billing/checkout-session', {
    plan_tier: planTier,
    billing_interval: billingInterval,
  })
  return res.data
}

export async function simulateCheckoutCompletion(
  sessionId: string,
  outcome: 'succeeded' | 'failed' = 'succeeded'
): Promise<Subscription> {
  const res = await apiClient.post<Subscription>('/api/billing/simulate-checkout-completion', {
    session_id: sessionId,
    outcome,
  })
  return res.data
}

export async function cancelSubscription(): Promise<Subscription> {
  const res = await apiClient.post<Subscription>('/api/billing/cancel-subscription')
  return res.data
}

export async function createOneTimeCheckoutSession(
  productName: string,
  amountCents: number,
  referenceId: string
): Promise<OneTimeCheckoutSession> {
  const res = await apiClient.post<OneTimeCheckoutSession>('/api/billing/onetime-checkout-session', {
    product_name: productName,
    amount_cents: amountCents,
    reference_id: referenceId,
  })
  return res.data
}

export async function simulateOneTimeCompletion(
  sessionId: string,
  outcome: 'succeeded' | 'failed' = 'succeeded'
): Promise<Transaction> {
  const res = await apiClient.post<Transaction>('/api/billing/simulate-onetime-completion', {
    session_id: sessionId,
    outcome,
  })
  return res.data
}

export async function listMyInvoices(): Promise<Invoice[]> {
  const res = await apiClient.get<Invoice[]>('/api/billing/invoices')
  return res.data
}

export async function downloadInvoiceHtml(invoiceId: string, invoiceNumber: string): Promise<void> {
  const res = await apiClient.get(`/api/billing/invoices/${invoiceId}/download`, {
    responseType: 'blob',
  })
  const blob = new Blob([res.data], { type: 'text/html' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${invoiceNumber}.html`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export async function adminGetBillingStats(): Promise<AdminBillingStats> {
  const res = await apiClient.get<AdminBillingStats>('/api/billing/admin/stats')
  return res.data
}

export async function adminListTransactions(): Promise<Transaction[]> {
  const res = await apiClient.get<Transaction[]>('/api/billing/admin/transactions')
  return res.data
}
