"""
Comprehensive Verification Test for Candidate Progress Dashboard:
1. User with zero interviews
2. User with one interview
3. User with multiple interviews
4. User with multiple roles
5. User with historical interviews
6. Data security & isolation between candidates
7. Static dashboard HTML and JS verification
8. Database immutability & score preservation
"""

import os
import sys
import json
import urllib.request
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from database import get_connection
from auth_utils import generate_secure_token, hash_token

PASSED = 0
FAILED = 0

def assert_test(name: str, condition: bool, detail: str = ""):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  [PASS] {name}" + (f" ({detail})" if detail else ""))
    else:
        FAILED += 1
        print(f"  [FAIL] {name}" + (f" ({detail})" if detail else ""))

def get_or_create_token_for_user(user_id: int) -> str:
    conn = get_connection()
    cursor = conn.cursor()
    raw_token = generate_secure_token(32)
    tok_hash = hash_token(raw_token)
    expires = datetime.utcnow() + timedelta(hours=2)
    cursor.execute("""
        INSERT INTO UserTokens (user_id, token_hash, expires_at, created_at, is_active)
        VALUES (?, ?, ?, GETUTCDATE(), 1)
    """, (user_id, tok_hash, expires))
    conn.commit()
    conn.close()
    return raw_token

def fetch_summary(token: str = None):
    url = "http://127.0.0.1:8000/api/dashboard/summary"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        res = urllib.request.urlopen(req)
        return res.status, json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, None

def run_dashboard_tests():
    print("======================================================================")
    print("STARTING CANDIDATE PROGRESS DASHBOARD VERIFICATION SUITE")
    print("======================================================================")

    # 1. Unauthenticated Security Boundary
    print("\n1. Authentication & Security Boundary:")
    status_unauth, _ = fetch_summary(None)
    assert_test("Unauthenticated request to /api/dashboard/summary returns 401", status_unauth == 401)

    status_bad_token, _ = fetch_summary("invalid_token_12345")
    assert_test("Invalid bearer token returns 401", status_bad_token == 401)

    # 2. User with Zero Interviews (e.g. User 22)
    print("\n2. User with Zero Interviews (Empty State):")
    token_zero = get_or_create_token_for_user(22)
    status_zero, data_zero = fetch_summary(token_zero)
    assert_test("Zero interviews endpoint returns 200", status_zero == 200)
    assert_test("total_interviews is 0", data_zero.get("total_interviews") == 0)
    assert_test("average_score is 0.0", data_zero.get("average_score") == 0.0)
    assert_test("best_score is 0.0", data_zero.get("best_score") == 0.0)
    assert_test("latest_score is 0.0", data_zero.get("latest_score") == 0.0)
    assert_test("score_history is empty", data_zero.get("score_history") == [])
    assert_test("role_performance is empty", data_zero.get("role_performance") == [])
    assert_test("achievements all locked", all(not a["unlocked"] for a in data_zero.get("achievements", [])))
    assert_test("Empty state text present in progress comparison", "Start your first mock interview" in data_zero.get("progress_comparison", {}).get("text", ""))

    # 3. User with One Interview (e.g. User 19)
    print("\n3. User with Exactly One Interview:")
    token_one = get_or_create_token_for_user(19)
    status_one, data_one = fetch_summary(token_one)
    assert_test("One interview endpoint returns 200", status_one == 200)
    assert_test("total_interviews is 1", data_one.get("total_interviews") == 1)
    assert_test("average_score matches single interview score", data_one.get("average_score") == data_one.get("latest_score"))
    assert_test("score_history contains exactly 1 point", len(data_one.get("score_history", [])) == 1)
    achievements_one = {a["id"]: a["unlocked"] for a in data_one.get("achievements", [])}
    assert_test("First Step milestone unlocked", achievements_one.get("first_interview") is True)
    assert_test("Latest interview card contains single interview details", data_one.get("latest_interview") is not None)

    # 4. User with Multiple Interviews & Multiple Roles (User 14)
    print("\n4. User with Multiple Interviews & Multiple Roles (User 14):")
    token_multi = get_or_create_token_for_user(14)
    status_multi, data_multi = fetch_summary(token_multi)
    assert_test("Multiple interviews endpoint returns 200", status_multi == 200)
    assert_test("total_interviews reflects actual count (33)", data_multi.get("total_interviews") == 33)
    assert_test("average_score calculated accurately", 40.0 <= data_multi.get("average_score", 0) <= 60.0, f"{data_multi.get('average_score')}%")
    assert_test("best_score calculated accurately", data_multi.get("best_score", 0) >= 70.0, f"{data_multi.get('best_score')}%")
    assert_test("latest_score calculated accurately", data_multi.get("latest_score", 0) >= 70.0, f"{data_multi.get('latest_score')}%")
    assert_test("score_history has 33 points", len(data_multi.get("score_history", [])) == 33)
    
    # Check chronological ordering
    score_hist = data_multi.get("score_history", [])
    indices = [h["index"] for h in score_hist]
    assert_test("score_history points are strictly chronological", indices == list(range(1, len(score_hist) + 1)))

    # Check Skill Performance
    skills = {s["dimension"]: s for s in data_multi.get("skill_performance", [])}
    assert_test("Technical knowledge dimension evaluated", skills.get("technical", {}).get("available") is True)
    assert_test("Communication dimension evaluated", skills.get("communication", {}).get("available") is True)
    assert_test("Confidence dimension evaluated", skills.get("confidence", {}).get("available") is True)
    assert_test("Problem solving dimension evaluated", skills.get("problem_solving", {}).get("available") is True)
    assert_test("Relevance dimension evaluated", skills.get("relevance", {}).get("available") is True)

    # Check Role-Wise Performance
    roles = [r["role"] for r in data_multi.get("role_performance", [])]
    assert_test("Multiple roles evaluated in role-wise breakdown", len(roles) >= 3, f"Roles: {roles}")
    assert_test("Role stats have average and best scores", all("average_score" in r and "best_score" in r for r in data_multi.get("role_performance", [])))

    # Check Strengths & Areas to Improve
    strengths = data_multi.get("strengths", [])
    improvements = data_multi.get("improvements", [])
    assert_test("Real strengths extracted from AI evaluations", len(strengths) > 0, f"{len(strengths)} strengths")
    assert_test("Real improvement recommendations extracted", len(improvements) > 0, f"{len(improvements)} improvements")

    # Check Latest Interview Card
    latest = data_multi.get("latest_interview", {})
    assert_test("Latest interview role is present", bool(latest.get("role")))
    assert_test("Latest interview score matches latest_score", latest.get("overall_score") == data_multi.get("latest_score"))
    assert_test("Latest interview report URL points to result.html?id=", "result.html?id=" in latest.get("report_url", ""))

    # Check Achievements
    ach_dict = {a["id"]: a["unlocked"] for a in data_multi.get("achievements", [])}
    assert_test("First Step achievement unlocked", ach_dict.get("first_interview") is True)
    assert_test("Practice Pro (5 interviews) unlocked", ach_dict.get("interviews_5") is True)
    assert_test("Interview Veteran (10+ interviews) unlocked", ach_dict.get("interviews_10") is True)
    assert_test("High Scorer (70%+) unlocked", ach_dict.get("score_70") is True)
    assert_test("Multi-Role Explorer unlocked", ach_dict.get("multi_role") is True)

    # Check History List
    history = data_multi.get("history", [])
    assert_test("History contains full list of interviews", len(history) == 33)
    assert_test("History items have performance labels", all("performance_label" in h for h in history))
    assert_test("History items have report URLs", all("result.html?id=" in h.get("report_url", "") for h in history))

    # 5. User Data Security & Isolation Test
    print("\n5. Candidate Data Isolation Verification:")
    assert_test("Candidate A (33 interviews) does NOT leak into Candidate B (0 interviews)",
                data_zero.get("total_interviews") == 0 and len(data_zero.get("history", [])) == 0)
    assert_test("Candidate B cannot see Candidate A's scores or roles",
                data_zero.get("average_score") == 0.0 and len(data_zero.get("role_performance", [])) == 0)

    # 6. Static HTML & Routing Verification
    print("\n6. Frontend HTML & Asset Routing Verification:")
    html_res = urllib.request.urlopen("http://127.0.0.1:8000/app/dashboard.html")
    assert_test("GET /app/dashboard.html returns 200", html_res.status == 200)
    html_content = html_res.read().decode("utf-8")
    assert_test("dashboard.html contains Chart.js script tag", "chart.js" in html_content.lower())
    assert_test("dashboard.html contains progressChart canvas", 'id="progressChart"' in html_content)
    assert_test("dashboard.html contains 5 stats cards markup", 'class="stats stats-5"' in html_content)
    assert_test("dashboard.html contains emptyStateSection", 'id="emptyStateSection"' in html_content)
    assert_test("dashboard.html contains skillsContainer", 'id="skillsContainer"' in html_content)
    assert_test("dashboard.html contains rolesContainer", 'id="rolesContainer"' in html_content)
    assert_test("dashboard.html contains strengthsList", 'id="strengthsList"' in html_content)
    assert_test("dashboard.html contains improvementsList", 'id="improvementsList"' in html_content)
    assert_test("dashboard.html contains achievementsGrid", 'id="achievementsGrid"' in html_content)
    assert_test("dashboard.html contains historyTableBody", 'id="historyTableBody"' in html_content)
    assert_test("dashboard.html contains historySearchInput", 'id="historySearchInput"' in html_content)

    js_res = urllib.request.urlopen("http://127.0.0.1:8000/app/js/dashboard.js")
    assert_test("GET /app/js/dashboard.js returns 200", js_res.status == 200)
    js_content = js_res.read().decode("utf-8")
    assert_test("dashboard.js fetches /api/dashboard/summary", "/api/dashboard/summary" in js_content)

    # 7. Database Immutability & Historical Scores Preservation
    print("\n7. Database Immutability & Historical Scores Preservation:")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Interviews")
    total_db_interviews = cursor.fetchone()[0]
    assert_test("Total database interviews preserved (>= 115)", total_db_interviews >= 115, f"Count: {total_db_interviews}")

    historical_checks = [
        (101, 50.36, "Data Analyst"),
        (94, 50.18, "Data Analyst"),
        (86, 50.18, "Python Developer"),
        (83, 43.35, "Web Developer"),
        (80, 39.31, "Data Analyst"),
        (79, 24.93, "Java Developer"),
        (76, 34.53, "Web Developer")
    ]
    for int_id, expected_score, expected_role in historical_checks:
        cursor.execute("SELECT overall_score, role FROM Interviews WHERE id = ?", (int_id,))
        row = cursor.fetchone()
        assert_test(
            f"Historical Interview #{int_id} ({expected_role}) score preserved ({expected_score})",
            row is not None and abs(float(row[0]) - expected_score) < 0.01 and row[1] == expected_role,
            f"Actual: {float(row[0]) if row else 'None'}"
        )
    conn.close()

    print("\n======================================================================")
    print(f"CANDIDATE DASHBOARD VERIFICATION SUMMARY: {PASSED} PASSED, {FAILED} FAILED (TOTAL {PASSED + FAILED})")
    print("======================================================================")
    return FAILED == 0

if __name__ == "__main__":
    success = run_dashboard_tests()
    sys.exit(0 if success else 1)
