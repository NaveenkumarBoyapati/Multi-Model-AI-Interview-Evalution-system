"""
Authentication Utilities for AI Interview Evaluation System.

Provides:
- Strict password rule enforcement (min 8 chars, uppercase first char, special char)
- Email normalization and validation
- Cryptographically secure PBKDF2-HMAC-SHA256 password hashing and verification
- Token generation and SHA256 token hashing for sessions and password resets
"""

import re
import hmac
import base64
import hashlib
import secrets
from typing import Tuple


SPECIAL_CHARACTERS = set("!@#$%^&*()_+-=[]{}|;:,.<>?/~`'\"\\")


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Enforces password rules:
    1. Minimum 8 characters.
    2. First character must be an uppercase English letter A-Z.
    3. At least one special character, such as @, #, $, or !.
    """
    if not password:
        return False, "Password cannot be empty."

    if len(password) < 8:
        return False, "Password must be at least 8 characters long."

    first_char = password[0]
    if not ('A' <= first_char <= 'Z'):
        return False, "The first character of the password must be an uppercase English letter (A-Z)."

    if not any(ch in SPECIAL_CHARACTERS for ch in password):
        return False, "Password must contain at least one special character (e.g. @, #, $, !)."

    return True, ""


def normalize_email(email: str) -> str:
    """Normalizes email to lowercase and strips surrounding whitespace."""
    if email is None:
        return ""
    return str(email).strip().lower()


def validate_email(email: str) -> Tuple[bool, str]:
    """Validates email format using standard RFC-compliant pattern."""
    cleaned = normalize_email(email)
    if not cleaned:
        return False, "Email address is required."

    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(pattern, cleaned):
        return False, "Please enter a valid email address (e.g. name@example.com)."

    return True, ""


def hash_password(password: str) -> str:
    """
    Hashes a password using PBKDF2-HMAC-SHA256 with 260,000 iterations.
    Format: pbkdf2_sha256$260000$<salt>$<hash>
    """
    if not password:
        raise ValueError("Cannot hash an empty password.")

    salt = secrets.token_urlsafe(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        260000
    )
    b64_hash = base64.urlsafe_b64encode(dk).decode("ascii").rstrip("=")
    return f"pbkdf2_sha256$260000${salt}${b64_hash}"


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verifies a plaintext password against a stored hash using constant-time comparison.
    Supports PBKDF2-HMAC-SHA256 format.
    """
    if not password or not hashed_password:
        return False

    try:
        parts = hashed_password.split("$")
        if len(parts) == 4 and parts[0] == "pbkdf2_sha256":
            _, iters_str, salt, expected_hash = parts
            iterations = int(iters_str)
            dk = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt.encode("utf-8"),
                iterations
            )
            actual_hash = base64.urlsafe_b64encode(dk).decode("ascii").rstrip("=")
            return hmac.compare_digest(actual_hash, expected_hash)

        # Fallback for plain text during testing or migration if any exist
        return hmac.compare_digest(password, hashed_password)
    except Exception:
        return False


def generate_secure_token(nbytes: int = 32) -> str:
    """Generates a cryptographically secure random token string."""
    return secrets.token_urlsafe(nbytes)


def hash_token(token: str) -> str:
    """Computes a SHA-256 hex digest of a token for safe database storage."""
    if not token:
        return ""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
