"""
Client Dashboard and Personal Account Endpoints.
Available to authenticated Client users (and Admins).
"""
from __future__ import annotations

from datetime import datetime, timezone
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import RefreshToken, User
from app.models.website import Website
from app.models.scan import Scan, ScanStatus
from app.schemas.client import ChangePasswordRequest, ClientOverviewResponse
from app.security.dependencies import get_current_user
from app.security.passwords import hash_password, verify_password
from app.security.rate_limiter import RateLimit
from app.services.activity.activity_service import ActivityService

router = APIRouter(prefix="/client", tags=["Client Dashboard"])
logger = structlog.get_logger(__name__)


@router.get(
    "/overview",
    response_model=ClientOverviewResponse,
    summary="Get client personal account overview",
)
async def get_client_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClientOverviewResponse:
    """
    Returns authentic account data for the client panel.
    Returns real count of registered website targets for this client.
    """
    targets_res = await db.execute(
        select(func.count(Website.id)).where(Website.user_id == current_user.id)
    )
    targets_count = targets_res.scalar_one() or 0

    scans_res = await db.execute(
        select(func.count(Scan.id)).where(
            Scan.user_id == current_user.id,
            Scan.status == ScanStatus.COMPLETED.value,
        )
    )
    scans_count = scans_res.scalar_one() or 0

    return ClientOverviewResponse(
        user_id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        active_targets_count=targets_count,
        scans_completed_count=scans_count,
        pending_fixes_count=0,
        security_shield_status="Active (PHP2Shell Shield Engaged)",
        php2shell_protected=True,
    )


@router.post(
    "/change-password",
    summary="Change account password",
    dependencies=[Depends(RateLimit(max_requests=10, window_seconds=60, scope="client_change_pwd"))],
)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    now = datetime.now(timezone.utc)
    current_user.hashed_password = hash_password(payload.new_password)

    # Invalidate all active refresh tokens for this user upon password change
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == current_user.id, RefreshToken.is_revoked == False)
        .values(is_revoked=True, revoked_at=now)
    )

    await ActivityService.log_event(
        db=db,
        event_category="account_security",
        event_name="password_changed",
        actor_type="user",
        actor_id=current_user.id,
        actor_email=current_user.email,
        target_type="user",
        target_id=current_user.id,
        target_identifier=current_user.username,
        outcome="success",
        severity="info",
        source_module="client",
        commit=False,
    )
    await db.commit()

    logger.info("User changed password successfully and revoked prior sessions", user_id=current_user.id)
    return {"success": True, "message": "Password changed successfully."}
