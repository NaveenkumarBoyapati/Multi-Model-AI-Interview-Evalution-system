import sys
import os
import unittest
import time
from typing import Dict, Any

# Ensure backend is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from transcription import (
    is_usable_candidate_name,
    get_initial_prompt,
    transcribe_recording,
    ACTIVE_MODEL_NAME
)
from database import get_connection


class TestTranscriptionRegression(unittest.TestCase):
    """
    Regression test suite for Whisper STT fixes:
    1. Candidate-name resolution and prompt generation.
    2. Transcription settings and temperature.
    3. Repetition handling and loop prevention.
    4. End-to-end transcription and interview workflow.
    """

    def test_01_candidate_name_validation(self):
        """Short handles or placeholders must not be recognized as full candidate names."""
        # Invalid / short handles that should never bias Whisper
        invalid_names = [
            "Nani", "nani", "Kumar", "kumar", "N", "12", "Admin", "User",
            "candidate", "The Candidate", "Unit Test", "Smoke Tester", "", None, "  "
        ]
        for name in invalid_names:
            self.assertFalse(
                is_usable_candidate_name(name),
                f"Expected name '{name}' to be rejected as full name"
            )

        # Valid full names that should be accepted
        valid_names = [
            "Naveen Kumar",
            "Naveen Kumar Boyapati",
            "John Doe",
            "Ada Lovelace",
            "Lokesh Gurram",
            "Arikatla Bhargav"
        ]
        for name in valid_names:
            self.assertTrue(
                is_usable_candidate_name(name),
                f"Expected full name '{name}' to be accepted"
            )

    def test_02_prompt_generation_name_handling(self):
        """Prompt generation must use Candidate <FullName> for full names, and 'The candidate' for short handles."""
        # Short handle -> 'The candidate'
        prompt_short = get_initial_prompt("Python Developer", "Nani")
        self.assertIn("The candidate discusses education", prompt_short)
        self.assertNotIn("Candidate Nani", prompt_short)

        # None -> 'The candidate'
        prompt_none = get_initial_prompt("Python Developer", None)
        self.assertIn("The candidate discusses education", prompt_none)

        # Full name -> 'Candidate Naveen Kumar Boyapati'
        prompt_full = get_initial_prompt("Python Developer", "Naveen Kumar Boyapati")
        self.assertIn("Candidate Naveen Kumar Boyapati discusses education", prompt_full)

    def test_03_prompt_domain_keywords(self):
        """Prompt generation must include relevant academic projects and technical keywords."""
        # Python Developer
        p_py = get_initial_prompt("Python Developer", "Naveen Kumar Boyapati")
        self.assertIn("drowsiness detection", p_py)
        self.assertIn("face digitisation", p_py)
        self.assertIn("Python", p_py)
        self.assertIn("Power BI", p_py)
        self.assertIn("Excel", p_py)
        self.assertIn("SQL", p_py)

        # Data Analyst
        p_da = get_initial_prompt("Data Analyst", "Naveen Kumar Boyapati")
        self.assertIn("drowsiness detection", p_da)
        self.assertIn("Power BI", p_da)
        self.assertIn("SQL", p_da)
        self.assertIn("Tableau", p_da)

        # Web Developer
        p_web = get_initial_prompt("Web Developer", "Naveen Kumar Boyapati")
        self.assertIn("HTML5", p_web)
        self.assertIn("React", p_web)
        self.assertIn("responsive web design", p_web)

        # Java Developer
        p_java = get_initial_prompt("Java Developer", "Naveen Kumar Boyapati")
        self.assertIn("Java", p_java)
        self.assertIn("Spring Boot", p_java)
        self.assertIn("Hibernate", p_java)

    def test_04_default_model_is_small_en(self):
        """Verify small.en is the active default model on CPU."""
        self.assertEqual(ACTIVE_MODEL_NAME, "small.en")

    def test_05_database_user_profile_name_resolution(self):
        """User 110 profile lookup in DB must resolve to full name 'Naveen Kumar Boyapati'."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, email FROM Users WHERE id = 110")
        row = cur.fetchone()
        cur.close()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[1], "Naveen Kumar Boyapati")
        self.assertTrue(is_usable_candidate_name(row[1]))

    def test_06_e2e_transcription_with_safeguards(self):
        """Transcribe the benchmark recording with new settings: verify accuracy, speed, and no repetition loops."""
        recording_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads", "Python_Developer_20261010_154759_009065.webm")
        if not os.path.exists(recording_path):
            self.skipTest(f"Recording file not found at {recording_path}")

        t0 = time.time()
        res = transcribe_recording(
            recording_path,
            role="Python Developer",
            candidate_name="Naveen Kumar Boyapati"
        )
        t_elapsed = time.time() - t0

        self.assertTrue(res["success"], f"Transcription failed: {res.get('error')}")
        text = res["text"]
        print(f"\n[E2E Test] Transcribed in {t_elapsed:.2f}s: {text}")

        # Accuracy checks
        self.assertIn("Naveen Kumar Boyapati", text)
        self.assertIn("B.Tech", text)
        self.assertIn("P.P. Savani University", text)
        self.assertIn("Power BI", text)
        self.assertIn("SQL", text)
        self.assertIn("Excel", text)

        # Hallucination & repetition loop prevention checks
        self.assertNotIn("thousands of years", text)
        self.assertNotIn("Shnan Kumar", text)
        self.assertNotIn("United States Department of Health", text)

        # Execution time sanity (must be fast on CPU, under 25s)
        self.assertLess(t_elapsed, 25.0)


if __name__ == "__main__":
    unittest.main()
