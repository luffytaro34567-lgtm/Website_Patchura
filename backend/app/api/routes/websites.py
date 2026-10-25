"""
Website Target Registration, Ownership Verification, and Scan Authorization Endpoints.
Ensures authenticated clients manage authorized targets safely without automatic scanning.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.user import User
from app.models.website import (
    ScanAuthorization,
    VerificationMethod,
    VerificationStatus,
    Website,
)
from app.schemas.website import (
    CreateWebsiteRequest,
    RevokeAuthorizationRequest,
    ScanAuthorizationRequest,
    ScanAuthorizationResponse,
    UpdateVerificationMethodRequest,
    VerificationInstructions,
    VerificationResultResponse,
    WebsiteResponse,
)
from app.security.dependencies import get_current_user
from app.security.url_validator import validate_and_normalize_target_url
from app.services.verification_service import VerificationService
from app.services.payment.quota_service import QuotaService
from app.services.activity.activity_service import ActivityService

router = APIRouter(prefix="/websites", tags=["Target Websites"])
logger = structlog.get_logger(__name__)


def build_instructions(website: Website) -> VerificationInstructions:
    token = website.verification_token
    domain = website.domain
    return VerificationInstructions(
        method=website.verification_method,
        token=token,
        file_path="/.well-known/patchora-verification.txt",
        file_content=f"patchora-site-verification={token}",
        meta_tag_snippet=f'<meta name="patchora-verification" content="{token}">',
        dns_record_name=f"_patchora-challenge.{domain}",
        dns_txt_value=f"patchora-site-verification={token}",
    )


def map_website_response(website: Website) -> WebsiteResponse:
    res = WebsiteResponse.model_validate(website)
    res.instructions = build_instructions(website)
    if website.authorization:
        res.authorization = ScanAuthorizationResponse.model_validate(website.authorization)
    return res


@router.post(
    "",
    response_model=WebsiteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new website target",
    description="Registers a new website target for ownership verification. A registered URL never automatically triggers a scan.",
)
async def create_website(
    payload: CreateWebsiteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WebsiteResponse:
    # Enforce plan quota on target websites
    can_add, reason = await QuotaService.can_add_target_website(db, current_user)
    if not can_add:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=reason,
        )

    try:
        normalized_url, domain = validate_and_normalize_target_url(payload.target_url)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    # Check if this user already registered this domain
    existing = await db.execute(
        select(Website).where(
            Website.user_id == current_user.id,
            Website.domain == domain,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"You have already registered '{domain}' in your workspace.",
        )

    website = Website(
        user_id=current_user.id,
        name=payload.name,
        target_url=normalized_url,
        domain=domain,
        verification_method=payload.verification_method.value,
        verification_status=VerificationStatus.PENDING.value,
    )
    db.add(website)
    await ActivityService.log_event(
        db=db,
        event_category="website_registration",
        event_name="website_registered",
        actor_type="user",
        actor_id=current_user.id,
        actor_email=current_user.email,
        target_type="website",
        target_id=website.id,
        target_identifier=website.domain,
        outcome="success",
        severity="info",
        source_module="websites",
        commit=False,
    )
    await db.commit()
    await db.refresh(website)

    logger.info("Website registered", user_id=current_user.id, domain=domain, website_id=website.id)
    return map_website_response(website)


@router.get(
    "",
    response_model=List[WebsiteResponse],
    summary="List client registered websites",
)
async def list_websites(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[WebsiteResponse]:
    result = await db.execute(
        select(Website)
        .options(selectinload(Website.authorization))
        .where(Website.user_id == current_user.id)
        .order_by(Website.created_at.desc())
    )
    websites = result.scalars().all()
    return [map_website_response(w) for w in websites]


@router.get(
    "/{website_id}",
    response_model=WebsiteResponse,
    summary="Get target website details",
)
async def get_website(
    website_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WebsiteResponse:
    result = await db.execute(
        select(Website)
        .options(selectinload(Website.authorization))
        .where(Website.id == website_id)
    )
    website = result.scalar_one_or_none()

    if website is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website target not found.",
        )

    if website.user_id != current_user.id and not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this website target.",
        )

    return map_website_response(website)


@router.patch(
    "/{website_id}/verification-method",
    response_model=WebsiteResponse,
    summary="Switch ownership verification method",
)
async def update_verification_method(
    website_id: str,
    payload: UpdateVerificationMethodRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WebsiteResponse:
    result = await db.execute(
        select(Website)
        .options(selectinload(Website.authorization))
        .where(Website.id == website_id, Website.user_id == current_user.id)
    )
    website = result.scalar_one_or_none()
    if website is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website target not found.")

    website.verification_method = payload.verification_method.value
    await db.commit()
    await db.refresh(website)
    return map_website_response(website)


@router.post(
    "/{website_id}/verify",
    response_model=VerificationResultResponse,
    summary="Execute target ownership verification check",
)
async def verify_website(
    website_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VerificationResultResponse:
    result = await db.execute(
        select(Website)
        .options(selectinload(Website.authorization))
        .where(Website.id == website_id, Website.user_id == current_user.id)
    )
    website = result.scalar_one_or_none()
    if website is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website target not found.")

    if website.is_suspended_by_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Target assessment is suspended by an administrator: {website.suspension_reason or 'Policy violation.'}",
        )

    now = datetime.now(timezone.utc)
    website.last_verification_attempt = now

    is_verified, message = await VerificationService.verify_website_ownership(website)

    if is_verified:
        website.verification_status = VerificationStatus.VERIFIED.value
        website.verified_at = now
        website.verification_error = None
    else:
        website.verification_status = VerificationStatus.FAILED.value
        website.verification_error = message

    await ActivityService.log_event(
        db=db,
        event_category="ownership_verification",
        event_name="website_verified" if is_verified else "verification_failed",
        actor_type="user",
        actor_id=current_user.id,
        actor_email=current_user.email,
        target_type="website",
        target_id=website.id,
        target_identifier=website.domain,
        outcome="success" if is_verified else "failure",
        severity="info" if is_verified else "warning",
        source_module="websites",
        metadata={"message": message},
        commit=False,
    )

    await db.commit()

    return VerificationResultResponse(
        is_verified=is_verified,
        verification_status=website.verification_status,
        message=message,
        verified_at=website.verified_at,
    )


@router.post(
    "/{website_id}/authorize",
    response_model=WebsiteResponse,
    summary="Grant explicit scan authorization",
    description="Explicitly authorizes security vulnerability assessments against this target. Requires ownership verification first.",
)
async def authorize_website_scan(
    website_id: str,
    payload: ScanAuthorizationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WebsiteResponse:
    result = await db.execute(
        select(Website)
        .options(selectinload(Website.authorization))
        .where(Website.id == website_id, Website.user_id == current_user.id)
    )
    website = result.scalar_one_or_none()
    if website is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website target not found.")

    if website.verification_status != VerificationStatus.VERIFIED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Website ownership must be verified before granting explicit scan authorization.",
        )

    if website.is_suspended_by_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Target assessment is suspended by an administrator.",
        )

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=90)  # 90-day authorization window

    if website.authorization is None:
        auth_record = ScanAuthorization(
            website_id=website.id,
            user_id=current_user.id,
            is_authorized=True,
            authorized_by_name=payload.authorized_by_name,
            authorized_by_email=payload.authorized_by_email,
            legal_confirmation=True,
            allowed_scan_types=payload.allowed_scan_types,
            authorized_at=now,
            expires_at=expires_at,
            is_revoked=False,
        )
        db.add(auth_record)
    else:
        website.authorization.is_authorized = True
        website.authorization.authorized_by_name = payload.authorized_by_name
        website.authorization.authorized_by_email = payload.authorized_by_email
        website.authorization.legal_confirmation = True
        website.authorization.allowed_scan_types = payload.allowed_scan_types
        website.authorization.authorized_at = now
        website.authorization.expires_at = expires_at
        website.authorization.is_revoked = False
        website.authorization.revoked_at = None
        website.authorization.revocation_reason = None

    await db.commit()
    await db.refresh(website)

    logger.info("Scan authorization granted", website_id=website.id, user_id=current_user.id)
    return map_website_response(website)


@router.post(
    "/{website_id}/revoke-authorization",
    response_model=WebsiteResponse,
    summary="Revoke scan authorization",
)
async def revoke_website_authorization(
    website_id: str,
    payload: RevokeAuthorizationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WebsiteResponse:
    result = await db.execute(
        select(Website)
        .options(selectinload(Website.authorization))
        .where(Website.id == website_id, Website.user_id == current_user.id)
    )
    website = result.scalar_one_or_none()
    if website is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website target not found.")

    if website.authorization:
        now = datetime.now(timezone.utc)
        website.authorization.is_authorized = False
        website.authorization.is_revoked = True
        website.authorization.revoked_at = now
        website.authorization.revocation_reason = payload.revocation_reason or "Revoked by user."
        await db.commit()
        await db.refresh(website)

    logger.info("Scan authorization revoked", website_id=website.id, user_id=current_user.id)
    return map_website_response(website)


@router.delete(
    "/{website_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete registered website target",
)
async def delete_website(
    website_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Website).where(Website.id == website_id)
    )
    website = result.scalar_one_or_none()
    if website is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website target not found.")

    if website.user_id != current_user.id and not current_user.is_admin():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied.")

    await db.delete(website)
    await db.commit()
    logger.info("Website target deleted", website_id=website_id, user_id=current_user.id)
    return None
