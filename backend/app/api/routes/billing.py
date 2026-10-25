"""
FastAPI router for Payment Gateway, Subscriptions, Invoices, Quotas, and Webhooks.
Financial operations strictly enforce backend prices and integer minor-unit arithmetic.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import uuid

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.payment import (
    BillingInterval,
    Invoice,
    InvoiceStatus,
    PaymentTransaction,
    PaymentWebhookEvent,
    Subscription,
    SubscriptionStatus,
    SubscriptionTier,
    TransactionStatus,
)
from app.models.user import User
from app.schemas.billing import (
    AdminBillingStatsResponse,
    CheckoutSessionResponse,
    CreateCheckoutSessionRequest,
    CreateOneTimeCheckoutRequest,
    InvoiceResponse,
    OneTimeCheckoutResponse,
    PlanTierInfo,
    SimulateCheckoutCompletionRequest,
    SubscriptionResponse,
    TransactionResponse,
)
from app.security.dependencies import get_current_user, require_admin
from app.services.payment.payment_plans import PLAN_CATALOG, get_plan_price
from app.services.payment.payment_provider import PaymentProviderService
from app.services.payment.quota_service import QuotaService

router = APIRouter(prefix="/billing", tags=["Payments & Subscriptions"])
logger = structlog.get_logger(__name__)


@router.get(
    "/plans",
    response_model=List[PlanTierInfo],
    summary="List available SaaS subscription plan tiers",
)
async def list_plans() -> List[PlanTierInfo]:
    return list(PLAN_CATALOG.values())


@router.get(
    "/subscription",
    response_model=SubscriptionResponse,
    summary="Get current user subscription and quota usage",
)
async def get_my_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionResponse:
    sub = await QuotaService.get_or_create_subscription(db, current_user)
    target_count, scan_count = await QuotaService.get_usage_counts(db, current_user)

    res = SubscriptionResponse.model_validate(sub)
    res.current_target_count = target_count
    res.scans_used_this_month = scan_count

    if current_user.is_admin():
        # Authorized administrators possess full platform access without subscription requirements.
        # We reflect active status and unconstrained quotas without altering underlying historical records.
        res.plan_tier = "admin" if sub.plan_tier in ("free", "admin") else sub.plan_tier
        res.status = SubscriptionStatus.ACTIVE.value
        res.max_target_websites = 999999
        res.monthly_scan_limit = 999999
        res.reports_included_per_month = 999999

    return res


@router.post(
    "/checkout-session",
    response_model=CheckoutSessionResponse,
    summary="Initiate payment checkout session for a subscription plan",
)
async def create_checkout_session(
    payload: CreateCheckoutSessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CheckoutSessionResponse:
    tier = payload.plan_tier.lower()
    interval = payload.billing_interval.lower()

    if tier not in [SubscriptionTier.PRO.value, SubscriptionTier.ENTERPRISE.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Paid checkout is only available for 'pro' or 'enterprise' tiers.",
        )

    if interval not in [BillingInterval.MONTH.value, BillingInterval.YEAR.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Billing interval must be 'month' or 'year'.",
        )

    session_info = await PaymentProviderService.create_subscription_checkout_session(
        user_id=current_user.id,
        user_email=current_user.email,
        plan_tier=tier,
        billing_interval=interval,
        success_url=payload.success_url,
        cancel_url=payload.cancel_url,
    )

    return CheckoutSessionResponse(
        session_id=session_info["session_id"],
        checkout_url=session_info["checkout_url"],
        provider=session_info["provider"],
        amount_cents=session_info["amount_cents"],
        currency=session_info["currency"],
        plan_tier=tier,
        billing_interval=interval,
    )


@router.post(
    "/simulate-checkout-completion",
    response_model=SubscriptionResponse,
    summary="Fulfill sandbox checkout session (Development/Gateway workflow)",
)
async def simulate_checkout_completion(
    payload: SimulateCheckoutCompletionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionResponse:
    """
    Fulfills development sandbox checkout session.
    Enforces real backend pricing, minor-unit calculations, and records an authentic transaction and invoice.
    """
    sub = await QuotaService.get_or_create_subscription(db, current_user)

    # Determine plan from payload or parse format cs_sandbox_<tier>_<interval>_<id>
    requested_tier = SubscriptionTier.PRO.value
    requested_interval = BillingInterval.MONTH.value

    if payload.plan_tier and payload.plan_tier.lower() in [SubscriptionTier.PRO.value, SubscriptionTier.ENTERPRISE.value]:
        requested_tier = payload.plan_tier.lower()
    if payload.billing_interval and payload.billing_interval.lower() in [BillingInterval.MONTH.value, BillingInterval.YEAR.value]:
        requested_interval = payload.billing_interval.lower()

    parts = payload.session_id.split("_")
    if len(parts) >= 4 and parts[0] == "cs" and parts[1] == "sandbox":
        if parts[2] in [SubscriptionTier.PRO.value, SubscriptionTier.ENTERPRISE.value]:
            requested_tier = parts[2]
        if parts[3] in [BillingInterval.MONTH.value, BillingInterval.YEAR.value]:
            requested_interval = parts[3]

    price_cents = get_plan_price(requested_tier, requested_interval)
    idempotency_key = f"idem_chk_{payload.session_id}"

    # Check for duplicate transaction
    dup_stmt = select(PaymentTransaction).where(PaymentTransaction.idempotency_key == idempotency_key)
    dup_res = await db.execute(dup_stmt)
    if dup_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This checkout session has already been processed.",
        )

    if payload.outcome == "failed":
        tx = PaymentTransaction(
            user_id=current_user.id,
            subscription_id=sub.id,
            amount_cents=price_cents,
            currency="USD",
            status=TransactionStatus.FAILED.value,
            payment_type="subscription",
            reference_id=requested_tier,
            provider="dev_sandbox",
            idempotency_key=idempotency_key,
            failure_message="Simulated payment card authorization decline.",
        )
        db.add(tx)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Payment authorization declined by provider.",
        )

    # Succeeded outcome
    plan_info = PLAN_CATALOG[requested_tier]
    now = datetime.now(timezone.utc)
    period_end = now + (timedelta(days=365) if requested_interval == "year" else timedelta(days=30))

    sub.plan_tier = requested_tier
    sub.billing_interval = requested_interval
    sub.status = SubscriptionStatus.ACTIVE.value
    sub.price_cents = price_cents
    sub.current_period_start = now
    sub.current_period_end = period_end
    sub.max_target_websites = plan_info.max_target_websites
    sub.monthly_scan_limit = plan_info.monthly_scan_limit
    sub.reports_included_per_month = plan_info.reports_included_per_month
    sub.provider = "dev_sandbox"

    # Record successful transaction
    tx = PaymentTransaction(
        user_id=current_user.id,
        subscription_id=sub.id,
        amount_cents=price_cents,
        currency="USD",
        status=TransactionStatus.SUCCEEDED.value,
        payment_type="subscription",
        reference_id=requested_tier,
        provider="dev_sandbox",
        provider_payment_id=f"pi_sandbox_{uuid.uuid4().hex[:12]}",
        idempotency_key=idempotency_key,
        receipt_url=f"/dashboard/billing/invoices",
    )
    db.add(tx)

    # Generate itemized invoice
    invoice_desc = f"{plan_info.name} Subscription ({requested_interval.capitalize()}ly)"
    await QuotaService.create_invoice(
        db=db,
        user=current_user,
        amount_cents=price_cents,
        currency="USD",
        description=invoice_desc,
        subscription_id=sub.id,
    )

    await db.commit()
    await db.refresh(sub)

    target_count, scan_count = await QuotaService.get_usage_counts(db, current_user)
    res = SubscriptionResponse.model_validate(sub)
    res.current_target_count = target_count
    res.scans_used_this_month = scan_count

    if current_user.is_admin():
        # Authorized administrators possess full platform access without subscription requirements.
        # We reflect active status and unconstrained quotas without altering underlying historical records.
        res.plan_tier = "admin" if sub.plan_tier in ("free", "admin") else sub.plan_tier
        res.status = SubscriptionStatus.ACTIVE.value
        res.max_target_websites = 999999
        res.monthly_scan_limit = 999999
        res.reports_included_per_month = 999999

    return res


@router.post(
    "/onetime-checkout-session",
    response_model=OneTimeCheckoutResponse,
    summary="Initiate payment checkout session for a one-time purchase",
)
async def create_onetime_checkout_session(
    payload: CreateOneTimeCheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OneTimeCheckoutResponse:
    session_info = await PaymentProviderService.create_onetime_checkout_session(
        user_id=current_user.id,
        user_email=current_user.email,
        product_name=payload.product_name,
        amount_cents=payload.amount_cents,
        reference_id=payload.reference_id,
        success_url=payload.success_url,
        cancel_url=payload.cancel_url,
    )

    return OneTimeCheckoutResponse(
        session_id=session_info["session_id"],
        checkout_url=session_info["checkout_url"],
        provider=session_info["provider"],
        amount_cents=session_info["amount_cents"],
        currency=session_info["currency"],
        reference_id=payload.reference_id,
    )


@router.post(
    "/simulate-onetime-completion",
    response_model=TransactionResponse,
    summary="Fulfill sandbox one-time purchase checkout session",
)
async def simulate_onetime_completion(
    payload: SimulateCheckoutCompletionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TransactionResponse:
    idempotency_key = f"idem_onetime_{payload.session_id}"

    # Check for duplicate transaction
    dup_stmt = select(PaymentTransaction).where(PaymentTransaction.idempotency_key == idempotency_key)
    dup_res = await db.execute(dup_stmt)
    existing_tx = dup_res.scalar_one_or_none()
    if existing_tx:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This checkout session has already been processed.",
        )

    # Standard default one-time report price ($49.00 = 4900 cents)
    amount_cents = 4900
    product_name = "Detailed Vulnerability Report"

    if payload.outcome == "failed":
        tx = PaymentTransaction(
            user_id=current_user.id,
            amount_cents=amount_cents,
            currency="USD",
            status=TransactionStatus.FAILED.value,
            payment_type="one_time_purchase",
            reference_id=payload.session_id,
            provider="dev_sandbox",
            idempotency_key=idempotency_key,
            failure_message="Simulated one-time card payment decline.",
        )
        db.add(tx)
        await db.commit()
        await db.refresh(tx)
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Payment authorization declined by provider.",
        )

    # Succeeded
    tx = PaymentTransaction(
        user_id=current_user.id,
        amount_cents=amount_cents,
        currency="USD",
        status=TransactionStatus.SUCCEEDED.value,
        payment_type="one_time_purchase",
        reference_id=payload.session_id,
        provider="dev_sandbox",
        provider_payment_id=f"pi_sandbox_onetime_{uuid.uuid4().hex[:12]}",
        idempotency_key=idempotency_key,
        receipt_url="/dashboard/billing/invoices",
    )
    db.add(tx)

    # Create invoice for one-time purchase
    await QuotaService.create_invoice(
        db=db,
        user=current_user,
        amount_cents=amount_cents,
        currency="USD",
        description=f"One-Time Purchase: {product_name}",
        subscription_id=None,
    )

    await db.commit()
    await db.refresh(tx)
    return TransactionResponse.model_validate(tx)


@router.post(
    "/cancel-subscription",
    response_model=SubscriptionResponse,
    summary="Cancel active subscription renewal at end of current period",
)
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionResponse:
    sub = await QuotaService.get_or_create_subscription(db, current_user)
    if sub.plan_tier == SubscriptionTier.FREE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Community Free plan does not have an active subscription renewal.",
        )

    sub.cancel_at_period_end = True
    await db.commit()
    await db.refresh(sub)

    target_count, scan_count = await QuotaService.get_usage_counts(db, current_user)
    res = SubscriptionResponse.model_validate(sub)
    res.current_target_count = target_count
    res.scans_used_this_month = scan_count

    if current_user.is_admin():
        # Authorized administrators possess full platform access without subscription requirements.
        # We reflect active status and unconstrained quotas without altering underlying historical records.
        res.plan_tier = "admin" if sub.plan_tier in ("free", "admin") else sub.plan_tier
        res.status = SubscriptionStatus.ACTIVE.value
        res.max_target_websites = 999999
        res.monthly_scan_limit = 999999
        res.reports_included_per_month = 999999

    return res


@router.get(
    "/invoices",
    response_model=List[InvoiceResponse],
    summary="List client billing invoices",
)
async def list_my_invoices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[InvoiceResponse]:
    stmt = (
        select(Invoice)
        .where(Invoice.user_id == current_user.id)
        .order_by(desc(Invoice.created_at))
    )
    res = await db.execute(stmt)
    invoices = res.scalars().all()
    return [InvoiceResponse.model_validate(i) for i in invoices]


@router.get(
    "/invoices/{invoice_id}/download",
    summary="Download printable HTML invoice",
)
async def download_invoice(
    invoice_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    invoice = await db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found.")

    if invoice.user_id != current_user.id and not current_user.is_admin():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return Response(
        content=invoice.pdf_html_content,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="{invoice.invoice_number}.html"'},
    )


# ── Webhook Processing Endpoint ───────────────────────────────────────────────

@router.post(
    "/webhooks/stripe",
    summary="Cryptographically verified payment gateway webhook receiver",
)
async def handle_stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db),
):
    """
    Receives and processes payment gateway webhooks.
    Enforces cryptographic signature verification and deduplication against replay attacks.
    """
    body_bytes = await request.body()

    # 1. Cryptographic Signature Verification
    is_valid = PaymentProviderService.verify_webhook_signature(body_bytes, stripe_signature)
    if not is_valid:
        logger.warning("unauthorized_webhook_signature_rejected")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid cryptographic webhook signature.",
        )

    # 2. Parse Event JSON
    try:
        event_data = json.loads(body_bytes.decode("utf-8"))
        event_id = event_data.get("id", f"evt_{uuid.uuid4().hex[:12]}")
        event_type = event_data.get("type", "unknown")
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Malformed JSON payload.")

    # 3. Deduplication Check (Replay Attack Defense)
    existing_stmt = select(PaymentWebhookEvent).where(PaymentWebhookEvent.event_id == event_id)
    existing_res = await db.execute(existing_stmt)
    if existing_res.scalar_one_or_none():
        logger.info("webhook_event_already_processed", event_id=event_id)
        return {"status": "duplicate_ignored"}

    # 4. Record Webhook Event
    webhook_record = PaymentWebhookEvent(
        event_id=event_id,
        provider="stripe",
        event_type=event_type,
        payload_json=body_bytes.decode("utf-8"),
        processed=False,
    )
    db.add(webhook_record)
    await db.commit()

    # 5. Process Business Logic
    try:
        if event_type == "invoice.payment_succeeded":
            obj = event_data.get("data", {}).get("object", {})
            customer_email = obj.get("customer_email")
            amount_paid = obj.get("amount_paid", 0)

            # Match user by email
            if customer_email:
                user_res = await db.execute(select(User).where(User.email == customer_email))
                user = user_res.scalar_one_or_none()
                if user:
                    await QuotaService.create_invoice(
                        db=db,
                        user=user,
                        amount_cents=amount_paid,
                        currency="USD",
                        description="Stripe Automated Subscription Renewal",
                    )

        elif event_type == "customer.subscription.deleted":
            obj = event_data.get("data", {}).get("object", {})
            sub_id = obj.get("id")
            if sub_id:
                sub_res = await db.execute(select(Subscription).where(Subscription.provider_subscription_id == sub_id))
                sub_obj = sub_res.scalar_one_or_none()
                if sub_obj:
                    # Downgrade to Free plan
                    free_plan = PLAN_CATALOG[SubscriptionTier.FREE.value]
                    sub_obj.plan_tier = SubscriptionTier.FREE.value
                    sub_obj.status = SubscriptionStatus.CANCELED.value
                    sub_obj.max_target_websites = free_plan.max_target_websites
                    sub_obj.monthly_scan_limit = free_plan.monthly_scan_limit
                    await db.commit()

        webhook_record.processed = True
        webhook_record.processed_at = datetime.now(timezone.utc)
        await db.commit()

    except Exception as exc:
        webhook_record.error_message = str(exc)
        await db.commit()
        logger.error("webhook_processing_failure", event_id=event_id, error=str(exc))

    return {"status": "success", "event_id": event_id}


# ── Administrative Billing Oversight ──────────────────────────────────────────

@router.get(
    "/admin/stats",
    response_model=AdminBillingStatsResponse,
    summary="Get platform billing revenue and subscription statistics (Admin only)",
)
async def get_admin_billing_stats(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminBillingStatsResponse:
    # 1. Total revenue
    rev_stmt = select(func.sum(PaymentTransaction.amount_cents)).where(
        PaymentTransaction.status == TransactionStatus.SUCCEEDED.value
    )
    rev_res = await db.execute(rev_stmt)
    total_rev = rev_res.scalar_one() or 0

    # 2. Active subscriptions
    sub_stmt = select(func.count(Subscription.id)).where(
        Subscription.status == SubscriptionStatus.ACTIVE.value,
        Subscription.plan_tier != SubscriptionTier.FREE.value,
    )
    sub_res = await db.execute(sub_stmt)
    active_subs = sub_res.scalar_one() or 0

    # 3. Pro count
    pro_stmt = select(func.count(Subscription.id)).where(
        Subscription.plan_tier == SubscriptionTier.PRO.value,
        Subscription.status == SubscriptionStatus.ACTIVE.value,
    )
    pro_res = await db.execute(pro_stmt)
    pro_subs = pro_res.scalar_one() or 0

    # 4. Enterprise count
    ent_stmt = select(func.count(Subscription.id)).where(
        Subscription.plan_tier == SubscriptionTier.ENTERPRISE.value,
        Subscription.status == SubscriptionStatus.ACTIVE.value,
    )
    ent_res = await db.execute(ent_stmt)
    ent_subs = ent_res.scalar_one() or 0

    # 5. Transactions count
    tx_stmt = select(func.count(PaymentTransaction.id))
    tx_res = await db.execute(tx_stmt)
    total_tx = tx_res.scalar_one() or 0

    return AdminBillingStatsResponse(
        total_revenue_cents=total_rev,
        active_subscriptions_count=active_subs,
        pro_subscriptions_count=pro_subs,
        enterprise_subscriptions_count=ent_subs,
        total_transactions_count=total_tx,
    )


@router.get(
    "/admin/transactions",
    response_model=List[TransactionResponse],
    summary="List all payment transactions across clients (Admin only)",
)
async def admin_list_transactions(
    limit: int = Query(100, ge=1, le=200),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> List[TransactionResponse]:
    stmt = (
        select(PaymentTransaction)
        .order_by(desc(PaymentTransaction.created_at))
        .limit(limit)
    )
    res = await db.execute(stmt)
    txs = res.scalars().all()
    return [TransactionResponse.model_validate(t) for t in txs]
