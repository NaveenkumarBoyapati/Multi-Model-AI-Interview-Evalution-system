"""
End-to-end regression tests for:
1. User Profile Update (load, edit name/role, read-only fields, mobile omitted, validation, isolation)
2. Dashboard Progress Chart (dynamic scaling, 34 completed -> 34 points, 35 -> 35 points, terminated exclusion)
3. Result Page (Overall Progress Chart omitted, current interview details preserved)
"""

import sys
import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import get_connection
from auth_utils import hash_password, generate_secure_token, hash_token

API_BASE = "http://127.0.0.1:8000"

def api_call(url_path, method="GET", data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(f"{API_BASE}{url_path}", data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as res:
            return res.getcode(), json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def test_user_profile_flow():
    print("\n--- [TEST] 1. User Profile Flow ---")
    conn = get_connection()
    cursor = conn.cursor()

    email = "prof_tester_unique_88@example.com"
    cursor.execute("SELECT id FROM Users WHERE email = ?", (email,))
    existing = cursor.fetchone()
    if existing:
        cursor.execute("DELETE FROM UserTokens WHERE user_id = ?", (existing[0],))
        cursor.execute("DELETE FROM Interviews WHERE user_id = ?", (existing[0],))
        cursor.execute("DELETE FROM Users WHERE id = ?", (existing[0],))
        conn.commit()

    # Create test candidate
    pwd_hash = hash_password("Password99@Secure")
    cursor.execute("""
        INSERT INTO Users (name, email, password_hash, is_admin, preferred_role, created_at)
        VALUES (?, ?, ?, 0, 'Java Developer', GETUTCDATE())
    """, ("Original Candidate", email, pwd_hash))
    conn.commit()

    cursor.execute("SELECT id FROM Users WHERE email = ?", (email,))
    user_id = cursor.fetchone()[0]

    raw_token = generate_secure_token()
    cursor.execute("""
        INSERT INTO UserTokens (user_id, token_hash, created_at, expires_at, is_active)
        VALUES (?, ?, GETUTCDATE(), DATEADD(day, 1, GETUTCDATE()), 1)
    """, (user_id, hash_token(raw_token)))
    conn.commit()

    # Create an old interview for this candidate with 'Java Developer'
    cursor.execute("""
        INSERT INTO Interviews (user_id, role, overall_score, status, created_at, total_questions)
        VALUES (?, 'Java Developer', 78.0, 'COMPLETED', GETUTCDATE(), 5)
    """, (user_id,))
    conn.commit()
    cursor.execute("SELECT TOP 1 id FROM Interviews WHERE user_id = ? ORDER BY id DESC", (user_id,))
    old_interview_id = cursor.fetchone()[0]

    # 1. Profile loads
    status, res = api_call("/api/profile", method="GET", token=raw_token)
    assert status == 200, f"Expected 200, got {status}"
    assert res["user"]["name"] == "Original Candidate"
    assert res["user"]["email"] == email
    assert res["user"]["role"] == "Java Developer"
    assert res["user"]["account_type"] == "User"
    assert "mobile" not in res["user"]
    print("  [PASS] Profile loads authenticated candidate data accurately.")

    # 2. Invalid name rejected (empty/whitespace)
    status, res = api_call("/api/profile", method="PUT", data={"name": "   ", "role": "Python Developer"}, token=raw_token)
    assert status == 400, f"Expected 400 for empty name, got {status}"
    print("  [PASS] Empty full name correctly rejected with 400.")

    # 3. Invalid role rejected
    status, res = api_call("/api/profile", method="PUT", data={"name": "Valid Name", "role": "Unreal Role"}, token=raw_token)
    assert status == 400, f"Expected 400 for invalid role, got {status}"
    print("  [PASS] Invalid interview role correctly rejected with 400.")

    # 4. Valid update: change name and role to 'Python Developer'
    status, res = api_call("/api/profile", method="PUT", data={"name": "Updated Candidate", "role": "Python Developer"}, token=raw_token)
    assert status == 200, f"Expected 200, got {status}"
    assert res["user"]["name"] == "Updated Candidate"
    assert res["user"]["role"] == "Python Developer"
    assert res["user"]["email"] == email  # email preserved
    print("  [PASS] Valid profile update saved successfully.")

    # 5. Check old interview retained its original role 'Java Developer'
    cursor.execute("SELECT role FROM Interviews WHERE id = ?", (old_interview_id,))
    preserved_role = cursor.fetchone()[0]
    assert preserved_role == "Java Developer", f"Historical interview role must remain Java Developer, got {preserved_role}"
    print(f"  [PASS] Historical interview #{old_interview_id} retained its original role '{preserved_role}'.")

    # 6. User cannot modify another user's profile
    cursor.execute("""
        INSERT INTO Users (name, email, password_hash, is_admin, preferred_role, created_at)
        VALUES (?, 'victim_user_99@example.com', ?, 0, 'Web Developer', GETUTCDATE())
    """, ("Victim User", pwd_hash))
    conn.commit()
    cursor.execute("SELECT id FROM Users WHERE email = 'victim_user_99@example.com'")
    victim_id = cursor.fetchone()[0]

    # Attempt to modify victim by passing user_id: victim_id
    status, res = api_call("/api/profile", method="PUT", data={"id": victim_id, "user_id": victim_id, "name": "Hacked Name", "role": "Data Analyst"}, token=raw_token)
    assert status == 200
    assert res["user"]["id"] == user_id, "Response must only reflect authenticated user"

    cursor.execute("SELECT name, preferred_role FROM Users WHERE id = ?", (victim_id,))
    v_row = cursor.fetchone()
    assert v_row[0] == "Victim User", f"Victim name was altered to {v_row[0]}"
    assert v_row[1] == "Web Developer", f"Victim role was altered to {v_row[1]}"
    print("  [PASS] Cross-user profile modification strictly prevented (caller cannot modify another user's profile).")

    cursor.execute("DELETE FROM Users WHERE id = ?", (victim_id,))
    conn.commit()

    # 7. Unauthenticated request rejected
    status, res = api_call("/api/profile", method="GET", token="invalid_bad_token_123")
    assert status == 401, f"Expected 401 for bad token, got {status}"
    print("  [PASS] Unauthenticated/invalid token correctly rejected with 401.")

    # Clean up test user
    cursor.execute("DELETE FROM Interviews WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM UserTokens WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM Users WHERE id = ?", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()


def test_dashboard_progression_scaling():
    print("\n--- [TEST] 2. Dashboard Progression Chart Scaling (34+ Interviews) ---")
    conn = get_connection()
    cursor = conn.cursor()

    email = "chart_scaler_test_99@example.com"
    cursor.execute("SELECT id FROM Users WHERE email = ?", (email,))
    existing = cursor.fetchone()
    if existing:
        cursor.execute("DELETE FROM UserTokens WHERE user_id = ?", (existing[0],))
        cursor.execute("DELETE FROM Interviews WHERE user_id = ?", (existing[0],))
        cursor.execute("DELETE FROM Users WHERE id = ?", (existing[0],))
        conn.commit()

    pwd_hash = hash_password("Pass123!Secure")
    cursor.execute("""
        INSERT INTO Users (name, email, password_hash, is_admin, preferred_role, created_at)
        VALUES (?, ?, ?, 0, 'Data Analyst', GETUTCDATE())
    """, ("Chart Candidate", email, pwd_hash))
    conn.commit()

    cursor.execute("SELECT id FROM Users WHERE email = ?", (email,))
    cand_id = cursor.fetchone()[0]

    raw_token = generate_secure_token()
    cursor.execute("""
        INSERT INTO UserTokens (user_id, token_hash, created_at, expires_at, is_active)
        VALUES (?, ?, GETUTCDATE(), DATEADD(day, 1, GETUTCDATE()), 1)
    """, (cand_id, hash_token(raw_token)))
    conn.commit()

    # Step A: Seed 30 completed interviews and 4 terminated interviews (34 total)
    base_time = datetime(2026, 1, 1, 10, 0, 0)
    for i in range(1, 31):
        s = 50.0 + (i * 1.0)
        t = base_time + timedelta(days=i)
        cursor.execute("""
            INSERT INTO Interviews (user_id, role, overall_score, technical_score, communication_score,
                                   confidence_score, problem_solving_score, relevance_score, status,
                                   created_at, completed_at, total_questions)
            VALUES (?, 'Data Analyst', ?, 60.0, 65.0, 70.0, 60.0, 65.0, 'COMPLETED', ?, ?, 5)
        """, (cand_id, s, t, t + timedelta(minutes=10)))

    for i in range(1, 5):
        t = base_time + timedelta(days=30 + i)
        cursor.execute("""
            INSERT INTO Interviews (user_id, role, overall_score, status, created_at, total_questions, terminated_reason)
            VALUES (?, 'Data Analyst', NULL, 'Terminated', ?, 5, 'Security Tab Switch')
        """, (cand_id, t))
    conn.commit()

    status, data = api_call("/api/dashboard/summary", method="GET", token=raw_token)
    assert status == 200
    assert data["total_interviews"] == 34, f"Expected 34 total, got {data['total_interviews']}"
    assert len(data["score_progression"]) == 30, f"Expected 30 progression points, got {len(data['score_progression'])}"
    assert len(data["score_history"]) == 30
    print("  [PASS] 34 total (30 completed + 4 terminated) -> exactly 30 points in score_progression.")

    # Step B: Add 4 more completed interviews -> 34 completed + 4 terminated = 38 total -> 34 chart points
    for i in range(31, 35):
        s = 50.0 + (i * 1.0)
        t = base_time + timedelta(days=35 + i)
        cursor.execute("""
            INSERT INTO Interviews (user_id, role, overall_score, technical_score, communication_score,
                                   confidence_score, problem_solving_score, relevance_score, status,
                                   created_at, completed_at, total_questions)
            VALUES (?, 'Data Analyst', ?, 70.0, 75.0, 80.0, 70.0, 75.0, 'COMPLETED', ?, ?, 5)
        """, (cand_id, s, t, t + timedelta(minutes=10)))
    conn.commit()

    status, data = api_call("/api/dashboard/summary", method="GET", token=raw_token)
    assert len(data["score_progression"]) == 34, f"Expected 34 progression points, got {len(data['score_progression'])}"
    print("  [PASS] 34 completed interviews -> exactly 34 points in score_progression (NO 15 limit).")

    # Step C: Complete new interview #35 -> dynamically grows to 35 points
    t35 = base_time + timedelta(days=80)
    cursor.execute("""
        INSERT INTO Interviews (user_id, role, overall_score, technical_score, communication_score,
                               confidence_score, problem_solving_score, relevance_score, status,
                               created_at, completed_at, total_questions)
        VALUES (?, 'Data Analyst', 94.0, 92.0, 95.0, 90.0, 93.0, 96.0, 'COMPLETED', ?, ?, 5)
    """, (cand_id, t35, t35 + timedelta(minutes=10)))
    conn.commit()

    status, data = api_call("/api/dashboard/summary", method="GET", token=raw_token)
    assert len(data["score_progression"]) == 35, f"Expected 35 progression points, got {len(data['score_progression'])}"
    assert data["score_progression"][-1]["score"] == 94.0
    print("  [PASS] New interview #35 completed -> dynamically appears as 35th point in score_progression.")

    # Step D: Add terminated interview -> does NOT add a chart point or fake score
    t_term = base_time + timedelta(days=81)
    cursor.execute("""
        INSERT INTO Interviews (user_id, role, overall_score, status, created_at, total_questions, terminated_reason)
        VALUES (?, 'Data Analyst', NULL, 'Terminated', ?, 5, 'Tab Switch Violation')
    """, (cand_id, t_term))
    conn.commit()

    status, data = api_call("/api/dashboard/summary", method="GET", token=raw_token)
    assert len(data["score_progression"]) == 35, f"Terminated interview must not add point, got {len(data['score_progression'])}"
    assert data["latest_score"] == 94.0, f"Latest score should remain 94.0, got {data['latest_score']}"
    print("  [PASS] Terminated interview did NOT affect score progression or latest score.")

    # Clean up test user
    cursor.execute("DELETE FROM Interviews WHERE user_id = ?", (cand_id,))
    cursor.execute("DELETE FROM UserTokens WHERE user_id = ?", (cand_id,))
    cursor.execute("DELETE FROM Users WHERE id = ?", (cand_id,))
    conn.commit()
    cursor.close()
    conn.close()


def test_result_page_isolation():
    print("\n--- [TEST] 3. Result Page Isolation ---")
    result_html_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "result.html")
    with open(result_html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Ensure NO Overall Progress Chart in result.html
    assert "Overall Progress Chart" not in html, "Result page must NOT contain Overall Progress Chart"
    assert "id=\"progressChart\"" not in html, "Result page must NOT contain progressChart canvas"
    print("  [PASS] result.html has NO Overall Progress Chart.")

    # Ensure result.html preserves required sections
    required_sections = [
        "resultStatusHeading",
        "performanceText",
        "technicalBar",
        "relevanceBar",
        "conceptCoverageBar",
        "completenessBar",
        "communicationBar",
        "questionEvaluationContainer",
        "technicalFeedbackText",
        "videoModal"
    ]
    for sec in required_sections:
        assert f"id=\"{sec}\"" in html, f"result.html must retain element '{sec}'"
    print(f"  [PASS] All {len(required_sections)} essential result sections preserved on result.html.")


if __name__ == "__main__":
    test_user_profile_flow()
    test_dashboard_progression_scaling()
    test_result_page_isolation()
    print("\n==========================================")
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("==========================================\n")
