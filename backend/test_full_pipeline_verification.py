import sys
import os
import httpx
import json
import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import get_connection

def test_full_pipeline():
    print("==================================================")
    print("STEP 1: Check server health")
    print("==================================================")
    health_resp = requests.get("http://127.0.0.1:8000/health", timeout=5)
    print("Health response:", health_resp.status_code, health_resp.json())
    assert health_resp.status_code == 200, "Health check failed"

    print("\n==================================================")
    print("STEP 2: Find a recording file for testing")
    print("==================================================")
    uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
    webm_files = glob.glob(os.path.join(uploads_dir, "*.webm"))
    assert len(webm_files) > 0, "No webm recording files found in uploads"
    sample_webm = webm_files[0]
    print(f"Using recording: {sample_webm} ({os.path.getsize(sample_webm)} bytes)")

    print("\n==================================================")
    print("STEP 3: POST /interview/upload with 3 questions (2 answered, 1 unanswered)")
    print("==================================================")
    question_data = [
        {
            "question_number": 1,
            "question": "Tell me about yourself.",
            "type": "Introduction",
            "start_time": 0.0,
            "end_time": 10.0,
            "start_ms": 0,
            "end_ms": 10000,
            "candidate_answer": "",
            "is_answered": False
        },
        {
            "question_number": 2,
            "question": "What are your strengths and how can they help you in this role?",
            "type": "HR",
            "start_time": 10.0,
            "end_time": 16.0,
            "start_ms": 10000,
            "end_ms": 16000,
            "candidate_answer": "",
            "is_answered": False
        },
        {
            "question_number": 3,
            "question": "What is hashCode()?",
            "type": "Technical",
            "start_time": 16.0,
            "end_time": 18.0,
            "start_ms": 16000,
            "end_ms": 18000,
            "candidate_answer": "",
            "is_answered": False
        }
    ]

    with open(sample_webm, "rb") as f:
        files = {
            "recording": (os.path.basename(sample_webm), f, "video/webm")
        }
        data = {
            "role": "Java Developer",
            "total_questions": "3",
            "attempted_questions": "3",
            "answered_questions": "2",
            "unanswered_questions": "1",
            "tab_switch_count": "0",
            "terminated_reason": "",
            "recording_start_time": "0.0",
            "question_data": json.dumps(question_data)
        }
        headers = {
            "X-API-Key": "AI_INTERVIEW_2026_SECRET"
        }

        print("Sending upload request to http://127.0.0.1:8000/interview/upload...")
        with httpx.Client(timeout=120.0) as client:
            resp = client.post("http://127.0.0.1:8000/interview/upload", files=files, data=data, headers=headers)

    print(f"HTTP Status: {resp.status_code}")
    res_json = resp.json()
    print("Response status:", res_json.get("status"))
    print("Interview ID:", res_json.get("interview_id"))
    assert resp.status_code == 200, f"Upload returned non-200: {resp.text}"
    assert res_json.get("status") == "success", f"Upload status not success: {res_json}"

    new_interview_id = res_json["interview_id"]
    print(f"\n==================================================")
    print(f"STEP 4: Verify SQL Server tables for interview_id = {new_interview_id}")
    print(f"==================================================")

    conn = get_connection()
    cur = conn.cursor()

    # 1. Check Interviews table
    cur.execute("SELECT id, role, status, duration_seconds, overall_score, technical_score, communication_score FROM Interviews WHERE id = ?", (new_interview_id,))
    int_row = cur.fetchone()
    print("1. Interviews table row:")
    print("  ", int_row)
    assert int_row is not None, "Interview record not found in Interviews table"
    assert int_row[2] == "COMPLETED", f"Status expected COMPLETED, got {int_row[2]}"

    # 2. Check InterviewAnswers table
    cur.execute("""
        SELECT question_number, question_id, question_text, answer_text, word_count, start_ms, end_ms, overall_answer_score, technical_score
        FROM InterviewAnswers
        WHERE interview_id = ?
        ORDER BY question_number
    """, (new_interview_id,))
    ans_rows = cur.fetchall()
    print("\n2. InterviewAnswers table rows:")
    for r in ans_rows:
        print("  ", r)

    assert len(ans_rows) == 3, f"Expected 3 answers rows, found {len(ans_rows)}"

    # Check Q1 (should be answered)
    q1 = ans_rows[0]
    print(f"\nQ1 check:")
    print(f"  question_number: {q1[0]}")
    print(f"  question_id: {q1[1]}")
    print(f"  answer_text: '{q1[3]}'")
    print(f"  word_count: {q1[4]}")
    print(f"  start_ms: {q1[5]}")
    print(f"  end_ms: {q1[6]}")
    print(f"  overall_score: {q1[7]}")
    assert q1[3] is not None and len(q1[3]) > 0, "Q1 answer_text MUST NOT be NULL or empty for answered question"
    assert q1[4] is not None and q1[4] > 0, "Q1 word_count MUST NOT be NULL or 0 for answered question"
    assert q1[5] is not None, "Q1 start_ms MUST NOT be NULL"
    assert q1[6] is not None, "Q1 end_ms MUST NOT be NULL"

    # Check Q3 (should be unanswered)
    q3 = ans_rows[2]
    print(f"\nQ3 check (unanswered):")
    print(f"  question_number: {q3[0]}")
    print(f"  answer_text: {repr(q3[3])}")
    print(f"  word_count: {q3[4]}")
    print(f"  overall_score: {q3[7]}")
    assert q3[3] is None or q3[3] == "", "Q3 answer_text must be empty/None for unanswered question"
    assert q3[4] == 0, f"Q3 word_count must be 0, got {q3[4]}"
    assert q3[7] == 0.0, f"Q3 overall_score must be 0.0, got {q3[7]}"

    # 3. Check EvaluationResults table
    cur.execute("SELECT interview_id, overall_score, technical_score, answered_count, answers_evaluated FROM EvaluationResults WHERE interview_id = ?", (new_interview_id,))
    eval_row = cur.fetchone()
    print("\n3. EvaluationResults table row:")
    print("  ", eval_row)
    assert eval_row is not None, "EvaluationResults row missing"
    assert eval_row[3] == 2, f"Expected 2 answered questions, got {eval_row[3]}"

    # 4. Check InterviewHistory table
    cur.execute("SELECT interview_id, user_id, role, overall_score FROM InterviewHistory WHERE interview_id = ?", (new_interview_id,))
    hist_row = cur.fetchone()
    print("\n4. InterviewHistory table row:")
    print("  ", hist_row)
    assert hist_row is not None, "InterviewHistory row missing"

    # 5. Check Feedback table
    cur.execute("SELECT interview_id, summary, overall_performance FROM Feedback WHERE interview_id = ?", (new_interview_id,))
    fb_row = cur.fetchone()
    print("\n5. Feedback table row:")
    print("  ", fb_row)
    assert fb_row is not None, "Feedback row missing"

    cur.close()
    conn.close()

    print("\n==================================================")
    print("STEP 5: Test GET /interview/{interview_id} endpoint")
    print("==================================================")
    get_resp = requests.get(f"http://127.0.0.1:8000/interview/{new_interview_id}", timeout=5)
    print(f"GET /interview/{new_interview_id} status: {get_resp.status_code}")
    assert get_resp.status_code == 200, "GET /interview endpoint failed"
    get_data = get_resp.json()
    assert get_data["interview"]["id"] == new_interview_id
    assert len(get_data["answers"]) == 3
    print("All assertions passed!")
    print(f"\nSUCCESS! Verified interview #{new_interview_id} has non-NULL answers and full persistence across all tables.")

if __name__ == "__main__":
    test_full_pipeline()
