"""
FastAPI router for Source-Code Integration, Pull Request Dispatch,
Staging Deployments, and Secure Production Gates.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.deployment import (
    DeploymentEnvironment,
    DeploymentRecord,
    DeploymentStatus,
    DeploymentTarget,
    RepositoryConnection,
)
from app.models.remediation import RemediationSession
from app.models.scan import ScanFinding
from app.models.user import User
from app.models.website import Website
from app.schemas.deployment import (
    AdminDeploymentOverviewResponse,
    CliInstructionsResponse,
    CreateDeploymentTargetRequest,
    CreatePullRequestPayload,
    CreateRepositoryConnectionRequest,
    DeployProductionPayload,
    DeployStagingPayload,
    DeploymentRecordResponse,
    DeploymentTargetResponse,
    RepositoryConnectionResponse,
    RollbackPayload,
)
from app.security.dependencies import get_current_user, require_admin
from app.services.deployment.deployment_service import DeploymentService
from app.services.deployment.git_adapter import GitIntegrationAdapter

router = APIRouter(prefix="/deployment", tags=["Source-Code Integration & Deployment"])


@router.post(
    "/repositories",
    response_model=RepositoryConnectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Connect a Git repository (GitHub / GitLab / Local Git)",
)
async def connect_repository(
    payload: CreateRepositoryConnectionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RepositoryConnectionResponse:
    conn = await DeploymentService.connect_repository(
        db=db,
        user=current_user,
        repo_name=payload.repo_name,
        access_token=payload.access_token,
        provider=payload.provider,
        default_branch=payload.default_branch,
        website_id=payload.website_id,
    )
    return RepositoryConnectionResponse.model_validate(conn)


@router.get(
    "/repositories",
    response_model=List[RepositoryConnectionResponse],
    summary="List client connected Git repositories",
)
async def list_repositories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[RepositoryConnectionResponse]:
    stmt = (
        select(RepositoryConnection)
        .where(RepositoryConnection.user_id == current_user.id)
        .order_by(desc(RepositoryConnection.created_at))
    )
    res = await db.execute(stmt)
    conns = res.scalars().all()
    return [RepositoryConnectionResponse.model_validate(c) for c in conns]


@router.delete(
    "/repositories/{repo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Disconnect a Git repository",
)
async def disconnect_repository(
    repo_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conn = await db.get(RepositoryConnection, repo_id)
    if not conn or (conn.user_id != current_user.id and not current_user.is_admin()):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository connection not found.")

    await db.delete(conn)
    await db.commit()
    return None


@router.post(
    "/targets",
    response_model=DeploymentTargetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Configure staging or production deployment target",
)
async def create_target(
    payload: CreateDeploymentTargetRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DeploymentTargetResponse:
    target = await DeploymentService.create_deployment_target(
        db=db,
        user=current_user,
        website_id=payload.website_id,
        name=payload.name,
        environment=payload.environment,
        target_type=payload.target_type,
        endpoint_url=payload.endpoint_url,
        is_enabled=payload.is_enabled,
        health_check_url=payload.health_check_url,
    )
    return DeploymentTargetResponse.model_validate(target)


@router.get(
    "/targets",
    response_model=List[DeploymentTargetResponse],
    summary="List client deployment targets",
)
async def list_targets(
    website_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[DeploymentTargetResponse]:
    stmt = select(DeploymentTarget).where(DeploymentTarget.user_id == current_user.id)
    if website_id:
        stmt = stmt.where(DeploymentTarget.website_id == website_id)
    stmt = stmt.order_by(desc(DeploymentTarget.created_at))

    res = await db.execute(stmt)
    targets = res.scalars().all()
    return [DeploymentTargetResponse.model_validate(t) for t in targets]


@router.post(
    "/create-pr",
    response_model=DeploymentRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Dispatch a Pull Request to connected GitHub repository for an approved patch",
)
async def create_pull_request(
    payload: CreatePullRequestPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DeploymentRecordResponse:
    record = await DeploymentService.create_pull_request(
        db=db,
        user=current_user,
        session_id=payload.session_id,
        repository_id=payload.repository_id,
        custom_branch=payload.branch_name,
        custom_title=payload.pr_title,
        commit_message=payload.commit_message,
    )

    # Decorate response with finding and website title
    session = await db.get(RemediationSession, record.session_id)
    finding = await db.get(ScanFinding, session.finding_id) if session else None
    website = await db.get(Website, record.website_id)

    res = DeploymentRecordResponse.model_validate(record)
    if finding:
        res.finding_title = finding.title
    if session:
        res.target_filename = session.target_filename
    if website:
        res.website_domain = website.domain

    return res


@router.post(
    "/deploy-staging",
    response_model=DeploymentRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Deploy an approved patch to the staging environment",
)
async def deploy_staging(
    payload: DeployStagingPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DeploymentRecordResponse:
    record = await DeploymentService.deploy_to_staging(
        db=db,
        user=current_user,
        session_id=payload.session_id,
        target_id=payload.target_id,
        notes=payload.notes,
    )

    session = await db.get(RemediationSession, record.session_id)
    finding = await db.get(ScanFinding, session.finding_id) if session else None
    website = await db.get(Website, record.website_id)

    res = DeploymentRecordResponse.model_validate(record)
    if finding:
        res.finding_title = finding.title
    if session:
        res.target_filename = session.target_filename
    if website:
        res.website_domain = website.domain

    return res


@router.post(
    "/deploy-production",
    response_model=DeploymentRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Deploy an approved patch to production (Strict multi-factor safety gate)",
)
async def deploy_production(
    payload: DeployProductionPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DeploymentRecordResponse:
    record = await DeploymentService.deploy_to_production(
        db=db,
        user=current_user,
        session_id=payload.session_id,
        target_id=payload.target_id,
        confirmation_token=payload.confirmation_token,
        notes=payload.client_notes,
    )

    session = await db.get(RemediationSession, record.session_id)
    finding = await db.get(ScanFinding, session.finding_id) if session else None
    website = await db.get(Website, record.website_id)

    res = DeploymentRecordResponse.model_validate(record)
    if finding:
        res.finding_title = finding.title
    if session:
        res.target_filename = session.target_filename
    if website:
        res.website_domain = website.domain

    return res


@router.post(
    "/{deployment_id}/rollback",
    response_model=DeploymentRecordResponse,
    summary="Execute instant rollback of a previous deployment",
)
async def rollback_deployment(
    deployment_id: str,
    payload: RollbackPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DeploymentRecordResponse:
    record = await DeploymentService.rollback_deployment(
        db=db,
        user=current_user,
        deployment_id=deployment_id,
        reason=payload.reason,
    )
    return DeploymentRecordResponse.model_validate(record)


@router.get(
    "/cli-instructions/{session_id}",
    response_model=CliInstructionsResponse,
    summary="Generate manual Git CLI patch application and rollback commands",
)
async def get_cli_instructions(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CliInstructionsResponse:
    session = await db.get(RemediationSession, session_id)
    if not session or (session.user_id != current_user.id and not current_user.is_admin()):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Remediation session not found.")

    instructions = GitIntegrationAdapter.generate_cli_instructions(
        session_id=session.id,
        target_filename=session.target_filename,
        proposed_diff=session.proposed_diff or "",
    )
    return CliInstructionsResponse(**instructions)


@router.get(
    "/history",
    response_model=List[DeploymentRecordResponse],
    summary="List client deployment and Git history",
)
async def get_deployment_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[DeploymentRecordResponse]:
    stmt = (
        select(DeploymentRecord, RemediationSession, ScanFinding, Website)
        .join(RemediationSession, DeploymentRecord.session_id == RemediationSession.id)
        .join(ScanFinding, RemediationSession.finding_id == ScanFinding.id)
        .join(Website, DeploymentRecord.website_id == Website.id)
        .where(DeploymentRecord.user_id == current_user.id)
        .order_by(desc(DeploymentRecord.created_at))
    )
    res = await db.execute(stmt)
    rows = res.all()

    output: List[DeploymentRecordResponse] = []
    for rec, sess, find, web in rows:
        r = DeploymentRecordResponse.model_validate(rec)
        r.finding_title = find.title
        r.target_filename = sess.target_filename
        r.website_domain = web.domain
        output.append(r)

    return output


@router.get(
    "/admin/overview",
    response_model=AdminDeploymentOverviewResponse,
    summary="Admin DevSecOps deployment and Git telemetry",
    dependencies=[Depends(require_admin)],
)
async def admin_get_deployment_overview(
    db: AsyncSession = Depends(get_db),
) -> AdminDeploymentOverviewResponse:
    total_repos = await db.scalar(select(func.count(RepositoryConnection.id))) or 0
    total_prs = await db.scalar(
        select(func.count(DeploymentRecord.id)).where(DeploymentRecord.status == DeploymentStatus.PR_CREATED.value)
    ) or 0
    total_staged = await db.scalar(
        select(func.count(DeploymentRecord.id)).where(DeploymentRecord.environment == DeploymentEnvironment.STAGING.value)
    ) or 0
    total_prod = await db.scalar(
        select(func.count(DeploymentRecord.id)).where(DeploymentRecord.environment == DeploymentEnvironment.PRODUCTION.value)
    ) or 0
    total_rollbacks = await db.scalar(
        select(func.count(DeploymentRecord.id)).where(DeploymentRecord.status == DeploymentStatus.ROLLED_BACK.value)
    ) or 0

    return AdminDeploymentOverviewResponse(
        total_connected_repositories=total_repos,
        total_pull_requests_dispatched=total_prs,
        total_staging_deployments=total_staged,
        total_production_deployments=total_prod,
        production_deployments_enabled=settings.ENABLE_PRODUCTION_DEPLOYMENT,
        total_rollbacks_executed=total_rollbacks,
    )
