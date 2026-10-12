from fastapi import (
    FastAPI,
    Request,
    UploadFile,
    File,
    Form,
    Header,
    HTTPException,
    Depends,
    Query
)
from fastapi.responses import RedirectResponse, Response, FileResponse

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel, Field

from database import get_connection
from transcription import transcribe_recording, is_usable_candidate_name
from question_segmentation import create_question_segments
from question_bank import get_expected_concepts
from evaluation import evaluate_interview, is_valid_answer
from report_generator import generate_interview_report_pdf
from admin_service import (
    init_admin_schema,
    log_admin_action,
    get_super_admin_dashboard_metrics,
    get_admin_users_list,
    create_user_by_admin,
    toggle_user_active_status,
    admin_reset_user_password,
    get_admin_interviews_list,
    get_admin_questions_list,
    create_question_by_admin,
    update_question_by_admin,
    delete_question_by_admin,
    get_admin_roles_list,
    create_role_by_admin,
    update_role_by_admin,
    get_admin_security_data,
    get_admin_audit_logs,
    check_system_health,
    get_admin_advanced_analytics
)

from auth_utils import (
    validate_password,
    normalize_email,
    validate_email,
    hash_password,
    verify_password,
    generate_secure_token,
    hash_token
)
from email_service import (
    send_password_reset_email,
    is_smtp_configured,
    get_missing_smtp_vars,
    print_smtp_diagnostic
)
from env_loader import load_env

# Ensure environment variables from .env files are loaded
load_env()


import os
import re
import shutil
import json
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any


# =========================================
# PROJECT BASE DIRECTORY
# =========================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


# =========================================
# FASTAPI APPLICATION
# =========================================

app = FastAPI(
    title="AI Interview Evaluation System",
    description="Backend API for AI Interview Evaluation System",
    version="2.0.0"
)


# =========================================
# SERVE FRONTEND STATIC FILES
# =========================================

app.mount(
    "/app",
    StaticFiles(
        directory=BASE_DIR,
        html=True
    ),
    name="frontend"
)

app.mount(
    "/css",
    StaticFiles(
        directory=os.path.join(BASE_DIR, "css")
    ),
    name="css"
)

app.mount(
    "/js",
    StaticFiles(
        directory=os.path.join(BASE_DIR, "js")
    ),
    name="js"
)

app.mount(
    "/images",
    StaticFiles(
        directory=os.path.join(BASE_DIR, "images")
    ),
    name="images"
)

app.mount(
    "/uploads",
    StaticFiles(
        directory=os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "uploads"
        )
    ),
    name="uploads"
)


# =========================================
# CORS MIDDLEWARE
# =========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)


# =========================================
# API SECURITY KEY
# =========================================

API_KEY = "AI_INTERVIEW_2026_SECRET"


# =========================================
# UPLOADS DIRECTORIES
# =========================================

UPLOAD_DIR = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)
    ),
    "uploads"
)

os.makedirs(UPLOAD_DIR, exist_ok=True)

QUESTION_SEGMENTS_DIR = os.path.join(
    UPLOAD_DIR,
    "question_segments"
)

os.makedirs(QUESTION_SEGMENTS_DIR, exist_ok=True)


# =========================================
# HEALTH CHECK ENDPOINT
# =========================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "AI Interview Evaluation System API",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)


# =========================================
# HOME ENDPOINT / REDIRECTS
# =========================================

@app.get("/")
def home():
    return RedirectResponse(url="/app/login.html")


@app.get("/login.html")
def redirect_login():
    return RedirectResponse(url="/app/login.html")


@app.get("/dashboard.html")
def redirect_dashboard():
    return RedirectResponse(url="/app/dashboard.html")


@app.get("/admin_dashboard.html")
def redirect_admin_dashboard():
    return RedirectResponse(url="/app/admin_dashboard.html")


@app.get("/forgot_password.html")
def redirect_forgot_password(request: Request):
    q = request.url.query
    return RedirectResponse(url="/app/forgot_password.html" + (f"?{q}" if q else ""))


@app.get("/reset_password.html")
def redirect_reset_password(request: Request):
    q = request.url.query
    return RedirectResponse(url="/app/reset_password.html" + (f"?{q}" if q else ""))


@app.get("/change_password.html")
def redirect_change_password(request: Request):
    q = request.url.query
    return RedirectResponse(url="/app/change_password.html" + (f"?{q}" if q else ""))


@app.get("/profile.html")
def redirect_profile(request: Request):
    q = request.url.query
    return RedirectResponse(url="/app/profile.html" + (f"?{q}" if q else ""))


# =========================================
# AUTHENTICATION & USER REQUEST MODELS
# =========================================

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: str = Field(...)
    password: str = Field(...)
    role: Optional[str] = "User"
    preferred_role: Optional[str] = None


class LoginRequest(BaseModel):
    email: str = Field(...)
    password: str = Field(...)
    role: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(...)
    new_password: str = Field(...)
    confirm_password: str = Field(...)


class ForgotPasswordRequest(BaseModel):
    email: str = Field(...)


class ResetPasswordRequest(BaseModel):
    token: str = Field(...)
    new_password: str = Field(...)
    confirm_password: str = Field(...)


class AdminUserUpdateRequest(BaseModel):
    name: Optional[str] = None
    preferred_role: Optional[str] = None
    is_admin: Optional[bool] = None


class AdminUserCreateRequest(BaseModel):
    name: str = Field(...)
    email: str = Field(...)
    password: str = Field(...)
    preferred_role: Optional[str] = "General"
    is_admin: Optional[bool] = False
    is_active: Optional[bool] = True


class AdminUserToggleStatusRequest(BaseModel):
    is_active: bool = Field(...)


class AdminUserResetPasswordRequest(BaseModel):
    new_password: str = Field(...)


class AdminQuestionCreateRequest(BaseModel):
    role_name: Optional[str] = None
    role: Optional[str] = None
    category: Optional[str] = "Technical"
    difficulty: Optional[str] = "Medium"
    question_text: str = Field(...)
    expected_topics: Optional[str] = ""
    expected_concepts: Optional[str] = ""
    reference_answer: Optional[str] = ""
    evaluation_guidance: Optional[str] = ""
    is_active: Optional[bool] = True


class AdminQuestionUpdateRequest(BaseModel):
    role_name: Optional[str] = None
    role: Optional[str] = None
    category: Optional[str] = "Technical"
    difficulty: Optional[str] = "Medium"
    question_text: Optional[str] = None
    expected_topics: Optional[str] = ""
    expected_concepts: Optional[str] = ""
    reference_answer: Optional[str] = ""
    evaluation_guidance: Optional[str] = ""
    is_active: Optional[bool] = True


class AdminRoleCreateRequest(BaseModel):
    role_name: str = Field(...)
    slug: Optional[str] = ""
    description: Optional[str] = ""
    topics: Optional[str] = ""
    icon: Optional[str] = "fa-briefcase"


class AdminRoleUpdateRequest(BaseModel):
    role_name: Optional[str] = None
    description: Optional[str] = ""
    topics: Optional[str] = ""
    icon: Optional[str] = "fa-briefcase"
    is_active: Optional[bool] = True


class AdminProfileUpdateRequest(BaseModel):
    name: str = Field(...)
    email: str = Field(...)


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    preferred_role: Optional[str] = None


# =========================================
# STARTUP EVENT: SEED ADMIN & VERIFY TABLES
# =========================================

def _run_background_startup_auth():
    """Seeds default admin if none exists and ensures tables/indexes are ready."""
    try:
        connection = get_connection()
        cursor = connection.cursor()

        # Check if an admin exists
        cursor.execute("SELECT COUNT(*) FROM Users WHERE is_admin = 1")
        admin_count = cursor.fetchone()[0]

        if admin_count == 0:
            admin_email = "admin@ai-interview.com"
            admin_pwd_hash = hash_password("Admin@Interview2026!")
            cursor.execute("SELECT id FROM Users WHERE LOWER(email) = ?", (admin_email,))
            existing = cursor.fetchone()
            if existing:
                cursor.execute("""
                    UPDATE Users 
                    SET is_admin = 1, password_hash = ?, preferred_role = 'System Administrator'
                    WHERE id = ?
                """, (admin_pwd_hash, existing[0]))
            else:
                cursor.execute("""
                    INSERT INTO Users (name, email, password_hash, is_admin, preferred_role, created_at)
                    VALUES ('System Administrator', ?, ?, 1, 'System Administrator', GETUTCDATE())
                """, (admin_email, admin_pwd_hash))
            connection.commit()
            print("[Startup Auth] Seeded default administrator account: admin@ai-interview.com")

        # Ensure Interviews, InterviewHistory, and Feedback tables have all required columns and definitions
        try:
            from database import DB_ENGINE
            is_pg = (DB_ENGINE in ("postgres", "postgresql", "neon") or bool(os.getenv("DATABASE_URL") and DB_ENGINE != "sqlite"))
            if is_pg:
                cursor.execute("ALTER TABLE Interviews ADD COLUMN IF NOT EXISTS termination_type VARCHAR(50) NULL")
                cursor.execute("ALTER TABLE Interviews ADD COLUMN IF NOT EXISTS security_violation INT NULL")
                cursor.execute("ALTER TABLE Interviews ADD COLUMN IF NOT EXISTS terminated_at TIMESTAMP NULL")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS InterviewHistory (
                        id SERIAL PRIMARY KEY,
                        interview_id INT NOT NULL,
                        user_id INT NULL,
                        role VARCHAR(100) NULL,
                        attempt_number INT NULL,
                        overall_score REAL NULL,
                        technical_score REAL NULL,
                        communication_score REAL NULL,
                        confidence_score REAL NULL,
                        problem_solving_score REAL NULL,
                        relevance_score REAL NULL,
                        completed_at TIMESTAMP NULL
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_interview_history_interview_id ON InterviewHistory (interview_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_interview_history_user_id ON InterviewHistory (user_id)")
                cursor.execute("ALTER TABLE Feedback ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NOT NULL DEFAULT NOW()")
                try:
                    cursor.execute("""
                        INSERT INTO InterviewHistory (interview_id, user_id, role, attempt_number, overall_score, technical_score, communication_score, confidence_score, problem_solving_score, relevance_score, completed_at)
                        SELECT i.id, i.user_id, i.role, 1, i.overall_score, i.technical_score, i.communication_score, i.confidence_score, i.problem_solving_score, i.relevance_score, i.completed_at
                        FROM Interviews i
                        WHERE NOT EXISTS (SELECT 1 FROM InterviewHistory h WHERE h.interview_id = i.id)
                    """)
                except Exception as bf_err:
                    print(f"[Startup Migration Notice] InterviewHistory backfill notice: {bf_err}")
                connection.commit()
                print("[Startup Migration] Verified InterviewHistory and Feedback tables in PostgreSQL.")
            elif DB_ENGINE == "sqlite":
                for col, typ in [("termination_type", "TEXT"), ("security_violation", "INTEGER"), ("terminated_at", "TEXT")]:
                    try:
                        cursor.execute(f"ALTER TABLE Interviews ADD COLUMN {col} {typ} NULL")
                        connection.commit()
                    except Exception:
                        pass
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS InterviewHistory (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        interview_id INTEGER NOT NULL,
                        user_id INTEGER,
                        role TEXT,
                        attempt_number INTEGER DEFAULT 1,
                        overall_score REAL,
                        technical_score REAL,
                        communication_score REAL,
                        confidence_score REAL,
                        problem_solving_score REAL,
                        relevance_score REAL,
                        completed_at TEXT
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_interview_history_interview_id ON InterviewHistory (interview_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_interview_history_user_id ON InterviewHistory (user_id)")
                try:
                    cursor.execute("ALTER TABLE Feedback ADD COLUMN created_at TEXT NOT NULL DEFAULT (datetime('now'))")
                except Exception:
                    pass
                connection.commit()
            else:
                cursor.execute("""
                    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Interviews' AND COLUMN_NAME = 'termination_type')
                        ALTER TABLE Interviews ADD termination_type NVARCHAR(50) NULL;
                    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Interviews' AND COLUMN_NAME = 'security_violation')
                        ALTER TABLE Interviews ADD security_violation BIT NULL;
                    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Interviews' AND COLUMN_NAME = 'terminated_at')
                        ALTER TABLE Interviews ADD terminated_at DATETIME2 NULL;
                    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'InterviewHistory')
                    BEGIN
                        CREATE TABLE InterviewHistory (
                            id INT IDENTITY(1,1) PRIMARY KEY,
                            interview_id INT NOT NULL,
                            user_id INT NULL,
                            role NVARCHAR(100) NULL,
                            attempt_number INT NULL,
                            overall_score FLOAT NULL,
                            technical_score FLOAT NULL,
                            communication_score FLOAT NULL,
                            confidence_score FLOAT NULL,
                            problem_solving_score FLOAT NULL,
                            relevance_score FLOAT NULL,
                            completed_at DATETIME2 NULL
                        );
                        CREATE INDEX idx_interview_history_interview_id ON InterviewHistory (interview_id);
                        CREATE INDEX idx_interview_history_user_id ON InterviewHistory (user_id);
                    END
                """)
                connection.commit()
        except Exception as mig_err:
            print(f"[Startup Migration Notice] {mig_err}")
        finally:
            cursor.close()
            connection.close()

        # Safe SMTP Configuration Diagnostic
        try:
            print_smtp_diagnostic()
        except Exception as smtp_diag_err:
            print(f"[SMTP Diagnostic Warning] {smtp_diag_err}")

        # Initialize Admin Schema extensions (Users.is_active, AdminAuditLogs, etc.)
        try:
            init_admin_schema()
        except Exception as schema_err:
            print(f"[Admin Schema Warning] {schema_err}")
    except Exception as exc:
        print(f"[Startup Auth Warning] {exc}")


@app.on_event("startup")
def startup_auth_init():
    """
    Non-blocking startup initialization. Launches background verification thread so
    Uvicorn binds to 0.0.0.0:$PORT immediately, preventing cloud port scan timeouts.
    """
    import threading
    threading.Thread(target=_run_background_startup_auth, daemon=True, name="StartupAuthThread").start()


# =========================================
# AUTHENTICATION & AUTHORIZATION DEPENDENCIES
# =========================================

def get_user_from_auth(
    authorization: Optional[str] = None,
    token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validates token from either Authorization Bearer header or query parameter against UserTokens table.
    Returns authenticated user information.
    """
    raw_token = None
    if authorization and authorization.startswith("Bearer "):
        raw_token = authorization.split("Bearer ", 1)[1].strip()
    elif token and str(token).strip():
        raw_token = str(token).strip()

    if not raw_token:
        raise HTTPException(
            status_code=401,
            detail="Authentication token required. Please log in."
        )

    tok_hash = hash_token(raw_token)

    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            SELECT u.id, u.name, u.email, u.is_admin, u.preferred_role, t.expires_at, t.is_active, t.id, u.created_at
            FROM UserTokens t
            JOIN Users u ON t.user_id = u.id
            WHERE t.token_hash = ? AND t.is_active = 1
        """, (tok_hash,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=401,
                detail="Session expired or invalid. Please log in again."
            )

        token_id = row[7]
        expires_at = row[5]

        # Check expiration against current UTC (handles both aware and naive timestamps)
        if expires_at:
            from datetime import timezone
            now_utc = datetime.now(timezone.utc) if getattr(expires_at, "tzinfo", None) is not None else datetime.utcnow()
            if expires_at < now_utc:
                cursor.execute("UPDATE UserTokens SET is_active = 0 WHERE id = ?", (token_id,))
                connection.commit()
                raise HTTPException(
                    status_code=401,
                    detail="Your session has expired. Please log in again."
                )

        created_dt = row[8]
        member_since_str = created_dt.strftime("%d %b %Y") if created_dt else "Recent"
        created_iso = created_dt.isoformat() if created_dt else None

        return {
            "id": row[0],
            "name": row[1],
            "email": row[2],
            "is_admin": bool(row[3]),
            "role": row[4] or "User",
            "preferred_role": row[4] or "User",
            "account_type": "Administrator" if row[3] else "User",
            "member_since": member_since_str,
            "created_at": created_iso
        }
    finally:
        cursor.close()
        connection.close()


def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Validates Bearer token from UserTokens table.
    Returns authenticated user information without sensitive password hashes.
    """
    return get_user_from_auth(authorization=authorization)


def get_current_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Role-based authorization guard.
    Requires current authenticated user to have is_admin = True.
    """
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=403,
            detail="Access forbidden: Administrator privileges required."
        )
    return current_user


# =========================================
# AUTHENTICATION API ENDPOINTS
# =========================================

@app.post("/api/auth/register")
def register(req: RegisterRequest):
    """
    Registers a new candidate user with rigorous password rule validation,
    email normalization, uniqueness checking, and PBKDF2 hashing.
    """
    clean_name = req.name.strip()
    if not clean_name:
        raise HTTPException(status_code=422, detail="Name is required.")

    clean_email = normalize_email(req.email)
    valid_em, em_err = validate_email(clean_email)
    if not valid_em:
        raise HTTPException(status_code=422, detail=em_err)

    valid_pwd, pwd_err = validate_password(req.password)
    if not valid_pwd:
        raise HTTPException(status_code=422, detail=pwd_err)

    connection = get_connection()
    cursor = connection.cursor()
    try:
        # Check duplicate email
        cursor.execute("SELECT id FROM Users WHERE LOWER(email) = ?", (clean_email,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=409,
                detail="An account with this email address already exists. Please log in or reset your password."
            )

        # Hash password securely
        pwd_hash = hash_password(req.password)
        pref_role = req.preferred_role or req.role or "User"

        cursor.execute("""
            INSERT INTO Users (name, email, password_hash, is_admin, preferred_role, created_at)
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, 0, ?, GETUTCDATE())
        """, (clean_name, clean_email, pwd_hash, pref_role))
        user_row = cursor.fetchone()
        user_id = user_row[0]

        # Generate session token (7-day duration)
        raw_token = generate_secure_token(32)
        tok_hash = hash_token(raw_token)
        cursor.execute("""
            INSERT INTO UserTokens (user_id, token_hash, created_at, expires_at, is_active)
            VALUES (?, ?, GETUTCDATE(), DATEADD(day, 7, GETUTCDATE()), 1)
        """, (user_id, tok_hash))

        connection.commit()

        return {
            "status": "success",
            "message": "Registration successful.",
            "token": raw_token,
            "user": {
                "id": user_id,
                "name": clean_name,
                "email": clean_email,
                "is_admin": False,
                "preferred_role": pref_role
            }
        }
    except HTTPException:
        raise
    except Exception as exc:
        print(f"[Auth Error] Registration failed for email '{clean_email}': {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during registration. Please try again."
        )
    finally:
        cursor.close()
        connection.close()


@app.post("/api/auth/login")
def login(req: LoginRequest):
    """
    Authenticates a user via email and password with role validation.
    Issues a cryptographically secure session token.
    """
    clean_email = normalize_email(req.email)
    if not clean_email or not req.password:
        raise HTTPException(status_code=400, detail="Email and password are required.")

    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            SELECT id, name, email, password_hash, is_admin, preferred_role
            FROM Users
            WHERE LOWER(email) = ?
        """, (clean_email,))
        row = cursor.fetchone()

        if not row or not verify_password(req.password, row[3]):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password. Please check your credentials."
            )

        user_id = row[0]
        user_name = row[1]
        user_email = row[2]
        is_admin = bool(row[4])
        pref_role = row[5]

        # Check account active status if column exists
        try:
            cursor.execute("SELECT is_active FROM Users WHERE id = ?", (user_id,))
            act_row = cursor.fetchone()
            if act_row and act_row[0] is not None and int(act_row[0]) == 0:
                raise HTTPException(
                    status_code=403,
                    detail="Your account has been deactivated. Please contact the administrator."
                )
        except HTTPException:
            raise
        except Exception:
            pass

        # Role enforcement if requested as Admin
        if req.role and req.role.strip().lower() == "admin" and not is_admin:
            raise HTTPException(
                status_code=403,
                detail="Access denied: This account does not possess administrator privileges."
            )

        # Issue new active session token
        raw_token = generate_secure_token(32)
        tok_hash = hash_token(raw_token)
        cursor.execute("""
            INSERT INTO UserTokens (user_id, token_hash, created_at, expires_at, is_active)
            VALUES (?, ?, GETUTCDATE(), DATEADD(day, 7, GETUTCDATE()), 1)
        """, (user_id, tok_hash))
        connection.commit()

        return {
            "status": "success",
            "message": "Login successful.",
            "token": raw_token,
            "user": {
                "id": user_id,
                "name": user_name,
                "email": user_email,
                "is_admin": is_admin,
                "preferred_role": pref_role
            }
        }
    except HTTPException:
        raise
    except Exception as exc:
        print(f"[Auth Error] Login failed for email '{clean_email}': {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during authentication. Please try again."
        )
    finally:
        cursor.close()
        connection.close()


@app.post("/api/auth/logout")
def logout(authorization: Optional[str] = Header(None)):
    """Logs out user by invalidating the current Bearer token."""
    if authorization and authorization.startswith("Bearer "):
        raw_token = authorization.split("Bearer ", 1)[1].strip()
        tok_hash = hash_token(raw_token)
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("UPDATE UserTokens SET is_active = 0 WHERE token_hash = ?", (tok_hash,))
            connection.commit()
        finally:
            cursor.close()
            connection.close()

    return {"status": "success", "message": "Logged out successfully."}


@app.get("/api/auth/me")
def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Returns currently authenticated user profile without sensitive data."""
    return {
        "status": "success",
        "user": current_user
    }


@app.get("/api/dashboard/profile")
def get_dashboard_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Returns authenticated user profile details including admin status."""
    return {
        "status": "success",
        "user": current_user
    }


@app.get("/api/profile")
def get_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Returns currently authenticated user's profile details."""
    return {
        "status": "success",
        "user": {
            "id": current_user["id"],
            "name": current_user["name"],
            "email": current_user["email"],
            "is_admin": current_user.get("is_admin", False),
            "role": current_user.get("role") or current_user.get("preferred_role") or "User",
            "preferred_role": current_user.get("preferred_role") or current_user.get("role") or "User",
            "account_type": current_user.get("account_type", "User"),
            "member_since": current_user.get("member_since", "Recent"),
            "created_at": current_user.get("created_at")
        }
    }


@app.get("/api/roles")
def get_roles():
    """Returns list of supported interview roles for role selection."""
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT id, role_name, slug, description FROM Roles ORDER BY id ASC")
        rows = cursor.fetchall()
        roles = []
        for r in rows:
            roles.append({
                "id": r[0],
                "name": r[1],
                "slug": r[2],
                "description": r[3]
            })
        return {"status": "success", "roles": roles}
    finally:
        cursor.close()
        connection.close()


@app.put("/api/profile")
def update_profile(
    req: ProfileUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Updates the authenticated user's editable profile fields: Full Name and Interview Role.
    - Security: Authenticated session token strictly identifies user (frontend user_id ignored).
    - Validation: Full Name is required, trimmed, non-empty.
    - Validation: Interview Role is required and must match supported roles.
    - Read-only fields: Email, Account Type, Member Since remain untouched.
    - Mobile Number: NOT required, validated, or updated.
    - Data Integrity: Past/historical interview records remain completely untouched.
    """
    user_id = current_user["id"]

    # 1. Full Name validation
    name_val = (req.name or "").strip()
    if not name_val:
        raise HTTPException(
            status_code=400,
            detail="Full Name is required and cannot be empty."
        )
    if len(name_val) > 100:
        raise HTTPException(
            status_code=400,
            detail="Full Name cannot exceed 100 characters."
        )

    # 2. Interview Role validation
    role_val = (req.role or req.preferred_role or "").strip()
    if not role_val:
        raise HTTPException(
            status_code=400,
            detail="Interview Role is required."
        )

    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT role_name FROM Roles")
        db_roles = [r[0] for r in cursor.fetchall()]
        supported_roles = db_roles if db_roles else ["Java Developer", "Python Developer", "Data Analyst", "Web Developer"]

        canonical_role = next(
            (r for r in supported_roles if r.lower() == role_val.lower()),
            None
        )
        if not canonical_role:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid interview role '{role_val}'. Supported roles are: {', '.join(supported_roles)}."
            )

        # 3. Update ONLY Users table for current user
        cursor.execute("""
            UPDATE Users
            SET name = ?, preferred_role = ?
            WHERE id = ?
        """, (name_val, canonical_role, user_id))
        connection.commit()

        # Fetch updated record
        cursor.execute("""
            SELECT id, name, email, is_admin, preferred_role, created_at
            FROM Users
            WHERE id = ?
        """, (user_id,))
        updated_row = cursor.fetchone()

        created_dt = updated_row[5] if updated_row else None
        member_since_str = created_dt.strftime("%d %b %Y") if created_dt else "Recent"
        created_iso = created_dt.isoformat() if created_dt else None

        updated_user = {
            "id": user_id,
            "name": updated_row[1] if updated_row else name_val,
            "email": updated_row[2] if updated_row else current_user["email"],
            "role": canonical_role,
            "preferred_role": canonical_role,
            "account_type": "Administrator" if (updated_row and updated_row[3]) else "User",
            "member_since": member_since_str,
            "created_at": created_iso
        }

        return {
            "status": "success",
            "message": "Profile updated successfully.",
            "user": updated_user
        }
    finally:
        cursor.close()
        connection.close()


# =========================================
# CANDIDATE DASHBOARD SUMMARY API
# =========================================

def safe_parse_json_list(val) -> List[str]:
    """Helper to safely parse strengths, weaknesses, or recommendations stored as JSON or string."""
    if not val:
        return []
    if isinstance(val, list):
        return [str(x).strip() for x in val if str(x).strip()]
    val_str = str(val).strip()
    if not val_str:
        return []
    try:
        parsed = json.loads(val_str)
        if isinstance(parsed, list):
            res = []
            for item in parsed:
                if isinstance(item, str) and item.strip():
                    res.append(item.strip())
                elif isinstance(item, dict):
                    text = item.get("text") or item.get("feedback") or item.get("point")
                    if text:
                        res.append(str(text).strip())
            return res
        if isinstance(parsed, str) and parsed.strip():
            return [parsed.strip()]
    except Exception:
        pass
    lines = [line.strip().lstrip("-*•0123456789. ") for line in val_str.splitlines() if line.strip()]
    return [l for l in lines if len(l) > 3]


@app.get("/api/dashboard/summary")
def get_dashboard_summary(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Returns comprehensive, secure, real-time dashboard progress analytics
    for the currently authenticated candidate user.
    """
    user_id = current_user["id"]
    connection = get_connection()
    cursor = connection.cursor()
    try:
        # Fetch all interviews for this specific user in chronological order
        cursor.execute("""
            SELECT i.id, i.role, i.overall_score, i.technical_score, i.communication_score,
                   i.confidence_score, i.problem_solving_score, i.relevance_score,
                   i.status, i.created_at, i.completed_at, i.total_questions,
                   e.strengths, e.weaknesses, e.recommendations,
                   f.strengths, f.areas_to_improve
            FROM Interviews i
            LEFT JOIN EvaluationResults e ON i.id = e.interview_id
            LEFT JOIN Feedback f ON i.id = f.interview_id
            WHERE i.user_id = ?
            ORDER BY i.created_at ASC, i.id ASC
        """, (user_id,))
        rows = cursor.fetchall()

        total_interviews = len(rows)

        # Base empty response structure if user has zero interviews
        if total_interviews == 0:
            return {
                "status": "success",
                "user": {
                    "id": current_user["id"],
                    "name": current_user["name"],
                    "email": current_user["email"],
                    "is_admin": current_user.get("is_admin", False),
                    "preferred_role": current_user.get("preferred_role")
                },
                "total_interviews": 0,
                "average_score": 0.0,
                "best_score": 0.0,
                "latest_score": 0.0,
                "monthly_interviews": 0,
                "score_history": [],
                "score_progression": [],
                "skill_performance": [
                    {"dimension": "technical", "label": "Technical Knowledge", "score": None, "available": False, "icon": "fa-code"},
                    {"dimension": "communication", "label": "Communication", "score": None, "available": False, "icon": "fa-comments"},
                    {"dimension": "problem_solving", "label": "Problem Solving", "score": None, "available": False, "icon": "fa-lightbulb"},
                    {"dimension": "confidence", "label": "Confidence", "score": None, "available": False, "icon": "fa-user-check"},
                    {"dimension": "relevance", "label": "Answer Relevance", "score": None, "available": False, "icon": "fa-bullseye"}
                ],
                "role_performance": [],
                "strengths": [],
                "improvements": [],
                "latest_interview": None,
                "progress_comparison": {
                    "text": "Start your first mock interview to track your progress.",
                    "improvement_pct": 0.0,
                    "has_improvement": False,
                    "previous_score": None,
                    "latest_score": None
                },
                "achievements": [
                    {"id": "first_interview", "title": "First Step", "desc": "Complete your first mock interview", "unlocked": False, "progress": 0, "target": 1, "icon": "fa-flag"},
                    {"id": "interviews_5", "title": "Practice Pro", "desc": "Complete 5 mock interviews", "unlocked": False, "progress": 0, "target": 5, "icon": "fa-fire"},
                    {"id": "interviews_10", "title": "Interview Veteran", "desc": "Complete 10 mock interviews", "unlocked": False, "progress": 0, "target": 10, "icon": "fa-medal"},
                    {"id": "score_70", "title": "High Scorer", "desc": "Score 70% or higher in an interview", "unlocked": False, "progress": 0, "target": 70, "icon": "fa-star"},
                    {"id": "score_85", "title": "Mastery", "desc": "Score 85% or higher in an interview", "unlocked": False, "progress": 0, "target": 85, "icon": "fa-trophy"},
                    {"id": "improvement", "title": "Rising Star", "desc": "Improve your score between interviews", "unlocked": False, "progress": 0, "target": 1, "icon": "fa-chart-line"},
                    {"id": "multi_role", "title": "Multi-Role Explorer", "desc": "Practice interviews for 2+ different roles", "unlocked": False, "progress": 0, "target": 2, "icon": "fa-compass"}
                ],
                "history": []
            }

        now = datetime.utcnow()
        scores = []
        tech_scores = []
        comm_scores = []
        conf_scores = []
        ps_scores = []
        rel_scores = []

        score_history = []
        roles_dict = {}
        monthly_count = 0
        all_strengths = []
        all_improvements = []

        for idx, r in enumerate(rows, 1):
            int_id = r[0]
            role = r[1] or "General"
            raw_ov = r[2]
            status = r[8] or "Completed"
            is_term = str(status).lower() == "terminated"

            date_obj = r[10] or r[9]
            if date_obj and date_obj.year == now.year and date_obj.month == now.month:
                monthly_count += 1

            date_str = date_obj.strftime("%d %b %Y") if date_obj else f"Interview #{int_id}"

            # Strict policy: Terminated interviews have NO valid AI evaluation score.
            # Do NOT include in average score, best score, progression chart, role averages, or skill averages.
            if not is_term and raw_ov is not None:
                ov_score = round(float(raw_ov), 1)
                scores.append(ov_score)
                t_score = round(float(r[3]), 1) if r[3] is not None else None
                c_score = round(float(r[4]), 1) if r[4] is not None else None
                conf_score = round(float(r[5]), 1) if r[5] is not None else None
                ps_score = round(float(r[6]), 1) if r[6] is not None else None
                rel_score = round(float(r[7]), 1) if r[7] is not None else None

                if t_score is not None and t_score > 0: tech_scores.append(t_score)
                if c_score is not None and c_score > 0: comm_scores.append(c_score)
                if conf_score is not None and conf_score > 0: conf_scores.append(conf_score)
                if ps_score is not None and ps_score > 0: ps_scores.append(ps_score)
                if rel_score is not None and rel_score > 0: rel_scores.append(rel_score)

                score_history.append({
                    "index": len(scores),
                    "interview_id": int_id,
                    "role": role,
                    "score": ov_score,
                    "date": date_str
                })

                if role not in roles_dict:
                    roles_dict[role] = {"scores": [], "count": 0, "latest": ov_score}
                roles_dict[role]["scores"].append(ov_score)
                roles_dict[role]["count"] += 1
                roles_dict[role]["latest"] = ov_score

                # Parse feedback items
                e_str = r[12]
                e_weak = r[13]
                e_rec = r[14]
                f_str = r[15]
                f_imp = r[16]

                for s in safe_parse_json_list(e_str) + safe_parse_json_list(f_str):
                    clean_s = s.strip()
                    if clean_s and clean_s not in all_strengths:
                        all_strengths.append(clean_s)

                for imp in safe_parse_json_list(e_weak) + safe_parse_json_list(f_imp) + safe_parse_json_list(e_rec):
                    clean_imp = imp.strip()
                    if clean_imp and clean_imp not in all_improvements:
                        all_improvements.append(clean_imp)

        avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
        best_score = round(max(scores), 1) if scores else 0.0
        latest_score = round(scores[-1], 1) if scores else 0.0

        # Skills breakdown
        skill_performance = [
            {
                "dimension": "technical",
                "label": "Technical Knowledge",
                "score": round(sum(tech_scores) / len(tech_scores), 1) if tech_scores else None,
                "available": bool(tech_scores),
                "icon": "fa-code"
            },
            {
                "dimension": "communication",
                "label": "Communication",
                "score": round(sum(comm_scores) / len(comm_scores), 1) if comm_scores else None,
                "available": bool(comm_scores),
                "icon": "fa-comments"
            },
            {
                "dimension": "problem_solving",
                "label": "Problem Solving",
                "score": round(sum(ps_scores) / len(ps_scores), 1) if ps_scores else None,
                "available": bool(ps_scores),
                "icon": "fa-lightbulb"
            },
            {
                "dimension": "confidence",
                "label": "Confidence",
                "score": round(sum(conf_scores) / len(conf_scores), 1) if conf_scores else None,
                "available": bool(conf_scores),
                "icon": "fa-user-check"
            },
            {
                "dimension": "relevance",
                "label": "Answer Relevance",
                "score": round(sum(rel_scores) / len(rel_scores), 1) if rel_scores else None,
                "available": bool(rel_scores),
                "icon": "fa-bullseye"
            }
        ]

        # Role performance
        role_performance = []
        for r_name, r_data in roles_dict.items():
            r_scores = r_data["scores"]
            role_performance.append({
                "role": r_name,
                "count": r_data["count"],
                "average_score": round(sum(r_scores) / len(r_scores), 1) if r_scores else 0.0,
                "best_score": round(max(r_scores), 1) if r_scores else 0.0,
                "latest_score": round(r_data["latest"], 1)
            })
        role_performance.sort(key=lambda x: x["count"], reverse=True)

        # Progress comparison
        previous_score = None
        improvement_pct = 0.0
        has_improvement = False
        comparison_text = ""

        if len(scores) >= 2:
            previous_score = scores[-2]
            improvement_pct = round(latest_score - previous_score, 1)
            has_improvement = improvement_pct > 0
            if improvement_pct > 0:
                comparison_text = f"Your score improved from {previous_score:.0f}% to {latest_score:.0f}% across your recent interviews (+{improvement_pct:.1f}%)."
            elif improvement_pct < 0:
                comparison_text = f"Your score changed from {previous_score:.0f}% to {latest_score:.0f}% in your latest interview ({improvement_pct:+.1f}%)."
            else:
                comparison_text = f"Your score remained steady at {latest_score:.0f}% in your latest interview."
        elif len(scores) == 1:
            comparison_text = f"You completed your first interview with a score of {latest_score:.0f}%. Keep practicing to build momentum!"
        else:
            comparison_text = "Start your first mock interview to track your progress."

        # Latest interview card data
        last_row = rows[-1]
        last_date_obj = last_row[10] or last_row[9]
        last_st = last_row[8] or "Completed"
        last_is_term = str(last_st).lower() == "terminated"

        latest_interview = {
            "id": last_row[0],
            "role": last_row[1] or "General",
            "overall_score": None if (last_is_term or last_row[2] is None) else round(float(last_row[2]), 1),
            "date": last_date_obj.strftime("%d %b %Y") if last_date_obj else "Recent",
            "total_questions": last_row[11] or 0,
            "status": "Terminated" if last_is_term else "Completed",
            "comparison": "Terminated session" if last_is_term else (
                f"+{improvement_pct:.1f}% vs previous" if improvement_pct > 0
                else (f"{improvement_pct:.1f}% vs previous" if improvement_pct < 0 else ("First interview" if len(scores) == 1 else "Same as previous"))
            ),
            "report_url": f"result.html?id={last_row[0]}"
        }

        # Achievements
        any_improvement = any(scores[i] > scores[i-1] for i in range(1, len(scores))) if len(scores) >= 2 else False
        achievements = [
            {
                "id": "first_interview",
                "title": "First Step",
                "desc": "Complete your first mock interview",
                "unlocked": total_interviews >= 1,
                "progress": min(total_interviews, 1),
                "target": 1,
                "icon": "fa-flag"
            },
            {
                "id": "interviews_5",
                "title": "Practice Pro",
                "desc": "Complete 5 mock interviews",
                "unlocked": total_interviews >= 5,
                "progress": min(total_interviews, 5),
                "target": 5,
                "icon": "fa-fire"
            },
            {
                "id": "interviews_10",
                "title": "Interview Veteran",
                "desc": "Complete 10 mock interviews",
                "unlocked": total_interviews >= 10,
                "progress": min(total_interviews, 10),
                "target": 10,
                "icon": "fa-medal"
            },
            {
                "id": "score_70",
                "title": "High Scorer",
                "desc": "Score 70% or higher in an interview",
                "unlocked": best_score >= 70,
                "progress": min(best_score, 70),
                "target": 70,
                "icon": "fa-star"
            },
            {
                "id": "score_85",
                "title": "Mastery",
                "desc": "Score 85% or higher in an interview",
                "unlocked": best_score >= 85,
                "progress": min(best_score, 85),
                "target": 85,
                "icon": "fa-trophy"
            },
            {
                "id": "improvement",
                "title": "Rising Star",
                "desc": "Show score improvement between interviews",
                "unlocked": any_improvement,
                "progress": 1 if any_improvement else 0,
                "target": 1,
                "icon": "fa-chart-line"
            },
            {
                "id": "multi_role",
                "title": "Multi-Role Explorer",
                "desc": "Practice interviews for 2+ different roles",
                "unlocked": len(roles_dict) >= 2,
                "progress": min(len(roles_dict), 2),
                "target": 2,
                "icon": "fa-compass"
            }
        ]

        # History list (newest first)
        history = []
        for r in reversed(rows):
            d_obj = r[10] or r[9]
            st = r[8] or "Completed"
            is_term = str(st).lower() == "terminated"
            raw_s = r[2]

            if is_term or raw_s is None:
                s_val = None
                perf_label = "Terminated"
                perf_class = "perf-terminated"
            else:
                s_val = round(float(raw_s), 1)
                if s_val >= 80:
                    perf_label = "Excellent"
                    perf_class = "perf-excellent"
                elif s_val >= 65:
                    perf_label = "Good"
                    perf_class = "perf-good"
                elif s_val >= 50:
                    perf_label = "Average"
                    perf_class = "perf-average"
                else:
                    perf_label = "Needs Improvement"
                    perf_class = "perf-needs-imp"

            history.append({
                "id": r[0],
                "role": r[1] or "General",
                "overall_score": s_val,
                "date": d_obj.strftime("%d %b %Y") if d_obj else "Completed",
                "status": "Terminated" if is_term else "Completed",
                "performance_label": perf_label,
                "performance_class": perf_class,
                "total_questions": r[11] or 0,
                "report_url": f"result.html?id={r[0]}"
            })

        return {
            "status": "success",
            "user": {
                "id": current_user["id"],
                "name": current_user["name"],
                "email": current_user["email"],
                "is_admin": current_user.get("is_admin", False),
                "preferred_role": current_user.get("preferred_role")
            },
            "total_interviews": total_interviews,
            "average_score": avg_score,
            "best_score": best_score,
            "latest_score": latest_score,
            "monthly_interviews": monthly_count,
            "score_history": score_history,
            "score_progression": score_history,
            "skill_performance": skill_performance,
            "role_performance": role_performance,
            "strengths": all_strengths[:5],
            "improvements": all_improvements[:5],
            "latest_interview": latest_interview,
            "progress_comparison": {
                "text": comparison_text,
                "improvement_pct": improvement_pct,
                "has_improvement": has_improvement,
                "previous_score": previous_score,
                "latest_score": latest_score
            },
            "achievements": achievements,
            "history": history
        }
    finally:
        cursor.close()
        connection.close()


@app.post("/api/auth/change-password")
def change_password(req: ChangePasswordRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Allows authenticated user to change their password with current password verification
    and strict rule validation on the new password.
    """
    if req.new_password != req.confirm_password:
        raise HTTPException(status_code=422, detail="New password and confirm password do not match.")

    if req.current_password == req.new_password:
        raise HTTPException(status_code=422, detail="New password cannot be identical to your current password.")

    valid_pwd, pwd_err = validate_password(req.new_password)
    if not valid_pwd:
        raise HTTPException(status_code=422, detail=pwd_err)

    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT password_hash FROM Users WHERE id = ?", (current_user["id"],))
        row = cursor.fetchone()
        if not row or not verify_password(req.current_password, row[0]):
            raise HTTPException(status_code=400, detail="Current password entered is incorrect.")

        new_hash = hash_password(req.new_password)
        cursor.execute("UPDATE Users SET password_hash = ? WHERE id = ?", (new_hash, current_user["id"]))
        connection.commit()

        return {
            "status": "success",
            "message": "Password updated successfully."
        }
    finally:
        cursor.close()
        connection.close()


def is_production_environment(request: Optional[Request] = None) -> bool:
    """
    Returns True if running in production or cloud deployment (Render, Vercel).
    In production mode, sensitive tokens, reset links, and dev notices are NEVER exposed.
    """
    env = os.getenv("ENV", os.getenv("APP_ENV", os.getenv("ENVIRONMENT", ""))).lower().strip()
    if env in ("production", "prod", "staging"):
        return True
    if os.getenv("RENDER") or os.getenv("VERCEL"):
        return True
    if request:
        for hdr_name in ("origin", "referer", "x-forwarded-host", "host"):
            hdr_val = request.headers.get(hdr_name)
            if hdr_val:
                host_only = hdr_val.lower().replace("https://", "").replace("http://", "").split("/")[0].split(":")[0]
                if host_only and host_only not in ("127.0.0.1", "localhost", "0.0.0.0", "testserver", "[::1]"):
                    return True
    if env in ("development", "dev", "local", "test"):
        return False
    return False


def is_token_expired(expires_at: Any) -> bool:
    """
    Safely verifies whether a token expiration timestamp is in the past across
    naive datetime, timezone-aware datetime (UTC), and ISO string formats.
    """
    if expires_at is None:
        return True
    if isinstance(expires_at, str):
        try:
            clean = expires_at.replace("T", " ")[:19]
            expires_at = datetime.strptime(clean, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return True
    if isinstance(expires_at, datetime):
        if expires_at.tzinfo is not None:
            return expires_at < datetime.now(timezone.utc)
        return expires_at < datetime.now(timezone.utc).replace(tzinfo=None)
    return False


def resolve_app_base_url(request: Optional[Request] = None) -> str:
    """
    Dynamically resolves the application base URL for generating password reset links.
    Priority order:
    1. If request is provided, inspect Origin or Referer header (from frontend Vercel app or public domain).
    2. Check APP_BASE_URL environment variable (configured for Vercel frontend or public custom domain).
    3. Check X-Forwarded-Host or Host header from request.
    4. Fallback to http://127.0.0.1:8000 for local development and test suites.
    """
    from urllib.parse import urlparse

    def _extract_external_base(raw_val: Optional[str], default_proto: str = "https") -> Optional[str]:
        if not raw_val:
            return None
        raw = raw_val.strip()
        try:
            if "://" in raw:
                parsed = urlparse(raw)
                proto = parsed.scheme.lower()
                netloc = parsed.netloc.strip()
            else:
                proto = default_proto
                netloc = raw

            host_only = netloc.split(":")[0].strip().lower()
            if host_only and host_only not in ("127.0.0.1", "localhost", "0.0.0.0", "testserver", "[::1]"):
                if "trycloudflare.com" in host_only or proto == "https":
                    proto = "https"
                return f"{proto}://{netloc}".rstrip("/")
        except Exception:
            pass
        return None

    # 1. Dynamically inspect incoming Origin or Referer (sent by browser on Vercel frontend)
    if request:
        try:
            origin_hdr = request.headers.get("origin")
            ext = _extract_external_base(origin_hdr)
            if ext:
                return ext

            referer_hdr = request.headers.get("referer")
            ext = _extract_external_base(referer_hdr)
            if ext:
                return ext
        except Exception as e:
            print(f"[Base URL Resolution Notice] Error inspecting request origin/referer: {e}")

    # 2. Inspect APP_BASE_URL from environment
    env_base = os.getenv("APP_BASE_URL", "").strip().rstrip("/")
    if not env_base:
        try:
            load_env(override=False)
            env_base = os.getenv("APP_BASE_URL", "").strip().rstrip("/")
        except Exception:
            pass
    if env_base:
        ext = _extract_external_base(env_base)
        if ext:
            return ext
        # If set to local address (e.g. http://localhost:8000), use it for intentional local testing
        return env_base

    # 3. Check X-Forwarded-Host and Host headers
    if request:
        try:
            fwd_host = (request.headers.get("x-forwarded-host") or "").strip()
            fwd_proto = (request.headers.get("x-forwarded-proto") or "").strip().lower()
            if fwd_host:
                proto = fwd_proto or ("https" if "trycloudflare.com" in fwd_host.lower() else "http")
                ext = _extract_external_base(fwd_host, default_proto=proto)
                if ext:
                    return ext

            host_hdr = (request.headers.get("host") or "").strip()
            if host_hdr:
                proto = "https" if ("trycloudflare.com" in host_hdr.lower() or request.url.scheme == "https") else request.url.scheme
                ext = _extract_external_base(host_hdr, default_proto=proto)
                if ext:
                    return ext
        except Exception as e:
            print(f"[Base URL Resolution Notice] Error inspecting request host headers: {e}")

    # 4. Fallback to 127.0.0.1:8000 for local development
    return "http://127.0.0.1:8000"


@app.post("/api/auth/forgot-password")
def forgot_password(req: ForgotPasswordRequest, request: Request = None):
    """
    Initiates single-use, 15-minute password reset token flow.
    Provides indistinguishable generic responses to eliminate email enumeration attacks.
    Never exposes reset links, tokens, or credentials in production responses or logs.
    """
    clean_email = normalize_email(req.email)
    is_prod = is_production_environment(request)
    smtp_ok = is_smtp_configured()

    generic_msg = (
        "Password reset link sent successfully. Please check your email inbox and spam folder."
        if smtp_ok
        else (
            "Password reset service is temporarily unavailable. Please contact the administrator."
            if is_prod
            else (
                "If this email address is registered in our system, you will receive single-use "
                "password reset instructions shortly."
            )
        )
    )

    if not clean_email:
        if is_prod and not smtp_ok:
            return {
                "status": "error",
                "delivery_status": "unconfigured",
                "smtp_configured": False,
                "message": "Password reset service is temporarily unavailable. Please contact the administrator."
            }
        return {
            "status": "success",
            "delivery_status": "sent" if smtp_ok else "unconfigured",
            "message": generic_msg,
            "smtp_configured": smtp_ok
        }

    # If SMTP is not configured in production, report error clearly without falsely claiming email was sent
    if is_prod and not smtp_ok:
        missing_vars = get_missing_smtp_vars()
        print(f"[Email Service Error] Password reset requested for '{clean_email}', but SMTP is not configured in production. Missing: {', '.join(missing_vars)}.")
        return {
            "status": "error",
            "delivery_status": "unconfigured",
            "smtp_configured": False,
            "message": "Password reset service is temporarily unavailable. Please contact the administrator to configure SMTP settings."
        }

    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT id, name, email FROM Users WHERE LOWER(email) = ?", (clean_email,))
        user_row = cursor.fetchone()

        if user_row:
            user_id = user_row[0]
            user_name = user_row[1]

            # Invalidate any previously active unused tokens for this user
            cursor.execute("""
                UPDATE PasswordResets
                SET used_at = GETUTCDATE()
                WHERE user_id = ? AND used_at IS NULL
            """, (user_id,))

            # Generate cryptographically secure single-use token (64-char hex)
            raw_token = generate_secure_token(32)
            tok_hash = hash_token(raw_token)

            cursor.execute("""
                INSERT INTO PasswordResets (user_id, token_hash, expires_at, created_at)
                VALUES (?, ?, DATEADD(minute, 15, GETUTCDATE()), GETUTCDATE())
            """, (user_id, tok_hash))
            connection.commit()

            app_base = resolve_app_base_url(request)
            reset_link = f"{app_base}/app/reset_password.html?token={raw_token}"
            email_info = send_password_reset_email(clean_email, user_name, reset_link)

            if email_info.get("sent"):
                return {
                    "status": "success",
                    "delivery_status": "sent",
                    "smtp_configured": True,
                    "message": "Password reset link sent successfully. Please check your email inbox and spam folder."
                }
            elif email_info.get("method") == "smtp_error":
                return {
                    "status": "error",
                    "delivery_status": "smtp_error",
                    "smtp_configured": True,
                    "message": "We couldn't send the reset email. Please try again later.",
                    "smtp_error": "Delivery error" if is_prod else email_info.get("error")
                }
            else:
                # Unconfigured fallback - strictly for local development on localhost
                response_data = {
                    "status": "success",
                    "delivery_status": "unconfigured",
                    "smtp_configured": False,
                    "message": generic_msg
                }
                if not is_prod:
                    response_data["dev_notice"] = "Local Development Fallback: SMTP is not configured. Reset link was logged for offline testing."
                    response_data["reset_link"] = reset_link

                return response_data

        # If user not found (anti-enumeration protection)
        return {
            "status": "success",
            "delivery_status": "sent" if smtp_ok else "unconfigured",
            "message": generic_msg,
            "smtp_configured": smtp_ok
        }
    finally:
        cursor.close()
        connection.close()


@app.get("/api/auth/verify-reset-token")
def verify_reset_token(token: str):
    """
    Validates token existence, expiration (15 mins), and single-use status.
    """
    if not token or not token.strip():
        return {"valid": False, "reason": "No reset token provided."}

    tok_hash = hash_token(token.strip())
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            SELECT r.id, r.user_id, r.expires_at, r.used_at, u.email
            FROM PasswordResets r
            JOIN Users u ON r.user_id = u.id
            WHERE r.token_hash = ?
        """, (tok_hash,))
        row = cursor.fetchone()

        if not row:
            return {"valid": False, "reason": "Password reset link is invalid or does not exist."}

        used_at = row[3]
        if used_at is not None:
            return {
                "valid": False,
                "reason": "This password reset link has already been used. Please request a new one."
            }

        expires_at = row[2]
        if is_token_expired(expires_at):
            return {
                "valid": False,
                "reason": "This password reset link has expired (links are valid for 15 minutes)."
            }

        email_str = row[4]
        parts = email_str.split("@")
        masked = (parts[0][:2] + "***@" + parts[1]) if len(parts) > 1 and len(parts[0]) > 2 else email_str

        return {
            "valid": True,
            "masked_email": masked
        }
    finally:
        cursor.close()
        connection.close()


@app.post("/api/auth/reset-password")
def reset_password(req: ResetPasswordRequest):
    """
    Executes password reset given a valid single-use token, enforcing password rules
    and revoking previous sessions.
    """
    if not req.token or not req.token.strip():
        raise HTTPException(status_code=400, detail="Reset token is required.")

    if req.new_password != req.confirm_password:
        raise HTTPException(status_code=422, detail="Passwords do not match.")

    valid_pwd, pwd_err = validate_password(req.new_password)
    if not valid_pwd:
        raise HTTPException(status_code=422, detail=pwd_err)

    tok_hash = hash_token(req.token.strip())
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            SELECT r.id, r.user_id, r.expires_at, r.used_at
            FROM PasswordResets r
            WHERE r.token_hash = ?
        """, (tok_hash,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=400, detail="Invalid password reset token.")

        reset_id, user_id, expires_at, used_at = row[0], row[1], row[2], row[3]

        if used_at is not None:
            raise HTTPException(
                status_code=400,
                detail="This reset token has already been used. Please request a new reset link."
            )

        if is_token_expired(expires_at):
            raise HTTPException(
                status_code=400,
                detail="This reset link has expired. Please request a new password reset."
            )

        # Mark token as used immediately
        cursor.execute("UPDATE PasswordResets SET used_at = GETUTCDATE() WHERE id = ?", (reset_id,))

        # Update password hash in Users
        new_hash = hash_password(req.new_password)
        cursor.execute("UPDATE Users SET password_hash = ? WHERE id = ?", (new_hash, user_id))

        # Revoke all active sessions for security
        cursor.execute("UPDATE UserTokens SET is_active = 0 WHERE user_id = ?", (user_id,))

        connection.commit()

        return {
            "status": "success",
            "message": "Your password has been successfully reset. You may now log in."
        }
    finally:
        cursor.close()
        connection.close()


# =========================================
# ADMIN API ENDPOINTS (RBAC ENFORCED)
# =========================================

@app.get("/api/admin/overview")
def admin_overview(admin: Dict[str, Any] = Depends(get_current_admin)):
    """
    Returns administrative dashboard summary metrics and statistics.
    Role-based authorization enforced via get_current_admin dependency.
    """
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM Users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Users WHERE is_admin = 1")
        total_admins = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*),
                   COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END),
                   AVG(overall_score)
            FROM Interviews
        """)
        row = cursor.fetchone()
        total_interviews = row[0]
        completed_interviews = row[1]
        avg_score = round(float(row[2]), 2) if row[2] is not None else 0.0

        cursor.execute("""
            SELECT role, COUNT(*) 
            FROM Interviews 
            GROUP BY role 
            ORDER BY COUNT(*) DESC
        """)
        role_breakdown = {r[0]: r[1] for r in cursor.fetchall()}

        cursor.execute("""
            SELECT TOP 6 i.id, i.role, i.overall_score, i.status, i.created_at, u.name, u.email
            FROM Interviews i
            LEFT JOIN Users u ON i.user_id = u.id
            ORDER BY i.id DESC
        """)
        recent_interviews = []
        for r in cursor.fetchall():
            recent_interviews.append({
                "id": r[0],
                "role": r[1],
                "overall_score": round(float(r[2]), 2) if r[2] is not None else 0.0,
                "status": r[3] or "COMPLETED",
                "created_at": r[4].isoformat() if r[4] else None,
                "candidate_name": r[5] or "Candidate",
                "candidate_email": r[6] or "N/A"
            })

        return {
            "status": "success",
            "total_users": total_users,
            "total_admins": total_admins,
            "total_interviews": total_interviews,
            "completed_interviews": completed_interviews,
            "average_score": avg_score,
            "role_breakdown": role_breakdown,
            "recent_interviews": recent_interviews
        }
    finally:
        cursor.close()
        connection.close()


@app.get("/api/admin/users")
def admin_get_users(
    search: Optional[str] = None,
    role: Optional[str] = None,
    account_type: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: Optional[str] = "id",
    order: Optional[str] = "desc",
    admin: Dict[str, Any] = Depends(get_current_admin)
):
    """
    Returns registered users, their interview counts, and average scores.
    Role-based authorization enforced. NEVER returns password hashes.
    Supports filtering by search, role, account_type, status and sorting.
    """
    return get_admin_users_list(
        search=search,
        role=role,
        account_type=account_type,
        status=status,
        sort_by=sort_by,
        order=order
    )


@app.get("/api/admin/users/{user_id}/interviews")
def admin_get_user_interviews(user_id: int, admin: Dict[str, Any] = Depends(get_current_admin)):
    """
    Returns all interviews and evaluation results for a specific user.
    Role-based authorization enforced.
    """
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT id, name, email FROM Users WHERE id = ?", (user_id,))
        user_row = cursor.fetchone()
        if not user_row:
            raise HTTPException(status_code=404, detail="User not found.")

        cursor.execute("""
            SELECT id, role, overall_score, technical_score, communication_score,
                   confidence_score, problem_solving_score, relevance_score,
                   status, created_at, completed_at, total_questions
            FROM Interviews
            WHERE user_id = ?
            ORDER BY id DESC
        """, (user_id,))
        interviews = []
        for r in cursor.fetchall():
            interviews.append({
                "id": r[0],
                "role": r[1],
                "overall_score": round(float(r[2]), 2) if r[2] is not None else 0.0,
                "technical_score": round(float(r[3]), 2) if r[3] is not None else 0.0,
                "communication_score": round(float(r[4]), 2) if r[4] is not None else 0.0,
                "confidence_score": round(float(r[5]), 2) if r[5] is not None else 0.0,
                "problem_solving_score": round(float(r[6]), 2) if r[6] is not None else None,
                "relevance_score": round(float(r[7]), 2) if r[7] is not None else None,
                "status": r[8] or "COMPLETED",
                "created_at": r[9].isoformat() if r[9] else None,
                "completed_at": r[10].isoformat() if r[10] else None,
                "total_questions": r[11] or 0
            })
        return {
            "status": "success",
            "user": {
                "id": user_row[0],
                "name": user_row[1],
                "email": user_row[2]
            },
            "interviews": interviews
        }
    finally:
        cursor.close()
        connection.close()


@app.put("/api/admin/users/{user_id}")
def admin_update_user(user_id: int, req: AdminUserUpdateRequest, admin: Dict[str, Any] = Depends(get_current_admin)):
    """
    Updates user account attributes (name, preferred_role, is_admin).
    Prevents revoking administrator privileges from the sole remaining admin.
    """
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT id, name, email, is_admin, preferred_role FROM Users WHERE id = ?", (user_id,))
        user_row = cursor.fetchone()
        if not user_row:
            raise HTTPException(status_code=404, detail="User not found.")

        # Guard against removing the last administrator
        if req.is_admin is False and user_row[3]:
            cursor.execute("SELECT COUNT(*) FROM Users WHERE is_admin = 1")
            admin_count = cursor.fetchone()[0]
            if admin_count <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot revoke administrator privileges from the sole remaining administrator."
                )

        new_name = req.name.strip() if req.name is not None and req.name.strip() else user_row[1]
        new_role = req.preferred_role.strip() if req.preferred_role is not None else user_row[4]
        new_is_admin = req.is_admin if req.is_admin is not None else user_row[3]

        cursor.execute("""
            UPDATE Users 
            SET name = ?, preferred_role = ?, is_admin = ?
            WHERE id = ?
        """, (new_name, new_role, int(new_is_admin), user_id))
        connection.commit()

        return {
            "status": "success",
            "message": "User updated successfully.",
            "user": {
                "id": user_id,
                "name": new_name,
                "email": user_row[2],
                "preferred_role": new_role,
                "is_admin": bool(new_is_admin)
            }
        }
    finally:
        cursor.close()
        connection.close()


@app.delete("/api/admin/users/{user_id}")
def admin_delete_user(user_id: int, admin: Dict[str, Any] = Depends(get_current_admin)):
    """
    Deletes a user account.
    Prevents self-deletion of the active admin.
    Safely disassociates user_id on existing interviews so historical records are preserved.
    """
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="You cannot delete your own active administrator account.")

    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT id, name, email, is_admin FROM Users WHERE id = ?", (user_id,))
        user_row = cursor.fetchone()
        if not user_row:
            raise HTTPException(status_code=404, detail="User not found.")

        # If user is admin, ensure other admins exist
        if user_row[3]:
            cursor.execute("SELECT COUNT(*) FROM Users WHERE is_admin = 1")
            admin_count = cursor.fetchone()[0]
            if admin_count <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot delete the sole administrator account."
                )

        # Preserve existing interview records by setting user_id = NULL
        cursor.execute("UPDATE Interviews SET user_id = NULL WHERE user_id = ?", (user_id,))

        # Clean up tokens and reset tokens
        cursor.execute("DELETE FROM UserTokens WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM PasswordResets WHERE user_id = ?", (user_id,))

        # Delete user
        cursor.execute("DELETE FROM Users WHERE id = ?", (user_id,))
        connection.commit()

        log_admin_action(
            admin=admin,
            action="USER_DELETED",
            target_type="User",
            target_id=user_id,
            details={"name": user_row[1], "email": user_row[2]}
        )

        return {
            "status": "success",
            "message": f"User '{user_row[1]}' ({user_row[2]}) deleted successfully. All interview history was preserved."
        }
    finally:
        cursor.close()
        connection.close()


# ==================================================
# SUPER ADMIN CONSOLE API ENDPOINTS
# ==================================================

@app.get("/api/admin/dashboard")
def api_admin_dashboard(admin: Dict[str, Any] = Depends(get_current_admin)):
    """Returns real-time Super Admin Command Center metrics and charts data."""
    return get_super_admin_dashboard_metrics()


@app.post("/api/admin/users")
def api_admin_create_user(req: AdminUserCreateRequest, admin: Dict[str, Any] = Depends(get_current_admin)):
    """Admin creates a candidate or administrator user account."""
    try:
        new_u = create_user_by_admin(
            name=req.name,
            email=req.email,
            password=req.password,
            preferred_role=req.preferred_role or "General",
            is_admin=bool(req.is_admin),
            is_active=bool(req.is_active)
        )
        log_admin_action(
            admin=admin,
            action="USER_CREATED",
            target_type="User",
            target_id=new_u["id"],
            details={"name": new_u["name"], "email": new_u["email"], "is_admin": new_u["is_admin"]}
        )
        return {"status": "success", "message": "User created successfully.", "user": new_u}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@app.patch("/api/admin/users/{user_id}/status")
def api_admin_toggle_user_status(user_id: int, req: AdminUserToggleStatusRequest, admin: Dict[str, Any] = Depends(get_current_admin)):
    """Admin activates or deactivates a user account."""
    if user_id == admin["id"] and not req.is_active:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own active administrator account.")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, name, email, is_admin FROM Users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found.")
    finally:
        cur.close()
        conn.close()

    toggle_user_active_status(user_id, req.is_active)
    action_type = "USER_ACTIVATED" if req.is_active else "USER_DEACTIVATED"
    log_admin_action(
        admin=admin,
        action=action_type,
        target_type="User",
        target_id=user_id,
        details={"name": row[1], "email": row[2], "is_active": req.is_active}
    )
    return {
        "status": "success",
        "message": f"User status updated to {'Active' if req.is_active else 'Inactive'}.",
        "is_active": req.is_active
    }


@app.post("/api/admin/users/{user_id}/reset-password")
def api_admin_reset_user_password(user_id: int, req: AdminUserResetPasswordRequest, admin: Dict[str, Any] = Depends(get_current_admin)):
    """Admin resets a user's password with strict password policy verification."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, name, email FROM Users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found.")
    finally:
        cur.close()
        conn.close()

    try:
        admin_reset_user_password(user_id, req.new_password)
        log_admin_action(
            admin=admin,
            action="PASSWORD_RESET_INITIATED",
            target_type="User",
            target_id=user_id,
            details={"user_email": row[2]}
        )
        return {"status": "success", "message": f"Password reset successfully for user '{row[1]}' ({row[2]})."}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@app.get("/api/admin/interviews")
def api_admin_get_interviews(
    search: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    security_violation: Optional[str] = None,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    limit: int = 150,
    admin: Dict[str, Any] = Depends(get_current_admin)
):
    """Admin retrieves all interviews system-wide with search and filtering."""
    return get_admin_interviews_list(
        search=search,
        role=role,
        status=status,
        security_violation=security_violation,
        min_score=min_score,
        max_score=max_score,
        limit=limit
    )


@app.get("/api/admin/interviews/{interview_id}")
def api_admin_get_interview_detail(interview_id: int, admin: Dict[str, Any] = Depends(get_current_admin)):
    """Admin retrieves complete evaluation and question answers for any interview."""
    data = get_interview(interview_id)
    int_dict = data.get("interview", {})
    if int_dict and "candidate_name" not in int_dict:
        u_id = int_dict.get("user_id")
        if u_id:
            conn = get_connection()
            cur = conn.cursor()
            try:
                cur.execute("SELECT name, email FROM Users WHERE id = ?", (u_id,))
                u_row = cur.fetchone()
                if u_row:
                    int_dict["candidate_name"] = u_row[0]
                    int_dict["candidate_email"] = u_row[1]
            finally:
                cur.close()
                conn.close()
        if "candidate_name" not in int_dict:
            int_dict["candidate_name"] = "Candidate"
            int_dict["candidate_email"] = "N/A"
    if int_dict and "pdf_report_url" not in int_dict:
        int_dict["pdf_report_url"] = f"/api/interview/{interview_id}/report/pdf"
    data["candidate_name"] = int_dict.get("candidate_name")
    data["pdf_report_url"] = f"/api/interview/{interview_id}/report/pdf"

    log_admin_action(
        admin=admin,
        action="INTERVIEW_VIEWED",
        target_type="Interview",
        target_id=interview_id
    )
    return data


@app.get("/api/admin/questions")
def api_admin_get_questions(
    role: Optional[str] = None,
    difficulty: Optional[str] = None,
    search: Optional[str] = None,
    admin: Dict[str, Any] = Depends(get_current_admin)
):
    """Admin retrieves curated and custom questions from Question Bank."""
    return get_admin_questions_list(role=role, difficulty=difficulty, search=search)


@app.post("/api/admin/questions")
def api_admin_create_question(req: AdminQuestionCreateRequest, admin: Dict[str, Any] = Depends(get_current_admin)):
    """Admin creates a new interview question."""
    try:
        target_role = req.role_name or req.role or "General"
        target_topics = req.expected_topics or req.expected_concepts or ""
        new_q = create_question_by_admin(
            role_name=target_role,
            category=req.category or "Technical",
            difficulty=req.difficulty or "Medium",
            question_text=req.question_text,
            expected_topics=target_topics,
            reference_answer=req.reference_answer or "",
            evaluation_guidance=req.evaluation_guidance or ""
        )
        log_admin_action(
            admin=admin,
            action="QUESTION_CREATED",
            target_type="Question",
            target_id=new_q["id"],
            details={"role": target_role, "question": req.question_text[:60]}
        )
        return {
            "status": "success",
            "message": "Question created successfully.",
            "id": new_q["id"],
            "question_id": new_q["id"]
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@app.put("/api/admin/questions/{question_id}")
def api_admin_update_question(question_id: int, req: AdminQuestionUpdateRequest, admin: Dict[str, Any] = Depends(get_current_admin)):
    """Admin updates an existing question."""
    try:
        target_role = req.role_name or req.role
        target_topics = req.expected_topics or req.expected_concepts
        update_question_by_admin(
            question_id=question_id,
            role_name=target_role,
            category=req.category,
            difficulty=req.difficulty,
            question_text=req.question_text,
            expected_topics=target_topics,
            reference_answer=req.reference_answer,
            evaluation_guidance=req.evaluation_guidance,
            is_active=req.is_active
        )
        log_admin_action(
            admin=admin,
            action="QUESTION_EDITED",
            target_type="Question",
            target_id=question_id,
            details={"role": target_role, "is_active": req.is_active}
        )
        return {"status": "success", "message": "Question updated successfully."}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@app.delete("/api/admin/questions/{question_id}")
def api_admin_delete_question(question_id: int, admin: Dict[str, Any] = Depends(get_current_admin)):
    """Admin safely deletes or disables a question."""
    delete_question_by_admin(question_id)
    log_admin_action(
        admin=admin,
        action="QUESTION_DELETED",
        target_type="Question",
        target_id=question_id
    )
    return {"status": "success", "message": "Question deleted/disabled successfully."}


@app.get("/api/admin/roles")
def api_admin_get_roles(admin: Dict[str, Any] = Depends(get_current_admin)):
    """Admin retrieves all configured interview roles."""
    return get_admin_roles_list()


@app.post("/api/admin/roles")
def api_admin_create_role(req: AdminRoleCreateRequest, admin: Dict[str, Any] = Depends(get_current_admin)):
    """Admin creates a new interview role."""
    try:
        new_r = create_role_by_admin(
            role_name=req.role_name,
            slug=req.slug or "",
            description=req.description or "",
            topics=req.topics or "",
            icon=req.icon or "fa-briefcase"
        )
        log_admin_action(
            admin=admin,
            action="ROLE_CREATED",
            target_type="Role",
            target_id=new_r["id"],
            details={"role_name": req.role_name}
        )
        return {
            "status": "success",
            "message": "Role created successfully.",
            "role": new_r,
            "role_id": new_r["id"]
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@app.put("/api/admin/roles/{role_id}")
def api_admin_update_role(role_id: int, req: AdminRoleUpdateRequest, admin: Dict[str, Any] = Depends(get_current_admin)):
    """Admin updates an interview role."""
    try:
        update_role_by_admin(
            role_id=role_id,
            role_name=req.role_name,
            description=req.description or "",
            topics=req.topics or "",
            icon=req.icon or "fa-briefcase",
            is_active=bool(req.is_active)
        )
        log_admin_action(
            admin=admin,
            action="ROLE_EDITED",
            target_type="Role",
            target_id=role_id,
            details={"role_name": req.role_name, "is_active": req.is_active}
        )
        return {"status": "success", "message": "Role updated successfully."}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@app.get("/api/admin/security")
def api_admin_get_security(admin: Dict[str, Any] = Depends(get_current_admin)):
    """Admin retrieves security events, violations, and tab-switch policy statuses."""
    return get_admin_security_data()


@app.get("/api/admin/audit-logs")
def api_admin_get_audit_logs(
    search: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 150,
    admin: Dict[str, Any] = Depends(get_current_admin)
):
    """Admin retrieves immutable system audit logs."""
    return get_admin_audit_logs(search=search, action=action, limit=limit)


@app.get("/api/admin/system-health")
def api_admin_system_health(admin: Dict[str, Any] = Depends(get_current_admin)):
    """Admin performs diagnostic health checks across all backend subsystems."""
    return check_system_health()


@app.get("/api/admin/analytics")
def api_admin_analytics(admin: Dict[str, Any] = Depends(get_current_admin)):
    """Admin retrieves question difficulty rankings, missed concepts, and role metrics."""
    return get_admin_advanced_analytics()


@app.put("/api/admin/profile")
def api_admin_update_profile(req: AdminProfileUpdateRequest, admin: Dict[str, Any] = Depends(get_current_admin)):
    """Admin updates their own name and email address safely."""
    clean_name = req.name.strip()
    if not clean_name:
        raise HTTPException(status_code=400, detail="Name cannot be empty.")

    clean_email = normalize_email(req.email)
    valid_em, em_err = validate_email(clean_email)
    if not valid_em:
        raise HTTPException(status_code=400, detail=em_err)

    conn = get_connection()
    cur = conn.cursor()
    try:
        # Check if email is taken by another user
        cur.execute("SELECT id FROM Users WHERE LOWER(email) = ? AND id != ?", (clean_email, admin["id"]))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Email is already in use by another user.")

        cur.execute("UPDATE Users SET name = ?, email = ? WHERE id = ?", (clean_name, clean_email, admin["id"]))
        conn.commit()

        log_admin_action(
            admin=admin,
            action="ADMIN_PROFILE_UPDATED",
            target_type="Admin",
            target_id=admin["id"],
            details={"new_name": clean_name, "new_email": clean_email}
        )
        return {
            "status": "success",
            "message": "Admin profile updated successfully.",
            "admin": {"id": admin["id"], "name": clean_name, "email": clean_email}
        }
    finally:
        cur.close()
        conn.close()


@app.post("/api/admin/change-password")
def api_admin_change_password(req: ChangePasswordRequest, admin: Dict[str, Any] = Depends(get_current_admin)):
    """Admin changes their password with policy verification and session invalidation."""
    if req.new_password != req.confirm_password:
        raise HTTPException(status_code=400, detail="New passwords do not match.")

    valid_pw, pw_err = validate_password(req.new_password)
    if not valid_pw:
        raise HTTPException(status_code=400, detail=pw_err)

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT password_hash FROM Users WHERE id = ?", (admin["id"],))
        row = cur.fetchone()
        if not row or not verify_password(req.current_password, row[0]):
            raise HTTPException(status_code=400, detail="Current password is incorrect.")

        new_hash = hash_password(req.new_password)
        cur.execute("UPDATE Users SET password_hash = ? WHERE id = ?", (new_hash, admin["id"]))
        conn.commit()

        log_admin_action(
            admin=admin,
            action="ADMIN_PASSWORD_CHANGED",
            target_type="Admin",
            target_id=admin["id"]
        )
        return {"status": "success", "message": "Administrator password changed successfully."}
    finally:
        cur.close()
        conn.close()


@app.get("/api/admin/settings")
def api_admin_get_settings(admin: Dict[str, Any] = Depends(get_current_admin)):
    """Returns system settings with fully masked credentials (NEVER exposes secrets)."""
    smtp_ok = is_smtp_configured()
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = os.environ.get("SMTP_PORT", "587")
    smtp_user = os.environ.get("SMTP_USER", "")
    masked_smtp_user = (smtp_user[:3] + "***@" + smtp_user.split("@")[-1]) if "@" in smtp_user else "***"

    int_policy = {
        "tab_switch_security": "Strict (1 Tab Switch = Immediate Termination)",
        "window_blur_mode": "Ignored (Prevents false positives on permissions/system alerts)",
        "camera_mic_requirement": "Mandatory continuous audio/video WebM capture",
        "scoring_engine": "Multi-model semantic analysis (Faster-Whisper + Timeline concepts)"
    }
    email_data = {
        "configured": smtp_ok,
        "host": smtp_host,
        "port": smtp_port,
        "sender_masked": masked_smtp_user if smtp_ok else "Not Configured"
    }
    ai_data = {
        "speech_to_text": "Faster-Whisper (base.en, CPU int8 inference)",
        "evaluation_engine": "Timeline segmentation + Semantic expected concept matching",
        "question_bank": "SQL Server Curated Role Questions"
    }
    return {
            "status": "success",
            "general": {
                "system_name": "Multi-Model AI Interview Evaluation System",
                "version": "2.4.0 (Enterprise Super Admin)",
                "environment": os.environ.get("ENVIRONMENT", "Production"),
                "organization": "Academic Research & Evaluation System"
            },
            "authentication": {
                "password_min_length": 8,
                "password_uppercase_first": True,
                "password_special_char_required": True,
                "hashing_algorithm": "PBKDF2-HMAC-SHA256 (260,000 iterations)",
                "session_token_lifetime_hours": 24
            },
            "interview_policy": int_policy,
            "interview": int_policy,
            "email_smtp": email_data,
            "email": email_data,
            "ai_subsystems": ai_data,
            "ai": ai_data
        }





# =========================================
# DATABASE TEST ENDPOINT
# =========================================

@app.get("/database-test")
def database_test():
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT DB_NAME()")
        database_name = cursor.fetchone()[0]

        # Check existing columns in Interviews table
        cursor.execute(
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Interviews'"
        )
        columns = [row[0] for row in cursor.fetchall()]

        cursor.close()
        connection.close()

        return {
            "status": "success",
            "message": "Database connection successful",
            "database": database_name,
            "interviews_columns": columns
        }
    except Exception as error:
        return {
            "status": "error",
            "message": str(error)
        }


# =========================================
# SQL SERVER INSERTION HELPER
# Dynamically adapts to existing columns in Interviews table
# =========================================

# =========================================
# SQL SERVER PERSISTENCE HELPER
# Transactionally persists interview records to:
# - Interviews
# - InterviewAnswers (with answer_text, word_count, start_ms, end_ms, scores)
# - EvaluationResults
# - InterviewHistory
# - Feedback
# =========================================

def _ensure_interview_history_table(cursor):
    """Guarantees InterviewHistory table and Feedback.created_at exist before writing."""
    try:
        from database import DB_ENGINE
        is_pg = (DB_ENGINE in ("postgres", "postgresql", "neon") or bool(os.getenv("DATABASE_URL") and DB_ENGINE != "sqlite"))
        if is_pg:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS InterviewHistory (
                    id SERIAL PRIMARY KEY,
                    interview_id INT NOT NULL,
                    user_id INT NULL,
                    role VARCHAR(100) NULL,
                    attempt_number INT NULL,
                    overall_score REAL NULL,
                    technical_score REAL NULL,
                    communication_score REAL NULL,
                    confidence_score REAL NULL,
                    problem_solving_score REAL NULL,
                    relevance_score REAL NULL,
                    completed_at TIMESTAMP NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_interview_history_interview_id ON InterviewHistory (interview_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_interview_history_user_id ON InterviewHistory (user_id)")
            cursor.execute("ALTER TABLE Feedback ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NOT NULL DEFAULT NOW()")
        elif DB_ENGINE == "sqlite":
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS InterviewHistory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    interview_id INTEGER NOT NULL,
                    user_id INTEGER,
                    role TEXT,
                    attempt_number INTEGER DEFAULT 1,
                    overall_score REAL,
                    technical_score REAL,
                    communication_score REAL,
                    confidence_score REAL,
                    problem_solving_score REAL,
                    relevance_score REAL,
                    completed_at TEXT
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_interview_history_interview_id ON InterviewHistory (interview_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_interview_history_user_id ON InterviewHistory (user_id)")
        else:
            # SQL Server / T-SQL
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'InterviewHistory')
                BEGIN
                    CREATE TABLE InterviewHistory (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        interview_id INT NOT NULL,
                        user_id INT NULL,
                        role NVARCHAR(100) NULL,
                        attempt_number INT NULL,
                        overall_score FLOAT NULL,
                        technical_score FLOAT NULL,
                        communication_score FLOAT NULL,
                        confidence_score FLOAT NULL,
                        problem_solving_score FLOAT NULL,
                        relevance_score FLOAT NULL,
                        completed_at DATETIME2 NULL
                    );
                    CREATE INDEX idx_interview_history_interview_id ON InterviewHistory (interview_id);
                    CREATE INDEX idx_interview_history_user_id ON InterviewHistory (user_id);
                END
            """)
    except Exception as eh_err:
        print(f"[SQL Notice] _ensure_interview_history_table notice: {eh_err}")


def save_interview_record(
    role: str,
    total_questions: int,
    recording_path: str,
    transcript: str,
    tab_switch_count: int,
    terminated_reason: str,
    evaluation: dict,
    question_data_list: Optional[list] = None,
    language: str = "en",
    filename: str = "",
    interview_id: Optional[int] = None,
    user_id: Optional[int] = None,
    termination_type: Optional[str] = None,
    security_violation: Optional[bool] = None,
    terminated_at: Optional[datetime] = None,
    status: Optional[str] = None
) -> int:
    """
    Safely and transactionally stores interview records in SQL Server:
    1. Inserts or updates Interviews table.
    2. Inserts or updates InterviewAnswers table with question timing (start_ms, end_ms),
       transcribed answers, word counts, and question-level scores.
    3. Inserts or updates EvaluationResults table with interview-level metrics.
    4. Inserts or updates InterviewHistory table.
    5. Inserts or updates Feedback table.
    Ensures empty answers receive zero scores without inventing text, avoids duplicate
    rows, and commits all operations in a single database transaction.
    """
    connection = get_connection()
    connection.autocommit = False
    cursor = connection.cursor()

    try:
        # Guarantee schema readiness before writing transaction
        _ensure_interview_history_table(cursor)
        # Determine user_id
        if user_id is None and interview_id is not None:
            cursor.execute("SELECT user_id FROM Interviews WHERE id = ?", (interview_id,))
            u_row = cursor.fetchone()
            if u_row and u_row[0] is not None:
                user_id = u_row[0]

        if user_id is None:
            cursor.execute("SELECT TOP 1 id FROM Users WHERE preferred_role = ?", (role,))
            u_row = cursor.fetchone()
            if u_row and u_row[0] is not None:
                user_id = u_row[0]
            else:
                cursor.execute("SELECT TOP 1 id FROM Users ORDER BY id")
                u_row = cursor.fetchone()
                user_id = u_row[0] if u_row else 1

        # Evaluation metrics
        total_attempted = int(evaluation.get("attempted_questions", total_questions))
        total_answered = int(evaluation.get("answered_questions", 0))
        total_unanswered = int(evaluation.get("unanswered_questions", max(0, total_attempted - total_answered)))

        overall_score = float(evaluation.get("overall_score") or 0.0)
        technical_score = float(evaluation.get("technical_score") or 0.0)
        communication_score = float(evaluation.get("communication_score") or 0.0)
        confidence_score = float(evaluation.get("confidence_score") or 0.0)
        raw_prob = evaluation.get("problem_solving_score")
        problem_solving_score = float(raw_prob) if raw_prob is not None else None
        relevance_score = float(evaluation.get("relevance_score") or 0.0)
        completeness_score = float(evaluation.get("completeness_score") or 0.0)

        strengths_list = evaluation.get("strengths", [])
        improvements_list = evaluation.get("improvements", [])
        feedback_json = json.dumps({
            "strengths": strengths_list,
            "improvements": improvements_list
        })
        now = datetime.utcnow()

        # Strict tab switch policy check
        is_tab_switch = (
            int(tab_switch_count or 0) > 0 or
            (terminated_reason and "tab switch" in str(terminated_reason).lower()) or
            (termination_type and str(termination_type).upper() == "TAB_SWITCH") or
            (status and str(status).lower() == "terminated")
        )

        if is_tab_switch:
            status_val = "Terminated"
            term_type_val = "TAB_SWITCH"
            term_reason_val = "Tab Switch Detected"
            sec_violation_val = 1
            term_at_val = terminated_at or now
            tab_count_val = 1
            # Terminated interviews MUST NOT receive any scores or AI feedback
            overall_score = None
            technical_score = None
            communication_score = None
            confidence_score = None
            problem_solving_score = None
            relevance_score = None
            completeness_score = None
            feedback_json = None
            transcript = ""
        else:
            status_val = "COMPLETED"
            term_type_val = None
            term_reason_val = None
            sec_violation_val = 0
            term_at_val = None
            tab_count_val = 0

        # Compute duration_seconds and question_timeline
        duration_seconds = 0.0
        if question_data_list:
            for q in question_data_list:
                r_end = q.get("relative_end")
                if r_end is not None:
                    try:
                        duration_seconds = max(duration_seconds, float(r_end))
                    except (ValueError, TypeError):
                        pass
        duration_seconds = round(duration_seconds, 3)

        timeline = [
            {
                "question_number": q.get("question_number", i + 1),
                "start": q.get("relative_start"),
                "end": q.get("relative_end")
            }
            for i, q in enumerate(question_data_list or [])
        ]
        question_timeline_json = json.dumps(timeline)

        # ---------------------------------------------
        # 1. Interviews Table (Insert or Update)
        # ---------------------------------------------
        is_existing_interview = False
        if interview_id is not None:
            cursor.execute("SELECT id FROM Interviews WHERE id = ?", (interview_id,))
            if cursor.fetchone():
                is_existing_interview = True

        if is_existing_interview:
            cursor.execute("""
                UPDATE Interviews
                SET role = ?,
                    total_questions = ?,
                    recording_path = ?,
                    technical_score = ?,
                    communication_score = ?,
                    confidence_score = ?,
                    problem_solving_score = ?,
                    relevance_score = ?,
                    overall_score = ?,
                    feedback = ?,
                    transcript = ?,
                    tab_switch_count = ?,
                    terminated_reason = ?,
                    user_id = COALESCE(?, user_id),
                    status = ?,
                    duration_seconds = ?,
                    transcript_language = ?,
                    recording_filename = ?,
                    evaluation_method = 'timeline+semantic',
                    completed_at = ?,
                    question_timeline = ?,
                    termination_type = ?,
                    security_violation = ?,
                    terminated_at = ?
                WHERE id = ?
            """, (
                role, total_attempted, recording_path, technical_score,
                communication_score, confidence_score, problem_solving_score,
                relevance_score, overall_score, feedback_json, transcript,
                tab_count_val, term_reason_val, user_id, status_val,
                duration_seconds, language, filename,
                now, question_timeline_json,
                term_type_val, sec_violation_val, term_at_val,
                interview_id
            ))
        else:
            cursor.execute("""
                INSERT INTO Interviews
                (
                    role, total_questions, recording_path, technical_score,
                    communication_score, confidence_score, problem_solving_score,
                    relevance_score, overall_score, feedback, transcript,
                    tab_switch_count, terminated_reason, user_id, status,
                    duration_seconds, transcript_language, recording_filename,
                    evaluation_method, completed_at, question_timeline,
                    termination_type, security_violation, terminated_at
                )
                OUTPUT INSERTED.id
                VALUES
                (
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    'timeline+semantic', ?, ?,
                    ?, ?, ?
                )
            """, (
                role, total_attempted, recording_path, technical_score,
                communication_score, confidence_score, problem_solving_score,
                relevance_score, overall_score, feedback_json, transcript,
                tab_count_val, term_reason_val, user_id, status_val,
                duration_seconds, language, filename,
                now, question_timeline_json,
                term_type_val, sec_violation_val, term_at_val
            ))
            row = cursor.fetchone()
            interview_id = row[0] if row else 1

        # Cleanly sanitize interview_id to int
        if interview_id is not None:
            try:
                clean_str = str(interview_id).strip()
                if clean_str and clean_str.lower() not in ("none", "null", "undefined"):
                    interview_id = int(clean_str)
                else:
                    interview_id = None
            except (ValueError, TypeError):
                interview_id = None

        print(f"[SQL Debug] Interviews table: {'UPDATED' if is_existing_interview else 'INSERTED'} row with ID={interview_id}")

        # ---------------------------------------------
        # 2. Questions Catalog Lookup
        # ---------------------------------------------
        cursor.execute(
            "SELECT id, role_name, question_text, category, difficulty FROM Questions WITH (NOLOCK)"
        )
        catalog_rows = cursor.fetchall()

        CATALOG_STOP_WORDS = {
            "what", "is", "a", "an", "the", "in", "of", "and", "or", "how", "to", "for",
            "with", "are", "do", "you", "your", "can", "they", "used", "tell", "me",
            "about", "why", "which", "would", "will", "this", "role", "please"
        }

        def extract_catalog_tokens(text):
            clean = text.lower().replace("?", " ").replace(".", " ").replace(",", " ").replace("`", " ")
            return set(w for w in clean.split() if w not in CATALOG_STOP_WORDS and len(w) > 1)

        exact_q_map = {}
        token_catalog = []
        for cr in catalog_rows:
            clean_t = " ".join(cr[2].lower().strip().split())
            exact_q_map[clean_t] = (cr[0], cr[3], cr[4])
            t_set = extract_catalog_tokens(clean_t)
            token_catalog.append((cr[0], cr[3], cr[4], t_set, cr[1]))

        def lookup_catalog_question(q_text, default_cat="Technical", default_diff="Easy"):
            clean_input = " ".join(q_text.lower().strip().split())
            if clean_input in exact_q_map:
                return exact_q_map[clean_input]

            input_tokens = extract_catalog_tokens(clean_input)
            best_sim = 0.0
            best_entry = None
            for q_id, c_cat, c_diff, q_toks, q_role in token_catalog:
                if not input_tokens or not q_toks:
                    continue
                overlap = len(input_tokens & q_toks)
                union = len(input_tokens | q_toks)
                sim = overlap / float(union) if union > 0 else 0.0
                if q_role and role and q_role.lower() == role.lower():
                    sim += 0.05
                if sim > best_sim:
                    best_sim = sim
                    best_entry = (q_id, c_cat, c_diff)

            if best_sim >= 0.65 and best_entry is not None:
                exact_q_map[clean_input] = best_entry
                return best_entry

            # Fallback category determination
            cat = default_cat or "Technical"
            if "tell me about yourself" in clean_input or "introduce yourself" in clean_input:
                cat = "Introduction"
            elif any(w in clean_input for w in ["why do you want", "strength", "weakness", "conflict", "work in this field"]):
                cat = "HR"

            # Check if there is a matching question in token_catalog with key phrases for this role
            for q_id, c_cat, c_diff, q_toks, q_role in token_catalog:
                role_matches = (not q_role or not role or q_role.lower() == role.lower())
                if "strength" in clean_input and "strengths" in q_toks and role_matches:
                    entry = (q_id, c_cat, c_diff)
                    exact_q_map[clean_input] = entry
                    return entry
                if ("tell me about yourself" in clean_input or "introduce yourself" in clean_input) and "yourself" in q_toks and role_matches:
                    entry = (q_id, c_cat, c_diff)
                    exact_q_map[clean_input] = entry
                    return entry

            # If not in catalog, dynamically register question in Questions table with its actual expected topics
            try:
                expected_list = get_expected_concepts(q_text, role=role)
                topics_str = ", ".join(expected_list) if isinstance(expected_list, list) else str(expected_list or "")
                cursor.execute("""
                    INSERT INTO Questions
                    (role_name, category, difficulty, question_text, expected_topics, reference_answer, evaluation_guidance, created_at)
                    OUTPUT INSERTED.id
                    VALUES (?, ?, ?, ?, ?, '', '', SYSUTCDATETIME())
                """, (role, cat, default_diff or "Easy", q_text, topics_str))
                new_q_row = cursor.fetchone()
                try:
                    connection.commit()
                except Exception:
                    pass
                if new_q_row:
                    new_entry = (new_q_row[0], cat, default_diff or "Easy")
                    exact_q_map[clean_input] = new_entry
                    token_catalog.append((new_entry[0], cat, default_diff or "Easy", input_tokens, role))
                    return new_entry
            except Exception as ins_err:
                print(f"[SQL Debug] Notice registering question in Questions: {ins_err}")

            return (None, cat, default_diff or "Easy")

        # ---------------------------------------------
        # 3. InterviewAnswers Table (Insert or Update)
        # ---------------------------------------------
        timing_map = {}
        for idx, q_item in enumerate(question_data_list or []):
            qn = q_item.get("question_number", idx + 1)
            timing_map[qn] = q_item

        eval_questions = evaluation.get("questions", [])
        highest_q_num = 0

        for item in eval_questions:
            q_num = int(item.get("question_number", 1))
            highest_q_num = max(highest_q_num, q_num)
            q_text = item.get("question", "")
            candidate_ans = item.get("candidate_answer", "")
            candidate_ans_clean = candidate_ans.strip() if isinstance(candidate_ans, str) else ""
            is_ans = bool(item.get("is_answered", False) and candidate_ans_clean)

            t_info = timing_map.get(q_num, {})
            rel_start = t_info.get("relative_start")
            rel_end = t_info.get("relative_end")

            start_ms = int(round(float(rel_start) * 1000)) if rel_start is not None else None
            end_ms = int(round(float(rel_end) * 1000)) if rel_end is not None else None
            speech_dur = round(float(rel_end) - float(rel_start), 2) if (rel_start is not None and rel_end is not None) else 0.0

            if start_ms is None and t_info.get("start_ms") is not None:
                try:
                    start_ms = int(round(float(t_info["start_ms"])))
                except (ValueError, TypeError):
                    pass
            if end_ms is None and t_info.get("end_ms") is not None:
                try:
                    end_ms = int(round(float(t_info["end_ms"])))
                except (ValueError, TypeError):
                    pass

            # Ensure start_ms and end_ms are non-null for answered questions
            if is_ans and (start_ms is None or end_ms is None):
                if start_ms is None:
                    start_ms = (q_num - 1) * 15000
                if end_ms is None:
                    end_ms = start_ms + max(10000, int(speech_dur * 1000 if speech_dur else 12000))

            q_id, q_cat, q_diff = lookup_catalog_question(
                q_text,
                item.get("category", "Technical"),
                item.get("difficulty", "Easy")
            )

            if is_tab_switch:
                ans_text_val = candidate_ans_clean if is_ans else None
                word_count_val = len(candidate_ans_clean.split()) if is_ans else 0
                tech_s = None
                comm_s = None
                conf_s = None
                prob_s = None
                rel_s = None
                comp_s = None
                overall_ans_s = None
                sem_sim = None
                matched_c = "[]"
                missing_c = "[]"
                q_strengths = "[]"
                q_weaknesses = "[]"
                fb_text = "AI evaluation was not generated because this interview was automatically terminated due to a security violation."
            elif is_ans:
                ans_text_val = candidate_ans_clean
                word_count_val = len(candidate_ans_clean.split())
                tech_s = float(item.get("technical_score") or 0.0)
                comm_s = float(item.get("communication_score") or 0.0)
                conf_s = float(item.get("confidence_score") or 0.0)
                raw_item_prob = item.get("problem_solving_score")
                prob_s = float(raw_item_prob) if raw_item_prob is not None else None
                rel_s = float(item.get("relevance_score") or 0.0)
                comp_s = float(item.get("completeness_score") or 0.0)
                overall_ans_s = float(item.get("overall_score") or 0.0)
                sem_sim = round(rel_s / 100.0, 4)
                matched_c = json.dumps(item.get("matched_concepts", []))
                missing_c = json.dumps(item.get("missing_concepts", []))
                fb_text = str(item.get("feedback", ""))
                q_strengths = json.dumps(item.get("strengths", []))
                q_weaknesses = json.dumps(item.get("improvements", []) or item.get("weaknesses", []))
            else:
                # Strictly zero scores for unanswered questions without inventing answers
                ans_text_val = None
                word_count_val = 0
                tech_s = 0.0
                comm_s = 0.0
                conf_s = 0.0
                prob_s = 0.0
                rel_s = 0.0
                comp_s = 0.0
                overall_ans_s = 0.0
                sem_sim = 0.0
                matched_c = "[]"
                missing_c = json.dumps(item.get("missing_concepts", []) or item.get("expected_concepts", []))
                fb_text = "No answer detected for this question."
                q_strengths = json.dumps(item.get("strengths", []))
                q_weaknesses = json.dumps(item.get("improvements", []) or item.get("weaknesses", []))

            cursor.execute(
                "SELECT id, question_id, question_text FROM InterviewAnswers WHERE interview_id = ? AND question_number = ?",
                (interview_id, q_num)
            )
            existing_ans_row = cursor.fetchone()

            if existing_ans_row:
                target_q_id = q_id if q_id is not None else existing_ans_row[1]
                target_q_text = q_text if q_text else existing_ans_row[2]

                cursor.execute("""
                    UPDATE InterviewAnswers
                    SET question_id = ?,
                        question_text = ?,
                        category = COALESCE(?, category),
                        difficulty = COALESCE(?, difficulty),
                        start_ms = ?,
                        end_ms = ?,
                        answer_text = ?,
                        word_count = ?,
                        speech_duration_seconds = ?,
                        technical_score = ?,
                        communication_score = ?,
                        confidence_score = ?,
                        problem_solving_score = ?,
                        relevance_score = ?,
                        completeness_score = ?,
                        overall_answer_score = ?,
                        semantic_similarity = ?,
                        matched_concepts = ?,
                        missing_concepts = ?,
                        strengths = ?,
                        weaknesses = ?,
                        feedback = ?
                    WHERE id = ?
                """, (
                    target_q_id, target_q_text, q_cat, q_diff,
                    start_ms, end_ms, ans_text_val, word_count_val, speech_dur,
                    tech_s, comm_s, conf_s, prob_s, rel_s, comp_s, overall_ans_s,
                    sem_sim, matched_c, missing_c, q_strengths, q_weaknesses,
                    fb_text, existing_ans_row[0]
                ))
                ans_row_id = existing_ans_row[0]
                action = "UPDATED"
            else:
                cursor.execute("""
                    INSERT INTO InterviewAnswers
                    (
                        interview_id, question_id, question_number, question_text, category, difficulty,
                        start_ms, end_ms, answer_text, word_count, speech_duration_seconds,
                        technical_score, communication_score, confidence_score, problem_solving_score,
                        relevance_score, completeness_score, overall_answer_score, semantic_similarity,
                        matched_concepts, missing_concepts, strengths, weaknesses, feedback, created_at
                    )
                    OUTPUT INSERTED.id
                    VALUES
                    (
                        ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, SYSUTCDATETIME()
                    )
                """, (
                    interview_id, q_id, q_num, q_text, q_cat, q_diff,
                    start_ms, end_ms, ans_text_val, word_count_val, speech_dur,
                    tech_s, comm_s, conf_s, prob_s,
                    rel_s, comp_s, overall_ans_s, sem_sim,
                    matched_c, missing_c, q_strengths, q_weaknesses, fb_text
                ))
                ins_row = cursor.fetchone()
                ans_row_id = ins_row[0] if ins_row else None
                action = "INSERTED"

            if is_ans:
                print(f"[SQL Debug] InterviewAnswers Q{q_num} (interview_id={interview_id}): {action} row #{ans_row_id} | question_id={target_q_id if existing_ans_row else q_id} | text={repr(ans_text_val)} | words={word_count_val} | start_ms={start_ms} | end_ms={end_ms} | score={overall_ans_s}")
            else:
                print(f"[SQL Debug] InterviewAnswers Q{q_num} (interview_id={interview_id}): {action} row #{ans_row_id} preserved as UNANSWERED (reason: no usable speech detected in window) | start_ms={start_ms} | end_ms={end_ms} | score=0.0")

        # Safely mark any unreached placeholder rows as unattempted (scores = 0.0)
        cursor.execute("""
            UPDATE InterviewAnswers
            SET answer_text = NULL,
                word_count = 0,
                technical_score = 0.0,
                communication_score = 0.0,
                confidence_score = 0.0,
                problem_solving_score = 0.0,
                relevance_score = 0.0,
                completeness_score = 0.0,
                overall_answer_score = 0.0,
                semantic_similarity = 0.0,
                matched_concepts = '[]',
                feedback = 'Question was not reached or attempted during the interview.'
            WHERE interview_id = ? AND question_number > ?
        """, (interview_id, highest_q_num))
        print(f"[SQL Debug] InterviewAnswers: Updated unreached placeholder questions (Q > {highest_q_num}) for interview_id={interview_id} as not reached.")

        # ---------------------------------------------
        # 4. EvaluationResults & Feedback Handling
        # ---------------------------------------------
        if is_tab_switch:
            cursor.execute("DELETE FROM EvaluationResults WHERE interview_id = ?", (interview_id,))
            cursor.execute("DELETE FROM Feedback WHERE interview_id = ?", (interview_id,))
            print(f"[SQL Debug] Terminated interview #{interview_id}: Purged EvaluationResults and Feedback rows.")

            cursor.execute("SELECT id FROM InterviewHistory WHERE interview_id = ?", (interview_id,))
            existing_hist_row = cursor.fetchone()
            if existing_hist_row:
                cursor.execute("""
                    UPDATE InterviewHistory
                    SET user_id = ?,
                        role = ?,
                        overall_score = NULL,
                        technical_score = NULL,
                        communication_score = NULL,
                        confidence_score = NULL,
                        problem_solving_score = NULL,
                        relevance_score = NULL,
                        completed_at = ?
                    WHERE id = ?
                """, (user_id, role, now, existing_hist_row[0]))
            else:
                cursor.execute("""
                    INSERT INTO InterviewHistory (interview_id, user_id, role, attempt_number, overall_score, completed_at)
                    VALUES (?, ?, ?, 1, NULL, ?)
                """, (interview_id, user_id, role, now))
            print(f"[SQL Debug] InterviewHistory: Recorded terminated state (overall_score=NULL) for interview #{interview_id}")
        else:
            tech_coverage = round(float(total_answered) / float(total_attempted), 4) if total_attempted > 0 else 0.0
            strengths_json_all = json.dumps(strengths_list)
            weaknesses_json_all = json.dumps(improvements_list)
            recs_json_all = json.dumps(improvements_list)

            cursor.execute("SELECT id FROM EvaluationResults WHERE interview_id = ?", (interview_id,))
            existing_eval_row = cursor.fetchone()

            if existing_eval_row:
                cursor.execute("""
                    UPDATE EvaluationResults
                    SET technical_score = ?,
                        communication_score = ?,
                        confidence_score = ?,
                        problem_solving_score = ?,
                        relevance_score = ?,
                        overall_score = ?,
                        answers_evaluated = ?,
                        answered_count = ?,
                        technical_coverage = ?,
                        strengths = ?,
                        weaknesses = ?,
                        recommendations = ?,
                        evaluation_method = 'timeline+semantic'
                    WHERE id = ?
                """, (
                    technical_score, communication_score, confidence_score,
                    problem_solving_score, relevance_score, overall_score,
                    total_answered, total_answered, tech_coverage,
                    strengths_json_all, weaknesses_json_all, recs_json_all,
                    existing_eval_row[0]
                ))
            else:
                cursor.execute("""
                    INSERT INTO EvaluationResults
                    (
                        interview_id, technical_score, communication_score, confidence_score,
                        problem_solving_score, relevance_score, overall_score, answers_evaluated,
                        answered_count, technical_coverage, strengths, weaknesses,
                        recommendations, evaluation_method, created_at
                    )
                    VALUES
                    (
                        ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, 'timeline+semantic', SYSUTCDATETIME()
                    )
                """, (
                    interview_id, technical_score, communication_score, confidence_score,
                    problem_solving_score, relevance_score, overall_score, total_answered,
                    total_answered, tech_coverage, strengths_json_all, weaknesses_json_all,
                    recs_json_all
                ))

            # 5. InterviewHistory Table (Insert or Update for Scored Completed)
            cursor.execute("SELECT id FROM InterviewHistory WHERE interview_id = ?", (interview_id,))
            existing_hist_row = cursor.fetchone()

            if existing_hist_row:
                cursor.execute("""
                    UPDATE InterviewHistory
                    SET user_id = ?,
                        role = ?,
                        attempt_number = 1,
                        overall_score = ?,
                        technical_score = ?,
                        communication_score = ?,
                        confidence_score = ?,
                        problem_solving_score = ?,
                        relevance_score = ?,
                        completed_at = ?
                    WHERE id = ?
                """, (
                    user_id, role, overall_score, technical_score,
                    communication_score, confidence_score, problem_solving_score,
                    relevance_score, now, existing_hist_row[0]
                ))
            else:
                cursor.execute("""
                    INSERT INTO InterviewHistory
                    (
                        interview_id, user_id, role, attempt_number,
                        overall_score, technical_score, communication_score,
                        confidence_score, problem_solving_score, relevance_score,
                        completed_at
                    )
                    VALUES
                    (
                        ?, ?, ?, 1,
                        ?, ?, ?,
                        ?, ?, ?,
                        ?
                    )
                """, (
                    interview_id, user_id, role,
                    overall_score, technical_score, communication_score,
                    confidence_score, problem_solving_score, relevance_score,
                    now
                ))

            # 6. Feedback Table (Insert or Update for Completed)
            prob_text = f"{problem_solving_score:.1f}" if problem_solving_score is not None else "N/A"
            overall_perf_text = (
                f"Scored {overall_score:.1f}/100 overall for the {role} interview. "
                f"Technical: {technical_score:.1f}, Communication: {communication_score:.1f}, "
                f"Confidence: {confidence_score:.1f}, Problem Solving: {prob_text}, "
                f"Relevance: {relevance_score:.1f}. Answered {total_answered} of {total_attempted} questions."
            )
            summary_text = f"Overall performance for {role}: {overall_score:.1f}/100."

            tech_sug = json.dumps([
                "Review core technical concepts and terminology for your target role.",
                "Practice articulating code mechanisms and system designs clearly."
            ])
            comm_sug = json.dumps([
                "Answer with a clear structure: definition, explanation, and concrete example.",
                "Maintain steady pacing and avoid filler words during complex explanations."
            ])
            conf_sug = json.dumps([
                "State answers with conviction and direct reasoning.",
                "Acknowledge knowledge boundaries constructively when uncertain."
            ])
            prob_sug = json.dumps([
                "Walk through problem-solving steps out loud to demonstrate methodology.",
                "Explain trade-offs between alternative technical approaches."
            ])
            practice_sug = json.dumps([
                f"Re-attempt mock interviews for {role} focusing on high-frequency questions.",
                "Review missing concepts identified in your question breakdown."
            ])

            cursor.execute("SELECT id FROM Feedback WHERE interview_id = ?", (interview_id,))
            existing_fb_row = cursor.fetchone()

            if existing_fb_row:
                cursor.execute("""
                    UPDATE Feedback
                    SET overall_performance = ?,
                        strengths = ?,
                        weaknesses = ?,
                        areas_to_improve = ?,
                        technical_suggestions = ?,
                        communication_suggestions = ?,
                        confidence_suggestions = ?,
                        problem_solving_suggestions = ?,
                        practice_areas = ?,
                        summary = ?
                    WHERE id = ?
                """, (
                    overall_perf_text, strengths_json_all, weaknesses_json_all,
                    recs_json_all, tech_sug, comm_sug, conf_sug,
                    prob_sug, practice_sug, summary_text, existing_fb_row[0]
                ))
            else:
                cursor.execute("""
                    INSERT INTO Feedback
                    (
                        interview_id, overall_performance, strengths, weaknesses,
                        areas_to_improve, technical_suggestions, communication_suggestions,
                        confidence_suggestions, problem_solving_suggestions, practice_areas,
                        summary, created_at
                    )
                    VALUES
                    (
                        ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?,
                        ?, SYSUTCDATETIME()
                    )
                """, (
                    interview_id, overall_perf_text, strengths_json_all, weaknesses_json_all,
                    recs_json_all, tech_sug, comm_sug,
                    conf_sug, prob_sug, practice_sug,
                    summary_text
                ))

            print(f"[SQL Debug] EvaluationResults: {'UPDATED' if existing_eval_row else 'INSERTED'} for interview_id={interview_id}")
            print(f"[SQL Debug] InterviewHistory: {'UPDATED' if existing_hist_row else 'INSERTED'} for interview_id={interview_id}")
            print(f"[SQL Debug] Feedback: {'UPDATED' if existing_fb_row else 'INSERTED'} for interview_id={interview_id}")
        print(f"[SQL Debug] Committing transaction for interview #{interview_id}...")

        # Commit transaction
        connection.commit()
        print(f"[SQL Database] Interview #{interview_id} successfully persisted to Interviews, InterviewAnswers, EvaluationResults, InterviewHistory, and Feedback.")
        return interview_id

    except Exception as db_err:
        connection.rollback()
        print(f"[SQL Database Transaction Rolled Back] Error saving interview record: {db_err}")
        raise
    finally:
        cursor.close()
        connection.close()


# =========================================
# IDEMPOTENCY & ASYNC SUBMISSION JOB CACHES
# =========================================

IDEMPOTENT_UPLOAD_CACHE: Dict[str, Any] = {}
SUBMISSION_JOBS: Dict[str, Dict[str, Any]] = {}
SESSION_ACTIVE_JOBS: Dict[str, str] = {}

def build_idempotent_interview_response(interview_id: int, row: tuple, cursor) -> Dict[str, Any]:
    """Builds consistent interview upload response for already processed/terminated interviews."""
    cursor.execute("""
        SELECT question_number, question_text, answer_text, technical_score,
               communication_score, confidence_score, problem_solving_score,
               relevance_score, completeness_score, overall_answer_score,
               matched_concepts, missing_concepts, strengths, weaknesses, feedback
        FROM InterviewAnswers
        WHERE interview_id = ?
        ORDER BY question_number
    """, (interview_id,))
    ans_rows = cursor.fetchall()
    existing_questions = []
    for ar in ans_rows:
        matched_c = []
        missing_c = []
        strengths_c = []
        weaknesses_c = []
        try:
            matched_c = json.loads(ar[10] or "[]")
        except Exception:
            pass
        try:
            missing_c = json.loads(ar[11] or "[]")
        except Exception:
            pass
        try:
            strengths_c = json.loads(ar[12] or "[]")
        except Exception:
            pass
        try:
            weaknesses_c = json.loads(ar[13] or "[]")
        except Exception:
            pass
        has_ans = bool(ar[2] and str(ar[2]).strip())
        existing_questions.append({
            "question_number": ar[0],
            "question": ar[1],
            "candidate_answer": ar[2] or "",
            "is_answered": has_ans,
            "technical_score": ar[3],
            "communication_score": ar[4],
            "confidence_score": ar[5],
            "problem_solving_score": ar[6],
            "relevance_score": ar[7],
            "completeness_score": ar[8],
            "overall_score": ar[9],
            "matched_concepts": matched_c,
            "missing_concepts": missing_c,
            "strengths": strengths_c,
            "improvements": weaknesses_c,
            "feedback": ar[14] or ""
        })

    is_term = str(row[2] or "").lower() == "terminated"
    eval_dict = None
    overall_score_val = None

    if not is_term:
        cursor.execute("""
            SELECT technical_score, communication_score, confidence_score,
                   problem_solving_score, relevance_score, overall_score, strengths, weaknesses
            FROM EvaluationResults
            WHERE interview_id = ?
        """, (interview_id,))
        eval_r = cursor.fetchone()
        if eval_r:
            s_list = []
            w_list = []
            try:
                s_list = json.loads(eval_r[6] or "[]")
            except Exception:
                pass
            try:
                w_list = json.loads(eval_r[7] or "[]")
            except Exception:
                pass
            eval_dict = {
                "overall_score": eval_r[5],
                "technical_score": eval_r[0],
                "communication_score": eval_r[1],
                "confidence_score": eval_r[2],
                "problem_solving_score": eval_r[3],
                "relevance_score": eval_r[4],
                "strengths": s_list,
                "improvements": w_list,
                "questions": existing_questions
            }
            overall_score_val = eval_r[5]
        else:
            eval_dict = {
                "overall_score": row[7],
                "questions": existing_questions
            }
            overall_score_val = row[7]

    answered_c = sum(1 for q in existing_questions if q.get("is_answered"))
    attempted_c = len(existing_questions) or row[8] or 0

    return {
        "status": "success",
        "message": "Interview already processed (idempotent result)",
        "interview_id": row[0],
        "role": row[1],
        "filename": row[12] or "",
        "recording_path": row[11] or "",
        "recording_url": f"/interview/{row[0]}/recording" if (row[11] or row[12]) else None,
        "recording_available": bool(row[11] or row[12]),
        "duration_seconds": row[9] or 0.0,
        "transcript": "" if is_term else (row[10] or ""),
        "language": "en",
        "total_questions": attempted_c,
        "attempted_questions": attempted_c,
        "answered_questions": answered_c,
        "unanswered_questions": max(0, attempted_c - answered_c),
        "tab_switch_count": row[3] or (1 if is_term else 0),
        "terminated_reason": row[4] or ("Tab Switch Detected" if is_term else ""),
        "interview_status": "Terminated" if is_term else (row[2] or "COMPLETED"),
        "termination_type": row[5] or ("TAB_SWITCH" if is_term else ""),
        "security_violation": bool(row[6]) if row[6] is not None else is_term,
        "overall_score": overall_score_val,
        "evaluation": eval_dict,
        "question_answers": existing_questions
    }


# =========================================
# SUBMISSION PIPELINE EXECUTION ENGINE
# =========================================

def execute_submission_pipeline(
    file_path: str,
    filename: str,
    role: str,
    total_questions: int,
    attempted_questions: Optional[int],
    answered_questions: Optional[int],
    unanswered_questions: Optional[int],
    question_data_list: list,
    recording_start_time: Optional[float],
    parsed_interview_id: Optional[int],
    parsed_user_id: Optional[int],
    client_session_id: Optional[str],
    interview_status: str,
    tab_switch_count: int,
    is_sec_violation: bool,
    termination_type: Optional[str],
    terminated_reason: Optional[str],
    terminated_at_dt: Optional[datetime],
    job_id: Optional[str] = None,
    raw_candidate_name: Optional[str] = None
) -> Dict[str, Any]:
    t_start = time.time()
    print("\n" + "=" * 60)
    print(f"[Submission Pipeline] Processing recording: {filename}")
    print(f"Role: {role} | Execution Mode: {'Async Job: ' + job_id if job_id else 'Synchronous'}")
    print("=" * 60)

    if job_id and job_id in SUBMISSION_JOBS:
        SUBMISSION_JOBS[job_id]["stage"] = "transcribing"
        SUBMISSION_JOBS[job_id]["progress"] = 25
        SUBMISSION_JOBS[job_id]["message"] = "Transcribing speech using Faster-Whisper AI..."

    # =====================================
    # COMPUTE RELATIVE TIMINGS
    # =====================================
    if question_data_list:
        first_start_time = None
        if recording_start_time is not None:
            try:
                first_start_time = float(recording_start_time)
            except (ValueError, TypeError):
                first_start_time = None

        if first_start_time is None:
            for item in question_data_list:
                st = item.get("start_time")
                if st is not None:
                    try:
                        first_start_time = float(st)
                        break
                    except (ValueError, TypeError):
                        continue

        if first_start_time is None:
            first_start_time = 0.0

        is_millis = float(first_start_time) > 100000

        for item in question_data_list:
            s_time = item.get("start_time")
            e_time = item.get("end_time")

            if s_time is None and item.get("start_ms") is not None:
                s_time = item.get("start_ms")
            if e_time is None and item.get("end_ms") is not None:
                e_time = item.get("end_ms")

            try:
                s_val = float(s_time) if s_time is not None else None
            except (ValueError, TypeError):
                s_val = None

            try:
                e_val = float(e_time) if e_time is not None else None
            except (ValueError, TypeError):
                e_val = None

            if is_millis:
                item["relative_start"] = (
                    round((s_val - first_start_time) / 1000.0, 3)
                    if s_val is not None else (
                        round(float(item["relative_start"]), 3) if item.get("relative_start") is not None else None
                    )
                )
                item["relative_end"] = (
                    round((e_val - first_start_time) / 1000.0, 3)
                    if e_val is not None else (
                        round(float(item["relative_end"]), 3) if item.get("relative_end") is not None else None
                    )
                )
            else:
                if s_val is not None:
                    item["relative_start"] = round(s_val, 3)
                elif item.get("relative_start") is not None:
                    item["relative_start"] = round(float(item["relative_start"]), 3)
                else:
                    item["relative_start"] = None

                if e_val is not None:
                    item["relative_end"] = round(e_val, 3)
                elif item.get("relative_end") is not None:
                    item["relative_end"] = round(float(item["relative_end"]), 3)
                else:
                    item["relative_end"] = None

    # Look up registered candidate full name for domain vocabulary tuning.
    # Never assume a short username/handle like 'Nani' is the spoken full name.
    candidate_name = None
    if raw_candidate_name and is_usable_candidate_name(raw_candidate_name):
        candidate_name = raw_candidate_name.strip()

    if not candidate_name and parsed_user_id:
        conn_usr = None
        try:
            conn_usr = get_connection()
            cur_usr = conn_usr.cursor()
            cur_usr.execute("SELECT name, email FROM Users WHERE id = ?", (parsed_user_id,))
            usr_row = cur_usr.fetchone()
            if usr_row:
                db_name = (usr_row[0] or "").strip()
                db_email = (usr_row[1] or "").strip()
                if is_usable_candidate_name(db_name):
                    candidate_name = db_name
                else:
                    # Look for associated registered profile possessing a full name
                    if db_email and ("ppsu.ac.in" in db_email.lower() or "boyapati" in db_email.lower()):
                        cur_usr.execute("SELECT TOP 1 name FROM Users WHERE (email LIKE '%ppsu.ac.in' OR email LIKE '%boyapati%') AND LEN(name) > 6 AND name LIKE '% %'")
                        match_row = cur_usr.fetchone()
                        if match_row and is_usable_candidate_name(match_row[0]):
                            candidate_name = match_row[0].strip()
            cur_usr.close()
        except Exception as u_err:
            print(f"[Submission Pipeline] Candidate name lookup notice: {u_err}")
        finally:
            if conn_usr:
                conn_usr.close()

    # =====================================
    # SINGLE-PASS FASTER-WHISPER TRANSCRIPTION
    # =====================================
    t_whisp_start = time.time()
    transcription_result = transcribe_recording(file_path, role=role, candidate_name=candidate_name)
    t_whisp_end = time.time()
    t_whisp_duration = round(t_whisp_end - t_whisp_start, 2)
    print(f"[Timing Breakdown] Faster-Whisper transcription completed in {t_whisp_duration}s")

    transcript = transcription_result.get("text", "")
    language = transcription_result.get("language", "en")
    whisper_segments = transcription_result.get("segments", [])

    # =====================================
    # ASSOCIATE SPEECH SEGMENTS WITH QUESTIONS (WORD-LEVEL PRECISION)
    # =====================================
    t_map_start = time.time()
    question_answers = []

    if question_data_list:
        max_whisper_time = 0.0
        if whisper_segments:
            max_whisper_time = max(float(seg.get("end", 0.0)) for seg in whisper_segments)

        num_q = len(question_data_list)
        last_end = 0.0

        for index, q_item in enumerate(question_data_list):
            raw_start = q_item.get("relative_start")
            raw_end = q_item.get("relative_end")

            if index == 0:
                win_start = 0.0
            else:
                win_start = last_end
                if raw_start is not None and float(raw_start) > win_start:
                    win_start = float(raw_start)

            if index + 1 < num_q:
                next_start = question_data_list[index + 1].get("relative_start")
                if next_start is not None and float(next_start) > win_start:
                    win_end = float(next_start)
                elif raw_end is not None and float(raw_end) >= win_start:
                    win_end = float(raw_end)
                else:
                    win_end = win_start
            else:
                if raw_end is not None and float(raw_end) >= win_start:
                    win_end = max(float(raw_end), max_whisper_time)
                elif max_whisper_time > win_start:
                    win_end = max_whisper_time
                else:
                    win_end = win_start

            q_item["relative_start"] = round(win_start, 3)
            q_item["relative_end"] = round(win_end, 3)
            last_end = win_end

        question_matched_speech = {i: [] for i in range(num_q)}
        question_word_details = {i: [] for i in range(num_q)}

        for seg_idx, seg in enumerate(whisper_segments):
            s_start = float(seg.get("start", 0.0))
            s_end = float(seg.get("end", 0.0))
            seg_text = seg.get("text", "").strip()
            words = seg.get("words", [])

            if not seg_text:
                continue

            if words:
                for w in words:
                    w_text = w.get("word", "").strip()
                    if not w_text:
                        continue
                    w_start = float(w.get("start", 0.0))
                    w_end = float(w.get("end", 0.0))
                    w_mid = (w_start + w_end) / 2.0
                    w_prob = float(w.get("probability", 1.0))

                    assigned_idx = None
                    for idx, q_item in enumerate(question_data_list):
                        qs = float(q_item["relative_start"])
                        qe = float(q_item["relative_end"])
                        if idx == num_q - 1:
                            if w_mid >= qs:
                                assigned_idx = idx
                                break
                        else:
                            if qs <= w_mid < qe:
                                assigned_idx = idx
                                break

                    if assigned_idx is None:
                        assigned_idx = 0 if w_mid < float(question_data_list[0]["relative_start"]) else num_q - 1

                    question_matched_speech[assigned_idx].append(w_text)
                    question_word_details[assigned_idx].append({
                        "word": w_text,
                        "start": round(w_start, 3),
                        "end": round(w_end, 3),
                        "probability": round(w_prob, 3)
                    })
            else:
                midpoint = (s_start + s_end) / 2.0
                assigned_idx = None
                for idx, q_item in enumerate(question_data_list):
                    qs = float(q_item["relative_start"])
                    qe = float(q_item["relative_end"])
                    if idx == num_q - 1:
                        if midpoint >= qs:
                            assigned_idx = idx
                            break
                    else:
                        if qs <= midpoint < qe:
                            assigned_idx = idx
                            break

                if assigned_idx is None:
                    assigned_idx = 0 if midpoint < float(question_data_list[0]["relative_start"]) else num_q - 1

                question_matched_speech[assigned_idx].append(seg_text)

        for index, q_item in enumerate(question_data_list):
            q_num = q_item.get("question_number", index + 1)
            q_text = q_item.get("question", "")
            rel_start = q_item.get("relative_start")
            rel_end = q_item.get("relative_end")
            typed_answer = q_item.get("candidate_answer", "").strip()

            matched_parts = question_matched_speech.get(index, [])
            spoken_text = " ".join(matched_parts).strip()
            spoken_text = re.sub(r"\.{2,}\s*$", "", spoken_text).strip()
            spoken_text = " ".join(spoken_text.split())

            if spoken_text:
                final_answer = spoken_text
            elif typed_answer:
                final_answer = typed_answer
            else:
                final_answer = ""

            concepts = get_expected_concepts(q_text, role=role)
            is_ans = is_valid_answer(final_answer, question=q_text)
            if not is_ans:
                final_answer = ""

            question_answers.append({
                "question_number": q_num,
                "question": q_text,
                "candidate_answer": final_answer,
                "is_answered": is_ans,
                "status": "answered" if is_ans else "not_answered",
                "relative_start": rel_start,
                "relative_end": rel_end,
                "expected_concepts": concepts
            })
    else:
        is_ans = is_valid_answer(transcript)
        question_answers.append({
            "question_number": 1,
            "question": "General Interview Response",
            "candidate_answer": transcript if is_ans else "",
            "is_answered": is_ans,
            "status": "answered" if is_ans else "not_answered",
            "expected_concepts": get_expected_concepts("Tell me about yourself.")
        })

    t_map_end = time.time()
    t_map_duration = round(t_map_end - t_map_start, 3)
    print(f"[Timing Breakdown] Speech segment mapping completed in {t_map_duration}s")

    if job_id and job_id in SUBMISSION_JOBS:
        SUBMISSION_JOBS[job_id]["stage"] = "evaluating"
        SUBMISSION_JOBS[job_id]["progress"] = 70
        SUBMISSION_JOBS[job_id]["message"] = "Evaluating answers across technical concepts and communication..."

    # =====================================
    # RUN SEMANTIC AI EVALUATION
    # =====================================
    t_eval_start = time.time()
    evaluation_result = evaluate_interview(question_answers)
    t_eval_end = time.time()
    t_eval_duration = round(t_eval_end - t_eval_start, 3)
    print(f"[Timing Breakdown] Semantic AI evaluation completed in {t_eval_duration}s")

    # Non-fatal video segment clips creation
    try:
        segments_dir = os.path.join(UPLOAD_DIR, "segments", os.path.splitext(filename)[0])
        create_question_segments(file_path, question_answers, segments_dir)
    except Exception as seg_err:
        print(f"[Segmentation] Media segmentation notice (non-fatal): {seg_err}")

    if job_id and job_id in SUBMISSION_JOBS:
        SUBMISSION_JOBS[job_id]["stage"] = "persisting"
        SUBMISSION_JOBS[job_id]["progress"] = 90
        SUBMISSION_JOBS[job_id]["message"] = "Saving interview evaluation report to database..."

    # =====================================
    # SAVE TO SQL SERVER DATABASE
    # =====================================
    t_db_start = time.time()
    duration_seconds = 0.0
    if question_answers:
        for q_ans in question_answers:
            q_end = q_ans.get("relative_end")
            if q_end is not None:
                try:
                    duration_seconds = max(duration_seconds, float(q_end))
                except (ValueError, TypeError):
                    pass
    duration_seconds = round(duration_seconds, 3)

    total_attempted = evaluation_result.get("attempted_questions", len(question_answers))
    total_answered = evaluation_result.get("answered_questions", sum(1 for q in question_answers if q.get("is_answered")))
    total_unanswered = evaluation_result.get("unanswered_questions", max(0, total_attempted - total_answered))

    interview_id = save_interview_record(
        role=role,
        total_questions=total_attempted,
        recording_path=file_path,
        transcript=transcript,
        tab_switch_count=tab_switch_count,
        terminated_reason=terminated_reason,
        evaluation=evaluation_result,
        question_data_list=question_answers,
        language=language,
        filename=filename,
        interview_id=parsed_interview_id,
        user_id=parsed_user_id,
        termination_type=termination_type,
        security_violation=is_sec_violation,
        terminated_at=terminated_at_dt,
        status=interview_status
    )
    t_db_end = time.time()
    t_db_duration = round(t_db_end - t_db_start, 3)

    t_total_backend = round(time.time() - t_start, 2)
    print(f"[Timing Breakdown] Database persistence completed in {t_db_duration}s (Interview #{interview_id})")
    print(f"[Timing Breakdown] TOTAL BACKEND PROCESSING: {t_total_backend}s")
    print("=" * 60 + "\n")

    response_payload = {
        "status": "success",
        "message": "Interview uploaded, segmented and evaluated successfully",
        "interview_id": interview_id,
        "role": role,
        "filename": filename,
        "recording_path": file_path,
        "recording_url": f"/interview/{interview_id}/recording",
        "recording_available": bool(file_path and os.path.exists(file_path)),
        "duration_seconds": duration_seconds,
        "transcript": transcript,
        "language": language,
        "total_questions": total_attempted,
        "attempted_questions": total_attempted,
        "answered_questions": total_answered,
        "unanswered_questions": total_unanswered,
        "tab_switch_count": tab_switch_count,
        "terminated_reason": terminated_reason,
        "interview_status": interview_status,
        "termination_type": termination_type,
        "security_violation": is_sec_violation,
        "terminated_at": terminated_at_dt.isoformat() if terminated_at_dt else None,
        "overall_score": evaluation_result.get("overall_score"),
        "evaluation": evaluation_result,
        "question_answers": evaluation_result["questions"],
        "timing_breakdown": {
            "whisper_seconds": t_whisp_duration,
            "mapping_seconds": t_map_duration,
            "evaluation_seconds": t_eval_duration,
            "database_seconds": t_db_duration,
            "total_backend_seconds": t_total_backend
        }
    }

    if client_session_id:
        IDEMPOTENT_UPLOAD_CACHE[client_session_id] = response_payload

    if job_id and job_id in SUBMISSION_JOBS:
        SUBMISSION_JOBS[job_id]["status"] = "completed"
        SUBMISSION_JOBS[job_id]["stage"] = "completed"
        SUBMISSION_JOBS[job_id]["progress"] = 100
        SUBMISSION_JOBS[job_id]["message"] = "Interview evaluated and stored successfully."
        SUBMISSION_JOBS[job_id]["interview_id"] = interview_id
        SUBMISSION_JOBS[job_id]["result"] = response_payload

    return response_payload


# =========================================
# =========================================
# AMAZON S3 PRESIGNED UPLOAD & STORAGE STATUS
# =========================================

@app.get("/interview/storage/status")
@app.get("/api/interview/storage/status")
def get_storage_status():
    """
    Returns non-sensitive storage health status for diagnostics and UI status indicators.
    Never exposes S3 credentials or access keys.
    """
    try:
        from storage_service import is_s3_configured, get_s3_config
        s3_ready = is_s3_configured()
        cfg = get_s3_config()
        return {
            "s3_configured": s3_ready,
            "r2_configured": s3_ready,  # backward compatibility alias
            "storage_mode": "amazon_s3" if s3_ready else "ephemeral_local",
            "bucket": cfg["bucket_name"] if s3_ready else None,
            "region": cfg["region"] if s3_ready else None,
            "has_access_key": bool(cfg["access_key_id"]),
            "has_secret_key": bool(cfg["secret_access_key"])
        }
    except Exception as exc:
        return {
            "s3_configured": False,
            "r2_configured": False,
            "storage_mode": "ephemeral_local",
            "error": str(exc)
        }


@app.post("/interview/presign_upload")
@app.post("/api/interview/presign_upload")
async def presign_interview_upload(
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """
    Generates a secure, short-lived presigned PUT URL for Amazon S3 direct uploads.
    The browser PUTs the large WebM recording directly to Amazon S3, bypassing
    Vercel's 4.5 MB proxy limit and Render server body buffering entirely.
    """
    if x_api_key is not None and x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    # Accept either JSON or Form data
    content_type_header = (request.headers.get("content-type") or "").lower()
    data = {}
    if "application/json" in content_type_header:
        try:
            data = await request.json()
        except Exception:
            data = {}
    else:
        try:
            form = await request.form()
            data = dict(form)
        except Exception:
            data = {}

    req_role = str(data.get("role") or "Python Developer").strip()
    req_session_id = data.get("client_session_id")
    req_file_size = data.get("file_size")
    req_content_type = str(data.get("content_type") or "video/webm").strip()

    print(f"\n[Storage Stage: Presign Request] Role: '{req_role}' | Session: {req_session_id} | Stated Size: {req_file_size} bytes")

    try:
        from storage_service import is_s3_configured, generate_presigned_upload_url
        if not is_s3_configured():
            print(f"[Storage Stage: Presign Notice] Amazon S3 is not configured. Direct browser S3 upload unavailable.")
            return {
                "s3_configured": False,
                "r2_configured": False,
                "status": "s3_not_configured",
                "message": "Amazon S3 is not configured on the backend server. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET_NAME) are required for persistent recording storage.",
                "required_env_vars": [
                    "AWS_ACCESS_KEY_ID",
                    "AWS_SECRET_ACCESS_KEY",
                    "AWS_REGION",
                    "S3_BUCKET_NAME"
                ],
                "direct_backend_upload_url": "/interview/upload"
            }

        safe_role = "".join(c if c.isalnum() else "_" for c in req_role).strip("_") or "interview"
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        rand_id = uuid.uuid4().hex[:8]
        object_key = f"recordings/{safe_role}_{ts}_{rand_id}.webm"

        presigned = generate_presigned_upload_url(
            object_key=object_key,
            content_type=req_content_type,
            expires_in=900
        )

        if not presigned.get("success"):
            print(f"[Storage Stage: Presign Error] Failed: {presigned.get('error')}")
            return {
                "s3_configured": True,
                "r2_configured": True,
                "status": "error",
                "message": f"Failed to generate presigned upload URL: {presigned.get('error')}",
                "stage": "presign_generation"
            }

        print(f"[Storage Stage: Presigned URL Ready] Object Key: {object_key}")
        return {
            "s3_configured": True,
            "r2_configured": True,
            "status": "success",
            "upload_url": presigned["upload_url"],
            "object_key": object_key,
            "bucket": presigned.get("bucket"),
            "region": presigned.get("region"),
            "expires_in": 900
        }
    except Exception as exc:
        print(f"[Storage Stage: Presign Exception] {exc}")
        return {
            "s3_configured": False,
            "r2_configured": False,
            "status": "error",
            "message": str(exc),
            "stage": "presign_exception"
        }


# =========================================
# INTERVIEW UPLOAD & EVALUATION API
# =========================================

@app.post("/interview/upload")
@app.post("/api/interview/upload")
@app.post("/interview/submit")
@app.post("/api/interview/submit")
async def upload_interview(
    role: str = Form(...),
    total_questions: int = Form(20),
    attempted_questions: Optional[int] = Form(None),
    answered_questions: Optional[int] = Form(None),
    unanswered_questions: Optional[int] = Form(None),
    recording: Optional[UploadFile] = File(None),
    recording_key: Optional[str] = Form(None),
    s3_object_key: Optional[str] = Form(None),
    r2_object_key: Optional[str] = Form(None),
    question_data: str = Form("[]"),
    tab_switch_count: int = Form(0),
    terminated_reason: str = Form(""),
    termination_type: Optional[str] = Form(None),
    security_violation: Optional[str] = Form(None),
    interview_status: Optional[str] = Form(None),
    terminated_at: Optional[str] = Form(None),
    recording_start_time: Optional[float] = Form(None),
    interview_id: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
    user_email: Optional[str] = Form(None),
    candidate_name: Optional[str] = Form(None),
    client_session_id: Optional[str] = Form(None),
    async_mode: Optional[str] = Form(None),
    x_api_key: str = Header(None)
):
    # API Key check
    if x_api_key is not None and x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    try:
        # Parse optional interview_id and user_id
        parsed_interview_id = None
        if interview_id is not None:
            try:
                clean_id = str(interview_id).strip()
                if clean_id and clean_id.lower() not in ("none", "null", "undefined"):
                    parsed_interview_id = int(clean_id)
            except (ValueError, TypeError):
                parsed_interview_id = None

        parsed_user_id = None
        if user_id is not None:
            try:
                clean_uid = str(user_id).strip()
                if clean_uid and clean_uid.lower() not in ("none", "null", "undefined"):
                    parsed_user_id = int(clean_uid)
            except (ValueError, TypeError):
                parsed_user_id = None

        # Idempotency check: client_session_id active job
        if client_session_id and client_session_id in SESSION_ACTIVE_JOBS:
            act_jid = SESSION_ACTIVE_JOBS[client_session_id]
            if act_jid in SUBMISSION_JOBS:
                act_job = SUBMISSION_JOBS[act_jid]
                if act_job.get("status") in ("processing", "completed"):
                    print(f"[Idempotency] Returning existing job '{act_jid}' for session '{client_session_id}'")
                    return {
                        "status": act_job.get("status"),
                        "job_id": act_jid,
                        "stage": act_job.get("stage"),
                        "progress": act_job.get("progress"),
                        "message": act_job.get("message"),
                        "interview_id": act_job.get("interview_id")
                    }

        # Idempotency check: client_session_id cache
        if client_session_id and client_session_id in IDEMPOTENT_UPLOAD_CACHE:
            cached_res = IDEMPOTENT_UPLOAD_CACHE[client_session_id]
            if not (cached_res.get("interview_status") == "Terminated" and not cached_res.get("recording_available")):
                print(f"[Idempotency] Returning cached result for client_session_id: {client_session_id}")
                return cached_res

        # Idempotency check: database check for completed/terminated interview
        if parsed_interview_id is not None:
            idemp_conn = get_connection()
            idemp_cur = idemp_conn.cursor()
            try:
                idemp_cur.execute("""
                    SELECT id, role, status, tab_switch_count, terminated_reason, termination_type,
                           security_violation, overall_score, total_questions, duration_seconds, transcript,
                           recording_path, recording_filename
                    FROM Interviews
                    WHERE id = ?
                """, (parsed_interview_id,))
                idemp_row = idemp_cur.fetchone()
                if idemp_row and idemp_row[2] in ("Terminated", "COMPLETED"):
                    has_recording = bool(idemp_row[11] and os.path.exists(idemp_row[11]))
                    if idemp_row[2] == "Terminated" and not has_recording:
                        print(f"[Upload] Interview #{parsed_interview_id} is Terminated but recording is not yet saved on disk. Proceeding to save recording.")
                    else:
                        print(f"[Idempotency] Interview #{parsed_interview_id} already exists with status '{idemp_row[2]}'. Returning existing evaluation.")
                        idemp_payload = build_idempotent_interview_response(parsed_interview_id, idemp_row, idemp_cur)
                        if client_session_id:
                            IDEMPOTENT_UPLOAD_CACHE[client_session_id] = idemp_payload
                        return idemp_payload
            finally:
                idemp_cur.close()
                idemp_conn.close()

        clean_email = str(user_email).strip() if user_email and str(user_email).strip().lower() not in ("none", "null", "undefined") else None
        if parsed_user_id is None and clean_email:
            try:
                u_conn = get_connection()
                u_cur = u_conn.cursor()
                u_cur.execute("SELECT id FROM Users WHERE email = ?", (clean_email,))
                u_row = u_cur.fetchone()
                if u_row:
                    parsed_user_id = u_row[0]
                else:
                    cand_name = clean_email.split("@")[0].replace(".", " ").title()
                    u_cur.execute("""
                        INSERT INTO Users (name, email, password_hash, is_admin, preferred_role, created_at)
                        OUTPUT INSERTED.id
                        VALUES (?, ?, 'N/A', 0, ?, SYSUTCDATETIME())
                    """, (cand_name, clean_email, role))
                    ins_u = u_cur.fetchone()
                    if ins_u:
                        parsed_user_id = ins_u[0]
                    u_conn.commit()
                u_cur.close()
                u_conn.close()
            except Exception as u_err:
                print(f"[Upload] User association notice: {u_err}")

        # Set user_id variable to parsed integer for SQL insertion
        user_id = parsed_user_id

        # =====================================
        # PARSE QUESTION TIMINGS DATA
        # =====================================
        try:
            question_data_list = json.loads(question_data)
            if not isinstance(question_data_list, list):
                question_data_list = []
        except Exception as err:
            print("[Upload] Error parsing question_data:", err)
            question_data_list = []

        safe_role = "".join(c if c.isalnum() else "_" for c in role)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

        # Resolve recording: direct Amazon S3/R2 object key OR uploaded binary file
        target_object_key = str(recording_key or s3_object_key or r2_object_key or "").strip()
        has_storage_key = bool(target_object_key and target_object_key.lower() not in ("none", "null", "undefined"))
        has_upload_file = bool(recording and hasattr(recording, "file") and recording.file)

        t_save_start = time.time()
        t_save_end = t_save_start

        if has_storage_key:
            from storage_service import verify_object_in_storage, download_file_from_storage
            print(f"\n[Storage Stage: Verification] Verifying uploaded object key in Amazon S3: '{target_object_key}'")
            verification = verify_object_in_storage(target_object_key)
            if not verification.get("exists"):
                err_detail = verification.get("error", "Object not found or is empty in Amazon S3 bucket.")
                print(f"[Storage Stage: Verification Error] {err_detail}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Recording verification failed: '{target_object_key}' was not found in Amazon S3. {err_detail}"
                )

            base_s3_name = os.path.basename(target_object_key)
            filename = base_s3_name if base_s3_name.endswith(".webm") else f"{safe_role}_{timestamp}.webm"
            file_path = os.path.join(UPLOAD_DIR, filename)

            print(f"[Storage Stage: Download] Retrieving recording from S3 to local path '{file_path}' ({verification.get('size_bytes')} bytes)...")
            t_dl_start = time.time()
            dl_ok = download_file_from_storage(target_object_key, file_path)
            t_dl_end = time.time()
            t_save_start = t_dl_start
            t_save_end = t_dl_end

            if not dl_ok or not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                print(f"[Storage Stage: Download Error] Failed to retrieve '{target_object_key}' to {file_path}")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to retrieve recording from persistent cloud storage for AI evaluation."
                )

            file_size_bytes = os.path.getsize(file_path)
            print(f"[Storage Stage: Download Complete] Retrieved {file_size_bytes} bytes in {round(t_dl_end - t_dl_start, 2)}s")

        elif has_upload_file:
            filename = f"{safe_role}_{timestamp}.webm"
            file_path = os.path.join(UPLOAD_DIR, filename)
            t_save_start = time.time()
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(recording.file, buffer)
            t_save_end = time.time()
            file_size_bytes = os.path.getsize(file_path) if os.path.exists(file_path) else 0

            # Mirror recording to Amazon S3 persistent storage if configured
            try:
                from storage_service import upload_file_to_storage
                upload_file_to_storage(file_path, f"recordings/{filename}", content_type="video/webm")
            except Exception as st_err:
                print(f"[Storage Service Notice] Local recording saved; S3 sync notice: {st_err}")

        else:
            # Neither S3 key nor file provided - allow only if terminated interview
            filename = f"{safe_role}_{timestamp}.webm"
            file_path = os.path.join(UPLOAD_DIR, filename)
            file_size_bytes = 0
            if not (tab_switch_count or terminated_reason or termination_type or (interview_status and interview_status.lower() == "terminated")):
                print("[Storage Stage Error] Neither 'recording' file nor 'recording_key' provided in request.")
                raise HTTPException(
                    status_code=400,
                    detail="Recording required: Either 'recording' binary file or 'recording_key' from Amazon S3 must be provided."
                )

        print("\n" + "=" * 60)
        print(f"INTERVIEW RECORDING RECEIVED & SAVED ({round(t_save_end - t_save_start, 3)}s)")
        print(f"Role: {role}")
        print(f"File: {file_path} ({file_size_bytes} bytes)")
        if parsed_interview_id:
            print(f"Interview ID: Session #{parsed_interview_id} (Reusing existing record)")
        else:
            print("Interview ID: New Session (Auto-assigned upon completion)")
        print(f"Total Questions: {total_questions} | Attempted: {attempted_questions} | Answered: {answered_questions}")
        print("=" * 60)

        # Check if client explicitly requests a normal completion
        client_says_completed = (
            (interview_status and str(interview_status).upper() == "COMPLETED") and
            int(tab_switch_count or 0) == 0 and
            (not termination_type or str(termination_type).upper() != "TAB_SWITCH") and
            (not terminated_reason or "tab switch" not in str(terminated_reason).lower())
        )

        # Check if existing interview in DB is already Terminated
        is_already_terminated = False
        if parsed_interview_id is not None:
            c_check = get_connection()
            cur_check = c_check.cursor()
            try:
                cur_check.execute("SELECT status FROM Interviews WHERE id = ?", (parsed_interview_id,))
                row_check = cur_check.fetchone()
                if row_check and str(row_check[0]).lower() == "terminated":
                    is_already_terminated = True
            finally:
                cur_check.close()
                c_check.close()

        # If client explicitly completed normally, do not let stale terminated DB row hijack it
        if client_says_completed:
            if is_already_terminated:
                print(f"[Upload] Client requested normal completion but parsed_interview_id #{parsed_interview_id} was already terminated. Creating fresh completed interview.")
                parsed_interview_id = None
            is_already_terminated = False

        # Strict Tab Switch Policy Detection
        is_tab_switch = (
            not client_says_completed and (
                is_already_terminated or
                int(tab_switch_count or 0) > 0 or
                (terminated_reason and "tab switch" in str(terminated_reason).lower()) or
                (termination_type and str(termination_type).upper() == "TAB_SWITCH") or
                (interview_status and str(interview_status).lower() == "terminated")
            )
        )

        terminated_at_dt = None
        if terminated_at:
            try:
                clean_t = str(terminated_at).replace("Z", "+00:00")
                terminated_at_dt = datetime.fromisoformat(clean_t)
            except Exception:
                terminated_at_dt = datetime.utcnow()

        if is_tab_switch:
            tab_switch_count = 1
            terminated_reason = "Tab Switch Detected"
            termination_type = "TAB_SWITCH"
            is_sec_violation = True
            interview_status = "Terminated"
            if not terminated_at_dt:
                terminated_at_dt = datetime.utcnow()

            question_answers = []
            if question_data_list:
                for idx, q_item in enumerate(question_data_list):
                    q_num = q_item.get("question_number", idx + 1)
                    q_text = q_item.get("question", "")
                    typed_ans = q_item.get("candidate_answer", "").strip()
                    is_ans = bool(typed_ans)
                    question_answers.append({
                        "question_number": q_num,
                        "question": q_text,
                        "candidate_answer": typed_ans,
                        "is_answered": is_ans,
                        "status": "answered" if is_ans else "not_answered",
                        "relative_start": q_item.get("relative_start"),
                        "relative_end": q_item.get("relative_end"),
                        "expected_concepts": [],
                        "matched_concepts": [],
                        "missing_concepts": [],
                        "feedback": "AI evaluation was not generated because this interview was automatically terminated due to a security violation."
                    })
            else:
                question_answers = [{
                    "question_number": 1,
                    "question": "Interview Question",
                    "candidate_answer": "",
                    "is_answered": False,
                    "status": "not_answered",
                    "feedback": "AI evaluation was not generated because this interview was automatically terminated due to a security violation."
                }]

            duration_seconds = 0.0
            for q_ans in question_answers:
                q_end = q_ans.get("relative_end")
                if q_end is not None:
                    try:
                        duration_seconds = max(duration_seconds, float(q_end))
                    except (ValueError, TypeError):
                        pass
            duration_seconds = round(duration_seconds, 3)

            total_attempted = len(question_answers)
            total_answered = sum(1 for q in question_answers if q.get("is_answered"))
            total_unanswered = max(0, total_attempted - total_answered)

            interview_id = save_interview_record(
                role=role,
                total_questions=total_attempted,
                recording_path=file_path,
                transcript="",
                tab_switch_count=1,
                terminated_reason="Tab Switch Detected",
                evaluation={},
                question_data_list=question_answers,
                language="en",
                filename=filename,
                interview_id=parsed_interview_id,
                user_id=parsed_user_id,
                termination_type="TAB_SWITCH",
                security_violation=True,
                terminated_at=terminated_at_dt,
                status="Terminated"
            )

            response_payload = {
                "status": "success",
                "message": "Interview terminated due to tab switch violation. Recording preserved.",
                "interview_id": interview_id,
                "role": role,
                "filename": filename,
                "recording_path": file_path,
                "recording_url": f"/interview/{interview_id}/recording",
                "recording_available": True,
                "duration_seconds": duration_seconds,
                "transcript": "",
                "language": "en",
                "total_questions": total_attempted,
                "attempted_questions": total_attempted,
                "answered_questions": total_answered,
                "unanswered_questions": total_unanswered,
                "tab_switch_count": 1,
                "terminated_reason": "Tab Switch Detected",
                "interview_status": "Terminated",
                "termination_type": "TAB_SWITCH",
                "security_violation": True,
                "terminated_at": terminated_at_dt.isoformat() if terminated_at_dt else None,
                "overall_score": None,
                "evaluation": None,
                "question_answers": question_answers
            }
            if client_session_id:
                IDEMPOTENT_UPLOAD_CACHE[client_session_id] = response_payload
            print(f"[Upload] Tab switch termination handled cleanly for interview #{interview_id}. Evaluation bypassed.")
            return response_payload

        # Normal Interview Completion
        interview_status = "COMPLETED"
        is_sec_violation = False
        termination_type = None
        terminated_reason = None
        tab_switch_count = 0
        terminated_at_dt = None

        is_async_requested = (async_mode is not None and str(async_mode).lower() in ("true", "1", "yes"))

        if is_async_requested:
            job_id = f"job_{uuid.uuid4().hex[:12]}"
            if client_session_id:
                SESSION_ACTIVE_JOBS[client_session_id] = job_id
            SUBMISSION_JOBS[job_id] = {
                "job_id": job_id,
                "status": "processing",
                "stage": "transcribing",
                "progress": 25,
                "message": "Recording uploaded and verified. Transcribing audio...",
                "interview_id": parsed_interview_id,
                "error_message": None,
                "created_at": datetime.utcnow().isoformat()
            }

            def _bg_worker():
                try:
                    execute_submission_pipeline(
                        file_path=file_path,
                        filename=filename,
                        role=role,
                        total_questions=total_questions,
                        attempted_questions=attempted_questions,
                        answered_questions=answered_questions,
                        unanswered_questions=unanswered_questions,
                        question_data_list=question_data_list,
                        recording_start_time=recording_start_time,
                        parsed_interview_id=parsed_interview_id,
                        parsed_user_id=parsed_user_id,
                        client_session_id=client_session_id,
                        interview_status=interview_status,
                        tab_switch_count=tab_switch_count,
                        is_sec_violation=is_sec_violation,
                        termination_type=termination_type,
                        terminated_reason=terminated_reason,
                        terminated_at_dt=terminated_at_dt,
                        job_id=job_id,
                        raw_candidate_name=candidate_name
                    )
                except Exception as bg_err:
                    print(f"[Submission Pipeline Background Exception] {bg_err}")
                    if job_id in SUBMISSION_JOBS:
                        SUBMISSION_JOBS[job_id]["status"] = "failed"
                        SUBMISSION_JOBS[job_id]["stage"] = "error"
                        SUBMISSION_JOBS[job_id]["error_message"] = str(bg_err)

            threading.Thread(target=_bg_worker, daemon=True).start()

            print(f"[Upload] Dispatched asynchronous submission job: {job_id}")
            return {
                "status": "processing",
                "job_id": job_id,
                "stage": "transcribing",
                "progress": 25,
                "message": "Recording uploaded and saved safely. Transcribing audio...",
                "interview_id": parsed_interview_id
            }

        # Synchronous execution (preserves exact behavior for automated test suites)
        return execute_submission_pipeline(
            file_path=file_path,
            filename=filename,
            role=role,
            total_questions=total_questions,
            attempted_questions=attempted_questions,
            answered_questions=answered_questions,
            unanswered_questions=unanswered_questions,
            question_data_list=question_data_list,
            recording_start_time=recording_start_time,
            parsed_interview_id=parsed_interview_id,
            parsed_user_id=parsed_user_id,
            client_session_id=client_session_id,
            interview_status=interview_status,
            tab_switch_count=tab_switch_count,
            is_sec_violation=is_sec_violation,
            termination_type=termination_type,
            terminated_reason=terminated_reason,
            terminated_at_dt=terminated_at_dt,
            job_id=None,
            raw_candidate_name=candidate_name
        )

    except HTTPException:
        raise
    except Exception as error:
        print("\n" + "=" * 50)
        print("CRITICAL UPLOAD/EVALUATION ERROR:")
        print(error)
        print("=" * 50 + "\n")

        return {
            "status": "error",
            "message": str(error)
        }


# =========================================
# ASYNC SUBMISSION STATUS POLLING ENDPOINT
# =========================================

@app.get("/interview/submission/{job_id}/status")
@app.get("/api/interview/submission/{job_id}/status")
async def get_submission_status(job_id: str, x_api_key: str = Header(None)):
    """
    Returns live progress and results for staged interview submissions.
    Stages:
      - 'transcribing': Audio STT in progress
      - 'evaluating': Concept matching & scoring
      - 'persisting': SQL database persistence
      - 'completed': Final result ready
      - 'failed': An error occurred during evaluation
    """
    if x_api_key is not None and x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    clean_jid = str(job_id).strip()
    job = SUBMISSION_JOBS.get(clean_jid)
    if not job:
        raise HTTPException(
            status_code=404,
            detail="Submission job not found"
        )

    return {
        "job_id": clean_jid,
        "status": job.get("status", "processing"),
        "stage": job.get("stage", "transcribing"),
        "message": job.get("message", "Processing interview recording..."),
        "progress": job.get("progress", 0),
        "interview_id": job.get("interview_id"),
        "error_message": job.get("error_message"),
        "result": job.get("result") if job.get("status") == "completed" else None
    }


# =========================================
# IDEMPOTENT TERMINATION ENDPOINT
# =========================================

@app.post("/interview/terminate")
async def terminate_interview_endpoint(
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """
    Authoritative and idempotent interview termination endpoint.
    Accepts JSON or Form data.
    Sets status = 'Terminated' and ensures no AI evaluation or scores remain.
    """
    if x_api_key is not None and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    content_type = request.headers.get("content-type", "")
    data = {}
    if "application/json" in content_type:
        try:
            data = await request.json()
        except Exception:
            data = {}
    else:
        try:
            form = await request.form()
            data = dict(form)
        except Exception:
            data = {}

    interview_id_raw = data.get("interview_id")
    resolved_id = None
    if interview_id_raw is not None:
        try:
            c_id = str(interview_id_raw).strip()
            if c_id and c_id.lower() not in ("none", "null", "undefined"):
                resolved_id = int(c_id)
        except Exception:
            resolved_id = None

    role = str(data.get("role") or "Developer").strip()
    total_questions = 20
    try:
        total_questions = int(data.get("total_questions", 20))
    except Exception:
        total_questions = 20

    termination_type = str(data.get("termination_type") or "TAB_SWITCH").strip()
    termination_reason = str(data.get("termination_reason") or data.get("terminated_reason") or "Tab Switch Detected").strip()
    tab_switch_count = 1
    try:
        tab_switch_count = int(data.get("tab_switch_count", 1))
    except Exception:
        tab_switch_count = 1

    sec_viol_raw = data.get("security_violation", True)
    security_violation = str(sec_viol_raw).lower() in ("true", "1", "yes") if sec_viol_raw is not None else True
    user_id = data.get("user_id")
    user_email = data.get("user_email")

    conn = get_connection()
    cur = conn.cursor()
    try:
        if resolved_id is not None:
            cur.execute("""
                SELECT id, status, termination_type, terminated_reason, tab_switch_count, security_violation, terminated_at
                FROM Interviews
                WHERE id = ?
            """, (resolved_id,))
            row = cur.fetchone()
            if row:
                if row[1] == "Terminated":
                    return {
                        "success": True,
                        "status": "Terminated",
                        "interview_id": row[0],
                        "interview_status": "Terminated",
                        "termination_type": row[2] or "TAB_SWITCH",
                        "terminated_reason": row[3] or "Tab Switch Detected",
                        "termination_reason": row[3] or "Tab Switch Detected",
                        "tab_switch_count": row[4] or 1,
                        "security_violation": bool(row[5]),
                        "terminated_at": row[6].isoformat() if row[6] else None
                    }
                cur.execute("""
                    UPDATE Interviews
                    SET status = 'Terminated',
                        termination_type = ?,
                        terminated_reason = ?,
                        tab_switch_count = ?,
                        security_violation = ?,
                        terminated_at = SYSUTCDATETIME(),
                        overall_score = NULL,
                        technical_score = NULL,
                        communication_score = NULL,
                        confidence_score = NULL,
                        problem_solving_score = NULL,
                        relevance_score = NULL,
                        feedback = NULL
                    WHERE id = ?
                """, (termination_type, termination_reason, tab_switch_count, 1 if security_violation else 0, resolved_id))
                cur.execute("DELETE FROM EvaluationResults WHERE interview_id = ?", (resolved_id,))
                cur.execute("DELETE FROM Feedback WHERE interview_id = ?", (resolved_id,))
                cur.execute("""
                    UPDATE InterviewAnswers
                    SET technical_score = NULL, communication_score = NULL, confidence_score = NULL,
                        problem_solving_score = NULL, relevance_score = NULL, completeness_score = NULL,
                        overall_answer_score = NULL, semantic_similarity = NULL,
                        feedback = 'AI evaluation was not generated because this interview was terminated due to a security violation.'
                    WHERE interview_id = ?
                """, (resolved_id,))
                conn.commit()
                return {
                    "success": True,
                    "status": "Terminated",
                    "interview_id": resolved_id,
                    "interview_status": "Terminated",
                    "termination_type": termination_type,
                    "terminated_reason": termination_reason,
                    "termination_reason": termination_reason,
                    "tab_switch_count": tab_switch_count,
                    "security_violation": bool(security_violation),
                    "terminated_at": datetime.utcnow().isoformat()
                }

        # If interview_id is not provided, create a new terminated interview row immediately
        parsed_uid = None
        if user_id:
            try:
                parsed_uid = int(str(user_id).strip())
            except Exception:
                parsed_uid = None
        if not parsed_uid and user_email:
            try:
                cur.execute("SELECT id FROM Users WHERE email = ?", (str(user_email).strip(),))
                u_row = cur.fetchone()
                if u_row:
                    parsed_uid = u_row[0]
            except Exception:
                parsed_uid = None

        cur.execute("""
            INSERT INTO Interviews
            (
                role, total_questions, status, termination_type, terminated_reason,
                tab_switch_count, security_violation, terminated_at, overall_score,
                user_id, completed_at, evaluation_method
            )
            OUTPUT INSERTED.id
            VALUES (?, ?, 'Terminated', ?, ?, ?, ?, SYSUTCDATETIME(), NULL, ?, SYSUTCDATETIME(), 'timeline+semantic')
        """, (
            role or "Developer",
            total_questions,
            termination_type,
            termination_reason,
            tab_switch_count,
            1 if security_violation else 0,
            parsed_uid
        ))
        new_row = cur.fetchone()
        new_id = new_row[0] if new_row else None
        conn.commit()

        return {
            "success": True,
            "status": "Terminated",
            "interview_id": new_id,
            "interview_status": "Terminated",
            "termination_type": termination_type,
            "terminated_reason": termination_reason,
            "termination_reason": termination_reason,
            "tab_switch_count": tab_switch_count,
            "security_violation": bool(security_violation),
            "terminated_at": datetime.utcnow().isoformat()
        }
    finally:
        cur.close()
        conn.close()


# =========================================
# GET INTERVIEW DETAILS API
# =========================================

@app.get("/interview/{interview_id}")
def get_interview(interview_id: int):
    """
    Retrieves complete interview details from SQL Server:
    - Interviews metadata
    - InterviewAnswers question-by-question breakdown
    - EvaluationResults
    - InterviewHistory
    - Feedback
    """
    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM Interviews WHERE id = ?", (interview_id,))
        int_desc = [c[0] for c in cursor.description]
        int_row = cursor.fetchone()
        if not int_row:
            cursor.close()
            connection.close()
            raise HTTPException(status_code=404, detail=f"Interview {interview_id} not found")

        interview_dict = dict(zip(int_desc, int_row))

        cursor.execute("""
            SELECT * FROM InterviewAnswers
            WHERE interview_id = ?
            ORDER BY question_number
        """, (interview_id,))
        ans_desc = [c[0] for c in cursor.description]
        answers_list = [dict(zip(ans_desc, r)) for r in cursor.fetchall()]

        # Enrich answers with expected_concepts, concept_score, and concept_coverage_score
        interview_role = interview_dict.get("role")
        for a in answers_list:
            q_id = a.get("question_id")
            q_text = a.get("question_text") or ""
            exp_concepts = []

            if q_id:
                try:
                    cursor.execute("SELECT expected_topics FROM Questions WHERE id = ?", (q_id,))
                    q_row = cursor.fetchone()
                    if q_row and q_row[0] and str(q_row[0]).strip():
                        exp_concepts = [t.strip() for t in str(q_row[0]).split(",") if t.strip()]
                except Exception:
                    pass

            if not exp_concepts and q_text:
                try:
                    exp_concepts = get_expected_concepts(q_text, role=interview_role)
                except Exception:
                    exp_concepts = []

            matched = []
            missing = []
            try:
                matched = json.loads(a.get("matched_concepts") or "[]")
            except Exception:
                matched = []
            try:
                missing = json.loads(a.get("missing_concepts") or "[]")
            except Exception:
                missing = []

            # If expected_concepts is still empty, reconstruct from evaluated matched + missing
            if not exp_concepts and (matched or missing):
                exp_concepts = list(dict.fromkeys(matched + missing))

            a["expected_concepts"] = exp_concepts

            has_ans = bool(a.get("answer_text") and str(a.get("answer_text")).strip())
            if not has_ans:
                a["concept_score"] = 0.0
                a["concept_coverage_score"] = 0.0
                if not missing and exp_concepts:
                    a["missing_concepts"] = json.dumps(exp_concepts)
            elif exp_concepts:
                a["concept_score"] = round((len(matched) / len(exp_concepts)) * 100.0, 2)
                a["concept_coverage_score"] = a["concept_score"]
            else:
                a["concept_score"] = None
                a["concept_coverage_score"] = None

        cursor.execute("SELECT * FROM EvaluationResults WHERE interview_id = ?", (interview_id,))
        eval_desc = [c[0] for c in cursor.description]
        eval_row = cursor.fetchone()
        eval_dict = dict(zip(eval_desc, eval_row)) if eval_row else None

        hist_dict = None
        try:
            cursor.execute("SELECT * FROM InterviewHistory WHERE interview_id = ?", (interview_id,))
            hist_desc = [c[0] for c in cursor.description]
            hist_row = cursor.fetchone()
            hist_dict = dict(zip(hist_desc, hist_row)) if hist_row else None
        except Exception as hist_err:
            print(f"[Interview Summary Notice] InterviewHistory fetch notice: {hist_err}")

        cursor.execute("SELECT * FROM Feedback WHERE interview_id = ?", (interview_id,))
        fb_desc = [c[0] for c in cursor.description]
        fb_row = cursor.fetchone()
        fb_dict = dict(zip(fb_desc, fb_row)) if fb_row else None

        cursor.close()
        connection.close()

        # Strict Tab Switch Policy Sanitization for Terminated Interviews
        is_term = str(interview_dict.get("status", "")).lower() == "terminated"
        if is_term:
            eval_dict = None
            fb_dict = None
            interview_dict["overall_score"] = None
            interview_dict["technical_score"] = None
            interview_dict["communication_score"] = None
            interview_dict["confidence_score"] = None
            interview_dict["problem_solving_score"] = None
            interview_dict["relevance_score"] = None
            interview_dict["feedback"] = None
            for a in answers_list:
                a["technical_score"] = None
                a["communication_score"] = None
                a["confidence_score"] = None
                a["problem_solving_score"] = None
                a["relevance_score"] = None
                a["completeness_score"] = None
                a["overall_answer_score"] = None
                a["concept_score"] = None
                a["concept_coverage_score"] = None
                a["matched_concepts"] = "[]"
                a["missing_concepts"] = "[]"
                a["strengths"] = "[]"
                a["weaknesses"] = "[]"
                a["feedback"] = "AI evaluation was not generated because this interview was terminated due to a security violation."

        rec_path = interview_dict.get("recording_path")
        rec_fname = interview_dict.get("recording_filename")
        is_rec_available = False
        valid_rec_url = None
        if rec_path and os.path.exists(rec_path) and os.path.getsize(rec_path) > 0:
            is_rec_available = True
            valid_rec_url = f"/interview/{interview_id}/recording"
        elif rec_fname:
            cand_p = os.path.join(UPLOAD_DIR, rec_fname)
            if os.path.exists(cand_p) and os.path.getsize(cand_p) > 0:
                is_rec_available = True
                valid_rec_url = f"/uploads/{rec_fname}"

        interview_dict["recording_available"] = is_rec_available
        interview_dict["recording_url"] = valid_rec_url
        interview_dict["termination_reason"] = interview_dict.get("terminated_reason") or ""
        interview_dict["security_violation"] = bool(interview_dict.get("security_violation")) if interview_dict.get("security_violation") is not None else False

        return {
            "status": "success",
            "interview": interview_dict,
            "answers": answers_list,
            "evaluation": eval_dict,
            "history": hist_dict,
            "feedback": fb_dict,
            "recording_available": is_rec_available,
            "recording_url": valid_rec_url
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================================
# INTERVIEW RECORDING SERVING ENDPOINT
# =========================================

@app.get("/interview/{interview_id}/recording")
@app.get("/api/interview/{interview_id}/recording")
def get_interview_recording(interview_id: int):
    """
    Directly streams or serves the saved interview recording WebM file.
    If local file was wiped by container restart, transparently redirects to Cloudflare R2 secure access URL.
    Works for both completed and terminated interviews.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT recording_path, recording_filename FROM Interviews WHERE id = ?", (interview_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Interview not found")
        rec_path, rec_fname = row[0], row[1]
        target_path = None
        if rec_path and os.path.exists(rec_path) and os.path.getsize(rec_path) > 0:
            target_path = rec_path
        elif rec_fname:
            cand_path = os.path.join(UPLOAD_DIR, rec_fname)
            if os.path.exists(cand_path) and os.path.getsize(cand_path) > 0:
                target_path = cand_path
        if not target_path:
            # Check Amazon S3 persistent storage
            try:
                from storage_service import is_s3_configured, get_recording_access_url
                if is_s3_configured():
                    candidate_keys = []
                    if rec_fname:
                        candidate_keys.extend([f"recordings/{rec_fname}", rec_fname])
                    if rec_path:
                        base = os.path.basename(rec_path)
                        candidate_keys.extend([f"recordings/{base}", base])
                    for s3_k in candidate_keys:
                        s3_url = get_recording_access_url(s3_k)
                        if s3_url:
                            print(f"[Recording Serving] Redirecting interview #{interview_id} playback to Amazon S3: {s3_k}")
                            return RedirectResponse(url=s3_url, status_code=307)
            except Exception as s3_redir_err:
                print(f"[Recording Serving Warning] S3 redirect notice for interview #{interview_id}: {s3_redir_err}")
            raise HTTPException(status_code=404, detail="Recording unavailable")
        return FileResponse(
            target_path,
            media_type="video/webm",
            filename=rec_fname or f"interview_{interview_id}.webm"
        )
    finally:
        cur.close()
        conn.close()


# =========================================
# DOWNLOADABLE PDF INTERVIEW REPORT ENDPOINT
# =========================================

@app.get("/api/interview/{interview_id}/report/pdf")
@app.get("/interview/{interview_id}/report/pdf")
def download_interview_report_pdf(
    interview_id: int,
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None)
):
    """
    Generates and downloads a professional server-side PDF interview report.
    Enforces authentication and strict candidate ownership verification.
    """
    # 1. Authenticate user
    current_user = get_user_from_auth(authorization=authorization, token=token)

    # 2. Fetch interview data (raises 404 if interview does not exist)
    interview_data = get_interview(interview_id)
    interview_dict = interview_data.get("interview", {}) or {}

    # 3. Ownership / Authorization Check
    # Candidate can ONLY access their own interview; admins can access any
    int_user_id = interview_dict.get("user_id")
    is_owner = (int_user_id is not None and int(int_user_id) == int(current_user["id"]))
    is_admin = bool(current_user.get("is_admin"))

    if not is_owner and not is_admin:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You do not have permission to access another candidate's interview report."
        )

    # 4. Resolve Candidate User Information (Name, Email)
    candidate_user = None
    if int_user_id:
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, name, email FROM Users WHERE id = ?", (int_user_id,))
            u_row = cur.fetchone()
            if u_row:
                candidate_user = {"id": u_row[0], "name": u_row[1], "email": u_row[2]}
        finally:
            cur.close()
            conn.close()

    if not candidate_user:
        candidate_user = {
            "id": current_user["id"],
            "name": current_user.get("name") or "Interview Candidate",
            "email": current_user.get("email") or ""
        }

    # 5. Generate PDF bytes
    try:
        pdf_bytes = generate_interview_report_pdf(interview_data, candidate_user)
    except Exception as exc:
        print(f"[PDF Generation Error] Interview {interview_id}: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Unable to generate the interview report. Please try again."
        )

    # 6. Stream attachment response
    filename = f"AI_Interview_Report_{interview_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )