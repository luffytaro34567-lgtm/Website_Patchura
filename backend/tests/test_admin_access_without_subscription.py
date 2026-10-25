"""
Regression and Integration Tests for Prompt 20:
PATCHORA Admin Access Without Subscription Requirements.

Verifies:
1. Authorized administrator with no subscription can access admin endpoints.
2. Authorized administrator with an expired or cancelled subscription retains admin access.
3. Administrator can perform permitted administrative operations without a paid plan.
4. Regular user without a subscription cannot access restricted paid features.
5. Regular user cannot access administrator endpoints.
6. A user cannot gain admin access by changing parameters, tokens, or subscription data.
7. Subscription billing and entitlement behavior for ordinary users remains unchanged.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.db.session import async_session_factory
from app.models.activity import SecurityAlert
from app.models.payment import Subscription, SubscriptionStatus, SubscriptionTier
from app.models.scan import Scan, ScanFinding, ScanStatus
from app.models.user import User, UserRole
from app.models.website import Website
from app.security.passwords import hash_password
from app.security.tokens import create_access_token


@pytest.fixture
async def admin_no_subscription() -> tuple[User, str]:
    """Creates an administrator account with NO entry in the subscriptions table."""
    unique_suffix = uuid.uuid4().hex[:6]
    admin = User(
        username=f"admin_nosub_{unique_suffix}",
        email=f"admin_nosub_{unique_suffix}@patchora.test",
        hashed_password=hash_password("AdminPass123!"),
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    async with async_session_factory() as db:
        db.add(admin)
        await db.commit()
        await db.refresh(admin)

    token = create_access_token(user_id=admin.id, role=admin.role)
    return admin, token


@pytest.fixture
async def admin_expired_subscription() -> tuple[User, str, Subscription]:
    """Creates an administrator account with an EXPIRED / CANCELLED subscription."""
    unique_suffix = uuid.uuid4().hex[:6]
    now = datetime.now(timezone.utc)
    admin = User(
        username=f"admin_expired_{unique_suffix}",
        email=f"admin_expired_{unique_suffix}@patchora.test",
        hashed_password=hash_password("AdminPass123!"),
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    async with async_session_factory() as db:
        db.add(admin)
        await db.commit()
        await db.refresh(admin)

        sub = Subscription(
            user_id=admin.id,
            plan_tier=SubscriptionTier.PRO.value,
            billing_interval="month",
            status=SubscriptionStatus.CANCELED.value,
            price_cents=7900,
            currency="USD",
            current_period_start=now - timedelta(days=60),
            current_period_end=now - timedelta(days=30),  # expired 30 days ago
            cancel_at_period_end=True,
            provider="test",
        )
        db.add(sub)
        await db.commit()
        await db.refresh(sub)

    token = create_access_token(user_id=admin.id, role=admin.role)
    return admin, token, sub


@pytest.fixture
async def regular_client() -> tuple[User, str]:
    """Creates an ordinary client account with no paid subscription."""
    unique_suffix = uuid.uuid4().hex[:6]
    client_user = User(
        username=f"client_{unique_suffix}",
        email=f"client_{unique_suffix}@example.com",
        hashed_password=hash_password("ClientPass123!"),
        role=UserRole.CLIENT.value,
        is_active=True,
    )
    async with async_session_factory() as db:
        db.add(client_user)
        await db.commit()
        await db.refresh(client_user)

    token = create_access_token(user_id=client_user.id, role=client_user.role)
    return client_user, token


# ──────────────────────────────────────────────────────────────────────────────
# Scenario 1: Admin with NO subscription accesses admin dashboard
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_with_no_subscription_accesses_dashboard(
    client: AsyncClient, admin_no_subscription: tuple[User, str]
):
    admin, token = admin_no_subscription
    headers = {"Authorization": f"Bearer {token}"}

    # Verify no subscription exists in database for this admin
    async with async_session_factory() as db:
        res = await db.execute(select(Subscription).where(Subscription.user_id == admin.id))
        assert res.scalar_one_or_none() is None

    # Overview endpoint
    overview_res = await client.get("/api/admin/overview", headers=headers)
    assert overview_res.status_code == 200, f"Expected 200, got {overview_res.status_code}: {overview_res.text}"
    data = overview_res.json()
    assert "total_users" in data
    assert "system_status" in data

    # Activity metrics endpoint
    metrics_res = await client.get("/api/admin/activity/metrics", headers=headers)
    assert metrics_res.status_code == 200

    # User management endpoint
    users_res = await client.get("/api/admin/users", headers=headers)
    assert users_res.status_code == 200

    # Websites directory endpoint
    sites_res = await client.get("/api/admin/websites", headers=headers)
    assert sites_res.status_code == 200

    # Scans directory endpoint
    scans_res = await client.get("/api/admin/scans", headers=headers)
    assert scans_res.status_code == 200


# ──────────────────────────────────────────────────────────────────────────────
# Scenario 2: Admin with EXPIRED/CANCELLED subscription retains admin access
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_with_expired_subscription_retains_access(
    client: AsyncClient, admin_expired_subscription: tuple[User, str, Subscription]
):
    admin, token, sub = admin_expired_subscription
    headers = {"Authorization": f"Bearer {token}"}

    # Admin access must succeed despite expired and canceled subscription
    overview_res = await client.get("/api/admin/overview", headers=headers)
    assert overview_res.status_code == 200

    audit_res = await client.get("/api/admin/audit-logs", headers=headers)
    assert audit_res.status_code == 200

    scans_res = await client.get("/api/admin/scans", headers=headers)
    assert scans_res.status_code == 200

    # Verify DB subscription record was preserved and NOT accidentally overwritten or deleted
    async with async_session_factory() as db:
        persisted = await db.get(Subscription, sub.id)
        assert persisted is not None
        assert persisted.status == SubscriptionStatus.CANCELED.value
        assert persisted.price_cents == 7900


# ──────────────────────────────────────────────────────────────────────────────
# Scenario 3: Admin performs administrative operations without a paid plan
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_performs_administrative_operations(
    client: AsyncClient, admin_no_subscription: tuple[User, str]
):
    admin, token = admin_no_subscription
    headers = {"Authorization": f"Bearer {token}"}

    async with async_session_factory() as db:
        # Create a test target website and a client
        client_u = User(
            username=f"target_client_{uuid.uuid4().hex[:6]}",
            email=f"target_{uuid.uuid4().hex[:6]}@test.com",
            hashed_password=hash_password("Pass123!"),
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        db.add(client_u)
        await db.commit()
        await db.refresh(client_u)

        site = Website(
            user_id=client_u.id,
            name="Suspected Target",
            target_url="https://admin-op-target.com",
            domain="admin-op-target.com",
            verification_method="file",
            verification_status="verified",
        )
        alert = SecurityAlert(
            alert_type="php2shell_detection",
            title="PHP2Shell Injection Pattern Detected",
            severity="critical",
            status="open",
            description="Re-entrancy in ob_start handler",
            source_module="scanner",
        )
        db.add_all([site, alert])
        await db.commit()
        await db.refresh(site)
        await db.refresh(alert)

    # Operation 1: Admin suspends a target website
    suspend_res = await client.patch(
        f"/api/admin/websites/{site.id}/suspend",
        headers=headers,
        json={"is_suspended": True, "suspension_reason": "Administrative safety audit"},
    )
    assert suspend_res.status_code == 200
    assert suspend_res.json()["is_suspended_by_admin"] is True

    # Operation 2: Admin triages a security alert
    triage_res = await client.patch(
        f"/api/admin/alerts/{alert.id}/triage",
        headers=headers,
        json={"status": "acknowledged", "resolution_notes": "Reviewed and acknowledged by sec lead."},
    )
    assert triage_res.status_code == 200
    assert triage_res.json()["status"] == "acknowledged"

    # Operation 3: Admin manages user status
    status_res = await client.patch(
        f"/api/admin/users/{client_u.id}/status",
        headers=headers,
        json={"is_active": False},
    )
    assert status_res.status_code == 200
    assert status_res.json()["is_active"] is False


# ──────────────────────────────────────────────────────────────────────────────
# Scenario 4: Regular user without subscription cannot access restricted features
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_regular_user_cannot_access_restricted_paid_features(
    client: AsyncClient, regular_client: tuple[User, str]
):
    user, token = regular_client
    headers = {"Authorization": f"Bearer {token}"}

    # Free plan target quota allows at most 1 website
    async with async_session_factory() as db:
        site1 = Website(
            user_id=user.id,
            name="Target 1",
            target_url="https://client-quota-target1.com",
            domain="client-quota-target1.com",
            verification_method="file",
            verification_status="verified",
        )
        db.add(site1)
        await db.commit()

    # Attempting to add 2nd target website on free tier must be blocked
    add_res = await client.post(
        "/api/websites",
        headers=headers,
        json={
            "name": "Target 2 Exceeding Free Quota",
            "target_url": "https://client-quota-target2.com",
            "verification_method": "file",
        },
    )
    assert add_res.status_code == 403
    assert "limit" in add_res.json().get("detail", "").lower() or "quota" in add_res.json().get("detail", "").lower()


# ──────────────────────────────────────────────────────────────────────────────
# Scenario 5: Regular user CANNOT access administrator endpoints
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_regular_user_cannot_access_admin_endpoints(
    client: AsyncClient, regular_client: tuple[User, str]
):
    _, token = regular_client
    headers = {"Authorization": f"Bearer {token}"}

    admin_endpoints = [
        ("GET", "/api/admin/overview"),
        ("GET", "/api/admin/users"),
        ("GET", "/api/admin/scans"),
        ("GET", "/api/admin/websites"),
        ("GET", "/api/admin/audit-logs"),
        ("GET", "/api/admin/activity/metrics"),
        ("GET", "/api/admin/alerts"),
        ("GET", "/api/billing/admin/stats"),
        ("GET", "/api/reports/admin/orders"),
    ]

    for method, path in admin_endpoints:
        if method == "GET":
            res = await client.get(path, headers=headers)
        assert res.status_code == 403, f"Expected 403 Forbidden for client accessing {path}, got {res.status_code}"


# ──────────────────────────────────────────────────────────────────────────────
# Scenario 6: User cannot elevate privileges via parameters, tokens, or subscription
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_privilege_escalation_is_prevented(
    client: AsyncClient, regular_client: tuple[User, str]
):
    client_user, _ = regular_client

    # 1. User fabricates a token with "role": "admin"
    tampered_token = create_access_token(user_id=client_user.id, role="admin")

    # Server must look up actual user in DB and reject because DB role is 'client'
    res = await client.get(
        "/api/admin/overview",
        headers={"Authorization": f"Bearer {tampered_token}"},
    )
    assert res.status_code == 403

    # 2. Even if a regular user purchases an Enterprise subscription, role stays 'client'
    async with async_session_factory() as db:
        enterprise_sub = Subscription(
            user_id=client_user.id,
            plan_tier=SubscriptionTier.ENTERPRISE.value,
            billing_interval="month",
            status=SubscriptionStatus.ACTIVE.value,
            price_cents=29900,
            currency="USD",
            current_period_start=datetime.now(timezone.utc),
            current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
            provider="test",
        )
        db.add(enterprise_sub)
        await db.commit()

    valid_client_token = create_access_token(user_id=client_user.id, role="client")
    res_enterprise_client = await client.get(
        "/api/admin/overview",
        headers={"Authorization": f"Bearer {valid_client_token}"},
    )
    assert res_enterprise_client.status_code == 403


# ──────────────────────────────────────────────────────────────────────────────
# Scenario 7: Subscription billing behavior for ordinary users remains unchanged
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ordinary_user_subscription_lifecycle_preserved(
    client: AsyncClient, regular_client: tuple[User, str]
):
    _, token = regular_client
    headers = {"Authorization": f"Bearer {token}"}

    # Initial subscription reflects Free tier
    sub_res = await client.get("/api/billing/subscription", headers=headers)
    assert sub_res.status_code == 200
    data = sub_res.json()
    assert data["plan_tier"] == "free"
    assert data["price_cents"] == 0

    # Regular user can start checkout session for Pro tier
    checkout_res = await client.post(
        "/api/billing/checkout-session",
        headers=headers,
        json={"plan_tier": "pro", "billing_interval": "month"},
    )
    assert checkout_res.status_code == 200
    session_data = checkout_res.json()
    assert session_data["plan_tier"] == "pro"
    assert "session_id" in session_data

    # Complete payment simulation
    fulfill_res = await client.post(
        "/api/billing/simulate-checkout-completion",
        headers=headers,
        json={"session_id": session_data["session_id"], "plan_tier": "pro"},
    )
    assert fulfill_res.status_code == 200
    updated_sub = fulfill_res.json()
    assert updated_sub["plan_tier"] == "pro"
    assert updated_sub["status"] == "active"
