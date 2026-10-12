"""
Email Delivery & SMTP Test Utility for AI Interview Evaluation System.

Allows testing real SMTP connection, Brevo REST API, authentication, and test email delivery.
Usage:
    python backend/test_smtp.py
    python backend/test_smtp.py --to your_email@domain.com
    python backend/test_smtp.py --mode api --to your_email@domain.com
    python backend/test_smtp.py --mode smtp --to your_email@domain.com
"""

import sys
import argparse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from env_loader import load_env
load_env()

from email_service import (
    get_smtp_config,
    is_smtp_configured,
    is_brevo_api_configured,
    print_smtp_diagnostic,
    send_via_brevo_api
)


def test_smtp_relay(to_email: str = None) -> bool:
    cfg = get_smtp_config()
    if not (cfg["host"] and cfg["user"] and cfg["password"]):
        print("\n[SKIP] Standard SMTP is not fully configured (missing host, user, or password).")
        return False

    print(f"\n[1/3] Connecting to SMTP server at {cfg['host']}:{cfg['port']}...")
    try:
        timeout = cfg.get("timeout", 6)
        if cfg.get("use_ssl"):
            print("      Connecting via Implicit SSL (port 465)...")
            server = smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=timeout)
            print("      Connected and SSL encrypted successfully.")
        else:
            server = smtplib.SMTP(cfg["host"], cfg["port"], timeout=timeout)
            print("      Connected successfully.")
            if cfg["use_tls"]:
                print("[2/3] Initiating STARTTLS encryption (port 587 / 2525)...")
                server.starttls()
                print("      TLS handshake established.")

        print(f"[3/3] Authenticating as '{cfg['user']}'...")
        server.login(cfg["user"], cfg["password"])
        print("      Authentication SUCCESSFUL!")

        if to_email:
            print(f"\n[Action] Sending verification email via SMTP to '{to_email}'...")
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "AI Interview Evaluation – SMTP Relay Verification"
            msg["From"] = f"{cfg['from_name']} <{cfg['from_email']}>" if cfg["from_name"] else cfg["from_email"]
            msg["To"] = to_email

            text = f"""Hello,

This is a live test email confirming that SMTP email delivery is functioning properly
for the Multi-model AI Interview Evaluation System.

SMTP Host: {cfg['host']}
SMTP Port: {cfg['port']}
Sender: {cfg['from_email']}

Best regards,
AI Interview Evaluation Team
"""
            msg.attach(MIMEText(text, "plain"))
            server.sendmail(cfg["from_email"], [to_email], msg.as_string())
            print(f"      [EMAIL SENT SUCCESSFULLY] Test email delivered to: {to_email}")

        server.quit()
        print("\n[SUCCESS] SMTP Relay verification passed.")
        return True

    except smtplib.SMTPAuthenticationError as auth_err:
        print(f"\n[FAIL] SMTP Authentication Failed: {auth_err}")
        return False
    except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, TimeoutError, OSError) as conn_err:
        print(f"\n[FAIL] SMTP Connection Error: {conn_err}")
        print("Note: If running on cloud platforms (e.g., Render), outbound ports 587/465 are often blocked.")
        print("Use BREVO_API_KEY for REST API delivery over HTTPS port 443.")
        return False
    except Exception as exc:
        print(f"\n[FAIL] SMTP Error: {exc}")
        return False


def test_brevo_api(to_email: str = None) -> bool:
    cfg = get_smtp_config()
    key = cfg.get("brevo_api_key", "").strip()

    if not key:
        print("\n[SKIP] Brevo REST API is not configured (BREVO_API_KEY is empty).")
        return False

    if key.startswith("xsmtpsib-"):
        print("\n[FAIL] BREVO_API_KEY starts with 'xsmtpsib-', which is a Brevo SMTP key, NOT a REST API key!")
        print("Obtain a valid API key (starts with 'xkeysib-') from Brevo Dashboard -> SMTP & API -> API Keys.")
        return False

    print(f"\n[1/2] Checking Brevo REST API Key configuration...")
    print(f"      Key prefix: {key[:8]}... (Length: {len(key)} chars)")
    print(f"      Sender email: {cfg['from_email']}")

    target = to_email or cfg["from_email"]
    if not target or target == "noreply@ai-interview.com":
        print("      Please provide a valid recipient via --to your_email@domain.com to send a live test.")
        return True

    print(f"\n[2/2] Sending test email via Brevo HTTPS REST API to '{target}'...")
    sample_link = "https://example.com/test-reset-link"
    res = send_via_brevo_api(
        to_email=target,
        clean_name="System Tester",
        reset_link=sample_link,
        api_key=key,
        from_email=cfg["from_email"],
        from_name=cfg["from_name"]
    )

    if res.get("sent"):
        print("      [EMAIL SENT SUCCESSFULLY] Brevo REST API delivery succeeded!")
        return True
    else:
        print(f"      [FAIL] Brevo REST API delivery failed: {res.get('error')}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test email delivery (SMTP Relay and/or Brevo REST API)")
    parser.add_argument("--to", type=str, help="Recipient email address to send a live test message to")
    parser.add_argument("--mode", type=str, choices=["all", "smtp", "api"], default="all",
                        help="Mode: 'all' (tests both), 'smtp' (SMTP relay only), 'api' (Brevo REST API only)")
    args = parser.parse_args()

    print_smtp_diagnostic()

    if not is_smtp_configured():
        print("\n[ERROR] Email service is not configured.")
        print("Configure either:")
        print("  1. BREVO_API_KEY and SMTP_FROM_EMAIL (for Brevo REST API via HTTPS port 443)")
        print("  2. SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_EMAIL (for SMTP Relay)")
        sys.exit(1)

    overall_ok = False

    if args.mode in ("all", "api"):
        if is_brevo_api_configured():
            api_ok = test_brevo_api(to_email=args.to)
            overall_ok = overall_ok or api_ok

    if args.mode in ("all", "smtp"):
        smtp_ok = test_smtp_relay(to_email=args.to)
        overall_ok = overall_ok or smtp_ok

    print("\n" + "=" * 60)
    print(f"TEST RESULT: {'SUCCESS' if overall_ok else 'FAILED'}")
    print("=" * 60)
    sys.exit(0 if overall_ok else 1)


if __name__ == "__main__":
    main()
