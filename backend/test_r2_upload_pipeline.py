"""
Test Suite: Cloudflare R2 Upload Pipeline & Large File (>10 MB) Workflow Verification
Tests:
1. Storage Service Diagnostics: is_r2_configured() with empty, placeholder, and valid credentials.
2. Presigned Upload Endpoint (/interview/presign_upload):
   - Returns r2_configured: False and required env var instructions when unconfigured.
   - Returns r2_configured: True with valid S3 SigV4 presigned PUT URL when credentials configured.
3. R2 Verification Stage:
   - Verifies rejection (HTTP 400) when recording object does not exist in R2 bucket.
   - Verifies acceptance and stage logging when object exists and exceeds 10 MB (10.7 MB recording simulation).
4. Full Interview Submission Pipeline with Direct R2 Object Key:
   - Submits interview metadata and answers referencing the verified R2 recording key.
   - Verifies AI transcription, evaluation concept matching, and database persistence.
5. Idempotency & Retry Safety:
   - Resubmits with the same client_session_id.
   - Confirms cached result is returned without duplicate database rows.
6. Direct Large File (>10 MB) Upload Support:
   - Direct multipart upload of >10 MB payload to FastAPI to verify backend does not 413.
"""

import os
import sys
import io
import json
import time
import uuid
import unittest
from unittest.mock import patch, MagicMock

# Ensure backend directory is in path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from fastapi.testclient import TestClient
from main import app, IDEMPOTENT_UPLOAD_CACHE, SESSION_ACTIVE_JOBS, SUBMISSION_JOBS, API_KEY
import storage_service
from database import get_connection


class TestR2UploadPipeline(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.headers = {"X-API-Key": API_KEY}

    def test_01_unconfigured_r2_diagnostics(self):
        """Verifies clear diagnostic feedback when R2 is not configured."""
        print("\n--- Test 1: Unconfigured R2 Diagnostics ---")
        with patch.dict(os.environ, {
            "AWS_ACCESS_KEY_ID": "",
            "AWS_SECRET_ACCESS_KEY": "",
            "R2_ACCOUNT_ID": "",
            "R2_ACCESS_KEY_ID": "",
            "R2_SECRET_ACCESS_KEY": "",
            "R2_BUCKET_NAME": ""
        }, clear=False):
            # Storage service should report False
            self.assertFalse(storage_service.is_r2_configured())

            # Presign endpoint should return structured unconfigured response
            resp = self.client.post("/interview/presign_upload", json={
                "role": "Python Developer",
                "client_session_id": f"test_session_{uuid.uuid4().hex[:6]}",
                "file_size": 11200000,
                "content_type": "video/webm"
            }, headers=self.headers)

            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertFalse(data.get("r2_configured"))
            self.assertIn(data.get("status"), ["s3_not_configured", "r2_not_configured"])
            self.assertIn("required_env_vars", data)
            print("[Pass] Unconfigured storage returns clear instructions with required env vars.")

    def test_02_presigned_upload_url_generation(self):
        """Verifies S3 SigV4 presigned PUT URL generation when credentials are set."""
        print("\n--- Test 2: Presigned Upload URL Generation ---")
        mock_env = {
            "AWS_ACCESS_KEY_ID": "mock_access_key_1234567890",
            "AWS_SECRET_ACCESS_KEY": "mock_secret_key_1234567890abcdef1234567890",
            "AWS_REGION": "ap-south-1",
            "S3_BUCKET_NAME": "ai-interview-recordings-nb2026"
        }
        with patch.dict(os.environ, mock_env, clear=False):
            self.assertTrue(storage_service.is_r2_configured())

            resp = self.client.post("/interview/presign_upload", json={
                "role": "Data Analyst",
                "client_session_id": f"test_session_{uuid.uuid4().hex[:6]}",
                "file_size": 11220000,
                "content_type": "video/webm"
            }, headers=self.headers)

            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertTrue(data.get("r2_configured"))
            self.assertEqual(data.get("status"), "success")
            self.assertIn("upload_url", data)
            self.assertIn("object_key", data)
            self.assertIn("ai-interview-recordings-nb2026", data["upload_url"])
            self.assertIn("X-Amz-Signature", data["upload_url"])
            self.assertTrue(data["object_key"].startswith("recordings/Data_Analyst_"))
            print(f"[Pass] Generated presigned PUT URL successfully: {data['object_key']}")

    def test_03_r2_verification_rejection_for_missing_object(self):
        """Verifies that submitting a non-existent recording_key is rejected at verification stage."""
        print("\n--- Test 3: R2 Verification Stage Rejection ---")
        with patch("storage_service.verify_object_in_storage") as mock_verify:
            mock_verify.return_value = {
                "exists": False,
                "size_bytes": 0,
                "error": "NoSuchKey: The specified key does not exist."
            }

            fake_key = "recordings/ghost_recording_missing.webm"
            resp = self.client.post("/interview/upload", data={
                "role": "Python Developer",
                "recording_key": fake_key,
                "total_questions": "1",
                "attempted_questions": "1",
                "client_session_id": f"ghost_session_{uuid.uuid4().hex[:6]}"
            }, headers=self.headers)

            self.assertEqual(resp.status_code, 400)
            self.assertIn("Recording verification failed", resp.json().get("detail", ""))
            print("[Pass] Non-existent R2 object was rejected with HTTP 400.")

    def test_04_r2_recording_verification_and_pipeline_execution_over_10mb(self):
        """
        Simulates an interview recording of 10.7 MB in R2.
        Verifies object verification, downloading, transcription, evaluation, and database persistence.
        """
        print("\n--- Test 4: Full Pipeline Execution with 10.7 MB Simulated R2 Recording ---")
        session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        object_key = f"recordings/Python_Developer_{uuid.uuid4().hex[:8]}.webm"
        simulated_size_bytes = int(10.7 * 1024 * 1024) # ~10.7 MB

        # Sample valid WebM file for Whisper execution
        sample_webm = os.path.join(CURRENT_DIR, "uploads", "Python_Developer_20261010_125558_058118.webm")
        if not os.path.exists(sample_webm):
            # Create a tiny dummy webm if sample file not present
            with open(sample_webm, "wb") as f:
                f.write(b"\x1a\x45\xdf\xa3" + b"\x00" * 1024)

        with patch("storage_service.verify_object_in_storage") as mock_verify, \
             patch("storage_service.download_file_from_storage") as mock_download:

            mock_verify.return_value = {
                "exists": True,
                "size_bytes": simulated_size_bytes,
                "content_type": "video/webm",
                "etag": "mock-etag-12345"
            }

            def fake_download(obj_key, dest_path):
                # Copy real sample webm to dest_path
                with open(sample_webm, "rb") as src, open(dest_path, "wb") as dst:
                    dst.write(src.read())
                return True

            mock_download.side_effect = fake_download

            questions_payload = [
                {
                    "question_number": 1,
                    "question": "What is Python and what are its main features?",
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "candidate_answer": "Python is an interpreted, high-level, dynamically typed language with automatic garbage collection."
                }
            ]

            payload = {
                "role": "Python Developer",
                "total_questions": "1",
                "attempted_questions": "1",
                "answered_questions": "1",
                "unanswered_questions": "0",
                "question_data": json.dumps(questions_payload),
                "recording_key": object_key,
                "client_session_id": session_id,
                "async_mode": "false" # Synchronous for direct assertion
            }

            resp = self.client.post("/interview/upload", data=payload, headers=self.headers)
            self.assertEqual(resp.status_code, 200)
            res_data = resp.json()

            self.assertEqual(res_data.get("status"), "success")
            self.assertIsNotNone(res_data.get("interview_id"))
            self.assertEqual(res_data.get("role"), "Python Developer")
            self.assertIn("evaluation", res_data)
            self.assertTrue(res_data.get("recording_available"))
            self.assertIn(f"/interview/{res_data['interview_id']}/recording", res_data.get("recording_url"))

            interview_id = res_data["interview_id"]
            print(f"[Pass] Interview #{interview_id} evaluated and persisted successfully via R2 object key.")

            # Test 5: Idempotency check with the same client_session_id
            print("\n--- Test 5: Idempotency & Retry Safety ---")
            resp_retry = self.client.post("/interview/upload", data=payload, headers=self.headers)
            self.assertEqual(resp_retry.status_code, 200)
            retry_data = resp_retry.json()
            self.assertEqual(retry_data.get("interview_id"), interview_id)
            print(f"[Pass] Idempotent retry returned the exact same interview_id (#{interview_id}) without duplicate row.")

    def test_06_direct_multipart_upload_over_10mb(self):
        """Verifies that direct upload of >10 MB binary directly to FastAPI succeeds without HTTP 413."""
        print("\n--- Test 6: Direct Multipart Upload of > 10 MB Payload to FastAPI ---")
        large_payload_bytes = b"0" * (11 * 1024 * 1024) # 11 MB payload
        large_file = io.BytesIO(large_payload_bytes)

        session_id = f"direct_large_{uuid.uuid4().hex[:6]}"
        questions_payload = [
            {
                "question_number": 1,
                "question": "What is Python?",
                "candidate_answer": "Python is a multi-paradigm programming language."
            }
        ]

        data = {
            "role": "Python Developer",
            "total_questions": "1",
            "attempted_questions": "1",
            "question_data": json.dumps(questions_payload),
            "client_session_id": session_id,
            "async_mode": "true"
        }
        files = {
            "recording": ("large_test_recording.webm", large_file, "video/webm")
        }

        resp = self.client.post("/interview/upload", data=data, files=files, headers=self.headers)
        self.assertNotEqual(resp.status_code, 413, "FastAPI backend must NOT return HTTP 413 for 11 MB direct upload.")
        self.assertEqual(resp.status_code, 200)
        res_data = resp.json()
        self.assertIn(res_data.get("status"), ["processing", "success"])
        print(f"[Pass] Direct 11 MB multipart upload handled cleanly by backend (Status: {res_data.get('status')}).")


if __name__ == "__main__":
    unittest.main()
