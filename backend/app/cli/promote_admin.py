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

from typing import Optional
from sqlalchemy import func, select

from app.db.session import get_session_factory, init_db
from app.models.user import User, UserRole


async def promote_user_to_admin(
    username: Optional[str] = None,
    user_id: Optional[str] = None,
    email: Optional[str] = None,
) -> bool:
    """
    Locates an existing account by exact username, user ID (UUID), or email,
    verifies uniqueness, and updates the role to UserRole.ADMIN,
    preserving all other account attributes.
    """
    await init_db()

    if not username and not user_id and not email:
        print("[ERROR] Please provide a username, user ID, or email.", file=sys.stderr)
        return False

    session_factory = get_session_factory()

    async with session_factory() as session:
        if user_id:
            target_id = user_id.strip()
            query = select(User).where(User.id == target_id)
            target_desc = f"ID '{target_id}'"
        elif username:
            target_username = username.strip()
            query = select(User).where(User.username == target_username)
            target_desc = f"username '{target_username}'"
        else:
            target_email = email.strip().lower()
            query = select(User).where(func.lower(User.email) == target_email)
            target_desc = f"email '{target_email}'"

        result = await session.execute(query)
        matching_users = result.scalars().all()

        if len(matching_users) == 0:
            print(
                f"[ERROR] User account with {target_desc} does not exist in the database.\n"
                f"Please register the account through the normal registration flow at "
                f"http://localhost:5173/register before running this tool, or use 'python -m app.cli.create_admin' "
                f"to provision a new administrator.",
                file=sys.stderr,
            )
            return False

        if len(matching_users) > 1:
            print(
                f"[ERROR] Multiple accounts ({len(matching_users)}) found with {target_desc}.\n"
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
    parser.add_argument("--username", "-u", required=False, default=None, help="Exact username of existing account to promote")
    parser.add_argument("--id", "--user-id", dest="user_id", required=False, default=None, help="Exact Account ID (UUID) of existing account to promote")
    parser.add_argument("--email", "-e", required=False, default=None, help="Exact email address of existing account to promote")

    args = parser.parse_args()

    if not args.username and not args.user_id and not args.email:
        parser.error("At least one of --username (-u), --id, or --email (-e) must be specified.")

    success = asyncio.run(
        promote_user_to_admin(
            username=args.username,
            user_id=args.user_id,
            email=args.email,
        )
    )
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
