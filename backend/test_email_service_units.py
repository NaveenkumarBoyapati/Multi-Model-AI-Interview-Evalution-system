"""
Unit test suite verifying Brevo REST API, SMTP separation, anti-confusion guard,
and fallback logic in email_service.py.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import io
from contextlib import redirect_stdout

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import email_service


class TestEmailService(unittest.TestCase):

    def setUp(self):
        # Clean any test environment variables
        self.saved_env = {}
        for k in ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "SMTP_FROM_EMAIL", "BREVO_API_KEY", "ENV", "RENDER", "VERCEL"]:
            self.saved_env[k] = os.environ.get(k)

    def tearDown(self):
        for k, v in self.saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_brevo_api_configured_detection(self):
        """Valid Brevo REST API keys are detected, while xsmtpsib- keys are flagged as invalid for REST API."""
        os.environ["BREVO_API_KEY"] = "xkeysib-1234567890abcdef"
        self.assertTrue(email_service.is_brevo_api_configured())

        # An SMTP key starting with xsmtpsib- must NOT be considered a valid REST API key
        os.environ["BREVO_API_KEY"] = "xsmtpsib-1234567890abcdef"
        self.assertFalse(email_service.is_brevo_api_configured())

        # Empty key
        os.environ["BREVO_API_KEY"] = ""
        self.assertFalse(email_service.is_brevo_api_configured())

    def test_is_smtp_configured_with_brevo_api_only(self):
        """is_smtp_configured returns True when only BREVO_API_KEY is present."""
        os.environ["SMTP_HOST"] = ""
        os.environ["SMTP_USER"] = ""
        os.environ["SMTP_PASSWORD"] = ""
        os.environ["BREVO_API_KEY"] = "xkeysib-validapikey123"

        self.assertTrue(email_service.is_smtp_configured())
        self.assertEqual(email_service.get_missing_smtp_vars(), [])

    def test_send_via_brevo_api_rejects_smtp_key(self):
        """Brevo REST API call explicitly refuses to execute if passed an xsmtpsib- key."""
        res = email_service.send_via_brevo_api(
            to_email="candidate@example.com",
            clean_name="Test User",
            reset_link="https://app.example.com/reset?token=123",
            api_key="xsmtpsib-invalid-for-api",
            from_email="verified@example.com"
        )
        self.assertFalse(res["sent"])
        self.assertEqual(res["method"], "smtp_error")
        self.assertIn("xsmtpsib", res["error"])

    @patch("urllib.request.urlopen")
    def test_send_via_brevo_api_success(self, mock_urlopen):
        """Brevo REST API dispatches with correct api-key header and payload."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"messageId": "<20261012.test@brevo.com>"}'
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = email_service.send_via_brevo_api(
            to_email="candidate@example.com",
            clean_name="Test Candidate",
            reset_link="https://app.example.com/reset?token=abc",
            api_key="xkeysib-secretkey999",
            from_email="verified@example.com",
            from_name="AI Interview System"
        )
        self.assertTrue(res["sent"])
        self.assertEqual(res["method"], "brevo_api")

        # Verify urllib.request.Request arguments
        call_args = mock_urlopen.call_args[0]
        req = call_args[0]
        self.assertEqual(req.headers.get("Api-key"), "xkeysib-secretkey999")
        self.assertEqual(req.headers.get("Content-type"), "application/json")
        self.assertIn("candidate@example.com", req.data.decode("utf-8"))
        self.assertIn("verified@example.com", req.data.decode("utf-8"))

    @patch("smtplib.SMTP")
    @patch("urllib.request.urlopen")
    def test_smtp_timeout_triggers_brevo_api_fallback(self, mock_urlopen, mock_smtp):
        """When SMTP times out (Render port block), fallback automatically invokes Brevo REST API."""
        os.environ["SMTP_HOST"] = "smtp-relay.brevo.com"
        os.environ["SMTP_PORT"] = "587"
        os.environ["SMTP_USER"] = "login@example.com"
        os.environ["SMTP_PASSWORD"] = "xsmtpsib-smtppassword"
        os.environ["BREVO_API_KEY"] = "xkeysib-restapikey"
        os.environ["SMTP_FROM_EMAIL"] = "verified@example.com"

        # Simulate SMTP timeout
        mock_smtp.side_effect = TimeoutError("Connection timed out to smtp-relay.brevo.com:587")

        # Mock Brevo REST API success
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"messageId": "<fallback.msg.id@brevo.com>"}'
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = email_service.send_password_reset_email(
            to_email="candidate@example.com",
            user_name="Candidate",
            reset_link="https://app.example.com/reset?token=xyz"
        )

        self.assertTrue(res["sent"])
        self.assertEqual(res["method"], "brevo_api")

        # Confirm the REST API was called with BREVO_API_KEY, NOT SMTP_PASSWORD
        call_args = mock_urlopen.call_args[0]
        req = call_args[0]
        self.assertEqual(req.headers.get("Api-key"), "xkeysib-restapikey")
        self.assertNotEqual(req.headers.get("Api-key"), "xsmtpsib-smtppassword")

    def test_safe_diagnostic_never_leaks_secrets(self):
        """Diagnostic output masks user emails and never shows raw passwords or API keys."""
        os.environ["SMTP_HOST"] = "smtp-relay.brevo.com"
        os.environ["SMTP_USER"] = "confidential_user@company.org"
        os.environ["SMTP_PASSWORD"] = "xsmtpsib-verysecretpassword12345"
        os.environ["BREVO_API_KEY"] = "xkeysib-supersecretapikey67890"
        os.environ["SMTP_FROM_EMAIL"] = "sender@company.org"

        f = io.StringIO()
        with redirect_stdout(f):
            email_service.print_smtp_diagnostic()
        output = f.getvalue()

        # Secrets must NOT be present
        self.assertNotIn("verysecretpassword12345", output)
        self.assertNotIn("supersecretapikey67890", output)
        self.assertNotIn("confidential_user@company.org", output)
        # Safe masked indicators must be present
        self.assertIn("CONFIGURED", output)
        self.assertIn("Brevo REST API Fallback", output)


if __name__ == "__main__":
    unittest.main()
