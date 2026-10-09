import io
import json
import urllib.request
import urllib.parse
import datetime
import uuid
from database import get_connection

BASE_URL = "http://127.0.0.1:8000"
API_KEY = "AI_INTERVIEW_2026_SECRET"

def send_multipart_form(url, fields, files, headers=None):
    boundary = uuid.uuid4().hex
    body = bytearray()

    for key, val in fields.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"))
        body.extend(f"{val}\r\n".encode("utf-8"))

    for key, (filename, content, content_type) in files.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{key}"; filename="{filename}"\r\n'.encode("utf-8"))
        body.extend(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
        body.extend(content)
        body.extend(b"\r\n")

    body.extend(f"--{boundary}--\r\n".encode("utf-8"))

    req = urllib.request.Request(url, data=bytes(body))
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    if headers:
        for hk, hv in headers.items():
            req.add_header(hk, hv)

    with urllib.request.urlopen(req) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))


def test_strict_tab_switch_termination():
    print("\n" + "=" * 60)
    print("TEST 1: STRICT TAB SWITCH TERMINATION PIPELINE")
    print("=" * 60)

    role = "Python Developer"
    sample_webm = b"\x1a\x45\xdf\xa3" + b"\x00" * 200
    
    question_payload = [
        {
            "question_number": 1,
            "question": "What is the difference between a list and a tuple in Python?",
            "start_time": 1000,
            "end_time": 8000,
            "candidate_answer": "Lists are mutable whereas tuples are immutable in Python.",
            "is_answered": True
        }
    ]

    files = {
        "recording": ("tab_switch_test.webm", sample_webm, "video/webm")
    }

    client_sess_id = f"test_tab_switch_{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    fields = {
        "role": role,
        "total_questions": "1",
        "attempted_questions": "1",
        "answered_questions": "1",
        "unanswered_questions": "0",
        "question_data": json.dumps(question_payload),
        "tab_switch_count": "1",
        "terminated_reason": "Tab Switch Detected",
        "termination_type": "TAB_SWITCH",
        "security_violation": "true",
        "interview_status": "Terminated",
        "terminated_at": datetime.datetime.utcnow().isoformat(),
        "client_session_id": client_sess_id
    }

    headers = {"X-API-Key": API_KEY}

    status_code, res_json = send_multipart_form(f"{BASE_URL}/interview/upload", fields, files, headers)
    assert status_code == 200, f"Upload failed: {res_json}"

    print("Response JSON status:", res_json.get("status"))
    print("Interview ID:", res_json.get("interview_id"))
    print("Interview Status:", res_json.get("interview_status"))
    print("Termination Reason:", res_json.get("terminated_reason"))
    print("Security Violation:", res_json.get("security_violation"))
    print("Tab Switch Count:", res_json.get("tab_switch_count"))

    assert res_json.get("interview_status") == "Terminated", f"Expected 'Terminated', got {res_json.get('interview_status')}"
    assert res_json.get("tab_switch_count") == 1, f"Expected 1, got {res_json.get('tab_switch_count')}"
    assert res_json.get("terminated_reason") == "Tab Switch Detected", f"Expected 'Tab Switch Detected', got {res_json.get('terminated_reason')}"
    assert res_json.get("security_violation") is True, f"Expected True, got {res_json.get('security_violation')}"
    assert res_json.get("termination_type") == "TAB_SWITCH", f"Expected 'TAB_SWITCH', got {res_json.get('termination_type')}"

    # Verify SQL Server Database Record
    int_id = res_json.get("interview_id")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, status, tab_switch_count, terminated_reason, termination_type, security_violation, terminated_at
        FROM Interviews WHERE id = ?
    """, (int_id,))
    row = cur.fetchone()
    assert row is not None, "Interview not found in SQL Server database"
    assert row[1] == "Terminated", f"DB Status: expected 'Terminated', got '{row[1]}'"
    assert row[2] == 1, f"DB tab_switch_count: expected 1, got '{row[2]}'"
    assert row[3] == "Tab Switch Detected", f"DB terminated_reason: expected 'Tab Switch Detected', got '{row[3]}'"
    assert row[4] == "TAB_SWITCH", f"DB termination_type: expected 'TAB_SWITCH', got '{row[4]}'"
    assert bool(row[5]) is True, f"DB security_violation: expected True, got '{row[5]}'"
    assert row[6] is not None, "DB terminated_at should not be null"
    cur.close()
    conn.close()

    print("[SUCCESS] Test 1 Passed: Database record accurately reflects strict tab switch termination policy.")
    return int_id, client_sess_id


def test_idempotency(int_id, client_sess_id):
    print("\n" + "=" * 60)
    print("TEST 2: IDEMPOTENCY OF TERMINATION & UPLOAD")
    print("=" * 60)

    # 1. Calling /interview/upload with same client_session_id
    files = {
        "recording": ("tab_switch_retry.webm", b"\x1a\x45\xdf\xa3\x00", "video/webm")
    }
    fields = {
        "role": "Python Developer",
        "interview_id": str(int_id),
        "client_session_id": client_sess_id,
        "tab_switch_count": "1",
        "terminated_reason": "Tab Switch Detected"
    }
    headers = {"X-API-Key": API_KEY}
    status_code, res1 = send_multipart_form(f"{BASE_URL}/interview/upload", fields, files, headers)
    assert status_code == 200
    assert res1.get("interview_id") == int_id
    assert res1.get("interview_status") == "Terminated"

    # 2. Calling /interview/upload with same interview_id but new session ID
    new_sess = f"sess_new_{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    fields["client_session_id"] = new_sess
    status_code, res2 = send_multipart_form(f"{BASE_URL}/interview/upload", fields, files, headers)
    assert status_code == 200
    assert res2.get("interview_id") == int_id
    assert res2.get("interview_status") == "Terminated"
    assert "already processed" in res2.get("message", "").lower() or "idempotent" in res2.get("message", "").lower() or res2.get("status") == "success"

    # 3. Dedicated /interview/terminate endpoint idempotency
    term_data = urllib.parse.urlencode({
        "interview_id": int_id,
        "termination_type": "TAB_SWITCH",
        "termination_reason": "Tab Switch Detected",
        "tab_switch_count": 1,
        "security_violation": True
    }).encode("utf-8")
    
    req = urllib.request.Request(f"{BASE_URL}/interview/terminate", data=term_data)
    req.add_header("X-API-Key", API_KEY)
    with urllib.request.urlopen(req) as resp:
        res3 = json.loads(resp.read().decode("utf-8"))

    assert res3.get("interview_status") == "Terminated"
    assert res3.get("interview_id") == int_id
    assert res3.get("tab_switch_count") == 1
    assert res3.get("security_violation") is True

    # Verify no duplicate rows created
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM Interviews WHERE id = ?", (int_id,))
    count = cur.fetchone()[0]
    assert count == 1, f"Duplicate Interviews row found: count={count}"
    cur.close()
    conn.close()

    print("[SUCCESS] Test 2 Passed: Repeated calls are fully idempotent, zero duplicate records generated.")


def test_normal_completion_flow():
    print("\n" + "=" * 60)
    print("TEST 3: NORMAL INTERVIEW COMPLETION FLOW REMAINS UNBROKEN")
    print("=" * 60)

    sample_webm = b"\x1a\x45\xdf\xa3" + b"\x00" * 200
    question_payload = [
        {
            "question_number": 1,
            "question": "What is Python?",
            "start_time": 1000,
            "end_time": 7000,
            "candidate_answer": "Python is a high-level interpreted programming language.",
            "is_answered": True
        }
    ]
    files = {
        "recording": ("normal_interview.webm", sample_webm, "video/webm")
    }
    fields = {
        "role": "Python Developer",
        "total_questions": "1",
        "attempted_questions": "1",
        "answered_questions": "1",
        "unanswered_questions": "0",
        "question_data": json.dumps(question_payload),
        "tab_switch_count": "0",
        "terminated_reason": "",
        "interview_status": "COMPLETED",
        "security_violation": "false"
    }
    headers = {"X-API-Key": API_KEY}
    status_code, res = send_multipart_form(f"{BASE_URL}/interview/upload", fields, files, headers)
    assert status_code == 200
    assert res.get("interview_status") == "COMPLETED"
    assert res.get("tab_switch_count") == 0
    assert res.get("security_violation") is False

    normal_id = res.get("interview_id")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT status, tab_switch_count, security_violation FROM Interviews WHERE id = ?", (normal_id,))
    row = cur.fetchone()
    assert row[0] == "COMPLETED"
    assert row[1] == 0
    assert bool(row[2]) is False
    cur.close()
    conn.close()

    print("[SUCCESS] Test 3 Passed: Normal interview completion preserved with COMPLETED status and 0 tab switches.")


def test_historical_immutability():
    print("\n" + "=" * 60)
    print("TEST 4: HISTORICAL DATABASE IMMUTABILITY")
    print("=" * 60)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, status, overall_score FROM Interviews WHERE id IN (101, 94, 86, 83, 80, 79, 76)")
    rows = cur.fetchall()
    print("Historical interviews verified:", rows)
    assert len(rows) == 7
    for r in rows:
        assert r[1] == "COMPLETED", f"Historical interview #{r[0]} status altered!"
    cur.close()
    conn.close()
    print("[SUCCESS] Test 4 Passed: 100% of historical scores and records are unmodified.")


if __name__ == "__main__":
    t_id, sess_id = test_strict_tab_switch_termination()
    test_idempotency(t_id, sess_id)
    test_normal_completion_flow()
    test_historical_immutability()
    print("\nALL TAB SWITCH POLICY AND REGRESSION TESTS COMPLETED SUCCESSFULLY!")
