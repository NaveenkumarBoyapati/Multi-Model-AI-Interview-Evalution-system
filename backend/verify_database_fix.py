import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from starlette.testclient import TestClient
from main import app
from database import get_connection

def run_verification():
    print("=" * 70)
    print("AI INTERVIEW EVALUATION SYSTEM: DATABASE VERIFICATION TEST")
    print("=" * 70)

    client = TestClient(app)

    # Use existing recording in uploads
    recording_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads", "Python_Developer_20261003_121525_257805.webm")
    assert os.path.exists(recording_path), f"Recording file not found: {recording_path}"
    print(f"Using recording: {os.path.basename(recording_path)} ({os.path.getsize(recording_path)} bytes)")

    # -------------------------------------------------------------
    # TEST 1: Update Existing Interview ID = 45
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print("TEST 1: Upload and Transcribe for Existing Interview ID = 45")
    print("=" * 70)

    # Q1 & Q2 answered by speech in recording, Q3 unanswered
    q_data_45 = [
        {
            "question_number": 1,
            "question": "Tell me about yourself.",
            "type": "HR",
            "start_time": 0.0,
            "end_time": 14.5,
            "start_ms": 0,
            "end_ms": 14500,
            "candidate_answer": "",
            "is_answered": False
        },
        {
            "question_number": 2,
            "question": "Why do you want to work in this field?",
            "type": "HR",
            "start_time": 14.5,
            "end_time": 26.0,
            "start_ms": 14500,
            "end_ms": 26000,
            "candidate_answer": "",
            "is_answered": False
        },
        {
            "question_number": 3,
            "question": "Explain the difference between `is` checks with small integers.",
            "type": "ROLE",
            "start_time": 26.0,
            "end_time": 30.0,
            "start_ms": 26000,
            "end_ms": 30000,
            "candidate_answer": "",
            "is_answered": False
        }
    ]

    with open(recording_path, "rb") as f:
        response_45 = client.post(
            "/interview/upload",
            data={
                "role": "Python Developer",
                "total_questions": "3",
                "attempted_questions": "3",
                "answered_questions": "2",
                "unanswered_questions": "1",
                "interview_id": "45",
                "recording_start_time": "0.0",
                "tab_switch_count": "0",
                "terminated_reason": "",
                "question_data": json.dumps(q_data_45)
            },
            files={
                "recording": ("Python_Developer_interview.webm", f, "video/webm")
            },
            headers={
                "X-API-Key": "AI_INTERVIEW_2026_SECRET"
            }
        )

    print(f"HTTP Status (Interview 45): {response_45.status_code}")
    res_json_45 = response_45.json()
    print("Response Status:", res_json_45.get("status"))
    print("Interview ID returned:", res_json_45.get("interview_id"))
    print("Overall Score:", res_json_45.get("evaluation", {}).get("overall_score"))
    print("Answered Questions:", res_json_45.get("answered_questions"))
    print("Unanswered Questions:", res_json_45.get("unanswered_questions"))

    assert response_45.status_code == 200, f"Upload failed: {response_45.text}"
    assert res_json_45["status"] == "success"
    assert res_json_45["interview_id"] == 45

    # Verify Database Rows for Interview 45
    print("\n--- Verifying SQL Server Rows for Interview 45 ---")
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, role, status, total_questions, overall_score, duration_seconds, transcript FROM Interviews WHERE id = 45")
    int_row = cur.fetchone()
    print("Interviews Row (45):", int_row)
    assert int_row[2] == "COMPLETED", f"Expected COMPLETED, got {int_row[2]}"
    assert int_row[4] > 0, "overall_score must be > 0"
    assert int_row[6] is not None and len(int_row[6]) > 0, "transcript must not be empty"

    cur.execute("""
        SELECT question_number, question_id, question_text, answer_text, word_count, start_ms, end_ms, overall_answer_score
        FROM InterviewAnswers
        WHERE interview_id = 45
        ORDER BY question_number
    """)
    ia_rows_45 = cur.fetchall()
    print(f"Total InterviewAnswers rows for interview 45: {len(ia_rows_45)}")
    for r in ia_rows_45:
        ans_preview = repr(r[3][:40] + "...") if r[3] else "NULL"
        print(f"  Q{r[0]} (q_id={r[1]}): words={r[4]} | start_ms={r[5]} | end_ms={r[6]} | score={r[7]} | ans={ans_preview}")

    # Q1 must be answered
    q1 = ia_rows_45[0]
    assert q1[3] is not None and len(q1[3]) > 0, "Q1 answer_text MUST NOT be NULL"
    assert q1[4] is not None and q1[4] > 0, "Q1 word_count MUST NOT be NULL or 0"
    assert q1[5] is not None, "Q1 start_ms MUST NOT be NULL"
    assert q1[6] is not None, "Q1 end_ms MUST NOT be NULL"
    assert q1[7] > 0, "Q1 overall_answer_score MUST be > 0"

    # Q2 must be answered
    q2 = ia_rows_45[1]
    assert q2[3] is not None and len(q2[3]) > 0, "Q2 answer_text MUST NOT be NULL"
    assert q2[4] is not None and q2[4] > 0, "Q2 word_count MUST NOT be NULL or 0"
    assert q2[5] is not None, "Q2 start_ms MUST NOT be NULL"
    assert q2[6] is not None, "Q2 end_ms MUST NOT be NULL"
    assert q2[7] > 0, "Q2 overall_answer_score MUST be > 0"

    # Q3 must be unanswered
    q3 = ia_rows_45[2]
    assert q3[3] is None, f"Q3 answer_text must be NULL, got {q3[3]}"
    assert q3[4] == 0, f"Q3 word_count must be 0, got {q3[4]}"
    assert q3[7] == 0.0, f"Q3 overall_answer_score must be 0.0, got {q3[7]}"

    # Q4..Q20 must be marked as unreached (NULL answers, 0 scores)
    for q_unreached in ia_rows_45[3:]:
        assert q_unreached[3] is None, f"Q{q_unreached[0]} answer_text must be NULL"
        assert q_unreached[4] == 0, f"Q{q_unreached[0]} word_count must be 0"
        assert q_unreached[7] == 0.0, f"Q{q_unreached[0]} score must be 0.0"

    print(">> TEST 1 PASSED: Interview 45 has non-NULL answers for answered questions and 0 for unanswered!")

    # -------------------------------------------------------------
    # TEST 2: Create a NEW Interview (No interview_id passed)
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print("TEST 2: Upload and Transcribe for a Brand New Interview")
    print("=" * 70)

    q_data_new = [
        {
            "question_number": 1,
            "question": "Tell me about yourself.",
            "type": "HR",
            "start_time": 0.0,
            "end_time": 14.5,
            "start_ms": 0,
            "end_ms": 14500,
            "candidate_answer": "",
            "is_answered": False
        },
        {
            "question_number": 2,
            "question": "What is the difference between a list and a tuple in Python?",
            "type": "ROLE",
            "start_time": 14.5,
            "end_time": 26.0,
            "start_ms": 14500,
            "end_ms": 26000,
            "candidate_answer": "",
            "is_answered": False
        },
        {
            "question_number": 3,
            "question": "How does Python manage memory?",
            "type": "ROLE",
            "start_time": 26.0,
            "end_time": 30.0,
            "start_ms": 26000,
            "end_ms": 30000,
            "candidate_answer": "",
            "is_answered": False
        }
    ]

    with open(recording_path, "rb") as f:
        response_new = client.post(
            "/interview/upload",
            data={
                "role": "Python Developer",
                "total_questions": "3",
                "attempted_questions": "3",
                "answered_questions": "2",
                "unanswered_questions": "1",
                "recording_start_time": "0.0",
                "tab_switch_count": "0",
                "terminated_reason": "",
                "question_data": json.dumps(q_data_new)
            },
            files={
                "recording": ("Python_Developer_interview.webm", f, "video/webm")
            },
            headers={
                "X-API-Key": "AI_INTERVIEW_2026_SECRET"
            }
        )

    print(f"HTTP Status (New Interview): {response_new.status_code}")
    res_json_new = response_new.json()
    new_id = res_json_new.get("interview_id")
    print("New Interview ID created:", new_id)
    assert response_new.status_code == 200, f"Upload failed: {response_new.text}"
    assert res_json_new["status"] == "success"
    assert new_id > 45, f"Expected new interview id > 45, got {new_id}"

    # Verify Database Rows for New Interview
    print(f"\n--- Verifying SQL Server Rows for New Interview #{new_id} ---")
    cur.execute("SELECT id, role, status, total_questions, overall_score, duration_seconds, transcript FROM Interviews WHERE id = ?", (new_id,))
    new_int_row = cur.fetchone()
    print(f"Interviews Row ({new_id}):", new_int_row)
    assert new_int_row[2] == "COMPLETED"

    cur.execute("""
        SELECT question_number, question_id, question_text, answer_text, word_count, start_ms, end_ms, overall_answer_score
        FROM InterviewAnswers
        WHERE interview_id = ?
        ORDER BY question_number
    """, (new_id,))
    ia_rows_new = cur.fetchall()
    print(f"Total InterviewAnswers rows for new interview {new_id}: {len(ia_rows_new)}")
    for r in ia_rows_new:
        ans_preview = repr(r[3][:40] + "...") if r[3] else "NULL"
        print(f"  Q{r[0]} (q_id={r[1]}): words={r[4]} | start_ms={r[5]} | end_ms={r[6]} | score={r[7]} | ans={ans_preview}")

    # Check Q1 and Q2 are answered
    assert ia_rows_new[0][3] is not None and len(ia_rows_new[0][3]) > 0, "New Q1 answer_text MUST NOT be NULL"
    assert ia_rows_new[0][4] is not None and ia_rows_new[0][4] > 0, "New Q1 word_count MUST NOT be NULL or 0"
    assert ia_rows_new[0][5] is not None, "New Q1 start_ms MUST NOT be NULL"
    assert ia_rows_new[0][6] is not None, "New Q1 end_ms MUST NOT be NULL"

    assert ia_rows_new[1][3] is not None and len(ia_rows_new[1][3]) > 0, "New Q2 answer_text MUST NOT be NULL"
    assert ia_rows_new[1][4] is not None and ia_rows_new[1][4] > 0, "New Q2 word_count MUST NOT be NULL or 0"
    assert ia_rows_new[1][5] is not None, "New Q2 start_ms MUST NOT be NULL"
    assert ia_rows_new[1][6] is not None, "New Q2 end_ms MUST NOT be NULL"

    # Check Q3 is unanswered
    assert ia_rows_new[2][3] is None, "New Q3 answer_text must be NULL"
    assert ia_rows_new[2][4] == 0, "New Q3 word_count must be 0"

    print(f">> TEST 2 PASSED: New Interview #{new_id} has non-NULL answers for answered questions!")

    # -------------------------------------------------------------
    # TEST 3: User's Exact Query Verification
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print("TEST 3: Running User's Exact SQL Query:")
    print("SELECT TOP 20 interview_id, question_number, answer_text, word_count, start_ms, end_ms FROM InterviewAnswers ORDER BY id DESC;")
    print("=" * 70)

    cur.execute("""
        SELECT TOP 20 interview_id, question_number, answer_text, word_count, start_ms, end_ms
        FROM InterviewAnswers
        ORDER BY id DESC;
    """)
    top_20_rows = cur.fetchall()
    for row in top_20_rows:
        ans_preview = repr(row[2][:35] + "...") if row[2] else "NULL"
        print(f"  interview_id={row[0]} | Q{row[1]} | words={row[3]} | start_ms={row[4]} | end_ms={row[5]} | answer={ans_preview}")

    cur.close()
    conn.close()

    print("\n" + "=" * 70)
    print("ALL VERIFICATION CHECKS COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_verification()
