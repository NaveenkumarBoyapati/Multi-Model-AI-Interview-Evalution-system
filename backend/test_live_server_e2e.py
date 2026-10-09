"""
Live HTTP End-to-End Test against running server at http://127.0.0.1:8000
"""

import urllib.request
import urllib.error
import json
import uuid

base = "http://127.0.0.1:8000"

print("=" * 60)
print("TESTING LIVE SERVER AT http://127.0.0.1:8000")
print("=" * 60)

# 1. Test Static files
print("\n[1] Testing HTML pages...")
req = urllib.request.urlopen(f"{base}/app/login.html")
login_html = req.read().decode("utf-8")
assert "Create Account" in login_html, "Create Account not found in login.html"
assert "create-account-btn" in login_html, "create-account-btn not found"
assert "register.html" in login_html, "register.html link not found"
print("    login.html: OK (Contains Create Account button, tabs, and register link)")

req = urllib.request.urlopen(f"{base}/app/register.html")
reg_html = req.read().decode("utf-8")
assert "Create an Account" in reg_html, "Create an Account heading not found in register.html"
assert "regName" in reg_html and "regPassword" in reg_html, "Registration fields not found"
print("    register.html: OK (Dedicated registration page served properly)")

req = urllib.request.urlopen(f"{base}/app/admin_dashboard.html")
admin_html = req.read().decode("utf-8")
assert "Administration Portal" in admin_html, "Admin portal not found in admin_dashboard.html"
print("    admin_dashboard.html: OK")

# 2. Test Admin Login on live server
print("\n[2] Testing Admin Login on live server...")
login_payload = json.dumps({"email": "admin@ai-interview.com", "password": "Admin@Interview2026!", "role": "Admin"}).encode("utf-8")
req = urllib.request.Request(f"{base}/api/auth/login", data=login_payload, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
data = json.loads(resp.read().decode("utf-8"))
assert data.get("status") == "success"
admin_token = data.get("token")
user_data = data.get("user", {})
assert user_data.get("is_admin") is True
print(f"    Admin login OK. User: {user_data.get('name')}, Email: {user_data.get('email')}, Role: {user_data.get('preferred_role')}")

# 3. Test Admin Overview on live server with admin token
print("\n[3] Testing Admin Overview endpoint...")
req = urllib.request.Request(f"{base}/api/admin/overview", headers={"Authorization": f"Bearer {admin_token}"})
resp = urllib.request.urlopen(req)
ov = json.loads(resp.read().decode("utf-8"))
print(f"    Admin Overview OK. Registered users: {ov.get('total_users')}, Completed interviews: {ov.get('total_interviews')}")

# 4. Test User Registration on live server
print("\n[4] Testing User Registration on live server...")
rand_email = f"live_cand_{uuid.uuid4().hex[:8]}@example.com"
reg_payload = json.dumps({
    "name": "Live Test Candidate",
    "email": rand_email,
    "password": "Secure@Candidate2026!",
    "role": "User",
    "preferred_role": "Python Developer"
}).encode("utf-8")
req = urllib.request.Request(f"{base}/api/auth/register", data=reg_payload, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
reg_res = json.loads(resp.read().decode("utf-8"))
cand_token = reg_res.get("token")
cand_user = reg_res.get("user", {})
assert cand_user.get("is_admin") is False
print(f"    Registration OK. New user ID: {cand_user.get('id')}, is_admin: {cand_user.get('is_admin')}")

# 5. Test Candidate RBAC Boundary on live server
print("\n[5] Testing Candidate RBAC Boundary (should be 403)...")
try:
    req = urllib.request.Request(f"{base}/api/admin/overview", headers={"Authorization": f"Bearer {cand_token}"})
    urllib.request.urlopen(req)
    assert False, "Candidate should not have accessed admin endpoint!"
except urllib.error.HTTPError as e:
    assert e.code == 403
    print("    Candidate RBAC block OK: 403 Forbidden correctly returned.")

# 6. Test Candidate Login on live server
print("\n[6] Testing Candidate Login...")
cand_login_payload = json.dumps({"email": rand_email, "password": "Secure@Candidate2026!"}).encode("utf-8")
req = urllib.request.Request(f"{base}/api/auth/login", data=cand_login_payload, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
cand_login_res = json.loads(resp.read().decode("utf-8"))
assert cand_login_res.get("status") == "success"
print(f"    Candidate login OK: {cand_login_res.get('user', {}).get('email')}")

# 7. Test Bad Password on live server
print("\n[7] Testing Bad Credentials (should be 401)...")
try:
    bad_payload = json.dumps({"email": rand_email, "password": "WrongPassword@123"}).encode("utf-8")
    req = urllib.request.Request(f"{base}/api/auth/login", data=bad_payload, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)
    assert False, "Bad credentials should have failed!"
except urllib.error.HTTPError as e:
    assert e.code == 401
    print("    Bad credentials block OK: 401 Unauthorized correctly returned.")

# 8. Test Forgot Password on live server
print("\n[8] Testing Forgot Password endpoint...")
forgot_payload = json.dumps({"email": rand_email}).encode("utf-8")
req = urllib.request.Request(f"{base}/api/auth/forgot-password", data=forgot_payload, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
forgot_res = json.loads(resp.read().decode("utf-8"))
assert forgot_res.get("status") == "success"
print(f"    Forgot password OK. Response message: {forgot_res.get('message')}")

print("\n" + "=" * 60)
print("ALL LIVE HTTP TESTS PASSED SUCCESSFULLY ON PORT 8000!")
print("=" * 60)
