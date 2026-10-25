"""
FastAPI router for Paid Detailed Vulnerability Reports, Entitlement Access Control,
Report Generation, and Order Workflows.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.report import (
    OrderStatus,
    ReportAccessLog,
    ReportDocument,
    ReportEntitlement,
    ReportOrder,
    ReportPricingConfig,
)
from app.models.scan import Scan, ScanFinding, ScanStatus
from app.models.user import User
from app.schemas.report import (
    AdminGrantEntitlementRequest,
    CompleteReportOrderRequest,
    CreateReportOrderRequest,
    DetailedReportResponse,
    ReportEntitlementResponse,
    ReportEntitlementStatusResponse,
    ReportOrderResponse,
    ReportPricingResponse,
)
from app.schemas.scan import ScanFindingResponse
from app.security.dependencies import get_current_user, require_admin
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Detailed Vulnerability Reports"])


@router.get(
    "/pricing",
    response_model=ReportPricingResponse,
    summary="Get detailed report product pricing and configuration",
)
async def get_report_pricing(
    db: AsyncSession = Depends(get_db),
) -> ReportPricingResponse:
    config = await ReportService.get_or_create_pricing(db)
    return ReportPricingResponse(
        product_name=config.product_name,
        price=config.price,
        currency=config.currency,
        description=config.description,
        features=[f.strip() for f in config.features_list.split(",") if f.strip()],
    )


@router.get(
    "/scan/{scan_id}/status",
    response_model=ReportEntitlementStatusResponse,
    summary="Get report entitlement and purchase status for a scan",
)
async def get_report_status(
    scan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReportEntitlementStatusResponse:
    scan = await db.get(Scan, scan_id)
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found.")

    if scan.user_id != current_user.id and not current_user.is_admin():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    config = await ReportService.get_or_create_pricing(db)
    pricing = ReportPricingResponse(
        product_name=config.product_name,
        price=config.price,
        currency=config.currency,
        description=config.description,
        features=[f.strip() for f in config.features_list.split(",") if f.strip()],
    )

    has_entitlement = await ReportService.has_active_entitlement(db, current_user, scan.id)
    entitlement = await ReportService.get_entitlement_for_scan(db, current_user, scan.id)

    # Latest order for this scan
    order_stmt = (
        select(ReportOrder)
        .where(ReportOrder.scan_id == scan_id, ReportOrder.user_id == current_user.id)
        .order_by(desc(ReportOrder.created_at))
        .limit(1)
    )
    order_res = await db.execute(order_stmt)
    latest_order = order_res.scalar_one_or_none()

    can_purchase = (
        scan.status == ScanStatus.COMPLETED.value
        and not has_entitlement
        and not current_user.is_admin()
    )

    return ReportEntitlementStatusResponse(
        scan_id=scan.id,
        has_entitlement=has_entitlement,
        can_purchase=can_purchase,
        pricing=pricing,
        entitlement=ReportEntitlementResponse.model_validate(entitlement) if entitlement else None,
        active_order=ReportOrderResponse.model_validate(latest_order) if latest_order else None,
    )


@router.post(
    "/scan/{scan_id}/order",
    response_model=ReportOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate report purchase order",
)
async def create_report_order(
    scan_id: str,
    payload: CreateReportOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReportOrderResponse:
    scan = await db.get(Scan, scan_id)
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found.")

    if scan.user_id != current_user.id and not current_user.is_admin():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    if scan.status != ScanStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A detailed report can only be ordered for a completed scan.",
        )

    # Check if already entitled
    already_entitled = await ReportService.has_active_entitlement(db, current_user, scan.id)
    if already_entitled and not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already possess an active entitlement for this report.",
        )

    config = await ReportService.get_or_create_pricing(db)

    order = ReportOrder(
        scan_id=scan.id,
        user_id=current_user.id,
        product_name=config.product_name,
        amount=config.price,
        currency=config.currency,
        status=OrderStatus.PENDING.value,
        payment_method=payload.payment_method,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    return ReportOrderResponse.model_validate(order)


@router.post(
    "/orders/{order_id}/complete",
    response_model=ReportOrderResponse,
    summary="Complete report order and grant entitlement (Dev & Gateway workflow)",
)
async def complete_report_order(
    order_id: str,
    payload: CompleteReportOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReportOrderResponse:
    order = await db.get(ReportOrder, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    if order.user_id != current_user.id and not current_user.is_admin():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    if order.status != OrderStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order is already in '{order.status}' status.",
        )

    if payload.simulate_status == "completed":
        order.status = OrderStatus.COMPLETED.value
        order.completed_at = datetime.now(timezone.utc)

        # Grant entitlement
        entitlement = ReportEntitlement(
            scan_id=order.scan_id,
            user_id=order.user_id,
            order_id=order.id,
            is_active=True,
            granted_by="order_checkout",
        )
        db.add(entitlement)

        # Pre-generate report document
        scan = await db.get(Scan, order.scan_id)
        if scan:
            await ReportService.generate_or_get_report_document(db, scan)

        await db.commit()
        await db.refresh(order)

    elif payload.simulate_status == "failed":
        order.status = OrderStatus.FAILED.value
        order.failure_reason = "Payment authorization declined by simulated issuer."
        await db.commit()
        await db.refresh(order)

    elif payload.simulate_status == "cancelled":
        order.status = OrderStatus.CANCELLED.value
        await db.commit()
        await db.refresh(order)

    return ReportOrderResponse.model_validate(order)


@router.get(
    "/scan/{scan_id}/details",
    response_model=DetailedReportResponse,
    summary="Access detailed vulnerability report (Entitlement Gated)",
)
async def get_detailed_report(
    scan_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DetailedReportResponse:
    # 1. Fetch scan
    stmt = (
        select(Scan)
        .options(selectinload(Scan.findings))
        .where(Scan.id == scan_id)
    )
    res = await db.execute(stmt)
    scan = res.scalar_one_or_none()

    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found.")

    # 2. Check ownership
    if scan.user_id != current_user.id and not current_user.is_admin():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    # 3. Access Control Gate: Verify active entitlement
    has_entitlement = await ReportService.has_active_entitlement(db, current_user, scan.id)
    if not has_entitlement:
        config = await ReportService.get_or_create_pricing(db)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Detailed report access requires an active report entitlement. "
                f"Please purchase access for ${config.price:.2f} {config.currency}."
            ),
        )

    # 4. Record access audit log
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    await ReportService.record_access(
        db=db,
        user_id=current_user.id,
        scan_id=scan.id,
        access_type="web_view",
        ip_address=client_ip,
        user_agent=user_agent,
    )

    # 5. Fetch or build report document
    doc = await ReportService.generate_or_get_report_document(db, scan)

    findings_res = [ScanFindingResponse.model_validate(f) for f in scan.findings]
    severity_breakdown = {
        "critical": scan.critical_count,
        "high": scan.high_count,
        "medium": scan.medium_count,
        "low": scan.low_count,
        "info": scan.info_count,
    }

    return DetailedReportResponse(
        id=doc.id,
        scan_id=scan.id,
        website_id=scan.website_id,
        title=doc.title,
        target_url=scan.target_url,
        target_domain=scan.target_domain,
        profile=scan.profile,
        executive_summary=doc.executive_summary,
        overall_risk_score=doc.overall_risk_score,
        overall_posture=doc.overall_posture,
        has_php2shell_finding=doc.has_php2shell_finding,
        php2shell_posture=doc.php2shell_posture,
        generated_at=doc.generated_at,
        version=doc.version,
        total_findings=scan.total_findings,
        severity_breakdown=severity_breakdown,
        findings=findings_res,
        html_content=doc.html_content,
    )


@router.get(
    "/scan/{scan_id}/download-html",
    summary="Download printable standalone HTML security report (Entitlement Gated)",
)
async def download_report_html(
    scan_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    scan = await db.get(Scan, scan_id)
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found.")

    if scan.user_id != current_user.id and not current_user.is_admin():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    has_entitlement = await ReportService.has_active_entitlement(db, current_user, scan.id)
    if not has_entitlement:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Entitlement required to download report.",
        )

    # Record download log
    client_ip = request.client.host if request.client else None
    await ReportService.record_access(
        db=db,
        user_id=current_user.id,
        scan_id=scan.id,
        access_type="html_download",
        ip_address=client_ip,
        user_agent=request.headers.get("user-agent"),
    )

    doc = await ReportService.generate_or_get_report_document(db, scan)

    filename = f"patchora-report-{scan.target_domain}-{scan.id[:8]}.html"
    return Response(
        content=doc.html_content,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/my-reports",
    response_model=List[ReportEntitlementResponse],
    summary="List client's active report entitlements",
)
async def list_my_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ReportEntitlementResponse]:
    stmt = (
        select(ReportEntitlement)
        .where(ReportEntitlement.user_id == current_user.id, ReportEntitlement.is_active == True)
        .order_by(desc(ReportEntitlement.granted_at))
    )
    res = await db.execute(stmt)
    items = res.scalars().all()
    return [ReportEntitlementResponse.model_validate(it) for it in items]


# ── Administrative Report Oversight ───────────────────────────────────────────

@router.get(
    "/admin/orders",
    response_model=List[ReportOrderResponse],
    summary="List all report purchase orders (Admin only)",
)
async def admin_list_report_orders(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> List[ReportOrderResponse]:
    stmt = select(ReportOrder).order_by(desc(ReportOrder.created_at))
    res = await db.execute(stmt)
    orders = res.scalars().all()
    return [ReportOrderResponse.model_validate(o) for o in orders]


@router.post(
    "/admin/grant-entitlement",
    response_model=ReportEntitlementResponse,
    summary="Manually grant report entitlement to a scan (Admin only)",
)
async def admin_grant_entitlement(
    payload: AdminGrantEntitlementRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ReportEntitlementResponse:
    scan = await db.get(Scan, payload.scan_id)
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found.")

    # Check existing entitlement
    stmt = select(ReportEntitlement).where(ReportEntitlement.scan_id == scan.id)
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()
    if existing:
        existing.is_active = True
        existing.granted_by = f"admin_grant:{admin.username}"
        await db.commit()
        await db.refresh(existing)
        return ReportEntitlementResponse.model_validate(existing)

    ent = ReportEntitlement(
        scan_id=scan.id,
        user_id=scan.user_id,
        is_active=True,
        granted_by=f"admin_grant:{admin.username}",
    )
    db.add(ent)
    await ReportService.generate_or_get_report_document(db, scan)
    await db.commit()
    await db.refresh(ent)

    return ReportEntitlementResponse.model_validate(ent)
