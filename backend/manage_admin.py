"""
Administrator Account Management & Security Utility.

Provides safe CLI operations to:
1. Check admin account status in the SQL Server database.
2. Securely create the default administrator account if missing (without creating duplicates).
3. Safely update / reset the administrator password using standard PBKDF2-HMAC-SHA256 hashing.
"""

import sys
import argparse
from typing import Optional

from database import get_connection
from auth_utils import validate_password, hash_password, verify_password, normalize_email

DEFAULT_ADMIN_EMAIL = "admin@ai-interview.com"
DEFAULT_ADMIN_NAME = "System Administrator"
DEFAULT_ADMIN_ROLE = "System Administrator"


def check_admin_status():
    """Checks the database for administrator accounts."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, name, email, is_admin, preferred_role, created_at, password_hash
            FROM Users
            WHERE is_admin = 1
        """)
        admins = cursor.fetchall()
        print("=" * 60)
        print("ADMINISTRATOR ACCOUNT STATUS IN DATABASE")
        print("=" * 60)
        if not admins:
            print("[STATUS] No administrator accounts found in the database.")
            print(f"[ACTION] You can initialize the default administrator account via:")
            print(f"         python backend/manage_admin.py --ensure-default")
            return

        print(f"Found {len(admins)} administrator account(s):")
        for adm in admins:
            user_id, name, email, is_admin, role, created_at, pwd_hash = adm
            has_hash = bool(pwd_hash and pwd_hash.startswith("pbkdf2_sha256$"))
            matches_default = verify_password("Admin@Interview2026!", pwd_hash) if pwd_hash else False
            print(f"- ID: {user_id}")
            print(f"  Name: {name}")
            print(f"  Email: {email}")
            print(f"  Role: {role}")
            print(f"  Created: {created_at}")
            print(f"  Password Hash Format: {'Valid PBKDF2-SHA256' if has_hash else 'Invalid/Missing'}")
            print(f"  Default Password Active ('Admin@Interview2026!'): {matches_default}")
            print("-" * 60)
    finally:
        cursor.close()
        conn.close()


def ensure_default_admin():
    """Creates the default admin if missing, without duplicate creation or unexpected reset."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM Users WHERE is_admin = 1")
        admin_count = cursor.fetchone()[0]

        if admin_count > 0:
            print(f"[OK] Administrator account already exists ({admin_count} active admin user(s)). No action taken.")
            return

        clean_email = normalize_email(DEFAULT_ADMIN_EMAIL)
        cursor.execute("SELECT id FROM Users WHERE LOWER(email) = ?", (clean_email,))
        existing = cursor.fetchone()

        default_pwd = "Admin@Interview2026!"
        pwd_hash = hash_password(default_pwd)

        if existing:
            cursor.execute("""
                UPDATE Users
                SET is_admin = 1, password_hash = ?, preferred_role = ?, name = ?
                WHERE id = ?
            """, (pwd_hash, DEFAULT_ADMIN_ROLE, DEFAULT_ADMIN_NAME, existing[0]))
            print(f"[OK] Promoted existing account '{clean_email}' (ID: {existing[0]}) to Administrator.")
        else:
            cursor.execute("""
                INSERT INTO Users (name, email, password_hash, is_admin, preferred_role, created_at)
                VALUES (?, ?, ?, 1, ?, GETUTCDATE())
            """, (DEFAULT_ADMIN_NAME, clean_email, pwd_hash, DEFAULT_ADMIN_ROLE))
            print(f"[OK] Successfully created default administrator account: {clean_email}")

        conn.commit()
    finally:
        cursor.close()
        conn.close()


def reset_admin_password(email: str, new_password: str):
    """Safely updates an administrator's password after validating security rules."""
    clean_email = normalize_email(email or DEFAULT_ADMIN_EMAIL)

    valid, err_msg = validate_password(new_password)
    if not valid:
        print(f"[ERROR] Password does not meet security requirements: {err_msg}")
        sys.exit(1)

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, name, is_admin FROM Users WHERE LOWER(email) = ?", (clean_email,))
        user = cursor.fetchone()

        if not user:
            print(f"[ERROR] No user found with email '{clean_email}'.")
            sys.exit(1)

        user_id, name, is_admin = user
        if not is_admin:
            print(f"[WARNING] Account '{clean_email}' is not currently marked as admin. Setting is_admin = 1.")

        pwd_hash = hash_password(new_password)
        cursor.execute("""
            UPDATE Users
            SET password_hash = ?, is_admin = 1
            WHERE id = ?
        """, (pwd_hash, user_id))

        # Invalidate existing sessions for this user so they must re-login with the new password
        cursor.execute("UPDATE UserTokens SET is_active = 0 WHERE user_id = ?", (user_id,))
        conn.commit()

        print(f"[SUCCESS] Password for administrator '{clean_email}' (ID: {user_id}) updated successfully.")
        print("[SUCCESS] Active sessions invalidated. Please log in with the new password.")
    finally:
        cursor.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="AI Interview Evaluation - Admin Management Utility")
    parser.add_argument("--status", action="store_true", help="Display status of administrator account(s)")
    parser.add_argument("--ensure-default", action="store_true", help="Create default admin if none exists")
    parser.add_argument("--reset-password", type=str, metavar="NEW_PASSWORD", help="Set a new password for admin")
    parser.add_argument("--email", type=str, default=DEFAULT_ADMIN_EMAIL, help="Admin email (default: admin@ai-interview.com)")

    args = parser.parse_args()

    if args.status:
        check_admin_status()
    elif args.ensure_default:
        ensure_default_admin()
    elif args.reset_password:
        reset_admin_password(args.email, args.reset_password)
    else:
        # Default action: show status
        check_admin_status()


if __name__ == "__main__":
    main()
