"""
Email Service for AI Interview Evaluation System.

Handles sending transactional emails (such as password reset links) via SMTP
when configured, and provides clear environment variable instructions and safe
fallback logging when SMTP credentials are not yet set.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List

# Ensure environment variables are loaded
try:
    from env_loader import load_env
except ImportError:
    try:
        from backend.env_loader import load_env
    except ImportError:
        def load_env(override=False):
            return {}

load_env()


def is_production() -> bool:
    """Returns True if running in production mode."""
    env = os.getenv("ENV", os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "development"))).lower()
    return env in ("production", "prod")


def get_smtp_config() -> Dict[str, Any]:
    """Dynamically reads the latest SMTP settings from environment variables."""
    try:
        load_env(override=True)
    except Exception:
        pass

    host = os.getenv("SMTP_HOST", "").strip()
    port_str = os.getenv("SMTP_PORT", "587").strip()
    try:
        port = int(port_str)
    except ValueError:
        port = 587

    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    from_email = os.getenv("SMTP_FROM_EMAIL", "").strip() or user or "noreply@ai-interview.com"
    use_tls_raw = os.getenv("SMTP_USE_TLS", "true").strip().lower()
    use_tls = use_tls_raw in ("true", "1", "yes")

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "from_email": from_email,
        "use_tls": use_tls,
    }


def is_smtp_configured() -> bool:
    """Returns True if the required SMTP environment variables (HOST, USER, PASSWORD) are set."""
    cfg = get_smtp_config()
    return bool(cfg["host"] and cfg["user"] and cfg["password"])


def get_missing_smtp_vars() -> List[str]:
    """Returns a list of missing SMTP environment variable names."""
    cfg = get_smtp_config()
    missing = []
    if not cfg["host"]:
        missing.append("SMTP_HOST")
    if not cfg["user"]:
        missing.append("SMTP_USER")
    if not cfg["password"]:
        missing.append("SMTP_PASSWORD")
    return missing


def print_smtp_diagnostic():
    """
    Prints a safe, non-sensitive diagnostic of SMTP configuration to console.
    Never exposes passwords, App Passwords, or reset tokens.
    """
    cfg = get_smtp_config()
    configured = is_smtp_configured()
    user_configured = bool(cfg["user"])
    pwd_configured = bool(cfg["password"])

    masked_user = ""
    if user_configured:
        parts = cfg["user"].split("@")
        masked_user = (parts[0][:2] + "***@" + parts[1]) if len(parts) == 2 and len(parts[0]) > 2 else "YES (configured)"

    print("=" * 60)
    print("SMTP CONFIGURATION DIAGNOSTIC")
    print("=" * 60)
    print(f"SMTP configured:          {'YES' if configured else 'NO'}")
    print(f"SMTP host:                {cfg['host'] or '(not set)'}")
    print(f"SMTP port:                {cfg['port']}")
    print(f"SMTP TLS enabled:         {'YES' if cfg['use_tls'] else 'NO'}")
    print(f"SMTP user configured:     {'YES' if user_configured else 'NO'}" + (f" ({masked_user})" if user_configured else ""))
    print(f"SMTP password configured: {'YES' if pwd_configured else 'NO'}" + (f" (length: {len(cfg['password'])} chars)" if pwd_configured else ""))
    print(f"SMTP from email:          {cfg['from_email']}")
    print("=" * 60)


def send_password_reset_email(to_email: str, user_name: str, reset_link: str) -> Dict[str, Any]:
    """
    Sends a password reset email to the user.
    If SMTP is configured, sends the email via SMTP.
    If SMTP is not configured, provides a clear fallback notice.
    In production environments, sensitive tokens and links are never exposed in logs.
    """
    clean_name = user_name or "Candidate"
    cfg = get_smtp_config()

    if is_smtp_configured():
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "AI Interview Evaluation – Password Reset"
            msg["From"] = cfg["from_email"]
            msg["To"] = to_email

            text_content = f"""Hello {clean_name},

We received a request to reset the password for your AI Interview Evaluation account.

Please use the link below to set a new password. This single-use link is valid for 15 minutes:
{reset_link}

If you did not request a password reset, please ignore this email. Your account remains secure.

Best regards,
AI Interview Evaluation Team
"""

            html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #1e293b; background-color: #f8fafc; margin: 0; padding: 20px; }}
    .container {{ max-width: 580px; margin: 0 auto; background: #ffffff; padding: 32px; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.04); }}
    .header {{ text-align: center; border-bottom: 1px solid #e2e8f0; padding-bottom: 20px; margin-bottom: 24px; }}
    .header h2 {{ color: #0f172a; margin: 0; font-size: 22px; font-weight: 700; }}
    .btn {{ display: inline-block; padding: 12px 28px; background-color: #2563eb; color: #ffffff !important; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 15px; margin: 20px 0; }}
    .warning {{ background: #fffbeb; border: 1px solid #fef3c7; border-left: 4px solid #f59e0b; padding: 12px 16px; border-radius: 6px; font-size: 13px; color: #92400e; margin: 20px 0; line-height: 1.5; }}
    .footer {{ font-size: 12px; color: #64748b; margin-top: 28px; border-top: 1px solid #e2e8f0; padding-top: 16px; text-align: center; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h2>AI Interview Evaluation System</h2>
      <p style="color: #64748b; font-size: 14px; margin: 4px 0 0 0;">Password Reset Request</p>
    </div>
    <p>Hello <strong>{clean_name}</strong>,</p>
    <p>We received a request to reset the password for your account on the Multi-model AI Interview Evaluation System.</p>
    <p>Click the button below to set your new password. This single-use link is valid for <strong>15 minutes</strong>:</p>
    <div style="text-align: center;">
      <a href="{reset_link}" class="btn" target="_blank">Reset Password</a>
    </div>
    <p style="font-size: 13px; color: #64748b;">Or copy and paste this link into your browser:<br>
      <a href="{reset_link}" style="color: #2563eb; word-break: break-all;">{reset_link}</a>
    </p>
    <div class="warning">
      <strong>Security notice:</strong> If you did not request this password reset, you can safely ignore this email. Your current password remains unchanged and your account is secure.
    </div>
    <div class="footer">
      Multi-model AI Interview Evaluation System &bull; Automated Security Notification<br>
      Please do not reply directly to this automated email.
    </div>
  </div>
</body>
</html>
"""
            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(cfg["host"], cfg["port"], timeout=20) as server:
                if cfg["use_tls"]:
                    server.starttls()
                server.login(cfg["user"], cfg["password"])
                server.sendmail(cfg["from_email"], [to_email], msg.as_string())

            print(f"[Email Service] [EMAIL SENT SUCCESSFULLY] Password reset email successfully dispatched via SMTP to {to_email}")
            return {
                "sent": True,
                "method": "smtp",
                "message": f"Password reset email delivered to {to_email}."
            }

        except smtplib.SMTPAuthenticationError as auth_err:
            print(f"[Email Service Error] SMTP Authentication Failed: {auth_err}")
            return {
                "sent": False,
                "method": "smtp_error",
                "error": "SMTP authentication failed. Please verify SMTP_USER and SMTP_PASSWORD / Gmail App Password.",
                "details": str(auth_err)
            }
        except smtplib.SMTPException as smtp_err:
            print(f"[Email Service Error] SMTP Delivery Failed: {smtp_err}")
            return {
                "sent": False,
                "method": "smtp_error",
                "error": f"SMTP delivery error: {smtp_err}",
                "details": str(smtp_err)
            }
        except Exception as err:
            print(f"[Email Service Error] Unexpected error during SMTP dispatch: {err}")
            return {
                "sent": False,
                "method": "smtp_error",
                "error": f"Failed to send email: {err}",
                "details": str(err)
            }

    else:
        missing_vars = get_missing_smtp_vars()
        print(f"[Email Service] [SMTP NOT CONFIGURED / LOCAL FALLBACK] Missing: {', '.join(missing_vars)}.")
        if not is_production():
            print(f"[Email Service Notice] Reset Link: {reset_link}")
        else:
            print(f"[Email Service Notice] Single-use reset link prepared for '{to_email}' (suppressed in production logs).")
        return {
            "sent": False,
            "method": "unconfigured",
            "missing_vars": missing_vars,
            "instructions": (
                f"To enable real email delivery, configure: {', '.join(missing_vars)} in your .env file. "
                + ("For local testing without SMTP, the reset link is displayed below." if not is_production() else "Configure SMTP credentials for live email delivery.")
            )
        }
