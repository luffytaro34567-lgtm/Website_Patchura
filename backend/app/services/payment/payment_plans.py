"""
Static Catalog of SaaS Subscription Plans and Pricing.
All monetary amounts are strictly defined as integer minor-units (cents) to avoid binary floating-point inaccuracies.
"""
from __future__ import annotations

from typing import Dict
from app.models.payment import BillingInterval, SubscriptionTier
from app.schemas.billing import PlanTierInfo

PLAN_CATALOG: Dict[str, PlanTierInfo] = {
    SubscriptionTier.FREE.value: PlanTierInfo(
        tier=SubscriptionTier.FREE.value,
        name="Community Free",
        tag="Starter",
        monthly_price_cents=0,
        annual_price_cents=0,
        currency="USD",
        max_target_websites=1,
        monthly_scan_limit=3,
        reports_included_per_month=0,
        features=[
            "1 Verified Target Website",
            "3 Vulnerability Scans / Month",
            "Passive Header & TLS Inspection",
            "Free Finding-Count Summary",
            "Community Support",
        ],
    ),
    SubscriptionTier.PRO.value: PlanTierInfo(
        tier=SubscriptionTier.PRO.value,
        name="Pro Security",
        tag="Popular",
        monthly_price_cents=7900,     # $79.00 USD
        annual_price_cents=79000,     # $790.00 USD (2 months free)
        currency="USD",
        max_target_websites=10,
        monthly_scan_limit=999999,   # Unlimited
        reports_included_per_month=5,
        features=[
            "Up to 10 Verified Target Websites",
            "Unlimited Vulnerability Scans",
            "5 Detailed Reports Included / Month",
            "Full OWASP Top 10 Web Assessment",
            "PHP2Shell Zero-Day Deep Audit (CVE-2026-109618/19)",
            "Developer Code Remediation Playbooks",
            "Priority Scan Queue Execution",
        ],
    ),
    SubscriptionTier.ENTERPRISE.value: PlanTierInfo(
        tier=SubscriptionTier.ENTERPRISE.value,
        name="Enterprise Shield",
        tag="Mission Critical",
        monthly_price_cents=29900,    # $299.00 USD
        annual_price_cents=299000,    # $2,990.00 USD (2 months free)
        currency="USD",
        max_target_websites=999999,  # Unlimited
        monthly_scan_limit=999999,   # Unlimited
        reports_included_per_month=999999, # Unlimited
        features=[
            "Unlimited Target Websites",
            "Unlimited Vulnerability Scans",
            "Unlimited Detailed Reports & PDF Exports",
            "Continuous Scheduled Security Audits",
            "Instant Webhook Alert Dispatching",
            "Dedicated Application Security SLA",
            "Priority Support & Technical Reviews",
        ],
    ),
}


def get_plan_price(tier: str, interval: str) -> int:
    """Return backend-enforced price in cents. Never trust client-side prices."""
    plan = PLAN_CATALOG.get(tier)
    if not plan:
        raise ValueError(f"Unknown plan tier '{tier}'.")

    if interval == BillingInterval.YEAR.value:
        return plan.annual_price_cents
    return plan.monthly_price_cents
