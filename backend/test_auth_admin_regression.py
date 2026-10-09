"""
Comprehensive Test Suite for Feature 1 (Admin Page & RBAC),
Feature 2 (Login & Password Validation, Forgot Password Flow),
Feature 3 (Email & Login Issues, SMTP Check), and System Regressions.
"""

import sys
import uuid
import datetime
import pyodbc
from fastapi.testclient import TestClient

import main
from main import app
from auth_utils import (
    validate_password,
    normalize_email,
    validate_email,
    hash_password,
    verify_password,
    generate_secure_token,
    hash_token
)
from email_service import is_smtp_configured, get_missing_smtp_vars
from database import get_connection

client = TestClient(app)

TOTAL_PASSED = 0
TOTAL_FAILED = 0


def record_result(test_name: str, passed: bool, detail: str = ""):
    global TOTAL_PASSED, TOTAL_FAILED
    if passed:
        TOTAL_PASSED += 1
        print(f"  [PASS] {test_name}" + (f": {detail}" if detail else ""))
    else:
        TOTAL_FAILED += 1
        print(f"  [FAIL] {test_name}" + (f": {detail}" if detail else ""))


print("=" * 70)
print("STARTING COMPREHENSIVE AUTH, ADMIN & SECURITY REGRESSION SUITE")
print("=" * 70)

# -------------------------------------------------------------
# 1. UNIT TESTS: Password Validation Rules
# -------------------------------------------------------------
print("\n--- Suite 1: Password Rule Validation ---")

# Rule 1: Min length >= 8
ok, err = validate_password("Short1!")
record_result("Reject password < 8 characters ('Short1!')", not ok and "at least 8 characters" in err)

ok, err = validate_password("Pass!1")
record_result("Reject password < 8 characters ('Pass!1')", not ok and "at least 8 characters" in err)

# Rule 2: First char uppercase A-Z
ok, err = validate_password("lowercase@123")
record_result("Reject lowercase first character ('lowercase@123')", not ok and "uppercase English letter" in err)

ok, err = validate_password("1Password@123")
record_result("Reject numeric first character ('1Password@123')", not ok and "uppercase English letter" in err)

ok, err = validate_password("@Password123")
record_result("Reject special first character ('@Password123')", not ok and "uppercase English letter" in err)

# Rule 3: Special character requirement
ok, err = validate_password("ValidPassword123")
record_result("Reject missing special character ('ValidPassword123')", not ok and "special character" in err)

# Valid combinations
ok, err = validate_password("Admin@Interview2026!")
record_result("Accept valid password ('Admin@Interview2026!')", ok)

ok, err = validate_password("Password#2026")
record_result("Accept valid password ('Password#2026')", ok)

ok, err = validate_password("Secure$User99")
record_result("Accept valid password ('Secure$User99')", ok)


# -------------------------------------------------------------
# 2. UNIT TESTS: Email Normalization & Validation
# -------------------------------------------------------------
print("\n--- Suite 2: Email Normalization & Validation ---")

normalized = normalize_email("   Candidate.User@Example.COM  ")
record_result("Normalize email (trim and lowercase)", normalized == "candidate.user@example.com")

ok, err = validate_email("candidate.user@example.com")
record_result("Validate correct email syntax", ok)

ok, err = validate_email("not-an-email")
record_result("Reject malformed email syntax", not ok)

ok, err = validate_email("")
record_result("Reject empty email", not ok)


# -------------------------------------------------------------
# 3. UNIT TESTS: Password Hashing & Verification
# -------------------------------------------------------------
print("\n--- Suite 3: Cryptographic Password Hashing & Token Hashing ---")

pwd = "TestPassword@2026!"
hashed = hash_password(pwd)
record_result("Password hash uses PBKDF2-HMAC-SHA256", hashed.startswith("pbkdf2_sha256$260000$"))
record_result("Password verifies correctly against hash", verify_password(pwd, hashed))
record_result("Wrong password rejected against hash", not verify_password("WrongPassword@2026!", hashed))

raw_tok = generate_secure_token(32)
tok_h = hash_token(raw_tok)
record_result("Token hash is 64-character SHA-256 hex digest", len(tok_h) == 64 and tok_h == hash_token(raw_tok))


# -------------------------------------------------------------
# 4. API TESTS: Registration Endpoint
# -------------------------------------------------------------
print("\n--- Suite 4: Registration API Endpoint ---")

# Weak password rejection via API
r = client.post("/api/auth/register", json={
    "name": "Candidate", "email": "test@test.com", "password": "pass"
})
record_result("API rejects short password with 422", r.status_code == 422)

r = client.post("/api/auth/register", json={
    "name": "Candidate", "email": "test@test.com", "password": "lowercase@first123"
})
record_result("API rejects lowercase first char with 422", r.status_code == 422)

r = client.post("/api/auth/register", json={
    "name": "Candidate", "email": "test@test.com", "password": "NoSpecialChar123"
})
record_result("API rejects missing special char with 422", r.status_code == 422)

# Successful registration
unique_email = f"candidate_{uuid.uuid4().hex[:8]}@domain.edu"
r = client.post("/api/auth/register", json={
    "name": "Test Candidate",
    "email": f"  {unique_email.upper()}  ",  # tests normalization
    "password": "Valid@Password2026!",
    "role": "User",
    "preferred_role": "Python Developer"
})
record_result("API registration succeeds with 200", r.status_code == 200)
reg_data = r.json()
user_token = reg_data.get("token")
user_id = reg_data.get("user", {}).get("id")
record_result("Registration returns session token", bool(user_token))
record_result("Registration normalizes email", reg_data.get("user", {}).get("email") == unique_email.lower())
record_result("Registration never exposes password hash in response", "password_hash" not in reg_data.get("user", {}))

# Duplicate registration prevention
r_dup = client.post("/api/auth/register", json={
    "name": "Test Candidate",
    "email": unique_email,
    "password": "Valid@Password2026!",
    "role": "User"
})
record_result("API rejects duplicate email with 409 Conflict", r_dup.status_code == 409)


# -------------------------------------------------------------
# 5. API TESTS: Login Endpoint & Role Enforcement
# -------------------------------------------------------------
print("\n--- Suite 5: Login API Endpoint & Role Enforcement ---")

# Valid login
r_login = client.post("/api/auth/login", json={
    "email": unique_email,
    "password": "Valid@Password2026!",
    "role": "User"
})
record_result("Login with valid credentials succeeds (200)", r_login.status_code == 200)
record_result("Login never exposes password hash in response", "password_hash" not in r_login.json().get("user", {}))

# Invalid password
r_bad_pwd = client.post("/api/auth/login", json={
    "email": unique_email,
    "password": "WrongPassword@2026!"
})
record_result("Login with incorrect password returns 401 Unauthorized", r_bad_pwd.status_code == 401)

# Unknown email
r_bad_email = client.post("/api/auth/login", json={
    "email": "non_existent_candidate_xyz99@domain.com",
    "password": "Valid@Password2026!"
})
record_result("Login with unknown email returns 401 Unauthorized", r_bad_email.status_code == 401)

# Normal user claiming Admin role at login
r_fake_admin = client.post("/api/auth/login", json={
    "email": unique_email,
    "password": "Valid@Password2026!",
    "role": "Admin"
})
record_result("Normal user attempting to login as Admin returns 403 Forbidden", r_fake_admin.status_code == 403)


# -------------------------------------------------------------
# 6. API TESTS: Admin Login & Role-Based Authorization
# -------------------------------------------------------------
print("\n--- Suite 6: Admin Login & RBAC Backend Enforcement ---")

# Admin login
r_admin_login = client.post("/api/auth/login", json={
    "email": "admin@ai-interview.com",
    "password": "Admin@Interview2026!",
    "role": "Admin"
})
record_result("Admin login succeeds with 200", r_admin_login.status_code == 200)
admin_data = r_admin_login.json()
admin_token = admin_data.get("token")
admin_user = admin_data.get("user", {})
record_result("Admin account has is_admin = True", admin_user.get("is_admin") is True)

# Unauthenticated access to admin endpoints
r_unauth = client.get("/api/admin/overview")
record_result("Unauthenticated access to /api/admin/overview returns 401", r_unauth.status_code == 401)

r_unauth_users = client.get("/api/admin/users")
record_result("Unauthenticated access to /api/admin/users returns 401", r_unauth_users.status_code == 401)

# Normal user (authenticated) accessing admin endpoints
r_forbidden = client.get("/api/admin/overview", headers={"Authorization": f"Bearer {user_token}"})
record_result("Normal user accessing /api/admin/overview returns 403 Forbidden", r_forbidden.status_code == 403)

r_forbidden_users = client.get("/api/admin/users", headers={"Authorization": f"Bearer {user_token}"})
record_result("Normal user accessing /api/admin/users returns 403 Forbidden", r_forbidden_users.status_code == 403)

# Admin accessing admin overview
r_admin_ov = client.get("/api/admin/overview", headers={"Authorization": f"Bearer {admin_token}"})
record_result("Admin accessing /api/admin/overview returns 200", r_admin_ov.status_code == 200)
ov_data = r_admin_ov.json()
record_result("Admin overview contains total_users count", "total_users" in ov_data and ov_data["total_users"] > 0)
record_result("Admin overview contains total_interviews", "total_interviews" in ov_data and ov_data["total_interviews"] >= 110)

# Admin accessing users list
r_admin_u = client.get("/api/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
record_result("Admin accessing /api/admin/users returns 200", r_admin_u.status_code == 200)
users_list = r_admin_u.json().get("users", [])
record_result("Admin users list has registered candidates", len(users_list) > 0)
record_result("Admin users list contains no password hashes", all("password_hash" not in u for u in users_list))


# -------------------------------------------------------------
# 7. API TESTS: Admin User Management Functionality
# -------------------------------------------------------------
print("\n--- Suite 7: Admin User Management Operations ---")

# View candidate interviews
r_u_interviews = client.get(f"/api/admin/users/{user_id}/interviews", headers={"Authorization": f"Bearer {admin_token}"})
record_result(f"Admin can view candidate interviews (User #{user_id})", r_u_interviews.status_code == 200)

# Update candidate details
r_update = client.put(f"/api/admin/users/{user_id}", headers={"Authorization": f"Bearer {admin_token}"}, json={
    "name": "Updated Candidate Name",
    "preferred_role": "Data Analyst"
})
record_result("Admin can update candidate role and name", r_update.status_code == 200 and r_update.json().get("user", {}).get("preferred_role") == "Data Analyst")

# Protection: Admin cannot delete their own active account
admin_id = admin_user.get("id")
r_self_del = client.delete(f"/api/admin/users/{admin_id}", headers={"Authorization": f"Bearer {admin_token}"})
record_result("Admin cannot self-delete their own account (returns 400)", r_self_del.status_code == 400)

# Protection: Cannot revoke admin from sole remaining admin
r_sole_admin = client.put(f"/api/admin/users/{admin_id}", headers={"Authorization": f"Bearer {admin_token}"}, json={
    "is_admin": False
})
record_result("Sole administrator privilege cannot be revoked (returns 400)", r_sole_admin.status_code == 400)

# Admin safely deleting a test user
r_del_cand = client.delete(f"/api/admin/users/{user_id}", headers={"Authorization": f"Bearer {admin_token}"})
record_result("Admin can safely delete test candidate user", r_del_cand.status_code == 200)


# -------------------------------------------------------------
# 8. API TESTS: Forgot Password & Reset Password Flow
# -------------------------------------------------------------
print("\n--- Suite 8: Forgot Password & Reset Flow ---")

# Register a fresh candidate for the reset test
reset_test_email = f"reset_test_{uuid.uuid4().hex[:8]}@domain.edu"
client.post("/api/auth/register", json={
    "name": "Reset Candidate",
    "email": reset_test_email,
    "password": "Initial@Password2026!"
})

# Anti-enumeration test: Existing vs Non-existing email responses
captured_links = []
orig_send = main.send_password_reset_email
def capturing_send(to_email, user_name, link):
    captured_links.append(link)
    return orig_send(to_email, user_name, link)

main.send_password_reset_email = capturing_send
try:
    r_forgot_exist = client.post("/api/auth/forgot-password", json={"email": reset_test_email})
    r_forgot_nonexist = client.post("/api/auth/forgot-password", json={"email": "nobody_exists_here_9999@domain.edu"})
finally:
    main.send_password_reset_email = orig_send

record_result("Forgot password response is indistinguishable (anti-enumeration)",
              r_forgot_exist.json().get("message") == r_forgot_nonexist.json().get("message"))

# Extract generated reset token
reset_link = r_forgot_exist.json().get("reset_link") or (captured_links[0] if captured_links else None)
reset_token = reset_link.split("token=")[1] if reset_link and "token=" in reset_link else None
record_result("Reset token generated successfully", bool(reset_token))

# Verify reset token
r_verify = client.get(f"/api/auth/verify-reset-token?token={reset_token}")
record_result("Reset token verified as valid and unexpired", r_verify.json().get("valid") is True)

# Reset password with non-matching passwords
r_mismatch = client.post("/api/auth/reset-password", json={
    "token": reset_token,
    "new_password": "New@Password2026!",
    "confirm_password": "Different@Password2026!"
})
record_result("Reject password reset when passwords do not match (422)", r_mismatch.status_code == 422)

# Reset password with rule-violating new password
r_bad_new_pwd = client.post("/api/auth/reset-password", json={
    "token": reset_token,
    "new_password": "badpassword",
    "confirm_password": "badpassword"
})
record_result("Reject password reset with rule-violating new password (422)", r_bad_new_pwd.status_code == 422)

# Execute valid password reset
r_reset_success = client.post("/api/auth/reset-password", json={
    "token": reset_token,
    "new_password": "BrandNew@Password2026!",
    "confirm_password": "BrandNew@Password2026!"
})
record_result("Execute valid password reset (200)", r_reset_success.status_code == 200)

# Token reuse prevention
r_reuse = client.post("/api/auth/reset-password", json={
    "token": reset_token,
    "new_password": "AnotherNew@Password2026!",
    "confirm_password": "AnotherNew@Password2026!"
})
record_result("Reused reset token is rejected (400)", r_reuse.status_code == 400)

# Verification of reused token shows invalid
r_verify_reused = client.get(f"/api/auth/verify-reset-token?token={reset_token}")
record_result("Reused reset token verified as invalid", r_verify_reused.json().get("valid") is False)

# Login with the new password
r_login_new = client.post("/api/auth/login", json={
    "email": reset_test_email,
    "password": "BrandNew@Password2026!"
})
record_result("Login with new password succeeds (200)", r_login_new.status_code == 200)

# Old password fails
r_login_old = client.post("/api/auth/login", json={
    "email": reset_test_email,
    "password": "Initial@Password2026!"
})
record_result("Login with old password is now rejected (401)", r_login_old.status_code == 401)


# -------------------------------------------------------------
# 9. API TESTS: Change Password Flow (Authenticated)
# -------------------------------------------------------------
print("\n--- Suite 9: Change Password Flow ---")

new_login_token = r_login_new.json().get("token")

# Change password with wrong current password
r_cp_wrong = client.post("/api/auth/change-password", headers={"Authorization": f"Bearer {new_login_token}"}, json={
    "current_password": "WrongCurrentPassword@2026!",
    "new_password": "Changed@Password2026!",
    "confirm_password": "Changed@Password2026!"
})
record_result("Change password with wrong current password rejected (400)", r_cp_wrong.status_code == 400)

# Change password with valid details
r_cp_valid = client.post("/api/auth/change-password", headers={"Authorization": f"Bearer {new_login_token}"}, json={
    "current_password": "BrandNew@Password2026!",
    "new_password": "Changed@Password2026!",
    "confirm_password": "Changed@Password2026!"
})
record_result("Change password with valid credentials succeeds (200)", r_cp_valid.status_code == 200)

# Login with changed password
r_login_changed = client.post("/api/auth/login", json={
    "email": reset_test_email,
    "password": "Changed@Password2026!"
})
record_result("Login with changed password succeeds (200)", r_login_changed.status_code == 200)


# -------------------------------------------------------------
# 10. REGRESSION TESTS: Historical Data Immutability
# -------------------------------------------------------------
print("\n--- Suite 10: Database Immutability & Interview Regression ---")

conn = get_connection()
cursor = conn.cursor()

# Verify historical interviews count
cursor.execute("SELECT COUNT(*) FROM Interviews")
total_interviews = cursor.fetchone()[0]
record_result(f"Interviews records preserved (Total count: {total_interviews} >= 110)", total_interviews >= 110)

# Verify key historical interview integrity
key_interviews = [
    (101, 50.36),
    (94, 50.18),
    (86, 50.18),
    (83, 43.35),
    (80, 39.31),
    (79, 24.93),
    (76, 34.53)
]

for inv_id, expected_score in key_interviews:
    cursor.execute("SELECT overall_score, status, role FROM Interviews WHERE id = ?", (inv_id,))
    row = cursor.fetchone()
    if row:
        actual_score = round(float(row[0]), 2)
        score_match = abs(actual_score - expected_score) < 0.05
        record_result(f"Historical Interview #{inv_id} ({row[2]}): Score {actual_score} matches expected {expected_score}", score_match)
    else:
        record_result(f"Historical Interview #{inv_id} exists", False, "Not found")

cursor.close()
conn.close()

# -------------------------------------------------------------
# FINAL RESULTS SUMMARY
# -------------------------------------------------------------
print("\n" + "=" * 70)
print(f"TEST RUN COMPLETED: {TOTAL_PASSED} PASSED, {TOTAL_FAILED} FAILED (TOTAL {TOTAL_PASSED + TOTAL_FAILED})")
print("=" * 70)

if TOTAL_FAILED > 0:
    sys.exit(1)
else:
    sys.exit(0)
