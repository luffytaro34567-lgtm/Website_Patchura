"""Authentication and User Account Endpoints."""
from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.auth import (
    AdminCreateUserRequest,
    AuthTokensResponse,
    PasswordRecoveryRequest,
    PasswordResetConfirmRequest,
    RefreshTokenRequest,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.security.dependencies import get_current_user, require_admin
from app.security.passwords import hash_password
from app.security.rate_limiter import RateLimit
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new Client account",
    description="Allows public users to create a Client account. Public registration cannot create Admin accounts.",
    dependencies=[Depends(RateLimit(max_requests=10, window_seconds=60, scope="auth_register"))],
)
async def register(
    payload: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    user = await AuthService.register_client(payload, db)
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=AuthTokensResponse,
    summary="User login",
    description="Authenticates via username or email and returns a short-lived access token and rotating refresh token.",
    dependencies=[Depends(RateLimit(max_requests=15, window_seconds=60, scope="auth_login"))],
)
async def login(
    payload: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthTokensResponse:
    user, access_token, refresh_token, expires_in = await AuthService.authenticate_user(
        login=payload.login,
        password=payload.password,
        db=db,
    )
    return AuthTokensResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/refresh",
    response_model=AuthTokensResponse,
    summary="Rotate refresh token and issue new access token",
    description="Exchanges a valid refresh token for a new access token and rotating refresh token. Detects token reuse.",
    dependencies=[Depends(RateLimit(max_requests=30, window_seconds=60, scope="auth_refresh"))],
)
async def refresh_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthTokensResponse:
    user, access_token, new_refresh_token, expires_in = await AuthService.rotate_refresh_token(
        raw_refresh=payload.refresh_token,
        db=db,
    )
    return AuthTokensResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        refresh_token=new_refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/logout",
    summary="Logout and revoke refresh token",
    description="Revokes the specified refresh token, ending the active session.",
)
async def logout(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    await AuthService.revoke_token(raw_refresh=payload.refresh_token, db=db)
    return {"success": True, "message": "Successfully logged out."}


@router.post(
    "/recover-password",
    summary="Request account password recovery",
    description="Initiates recovery for registered accounts. Always returns generic success for timing & enumeration safety.",
    dependencies=[Depends(RateLimit(max_requests=10, window_seconds=60, scope="auth_recover"))],
)
async def recover_password(
    payload: PasswordRecoveryRequest,
    db: AsyncSession = Depends(get_db),
):
    token = await AuthService.request_password_recovery(payload.email, db)
    resp = {
        "success": True,
        "message": "If an account exists with this email, recovery instructions have been dispatched.",
    }
    # Security: Only return recovery token in non-production debug environments
    if token and (settings.APP_ENV != "production" or settings.DEBUG):
        resp["recovery_token"] = token
    return resp


@router.post(
    "/reset-password",
    summary="Reset account password using recovery token",
    description="Resets the user's password using a valid, non-expired recovery token.",
    dependencies=[Depends(RateLimit(max_requests=10, window_seconds=60, scope="auth_reset"))],
)
async def reset_password(
    payload: PasswordResetConfirmRequest,
    db: AsyncSession = Depends(get_db),
):
    user = await AuthService.reset_password_with_token(payload.token, payload.new_password, db)
    return {
        "success": True,
        "message": f"Password reset successfully for account '{user.username}'. You may now log in with your new password.",
        "username": user.username,
    }


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Returns the authenticated user's profile details.",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)


# ── Administrative Endpoints ──────────────────────────────────────────────────

@router.get(
    "/admin/users",
    response_model=List[UserResponse],
    summary="List all users (Admin only)",
    description="Requires an authenticated Admin account.",
)
async def list_users(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> List[UserResponse]:
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [UserResponse.model_validate(u) for u in users]


@router.post(
    "/admin/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user with designated role (Admin only)",
    description="Allows authenticated administrators to provision Admin or Client accounts directly.",
)
async def admin_create_user(
    payload: AdminCreateUserRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    # Check duplicate username
    res = await db.execute(select(User).where(User.username == payload.username))
    if res.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already taken.",
        )

    # Check duplicate email
    res = await db.execute(select(User).where(User.email == payload.email))
    if res.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address is already in use.",
        )

    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role.value,
        is_active=payload.is_active,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return UserResponse.model_validate(user)
