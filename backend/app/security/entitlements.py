"""
PATCHORA Centralized Authorization & Subscription Entitlement Service.
Enforces that authorized administrators have unrestricted access to all
administrative capabilities and platform features without requiring any
active subscription, paid plan, renewal, or payment records.
Preserves strict server-side entitlement checks for regular users.
"""
from __future__ import annotations

from typing import Optional, Tuple
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, UserRole
from app.models.payment import Subscription, SubscriptionStatus, SubscriptionTier

logger = structlog.get_logger(__name__)


class EntitlementService:
    @staticmethod
    def is_admin(user: User) -> bool:
        """Determines if the user has verified server-side administrator role."""
        return user.role == UserRole.ADMIN.value

    @staticmethod
    def can_access_admin_portal(user: User) -> Tuple[bool, str]:
        """
        Validates access to the admin dashboard and administrative tools.
        Authorized admins NEVER require a subscription, active plan, or payment history.
        Expired, cancelled, or missing subscriptions do not block administrator access.
        """
        if not user.is_active:
            return False, "Account is suspended or deactivated."
        if not EntitlementService.is_admin(user):
            return False, "Administrative privileges required."
        return True, "Administrator access authorized without subscription requirement."

    @staticmethod
    def can_execute_admin_operation(user: User, operation_name: str) -> Tuple[bool, str]:
        """
        Validates permission to perform a specific administrative operation
        (e.g., user management, scan monitoring, security alert triage, system settings).
        """
        if not user.is_active:
            return False, "Account is suspended or deactivated."
        if not EntitlementService.is_admin(user):
            logger.warning(
                "Unauthorized administrative operation attempt",
                user_id=user.id,
                operation=operation_name,
                role=user.role,
            )
            return False, f"Administrative privileges required for {operation_name}."
        return True, f"Admin authorized for {operation_name}."

    @staticmethod
    def can_access_paid_feature(
        user: User,
        required_tier: str = SubscriptionTier.PRO.value,
        subscription: Optional[Subscription] = None,
    ) -> Tuple[bool, str]:
        """
        Evaluates feature entitlement.
        - Administrators: Exempt from all subscription and payment restrictions.
        - Regular users: Server-side check strictly requiring an active subscription of matching or higher tier.
        """
        # 1. Administrator Exemption
        if EntitlementService.is_admin(user):
            return True, "Admin exemption: Full access permitted without paid plan."

        # 2. Regular user verification
        if subscription is None:
            return False, "No active subscription found. Paid plan required."

        if subscription.status != SubscriptionStatus.ACTIVE.value:
            return False, f"Subscription status is '{subscription.status}'. Active paid plan required."

        tier_weights = {
            SubscriptionTier.FREE.value: 0,
            SubscriptionTier.PRO.value: 1,
            SubscriptionTier.ENTERPRISE.value: 2,
        }
        current_weight = tier_weights.get(subscription.plan_tier.lower(), 0)
        required_weight = tier_weights.get(required_tier.lower(), 1)

        if current_weight < required_weight:
            return (
                False,
                f"Feature requires '{required_tier.capitalize()}' subscription tier. "
                f"Current tier: '{subscription.plan_tier.capitalize()}'.",
            )

        return True, "Subscription entitlement verified."
