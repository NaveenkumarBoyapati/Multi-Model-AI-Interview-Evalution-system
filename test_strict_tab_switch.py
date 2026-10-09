import urllib.request
import urllib.parse
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
from database import get_connection

BASE_URL = "http://127.0.0.1:8000"
API_KEY = "AI_INTERVIEW_2026_SECRET"

def make_request(url, method="GET", headers=None, data=None, json_data=None):
    if headers is None:
        headers = {}
    if "X-API-Key" not in headers:
        headers["X-API-Key"] = API_KEY

    body = None
    if json_data is not None:
        body = json.dumps(json_data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif data is not None:
        if isinstance(data, dict):
            body = urllib.parse.urlencode(data).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        elif isinstance(data, bytes):
            body = data

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read()
            return resp.status, resp.headers, content
    except urllib.error.HTTPError as e:
        content = e.read()
        return e.code, e.headers, content

def encode_multipart_formdata(fields, files):
    boundary = uuid.uuid4().hex
    body = bytearray()
    for name, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        body.extend(str(value).encode("utf-8"))
        body.extend(b"\r\n")

    for name, (filename, filedata, content_type) in files.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode("utf-8"))
        body.extend(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
        body.extend(filedata if isinstance(filedata, bytes) else filedata.encode("utf-8"))
        body.extend(b"\r\n")

    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    content_type = f"multipart/form-data; boundary={boundary}"
    return content_type, bytes(body)

def run_tests():
    print("=" * 65)
    print("STRICT TAB-SWITCH TEST SUITE: END-TO-END VALIDATION")
    print("=" * 65)

    # -------------------------------------------------------------
    # TEST A: NORMAL COMPLETED INTERVIEW FLOW
    # -------------------------------------------------------------
    print("\n--- TEST A: Normal Completed Interview Flow ---")
    sample_webm_path = os.path.join(os.path.dirname(__file__), "backend", "uploads", "Data_Analyst_20261004_195828_672015.webm")
    if os.path.exists(sample_webm_path):
        with open(sample_webm_path, "rb") as f:
            normal_webm_bytes = f.read()
    else:
        normal_webm_bytes = b"\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01\x42\xf2\x81\x04\x42\xf3\x81\x08" + b"NORMAL_REC_BYTES" * 100

    fields_normal = {
        "role": "Java Developer",
        "total_questions": "2",
        "attempted_questions": "2",
        "answered_questions": "2",
        "unanswered_questions": "0",
        "tab_switch_count": "0",
        "terminated_reason": "",
        "interview_status": "COMPLETED",
        "question_data": json.dumps([
            {
                "question_number": 1,
                "question": "What is polymorphism in Java?",
                "candidate_answer": "Polymorphism allows objects to take multiple forms through method overloading and method overriding in object oriented programming.",
                "is_answered": True,
                "start_time": 1000,
                "end_time": 15000
            },
            {
                "question_number": 2,
                "question": "What is an abstract class in Java?",
                "candidate_answer": "An abstract class cannot be instantiated directly and can contain both abstract and concrete methods.",
                "is_answered": True,
                "start_time": 15000,
                "end_time": 30000
            }
        ]),
        "user_email": "naveenboyapati48@gmail.com"
    }
    files_normal = {"recording": ("normal_test.webm", normal_webm_bytes, "video/webm")}
    ctype_norm, body_norm = encode_multipart_formdata(fields_normal, files_normal)

    status_norm, _, content_norm = make_request(
        f"{BASE_URL}/interview/upload",
        method="POST",
        headers={"Content-Type": ctype_norm},
        data=body_norm
    )
    assert status_norm == 200, f"Normal upload failed: {status_norm}, {content_norm.decode()}"
    norm_data = json.loads(content_norm.decode())
    normal_id = norm_data["interview_id"]
    print(f"Normal Completed Interview ID: #{normal_id}")
    print(f"  status: {norm_data.get('interview_status')}")
    print(f"  overall_score: {norm_data.get('overall_score')}")
    print(f"  recording_available: {norm_data.get('recording_available')}")

    assert norm_data.get("interview_status") == "COMPLETED"
    assert norm_data.get("overall_score") is not None
    assert norm_data.get("evaluation") is not None
    assert norm_data.get("recording_available") is True

    # Check normal interview DB record
    conn_norm = get_connection()
    cur_norm = conn_norm.cursor()
    cur_norm.execute("SELECT status, overall_score, termination_type, security_violation FROM Interviews WHERE id = ?", (normal_id,))
    norm_db = cur_norm.fetchone()
    assert norm_db[0] == "COMPLETED"
    assert norm_db[1] is not None and float(norm_db[1]) > 0
    assert norm_db[2] is None
    assert norm_db[3] == 0 or norm_db[3] is False

    # Check EvaluationResults row exists
    cur_norm.execute("SELECT COUNT(*) FROM EvaluationResults WHERE interview_id = ?", (normal_id,))
    eval_row_count = cur_norm.fetchone()[0]
    assert eval_row_count > 0, "Normal interview MUST have EvaluationResults row"
    print("Normal interview verified: score generated, status COMPLETED, EvaluationResults row exists.")
    cur_norm.close()
    conn_norm.close()

    # -------------------------------------------------------------
    # TEST D: TERMINATION API & IDEMPOTENCY
    # -------------------------------------------------------------
    print("\n--- TEST D: Termination API & Duplicate Idempotency ---")
    term_payload = {
        "role": "Java Developer",
        "total_questions": 5,
        "tab_switch_count": 1,
        "termination_type": "TAB_SWITCH",
        "termination_reason": "Tab Switch Detected",
        "security_violation": True,
        "user_email": "naveenboyapati48@gmail.com"
    }
    status, _, content = make_request(f"{BASE_URL}/interview/terminate", method="POST", json_data=term_payload)
    assert status == 200, f"Termination API failed: {status}, {content.decode()}"
    data1 = json.loads(content.decode())
    test_id = data1["interview_id"]
    print(f"Created Terminated Interview ID: {test_id}")
    assert data1["success"] is True
    assert data1["status"] == "Terminated"
    assert data1["tab_switch_count"] == 1
    assert data1["security_violation"] is True
    assert data1["termination_type"] == "TAB_SWITCH"
    assert data1["terminated_reason"] == "Tab Switch Detected"
    print("First termination call SUCCESS:", data1)

    # Duplicate call
    term_payload_dup = {
        "interview_id": test_id,
        "role": "Java Developer",
        "tab_switch_count": 1,
        "termination_type": "TAB_SWITCH",
        "termination_reason": "Tab Switch Detected",
        "security_violation": True
    }
    status2, _, content2 = make_request(f"{BASE_URL}/interview/terminate", method="POST", json_data=term_payload_dup)
    assert status2 == 200
    data2 = json.loads(content2.decode())
    assert data2["success"] is True
    assert data2["status"] == "Terminated"
    assert data2["interview_id"] == test_id
    print("Duplicate termination call SUCCESS (Idempotent):", data2)

    # -------------------------------------------------------------
    # TEST B: TAB SWITCH UPLOAD WITH RECORDING
    # -------------------------------------------------------------
    print("\n--- TEST B: Tab Switch Upload With Recording ---")
    dummy_webm = b"\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01\x42\xf2\x81\x04\x42\xf3\x81\x08" + b"TEST_RECORDING_BYTES" * 100
    fields = {
        "interview_id": str(test_id),
        "role": "Java Developer",
        "total_questions": "5",
        "attempted_questions": "2",
        "answered_questions": "1",
        "unanswered_questions": "1",
        "tab_switch_count": "1",
        "terminated_reason": "Tab Switch Detected",
        "termination_type": "TAB_SWITCH",
        "security_violation": "true",
        "interview_status": "Terminated",
        "question_data": json.dumps([
            {
                "question_number": 1,
                "question": "What is JVM?",
                "candidate_answer": "JVM is Java Virtual Machine which runs bytecode.",
                "is_answered": True,
                "start_time": 1000,
                "end_time": 5000
            },
            {
                "question_number": 2,
                "question": "What is JDK?",
                "candidate_answer": "",
                "is_answered": False,
                "start_time": 5000,
                "end_time": 8000
            }
        ]),
        "user_email": "naveenboyapati48@gmail.com"
    }
    files = {"recording": ("test_interview.webm", dummy_webm, "video/webm")}
    ctype, body = encode_multipart_formdata(fields, files)

    status_up, _, content_up = make_request(f"{BASE_URL}/interview/upload", method="POST", headers={"Content-Type": ctype}, data=body)
    assert status_up == 200, f"Upload failed: {status_up}, {content_up.decode()}"
    up_data = json.loads(content_up.decode())
    print("Upload response for terminated interview:")
    print(f"  interview_status: {up_data['interview_status']}")
    print(f"  overall_score: {up_data['overall_score']}")
    print(f"  evaluation: {up_data['evaluation']}")
    print(f"  recording_available: {up_data['recording_available']}")
    print(f"  recording_url: {up_data['recording_url']}")

    assert up_data["interview_status"] == "Terminated"
    assert up_data["overall_score"] is None
    assert up_data["evaluation"] is None
    assert up_data["recording_available"] is True
    assert up_data["recording_url"] == f"/interview/{test_id}/recording"

    # Verify Database state directly via SQL Server
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, status, termination_type, terminated_reason, security_violation, tab_switch_count, terminated_at, recording_path, overall_score
        FROM Interviews WHERE id = ?
    """, (test_id,))
    row = cur.fetchone()
    print(f"\nSQL Server record for interview #{test_id}:")
    print(f"  id: {row[0]}")
    print(f"  status: {row[1]}")
    print(f"  termination_type: {row[2]}")
    print(f"  terminated_reason: {row[3]}")
    print(f"  security_violation: {row[4]}")
    print(f"  tab_switch_count: {row[5]}")
    print(f"  terminated_at: {row[6]}")
    print(f"  recording_path: {row[7]}")
    print(f"  overall_score: {row[8]}")

    assert row[1] == "Terminated", f"Expected status Terminated, got {row[1]}"
    assert row[2] == "TAB_SWITCH", f"Expected TAB_SWITCH, got {row[2]}"
    assert row[3] == "Tab Switch Detected", f"Expected Tab Switch Detected, got {row[3]}"
    assert bool(row[4]) is True, f"Expected security_violation True, got {row[4]}"
    assert row[5] == 1, f"Expected tab_switch_count 1, got {row[5]}"
    assert row[6] is not None, "terminated_at must NOT be None"
    assert row[7] is not None and os.path.exists(row[7]), f"recording_path must exist on disk: {row[7]}"
    assert row[8] is None, f"overall_score must be NULL for terminated interview, got {row[8]}"

    # Verify EvaluationResults has NO rows
    cur.execute("SELECT COUNT(*) FROM EvaluationResults WHERE interview_id = ?", (test_id,))
    eval_count = cur.fetchone()[0]
    assert eval_count == 0, f"Expected 0 EvaluationResults rows, got {eval_count}"
    print("Verified: NO EvaluationResults row exists.")

    # Verify Feedback has NO rows
    cur.execute("SELECT COUNT(*) FROM Feedback WHERE interview_id = ?", (test_id,))
    fb_count = cur.fetchone()[0]
    assert fb_count == 0, f"Expected 0 Feedback rows, got {fb_count}"
    print("Verified: NO Feedback row exists.")

    # -------------------------------------------------------------
    # TEST C: BACKEND OVERWRITE PROTECTION
    # -------------------------------------------------------------
    print("\n--- TEST C: Overwrite Protection ---")
    fields_ov = {
        "interview_id": str(test_id),
        "role": "Java Developer",
        "total_questions": "5",
        "tab_switch_count": "0",
        "interview_status": "COMPLETED",
        "question_data": json.dumps([{"question_number": 1, "question": "Q1", "candidate_answer": "ans"}])
    }
    files_ov = {"recording": ("test_interview2.webm", dummy_webm, "video/webm")}
    ctype_ov, body_ov = encode_multipart_formdata(fields_ov, files_ov)

    status_ov, _, content_ov = make_request(f"{BASE_URL}/interview/upload", method="POST", headers={"Content-Type": ctype_ov}, data=body_ov)
    assert status_ov == 200
    ov_data = json.loads(content_ov.decode())
    print("Overwrite attempt response:", ov_data)
    assert ov_data["interview_status"] == "Terminated", f"Overwrite succeeded incorrectly: {ov_data}"
    assert ov_data["overall_score"] is None, "Score must remain None"

    cur.execute("SELECT status, overall_score FROM Interviews WHERE id = ?", (test_id,))
    row_check = cur.fetchone()
    assert row_check[0] == "Terminated", f"Status in DB was overwritten to {row_check[0]}"
    assert row_check[1] is None, f"Score in DB was set to {row_check[1]}"
    print("Verified: Terminated interview status CANNOT be overwritten back to Completed!")

    # -------------------------------------------------------------
    # TEST RECORDING STREAMING ENDPOINT
    # -------------------------------------------------------------
    print("\n--- TEST Recording Endpoint (/interview/{id}/recording) ---")
    status_stream, headers_stream, content_stream = make_request(f"{BASE_URL}/interview/{test_id}/recording")
    assert status_stream == 200, f"Stream failed: {status_stream}"
    ct = headers_stream.get("content-type", "")
    assert ct.startswith("video/webm"), f"Wrong content-type: {ct}"
    assert len(content_stream) > 0, "Empty video content"
    print(f"Verified: /interview/{test_id}/recording streams {len(content_stream)} bytes of WebM video.")

    # -------------------------------------------------------------
    # TEST DETAILS API (/interview/{id})
    # -------------------------------------------------------------
    print("\n--- TEST Details Endpoint (/interview/{id}) ---")
    status_det, _, content_det = make_request(f"{BASE_URL}/interview/{test_id}")
    assert status_det == 200
    det_json = json.loads(content_det.decode())
    assert det_json["status"] == "success"
    int_d = det_json["interview"]
    assert int_d["status"] == "Terminated"
    assert int_d["termination_type"] == "TAB_SWITCH"
    assert int_d["terminated_reason"] == "Tab Switch Detected"
    assert int_d["security_violation"] is True
    assert int_d["tab_switch_count"] == 1
    assert int_d["overall_score"] is None
    assert det_json["evaluation"] is None
    assert det_json["feedback"] is None
    assert det_json["recording_available"] is True
    assert det_json["recording_url"] == f"/interview/{test_id}/recording"
    print("Verified: GET /interview/{id} returns clean terminated metadata and recording url.")

    # -------------------------------------------------------------
    # TEST E: HISTORICAL DATA INTEGRITY
    # -------------------------------------------------------------
    print("\n--- TEST E: Historical Completed Interviews ---")
    cur.execute("SELECT COUNT(*) FROM Interviews WHERE status = 'COMPLETED'")
    comp_count = cur.fetchone()[0]
    print(f"Total existing Completed interviews in database: {comp_count}")
    assert comp_count > 0, "Database should have existing completed interviews"

    # -------------------------------------------------------------
    # TEST F: DASHBOARD SUMMARY
    # -------------------------------------------------------------
    print("\n--- TEST F: Dashboard Analytics Exclusion ---")
    import hashlib
    raw_token = uuid.uuid4().hex + uuid.uuid4().hex
    tok_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    conn_t = get_connection()
    cur_t = conn_t.cursor()
    cur_t.execute("""
        INSERT INTO UserTokens (user_id, token_hash, expires_at, created_at, is_active)
        VALUES (31, ?, DATEADD(hour, 2, GETUTCDATE()), GETUTCDATE(), 1)
    """, (tok_hash,))
    conn_t.commit()
    cur_t.close()
    conn_t.close()
    token = raw_token
    status_dash, _, content_dash = make_request(
        f"{BASE_URL}/api/dashboard/summary",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert status_dash == 200
    dash_data = json.loads(content_dash.decode())
    print("Dashboard summary stats:")
    print(f"  total_interviews: {dash_data['total_interviews']}")
    print(f"  average_score: {dash_data['average_score']}")
    print(f"  best_score: {dash_data['best_score']}")

    # Ensure terminated interview in history has overall_score None
    found_test_in_history = False
    for h in dash_data.get("history", []):
        if h.get("report_url", "").endswith(f"id={test_id}"):
            found_test_in_history = True
            assert h["status"] == "Terminated"
            assert h["overall_score"] is None
            assert h["performance_label"] == "Terminated"
            print(f"Verified: Interview #{test_id} appears in history with overall_score=None and status=Terminated.")
            break
    assert found_test_in_history, f"Interview #{test_id} not found in candidate dashboard history"

    cur.close()
    conn.close()

    print("\n" + "=" * 65)
    print("ALL TESTS PASSED SUCCESSFULLY! (TEST B, C, D, E, F VERIFIED)")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
