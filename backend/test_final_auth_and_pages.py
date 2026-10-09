"""
End-to-End Verification Test for Login, Admin Access, and Create Account.
Validates:
1. SQL Server database admin account & hash verification
2. Admin login via API & admin endpoints access
3. Normal user registration with password rules enforcement & normal user role in DB
4. Normal user RBAC boundary (403 on admin endpoints)
5. Invalid credentials rejection
6. Forgot password & reset password flow
7. Production logging safety (no reset_link when ENV=production)
8. Frontend pages existence and Create Account link/button verification
"""

import os
import sys
import uuid
import pyodbc
from fastapi.testclient import TestClient

# Ensure backend directory is in python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import main
from main import app
from database import get_connection
from auth_utils import verify_password, hash_password, validate_password

client = TestClient(app)

PASSED = 0
FAILED = 0


def assert_test(desc: str, condition: bool, detail: str = ""):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  [PASS] {desc}")
    else:
        FAILED += 1
        print(f"  [FAIL] {desc}" + (f" -> {detail}" if detail else ""))


print("=" * 70)
print("RUNNING FINAL VERIFICATION FOR AUTH, ADMIN ACCESS & REGISTRATION")
print("=" * 70)

# -------------------------------------------------------------
# 1. Database Admin Account Verification
# -------------------------------------------------------------
print("\n1. SQL Server Database Admin Account Inspection:")
conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT id, name, email, is_admin, preferred_role, password_hash FROM Users WHERE is_admin = 1")
admins = cursor.fetchall()

assert_test("Administrator account exists in SQL Server", len(admins) >= 1)
admin_row = admins[0]
admin_id, admin_name, admin_email, is_admin, admin_role, admin_pwd_hash = admin_row

assert_test("Admin email is admin@ai-interview.com", admin_email.lower() == "admin@ai-interview.com")
assert_test("Admin is_admin flag is True (1)", bool(is_admin) is True)
assert_test("Admin password hash uses PBKDF2-SHA256 format", admin_pwd_hash.startswith("pbkdf2_sha256$260000$"))
assert_test("Admin password verifies correctly with 'Admin@Interview2026!'", verify_password("Admin@Interview2026!", admin_pwd_hash))

cursor.close()
conn.close()

# -------------------------------------------------------------
# 2. Admin Login & Authorization Endpoints
# -------------------------------------------------------------
print("\n2. Admin Login & Authorization Flow:")
r_admin_login = client.post("/api/auth/login", json={
    "email": "admin@ai-interview.com",
    "password": "Admin@Interview2026!",
    "role": "Admin"
})
assert_test("Admin login succeeds (200)", r_admin_login.status_code == 200)
admin_login_data = r_admin_login.json()
admin_token = admin_login_data.get("token")
assert_test("Admin login returns session token", bool(admin_token))
assert_test("Admin login payload has is_admin = True", admin_login_data.get("user", {}).get("is_admin") is True)

# Admin accessing admin dashboard API
r_ov = client.get("/api/admin/overview", headers={"Authorization": f"Bearer {admin_token}"})
assert_test("Admin token can access /api/admin/overview (200)", r_ov.status_code == 200)
assert_test("Overview returns valid total_users count", r_ov.json().get("total_users", 0) > 0)

r_users = client.get("/api/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
assert_test("Admin token can access /api/admin/users (200)", r_users.status_code == 200)

# -------------------------------------------------------------
# 3. Create Account / Registration API & Password Rules
# -------------------------------------------------------------
print("\n3. Registration API & Password Rules Validation:")

# Test password rules enforcement
r_short = client.post("/api/auth/register", json={
    "name": "Short Pass User", "email": "short@test.com", "password": "Short1!"
})
assert_test("Rejects password under 8 chars with 422", r_short.status_code == 422)

r_lower = client.post("/api/auth/register", json={
    "name": "Lower Pass User", "email": "lower@test.com", "password": "lowercase@first123"
})
assert_test("Rejects lowercase first char with 422", r_lower.status_code == 422)

r_nospec = client.post("/api/auth/register", json={
    "name": "No Spec User", "email": "nospec@test.com", "password": "NoSpecialChar123"
})
assert_test("Rejects missing special char with 422", r_nospec.status_code == 422)

# Successful registration
test_email = f"test_cand_{uuid.uuid4().hex[:8]}@example.com"
r_reg = client.post("/api/auth/register", json={
    "name": "New Candidate",
    "email": test_email,
    "password": "Valid@Password2026!",
    "role": "User",
    "preferred_role": "Python Developer"
})
assert_test("Registration with valid data succeeds (200)", r_reg.status_code == 200)
reg_data = r_reg.json()
candidate_token = reg_data.get("token")
candidate_id = reg_data.get("user", {}).get("id")
assert_test("Registration response has is_admin = False", reg_data.get("user", {}).get("is_admin") is False)

# Verify in SQL Server that candidate is NOT an admin
conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT is_admin, preferred_role FROM Users WHERE id = ?", (candidate_id,))
cand_db = cursor.fetchone()
assert_test("Database confirms new user has is_admin = 0 (Normal User)", cand_db[0] is False or cand_db[0] == 0)
cursor.close()
conn.close()

# -------------------------------------------------------------
# 4. RBAC Boundary: Candidate Cannot Access Admin Endpoints
# -------------------------------------------------------------
print("\n4. RBAC Protection & Boundary Enforcement:")
r_cand_forbidden = client.get("/api/admin/overview", headers={"Authorization": f"Bearer {candidate_token}"})
assert_test("Normal candidate accessing /api/admin/overview returns 403 Forbidden", r_cand_forbidden.status_code == 403)

r_cand_users_forbidden = client.get("/api/admin/users", headers={"Authorization": f"Bearer {candidate_token}"})
assert_test("Normal candidate accessing /api/admin/users returns 403 Forbidden", r_cand_users_forbidden.status_code == 403)

r_unauth = client.get("/api/admin/overview")
assert_test("Unauthenticated access to /api/admin/overview returns 401 Unauthorized", r_unauth.status_code == 401)

# Normal user attempting to login as Admin
r_fake_admin = client.post("/api/auth/login", json={
    "email": test_email,
    "password": "Valid@Password2026!",
    "role": "Admin"
})
assert_test("Normal user attempting to login as Admin role returns 403 Forbidden", r_fake_admin.status_code == 403)

# -------------------------------------------------------------
# 5. Normal User Login & Invalid Credentials
# -------------------------------------------------------------
print("\n5. Normal Login & Credential Verification:")
r_cand_login = client.post("/api/auth/login", json={
    "email": test_email,
    "password": "Valid@Password2026!"
})
assert_test("Candidate login succeeds (200)", r_cand_login.status_code == 200)

r_wrong_pwd = client.post("/api/auth/login", json={
    "email": test_email,
    "password": "WrongPassword@2026!"
})
assert_test("Login with wrong password returns 401 Unauthorized", r_wrong_pwd.status_code == 401)

r_wrong_email = client.post("/api/auth/login", json={
    "email": "non_existent_candidate_xyz99@domain.com",
    "password": "Valid@Password2026!"
})
assert_test("Login with unknown email returns 401 Unauthorized", r_wrong_email.status_code == 401)

# -------------------------------------------------------------
# 6. Forgot Password & Reset Password Flow
# -------------------------------------------------------------
print("\n6. Forgot Password & Reset Password Flow:")
captured_links = []
orig_send = main.send_password_reset_email
def capturing_send(to_email, user_name, link):
    captured_links.append(link)
    return orig_send(to_email, user_name, link)

main.send_password_reset_email = capturing_send
try:
    r_forgot = client.post("/api/auth/forgot-password", json={"email": test_email})
finally:
    main.send_password_reset_email = orig_send

assert_test("Forgot password endpoint returns 200 success", r_forgot.status_code == 200)
reset_link = r_forgot.json().get("reset_link") or (captured_links[0] if captured_links else None)
assert_test("Reset link generated in non-production mode", bool(reset_link and "token=" in reset_link))

reset_token = reset_link.split("token=")[1]
r_verify = client.get(f"/api/auth/verify-reset-token?token={reset_token}")
assert_test("Reset token verifies as valid", r_verify.json().get("valid") is True)

# Reset password
r_reset = client.post("/api/auth/reset-password", json={
    "token": reset_token,
    "new_password": "NewCandidatePassword@2026!",
    "confirm_password": "NewCandidatePassword@2026!"
})
assert_test("Password reset completes successfully (200)", r_reset.status_code == 200)

# Login with new password
r_login_new_pwd = client.post("/api/auth/login", json={
    "email": test_email,
    "password": "NewCandidatePassword@2026!"
})
assert_test("Login with newly reset password succeeds (200)", r_login_new_pwd.status_code == 200)

# Old password fails
r_login_old_pwd = client.post("/api/auth/login", json={
    "email": test_email,
    "password": "Valid@Password2026!"
})
assert_test("Login with old password fails (401)", r_login_old_pwd.status_code == 401)

# -------------------------------------------------------------
# 7. Production Logging & Data Security Verification
# -------------------------------------------------------------
print("\n7. Production Logging & Token Protection:")
os.environ["ENV"] = "production"
r_forgot_prod = client.post("/api/auth/forgot-password", json={"email": test_email})
assert_test("In production mode, reset_link is NOT included in API response", "reset_link" not in r_forgot_prod.json())
os.environ["ENV"] = "development"

# -------------------------------------------------------------
# 8. Frontend HTML & Routing Verification
# -------------------------------------------------------------
print("\n8. Frontend HTML & Static Routing Verification:")

# Login page
r_html_login = client.get("/app/login.html")
assert_test("GET /app/login.html returns 200", r_html_login.status_code == 200)
login_html_text = r_html_login.text
assert_test("login.html contains 'Create Account' tab", "Create Account" in login_html_text)
assert_test("login.html contains visible 'Create Account' button/link", "btnGoToRegister" in login_html_text or "create-account-btn" in login_html_text)
assert_test("login.html contains link to register.html", 'href="register.html"' in login_html_text)

# Register page
r_html_reg = client.get("/app/register.html")
assert_test("GET /app/register.html returns 200", r_html_reg.status_code == 200)
reg_html_text = r_html_reg.text
assert_test("register.html has Full Name field", 'id="regName"' in reg_html_text)
assert_test("register.html has Email field", 'id="regEmail"' in reg_html_text)
assert_test("register.html has Password field", 'id="regPassword"' in reg_html_text)
assert_test("register.html has Confirm Password field", 'id="regConfirmPassword"' in reg_html_text)
assert_test("register.html has Password Rules checklist", 'ruleMinLength' in reg_html_text and 'ruleFirstUpper' in reg_html_text and 'ruleSpecialChar' in reg_html_text)
assert_test("register.html links back to login.html", 'href="login.html"' in reg_html_text)

# Admin Dashboard
r_html_admin = client.get("/app/admin_dashboard.html")
assert_test("GET /app/admin_dashboard.html returns 200", r_html_admin.status_code == 200)

print("\n" + "=" * 70)
print(f"VERIFICATION SUMMARY: {PASSED} PASSED, {FAILED} FAILED (TOTAL {PASSED + FAILED})")
print("=" * 70)

if FAILED > 0:
    sys.exit(1)
else:
    sys.exit(0)
