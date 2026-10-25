"""
Comprehensive Automated Tests for AI Bug-Fixing Engine, Patch Generation,
Isolated Sandbox Verification, PHP2Shell Defense, and Human Approval.
"""
from __future__ import annotations

import pytest
from app.db.session import get_session_factory
from app.models.remediation import RemediationSession, RemediationStatus, TestStatus, ApprovalStatus
from app.models.scan import FindingSeverity, Scan, ScanFinding, ScanProfile, ScanStatus
from app.models.user import User, UserRole
from app.models.website import VerificationMethod, VerificationStatus, Website
from app.security.passwords import hash_password
from app.services.remediation.isolated_tester import IsolatedPatchTester


@pytest.fixture
async def setup_remediation_test_env(client):
    session_factory = get_session_factory()
    async with session_factory() as session:
        client_a = User(
            username="rem_client_a",
            email="rema@test.com",
            hashed_password=hash_password("ClientSecure123!"),
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        client_b = User(
            username="rem_client_b",
            email="remb@test.com",
            hashed_password=hash_password("ClientSecure123!"),
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        admin = User(
            username="rem_admin",
            email="rem_admin@bughunter.internal",
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
            domain="app-a.com",
            base_url="https://app-a.com",
            verification_status=VerificationStatus.VERIFIED.value,
            verification_token="token_a_123",
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
            target_url="https://app-a.com",
            target_domain="app-a.com",
            progress_percent=100,
            critical_count=1,
            high_count=1,
            total_findings=2,
        )
        session.add(scan_a)
        await session.commit()
        await session.refresh(scan_a)

        # 1. Standard finding: Missing HSTS Header
        finding_header = ScanFinding(
            scan_id=scan_a.id,
            website_id=site_a.id,
            title="Missing Strict-Transport-Security Header",
            severity=FindingSeverity.HIGH.value,
            category="Security Headers",
            description="The web server failed to return the HSTS security header.",
            evidence="Strict-Transport-Security header omitted from HTTP response.",
            remediation="Configure Strict-Transport-Security: max-age=63072000; includeSubDomains; preload",
            cwe_id="CWE-319",
            cvss_score=7.4,
            target_url="https://app-a.com",
        )

        # 2. PHP2Shell Zero-Day finding: CVE-2026-109618
        finding_php2shell = ScanFinding(
            scan_id=scan_a.id,
            website_id=site_a.id,
            title="PHP2Shell Memory Corruption via Custom Error Handler (CVE-2026-109618)",
            severity=FindingSeverity.CRITICAL.value,
            category="Remote Code Execution",
            description="Vulnerable PHP error handling leads to unauthenticated memory corruption.",
            evidence="PHP server disclosure and recursive custom error handler detected.",
            remediation="Disable display_errors and register bounded re-entrancy safe error handler.",
            cwe_id="CWE-119",
            cvss_score=9.2,
            target_url="https://app-a.com/index.php",
        )

        session.add_all([finding_header, finding_php2shell])
        await session.commit()
        await session.refresh(finding_header)
        await session.refresh(finding_php2shell)

    # Logins
    a_res = await client.post("/api/auth/login", json={"login": "rem_client_a", "password": "ClientSecure123!"})
    token_a = a_res.json()["access_token"]

    b_res = await client.post("/api/auth/login", json={"login": "rem_client_b", "password": "ClientSecure123!"})
    token_b = b_res.json()["access_token"]

    adm_res = await client.post("/api/auth/login", json={"login": "rem_admin", "password": "AdminSecure123!"})
    token_admin = adm_res.json()["access_token"]

    return {
        "client_a": client_a,
        "client_b": client_b,
        "admin": admin,
        "site_a": site_a,
        "scan_a": scan_a,
        "finding_header": finding_header,
        "finding_php2shell": finding_php2shell,
        "token_a": token_a,
        "token_b": token_b,
        "token_admin": token_admin,
    }


@pytest.mark.asyncio
async def test_remediation_request_requires_consent(client, setup_remediation_test_env):
    token_a = setup_remediation_test_env["token_a"]
    finding = setup_remediation_test_env["finding_header"]

    res = await client.post(
        "/api/remediations/request",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "finding_id": finding.id,
            "target_filename": "index.php",
            "language": "php",
            "source_code": "<?php echo 'Hello World'; ?>",
            "consent_acknowledged": False,
        },
    )
    assert res.status_code == 400
    assert "consent and terms" in res.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_remediation_generates_patch_and_diff(client, setup_remediation_test_env):
    token_a = setup_remediation_test_env["token_a"]
    finding = setup_remediation_test_env["finding_header"]

    code = "<?php\necho 'API Response';\n?>"
    res = await client.post(
        "/api/remediations/request",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "finding_id": finding.id,
            "input_method": "snippet",
            "target_filename": "index.php",
            "language": "php",
            "source_code": code,
            "consent_acknowledged": True,
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["status"] in ["test_passed", "patch_ready"]
    assert "Strict-Transport-Security" in data["patched_code"]
    assert "--- a/index.php" in data["proposed_diff"]
    assert "+++ b/index.php" in data["proposed_diff"]
    assert data["ai_provider"] == "deterministic_rules"
    assert data["test_status"] == "passed"
    assert data["approval_status"] == "pending"


@pytest.mark.asyncio
async def test_remediation_php2shell_defense(client, setup_remediation_test_env):
    token_a = setup_remediation_test_env["token_a"]
    finding_php2 = setup_remediation_test_env["finding_php2shell"]

    vulnerable_php = "<?php\n// Insecure script\nset_error_handler(function($e){ echo $e; });\n?>"
    res = await client.post(
        "/api/remediations/request",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "finding_id": finding_php2.id,
            "target_filename": "error_handler.php",
            "language": "php",
            "source_code": vulnerable_php,
            "consent_acknowledged": True,
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert "CVE-2026-109618" in data["php2shell_mitigation_notes"]
    assert "ini_set('display_errors', '0');" in data["patched_code"]
    assert "isHandling" in data["patched_code"]
    assert data["test_status"] == "passed"


@pytest.mark.asyncio
async def test_isolated_tester_blocks_malicious_code():
    original = "<?php echo 'safe'; ?>"
    malicious_patch = "<?php system($_GET['cmd']); echo 'safe'; ?>"
    diff = "--- a/safe.php\n+++ b/safe.php\n@@ -1 +1 @@\n-safe\n+system"

    res = IsolatedPatchTester.run_isolated_verification(
        filename="safe.php",
        language="php",
        original_code=original,
        patched_code=malicious_patch,
        proposed_diff=diff,
        finding_category="security",
        finding_title="Sample Finding",
    )
    assert res["passed"] is False
    assert "SECURITY ALERT" in res["diagnostics"]
    assert "Direct process execution" in res["diagnostics"]


@pytest.mark.asyncio
async def test_isolated_tester_detects_syntax_error():
    original = "def safe(): pass"
    broken_patch = "def safe(): unclosed bracket ("
    diff = "--- a/test.py\n+++ b/test.py\n@@ -1 +1 @@\n-safe\n+broken"

    res = IsolatedPatchTester.run_isolated_verification(
        filename="test.py",
        language="python",
        original_code=original,
        patched_code=broken_patch,
        proposed_diff=diff,
        finding_category="security",
        finding_title="Sample Python Finding",
    )
    assert res["passed"] is False
    assert res["test_status"] == "syntax_error"


@pytest.mark.asyncio
async def test_remediation_approval_workflow(client, setup_remediation_test_env):
    token_a = setup_remediation_test_env["token_a"]
    finding = setup_remediation_test_env["finding_header"]

    # 1. Create remediation
    create_res = await client.post(
        "/api/remediations/request",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "finding_id": finding.id,
            "target_filename": "headers.php",
            "language": "php",
            "source_code": "<?php echo 1; ?>",
            "consent_acknowledged": True,
        },
    )
    session_id = create_res.json()["id"]

    # 2. Approve patch
    appr_res = await client.post(
        f"/api/remediations/{session_id}/approve",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"approval_notes": "Reviewed and verified safe for staging."},
    )
    assert appr_res.status_code == 200
    assert appr_res.json()["approval_status"] == "approved"
    assert appr_res.json()["status"] == "approved"
    assert "Reviewed and verified" in appr_res.json()["approval_notes"]


@pytest.mark.asyncio
async def test_remediation_rejection_workflow(client, setup_remediation_test_env):
    token_a = setup_remediation_test_env["token_a"]
    finding = setup_remediation_test_env["finding_header"]

    # 1. Create remediation
    create_res = await client.post(
        "/api/remediations/request",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "finding_id": finding.id,
            "target_filename": "headers2.php",
            "language": "php",
            "source_code": "<?php echo 2; ?>",
            "consent_acknowledged": True,
        },
    )
    session_id = create_res.json()["id"]

    # 2. Reject patch
    rej_res = await client.post(
        f"/api/remediations/{session_id}/reject",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"rejection_reason": "Conflicts with custom internal reverse proxy headers."},
    )
    assert rej_res.status_code == 200
    assert rej_res.json()["approval_status"] == "rejected"
    assert "reverse proxy" in rej_res.json()["approval_notes"]


@pytest.mark.asyncio
async def test_download_patch_and_file(client, setup_remediation_test_env):
    token_a = setup_remediation_test_env["token_a"]
    finding = setup_remediation_test_env["finding_header"]

    create_res = await client.post(
        "/api/remediations/request",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "finding_id": finding.id,
            "target_filename": "script.php",
            "language": "php",
            "source_code": "<?php echo 3; ?>",
            "consent_acknowledged": True,
        },
    )
    session_id = create_res.json()["id"]

    # 1. Download .patch file
    patch_dl = await client.get(
        f"/api/remediations/{session_id}/download/patch",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert patch_dl.status_code == 200
    assert "--- a/script.php" in patch_dl.text
    assert "text/x-diff" in patch_dl.headers["content-type"]

    # 2. Download patched source file
    file_dl = await client.get(
        f"/api/remediations/{session_id}/download/file",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert file_dl.status_code == 200
    assert "Strict-Transport-Security" in file_dl.text


@pytest.mark.asyncio
async def test_remediation_multi_tenant_isolation(client, setup_remediation_test_env):
    token_a = setup_remediation_test_env["token_a"]
    token_b = setup_remediation_test_env["token_b"]
    finding = setup_remediation_test_env["finding_header"]

    # Client A creates remediation
    create_res = await client.post(
        "/api/remediations/request",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "finding_id": finding.id,
            "target_filename": "private.php",
            "language": "php",
            "source_code": "<?php echo 'private'; ?>",
            "consent_acknowledged": True,
        },
    )
    session_id = create_res.json()["id"]

    # Client B attempts to view Client A's session (403 Forbidden)
    get_res = await client.get(
        f"/api/remediations/{session_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert get_res.status_code == 403

    # Client B attempts to approve Client A's session (403 Forbidden)
    appr_res = await client.post(
        f"/api/remediations/{session_id}/approve",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"approval_notes": "Unauthorized approval attempt"},
    )
    assert appr_res.status_code == 403

    # Client B attempts to download Client A's patch (403 Forbidden)
    dl_res = await client.get(
        f"/api/remediations/{session_id}/download/patch",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert dl_res.status_code == 403


@pytest.mark.asyncio
async def test_admin_remediation_stats(client, setup_remediation_test_env):
    token_admin = setup_remediation_test_env["token_admin"]

    res = await client.get("/api/remediations/admin/stats", headers={"Authorization": f"Bearer {token_admin}"})
    assert res.status_code == 200
    data = res.json()
    assert "total_remediations" in data
    assert "approved_patches" in data
    assert "ai_provider_active" in data
