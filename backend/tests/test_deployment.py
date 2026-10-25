"""
Comprehensive Automated Tests for DevSecOps Source-Code Integration,
Git Pull Request Dispatches, Staging Deployments, Production Safety Gates, and Rollback.
"""
from __future__ import annotations

import pytest
from app.core.config import settings
from app.db.session import get_session_factory
from app.models.deployment import DeploymentRecord, DeploymentStatus, DeploymentTarget, RepositoryConnection
from app.models.remediation import ApprovalStatus, RemediationSession, RemediationStatus, TestStatus
from app.models.scan import FindingSeverity, Scan, ScanFinding, ScanProfile, ScanStatus
from app.models.user import User, UserRole
from app.models.website import VerificationMethod, VerificationStatus, Website
from app.security.passwords import hash_password


@pytest.fixture
async def setup_deployment_test_env(client):
    session_factory = get_session_factory()
    async with session_factory() as session:
        client_a = User(
            username="dep_client_a",
            email="depa@test.com",
            hashed_password=hash_password("ClientSecure123!"),
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        client_b = User(
            username="dep_client_b",
            email="depb@test.com",
            hashed_password=hash_password("ClientSecure123!"),
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        admin = User(
            username="dep_admin",
            email="dep_admin@bughunter.internal",
            hashed_password=hash_password("AdminSecure123!"),
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        session.add_all([client_a, client_b, admin])
        await session.commit()
        await session.refresh(client_a)
        await session.refresh(client_b)
        await session.refresh(admin)

        site_a = Website(
            user_id=client_a.id,
            domain="production-target.com",
            base_url="https://production-target.com",
            verification_status=VerificationStatus.VERIFIED.value,
            verification_token="token_dep_123",
            verification_method=VerificationMethod.META_TAG.value,
        )
        session.add(site_a)
        await session.commit()
        await session.refresh(site_a)

        scan_a = Scan(
            website_id=site_a.id,
            user_id=client_a.id,
            profile=ScanProfile.PHP_DEEP.value,
            status=ScanStatus.COMPLETED.value,
            target_url="https://production-target.com",
            target_domain="production-target.com",
        )
        session.add(scan_a)
        await session.commit()
        await session.refresh(scan_a)

        finding = ScanFinding(
            scan_id=scan_a.id,
            website_id=site_a.id,
            title="Missing Security Headers and Insecure Error Display",
            severity=FindingSeverity.HIGH.value,
            category="Security Headers",
            description="Missing HSTS and display_errors is enabled.",
            evidence="Header omitted from HTTP response.",
            remediation="Enforce headers and disable display_errors.",
            target_url="https://production-target.com",
        )
        session.add(finding)
        await session.commit()
        await session.refresh(finding)

        # 1. Approved & Tested remediation session
        approved_session = RemediationSession(
            finding_id=finding.id,
            scan_id=scan_a.id,
            website_id=site_a.id,
            user_id=client_a.id,
            input_method="snippet",
            target_filename="index.php",
            language="php",
            original_code="<?php echo 'unpatched'; ?>",
            patched_code="<?php header('Strict-Transport-Security: max-age=63072000;'); echo 'unpatched'; ?>",
            proposed_diff="--- a/index.php\n+++ b/index.php\n@@ -1 +1,2 @@\n+header('Strict-Transport-Security: max-age=63072000;');\n <?php echo 'unpatched'; ?>",
            status=RemediationStatus.APPROVED.value,
            test_status=TestStatus.PASSED.value,
            approval_status=ApprovalStatus.APPROVED.value,
            approval_notes="Approved by security officer.",
        )

        # 2. Unapproved remediation session
        unapproved_session = RemediationSession(
            finding_id=finding.id,
            scan_id=scan_a.id,
            website_id=site_a.id,
            user_id=client_a.id,
            input_method="snippet",
            target_filename="config.php",
            language="php",
            original_code="<?php $db = 'root'; ?>",
            patched_code="<?php $db = 'root'; ?>",
            proposed_diff="--- a/config.php\n+++ b/config.php",
            status=RemediationStatus.PENDING.value,
            test_status=TestStatus.UNTESTED.value,
            approval_status=ApprovalStatus.PENDING.value,
        )

        session.add_all([approved_session, unapproved_session])
        await session.commit()
        await session.refresh(approved_session)
        await session.refresh(unapproved_session)

    # Logins
    a_res = await client.post("/api/auth/login", json={"login": "dep_client_a", "password": "ClientSecure123!"})
    token_a = a_res.json()["access_token"]

    b_res = await client.post("/api/auth/login", json={"login": "dep_client_b", "password": "ClientSecure123!"})
    token_b = b_res.json()["access_token"]

    adm_res = await client.post("/api/auth/login", json={"login": "dep_admin", "password": "AdminSecure123!"})
    token_admin = adm_res.json()["access_token"]

    return {
        "client_a": client_a,
        "client_b": client_b,
        "admin": admin,
        "site_a": site_a,
        "finding": finding,
        "approved_session": approved_session,
        "unapproved_session": unapproved_session,
        "token_a": token_a,
        "token_b": token_b,
        "token_admin": token_admin,
    }


@pytest.mark.asyncio
async def test_connect_repository_masks_token(client, setup_deployment_test_env):
    token_a = setup_deployment_test_env["token_a"]

    res = await client.post(
        "/api/deployment/repositories",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "provider": "github",
            "repo_name": "acme/web-app",
            "default_branch": "main",
            "access_token": "ghp_secureToken123456789ABCDEF",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["repo_name"] == "acme/web-app"
    assert data["masked_token"].startswith("ghp_***")
    assert "ghp_secureToken123456789ABCDEF" not in data["masked_token"]


@pytest.mark.asyncio
async def test_create_deployment_target_defaults_production_disabled(client, setup_deployment_test_env):
    token_a = setup_deployment_test_env["token_a"]
    site_a = setup_deployment_test_env["site_a"]

    res = await client.post(
        "/api/deployment/targets",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "website_id": site_a.id,
            "name": "AWS Production Cluster",
            "environment": "production",
            "target_type": "webhook",
            "is_enabled": True,  # Attempts to enable
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["environment"] == "production"
    # Strict safety default: production is forced to disabled unless ENABLE_PRODUCTION_DEPLOYMENT=true
    assert data["is_enabled"] is False


@pytest.mark.asyncio
async def test_create_pull_request_requires_approved_patch(client, setup_deployment_test_env):
    token_a = setup_deployment_test_env["token_a"]
    unapproved = setup_deployment_test_env["unapproved_session"]

    # Connect repo first
    repo_res = await client.post(
        "/api/deployment/repositories",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"repo_name": "acme/web", "access_token": "ghp_1234567890"},
    )
    repo_id = repo_res.json()["id"]

    # Attempt to dispatch PR for unapproved session
    res = await client.post(
        "/api/deployment/create-pr",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "session_id": unapproved.id,
            "repository_id": repo_id,
        },
    )
    assert res.status_code == 400
    assert "Security Gate Violation" in res.json()["error"]["message"]


@pytest.mark.asyncio
async def test_create_pull_request_success(client, setup_deployment_test_env):
    token_a = setup_deployment_test_env["token_a"]
    approved = setup_deployment_test_env["approved_session"]

    # Connect repo
    repo_res = await client.post(
        "/api/deployment/repositories",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"repo_name": "acme/storefront", "access_token": "ghp_9876543210"},
    )
    repo_id = repo_res.json()["id"]

    res = await client.post(
        "/api/deployment/create-pr",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "session_id": approved.id,
            "repository_id": repo_id,
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "pr_created"
    assert "bughunter/patch-" in data["git_branch"]
    assert data["pull_request_url"] is not None
    assert data["git_commit_sha"] is not None


@pytest.mark.asyncio
async def test_deploy_to_staging(client, setup_deployment_test_env):
    token_a = setup_deployment_test_env["token_a"]
    approved = setup_deployment_test_env["approved_session"]

    res = await client.post(
        "/api/deployment/deploy-staging",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "session_id": approved.id,
            "notes": "Automated staging rollout",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["environment"] == "staging"
    assert data["status"] == "staged"


@pytest.mark.asyncio
async def test_deploy_to_production_blocks_without_token(client, setup_deployment_test_env):
    token_a = setup_deployment_test_env["token_a"]
    approved = setup_deployment_test_env["approved_session"]
    site_a = setup_deployment_test_env["site_a"]

    # Create target
    tgt_res = await client.post(
        "/api/deployment/targets",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"website_id": site_a.id, "name": "Prod Target", "environment": "production"},
    )
    tgt_id = tgt_res.json()["id"]

    # Mismatched confirmation token is blocked
    res = await client.post(
        "/api/deployment/deploy-production",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "session_id": approved.id,
            "target_id": tgt_id,
            "confirmation_token": "WRONG_TOKEN",
        },
    )
    assert res.status_code == 400
    assert "Safety confirmation token mismatch" in res.json()["error"]["message"]


@pytest.mark.asyncio
async def test_rollback_deployment(client, setup_deployment_test_env):
    token_a = setup_deployment_test_env["token_a"]
    approved = setup_deployment_test_env["approved_session"]

    # Stage deployment first
    stg_res = await client.post(
        "/api/deployment/deploy-staging",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"session_id": approved.id},
    )
    dep_id = stg_res.json()["id"]

    # Execute rollback
    roll_res = await client.post(
        f"/api/deployment/{dep_id}/rollback",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"reason": "Staging integration smoke test identified edge-case failure."},
    )
    assert roll_res.status_code == 200
    data = roll_res.json()
    assert data["status"] == "rolled_back"
    assert data["rollback_executed_at"] is not None


@pytest.mark.asyncio
async def test_cli_instructions_generation(client, setup_deployment_test_env):
    token_a = setup_deployment_test_env["token_a"]
    approved = setup_deployment_test_env["approved_session"]

    res = await client.get(
        f"/api/deployment/cli-instructions/{approved.id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "git apply" in data["git_apply_script"]
    assert "git checkout -b" in data["git_apply_script"]
    assert "Never merge directly into protected branches" in data["security_notice"]


@pytest.mark.asyncio
async def test_deployment_multi_tenant_isolation(client, setup_deployment_test_env):
    token_b = setup_deployment_test_env["token_b"]
    approved_a = setup_deployment_test_env["approved_session"]

    # Client B attempts to deploy Client A's approved patch (404/403)
    res = await client.post(
        "/api/deployment/deploy-staging",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"session_id": approved_a.id},
    )
    assert res.status_code in [403, 404]


@pytest.mark.asyncio
async def test_admin_deployment_overview(client, setup_deployment_test_env):
    token_admin = setup_deployment_test_env["token_admin"]

    res = await client.get("/api/deployment/admin/overview", headers={"Authorization": f"Bearer {token_admin}"})
    assert res.status_code == 200
    data = res.json()
    assert "total_connected_repositories" in data
    assert "production_deployments_enabled" in data
    assert "total_staging_deployments" in data
