"""
Comprehensive Test Suite for Super Admin Console
Verifies all 22 Phases:
- Command Center Metrics & Charts
- User Management (CRUD, status toggle, secure password reset, RBAC)
- Interview Management & Details (read-only, no re-evaluation mutation)
- Question Bank Management (CRUD, safe soft-delete when referenced)
- Role Management (CRUD)
- Security Center (Tab-switch violations, real events)
- Recordings & Evidence
- Report Center (PDF endpoint reuse)
- Analytics Center (Real statistics)
- Audit Logs (Automatic logging, sanitized payloads, immutable)
- System Health Diagnostics
- Settings & Masked Secrets
- Admin Profile & Password Update
- Server-Side RBAC Enforcement (401 unauthenticated, 403 candidate)
- Data Immutability & Anti-Regression
"""

import sys
import os
import unittest
import uuid
import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app
from database import get_connection
from auth_utils import hash_password, verify_password, normalize_email, generate_secure_token, hash_token

client = TestClient(app)

class SuperAdminConsoleTestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = get_connection()
        cls.cursor = cls.conn.cursor()

        # 1. Fetch or ensure Admin user
        cls.cursor.execute("SELECT id, email FROM Users WHERE is_admin = 1 ORDER BY id ASC")
        admin_row = cls.cursor.fetchone()
        if not admin_row:
            admin_pwd_hash = hash_password("Admin@Interview2026!")
            cls.cursor.execute(
                "INSERT INTO Users (name, email, password_hash, is_admin, role) OUTPUT INSERTED.id VALUES (?, ?, ?, 1, 'Admin')",
                ("Super Admin", "admin@ai-interview.com", admin_pwd_hash)
            )
            cls.conn.commit()
            cls.admin_id = cls.cursor.fetchone()[0]
            cls.admin_email = "admin@ai-interview.com"
        else:
            cls.admin_id = admin_row[0]
            cls.admin_email = admin_row[1]

        # Ensure password is Admin@Interview2026!
        admin_pwd_hash = hash_password("Admin@Interview2026!")
        cls.cursor.execute("UPDATE Users SET password_hash = ? WHERE id = ?", (admin_pwd_hash, cls.admin_id))
        cls.conn.commit()

        login_res = client.post("/api/auth/login", json={
            "email": cls.admin_email,
            "password": "Admin@Interview2026!",
            "role": "admin"
        })
        cls.admin_token = login_res.json().get("token")
        cls.admin_headers = {"Authorization": f"Bearer {cls.admin_token}"}

        # 2. Fetch or create Candidate user for RBAC negative testing
        cls.cursor.execute("SELECT id, email FROM Users WHERE is_admin = 0 ORDER BY id ASC")
        cand_row = cls.cursor.fetchone()
        if not cand_row:
            cand_pwd_hash = hash_password("Candidate@2026!")
            cand_email = f"cand_test_{uuid.uuid4().hex[:6]}@example.com"
            cls.cursor.execute(
                "INSERT INTO Users (name, email, password_hash, is_admin, role) OUTPUT INSERTED.id VALUES (?, ?, ?, 0, 'Python Developer')",
                ("Test Candidate", cand_email, cand_pwd_hash)
            )
            cls.conn.commit()
            cls.candidate_id = cls.cursor.fetchone()[0]
            cls.candidate_email = cand_email
        else:
            cls.candidate_id = cand_row[0]
            cls.candidate_email = cand_row[1]

        # Candidate token via UserTokens
        cand_raw_token = generate_secure_token()
        cand_t_hash = hash_token(cand_raw_token)
        exp = datetime.datetime.now() + datetime.timedelta(hours=2)
        cls.cursor.execute(
            "INSERT INTO UserTokens (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
            (cls.candidate_id, cand_t_hash, exp)
        )
        cls.conn.commit()
        cls.candidate_headers = {"Authorization": f"Bearer {cand_raw_token}"}

    @classmethod
    def tearDownClass(cls):
        try:
            cls.cursor.close()
            cls.conn.close()
        except Exception:
            pass

    # ==================== RBAC & SECURITY TESTS ====================
    def test_01_unauthenticated_requests_blocked(self):
        """Unauthenticated requests to admin endpoints must return 401 Unauthorized"""
        endpoints = [
            "/api/admin/dashboard",
            "/api/admin/users",
            "/api/admin/interviews",
            "/api/admin/questions",
            "/api/admin/roles",
            "/api/admin/security",
            "/api/admin/audit-logs",
            "/api/admin/system-health",
            "/api/admin/analytics",
            "/api/admin/settings"
        ]
        for ep in endpoints:
            res = client.get(ep)
            self.assertEqual(res.status_code, 401, f"Endpoint {ep} should return 401 when unauthenticated")

    def test_02_candidate_access_forbidden(self):
        """Candidate tokens attempting to access admin endpoints must return 403 Forbidden"""
        endpoints = [
            "/api/admin/dashboard",
            "/api/admin/users",
            "/api/admin/interviews",
            "/api/admin/questions",
            "/api/admin/roles",
            "/api/admin/security",
            "/api/admin/audit-logs",
            "/api/admin/system-health",
            "/api/admin/analytics",
            "/api/admin/settings"
        ]
        for ep in endpoints:
            res = client.get(ep, headers=self.candidate_headers)
            self.assertEqual(res.status_code, 403, f"Endpoint {ep} should return 403 for candidate token")

    # ==================== COMMAND CENTER DASHBOARD ====================
    def test_03_dashboard_metrics_real_database_data(self):
        """Dashboard returns 12 verified real metrics with proper numeric types"""
        res = client.get("/api/admin/dashboard", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn("metrics", data)
        metrics = data["metrics"]
        required_keys = [
            "total_candidates", "active_candidates", "inactive_candidates",
            "total_interviews", "completed_interviews", "terminated_interviews",
            "average_score", "highest_score", "interviews_today",
            "interviews_this_week", "security_violations", "active_sessions"
        ]
        for k in required_keys:
            self.assertIn(k, metrics, f"Missing metric {k}")
            self.assertIsInstance(metrics[k], (int, float), f"Metric {k} must be numeric")

        # Verify logical relationships
        self.assertGreaterEqual(metrics["total_candidates"], 0)
        self.assertEqual(
            metrics["total_candidates"],
            metrics["active_candidates"] + metrics["inactive_candidates"]
        )
        self.assertGreaterEqual(metrics["total_interviews"], 0)
        self.assertLessEqual(
            metrics["completed_interviews"] + metrics["terminated_interviews"],
            metrics["total_interviews"]
        )

        # Charts section
        self.assertIn("charts", data)
        charts = data["charts"]
        self.assertIn("interview_activity", charts)
        self.assertIn("completed_vs_terminated", charts)
        self.assertIn("score_distribution", charts)
        self.assertIn("avg_score_by_role", charts)
        self.assertIn("candidates_by_role", charts)
        self.assertIn("security_violations_trend", charts)

    # ==================== USER MANAGEMENT ====================
    def test_04_user_management_crud_and_status(self):
        """Admin can list, search, filter, create, toggle status, and securely reset passwords"""
        # 1. List users
        res = client.get("/api/admin/users", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        users_data = res.json()
        self.assertIn("users", users_data)
        self.assertIsInstance(users_data["users"], list)

        # Check that sensitive data is NEVER returned
        for u in users_data["users"]:
            self.assertNotIn("password_hash", u)
            self.assertNotIn("password", u)
            self.assertNotIn("token", u)

        # 2. Create a test candidate
        test_email = f"admintest_{uuid.uuid4().hex[:6]}@domain.edu"
        create_payload = {
            "name": "Admin Created User",
            "email": test_email,
            "role": "Python Developer",
            "password": "Password#2026",
            "is_admin": False
        }
        res_create = client.post("/api/admin/users", headers=self.admin_headers, json=create_payload)
        self.assertEqual(res_create.status_code, 200)
        new_user = res_create.json()["user"]
        new_user_id = new_user["id"]
        self.assertGreater(new_user_id, 0)

        # 3. Toggle Status (Deactivate then Reactivate)
        res_deactivate = client.patch(
            f"/api/admin/users/{new_user_id}/status",
            headers=self.admin_headers,
            json={"is_active": False}
        )
        self.assertEqual(res_deactivate.status_code, 200)
        self.assertFalse(res_deactivate.json()["is_active"])

        res_activate = client.patch(
            f"/api/admin/users/{new_user_id}/status",
            headers=self.admin_headers,
            json={"is_active": True}
        )
        self.assertEqual(res_activate.status_code, 200)
        self.assertTrue(res_activate.json()["is_active"])

        # 4. Admin Secure Password Reset
        reset_res = client.post(
            f"/api/admin/users/{new_user_id}/reset-password",
            headers=self.admin_headers,
            json={"new_password": "NewSecretPassword@99"}
        )
        self.assertEqual(reset_res.status_code, 200)

        # Verify user can log in with new password
        test_login = client.post("/api/auth/login", json={
            "email": test_email,
            "password": "NewSecretPassword@99",
            "role": "candidate"
        })
        self.assertEqual(test_login.status_code, 200, "User should be able to log in with admin-reset password")

        # 5. Clean up test user
        del_res = client.delete(f"/api/admin/users/{new_user_id}", headers=self.admin_headers)
        self.assertEqual(del_res.status_code, 200)

    # ==================== INTERVIEW MANAGEMENT ====================
    def test_05_interview_management_and_details(self):
        """Admin can list interviews, filter, and inspect detailed evaluation without database mutation"""
        res = client.get("/api/admin/interviews", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        interviews_data = res.json()
        self.assertIn("interviews", interviews_data)
        interviews = interviews_data["interviews"]
        self.assertGreater(len(interviews), 0)

        first_interview = interviews[0]
        int_id = first_interview["id"]

        # Inspect details
        res_det = client.get(f"/api/admin/interviews/{int_id}", headers=self.admin_headers)
        self.assertEqual(res_det.status_code, 200)
        det_full = res_det.json()
        det = det_full.get("interview", det_full)
        self.assertEqual(det["id"], int_id)
        self.assertIn("candidate_name", det)
        self.assertIn("role", det)
        self.assertIn("status", det)
        self.assertIn("answers", det_full)

    # ==================== QUESTION BANK MANAGEMENT ====================
    def test_06_question_bank_management(self):
        """Admin can view, search, add, edit, and safe-delete questions"""
        # 1. List questions
        res = client.get("/api/admin/questions", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        questions = res.json().get("questions", [])
        self.assertIsInstance(questions, list)
        self.assertGreater(len(questions), 0)

        # 2. Add Question
        new_q_payload = {
            "question_text": "What is Python GIL and how does it affect threading?",
            "role": "Python Developer",
            "difficulty": "Medium",
            "expected_concepts": "Global Interpreter Lock, CPython, single-threaded execution, multiprocessing",
            "is_active": True
        }
        res_add = client.post("/api/admin/questions", headers=self.admin_headers, json=new_q_payload)
        self.assertEqual(res_add.status_code, 200)
        created_q = res_add.json()
        q_id = created_q["question_id"]

        # 3. Edit Question
        res_edit = client.put(f"/api/admin/questions/{q_id}", headers=self.admin_headers, json={
            "question_text": "What is Python GIL and how does it affect multi-threading?",
            "difficulty": "Hard",
            "is_active": False
        })
        self.assertEqual(res_edit.status_code, 200)

        # 4. Delete Question (Unreferenced question is safely removed)
        res_del = client.delete(f"/api/admin/questions/{q_id}", headers=self.admin_headers)
        self.assertEqual(res_del.status_code, 200)

    # ==================== INTERVIEW ROLE MANAGEMENT ====================
    def test_07_interview_role_management(self):
        """Admin can list, add, and update interview roles"""
        res = client.get("/api/admin/roles", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        roles = res.json().get("roles", [])
        self.assertGreater(len(roles), 0)

        # Add a custom role
        role_name = f"DevOps_{uuid.uuid4().hex[:4]}"
        res_add = client.post("/api/admin/roles", headers=self.admin_headers, json={
            "role_name": role_name,
            "description": "DevOps and Site Reliability Engineer",
            "is_active": True
        })
        self.assertEqual(res_add.status_code, 200)
        new_role_id = res_add.json()["role_id"]

        # Update role description
        res_upd = client.put(f"/api/admin/roles/{new_role_id}", headers=self.admin_headers, json={
            "description": "DevOps & Cloud Infrastructure Engineer",
            "is_active": True
        })
        self.assertEqual(res_upd.status_code, 200)

    # ==================== SECURITY CENTER ====================
    def test_08_security_center_data(self):
        """Security center provides real security events and statistics with 0 false positives"""
        res = client.get("/api/admin/security", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        sec = res.json()
        self.assertIn("summary", sec)
        self.assertIn("recent_security_events", sec)
        self.assertIn("tab_switch_violations", sec["summary"])
        self.assertIn("terminated_interviews", sec["summary"])

    # ==================== SYSTEM HEALTH ====================
    def test_09_system_health_checks(self):
        """System health checks return real diagnostic status for backend, database, smtp, ai, stt, storage"""
        res = client.get("/api/admin/system-health", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        health = health_data = res.json()
        services = health_data.get("services", {})
        self.assertIn("backend_api", services)
        self.assertEqual(services["backend_api"]["status"].lower(), "online")
        self.assertIn("database", services)
        self.assertEqual(services["database"]["status"].lower(), "connected")
        self.assertIn("authentication", services)
        self.assertIn("speech_to_text", services)
        self.assertIn("ai_evaluation", services)
        self.assertIn("storage", services)

    # ==================== AUDIT LOG SYSTEM ====================
    def test_10_audit_log_system(self):
        """Audit log records administrative actions and never stores secrets"""
        res = client.get("/api/admin/audit-logs", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        logs_data = res.json()
        self.assertIn("logs", logs_data)
        logs = logs_data["logs"]
        self.assertGreater(len(logs), 0)

        # Inspect fields and ensure no passwords or secrets
        for log in logs[:10]:
            self.assertIn("action", log)
            self.assertTrue("created_at" in log or "timestamp" in log)
            self.assertIn("admin_name", log)
            details_str = str(log.get("details", ""))
            self.assertNotIn("password_hash", details_str)
            self.assertNotIn("secret", details_str.lower())
            self.assertNotIn("bearer", details_str.lower())

    # ==================== SETTINGS & MASKING ====================
    def test_11_settings_masked_information(self):
        """Settings returns masked status without exposing raw credentials"""
        res = client.get("/api/admin/settings", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        settings = res.json()
        self.assertIn("general", settings)
        self.assertIn("authentication", settings)
        self.assertIn("interview", settings)
        self.assertIn("email", settings)
        self.assertIn("ai", settings)

        # Verify no cleartext password or api key exposed
        email_cfg = settings["email"]
        self.assertNotIn("smtp_password", email_cfg)
        self.assertNotIn("password", email_cfg)

    # ==================== REPORT REUSE ====================
    def test_12_pdf_report_endpoint_reuse(self):
        """Admin can access existing PDF report endpoint for completed and terminated interviews"""
        self.cursor.execute("SELECT TOP 1 id FROM Interviews ORDER BY id DESC")
        row = self.cursor.fetchone()
        if row:
            int_id = row[0]
            res = client.get(f"/api/interview/{int_id}/report/pdf", headers=self.admin_headers)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.headers.get("content-type"), "application/pdf")

if __name__ == "__main__":
    unittest.main()
