"""
Automated Test Suite for Client Finder Automation, Lead Discovery,
Compliant Outreach, Suppression List Enforcement, and Lead Conversion.
"""
from __future__ import annotations

import pytest
from app.db.session import get_session_factory
from app.models.lead import (
    DiscoveryCampaign,
    Lead,
    LeadStatus,
    OutreachDraft,
    OutreachStatus,
    RiskLevel,
    SuppressionList,
)
from app.models.user import User, UserRole
from app.security.passwords import hash_password


@pytest.fixture
async def setup_lead_finder_test_env(client):
    session_factory = get_session_factory()
    async with session_factory() as session:
        admin = User(
            username="lead_admin",
            email="lead_admin@bughunter.internal",
            hashed_password=hash_password("AdminSecure123!"),
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        regular_client = User(
            username="regular_client_1",
            email="client1@test.com",
            hashed_password=hash_password("ClientSecure123!"),
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        session.add_all([admin, regular_client])
        await session.commit()
        await session.refresh(admin)
        await session.refresh(regular_client)

        # Pre-seed campaign
        campaign = DiscoveryCampaign(
            created_by_admin_id=admin.id,
            name="PHP2Shell Vulnerability Awareness - Q4",
            target_technology="PHP 8.1 / Laravel",
            search_query="php error disclosure",
        )
        session.add(campaign)
        await session.commit()
        await session.refresh(campaign)

    # Logins
    adm_res = await client.post("/api/auth/login", json={"login": "lead_admin", "password": "AdminSecure123!"})
    token_admin = adm_res.json()["access_token"]

    cli_res = await client.post("/api/auth/login", json={"login": "regular_client_1", "password": "ClientSecure123!"})
    token_client = cli_res.json()["access_token"]

    return {
        "admin": admin,
        "client": regular_client,
        "campaign": campaign,
        "token_admin": token_admin,
        "token_client": token_client,
    }


@pytest.mark.asyncio
async def test_client_forbidden_from_client_finder(client, setup_lead_finder_test_env):
    token_client = setup_lead_finder_test_env["token_client"]

    # Regular client cannot access lead stats (403 Forbidden)
    res = await client.get("/api/leads/stats", headers={"Authorization": f"Bearer {token_client}"})
    assert res.status_code == 403

    # Regular client cannot list leads
    res = await client.get("/api/leads", headers={"Authorization": f"Bearer {token_client}"})
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_admin_creates_manual_lead(client, setup_lead_finder_test_env):
    token_admin = setup_lead_finder_test_env["token_admin"]

    res = await client.post(
        "/api/leads",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={
            "company_name": "Globex Retail Corp",
            "domain": "globex-retail.com",
            "website_url": "https://globex-retail.com",
            "contact_name": "Hank Scorpio",
            "contact_email": "hank@globex-retail.com",
            "contact_title": "CTO",
            "technology_stack": "PHP 8.2, Nginx, MySQL",
            "php2shell_risk_level": "critical",
            "notes": "Target runs PHP with verbose error handlers.",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["company_name"] == "Globex Retail Corp"
    assert data["domain"] == "globex-retail.com"
    assert data["status"] == "new"
    assert data["php2shell_risk_level"] == "critical"
    assert data["qualification_score"] >= 80


@pytest.mark.asyncio
async def test_suppression_list_blocks_lead_and_outreach(client, setup_lead_finder_test_env):
    token_admin = setup_lead_finder_test_env["token_admin"]

    # 1. Add domain to suppression list
    supp_res = await client.post(
        "/api/leads/suppression",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={
            "domain_or_email": "optedout-domain.org",
            "reason": "Explicit GDPR do-not-contact request",
        },
    )
    assert supp_res.status_code == 201

    # 2. Creating lead with suppressed domain is blocked
    block_res = await client.post(
        "/api/leads",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={
            "company_name": "Opted Out Corp",
            "domain": "optedout-domain.org",
            "website_url": "https://optedout-domain.org",
            "contact_email": "security@optedout-domain.org",
        },
    )
    assert block_res.status_code == 400
    assert "Suppression List Enforcement" in block_res.json()["error"]["message"]


@pytest.mark.asyncio
async def test_admin_runs_campaign_discovery(client, setup_lead_finder_test_env):
    token_admin = setup_lead_finder_test_env["token_admin"]
    campaign = setup_lead_finder_test_env["campaign"]

    res = await client.post(
        f"/api/leads/campaigns/{campaign.id}/run",
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert res.status_code == 200
    discovered = res.json()
    assert len(discovered) > 0
    first = discovered[0]
    assert "php2shell_risk_level" in first
    assert first["status"] == "new"


@pytest.mark.asyncio
async def test_draft_outreach_injects_compliance_footer(client, setup_lead_finder_test_env):
    token_admin = setup_lead_finder_test_env["token_admin"]

    # Create lead
    lead_res = await client.post(
        "/api/leads",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={
            "company_name": "CyberDefense Labs",
            "domain": "cyberdefense-labs.io",
            "website_url": "https://cyberdefense-labs.io",
            "contact_name": "Alice Vance",
            "contact_email": "alice@cyberdefense-labs.io",
        },
    )
    lead_id = lead_res.json()["id"]

    # Generate draft
    draft_res = await client.post(
        f"/api/leads/{lead_id}/draft-outreach",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={},
    )
    assert draft_res.status_code == 201
    draft = draft_res.json()
    assert draft["status"] == "draft"
    assert "COMPLIANCE & OPT-OUT NOTICE" in draft["body"]
    assert "opt-out" in draft["body"]
    assert "cyberdefense-labs.io" in draft["subject"]


@pytest.mark.asyncio
async def test_send_outreach_updates_status(client, setup_lead_finder_test_env):
    token_admin = setup_lead_finder_test_env["token_admin"]

    # 1. Create lead
    lead_res = await client.post(
        "/api/leads",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={
            "company_name": "Initech Systems",
            "domain": "initech-systems.net",
            "website_url": "https://initech-systems.net",
            "contact_name": "Peter Gibbons",
            "contact_email": "peter@initech-systems.net",
        },
    )
    lead_id = lead_res.json()["id"]

    # 2. Draft outreach
    draft_res = await client.post(
        f"/api/leads/{lead_id}/draft-outreach",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={},
    )
    draft_id = draft_res.json()["id"]

    # 3. Send outreach
    send_res = await client.post(
        f"/api/leads/outreach/{draft_id}/send",
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert send_res.status_code == 200
    sent_data = send_res.json()
    assert sent_data["status"] == "sent"
    assert sent_data["sent_at"] is not None
    assert sent_data["delivery_message_id"].startswith("msg_bh_outreach_")

    # 4. Lead status is now CONTACTED
    get_lead = await client.get(f"/api/leads/{lead_id}", headers={"Authorization": f"Bearer {token_admin}"})
    assert get_lead.json()["status"] == "contacted"


@pytest.mark.asyncio
async def test_public_opt_out_endpoint(client, setup_lead_finder_test_env):
    # Public unauthenticated user unsubscribes
    res = await client.post(
        "/api/leads/opt-out",
        json={"target": "unsubscribe-me.com"},
    )
    assert res.status_code == 200
    assert res.json()["domain_or_email"] == "unsubscribe-me.com"


@pytest.mark.asyncio
async def test_convert_lead_to_assessment(client, setup_lead_finder_test_env):
    token_admin = setup_lead_finder_test_env["token_admin"]

    # Create lead
    lead_res = await client.post(
        "/api/leads",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={
            "company_name": "Acme Converted Corp",
            "domain": "acme-converted.com",
            "website_url": "https://acme-converted.com",
            "contact_name": "Jane Doe",
            "contact_email": "jane@acme-converted.com",
        },
    )
    lead_id = lead_res.json()["id"]

    # Convert lead
    conv_res = await client.post(
        f"/api/leads/{lead_id}/convert",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={},
    )
    assert conv_res.status_code == 200
    data = conv_res.json()
    assert data["status"] == "converted"
    assert data["attributed_website_id"] is not None


@pytest.mark.asyncio
async def test_client_finder_stats_real_database_metrics(client, setup_lead_finder_test_env):
    token_admin = setup_lead_finder_test_env["token_admin"]

    res = await client.get("/api/leads/stats", headers={"Authorization": f"Bearer {token_admin}"})
    assert res.status_code == 200
    stats = res.json()
    assert "total_leads" in stats
    assert "new_leads" in stats
    assert "qualified_leads" in stats
    assert "contacted_leads" in stats
    assert "converted_clients" in stats
    assert "php2shell_high_risk_leads" in stats
