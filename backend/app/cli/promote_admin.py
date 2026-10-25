"""
Administrative Account Promotion Tool
====================================
Secure CLI utility to promote an existing user account to an Administrator role.
Used for local administrative bootstrapping and controlled operations.

Usage:
    python -m app.cli.promote_admin --username <user>
"""
from __future__ import annotations

import argparse
import asyncio
import sys

from sqlalchemy import select

from app.db.session import get_session_factory, init_db
from app.models.user import User, UserRole


async def promote_user_to_admin(username: str) -> bool:
    """
    Locates an existing account by exact username, verifies uniqueness,
    and updates the role to UserRole.ADMIN, preserving all other account attributes.
    """
    await init_db()

    target_username = username.strip()
    session_factory = get_session_factory()

    async with session_factory() as session:
        # Fetch all matching accounts to verify exact count
        query = select(User).where(User.username == target_username)
        result = await session.execute(query)
        matching_users = result.scalars().all()

        if len(matching_users) == 0:
            print(
                f"[ERROR] User account with username '{target_username}' does not exist in the database.\n"
                f"Please register the account through the normal registration flow at "
                f"http://localhost:5173/register before running this tool, or use 'python -m app.cli.create_admin' "
                f"to provision a new administrator.",
                file=sys.stderr,
            )
            return False

        if len(matching_users) > 1:
            print(
                f"[ERROR] Multiple accounts ({len(matching_users)}) found with username '{target_username}'.\n"
                f"Cannot safely determine which account to promote. Please inspect the database manually.",
                file=sys.stderr,
            )
            return False

        user = matching_users[0]
        old_role = user.role

        if old_role == UserRole.ADMIN.value:
            print(
                f"[INFO] User '{user.username}' (ID: {user.id}) is already an Administrator. "
                f"No changes required."
            )
            return True

        # Apply promotion to Administrator role
        user.role = UserRole.ADMIN.value
        await session.commit()
        await session.refresh(user)

        print(
            f"[SUCCESS] User '{user.username}' was successfully promoted to Administrator.\n"
            f"  User ID:    {user.id}\n"
            f"  Username:   {user.username}\n"
            f"  Email:      {user.email}\n"
            f"  Old Role:   {old_role}\n"
            f"  New Role:   {user.role}\n"
            f"  Is Active:  {user.is_active}\n"
            f"\n"
            f"Important: If '{user.username}' is currently logged in, please sign out and log in again\n"
            f"to obtain an updated session token reflecting the Administrator role."
        )
        return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Promote an existing PATCHORA account to Administrator.")
    parser.add_argument("--username", "-u", required=True, help="Exact username of existing account to promote")

    args = parser.parse_args()

    success = asyncio.run(promote_user_to_admin(args.username))
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
