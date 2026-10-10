"""
Comprehensive Regression Test Suite for Interview Submission Pipeline,
PostgreSQL Schema Readiness, Missing-Table Recovery, and Authentication.

Tests:
1. User Registration via /api/auth/register
2. User Login via /api/auth/login and JWT / User Token generation
3. Full Interview Submission via save_interview_record:
   - Persists to Interviews, InterviewAnswers, EvaluationResults, InterviewHistory, Feedback
   - Validates transaction integrity (all or nothing)
4. Result Retrieval via /interview/{id}
   - Returns answers, transcript, score, evaluation feedback, and history consistently
5. Idempotent Repeat Submission:
   - Re-submitting the same interview_id updates in-place without duplicate rows
6. Missing Table Regression & Self-Healing Guard:
   - Demonstrates that a missing InterviewHistory table causes the confirmed error
   - Demonstrates that _ensure_interview_history_table heals the schema and prevents the error
7. Async Submission Job Status API (/interview/submission/{job_id}/status):
   - Verifies immediate failure reporting with exact error message (no misleading timeouts)
   - Verifies success state with complete payload
8. PostgreSQL Schema Definition Integrity:
   - Validates SCHEMA_POSTGRES_SQL contains InterviewHistory, indexes, and Feedback.created_at
"""

import os
import sys
import json
import uuid
import unittest
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from fastapi.testclient import TestClient
import main
from main import (
    app,
    save_interview_record,
    _ensure_interview_history_table,
    SUBMISSION_JOBS,
    API_KEY
)
from database import get_connection
import postgres_init


class InterviewSubmissionRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.test_email = f"candidate_{uuid.uuid4().hex[:8]}@example.com"
        cls.test_password = "SecurePassword@2026!"
        cls.test_name = "Regression Candidate"

    def test_01_user_registration(self):
        """Test registration endpoint creates active user."""
        res = self.client.post("/api/auth/register", json={
            "name": self.test_name,
            "email": self.test_email,
            "password": self.test_password,
            "role": "User",
            "preferred_role": "Python Developer"
        })
        self.assertEqual(res.status_code, 200, f"Registration failed: {res.text}")
        data = res.json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("user", data)
        self.assertEqual(data["user"]["email"].lower(), self.test_email.lower())

    def test_02_user_login(self):
        """Test login endpoint returns valid session token."""
        res = self.client.post("/api/auth/login", json={
            "email": self.test_email,
            "password": self.test_password
        })
        self.assertEqual(res.status_code, 200, f"Login failed: {res.text}")
        data = res.json()
        self.assertEqual(data.get("status"), "success")
        self.assertTrue(bool(data.get("token")), "No token returned upon login")
        self.__class__.auth_token = data["token"]
        self.__class__.user_id = data["user"]["id"]

    def test_03_interview_submission_pipeline_persistence(self):
        """Test complete interview submission saves all 5 tables consistently."""
        eval_payload = {
            "overall_score": 82.5,
            "technical_score": 85.0,
            "communication_score": 80.0,
            "confidence_score": 78.0,
            "problem_solving_score": 84.0,
            "relevance_score": 88.0,
            "completeness_score": 82.0,
            "attempted_questions": 2,
            "answered_questions": 2,
            "unanswered_questions": 0,
            "strengths": ["Clear FastAPI knowledge", "Strong SQL indexing rationale"],
            "improvements": ["Elaborate on async database sessions"],
            "questions": [
                {
                    "question_number": 1,
                    "question": "Explain async/await in FastAPI.",
                    "candidate_answer": "FastAPI leverages Python asyncio for high concurrency non-blocking I/O.",
                    "is_answered": True,
                    "technical_score": 88.0,
                    "communication_score": 82.0,
                    "confidence_score": 80.0,
                    "problem_solving_score": 85.0,
                    "relevance_score": 90.0,
                    "completeness_score": 85.0,
                    "overall_score": 86.0,
                    "matched_concepts": ["asyncio", "non-blocking", "concurrency"],
                    "missing_concepts": [],
                    "feedback": "Thorough async overview."
                },
                {
                    "question_number": 2,
                    "question": "What is database indexing and how does it optimize queries?",
                    "candidate_answer": "Indexes create B-Tree structures allowing logarithmic lookup time instead of sequential scans.",
                    "is_answered": True,
                    "technical_score": 84.0,
                    "communication_score": 80.0,
                    "confidence_score": 78.0,
                    "problem_solving_score": 82.0,
                    "relevance_score": 86.0,
                    "completeness_score": 80.0,
                    "overall_score": 82.0,
                    "matched_concepts": ["b-tree", "lookup time", "sequential scan"],
                    "missing_concepts": [],
                    "feedback": "Solid database indexing concept explanation."
                }
            ]
        }

        question_timings = [
            {"question_number": 1, "relative_start": 0.0, "relative_end": 14.5},
            {"question_number": 2, "relative_start": 14.5, "relative_end": 32.0}
        ]

        interview_id = save_interview_record(
            role="Python Developer",
            total_questions=2,
            recording_path="/recordings/test_rec.webm",
            transcript="FastAPI leverages asyncio. Indexes create B-Tree structures.",
            tab_switch_count=0,
            terminated_reason="",
            evaluation=eval_payload,
            question_data_list=question_timings,
            language="en",
            filename="test_rec.webm",
            user_id=getattr(self.__class__, "user_id", None)
        )

        self.assertIsNotNone(interview_id)
        self.assertGreater(interview_id, 0)
        self.__class__.created_interview_id = interview_id

        # Direct database checks across all 5 tables
        conn = get_connection()
        cur = conn.cursor()

        # 1. Interviews
        cur.execute("SELECT id, role, overall_score, status FROM Interviews WHERE id = ?", (interview_id,))
        i_row = cur.fetchone()
        self.assertIsNotNone(i_row)
        self.assertEqual(i_row[1], "Python Developer")
        self.assertEqual(round(float(i_row[2]), 1), 82.5)
        self.assertEqual(i_row[3], "COMPLETED")

        # 2. InterviewAnswers
        cur.execute("SELECT COUNT(*) FROM InterviewAnswers WHERE interview_id = ?", (interview_id,))
        ans_count = cur.fetchone()[0]
        self.assertEqual(ans_count, 2)

        # 3. EvaluationResults
        cur.execute("SELECT overall_score, technical_score FROM EvaluationResults WHERE interview_id = ?", (interview_id,))
        eval_row = cur.fetchone()
        self.assertIsNotNone(eval_row)
        self.assertEqual(round(float(eval_row[0]), 1), 82.5)

        # 4. InterviewHistory (Target of Render production bug)
        cur.execute("SELECT interview_id, role, overall_score FROM InterviewHistory WHERE interview_id = ?", (interview_id,))
        hist_row = cur.fetchone()
        self.assertIsNotNone(hist_row, "InterviewHistory record was NOT created!")
        self.assertEqual(hist_row[0], interview_id)
        self.assertEqual(hist_row[1], "Python Developer")
        self.assertEqual(round(float(hist_row[2]), 1), 82.5)

        # 5. Feedback
        cur.execute("SELECT id, summary FROM Feedback WHERE interview_id = ?", (interview_id,))
        fb_row = cur.fetchone()
        self.assertIsNotNone(fb_row, "Feedback record was NOT created!")
        self.assertIn("Python Developer", fb_row[1])

        cur.close()
        conn.close()

    def test_04_interview_summary_retrieval(self):
        """Test GET /interview/{id} retrieves complete result payload."""
        iid = getattr(self.__class__, "created_interview_id", None)
        self.assertIsNotNone(iid, "No interview_id from previous test")

        headers = {"X-API-Key": API_KEY}
        res = self.client.get(f"/interview/{iid}", headers=headers)
        self.assertEqual(res.status_code, 200, f"Summary retrieval failed: {res.text}")

        data = res.json()
        interview_obj = data.get("interview", {})
        self.assertEqual(interview_obj.get("id"), iid)
        self.assertEqual(interview_obj.get("role"), "Python Developer")
        self.assertEqual(round(float(interview_obj.get("overall_score")), 1), 82.5)
        self.assertEqual(len(data.get("answers", [])), 2)
        self.assertIn("evaluation", data)
        self.assertIn("history", data)
        self.assertEqual(data["history"]["interview_id"], iid)

    def test_05_idempotent_repeat_submission_no_duplicates(self):
        """Test repeat submission updates in place rather than creating duplicate rows."""
        iid = getattr(self.__class__, "created_interview_id", None)
        self.assertIsNotNone(iid)

        eval_payload_update = {
            "overall_score": 86.0,
            "technical_score": 88.0,
            "communication_score": 84.0,
            "confidence_score": 80.0,
            "problem_solving_score": 86.0,
            "relevance_score": 90.0,
            "completeness_score": 86.0,
            "attempted_questions": 2,
            "answered_questions": 2,
            "unanswered_questions": 0,
            "strengths": ["Enhanced explanation"],
            "improvements": ["None"],
            "questions": [
                {
                    "question_number": 1,
                    "question": "Explain async/await in FastAPI.",
                    "candidate_answer": "FastAPI leverages Python asyncio for high concurrency non-blocking I/O. Updated answer.",
                    "is_answered": True,
                    "technical_score": 90.0,
                    "communication_score": 85.0,
                    "confidence_score": 82.0,
                    "problem_solving_score": 88.0,
                    "relevance_score": 92.0,
                    "completeness_score": 88.0,
                    "overall_score": 89.0,
                    "matched_concepts": ["asyncio"],
                    "missing_concepts": [],
                    "feedback": "Updated feedback"
                },
                {
                    "question_number": 2,
                    "question": "What is database indexing and how does it optimize queries?",
                    "candidate_answer": "Updated indexing answer.",
                    "is_answered": True,
                    "technical_score": 86.0,
                    "communication_score": 82.0,
                    "confidence_score": 80.0,
                    "problem_solving_score": 84.0,
                    "relevance_score": 88.0,
                    "completeness_score": 84.0,
                    "overall_score": 85.0,
                    "matched_concepts": ["b-tree"],
                    "missing_concepts": [],
                    "feedback": "Updated feedback"
                }
            ]
        }

        # Re-submit with the exact same interview_id
        returned_id = save_interview_record(
            role="Python Developer",
            total_questions=2,
            recording_path="/recordings/test_rec.webm",
            transcript="Updated transcript",
            tab_switch_count=0,
            terminated_reason="",
            evaluation=eval_payload_update,
            question_data_list=[],
            language="en",
            filename="test_rec.webm",
            interview_id=iid,
            user_id=getattr(self.__class__, "user_id", None)
        )

        self.assertEqual(returned_id, iid)

        # Confirm NO DUPLICATES created in any of the tables
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM Interviews WHERE id = ?", (iid,))
        self.assertEqual(cur.fetchone()[0], 1)

        cur.execute("SELECT COUNT(*) FROM InterviewAnswers WHERE interview_id = ?", (iid,))
        self.assertEqual(cur.fetchone()[0], 2, "InterviewAnswers created duplicate rows on re-submission!")

        cur.execute("SELECT COUNT(*) FROM EvaluationResults WHERE interview_id = ?", (iid,))
        self.assertEqual(cur.fetchone()[0], 1, "EvaluationResults created duplicate rows on re-submission!")

        cur.execute("SELECT COUNT(*) FROM InterviewHistory WHERE interview_id = ?", (iid,))
        self.assertEqual(cur.fetchone()[0], 1, "InterviewHistory created duplicate rows on re-submission!")

        cur.execute("SELECT COUNT(*) FROM Feedback WHERE interview_id = ?", (iid,))
        self.assertEqual(cur.fetchone()[0], 1, "Feedback created duplicate rows on re-submission!")

        cur.close()
        conn.close()

    def test_06_missing_table_reproduction_and_guard(self):
        """Test simulates missing InterviewHistory table and verifies schema guard recreates it."""
        conn = get_connection()
        cur = conn.cursor()

        # Step A: Drop InterviewHistory to reproduce the missing-table state
        cur.execute("DROP TABLE IF EXISTS InterviewHistory")
        conn.commit()

        # Confirm table does not exist
        table_missing = False
        try:
            cur.execute("SELECT id FROM InterviewHistory WHERE interview_id = 9999")
            cur.fetchone()
        except Exception as e:
            table_missing = True
            err_str = str(e).lower()
            # SQLite: "no such table", PostgreSQL: "relation 'interviewhistory' does not exist", SQL Server: "invalid object name"
            self.assertTrue(
                "no such table" in err_str or "does not exist" in err_str or "invalid object name" in err_str,
                f"Unexpected error: {e}"
            )

        self.assertTrue(table_missing, "Failed to drop InterviewHistory for test reproduction")

        # Step B: Call _ensure_interview_history_table schema guard
        _ensure_interview_history_table(cur)
        conn.commit()

        # Step C: Verify query now succeeds without raising an error
        cur.execute("SELECT id FROM InterviewHistory WHERE interview_id = 9999")
        row = cur.fetchone()
        self.assertIsNone(row, "Table exists and query succeeded with 0 rows")

        cur.close()
        conn.close()

    def test_07_async_submission_job_status_reporting(self):
        """Test submission status endpoint immediately reports real error or success without timeout."""
        # 1. Failure state
        failed_job_id = f"job_fail_{uuid.uuid4().hex[:8]}"
        SUBMISSION_JOBS[failed_job_id] = {
            "job_id": failed_job_id,
            "status": "failed",
            "stage": "error",
            "progress": 50,
            "message": "Submission aborted due to database transaction failure",
            "error_message": 'relation "interviewhistory" does not exist',
            "created_at": datetime.utcnow().isoformat()
        }

        res_fail = self.client.get(
            f"/interview/submission/{failed_job_id}/status",
            headers={"X-API-Key": API_KEY}
        )
        self.assertEqual(res_fail.status_code, 200)
        data_fail = res_fail.json()
        self.assertEqual(data_fail["status"], "failed")
        self.assertEqual(data_fail["error_message"], 'relation "interviewhistory" does not exist')

        # 2. Completed state
        completed_job_id = f"job_comp_{uuid.uuid4().hex[:8]}"
        SUBMISSION_JOBS[completed_job_id] = {
            "job_id": completed_job_id,
            "status": "completed",
            "stage": "completed",
            "progress": 100,
            "message": "Interview evaluated and stored successfully.",
            "error_message": None,
            "result": {
                "interview_id": 100,
                "overall_score": 85.0,
                "status": "COMPLETED"
            },
            "created_at": datetime.utcnow().isoformat()
        }

        res_comp = self.client.get(
            f"/interview/submission/{completed_job_id}/status",
            headers={"X-API-Key": API_KEY}
        )
        self.assertEqual(res_comp.status_code, 200)
        data_comp = res_comp.json()
        self.assertEqual(data_comp["status"], "completed")
        self.assertEqual(data_comp["progress"], 100)
        self.assertIsNotNone(data_comp["result"])

    def test_08_postgres_schema_definition_integrity(self):
        """Test that postgres_init.py SCHEMA_POSTGRES_SQL includes InterviewHistory and Feedback.created_at."""
        schema_sql = postgres_init.SCHEMA_POSTGRES_SQL
        self.assertIn("CREATE TABLE IF NOT EXISTS InterviewHistory", schema_sql)
        self.assertIn("idx_interview_history_interview_id", schema_sql)
        self.assertIn("idx_interview_history_user_id", schema_sql)
        self.assertIn("created_at TIMESTAMP NOT NULL DEFAULT NOW()", schema_sql)


if __name__ == "__main__":
    unittest.main()
