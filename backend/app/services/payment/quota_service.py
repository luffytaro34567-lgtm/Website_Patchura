"""
Subscription Quota Enforcement and Invoice Generation Service.
Enforces website target limits and monthly scan quotas according to customer subscription tier.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import html
from typing import Optional, Tuple
import uuid

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import (
    BillingInterval,
    Invoice,
    InvoiceStatus,
    Subscription,
    SubscriptionStatus,
    SubscriptionTier,
)
from app.models.scan import Scan
from app.models.user import User
from app.models.website import Website
from app.services.payment.payment_plans import PLAN_CATALOG

logger = structlog.get_logger(__name__)


class QuotaService:
    @staticmethod
    async def get_or_create_subscription(db: AsyncSession, user: User) -> Subscription:
        """Retrieve existing subscription or provision default Free tier."""
        stmt = select(Subscription).where(Subscription.user_id == user.id)
        res = await db.execute(stmt)
        sub = res.scalar_one_or_none()

        if not sub:
            now = datetime.now(timezone.utc)
            free_plan = PLAN_CATALOG[SubscriptionTier.FREE.value]
            sub = Subscription(
                user_id=user.id,
                plan_tier=SubscriptionTier.FREE.value,
                billing_interval=BillingInterval.MONTH.value,
                status=SubscriptionStatus.ACTIVE.value,
                price_cents=0,
                currency="USD",
                current_period_start=now,
                current_period_end=now + timedelta(days=3650),  # Evergreen free tier
                max_target_websites=free_plan.max_target_websites,
                monthly_scan_limit=free_plan.monthly_scan_limit,
                reports_included_per_month=free_plan.reports_included_per_month,
                provider="sandbox",
            )
            db.add(sub)
            await db.commit()
            await db.refresh(sub)

        return sub

    @staticmethod
    async def can_add_target_website(db: AsyncSession, user: User) -> Tuple[bool, str]:
        """Check if client is permitted to register an additional target website under their plan quota."""
        if user.is_admin():
            return True, "Admin exemption"

        sub = await QuotaService.get_or_create_subscription(db, user)

        # Count current websites
        count_stmt = select(func.count(Website.id)).where(Website.user_id == user.id)
        res = await db.execute(count_stmt)
        current_count = res.scalar_one() or 0

        if current_count >= sub.max_target_websites:
            return (
                False,
                f"You have reached the target website limit for your {sub.plan_tier.capitalize()} plan "
                f"({current_count}/{sub.max_target_websites} websites). Upgrade to Pro to register up to 10 websites.",
            )

        return True, "Quota available"

    @staticmethod
    async def can_execute_scan(db: AsyncSession, user: User) -> Tuple[bool, str]:
        """Check if client has remaining monthly scans under their subscription quota."""
        if user.is_admin():
            return True, "Admin exemption"

        sub = await QuotaService.get_or_create_subscription(db, user)

        if sub.monthly_scan_limit >= 999999:
            return True, "Unlimited quota"

        # Count scans performed in current month
        now = datetime.now(timezone.utc)
        start_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

        count_stmt = select(func.count(Scan.id)).where(
            Scan.user_id == user.id,
            Scan.created_at >= start_of_month,
        )
        res = await db.execute(count_stmt)
        scans_this_month = res.scalar_one() or 0

        if scans_this_month >= sub.monthly_scan_limit:
            return (
                False,
                f"Monthly scan limit reached for your {sub.plan_tier.capitalize()} plan "
                f"({scans_this_month}/{sub.monthly_scan_limit} scans this month). "
                f"Upgrade to Pro Security for unlimited vulnerability scans.",
            )

        return True, "Quota available"

    @staticmethod
    async def get_usage_counts(db: AsyncSession, user: User) -> Tuple[int, int]:
        """Return (target_count, scans_used_this_month)."""
        target_res = await db.execute(select(func.count(Website.id)).where(Website.user_id == user.id))
        target_count = target_res.scalar_one() or 0

        now = datetime.now(timezone.utc)
        start_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        scan_res = await db.execute(
            select(func.count(Scan.id)).where(Scan.user_id == user.id, Scan.created_at >= start_of_month)
        )
        scan_count = scan_res.scalar_one() or 0

        return target_count, scan_count

    @staticmethod
    async def create_invoice(
        db: AsyncSession,
        user: User,
        amount_cents: int,
        currency: str,
        description: str,
        subscription_id: Optional[str] = None,
    ) -> Invoice:
        """Generates an immutable invoice record with self-contained printable HTML."""
        invoice_num = f"INV-2026-BH-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc)

        amount_decimal = amount_cents / 100.0

        # XSS defense: HTML-escape user-controlled content
        safe_user_name = html.escape(user.username, quote=True)
        safe_user_email = html.escape(user.email, quote=True)
        safe_description = html.escape(description, quote=True)
        safe_currency = html.escape(currency, quote=True)
        safe_invoice_num = html.escape(invoice_num, quote=True)

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; font-src 'none'; img-src data:; script-src 'none'; frame-ancestors 'none';">
    <meta http-equiv="X-Content-Type-Options" content="nosniff">
    <title>PATCHORA Invoice — {safe_invoice_num}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #0f172a; padding: 40px; margin: 0; }}
        .header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #0f172a; padding-bottom: 20px; margin-bottom: 30px; }}
        .paid-stamp {{ display: inline-block; padding: 6px 14px; background: #ecfdf5; border: 2px solid #059669; color: #059669; font-weight: bold; font-size: 14px; border-radius: 6px; text-transform: uppercase; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 25px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
        th {{ background: #f8fafc; font-size: 12px; text-transform: uppercase; color: #64748b; }}
        .total-row td {{ font-weight: bold; font-size: 16px; border-top: 2px solid #0f172a; }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1 style="margin: 0; font-size: 24px; color: #0f172a;">PATCHORA</h1>
            <p style="margin: 4px 0 0 0; color: #64748b; font-size: 13px;">AI Vulnerability Assessment & Remediation SaaS</p>
        </div>
        <div style="text-align: right;">
            <div class="paid-stamp">PAID</div>
            <p style="margin: 6px 0 0 0; font-size: 12px; font-family: monospace;">Invoice: {safe_invoice_num}</p>
            <p style="margin: 2px 0 0 0; font-size: 12px; color: #64748b;">Date: {now.strftime('%Y-%m-%d')}</p>
        </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; font-size: 13px;">
        <div>
            <strong style="color: #64748b; text-transform: uppercase; font-size: 11px;">Billed To:</strong><br/>
            <strong>{safe_user_name}</strong><br/>
            {safe_user_email}<br/>
            Client ID: {user.id[:8]}...
        </div>
        <div style="text-align: right;">
            <strong style="color: #64748b; text-transform: uppercase; font-size: 11px;">Provider:</strong><br/>
            PATCHORA Inc.<br/>
            Zero-Day Threat Defense Division<br/>
            billing@patchora.io
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Description</th>
                <th style="text-align: center;">Qty</th>
                <th style="text-align: right;">Amount ({safe_currency})</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>{safe_description}</strong></td>
                <td style="text-align: center;">1</td>
                <td style="text-align: right; font-family: monospace;">${amount_decimal:.2f}</td>
            </tr>
            <tr class="total-row">
                <td colspan="2">Total Paid</td>
                <td style="text-align: right; font-family: monospace;">${amount_decimal:.2f} {safe_currency}</td>
            </tr>
        </tbody>
    </table>

    <div style="margin-top: 50px; text-align: center; color: #94a3b8; font-size: 11px;">
        Thank you for choosing PATCHORA. For billing questions contact billing@patchora.io.
    </div>
</body>
</html>"""

        invoice = Invoice(
            user_id=user.id,
            subscription_id=subscription_id,
            invoice_number=invoice_num,
            amount_cents=amount_cents,
            currency=currency,
            status=InvoiceStatus.PAID.value,
            description=description,
            paid_at=now,
            billing_name=user.username,
            billing_email=user.email,
            pdf_html_content=html_content,
        )
        db.add(invoice)
        await db.commit()
        await db.refresh(invoice)
        return invoice
