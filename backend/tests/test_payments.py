"""
Comprehensive Tests for Payment Gateway, Subscriptions, Invoices, Quotas,
Webhooks Cryptographic Verification, and Idempotency Protection.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time

import pytest
from app.core.config import settings
from app.db.session import get_session_factory
from app.models.payment import Invoice, PaymentTransaction, Subscription, SubscriptionStatus, SubscriptionTier
from app.models.user import User, UserRole
from app.models.website import VerificationStatus, Website
from app.security.passwords import hash_password


@pytest.fixture
async def setup_billing_test_env(client):
    session_factory = get_session_factory()
    async with session_factory() as session:
        client_a = User(
            username="bill_client_a",
            email="billa@test.com",
            hashed_password=hash_password("ClientSecure123!"),
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        client_b = User(
            username="bill_client_b",
            email="billb@test.com",
            hashed_password=hash_password("ClientSecure123!"),
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        admin = User(
            username="bill_admin",
            email="bill_admin@bughunter.internal",
            hashed_password=hash_password("AdminSecure123!"),
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        session.add_all([client_a, client_b, admin])
        await session.commit()
        await session.refresh(client_a)
        await session.refresh(client_b)
        await session.refresh(admin)

    # Logins
    a_res = await client.post("/api/auth/login", json={"login": "bill_client_a", "password": "ClientSecure123!"})
    token_a = a_res.json()["access_token"]

    b_res = await client.post("/api/auth/login", json={"login": "bill_client_b", "password": "ClientSecure123!"})
    token_b = b_res.json()["access_token"]

    adm_res = await client.post("/api/auth/login", json={"login": "bill_admin", "password": "AdminSecure123!"})
    token_admin = adm_res.json()["access_token"]

    return {
        "client_a": client_a,
        "client_b": client_b,
        "admin": admin,
        "token_a": token_a,
        "token_b": token_b,
        "token_admin": token_admin,
    }


@pytest.mark.asyncio
async def test_list_plans_enforces_minor_unit_pricing(client):
    res = await client.get("/api/billing/plans")
    assert res.status_code == 200
    plans = res.json()
    assert len(plans) == 3

    free_plan = next(p for p in plans if p["tier"] == "free")
    assert free_plan["monthly_price_cents"] == 0
    assert free_plan["max_target_websites"] == 1

    pro_plan = next(p for p in plans if p["tier"] == "pro")
    assert pro_plan["monthly_price_cents"] == 7900  # $79.00 USD
    assert pro_plan["annual_price_cents"] == 79000  # $790.00 USD
    assert pro_plan["max_target_websites"] == 10

    ent_plan = next(p for p in plans if p["tier"] == "enterprise")
    assert ent_plan["monthly_price_cents"] == 29900  # $299.00 USD


@pytest.mark.asyncio
async def test_subscription_auto_provision_free_tier(client, setup_billing_test_env):
    token_a = setup_billing_test_env["token_a"]

    res = await client.get("/api/billing/subscription", headers={"Authorization": f"Bearer {token_a}"})
    assert res.status_code == 200
    data = res.json()
    assert data["plan_tier"] == "free"
    assert data["status"] == "active"
    assert data["max_target_websites"] == 1
    assert data["monthly_scan_limit"] == 3


@pytest.mark.asyncio
async def test_quota_enforcement_blocks_excess_targets_on_free_tier(client, setup_billing_test_env):
    token_a = setup_billing_test_env["token_a"]

    # 1. Register 1st website target (Allowed on Free tier)
    res1 = await client.post(
        "/api/websites",
        json={"name": "First Target", "target_url": "https://first-target.com", "verification_method": "file"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res1.status_code == 201

    # 2. Register 2nd website target (Blocked: Free tier allows only 1)
    res2 = await client.post(
        "/api/websites",
        json={"name": "Second Target", "target_url": "https://second-target.com", "verification_method": "file"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res2.status_code == 403
    assert "target website limit" in res2.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_checkout_session_and_upgrade_to_pro(client, setup_billing_test_env):
    token_a = setup_billing_test_env["token_a"]

    # 1. Create checkout session
    sess_res = await client.post(
        "/api/billing/checkout-session",
        json={"plan_tier": "pro", "billing_interval": "month"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert sess_res.status_code == 200
    sess_data = sess_res.json()
    assert sess_data["amount_cents"] == 7900
    assert sess_data["session_id"].startswith("cs_")
    session_id = sess_data["session_id"]

    # 2. Complete checkout session
    comp_res = await client.post(
        "/api/billing/simulate-checkout-completion",
        json={"session_id": session_id, "outcome": "succeeded"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert comp_res.status_code == 200
    updated_sub = comp_res.json()
    assert updated_sub["plan_tier"] == "pro"
    assert updated_sub["max_target_websites"] == 10

    # 3. Verify an invoice was automatically generated
    inv_res = await client.get("/api/billing/invoices", headers={"Authorization": f"Bearer {token_a}"})
    assert inv_res.status_code == 200
    invoices = inv_res.json()
    assert len(invoices) >= 1
    assert invoices[0]["amount_cents"] == 7900
    assert invoices[0]["status"] == "paid"

    # 4. Idempotency test: reprocessing same session must be rejected
    dup_res = await client.post(
        "/api/billing/simulate-checkout-completion",
        json={"session_id": session_id, "outcome": "succeeded"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert dup_res.status_code == 400
    assert "already been processed" in dup_res.json()["error"]["message"].lower()

    # 5. Customer can now register second website (since Pro tier limit is 10)
    res_allowed = await client.post(
        "/api/websites",
        json={"name": "Second Target Pro", "target_url": "https://second-target.com", "verification_method": "file"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_allowed.status_code == 201


@pytest.mark.asyncio
async def test_webhook_cryptographic_verification_and_replay_defense(client):
    secret = settings.STRIPE_WEBHOOK_SECRET or settings.SECRET_KEY
    now = int(time.time())

    payload = json.dumps({
        "id": "evt_test_unique_12345",
        "type": "invoice.payment_succeeded",
        "data": {
            "object": {
                "customer_email": "customer@example.com",
                "amount_paid": 7900,
            }
        }
    }).encode("utf-8")

    # 1. Invalid signature is rejected (400)
    bad_res = await client.post(
        "/api/billing/webhooks/stripe",
        content=payload,
        headers={"Stripe-Signature": "t=12345,v1=bad_hash", "Content-Type": "application/json"},
    )
    assert bad_res.status_code == 400

    # 2. Valid signature is accepted
    signed_payload = f"{now}.".encode() + payload
    valid_sig = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    sig_header = f"t={now},v1={valid_sig}"

    good_res = await client.post(
        "/api/billing/webhooks/stripe",
        content=payload,
        headers={"Stripe-Signature": sig_header, "Content-Type": "application/json"},
    )
    assert good_res.status_code == 200
    assert good_res.json()["status"] == "success"

    # 3. Replay attack with same event ID is deduplicated
    replay_res = await client.post(
        "/api/billing/webhooks/stripe",
        content=payload,
        headers={"Stripe-Signature": sig_header, "Content-Type": "application/json"},
    )
    assert replay_res.status_code == 200
    assert replay_res.json()["status"] == "duplicate_ignored"


@pytest.mark.asyncio
async def test_invoice_download_and_client_isolation(client, setup_billing_test_env):
    token_a = setup_billing_test_env["token_a"]
    token_b = setup_billing_test_env["token_b"]
    user_a = setup_billing_test_env["client_a"]

    # Create invoice for user A in DB
    session_factory = get_session_factory()
    async with session_factory() as session:
        inv = Invoice(
            user_id=user_a.id,
            invoice_number="INV-2026-BH-TESTISOLATION",
            amount_cents=7900,
            currency="USD",
            status="paid",
            description="Pro Security Monthly",
            billing_name="User A",
            billing_email="billa@test.com",
            pdf_html_content="<html><body>Paid Invoice</body></html>",
        )
        session.add(inv)
        await session.commit()
        await session.refresh(inv)
        inv_id = inv.id

    # User A can download invoice
    dl_res = await client.get(f"/api/billing/invoices/{inv_id}/download", headers={"Authorization": f"Bearer {token_a}"})
    assert dl_res.status_code == 200
    assert "Paid Invoice" in dl_res.text

    # User B cannot download User A's invoice (403 Forbidden)
    denied_res = await client.get(f"/api/billing/invoices/{inv_id}/download", headers={"Authorization": f"Bearer {token_b}"})
    assert denied_res.status_code == 403


@pytest.mark.asyncio
async def test_admin_billing_stats(client, setup_billing_test_env):
    token_admin = setup_billing_test_env["token_admin"]

    res = await client.get("/api/billing/admin/stats", headers={"Authorization": f"Bearer {token_admin}"})
    assert res.status_code == 200
    data = res.json()
    assert "total_revenue_cents" in data
    assert "active_subscriptions_count" in data


@pytest.mark.asyncio
async def test_onetime_checkout_and_fulfillment(client, setup_billing_test_env):
    token_a = setup_billing_test_env["token_a"]

    # 1. Initiate one-time checkout session
    create_res = await client.post(
        "/api/billing/onetime-checkout-session",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "product_name": "Detailed Vulnerability Report",
            "amount_cents": 4900,
            "reference_id": "ORD-BH-TEST-999",
        },
    )
    assert create_res.status_code == 200
    sess_data = create_res.json()
    assert sess_data["amount_cents"] == 4900
    assert sess_data["currency"] == "USD"
    session_id = sess_data["session_id"]

    # 2. Complete one-time checkout session
    comp_res = await client.post(
        "/api/billing/simulate-onetime-completion",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "session_id": session_id,
            "outcome": "succeeded",
        },
    )
    assert comp_res.status_code == 200
    tx_data = comp_res.json()
    assert tx_data["amount_cents"] == 4900
    assert tx_data["status"] == "succeeded"
    assert tx_data["payment_type"] == "one_time_purchase"

    # 3. Duplicate completion is rejected by idempotency check
    dup_res = await client.post(
        "/api/billing/simulate-onetime-completion",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "session_id": session_id,
            "outcome": "succeeded",
        },
    )
    assert dup_res.status_code == 400
