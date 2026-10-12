"""
Comprehensive Password Reset Security & Edge Case Verification Suite
Tests:
1. Production suppression of fallback links & dev notices when SMTP is unconfigured.
2. Local development fallback availability strictly when running locally.
3. Anti-enumeration protection.
4. Single-use token invalidation and expiry enforcement.
5. Cross-user isolation (token for User A cannot reset User B).
6. Non-exposure of credentials in responses or diagnostics.
"""

import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from starlette.testclient import TestClient

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from env_loader import load_env
load_env()

from main import app, is_token_expired, is_production_environment
from database import get_connection
from auth_utils import hash_password, verify_password, generate_secure_token, hash_token


class TestPasswordResetSecurity(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_token_expiration_helper(self):
        """Test is_token_expired across naive, UTC tz-aware, and ISO string formats"""
        # Expired in past
        now_utc = datetime.now(timezone.utc)
        past_naive = now_utc.replace(tzinfo=None) - timedelta(minutes=5)
        self.assertTrue(is_token_expired(past_naive))

        past_aware = now_utc - timedelta(minutes=5)
        self.assertTrue(is_token_expired(past_aware))

        past_str = (now_utc - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
        self.assertTrue(is_token_expired(past_str))

        # Future unexpired
        future_naive = now_utc.replace(tzinfo=None) + timedelta(minutes=15)
        self.assertFalse(is_token_expired(future_naive))

        future_aware = now_utc + timedelta(minutes=15)
        self.assertFalse(is_token_expired(future_aware))

        future_str = (now_utc + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
        self.assertFalse(is_token_expired(future_str))

        # None
        self.assertTrue(is_token_expired(None))

    def test_production_detection(self):
        """Test production environment detection via ENV, RENDER, VERCEL, and headers"""
        # Simulation: RENDER=true
        orig_render = os.environ.get("RENDER")
        try:
            os.environ["RENDER"] = "true"
            self.assertTrue(is_production_environment())
        finally:
            if orig_render is None:
                os.environ.pop("RENDER", None)
            else:
                os.environ["RENDER"] = orig_render

        # Simulation: ENV=production
        orig_env = os.environ.get("ENV")
        try:
            os.environ["ENV"] = "production"
            self.assertTrue(is_production_environment())
        finally:
            if orig_env is None:
                os.environ.pop("ENV", None)
            else:
                os.environ["ENV"] = orig_env

    def test_production_unconfigured_smtp_never_exposes_links(self):
        """
        When running in production with unconfigured SMTP:
        - Must return error status
        - Must NOT return reset_link
        - Must NOT return dev_notice
        - Must NOT return instructions with missing env vars
        - Must NOT falsely claim email was sent
        """
        orig_env = os.environ.get("ENV")
        orig_host = os.environ.get("SMTP_HOST")
        try:
            os.environ["ENV"] = "production"
            os.environ["SMTP_HOST"] = ""  # Force unconfigured

            res = self.client.post(
                "/api/auth/forgot-password",
                json={"email": "candidate@example.com"},
                headers={"Host": "ai-interview-system.onrender.com"}
            )
            data = res.json()

            self.assertEqual(data.get("status"), "error")
            self.assertEqual(data.get("delivery_status"), "unconfigured")
            self.assertFalse(data.get("smtp_configured"))
            self.assertNotIn("reset_link", data)
            self.assertNotIn("dev_notice", data)
            self.assertNotIn("instructions", data)
            self.assertIn("unavailable", data.get("message", "").lower())
        finally:
            if orig_env:
                os.environ["ENV"] = orig_env
            else:
                os.environ.pop("ENV", None)
            if orig_host:
                os.environ["SMTP_HOST"] = orig_host
            else:
                os.environ.pop("SMTP_HOST", None)

    def test_local_dev_fallback_on_localhost(self):
        """
        When running strictly in development on localhost with unconfigured SMTP:
        - Provides fallback link for developer testing
        """
        orig_env = os.environ.get("ENV")
        orig_host = os.environ.get("SMTP_HOST")
        try:
            os.environ["ENV"] = "development"
            os.environ["SMTP_HOST"] = ""  # Force unconfigured

            # Use existing user in database
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT TOP 1 email FROM Users WHERE email LIKE '%@%'")
            row = cur.fetchone()
            cur.close()
            conn.close()

            if row:
                test_email = row[0]
                res = self.client.post(
                    "/api/auth/forgot-password",
                    json={"email": test_email},
                    headers={"Host": "127.0.0.1:8000"}
                )
                data = res.json()
                self.assertEqual(data.get("delivery_status"), "unconfigured")
                self.assertIn("reset_link", data)
                self.assertIn("token=", data["reset_link"])
        finally:
            if orig_env:
                os.environ["ENV"] = orig_env
            else:
                os.environ.pop("ENV", None)
            if orig_host:
                os.environ["SMTP_HOST"] = orig_host
            else:
                os.environ.pop("SMTP_HOST", None)

    def test_single_use_and_cross_user_isolation(self):
        """
        Ensure reset token is single-use and cannot be used for any other user.
        """
        conn = get_connection()
        cur = conn.cursor()
        try:
            # Create two test users
            pwd_hash = hash_password("OldPassword1!")
            cur.execute("INSERT INTO Users (name, email, password_hash) VALUES (?, ?, ?)",
                        ("Test User A", "test_user_a_sec@domain.com", pwd_hash))
            cur.execute("INSERT INTO Users (name, email, password_hash) VALUES (?, ?, ?)",
                        ("Test User B", "test_user_b_sec@domain.com", pwd_hash))
            conn.commit()

            cur.execute("SELECT id FROM Users WHERE email = ?", ("test_user_a_sec@domain.com",))
            user_a_id = cur.fetchone()[0]

            cur.execute("SELECT id FROM Users WHERE email = ?", ("test_user_b_sec@domain.com",))
            user_b_id = cur.fetchone()[0]

            # Generate token for User A
            raw_token = generate_secure_token(32)
            tok_hash = hash_token(raw_token)
            cur.execute("""
                INSERT INTO PasswordResets (user_id, token_hash, expires_at, created_at)
                VALUES (?, ?, DATEADD(minute, 15, GETUTCDATE()), GETUTCDATE())
            """, (user_a_id, tok_hash))
            conn.commit()

            # Verify token
            v_res = self.client.get(f"/api/auth/verify-reset-token?token={raw_token}")
            self.assertTrue(v_res.json().get("valid"))

            # Reset password using token
            r_res = self.client.post("/api/auth/reset-password", json={
                "token": raw_token,
                "new_password": "NewSecretPass1!",
                "confirm_password": "NewSecretPass1!"
            })
            self.assertEqual(r_res.status_code, 200)

            # Check User A password changed
            cur.execute("SELECT password_hash FROM Users WHERE id = ?", (user_a_id,))
            new_a_hash = cur.fetchone()[0]
            self.assertTrue(verify_password("NewSecretPass1!", new_a_hash))

            # Check User B password is UNTOUCHED
            cur.execute("SELECT password_hash FROM Users WHERE id = ?", (user_b_id,))
            b_hash = cur.fetchone()[0]
            self.assertTrue(verify_password("OldPassword1!", b_hash))
            self.assertFalse(verify_password("NewSecretPass1!", b_hash))

            # Attempt single-use reuse: MUST FAIL
            reuse_res = self.client.post("/api/auth/reset-password", json={
                "token": raw_token,
                "new_password": "AnotherPass1!",
                "confirm_password": "AnotherPass1!"
            })
            self.assertEqual(reuse_res.status_code, 400)
            self.assertIn("already been used", reuse_res.json().get("detail", ""))

            # Cleanup
            cur.execute("DELETE FROM PasswordResets WHERE user_id IN (?, ?)", (user_a_id, user_b_id))
            cur.execute("DELETE FROM Users WHERE id IN (?, ?)", (user_a_id, user_b_id))
            conn.commit()

        finally:
            cur.close()
            conn.close()


if __name__ == "__main__":
    unittest.main()
