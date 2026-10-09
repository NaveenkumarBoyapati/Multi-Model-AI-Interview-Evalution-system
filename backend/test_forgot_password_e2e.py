"""
End-to-End Verification of Forgot Password page and API flow
"""
import urllib.request
import json
import re

def run_tests():
    # 1. Fetch forgot_password.html from live server
    html_url = "http://127.0.0.1:8000/app/forgot_password.html"
    res_html = urllib.request.urlopen(html_url)
    html_content = res_html.read().decode("utf-8")

    print("--- HTML Initial State Checks ---")
    assert '<div id="devNoticeBox" style="display: none;"></div>' in html_content, "devNoticeBox should be hidden"
    assert "Local Testing Notice" not in html_content.split("<script>")[0], "No static notice in initial DOM"
    print("1. Initial devNoticeBox is completely hidden and empty: PASS")
    print("2. No static Local Testing Notice on initial page: PASS")

    assert 'id="email"' in html_content, "Email input exists"
    print("3. Registered Email input exists: PASS")

    assert 'id="submitBtn"' in html_content and "Send Reset Link" in html_content, "Submit button exists"
    print("4. Send Reset Link button exists: PASS")

    assert 'href="login.html"' in html_content and "Back to Login" in html_content, "Back to Login link exists"
    print("5. Back to Login link exists: PASS")

    # 2. Check JavaScript logic in forgot_password.html
    js_part = html_content.split("<script>")[1]
    assert 'deliveryStatus === "sent"' in js_part, "Handles deliveryStatus === 'sent'"
    assert "Password reset link sent successfully. Please check your email inbox and spam folder." in js_part
    assert 'deliveryStatus === "smtp_error"' in js_part, "Handles deliveryStatus === 'smtp_error'"
    assert "send the reset email. Please try again later." in js_part
    assert 'deliveryStatus === "unconfigured"' in js_part, "Handles deliveryStatus === 'unconfigured'"
    assert 'devNoticeBox.style.display = "none"' in js_part
    print("6. Frontend delivery_status handling logic strictly matches requirements: PASS")

    # 3. Live API Dispatch Check
    print("\n--- Live API Dispatch Check ---")
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/auth/forgot-password",
        data=json.dumps({"email": "naveenboyapati48@gmail.com"}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    res = urllib.request.urlopen(req)
    data = json.loads(res.read().decode("utf-8"))
    print("Status Code:", res.status)
    print("Response JSON:", data)

    assert data.get("status") == "success", "status should be success"
    assert data.get("delivery_status") == "sent", "delivery_status should be 'sent'"
    assert data.get("smtp_configured") is True, "smtp_configured should be True"
    assert data.get("message") == "Password reset link sent successfully. Please check your email inbox and spam folder."
    assert "reset_link" not in data, "reset_link must NOT be returned when delivery_status is 'sent'"
    print("7. API response matches requirements 100%: PASS")

    # 4. Anti-enumeration check
    print("\n--- Anti-Enumeration Check ---")
    req_nonexist = urllib.request.Request(
        "http://127.0.0.1:8000/api/auth/forgot-password",
        data=json.dumps({"email": "unknown_user_9999@example.com"}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    res_nonexist = urllib.request.urlopen(req_nonexist)
    data_nonexist = json.loads(res_nonexist.read().decode("utf-8"))
    assert data_nonexist.get("message") == data.get("message"), "Anti-enumeration message mismatch"
    assert data_nonexist.get("delivery_status") == "sent", "Nonexistent user should return identical delivery_status"
    print("8. Anti-enumeration check passes: PASS")

    print("\n==========================================")
    print("ALL FORGOT PASSWORD REQUIREMENTS VERIFIED!")
    print("==========================================")

if __name__ == "__main__":
    run_tests()
