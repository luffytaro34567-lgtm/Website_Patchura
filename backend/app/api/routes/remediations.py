"""
FastAPI router for AI Bug-Fixing Engine, Patch Generation,
Isolated Verification Testing, and Human Approval.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
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
from app.schemas.remediation import (
    AdminRemediationStatsResponse,
    ApprovePatchRequest,
    CreateRemediationRequest,
    RejectPatchRequest,
    RemediationSessionResponse,
    RemediationSessionSummary,
    TestResultResponse,
)
from app.security.dependencies import get_current_user, require_admin
from app.services.remediation.remediation_service import RemediationService

router = APIRouter(prefix="/remediations", tags=["AI Bug-Fixing & Patch Generator"])


@router.post(
    "/request",
    response_model=RemediationSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request automated remediation & patch generation for a vulnerability finding",
)
async def create_remediation(
    payload: CreateRemediationRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RemediationSessionResponse:
    if not payload.consent_acknowledged:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client security consent and terms acknowledgment must be explicitly granted.",
        )

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    session = await RemediationService.create_remediation_session(
        db=db,
        user=current_user,
        finding_id=payload.finding_id,
        input_method=payload.input_method,
        target_filename=payload.target_filename,
        language=payload.language,
        source_code=payload.source_code,
        client_consent=payload.consent_acknowledged,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    # Decorate with finding and website context
    finding = await db.get(ScanFinding, session.finding_id)
    website = await db.get(Website, session.website_id)

    res = RemediationSessionResponse.model_validate(session)
    if finding:
        res.finding_title = finding.title
        res.finding_severity = finding.severity
        res.finding_category = finding.category
        res.cwe_id = finding.cwe_id
    if website:
        res.website_domain = website.domain

    return res


@router.get(
    "",
    response_model=List[RemediationSessionSummary],
    summary="List client remediation sessions",
)
async def list_my_remediations(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[RemediationSessionSummary]:
    stmt = (
        select(RemediationSession, ScanFinding, Website)
        .join(ScanFinding, RemediationSession.finding_id == ScanFinding.id)
        .join(Website, RemediationSession.website_id == Website.id)
        .where(RemediationSession.user_id == current_user.id)
        .order_by(desc(RemediationSession.created_at))
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    rows = result.all()

    summaries: List[RemediationSessionSummary] = []
    for sess, find, web in rows:
        summaries.append(
            RemediationSessionSummary(
                id=sess.id,
                finding_id=sess.finding_id,
                finding_title=find.title,
                finding_severity=find.severity,
                website_domain=web.domain,
                target_filename=sess.target_filename,
                language=sess.language,
                status=sess.status,
                ai_provider=sess.ai_provider,
                test_status=sess.test_status,
                approval_status=sess.approval_status,
                created_at=sess.created_at,
            )
        )
    return summaries


@router.get(
    "/{session_id}",
    response_model=RemediationSessionResponse,
    summary="Get detailed remediation session, diff, and test results",
)
async def get_remediation_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RemediationSessionResponse:
    session = await RemediationService.get_session_by_id(db, current_user, session_id)
    finding = await db.get(ScanFinding, session.finding_id)
    website = await db.get(Website, session.website_id)

    res = RemediationSessionResponse.model_validate(session)
    if finding:
        res.finding_title = finding.title
        res.finding_severity = finding.severity
        res.finding_category = finding.category
        res.cwe_id = finding.cwe_id
    if website:
        res.website_domain = website.domain

    return res


@router.get(
    "/finding/{finding_id}",
    response_model=List[RemediationSessionResponse],
    summary="Get all remediation sessions for a specific finding",
)
async def get_remediations_for_finding(
    finding_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[RemediationSessionResponse]:
    finding = await db.get(ScanFinding, finding_id)
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found.")

    scan = await db.get(Scan, finding.scan_id)
    if not scan or (scan.user_id != current_user.id and not current_user.is_admin()):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    website = await db.get(Website, finding.website_id)

    stmt = (
        select(RemediationSession)
        .where(RemediationSession.finding_id == finding_id)
        .order_by(desc(RemediationSession.created_at))
    )
    res = await db.execute(stmt)
    sessions = res.scalars().all()

    output: List[RemediationSessionResponse] = []
    for s in sessions:
        r = RemediationSessionResponse.model_validate(s)
        r.finding_title = finding.title
        r.finding_severity = finding.severity
        r.finding_category = finding.category
        r.cwe_id = finding.cwe_id
        if website:
            r.website_domain = website.domain
        output.append(r)

    return output


@router.post(
    "/{session_id}/test",
    response_model=TestResultResponse,
    summary="Execute isolated sandbox verification on proposed patch",
)
async def test_remediation_patch(
    session_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TestResultResponse:
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    session = await RemediationService.run_isolated_test(
        db=db,
        user=current_user,
        session_id=session_id,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    return TestResultResponse(
        session_id=session.id,
        test_status=session.test_status,
        passed=(session.test_status == TestStatus.PASSED.value),
        diagnostics=session.test_output or "",
        tested_at=session.tested_at or session.created_at,
    )


@router.post(
    "/{session_id}/approve",
    response_model=RemediationSessionResponse,
    summary="Explicit human approval of proposed patch",
)
async def approve_patch(
    session_id: str,
    payload: ApprovePatchRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RemediationSessionResponse:
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    session = await RemediationService.approve_patch(
        db=db,
        user=current_user,
        session_id=session_id,
        notes=payload.approval_notes,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    finding = await db.get(ScanFinding, session.finding_id)
    website = await db.get(Website, session.website_id)

    res = RemediationSessionResponse.model_validate(session)
    if finding:
        res.finding_title = finding.title
        res.finding_severity = finding.severity
    if website:
        res.website_domain = website.domain

    return res


@router.post(
    "/{session_id}/reject",
    response_model=RemediationSessionResponse,
    summary="Explicit human rejection of proposed patch",
)
async def reject_patch(
    session_id: str,
    payload: RejectPatchRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RemediationSessionResponse:
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    session = await RemediationService.reject_patch(
        db=db,
        user=current_user,
        session_id=session_id,
        reason=payload.rejection_reason,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    finding = await db.get(ScanFinding, session.finding_id)
    website = await db.get(Website, session.website_id)

    res = RemediationSessionResponse.model_validate(session)
    if finding:
        res.finding_title = finding.title
        res.finding_severity = finding.severity
    if website:
        res.website_domain = website.domain

    return res


@router.get(
    "/{session_id}/download/patch",
    summary="Download unified diff as a standard .patch file",
)
async def download_patch_file(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    session = await RemediationService.get_session_by_id(db, current_user, session_id)
    if not session.proposed_diff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No patch diff available for this session.",
        )

    base_name = session.target_filename.rsplit(".", 1)[0]
    filename = f"{base_name}_fix.patch"

    return Response(
        content=session.proposed_diff,
        media_type="text/x-diff",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/{session_id}/download/file",
    summary="Download complete patched source code file",
)
async def download_patched_code_file(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    session = await RemediationService.get_session_by_id(db, current_user, session_id)
    if not session.patched_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No patched code available for this session.",
        )

    filename = f"patched_{session.target_filename}"

    return Response(
        content=session.patched_code,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ──────────────────────────────────────────────────────────────────────────────
# Admin Endpoints
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/admin/stats",
    response_model=AdminRemediationStatsResponse,
    summary="Get administrative remediation and testing metrics",
    dependencies=[Depends(require_admin)],
)
async def admin_get_remediation_stats(
    db: AsyncSession = Depends(get_db),
) -> AdminRemediationStatsResponse:
    total_remediations = await db.scalar(select(func.count(RemediationSession.id))) or 0
    approved = await db.scalar(
        select(func.count(RemediationSession.id)).where(RemediationSession.approval_status == ApprovalStatus.APPROVED.value)
    ) or 0
    rejected = await db.scalar(
        select(func.count(RemediationSession.id)).where(RemediationSession.approval_status == ApprovalStatus.REJECTED.value)
    ) or 0
    passed = await db.scalar(
        select(func.count(RemediationSession.id)).where(RemediationSession.test_status == TestStatus.PASSED.value)
    ) or 0
    failed = await db.scalar(
        select(func.count(RemediationSession.id)).where(RemediationSession.test_status.in_([TestStatus.FAILED.value, TestStatus.SYNTAX_ERROR.value]))
    ) or 0
    pending = await db.scalar(
        select(func.count(RemediationSession.id)).where(RemediationSession.approval_status == ApprovalStatus.PENDING.value)
    ) or 0

    return AdminRemediationStatsResponse(
        total_remediations=total_remediations,
        approved_patches=approved,
        rejected_patches=rejected,
        tests_passed=passed,
        tests_failed=failed,
        pending_approval=pending,
        ai_provider_active="Deterministic Security Rules Engine (AST Analyzer)",
    )
