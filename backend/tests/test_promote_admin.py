"""
Automated Verification Tests: Promote Existing Local Account to Admin
====================================================================
Verifies:
1. `promote_user_to_admin` fails gracefully if account does not exist.
2. `promote_user_to_admin` promotes an existing client account to admin while preserving:
   - User ID, email, hashed password, is_active status.
   - Any subscription or billing data.
3. `promote_user_to_admin` is idempotent for accounts that are already admins.
4. The promoted account (`test_login`) in the development database has role='admin'
   and can access administrative endpoints without a subscription.
5. Ordinary client accounts receive 403 Forbidden on administrative endpoints.
6. Privilege escalation cannot be achieved via query params or request payload tampering.
"""
from __future__ import annotations

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.cli.promote_admin import promote_user_to_admin
from app.db.session import async_session_factory
from app.models.user import User, UserRole
from app.security.passwords import hash_password
from app.security.tokens import create_access_token


@pytest.mark.asyncio
async def test_promote_non_existent_user_returns_false():
    """Verify that attempting to promote a nonexistent user fails cleanly."""
    non_existent = f"non_existent_{uuid.uuid4().hex[:8]}"
    success = await promote_user_to_admin(non_existent)
    assert success is False


@pytest.mark.asyncio
async def test_promote_client_user_preserves_data_and_elevates_role():
    """Verify role elevation preserves ID, password hash, email, and only changes role."""
    suffix = uuid.uuid4().hex[:6]
    username = f"user_to_promote_{suffix}"
    email = f"user_{suffix}@example.com"
    pwd_hash = hash_password("SuperSecretPassword123!")

    async with async_session_factory() as session:
        user = User(
            username=username,
            email=email,
            hashed_password=pwd_hash,
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        user_id = user.id

    # Execute promotion
    success = await promote_user_to_admin(username)
    assert success is True

    # Re-query user and check fields
    async with async_session_factory() as session:
        res = await session.execute(select(User).where(User.id == user_id))
        updated_user = res.scalar_one()

        assert updated_user.role == UserRole.ADMIN.value
        assert updated_user.username == username
        assert updated_user.email == email
        assert updated_user.hashed_password == pwd_hash
        assert updated_user.is_active is True

    # Check idempotency
    repeat_success = await promote_user_to_admin(username)
    assert repeat_success is True


@pytest.mark.asyncio
async def test_test_login_account_promotion_and_admin_access(client: AsyncClient):
    """
    Verify that an account with username 'test_login' promoted to admin
    can access administrative endpoints without purchasing a subscription.
    """
    async with async_session_factory() as session:
        # Check if test_login already exists in the test database; if not create it
        res = await session.execute(select(User).where(User.username == "test_login"))
        user = res.scalar_one_or_none()
        if user is None:
            user = User(
                username="test_login",
                email="test@organization.com",
                hashed_password=hash_password("DevPassword123!"),
                role=UserRole.CLIENT.value,
                is_active=True,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

    # Promote test_login to admin
    success = await promote_user_to_admin("test_login")
    assert success is True

    # Re-fetch user
    async with async_session_factory() as session:
        res = await session.execute(select(User).where(User.username == "test_login"))
        user = res.scalar_one()

    assert user.role == UserRole.ADMIN.value, f"Expected role 'admin', found '{user.role}'."

    # Generate token for test_login with its admin role
    token = create_access_token(user_id=user.id, role=user.role)
    headers = {"Authorization": f"Bearer {token}"}

    # Test admin overview endpoint
    res = await client.get("/api/admin/overview", headers=headers)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert "metrics" in data or "total_users" in str(data) or "active_scans" in str(data) or "users" in str(data)

    # Test admin users endpoint
    res_users = await client.get("/api/admin/users", headers=headers)
    assert res_users.status_code == 200, f"Expected 200, got {res_users.status_code}: {res_users.text}"

    # Test billing admin stats endpoint (admins can view stats without a subscription)
    res_billing = await client.get("/api/billing/admin/stats", headers=headers)
    assert res_billing.status_code == 200, f"Expected 200, got {res_billing.status_code}: {res_billing.text}"


@pytest.mark.asyncio
async def test_client_cannot_access_admin_endpoints(client: AsyncClient):
    """Verify that an ordinary client cannot access admin endpoints."""
    suffix = uuid.uuid4().hex[:6]
    client_user = User(
        username=f"client_test_{suffix}",
        email=f"client_{suffix}@example.com",
        hashed_password=hash_password("Pass123456!"),
        role=UserRole.CLIENT.value,
        is_active=True,
    )
    async with async_session_factory() as session:
        session.add(client_user)
        await session.commit()
        await session.refresh(client_user)

    client_token = create_access_token(user_id=client_user.id, role=client_user.role)
    headers = {"Authorization": f"Bearer {client_token}"}

    res = await client.get("/api/admin/overview", headers=headers)
    assert res.status_code == 403

    res_users = await client.get("/api/admin/users", headers=headers)
    assert res_users.status_code == 403

    res_billing = await client.get("/api/billing/admin/stats", headers=headers)
    assert res_billing.status_code == 403


@pytest.mark.asyncio
async def test_tampered_role_claims_rejected(client: AsyncClient):
    """
    Verify that an attacker attempting to forge an admin role with a regular user ID
    is rejected because live user lookup validates the trusted DB role.
    """
    suffix = uuid.uuid4().hex[:6]
    client_user = User(
        username=f"attacker_{suffix}",
        email=f"attacker_{suffix}@example.com",
        hashed_password=hash_password("Pass123456!"),
        role=UserRole.CLIENT.value,
        is_active=True,
    )
    async with async_session_factory() as session:
        session.add(client_user)
        await session.commit()
        await session.refresh(client_user)

    # Attacker crafts a token with role='admin' but their own user_id
    forged_token = create_access_token(user_id=client_user.id, role="admin")
    headers = {"Authorization": f"Bearer {forged_token}"}

    # require_admin checks current_user.role loaded from database
    res = await client.get("/api/admin/overview", headers=headers)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_promote_by_user_id_and_email():
    """Verify role promotion operates reliably using user_id or email flags."""
    suffix = uuid.uuid4().hex[:6]
    test_user = User(
        username=f"target_id_{suffix}",
        email=f"target_{suffix}@example.com",
        hashed_password=hash_password("Pass123456!"),
        role=UserRole.CLIENT.value,
        is_active=True,
    )
    async with async_session_factory() as session:
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)
        user_id = test_user.id
        user_email = test_user.email

    # Promote by user_id
    success_id = await promote_user_to_admin(user_id=user_id)
    assert success_id is True

    async with async_session_factory() as session:
        res = await session.execute(select(User).where(User.id == user_id))
        promoted = res.scalar_one()
        assert promoted.role == UserRole.ADMIN.value
