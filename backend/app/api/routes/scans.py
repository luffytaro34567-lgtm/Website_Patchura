"""
FastAPI router for Vulnerability Scans, safe execution, and findings.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.scan import FindingSeverity, Scan, ScanFinding, ScanProfile, ScanStatus
from app.models.user import User
from app.models.website import Website
from app.schemas.scan import CreateScanRequest, ScanFindingResponse, ScanResponse, ScanSummaryExport
from app.security.dependencies import get_current_user
from app.security.url_validator import validate_target_url
from app.services.scanner.web_scanner import WebScannerEngine
from app.services.payment.quota_service import QuotaService
from app.services.activity.activity_service import ActivityService

router = APIRouter(prefix="/scans", tags=["Vulnerability Scans"])


@router.post(
    "",
    response_model=ScanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate an authorized vulnerability scan",
    description="Validates ownership verification and active scan authorization before launching a background scan.",
)
async def create_scan(
    payload: CreateScanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ScanResponse:
    # Enforce monthly scan quota according to customer subscription tier
    can_scan, quota_reason = await QuotaService.can_execute_scan(db, current_user)
    if not can_scan:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=quota_reason,
        )

    # 1. Fetch website and authorization
    stmt = (
        select(Website)
        .options(selectinload(Website.authorization))
        .where(Website.id == payload.website_id)
    )
    result = await db.execute(stmt)
    website = result.scalar_one_or_none()

    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target website not found.",
        )

    # 2. Check ownership (or admin role)
    if website.user_id != current_user.id and not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to scan this website.",
        )

    # 3. Check admin suspension
    if website.is_suspended_by_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Scanning this target is suspended by administrator. Reason: {website.suspension_reason or 'Policy violation'}",
        )

    # 4. Check ownership verification
    if website.verification_status != "verified":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Target website ownership is not verified. "
                "You must complete DNS TXT, HTML Meta Tag, or HTTP File verification before scanning."
            ),
        )

    # 5. Check active explicit authorization
    auth = website.authorization
    if not auth or not auth.is_authorized or auth.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Target website does not have an active scan authorization warrant. Grant authorization before initiating a scan.",
        )

    if auth.expires_at and auth.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The scan authorization warrant for this target has expired. Please renew authorization.",
        )

    # 6. Validate target URL safety (SSRF defense)
    try:
        validate_target_url(website.target_url)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Target URL failed safety policy: {str(e)}",
        )

    # 7. Create Scan record
    scan = Scan(
        website_id=website.id,
        user_id=current_user.id,
        profile=payload.profile.value,
        status=ScanStatus.QUEUED.value,
        progress_percent=0,
        target_url=website.target_url,
        target_domain=website.domain,
    )
    db.add(scan)
    await ActivityService.log_event(
        db=db,
        event_category="vulnerability_scanning",
        event_name="scan_started",
        actor_type="user",
        actor_id=current_user.id,
        actor_email=current_user.email,
        target_type="scan",
        target_id=scan.id,
        target_identifier=website.domain,
        outcome="success",
        severity="info",
        source_module="scans",
        metadata={"profile": payload.profile.value, "target_url": website.target_url},
        commit=False,
    )
    await db.commit()
    await db.refresh(scan)

    # 8. Dispatch background scan task
    asyncio.create_task(WebScannerEngine.run_scan(scan.id))

    return ScanResponse.model_validate(scan)


@router.get(
    "",
    response_model=List[ScanResponse],
    summary="List client scans",
)
async def list_scans(
    website_id: Optional[str] = Query(None, description="Filter by website ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by scan status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ScanResponse]:
    stmt = select(Scan).where(Scan.user_id == current_user.id)

    if website_id:
        stmt = stmt.where(Scan.website_id == website_id)
    if status_filter:
        stmt = stmt.where(Scan.status == status_filter)

    stmt = stmt.order_by(desc(Scan.created_at)).limit(limit).offset(offset)
    result = await db.execute(stmt)
    scans = result.scalars().all()
    return [ScanResponse.model_validate(s) for s in scans]


@router.get(
    "/{scan_id}",
    response_model=ScanResponse,
    summary="Get scan details and findings",
)
async def get_scan_details(
    scan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ScanResponse:
    stmt = (
        select(Scan)
        .options(selectinload(Scan.findings))
        .where(Scan.id == scan_id)
    )
    result = await db.execute(stmt)
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan record not found.",
        )

    # Check ownership or admin
    if scan.user_id != current_user.id and not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this scan.",
        )

    return ScanResponse.model_validate(scan)


@router.post(
    "/{scan_id}/cancel",
    response_model=ScanResponse,
    summary="Cancel a queued or running scan",
)
async def cancel_scan(
    scan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ScanResponse:
    scan = await db.get(Scan, scan_id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan record not found.",
        )

    if scan.user_id != current_user.id and not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to cancel this scan.",
        )

    if scan.status in [ScanStatus.COMPLETED.value, ScanStatus.FAILED.value, ScanStatus.CANCELLED.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel a scan with status '{scan.status}'.",
        )

    scan.is_cancelled = True
    scan.cancelled_by = "admin" if current_user.is_admin() else "client"
    scan.status = ScanStatus.CANCELLED.value
    scan.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(scan)

    return ScanResponse.model_validate(scan)


@router.get(
    "/{scan_id}/export",
    response_model=ScanSummaryExport,
    summary="Export free basic scan summary and findings in JSON format",
)
async def export_scan_summary(
    scan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ScanSummaryExport:
    stmt = (
        select(Scan)
        .options(selectinload(Scan.findings))
        .where(Scan.id == scan_id)
    )
    result = await db.execute(stmt)
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan record not found.",
        )

    if scan.user_id != current_user.id and not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this scan.",
        )

    findings_res = [ScanFindingResponse.model_validate(f) for f in scan.findings]

    severity_counts = {
        "critical": scan.critical_count,
        "high": scan.high_count,
        "medium": scan.medium_count,
        "low": scan.low_count,
        "info": scan.info_count,
    }

    return ScanSummaryExport(
        scan_id=scan.id,
        target_url=scan.target_url,
        target_domain=scan.target_domain,
        profile=scan.profile,
        status=scan.status,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
        duration_seconds=scan.duration_seconds,
        total_findings=scan.total_findings,
        severity_breakdown=severity_counts,
        findings=findings_res,
        exported_at=datetime.now(timezone.utc),
    )
