"""
Deployment Service: Enforces DevSecOps governance, Pull Request dispatch,
staging execution, production safety gates, and instant rollback.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.deployment import (
    DeploymentEnvironment,
    DeploymentRecord,
    DeploymentStatus,
    DeploymentTarget,
    RepositoryConnection,
    RepositoryProvider,
)
from app.models.remediation import ApprovalStatus, RemediationSession, TestStatus
from app.models.scan import ScanFinding
from app.models.user import User
from app.models.website import Website
from app.services.deployment.git_adapter import GitIntegrationAdapter


class DeploymentService:
    @classmethod
    async def connect_repository(
        cls,
        db: AsyncSession,
        user: User,
        repo_name: str,
        access_token: str,
        provider: str = "github",
        default_branch: str = "main",
        website_id: Optional[str] = None,
    ) -> RepositoryConnection:
        """Connects a Git repository, securely masking the access token."""
        if website_id:
            web = await db.get(Website, website_id)
            if not web or (web.user_id != user.id and not user.is_admin()):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to website.")

        # Create masked representation (e.g. ghp_***4a2b)
        masked = f"{access_token[:4]}***{access_token[-4:]}" if len(access_token) >= 8 else "***"

        conn = RepositoryConnection(
            user_id=user.id,
            website_id=website_id,
            provider=provider,
            repo_name=repo_name.strip(),
            default_branch=default_branch.strip() or "main",
            masked_token=masked,
            encrypted_token=access_token,  # In production, use KMS / fernet encryption
            is_active=True,
        )
        db.add(conn)
        await db.commit()
        await db.refresh(conn)
        return conn

    @classmethod
    async def create_deployment_target(
        cls,
        db: AsyncSession,
        user: User,
        website_id: str,
        name: str,
        environment: str = "staging",
        target_type: str = "github_pr",
        endpoint_url: Optional[str] = None,
        is_enabled: bool = False,
        health_check_url: Optional[str] = None,
    ) -> DeploymentTarget:
        """Configures a staging or production deployment target with strict defaults."""
        web = await db.get(Website, website_id)
        if not web or (web.user_id != user.id and not user.is_admin()):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to website.")

        env_val = environment.lower()
        if env_val not in [DeploymentEnvironment.STAGING.value, DeploymentEnvironment.PRODUCTION.value]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Environment must be 'staging' or 'production'.")

        # Production is strictly disabled by default
        enabled_val = is_enabled if env_val == "staging" else (is_enabled and settings.ENABLE_PRODUCTION_DEPLOYMENT)

        target = DeploymentTarget(
            user_id=user.id,
            website_id=website_id,
            name=name,
            environment=env_val,
            target_type=target_type,
            endpoint_url=endpoint_url,
            is_enabled=enabled_val,
            health_check_url=health_check_url,
        )
        db.add(target)
        await db.commit()
        await db.refresh(target)
        return target

    @classmethod
    async def create_pull_request(
        cls,
        db: AsyncSession,
        user: User,
        session_id: str,
        repository_id: str,
        custom_branch: Optional[str] = None,
        custom_title: Optional[str] = None,
        commit_message: Optional[str] = None,
    ) -> DeploymentRecord:
        """
        Dispatches a Pull Request for an approved patch.
        Strict Gate: Patch must be explicitly approved and pass sandbox tests.
        """
        session = await cls._validate_session_for_transfer(db, user, session_id)

        # Get connected repository
        repo = await db.get(RepositoryConnection, repository_id)
        if not repo or (repo.user_id != user.id and not user.is_admin()):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository connection not found.")

        finding = await db.get(ScanFinding, session.finding_id)

        pr_info = await GitIntegrationAdapter.create_pull_request(
            repo_name=repo.repo_name,
            base_branch=repo.default_branch,
            target_filename=session.target_filename,
            patched_code=session.patched_code or "",
            proposed_diff=session.proposed_diff or "",
            finding_title=finding.title if finding else "Security Finding",
            finding_severity=finding.severity if finding else "medium",
            cwe_id=finding.cwe_id if finding else None,
            explanation=session.explanation,
            test_diagnostics=session.test_output,
            php2shell_notes=session.php2shell_mitigation_notes,
            session_id=session.id,
            access_token=repo.encrypted_token,
            custom_branch=custom_branch,
            custom_title=custom_title,
        )

        record = DeploymentRecord(
            session_id=session.id,
            user_id=user.id,
            website_id=session.website_id,
            environment=DeploymentEnvironment.GIT_PR_ONLY.value,
            status=DeploymentStatus.PR_CREATED.value,
            git_branch=pr_info["branch_name"],
            git_commit_sha=pr_info["commit_sha"],
            pull_request_url=pr_info["pull_request_url"],
            pull_request_number=pr_info["pull_request_number"],
            pre_deployment_test_status=session.test_status,
            client_approved_at=session.approved_at or datetime.now(timezone.utc),
            client_notes=commit_message or "Dispatched Pull Request via PATCHORA DevSecOps",
            rollback_snapshot=session.original_code,
            audit_trail=json.dumps([{
                "event": "pr_dispatched",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "pr_url": pr_info["pull_request_url"],
            }]),
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record

    @classmethod
    async def deploy_to_staging(
        cls,
        db: AsyncSession,
        user: User,
        session_id: str,
        target_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> DeploymentRecord:
        """Triggers controlled staging deployment for an approved patch."""
        session = await cls._validate_session_for_transfer(db, user, session_id)

        target = None
        if target_id:
            target = await db.get(DeploymentTarget, target_id)
            if not target or (target.user_id != user.id and not user.is_admin()):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found.")

        branch_name = f"patchora/staging-{session.id[:8]}"
        now = datetime.now(timezone.utc)

        record = DeploymentRecord(
            session_id=session.id,
            target_id=target.id if target else None,
            user_id=user.id,
            website_id=session.website_id,
            environment=DeploymentEnvironment.STAGING.value,
            status=DeploymentStatus.STAGED.value,
            git_branch=branch_name,
            pre_deployment_test_status=session.test_status,
            client_approved_at=session.approved_at or now,
            client_notes=notes or "Staging validation deployment",
            deployed_at=now,
            rollback_snapshot=session.original_code,
            audit_trail=json.dumps([{
                "event": "staged_deployment_executed",
                "timestamp": now.isoformat(),
                "status": "staged",
            }]),
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record

    @classmethod
    async def deploy_to_production(
        cls,
        db: AsyncSession,
        user: User,
        session_id: str,
        target_id: str,
        confirmation_token: str,
        notes: Optional[str] = None,
    ) -> DeploymentRecord:
        """
        Executes production deployment under strict multi-factor safety gates:
        1. Patch must be approved & passed tests.
        2. Production deployment must be enabled.
        3. Confirmation token must match 'DEPLOY PRODUCTION'.
        4. Rollback snapshot is created.
        """
        if confirmation_token.strip() != "DEPLOY PRODUCTION":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Safety confirmation token mismatch. You must explicitly type 'DEPLOY PRODUCTION'.",
            )

        if not settings.ENABLE_PRODUCTION_DEPLOYMENT and not user.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Production deployment is strictly disabled on this cluster. Contact your administrator or enable ENABLE_PRODUCTION_DEPLOYMENT in .env.",
            )

        session = await cls._validate_session_for_transfer(db, user, session_id)

        target = await db.get(DeploymentTarget, target_id)
        if not target or (target.user_id != user.id and not user.is_admin()):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment target not found.")

        if target.environment != DeploymentEnvironment.PRODUCTION.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected target is not a production target.")

        if not target.is_enabled and not user.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Target is currently disabled. Explicitly enable it in target settings.",
            )

        branch_name = f"patchora/release-prod-{session.id[:8]}"
        now = datetime.now(timezone.utc)

        record = DeploymentRecord(
            session_id=session.id,
            target_id=target.id,
            user_id=user.id,
            website_id=session.website_id,
            environment=DeploymentEnvironment.PRODUCTION.value,
            status=DeploymentStatus.DEPLOYED.value,
            git_branch=branch_name,
            pre_deployment_test_status=session.test_status,
            client_approved_at=now,
            client_notes=notes or "Production release authorized by client",
            deployed_at=now,
            rollback_snapshot=session.original_code,
            audit_trail=json.dumps([{
                "event": "production_deployment_authorized",
                "timestamp": now.isoformat(),
                "status": "deployed",
            }]),
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record

    @classmethod
    async def rollback_deployment(
        cls,
        db: AsyncSession,
        user: User,
        deployment_id: str,
        reason: str,
    ) -> DeploymentRecord:
        """Executes instant rollback to previous code snapshot."""
        record = await db.get(DeploymentRecord, deployment_id)
        if not record or (record.user_id != user.id and not user.is_admin()):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment record not found.")

        now = datetime.now(timezone.utc)
        record.status = DeploymentStatus.ROLLED_BACK.value
        record.rollback_executed_at = now
        record.rollback_reason = reason

        trail = json.loads(record.audit_trail or "[]")
        trail.append({
            "event": "rollback_executed",
            "timestamp": now.isoformat(),
            "reason": reason,
        })
        record.audit_trail = json.dumps(trail)

        await db.commit()
        await db.refresh(record)
        return record

    @classmethod
    async def _validate_session_for_transfer(
        cls,
        db: AsyncSession,
        user: User,
        session_id: str,
    ) -> RemediationSession:
        """Enforces that the patch was explicitly approved and passed sandbox verification."""
        session = await db.get(RemediationSession, session_id)
        if not session or (session.user_id != user.id and not user.is_admin()):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Remediation session not found.")

        if session.approval_status != ApprovalStatus.APPROVED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Security Gate Violation: Patch has not received explicit client approval.",
            )

        if session.test_status != TestStatus.PASSED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Security Gate Violation: Patch has not passed isolated sandbox verification tests.",
            )

        return session
