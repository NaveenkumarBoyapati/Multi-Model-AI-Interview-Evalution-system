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
    """Returns True if running in production mode (or on cloud deployment like Render / Vercel)."""
    env = os.getenv("ENV", os.getenv("APP_ENV", os.getenv("ENVIRONMENT", ""))).lower().strip()
    if env in ("production", "prod", "staging"):
        return True
    if os.getenv("RENDER") or os.getenv("VERCEL"):
        return True
    return False


def get_smtp_config() -> Dict[str, Any]:
    """Dynamically reads the latest SMTP settings from environment variables."""
    try:
        load_env(override=False)
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

    # SSL vs TLS detection: port 465 defaults to SSL; port 587 and 2525 default to STARTTLS
    use_ssl_raw = os.getenv("SMTP_USE_SSL", "").strip().lower()
    if use_ssl_raw:
        use_ssl = use_ssl_raw in ("true", "1", "yes")
    else:
        use_ssl = (port == 465)

    use_tls_raw = os.getenv("SMTP_USE_TLS", "true").strip().lower()
    use_tls = (use_tls_raw in ("true", "1", "yes")) and not use_ssl

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "from_email": from_email,
        "use_tls": use_tls,
        "use_ssl": use_ssl,
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
    Never exposes passwords, App Passwords, API keys, or reset tokens.
    """
    cfg = get_smtp_config()
    configured = is_smtp_configured()
    user_configured = bool(cfg["user"])
    pwd_configured = bool(cfg["password"])

    masked_user = ""
    if user_configured:
        parts = cfg["user"].split("@")
        masked_user = (parts[0][:2] + "***@" + parts[1]) if len(parts) == 2 and len(parts[0]) > 2 else "YES (configured)"

    provider = "Custom SMTP"
    if "brevo" in cfg["host"].lower() or "sendinblue" in cfg["host"].lower():
        provider = "Brevo SMTP (smtp-relay.brevo.com)"
    elif "gmail" in cfg["host"].lower():
        provider = "Google Gmail SMTP"

    print("=" * 60)
    print("SMTP CONFIGURATION DIAGNOSTIC")
    print("=" * 60)
    print(f"SMTP provider:            {provider}")
    print(f"SMTP configured:          {'YES' if configured else 'NO'}")
    print(f"SMTP host:                {cfg['host'] or '(not set)'}")
    print(f"SMTP port:                {cfg['port']}")
    print(f"SMTP SSL (port 465):      {'YES' if cfg['use_ssl'] else 'NO'}")
    print(f"SMTP STARTTLS (port 587): {'YES' if cfg['use_tls'] else 'NO'}")
    print(f"SMTP user configured:     {'YES' if user_configured else 'NO'}" + (f" ({masked_user})" if user_configured else ""))
    print(f"SMTP password configured: {'YES' if pwd_configured else 'NO'}" + (f" (length: {len(cfg['password'])} chars)" if pwd_configured else ""))
    print(f"SMTP from email:          {cfg['from_email']}")
    print("=" * 60)


def build_reset_email_text(clean_name: str, reset_link: str) -> str:
    return f"""Hello {clean_name},

We received a request to reset the password for your AI Interview Evaluation account.

Please use the single-use link below to set a new password. This link is valid for 15 minutes:
{reset_link}

Security Notice:
If you did not request a password reset, you can safely ignore this email. Your current password remains unchanged and your account is secure.

Best regards,
AI Interview Evaluation Team
"""


def build_reset_email_html(clean_name: str, reset_link: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Interview Evaluation – Password Reset</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #1e293b; background-color: #f8fafc; margin: 0; padding: 24px; }}
    .container {{ max-width: 560px; margin: 0 auto; background: #ffffff; padding: 36px 32px; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,0.04); }}
    .header {{ text-align: center; border-bottom: 1px solid #f1f5f9; padding-bottom: 22px; margin-bottom: 24px; }}
    .header h2 {{ color: #0f172a; margin: 0; font-size: 22px; font-weight: 700; }}
    .header p {{ color: #64748b; font-size: 13px; margin: 4px 0 0 0; }}
    .greeting {{ font-size: 15px; color: #334155; margin-bottom: 16px; }}
    .btn-container {{ text-align: center; margin: 28px 0; }}
    .btn {{ display: inline-block; padding: 13px 32px; background-color: #2563eb; color: #ffffff !important; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 15px; }}
    .btn:hover {{ background-color: #1d4ed8; }}
    .link-fallback {{ font-size: 12px; color: #64748b; word-break: break-all; margin: 20px 0; background: #f8fafc; padding: 12px; border-radius: 6px; border: 1px solid #e2e8f0; }}
    .link-fallback a {{ color: #2563eb; }}
    .warning {{ background: #fffbeb; border: 1px solid #fef3c7; border-left: 4px solid #f59e0b; padding: 12px 16px; border-radius: 6px; font-size: 13px; color: #92400e; margin: 24px 0; line-height: 1.5; }}
    .footer {{ font-size: 12px; color: #94a3b8; margin-top: 28px; border-top: 1px solid #f1f5f9; padding-top: 18px; text-align: center; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h2>AI Interview Evaluation System</h2>
      <p>Single-Use Password Reset Request</p>
    </div>
    <div class="greeting">
      Hello <strong>{clean_name}</strong>,
    </div>
    <p>We received a request to reset the password for your account. Click the button below to choose a new password. For security, this single-use link is valid for <strong>15 minutes</strong>:</p>
    <div class="btn-container">
      <a href="{reset_link}" class="btn" target="_blank" rel="noopener noreferrer">Reset Password</a>
    </div>
    <div class="link-fallback">
      If the button above does not work, copy and paste this link into your browser:<br>
      <a href="{reset_link}">{reset_link}</a>
    </div>
    <div class="warning">
      <strong>Security notice:</strong> If you did not request this password reset, please disregard this email. Your current password remains active and your account is secure.
    </div>
    <div class="footer">
      Multi-model AI Interview Evaluation System &bull; Automated Security Notification<br>
      This is an automated security email. Please do not reply directly to this address.
    </div>
  </div>
</body>
</html>
"""


def _send_brevo_api_fallback(to_email: str, clean_name: str, reset_link: str, api_key: str, from_email: str) -> Dict[str, Any]:
    """
    Direct HTTPS REST API fallback for Brevo (Sendinblue).
    Operates over port 443 (HTTPS), bypassing any cloud provider / ISP port blocks on SMTP 587/465.
    """
    import urllib.request
    import json

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "sender": {"email": from_email, "name": "AI Interview System"},
        "to": [{"email": to_email, "name": clean_name}],
        "subject": "AI Interview Evaluation – Password Reset",
        "htmlContent": build_reset_email_html(clean_name, reset_link),
        "textContent": build_reset_email_text(clean_name, reset_link)
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp_body = resp.read().decode("utf-8")
            data = json.loads(resp_body) if resp_body else {}
            msg_id = data.get("messageId", "ok")
            print(f"[Email Service] [EMAIL SENT SUCCESSFULLY] Password reset dispatched via Brevo REST API to {to_email} (messageId: {msg_id})")
            return {
                "sent": True,
                "method": "brevo_api",
                "message": f"Password reset email delivered to {to_email}."
            }
    except Exception as exc:
        print(f"[Email Service Error] Brevo REST API fallback failed: {exc}")
        return {
            "sent": False,
            "method": "smtp_error",
            "error": f"Brevo API error: {exc}",
            "details": str(exc)
        }


def send_password_reset_email(to_email: str, user_name: str, reset_link: str) -> Dict[str, Any]:
    """
    Sends a password reset email to the user.
    If SMTP is configured, sends the email via standard SMTP (Brevo, Gmail, or custom SMTP).
    If SMTP connection times out or fails on Brevo, automatically falls back to Brevo HTTPS API.
    If SMTP is not configured, provides clear diagnostic notice.
    In production mode, sensitive tokens and links are NEVER exposed in logs or API responses.
    """
    clean_name = user_name or "Candidate"
    cfg = get_smtp_config()

    if is_smtp_configured():
        text_content = build_reset_email_text(clean_name, reset_link)
        html_content = build_reset_email_html(clean_name, reset_link)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "AI Interview Evaluation – Password Reset"
        msg["From"] = cfg["from_email"]
        msg["To"] = to_email
        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        is_brevo = ("brevo" in cfg["host"].lower()) or ("sendinblue" in cfg["host"].lower())

        try:
            if cfg["use_ssl"]:
                server = smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=20)
            else:
                server = smtplib.SMTP(cfg["host"], cfg["port"], timeout=20)
                if cfg["use_tls"]:
                    server.starttls()

            with server:
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
            # If Brevo, attempt HTTPS API with the same key
            if is_brevo:
                print("[Email Service Notice] SMTP authentication failed on Brevo relay. Attempting Brevo HTTPS REST API fallback...")
                api_res = _send_brevo_api_fallback(to_email, clean_name, reset_link, cfg["password"], cfg["from_email"])
                if api_res.get("sent"):
                    return api_res

            return {
                "sent": False,
                "method": "smtp_error",
                "error": "SMTP authentication failed. Please verify SMTP_USER and SMTP_PASSWORD.",
                "details": str(auth_err)
            }
        except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, TimeoutError, OSError) as conn_err:
            print(f"[Email Service Error] SMTP Connection Failed ({cfg['host']}:{cfg['port']}): {conn_err}")
            # If Brevo, fallback to HTTPS API
            if is_brevo:
                print("[Email Service Notice] Outbound SMTP port may be restricted by cloud host. Attempting Brevo HTTPS REST API fallback (port 443)...")
                api_res = _send_brevo_api_fallback(to_email, clean_name, reset_link, cfg["password"], cfg["from_email"])
                if api_res.get("sent"):
                    return api_res

            return {
                "sent": False,
                "method": "smtp_error",
                "error": f"SMTP connection error: {conn_err}",
                "details": str(conn_err)
            }
        except smtplib.SMTPException as smtp_err:
            print(f"[Email Service Error] SMTP Delivery Failed: {smtp_err}")
            if is_brevo:
                print("[Email Service Notice] Attempting Brevo HTTPS REST API fallback...")
                api_res = _send_brevo_api_fallback(to_email, clean_name, reset_link, cfg["password"], cfg["from_email"])
                if api_res.get("sent"):
                    return api_res

            return {
                "sent": False,
                "method": "smtp_error",
                "error": f"SMTP delivery error: {smtp_err}",
                "details": str(smtp_err)
            }
        except Exception as err:
            print(f"[Email Service Error] Unexpected error during SMTP dispatch: {err}")
            if is_brevo:
                print("[Email Service Notice] Attempting Brevo HTTPS REST API fallback...")
                api_res = _send_brevo_api_fallback(to_email, clean_name, reset_link, cfg["password"], cfg["from_email"])
                if api_res.get("sent"):
                    return api_res

            return {
                "sent": False,
                "method": "smtp_error",
                "error": f"Failed to send email: {err}",
                "details": str(err)
            }

    else:
        missing_vars = get_missing_smtp_vars()
        print(f"[Email Service] [SMTP NOT CONFIGURED] Missing: {', '.join(missing_vars)}.")
        if not is_production():
            print(f"[Email Service Notice] [Local Dev Fallback] Reset Link: {reset_link}")
        else:
            print(f"[Email Service Notice] Single-use reset link prepared for '{to_email}' (suppressed in production logs).")
        return {
            "sent": False,
            "method": "unconfigured",
            "missing_vars": missing_vars,
            "instructions": (
                f"To enable real email delivery, configure: {', '.join(missing_vars)} in your .env file or Render Environment. "
                + ("For local testing without SMTP, the reset link is displayed below." if not is_production() else "Configure SMTP credentials for live email delivery.")
            )
        }
