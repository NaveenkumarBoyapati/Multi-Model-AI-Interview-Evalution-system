"""
SMTP Mail Delivery Test Utility for AI Interview Evaluation System.

Allows testing real SMTP connection, authentication, and test email delivery.
Usage:
    python backend/test_smtp.py
    python backend/test_smtp.py --to your_email@domain.com
"""

import sys
import argparse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from env_loader import load_env
load_env()

from email_service import get_smtp_config, is_smtp_configured, print_smtp_diagnostic


def test_smtp_connection(to_email: str = None) -> bool:
    print_smtp_diagnostic()

    cfg = get_smtp_config()
    if not is_smtp_configured():
        print("\n[ERROR] SMTP is not fully configured.")
        print("Please configure in .env (or environment variables):")
        print("  SMTP_HOST=smtp.gmail.com")
        print("  SMTP_PORT=587")
        print("  SMTP_USE_TLS=true")
        print("  SMTP_USER=your_email@gmail.com")
        print("  SMTP_PASSWORD=your_16_char_app_password")
        print("  SMTP_FROM_EMAIL=your_email@gmail.com")
        return False

    print(f"\n[1/3] Connecting to SMTP server at {cfg['host']}:{cfg['port']}...")
    try:
        if cfg.get("use_ssl"):
            print("      Connecting via Implicit SSL (port 465)...")
            server = smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=20)
            print("      Connected and SSL encrypted successfully.")
        else:
            server = smtplib.SMTP(cfg["host"], cfg["port"], timeout=20)
            print("      Connected successfully.")
            if cfg["use_tls"]:
                print("[2/3] Initiating STARTTLS encryption (port 587 / 2525)...")
                server.starttls()
                print("      TLS handshake established.")

        print(f"[3/3] Authenticating as '{cfg['user']}'...")
        server.login(cfg["user"], cfg["password"])
        print("      Authentication SUCCESSFUL!")

        if to_email:
            print(f"\n[Action] Sending verification email to '{to_email}'...")
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "AI Interview Evaluation – SMTP Verification Test"
            msg["From"] = cfg["from_email"]
            msg["To"] = to_email

            text = f"""Hello,

This is a live test email confirming that SMTP email delivery is functioning properly
for the Multi-model AI Interview Evaluation System.

SMTP Host: {cfg['host']}
SMTP Port: {cfg['port']}
Sender: {cfg['from_email']}

If you received this message, password reset emails will successfully arrive in candidate inboxes.

Best regards,
AI Interview Evaluation Team
"""
            html = f"""<!DOCTYPE html>
<html>
<head><style>body {{ font-family: sans-serif; line-height: 1.6; color: #1e293b; }} .box {{ padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px; max-width: 520px; }}</style></head>
<body>
<div class="box">
  <h2 style="color: #2563eb;">AI Interview Evaluation</h2>
  <h3 style="color: #16a34a; margin-top: 0;">&#10004; SMTP Verification Successful</h3>
  <p>This email confirms that the mail delivery system is properly configured and active.</p>
  <ul>
    <li><strong>Host:</strong> {cfg['host']}</li>
    <li><strong>Port:</strong> {cfg['port']}</li>
    <li><strong>Sender:</strong> {cfg['from_email']}</li>
  </ul>
  <p style="color: #64748b; font-size: 13px;">Password reset emails will now be delivered directly to registered candidate inboxes.</p>
</div>
</body>
</html>
"""
            msg.attach(MIMEText(text, "plain"))
            msg.attach(MIMEText(html, "html"))

            server.sendmail(cfg["from_email"], [to_email], msg.as_string())
            print(f"      [EMAIL SENT SUCCESSFULLY] Test email delivered to: {to_email}")

        server.quit()
        print("\n" + "=" * 60)
        print("SMTP VERIFICATION COMPLETED: ALL CHECKS PASSED")
        print("=" * 60)
        return True

    except smtplib.SMTPAuthenticationError as auth_err:
        print(f"\n[FAIL] SMTP Authentication Failed: {auth_err}")
        if "brevo" in cfg["host"].lower() or "sendinblue" in cfg["host"].lower():
            print("\nTroubleshooting tips for Brevo (Sendinblue):")
            print("1. Log in to your Brevo dashboard at https://app.brevo.com")
            print("2. Navigate to: Transactional -> Settings -> Configuration (or SMTP & API -> SMTP)")
            print("3. Ensure SMTP_USER is your Brevo login email or the SMTP login user displayed on that page.")
            print("4. Ensure SMTP_PASSWORD is a generated master SMTP Key (starts with 'xsmtpsib-' or similar).")
            print("5. Ensure SMTP_FROM_EMAIL matches a verified sender in Brevo (Senders & IP -> Senders).")
        else:
            print("\nTroubleshooting tips for Gmail:")
            print("1. Ensure 2-Step Verification is enabled on your Google Account.")
            print("2. Generate a dedicated 16-character App Password at: https://myaccount.google.com/apppasswords")
            print("3. Enter the 16-character App Password into SMTP_PASSWORD (do not use your regular account password).")
            print("4. Remove any spaces from the App Password.")
        return False
    except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, TimeoutError, OSError) as conn_err:
        print(f"\n[FAIL] SMTP Connection Error: {conn_err}")
        if "brevo" in cfg["host"].lower():
            print("\nNotice for Brevo on restricted networks or cloud hosts:")
            print("- If port 587 is blocked by your ISP or cloud host, try port 2525 (SMTP_PORT=2525).")
            print("- Alternatively, try port 465 with SSL (SMTP_PORT=465, SMTP_USE_SSL=true).")
        return False
    except smtplib.SMTPException as smtp_err:
        print(f"\n[FAIL] SMTP Protocol Error: {smtp_err}")
        return False
    except Exception as exc:
        print(f"\n[FAIL] Connection error: {exc}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test SMTP connection and delivery")
    parser.add_argument("--to", type=str, help="Recipient email address to send a live test message to")
    args = parser.parse_args()

    success = test_smtp_connection(to_email=args.to)
    sys.exit(0 if success else 1)
