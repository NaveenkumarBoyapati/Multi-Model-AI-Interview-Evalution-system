"""
End-to-end verification of live Render deployment and interview submission pipeline.
Connects to: https://ai-interview-backend-new-2ccj.onrender.com
Validates:
1. Health check & live availability
2. User login / authentication
3. Async interview submission upload (/interview/upload)
4. Status polling (/interview/submission/{job_id}/status)
5. Result retrieval (/interview/{interview_id})
"""

import os
import sys
import time
import json
import uuid
import httpx

LIVE_BASE = "https://ai-interview-backend-new-2ccj.onrender.com"
API_KEY = "AI_INTERVIEW_2026_SECRET"
SAMPLE_WEBM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads", "Python_Developer_20261010_125558_058118.webm")

print("=" * 70)
print(f"TESTING LIVE RENDER BACKEND SUBMISSION: {LIVE_BASE}")
print("=" * 70)

client = httpx.Client(timeout=60.0)

# Step 1: Health Check
try:
    r_health = client.get(f"{LIVE_BASE}/health")
    print(f"[1] Health Check: HTTP {r_health.status_code} -> {r_health.json()}")
except Exception as e:
    print(f"[1] Health Check failed: {e}")
    sys.exit(1)

# Step 2: Auth Check (Login as Admin or Register test candidate)
test_email = f"live_cand_{uuid.uuid4().hex[:6]}@example.com"
test_pwd = "LivePassword@2026!"
token = None
try:
    r_reg = client.post(f"{LIVE_BASE}/api/auth/register", json={
        "name": "Live Test Candidate",
        "email": test_email,
        "password": test_pwd,
        "role": "User",
        "preferred_role": "Python Developer"
    })
    print(f"[2] Candidate Registration: HTTP {r_reg.status_code}")
    r_login = client.post(f"{LIVE_BASE}/api/auth/login", json={
        "email": test_email,
        "password": test_pwd
    })
    login_data = r_login.json()
    token = login_data.get("token")
    user_id = login_data.get("user", {}).get("id")
    print(f"[2] Candidate Login: HTTP {r_login.status_code} (User ID: {user_id})")
except Exception as e:
    print(f"[2] Auth warning: {e}")

# Step 3: Upload recording
if not os.path.exists(SAMPLE_WEBM):
    print(f"Error: Sample webm not found at {SAMPLE_WEBM}")
    sys.exit(1)

with open(SAMPLE_WEBM, "rb") as f:
    webm_bytes = f.read()

questions_payload = [
    {
        "question_number": 1,
        "question": "What is Python GIL and how does it affect multi-threading?",
        "start_time": 0.0,
        "end_time": 10.0,
        "candidate_answer": "The Global Interpreter Lock allows only one thread to execute Python bytecode at once."
    }
]

form_data = {
    "role": "Python Developer",
    "total_questions": "1",
    "attempted_questions": "1",
    "async_mode": "true",
    "question_data": json.dumps(questions_payload),
    "client_session_id": f"live_session_{uuid.uuid4().hex[:8]}"
}
if token and user_id:
    form_data["user_id"] = str(user_id)
    form_data["user_email"] = test_email

files = {
    "recording": ("Python_Developer_interview.webm", webm_bytes, "video/webm")
}
headers = {
    "X-API-Key": API_KEY
}

print(f"[3] Uploading interview recording ({len(webm_bytes)} bytes) to /interview/upload...")
r_upload = client.post(f"{LIVE_BASE}/interview/upload", data=form_data, files=files, headers=headers)
print(f"[3] Upload Response: HTTP {r_upload.status_code} -> {r_upload.text[:200]}")

upload_data = r_upload.json()
job_id = upload_data.get("job_id")

if not job_id:
    if upload_data.get("status") == "success" and upload_data.get("interview_id"):
        print(f"[3] Immediate synchronous result returned: interview_id={upload_data.get('interview_id')}")
        iid = upload_data.get("interview_id")
    else:
        print("[3] No job_id returned!")
        sys.exit(1)
else:
    print(f"[4] Polling submission job: {job_id}...")
    poll_success = False
    final_result = None
    for attempt in range(60):
        time.sleep(3)
        try:
            r_status = client.get(f"{LIVE_BASE}/interview/submission/{job_id}/status", headers=headers)
            status_data = r_status.json()
            st = status_data.get("status")
            stage = status_data.get("stage")
            prog = status_data.get("progress")
            msg = status_data.get("message")
            print(f"    [Poll #{attempt+1}] status={st}, stage={stage}, progress={prog}%: {msg}")

            if st == "failed":
                print(f"\n[FAILURE DETECTED ON LIVE SERVER]: {status_data.get('error_message')}")
                sys.exit(2)
            elif st == "completed":
                poll_success = True
                final_result = status_data.get("result")
                break
        except Exception as poll_e:
            print(f"    [Poll #{attempt+1}] Warning: {poll_e}")

    if not poll_success:
        print("\n[TIMEOUT]: Submission job did not complete in time.")
        sys.exit(3)

    iid = final_result.get("interview_id") if final_result else None
    print(f"\n[4] Job completed successfully! Generated interview_id={iid}")

# Step 5: Fetch Result Summary
if iid:
    print(f"[5] Fetching complete interview summary for interview #{iid}...")
    r_sum = client.get(f"{LIVE_BASE}/interview/{iid}", headers=headers)
    print(f"[5] Summary Response: HTTP {r_sum.status_code}")
    sum_data = r_sum.json()
    print(f"    Interview ID: {sum_data.get('interview', {}).get('id')}")
    print(f"    Role: {sum_data.get('interview', {}).get('role')}")
    print(f"    Overall Score: {sum_data.get('interview', {}).get('overall_score')}")
    print(f"    History Record: {sum_data.get('history')}")
    print(f"    Evaluation Record: {bool(sum_data.get('evaluation'))}")
    print(f"    Feedback Record: {bool(sum_data.get('feedback'))}")

    if sum_data.get("history") is not None:
        print("\n" + "=" * 70)
        print(">>> LIVE PRODUCTION FIX VERIFIED: INTERVIEWHISTORY SUCCESSFULLY PERSISTED! <<<")
        print("=" * 70)
    else:
        print("Warning: History record is None")
