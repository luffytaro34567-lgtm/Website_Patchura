"""
Tests for PHP vulnerability scanner service and endpoints,
including PHP2Shell (CVE-2026-109618 & CVE-2026-109619) detection & fixes.
"""
from __future__ import annotations

import pytest
from app.services.scanner.php_analyzer import (
    analyze_php_code,
    get_php2shell_mitigation_plan,
)


def test_php2shell_error_handler_detected():
    vulnerable_code = """<?php
    // Dangerous error handler without re-entrancy protection
    set_error_handler(function($errno, $errstr, $errfile, $errline) {
        echo "Error: $errstr in $errfile on line $errline";
    });
    """
    result = analyze_php_code(vulnerable_code)
    assert result.has_php2shell_vulnerability is True
    rule_ids = [f.rule_id for f in result.findings]
    assert "PHP2SHELL-001" in rule_ids
    assert result.remediation_guidance is not None
    assert "CVE-2026-109618" in result.remediation_guidance["cves"]


def test_php2shell_exception_handler_detected():
    vulnerable_code = """<?php
    set_exception_handler(function($e) {
        throw new Exception("Nested crash");
    });
    """
    result = analyze_php_code(vulnerable_code)
    assert result.has_php2shell_vulnerability is True
    rule_ids = [f.rule_id for f in result.findings]
    assert "PHP2SHELL-002" in rule_ids


def test_php2shell_display_errors_detected():
    vulnerable_code = """<?php
    ini_set('display_errors', '1');
    """
    result = analyze_php_code(vulnerable_code)
    assert result.has_php2shell_vulnerability is True
    rule_ids = [f.rule_id for f in result.findings]
    assert "PHP2SHELL-003" in rule_ids


def test_clean_php_code_has_no_findings():
    safe_code = """<?php
    declare(strict_types=1);
    
    function add(int $a, int $b): int {
        return $a + $b;
    }
    """
    result = analyze_php_code(safe_code)
    assert len(result.findings) == 0
    assert result.has_php2shell_vulnerability is False
    assert result.remediation_guidance is None


def test_php2shell_mitigation_plan_structure():
    plan = get_php2shell_mitigation_plan()
    assert plan["cvss_score"] == 9.2
    assert "CVE-2026-109618" in plan["cves"]
    assert "CVE-2026-109619" in plan["cves"]
    assert len(plan["recommended_actions"]) >= 4


@pytest.mark.asyncio
async def test_api_scan_php_analyze_vulnerable(client):
    code = """<?php
    set_error_handler(function($errno, $errstr) { return true; });
    $user_id = $_GET['id'];
    $sql = "SELECT * FROM users WHERE id = " . $user_id;
    mysql_query($sql);
    """
    response = await client.post(
        "/api/scan/php/analyze",
        json={"source_code": code, "file_name": "vulnerable.php"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["has_php2shell_vulnerability"] is True
    assert len(data["findings"]) >= 2
    assert data["remediation_guidance"] is not None
    assert "CVE-2026-109618" in data["remediation_guidance"]["cves"]


@pytest.mark.asyncio
async def test_api_scan_php_analyze_clean(client):
    code = """<?php
    $stmt = $pdo->prepare('SELECT * FROM users WHERE id = :id');
    $stmt->execute(['id' => $id]);
    """
    response = await client.post(
        "/api/scan/php/analyze",
        json={"source_code": code, "file_name": "safe.php"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["has_php2shell_vulnerability"] is False
    assert len(data["findings"]) == 0


@pytest.mark.asyncio
async def test_api_scan_php_analyze_empty_code_rejected(client):
    response = await client.post(
        "/api/scan/php/analyze",
        json={"source_code": "   ", "file_name": "empty.php"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_api_list_php_rules(client):
    response = await client.get("/api/scan/php/rules")
    assert response.status_code == 200
    rules = response.json()
    assert len(rules) >= 15
    rule_ids = [r["rule_id"] for r in rules]
    assert "PHP2SHELL-001" in rule_ids
    assert "PHP2SHELL-002" in rule_ids


@pytest.mark.asyncio
async def test_api_php2shell_mitigation_endpoint(client):
    response = await client.get("/api/scan/php/php2shell-mitigation")
    assert response.status_code == 200
    data = response.json()
    assert data["cvss_score"] == 9.2
    assert "CVE-2026-109618" in data["cves"]
    assert "CVE-2026-109619" in data["cves"]
