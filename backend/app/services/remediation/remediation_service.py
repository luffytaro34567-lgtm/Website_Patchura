"""
Remediation Service: Coordinates patch generation, isolated testing,
human approval workflows, multi-tenant isolation, and audit logging.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.payment import Subscription, SubscriptionTier
from app.models.remediation import (
    ApprovalStatus,
    RemediationAuditLog,
    RemediationSession,
    RemediationStatus,
    TestStatus,
)
from app.models.scan import Scan, ScanFinding
from app.models.user import User
from app.models.website import Website
from app.security.path_validator import validate_safe_relative_path
from app.services.remediation.isolated_tester import IsolatedPatchTester
from app.services.remediation.patch_engine import PatchEngineService


class RemediationService:
    @classmethod
    async def create_remediation_session(
        cls,
        db: AsyncSession,
        user: User,
        finding_id: str,
        input_method: str,
        target_filename: str,
        language: str,
        source_code: str,
        client_consent: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> RemediationSession:
        """Creates a remediation request, generates a proposed patch, and runs isolated verification."""
        # 0. Validate target filename safety against path traversal and source code length
        try:
            target_filename = validate_safe_relative_path(target_filename)
        except ValueError as ve:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

        if source_code and len(source_code) > 500_000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source code exceeds maximum permitted buffer size (500 KB).",
            )

        # 1. Fetch Finding and verify ownership
        finding = await db.get(ScanFinding, finding_id)
        if not finding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target vulnerability finding not found.",
            )

        scan = await db.get(Scan, finding.scan_id)
        if not scan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan record not found.")

        if scan.user_id != user.id and not user.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to remediate findings on this website.",
            )

        website = await db.get(Website, finding.website_id)
        if not website:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target website not found.")

        # 2. Check Subscription Quota / Entitlement
        # Free users can generate patches, but Pro/Enterprise users get priority and PHP2Shell deep fixes
        sub_stmt = select(Subscription).where(Subscription.user_id == user.id)
        sub_res = await db.execute(sub_stmt)
        sub = sub_res.scalar_one_or_none()

        is_php2shell = "php2shell" in finding.title.lower() or "cve-2026-109618" in finding.title.lower() or "cve-2026-109619" in finding.title.lower()

        # 3. Generate Proposed Patch
        patch_res = await PatchEngineService.generate_patch(
            finding_id=finding.id,
            finding_title=finding.title,
            finding_category=finding.category,
            finding_description=finding.description,
            finding_evidence=finding.evidence,
            cwe_id=finding.cwe_id,
            filename=target_filename,
            language=language,
            original_code=source_code,
            client_consent=client_consent,
        )

        # 4. Run Isolated Verification Test immediately
        test_res = IsolatedPatchTester.run_isolated_verification(
            filename=target_filename,
            language=language,
            original_code=source_code,
            patched_code=patch_res["patched_code"],
            proposed_diff=patch_res["proposed_diff"],
            finding_category=finding.category,
            finding_title=finding.title,
        )

        session_status = RemediationStatus.TEST_PASSED.value if test_res["passed"] else RemediationStatus.TEST_FAILED.value

        session = RemediationSession(
            finding_id=finding.id,
            scan_id=scan.id,
            website_id=website.id,
            user_id=user.id,
            input_method=input_method,
            target_filename=target_filename,
            language=language,
            original_code=source_code,
            status=session_status,
            ai_provider=patch_res["ai_provider"],
            proposed_diff=patch_res["proposed_diff"],
            patched_code=patch_res["patched_code"],
            explanation=patch_res["explanation"],
            security_warnings=patch_res["security_warnings"],
            php2shell_mitigation_notes=patch_res["php2shell_mitigation_notes"],
            confidence_score=patch_res["confidence_score"],
            test_status=test_res["test_status"],
            test_output=test_res["diagnostics"],
            tested_at=test_res["tested_at"],
            approval_status=ApprovalStatus.PENDING.value,
            client_consent_given=client_consent,
        )
        db.add(session)
        await db.flush()

        # 5. Audit Log
        audit = RemediationAuditLog(
            session_id=session.id,
            user_id=user.id,
            action="patch_generated_and_tested",
            details=f"Generated {patch_res['ai_provider']} patch for '{finding.title}'. Test verdict: {test_res['test_status']}.",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(audit)
        await db.commit()
        await db.refresh(session)
        return session

    @classmethod
    async def run_isolated_test(
        cls,
        db: AsyncSession,
        user: User,
        session_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> RemediationSession:
        """Re-runs isolated sandbox verification on the session's proposed patch."""
        session = await cls.get_session_by_id(db, user, session_id)
        finding = await db.get(ScanFinding, session.finding_id)

        test_res = IsolatedPatchTester.run_isolated_verification(
            filename=session.target_filename,
            language=session.language,
            original_code=session.original_code,
            patched_code=session.patched_code or "",
            proposed_diff=session.proposed_diff or "",
            finding_category=finding.category if finding else "security",
            finding_title=finding.title if finding else "Remediation",
        )

        session.test_status = test_res["test_status"]
        session.test_output = test_res["diagnostics"]
        session.tested_at = test_res["tested_at"]
        session.status = RemediationStatus.TEST_PASSED.value if test_res["passed"] else RemediationStatus.TEST_FAILED.value

        audit = RemediationAuditLog(
            session_id=session.id,
            user_id=user.id,
            action="isolated_test_executed",
            details=f"Test executed manually. Status: {test_res['test_status']}",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(audit)
        await db.commit()
        await db.refresh(session)
        return session

    @classmethod
    async def approve_patch(
        cls,
        db: AsyncSession,
        user: User,
        session_id: str,
        notes: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> RemediationSession:
        """Explicit human approval of the proposed patch."""
        session = await cls.get_session_by_id(db, user, session_id)

        session.approval_status = ApprovalStatus.APPROVED.value
        session.status = RemediationStatus.APPROVED.value
        session.approval_notes = notes
        session.approved_at = datetime.now(timezone.utc)

        audit = RemediationAuditLog(
            session_id=session.id,
            user_id=user.id,
            action="patch_approved",
            details=f"Client approved proposed patch. Notes: {notes or 'No remarks provided.'}",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(audit)
        await db.commit()
        await db.refresh(session)
        return session

    @classmethod
    async def reject_patch(
        cls,
        db: AsyncSession,
        user: User,
        session_id: str,
        reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> RemediationSession:
        """Explicit human rejection of the proposed patch."""
        session = await cls.get_session_by_id(db, user, session_id)

        session.approval_status = ApprovalStatus.REJECTED.value
        session.status = RemediationStatus.REJECTED.value
        session.approval_notes = f"Rejected: {reason}"

        audit = RemediationAuditLog(
            session_id=session.id,
            user_id=user.id,
            action="patch_rejected",
            details=f"Client rejected proposed patch. Reason: {reason}",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(audit)
        await db.commit()
        await db.refresh(session)
        return session

    @classmethod
    async def get_session_by_id(
        cls,
        db: AsyncSession,
        user: User,
        session_id: str,
    ) -> RemediationSession:
        """Fetches remediation session enforcing tenant boundary."""
        session = await db.get(RemediationSession, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Remediation session not found.",
            )

        if session.user_id != user.id and not user.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You do not own this remediation session.",
            )

        return session
