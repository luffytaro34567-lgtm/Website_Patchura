"""
Administrative Account Provisioning Tool
=========================================
Secure CLI utility to provision an initial or additional Administrator account.
Admins cannot be created via public self-service registration.

Usage:
    python -m app.cli.create_admin --username <user> --email <email> [--password <pwd>]
    If --password is not provided, it will prompt securely via getpass.
"""
from __future__ import annotations

import argparse
import asyncio
import getpass
import sys

from sqlalchemy import select

from app.db.session import get_session_factory, init_db
from app.models.user import User, UserRole
from app.security.passwords import hash_password, validate_password_strength


async def provision_admin(username: str, email: str, password: str) -> None:
    # Ensure database schema is initialized (creates tables in SQLite fallback mode)
    await init_db()

    # Validate password strength
    is_valid, error = validate_password_strength(password)
    if not is_valid:
        print(f"[ERROR] Password does not meet security policy: {error}", file=sys.stderr)
        sys.exit(1)

    username = username.strip()
    email = email.strip().lower()

    session_factory = get_session_factory()
    async with session_factory() as session:
        # Check if username exists
        res = await session.execute(select(User).where(User.username == username))
        if res.scalar_one_or_none() is not None:
            print(f"[ERROR] Username '{username}' already exists.", file=sys.stderr)
            sys.exit(1)

        # Check if email exists
        res = await session.execute(select(User).where(User.email == email))
        if res.scalar_one_or_none() is not None:
            print(f"[ERROR] Email '{email}' already exists.", file=sys.stderr)
            sys.exit(1)

        admin = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        await session.refresh(admin)

        print(f"[SUCCESS] Admin account '{admin.username}' ({admin.email}) provisioned successfully with ID: {admin.id}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Provision a PATCHORA Administrator account.")
    parser.add_argument("--username", "-u", required=True, help="Administrator username")
    parser.add_argument("--email", "-e", required=True, help="Administrator email address")
    parser.add_argument("--password", "-p", required=False, help="Administrator password (optional, prompted if omitted)")

    args = parser.parse_args()

    password = args.password
    if not password:
        password = getpass.getpass("Enter secure Administrator password: ")
        confirm = getpass.getpass("Confirm Administrator password: ")
        if password != confirm:
            print("[ERROR] Passwords do not match.", file=sys.stderr)
            sys.exit(1)

    asyncio.run(provision_admin(args.username, args.email, password))


if __name__ == "__main__":
    main()
