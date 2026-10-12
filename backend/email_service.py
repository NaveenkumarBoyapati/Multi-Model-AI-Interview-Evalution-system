"""
Email Service for AI Interview Evaluation System.

Handles sending transactional emails (such as single-use password reset links)
via standard SMTP (Brevo relay, Gmail, custom SMTP) and/or Brevo HTTPS REST API.

Key Design & Operational Security:
1. SMTP Relay: Uses SMTP_HOST, SMTP_PORT, SMTP_USER, and SMTP_PASSWORD.
2. Brevo REST API: Uses BREVO_API_KEY (passed in 'api-key' header over HTTPS port 443).
   Never uses SMTP_PASSWORD as the Brevo REST API key.
3. Fallback & Egress Handling:
   Cloud container platforms (e.g. Render free/starter tiers) frequently drop/block
   outbound connections on SMTP ports 587 and 465. When SMTP times out, the service
   seamlessly falls back to Brevo HTTPS REST API (port 443).
4. Sender Verification:
   Brevo enforces sender email verification. SMTP_FROM_EMAIL / BREVO_SENDER_EMAIL
   must match a verified sender in the Brevo account.
5. Safe Diagnostics:
   Diagnostic logs never print passwords, API keys, or security tokens.
"""

import os
import smtplib
import socket
import json
import urllib.request
import urllib.error
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional

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
    """Dynamically reads the latest SMTP and Email API settings from environment variables."""
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
    brevo_api_key = os.getenv("BREVO_API_KEY", "").strip()

    from_email = (
        os.getenv("SMTP_FROM_EMAIL", "").strip()
        or os.getenv("BREVO_SENDER_EMAIL", "").strip()
        or user
        or "noreply@ai-interview.com"
    )
    from_name = (
        os.getenv("SMTP_FROM_NAME", "").strip()
        or os.getenv("BREVO_SENDER_NAME", "").strip()
        or "AI Interview Evaluation System"
    )

    # SSL vs TLS detection: port 465 defaults to SSL; port 587 and 2525 default to STARTTLS
    use_ssl_raw = os.getenv("SMTP_USE_SSL", "").strip().lower()
    if use_ssl_raw:
        use_ssl = use_ssl_raw in ("true", "1", "yes")
    else:
        use_ssl = (port == 465)

    use_tls_raw = os.getenv("SMTP_USE_TLS", "true").strip().lower()
    use_tls = (use_tls_raw in ("true", "1", "yes")) and not use_ssl

    try:
        timeout = int(os.getenv("SMTP_TIMEOUT", "6").strip())
    except ValueError:
        timeout = 6

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "brevo_api_key": brevo_api_key,
        "from_email": from_email,
        "from_name": from_name,
        "use_tls": use_tls,
        "use_ssl": use_ssl,
        "timeout": timeout,
    }


def is_brevo_api_configured() -> bool:
    """Returns True if a valid-format Brevo REST API key is configured."""
    cfg = get_smtp_config()
    key = cfg.get("brevo_api_key", "").strip()
    # Reject empty or mistakenly provided SMTP keys (starts with xsmtpsib-)
    return bool(key and not key.startswith("xsmtpsib-"))


def is_smtp_configured() -> bool:
    """
    Returns True if email delivery is configured via either:
    1. Brevo REST API (BREVO_API_KEY) over HTTPS port 443, OR
    2. Standard SMTP relay (SMTP_HOST, SMTP_USER, SMTP_PASSWORD).
    """
    cfg = get_smtp_config()
    has_smtp = bool(cfg["host"] and cfg["user"] and cfg["password"])
    has_brevo_api = is_brevo_api_configured()
    return has_smtp or has_brevo_api


def get_missing_smtp_vars() -> List[str]:
    """Returns a list of missing email delivery configuration variables."""
    cfg = get_smtp_config()
    if is_brevo_api_configured():
        return []
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
    Prints a safe, non-sensitive diagnostic of SMTP and Email API configuration to console.
    Never exposes passwords, App Passwords, API keys, or reset tokens.
    """
    cfg = get_smtp_config()
    smtp_ok = is_smtp_configured()
    user_configured = bool(cfg["user"])
    pwd_configured = bool(cfg["password"])
    api_key_configured = bool(cfg["brevo_api_key"])

    masked_user = ""
    if user_configured:
        parts = cfg["user"].split("@")
        masked_user = (parts[0][:2] + "***@" + parts[1]) if len(parts) == 2 and len(parts[0]) > 2 else "YES (configured)"

    masked_from = cfg["from_email"]
    if "@" in masked_from:
        fparts = masked_from.split("@")
        masked_from = (fparts[0][:2] + "***@" + fparts[1]) if len(fparts[0]) > 2 else masked_from

    # Safe Brevo API Key status
    api_key_status = "NOT CONFIGURED"
    if api_key_configured:
        raw_key = cfg["brevo_api_key"]
        if raw_key.startswith("xsmtpsib-"):
            api_key_status = "MISCONFIGURED (starts with 'xsmtpsib-', which is an SMTP key, NOT a REST API key!)"
        elif raw_key.startswith("xkeysib-"):
            api_key_status = f"CONFIGURED (valid Brevo v3 API key format, length: {len(raw_key)} chars)"
        else:
            api_key_status = f"CONFIGURED (length: {len(raw_key)} chars)"

    # Safe SMTP Password status
    pwd_status = "NOT CONFIGURED"
    if pwd_configured:
        pwd = cfg["password"]
        if pwd.startswith("xsmtpsib-"):
            pwd_status = f"CONFIGURED (Brevo SMTP key, length: {len(pwd)} chars)"
        elif "gmail" in cfg["host"].lower():
            pwd_status = f"CONFIGURED (Gmail App Password, length: {len(pwd)} chars)"
        else:
            pwd_status = f"CONFIGURED (length: {len(pwd)} chars)"

    # Determine delivery mode
    if cfg["host"] and pwd_configured and api_key_configured:
        mode = f"SMTP Relay ({cfg['host']}:{cfg['port']}) with Brevo REST API Fallback (HTTPS 443)"
    elif api_key_configured:
        mode = "Brevo REST API Direct (HTTPS port 443)"
    elif cfg["host"] and pwd_configured:
        mode = f"SMTP Relay ({cfg['host']}:{cfg['port']})"
    else:
        mode = "Unconfigured"

    print("=" * 60)
    print("EMAIL DELIVERY SERVICE DIAGNOSTIC")
    print("=" * 60)
    print(f"Delivery Mode:            {mode}")
    print(f"Email Service Active:     {'YES' if smtp_ok else 'NO'}")
    print(f"Brevo REST API Key:       {api_key_status}")
    print(f"SMTP Host:                {cfg['host'] or '(not set)'}")
    print(f"SMTP Port:                {cfg['port']}")
    print(f"SMTP SSL (port 465):      {'YES' if cfg['use_ssl'] else 'NO'}")
    print(f"SMTP STARTTLS (port 587): {'YES' if cfg['use_tls'] else 'NO'}")
    print(f"SMTP User:                {'YES' if user_configured else 'NO'}" + (f" ({masked_user})" if user_configured else ""))
    print(f"SMTP Password:            {pwd_status}")
    print(f"Sender From Email:        {masked_from}")
    print(f"Sender From Name:         {cfg['from_name']}")
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


def send_via_brevo_api(
    to_email: str,
    clean_name: str,
    reset_link: str,
    api_key: Optional[str] = None,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sends transactional email directly via Brevo v3 HTTPS REST API.
    Endpoint: https://api.brevo.com/v3/smtp/email (Port 443 / HTTPS).

    Security & Validation Rules:
    1. Authenticates via 'api-key' header using BREVO_API_KEY.
    2. Strictly rejects SMTP keys (starting with 'xsmtpsib-') to avoid HTTP 401 Unauthorized.
    3. Never logs or leaks the api-key or reset link in output.
    4. Handles verified sender emails as required by Brevo policy.
    """
    cfg = get_smtp_config()
    resolved_key = (api_key or cfg.get("brevo_api_key", "")).strip()
    resolved_from = (from_email or cfg.get("from_email", "")).strip() or "noreply@ai-interview.com"
    resolved_name = (from_name or cfg.get("from_name", "")).strip() or "AI Interview Evaluation System"

    if not resolved_key:
        print("[Email Service Error] Brevo REST API dispatch aborted: BREVO_API_KEY is not set.")
        return {
            "sent": False,
            "method": "smtp_error",
            "error": "BREVO_API_KEY is not configured.",
            "details": "BREVO_API_KEY environment variable is empty."
        }

    # Anti-confusion guard: Brevo SMTP keys start with 'xsmtpsib-' and CANNOT be used for the REST API
    if resolved_key.startswith("xsmtpsib-"):
        print(
            "[Email Service Error] Configuration Mismatch: BREVO_API_KEY starts with 'xsmtpsib-', "
            "which is a Brevo SMTP key, not a Brevo REST API key. Brevo REST API requires an API key "
            "(starting with 'xkeysib-') generated under Brevo Dashboard -> SMTP & API -> API Keys. "
            "Aborting REST API request to prevent HTTP 401 Unauthorized."
        )
        return {
            "sent": False,
            "method": "smtp_error",
            "error": "Misconfigured BREVO_API_KEY: Received an SMTP key (xsmtpsib-). REST API requires an API key (xkeysib-).",
            "details": "Invalid key format for Brevo REST API."
        }

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "api-key": resolved_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "AI-Interview-Evaluation-System/2.4"
    }
    payload = {
        "sender": {"email": resolved_from, "name": resolved_name},
        "to": [{"email": to_email, "name": clean_name}],
        "subject": "AI Interview Evaluation – Password Reset",
        "htmlContent": build_reset_email_html(clean_name, reset_link),
        "textContent": build_reset_email_text(clean_name, reset_link)
    }

    try:
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=12) as resp:
            resp_body = resp.read().decode("utf-8")
            data = json.loads(resp_body) if resp_body else {}
            msg_id = data.get("messageId", "ok")
            print(f"[Email Service] [EMAIL SENT SUCCESSFULLY] Password reset delivered via Brevo REST API to {to_email} (messageId: {msg_id})")
            return {
                "sent": True,
                "method": "brevo_api",
                "message": f"Password reset email delivered to {to_email} via Brevo REST API.",
                "message_id": msg_id
            }
    except urllib.error.HTTPError as http_err:
        err_code = http_err.code
        err_msg = ""
        try:
            body = http_err.read().decode("utf-8")
            parsed = json.loads(body)
            err_msg = parsed.get("message", body)
        except Exception:
            err_msg = str(http_err)

        if err_code == 401:
            print(f"[Email Service Error] Brevo REST API HTTP 401 Unauthorized ({err_msg}). Verify that BREVO_API_KEY is a valid v3 API key from Brevo Dashboard -> SMTP & API -> API Keys.")
        elif err_code == 400:
            print(f"[Email Service Error] Brevo REST API HTTP 400 Bad Request ({err_msg}). Ensure sender '{resolved_from}' is verified in Brevo Dashboard -> Senders & IP -> Senders.")
        else:
            print(f"[Email Service Error] Brevo REST API HTTP {err_code}: {err_msg}")

        return {
            "sent": False,
            "method": "smtp_error",
            "error": f"Brevo API error HTTP {err_code}: {err_msg}",
            "details": f"HTTP {err_code}: {err_msg}"
        }
    except Exception as exc:
        print(f"[Email Service Error] Brevo REST API request failed: {exc}")
        return {
            "sent": False,
            "method": "smtp_error",
            "error": f"Brevo API network error: {exc}",
            "details": str(exc)
        }


def _send_brevo_api_fallback(to_email: str, clean_name: str, reset_link: str, api_key: str, from_email: str) -> Dict[str, Any]:
    """Compatibility wrapper for send_via_brevo_api."""
    return send_via_brevo_api(to_email, clean_name, reset_link, api_key=api_key, from_email=from_email)


def send_password_reset_email(to_email: str, user_name: str, reset_link: str) -> Dict[str, Any]:
    """
    Sends a single-use password reset email to the specified recipient.

    Delivery Strategy:
    1. If unconfigured (neither SMTP nor BREVO_API_KEY), returns unconfigured status.
       (Suppresses links in production, shows safe dev link on localhost only).
    2. If SMTP_HOST is not set but BREVO_API_KEY is set:
       Directly dispatches via Brevo HTTPS REST API (port 443).
    3. If SMTP_HOST is set:
       Attempts SMTP dispatch with configured timeout (default 6s).
       If SMTP connection times out, disconnects, or fails AND BREVO_API_KEY is configured:
       Seamlessly falls back to Brevo HTTPS REST API (port 443).
    """
    clean_name = user_name or "Candidate"
    cfg = get_smtp_config()

    if not is_smtp_configured():
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

    has_smtp = bool(cfg["host"] and cfg["user"] and cfg["password"])
    has_brevo_api = is_brevo_api_configured()

    # If only Brevo REST API is configured (or SMTP_HOST is omitted), send via REST API directly
    if has_brevo_api and not has_smtp:
        print(f"[Email Service] Dispatching password reset via Brevo REST API (HTTPS port 443) to {to_email}...")
        return send_via_brevo_api(
            to_email=to_email,
            clean_name=clean_name,
            reset_link=reset_link,
            api_key=cfg["brevo_api_key"],
            from_email=cfg["from_email"],
            from_name=cfg["from_name"]
        )

    # Otherwise, SMTP is configured. Attempt SMTP delivery first.
    text_content = build_reset_email_text(clean_name, reset_link)
    html_content = build_reset_email_html(clean_name, reset_link)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "AI Interview Evaluation – Password Reset"
    msg["From"] = f"{cfg['from_name']} <{cfg['from_email']}>" if cfg["from_name"] else cfg["from_email"]
    msg["To"] = to_email
    msg.attach(MIMEText(text_content, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    timeout_val = cfg["timeout"]

    try:
        print(f"[Email Service] Attempting SMTP delivery to {to_email} via {cfg['host']}:{cfg['port']} (timeout={timeout_val}s)...")
        if cfg["use_ssl"]:
            server = smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=timeout_val)
        else:
            server = smtplib.SMTP(cfg["host"], cfg["port"], timeout=timeout_val)
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

    except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, TimeoutError, OSError, socket.timeout) as conn_err:
        print(f"[Email Service Error] SMTP connection failed ({cfg['host']}:{cfg['port']}): {conn_err}")
        print("[Email Service Notice] Note: Render and cloud containers often block or drop outbound SMTP ports 587 and 465.")
        if has_brevo_api:
            print("[Email Service Notice] Seamlessly falling back to Brevo HTTPS REST API (port 443)...")
            api_res = send_via_brevo_api(
                to_email=to_email,
                clean_name=clean_name,
                reset_link=reset_link,
                api_key=cfg["brevo_api_key"],
                from_email=cfg["from_email"],
                from_name=cfg["from_name"]
            )
            if api_res.get("sent"):
                return api_res
            return api_res

        return {
            "sent": False,
            "method": "smtp_error",
            "error": f"SMTP connection error: {conn_err}. In cloud environments, configure BREVO_API_KEY to bypass SMTP port restrictions.",
            "details": str(conn_err)
        }

    except smtplib.SMTPAuthenticationError as auth_err:
        print(f"[Email Service Error] SMTP Authentication Failed: {auth_err}")
        if has_brevo_api:
            print("[Email Service Notice] SMTP authentication failed. Attempting Brevo HTTPS REST API fallback...")
            api_res = send_via_brevo_api(
                to_email=to_email,
                clean_name=clean_name,
                reset_link=reset_link,
                api_key=cfg["brevo_api_key"],
                from_email=cfg["from_email"],
                from_name=cfg["from_name"]
            )
            if api_res.get("sent"):
                return api_res
            return api_res

        return {
            "sent": False,
            "method": "smtp_error",
            "error": "SMTP authentication failed. Please verify SMTP_USER and SMTP_PASSWORD.",
            "details": str(auth_err)
        }

    except smtplib.SMTPException as smtp_err:
        print(f"[Email Service Error] SMTP Delivery Failed: {smtp_err}")
        if has_brevo_api:
            print("[Email Service Notice] SMTP delivery failed. Attempting Brevo HTTPS REST API fallback...")
            api_res = send_via_brevo_api(
                to_email=to_email,
                clean_name=clean_name,
                reset_link=reset_link,
                api_key=cfg["brevo_api_key"],
                from_email=cfg["from_email"],
                from_name=cfg["from_name"]
            )
            if api_res.get("sent"):
                return api_res
            return api_res

        return {
            "sent": False,
            "method": "smtp_error",
            "error": f"SMTP delivery error: {smtp_err}",
            "details": str(smtp_err)
        }

    except Exception as err:
        print(f"[Email Service Error] Unexpected error during email dispatch: {err}")
        if has_brevo_api:
            print("[Email Service Notice] Attempting Brevo HTTPS REST API fallback...")
            api_res = send_via_brevo_api(
                to_email=to_email,
                clean_name=clean_name,
                reset_link=reset_link,
                api_key=cfg["brevo_api_key"],
                from_email=cfg["from_email"],
                from_name=cfg["from_name"]
            )
            if api_res.get("sent"):
                return api_res
            return api_res

        return {
            "sent": False,
            "method": "smtp_error",
            "error": f"Failed to send email: {err}",
            "details": str(err)
        }
