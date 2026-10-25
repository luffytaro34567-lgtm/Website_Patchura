"""Authentication, registration, token rotation, and credential management service."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import structlog
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import RefreshToken, User, UserRole
from app.schemas.auth import UserRegisterRequest
from app.security.passwords import hash_password, verify_password, pwd_context
from app.security.tokens import create_access_token, generate_refresh_token, hash_refresh_token
from app.services.activity.activity_service import ActivityService

logger = structlog.get_logger(__name__)

# Dummy hash for timing attack mitigation when user doesn't exist
DUMMY_HASH = "$2b$12$e8Y2dF8VnUuXqR1U1K1BSeKkCjJmNv8s1R5eB0q8y3gB1bZ2j4k5a"


class AuthService:
    @staticmethod
    async def register_client(
        payload: UserRegisterRequest,
        db: AsyncSession,
    ) -> User:
        """
        Registers a new Client account.
        Public registration can NEVER assign the Admin role.
        """
        # Check duplicate username (case-insensitive)
        res = await db.execute(select(User).where(func.lower(User.username) == payload.username.lower()))
        if res.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username is already registered. Please choose another.",
            )

        # Check duplicate email (case-insensitive)
        res = await db.execute(select(User).where(func.lower(User.email) == payload.email.lower()))
        if res.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email address is already registered. Please log in.",
            )

        # Hash password and create user
        hashed = hash_password(payload.password)
        user = User(
            username=payload.username,
            email=payload.email,
            hashed_password=hashed,
            role=UserRole.CLIENT.value,  # strictly enforce client role
            is_active=True,
        )
        db.add(user)
        await ActivityService.log_event(
            db=db,
            event_category="client_management",
            event_name="client_registered",
            actor_type="user",
            actor_id=user.id,
            actor_email=user.email,
            target_type="user",
            target_id=user.id,
            target_identifier=user.username,
            outcome="success",
            severity="info",
            source_module="auth",
            commit=False,
        )
        await db.commit()
        await db.refresh(user)

        logger.info("New client account registered", user_id=user.id, username=user.username)
        return user

    @staticmethod
    async def authenticate_user(
        login: str,
        password: str,
        db: AsyncSession,
    ) -> Tuple[User, str, str, int]:
        """
        Authenticates a user by email or username.
        Mitigates user enumeration and timing attacks by using uniform error messages
        and timing equalization.
        """
        normalized_login = login.strip().lower()

        # Query user by username or email (case-insensitive)
        res = await db.execute(
            select(User).where(
                or_(
                    func.lower(User.username) == normalized_login,
                    func.lower(User.email) == normalized_login,
                )
            )
        )
        user = res.scalar_one_or_none()

        if user is None:
            # Timing mitigation: run bcrypt verify against dummy hash
            pwd_context.verify(password, DUMMY_HASH)
            logger.warning("Authentication failed: user not found", login=normalized_login)
            await ActivityService.log_event(
                db=db,
                event_category="authentication",
                event_name="user_login_failed",
                actor_type="anonymous",
                target_type="user",
                target_identifier=normalized_login,
                outcome="failure",
                severity="warning",
                source_module="auth",
                metadata={"reason": "user_not_found"},
                commit=True,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username/email or password.",
            )

        now = datetime.now(timezone.utc)

        # Check account lockout (ensure timezone awareness for cross-database compatibility)
        locked_until = user.locked_until
        if locked_until is not None:
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=timezone.utc)
            if locked_until > now:
                logger.warning("Authentication blocked: account locked", user_id=user.id)
                await ActivityService.log_event(
                    db=db,
                    event_category="account_security",
                    event_name="user_login_blocked_locked",
                    actor_type="user",
                    actor_id=user.id,
                    actor_email=user.email,
                    target_type="user",
                    target_id=user.id,
                    target_identifier=user.username,
                    outcome="blocked",
                    severity="warning",
                    source_module="auth",
                    metadata={"locked_until": locked_until.isoformat()},
                    commit=True,
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account is temporarily locked due to repeated failed login attempts. Please try again later.",
                )

        if not verify_password(password, user.hashed_password):
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            logger.warning("Authentication failed: invalid password", user_id=user.id, attempts=user.failed_login_attempts)

            if user.failed_login_attempts >= 5:
                user.locked_until = now + timedelta(minutes=30)
                await ActivityService.create_security_alert(
                    db=db,
                    alert_type="repeated_failed_logins",
                    title=f"Multiple failed logins detected for '{user.username}'",
                    description=f"Account '{user.username}' ({user.email}) temporarily locked after {user.failed_login_attempts} failed login attempts.",
                    severity="high",
                    source_module="auth",
                    target_entity_type="user",
                    target_entity_id=user.id,
                    metadata={"failed_attempts": user.failed_login_attempts, "locked_until": user.locked_until.isoformat()},
                    commit=False,
                )

            await ActivityService.log_event(
                db=db,
                event_category="authentication",
                event_name="user_login_failed",
                actor_type="user",
                actor_id=user.id,
                actor_email=user.email,
                target_type="user",
                target_id=user.id,
                target_identifier=user.username,
                outcome="failure",
                severity="warning" if user.failed_login_attempts < 5 else "critical",
                source_module="auth",
                metadata={"attempt_count": user.failed_login_attempts},
                commit=False,
            )
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username/email or password.",
            )

        if not user.is_active or user.account_status in ["suspended", "terminated"]:
            logger.warning("Authentication blocked: account disabled", user_id=user.id)
            await ActivityService.log_event(
                db=db,
                event_category="authentication",
                event_name="user_login_blocked_disabled",
                actor_type="user",
                actor_id=user.id,
                actor_email=user.email,
                target_type="user",
                target_id=user.id,
                target_identifier=user.username,
                outcome="blocked",
                severity="warning",
                source_module="auth",
                metadata={"account_status": user.account_status},
                commit=True,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is disabled or suspended. Please contact support.",
            )

        # Successful authentication: reset failed attempts & record activity
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = now
        await ActivityService.log_event(
            db=db,
            event_category="authentication",
            event_name="user_login_success",
            actor_type="user",
            actor_id=user.id,
            actor_email=user.email,
            target_type="user",
            target_id=user.id,
            target_identifier=user.username,
            outcome="success",
            severity="info",
            source_module="auth",
            commit=False,
        )

        # Issue tokens
        expires_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        access_token = create_access_token(user_id=user.id, role=user.role)

        raw_refresh, token_hash = generate_refresh_token()
        family_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        refresh_record = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            family_id=family_id,
            expires_at=expires_at,
            is_revoked=False,
        )
        db.add(refresh_record)
        await db.commit()

        logger.info("User authenticated successfully", user_id=user.id, role=user.role)
        return user, access_token, raw_refresh, expires_seconds

    @staticmethod
    async def rotate_refresh_token(
        raw_refresh: str,
        db: AsyncSession,
    ) -> Tuple[User, str, str, int]:
        """
        Implements RFC 6749 refresh token rotation with reuse detection.
        If an already-revoked refresh token is presented, the entire token family
        is invalidated immediately to prevent replay attacks.
        """
        token_hash = hash_refresh_token(raw_refresh)

        res = await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        token_record = res.scalar_one_or_none()

        if token_record is None:
            logger.warning("Token rotation failed: refresh token not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
            )

        # Reuse Detection: If token is already revoked, an attacker or compromised client
        # is attempting to replay an old token. Invalidate all tokens in the family!
        if token_record.is_revoked:
            logger.error(
                "SECURITY ALERT: Refresh token reuse detected! Invalidating token family.",
                user_id=token_record.user_id,
                family_id=token_record.family_id,
            )
            now = datetime.now(timezone.utc)
            await db.execute(
                update(RefreshToken)
                .where(RefreshToken.family_id == token_record.family_id)
                .values(is_revoked=True, revoked_at=now)
            )
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token compromise detected. All active sessions have been terminated. Please log in again.",
            )

        # Check expiration
        now = datetime.now(timezone.utc)
        token_exp = token_record.expires_at
        if token_exp.tzinfo is None:
            token_exp = token_exp.replace(tzinfo=timezone.utc)

        if token_exp < now:
            logger.warning("Refresh token expired", user_id=token_record.user_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired. Please log in again.",
            )

        # Retrieve user
        user_res = await db.execute(select(User).where(User.id == token_record.user_id))
        user = user_res.scalar_one_or_none()

        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive or not found.",
            )

        # Revoke current token
        token_record.is_revoked = True
        token_record.revoked_at = now

        # Generate new rotated refresh token in the SAME family
        new_raw_refresh, new_token_hash = generate_refresh_token()
        new_expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        new_token_record = RefreshToken(
            user_id=user.id,
            token_hash=new_token_hash,
            family_id=token_record.family_id,
            expires_at=new_expires_at,
            is_revoked=False,
        )
        db.add(new_token_record)

        # Generate new access token
        access_token = create_access_token(user_id=user.id, role=user.role)
        expires_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

        await db.commit()
        logger.info("Refresh token rotated successfully", user_id=user.id)
        return user, access_token, new_raw_refresh, expires_seconds

    @staticmethod
    async def revoke_token(
        raw_refresh: str,
        db: AsyncSession,
    ) -> bool:
        """Revokes a refresh token on logout."""
        token_hash = hash_refresh_token(raw_refresh)
        now = datetime.now(timezone.utc)

        res = await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        token_record = res.scalar_one_or_none()
        if token_record and not token_record.is_revoked:
            token_record.is_revoked = True
            token_record.revoked_at = now
            await db.commit()
            logger.info("Refresh token revoked on logout", user_id=token_record.user_id)
            return True

        return False

    @staticmethod
    async def request_password_recovery(email: str, db: AsyncSession) -> Optional[str]:
        """
        Initiates password recovery for an account by email.
        Generates a 1-hour recovery token.
        Timing-safe against email enumeration.
        """
        clean_email = email.strip().lower()
        res = await db.execute(select(User).where(func.lower(User.email) == clean_email))
        user = res.scalar_one_or_none()
        if not user:
            pwd_context.verify("DummyPass123!", DUMMY_HASH)
            return None

        token = str(uuid.uuid4())
        user.recovery_token = token
        user.recovery_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        await ActivityService.log_event(
            db=db,
            event_category="account_security",
            event_name="password_recovery_requested",
            actor_type="user",
            actor_id=user.id,
            actor_email=user.email,
            target_type="user",
            target_id=user.id,
            target_identifier=user.username,
            outcome="success",
            severity="info",
            source_module="auth",
            commit=False,
        )
        await db.commit()
        await db.refresh(user)
        return token

    @staticmethod
    async def reset_password_with_token(token: str, new_password: str, db: AsyncSession) -> User:
        """
        Resets user password using a valid, non-expired recovery token.
        """
        now = datetime.now(timezone.utc)
        res = await db.execute(
            select(User).where(
                User.recovery_token == token,
                User.recovery_token_expires_at > now,
            )
        )
        user = res.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password recovery token.",
            )

        user.hashed_password = hash_password(new_password)
        user.recovery_token = None
        user.recovery_token_expires_at = None
        user.failed_login_attempts = 0
        user.locked_until = None
        user.force_password_reset = False
        if user.account_status != "terminated":
            user.is_active = True
            user.account_status = "active"

        # Security: Invalidate all existing active refresh tokens upon password reset
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user.id, RefreshToken.is_revoked == False)
            .values(is_revoked=True, revoked_at=now)
        )

        await ActivityService.log_event(
            db=db,
            event_category="account_security",
            event_name="password_reset_completed",
            actor_type="user",
            actor_id=user.id,
            actor_email=user.email,
            target_type="user",
            target_id=user.id,
            target_identifier=user.username,
            outcome="success",
            severity="info",
            source_module="auth",
            commit=False,
        )
        await db.commit()
        await db.refresh(user)
        return user
