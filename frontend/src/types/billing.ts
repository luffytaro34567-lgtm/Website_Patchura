export type PlanTier = 'free' | 'pro' | 'enterprise' | 'admin'

export type BillingInterval = 'month' | 'year'

export interface PlanTierInfo {
  tier: PlanTier
  name: string
  tag: string
  monthly_price_cents: number
  annual_price_cents: number
  currency: string
  max_target_websites: number
  monthly_scan_limit: number
  reports_included_per_month: number
  features: string[]
}

export interface Subscription {
  id: string
  user_id: string
  plan_tier: PlanTier
  billing_interval: BillingInterval
  status: string
  price_cents: number
  currency: string
  current_period_start: string
  current_period_end?: string | null
  cancel_at_period_end: boolean
  provider: string
  max_target_websites: number
  monthly_scan_limit: number
  reports_included_per_month: number
  current_target_count: number
  scans_used_this_month: number
}

export interface CheckoutSession {
  session_id: string
  checkout_url: string
  provider: string
  amount_cents: number
  currency: string
  plan_tier: string
  billing_interval: string
}

export interface OneTimeCheckoutSession {
  session_id: string
  checkout_url: string
  provider: string
  amount_cents: number
  currency: string
  reference_id: string
}

export interface Invoice {
  id: string
  invoice_number: string
  amount_cents: number
  currency: string
  status: 'paid' | 'open' | 'void'
  description: string
  paid_at?: string | null
  billing_name: string
  billing_email: string
  created_at: string
}

export interface Transaction {
  id: string
  user_id: string
  amount_cents: number
  currency: string
  status: string
  payment_type: string
  reference_id?: string | null
  provider: string
  idempotency_key: string
  created_at: string
}

export interface AdminBillingStats {
  total_revenue_cents: number
  active_subscriptions_count: number
  pro_subscriptions_count: number
  enterprise_subscriptions_count: number
  total_transactions_count: number
}
