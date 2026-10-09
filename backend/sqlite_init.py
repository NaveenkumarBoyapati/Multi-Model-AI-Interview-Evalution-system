"""
SQLite Production Initialization & Schema Management Module.
Automatically provisions tables, default roles, admin account, and curated questions
when running in zero-dependency SQLite mode (Docker / Cloud / Local).
"""

import os
import sys
import sqlite3
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "interview_system.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0,
    preferred_role TEXT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    description TEXT NULL,
    topics TEXT NULL,
    icon TEXT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT NOT NULL,
    category TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    question_text TEXT NOT NULL,
    expected_topics TEXT NULL,
    reference_answer TEXT NULL,
    evaluation_guidance TEXT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Interviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    total_questions INTEGER DEFAULT 20,
    recording_path TEXT NULL,
    technical_score REAL DEFAULT 0,
    communication_score REAL DEFAULT 0,
    confidence_score REAL DEFAULT 0,
    problem_solving_score REAL DEFAULT 0,
    overall_score REAL DEFAULT 0,
    feedback TEXT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    transcript TEXT NULL,
    tab_switch_count INTEGER NOT NULL DEFAULT 0,
    terminated_reason TEXT NULL,
    user_id INTEGER NULL,
    status TEXT NULL,
    relevance_score REAL NULL,
    duration_seconds REAL NULL,
    transcript_language TEXT NULL,
    recording_filename TEXT NULL,
    evaluation_method TEXT NULL,
    completed_at TEXT NULL,
    question_timeline TEXT NULL,
    termination_type TEXT NULL,
    security_violation INTEGER NULL,
    terminated_at TEXT NULL
);

CREATE TABLE IF NOT EXISTS InterviewAnswers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    interview_id INTEGER NOT NULL,
    question_id INTEGER NULL,
    question_number INTEGER NOT NULL,
    question_text TEXT NULL,
    category TEXT NULL,
    difficulty TEXT NULL,
    start_ms INTEGER NULL,
    end_ms INTEGER NULL,
    answer_text TEXT NULL,
    word_count INTEGER NULL,
    speech_duration_seconds REAL NULL,
    technical_score REAL NULL,
    communication_score REAL NULL,
    confidence_score REAL NULL,
    problem_solving_score REAL NULL,
    relevance_score REAL NULL,
    completeness_score REAL NULL,
    overall_answer_score REAL NULL,
    semantic_similarity REAL NULL,
    matched_concepts TEXT NULL,
    missing_concepts TEXT NULL,
    strengths TEXT NULL,
    weaknesses TEXT NULL,
    feedback TEXT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS EvaluationResults (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    interview_id INTEGER NOT NULL,
    technical_score REAL NULL,
    communication_score REAL NULL,
    confidence_score REAL NULL,
    problem_solving_score REAL NULL,
    relevance_score REAL NULL,
    overall_score REAL NULL,
    answers_evaluated INTEGER NULL,
    answered_count INTEGER NULL,
    technical_coverage REAL NULL,
    strengths TEXT NULL,
    weaknesses TEXT NULL,
    recommendations TEXT NULL,
    evaluation_method TEXT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS Feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    interview_id INTEGER NOT NULL,
    overall_performance TEXT NULL,
    strengths TEXT NULL,
    weaknesses TEXT NULL,
    areas_to_improve TEXT NULL,
    technical_suggestions TEXT NULL,
    communication_suggestions TEXT NULL,
    confidence_suggestions TEXT NULL,
    problem_solving_suggestions TEXT NULL,
    practice_areas TEXT NULL,
    summary TEXT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS InterviewHistory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    interview_id INTEGER NOT NULL,
    user_id INTEGER NULL,
    role TEXT NULL,
    attempt_number INTEGER NULL,
    overall_score REAL NULL,
    technical_score REAL NULL,
    communication_score REAL NULL,
    confidence_score REAL NULL,
    problem_solving_score REAL NULL,
    relevance_score REAL NULL,
    completed_at TEXT NULL
);

CREATE TABLE IF NOT EXISTS PasswordResets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    used_at TEXT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS UserTokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS AdminAuditLogs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id INTEGER NULL,
    admin_name TEXT NULL,
    admin_email TEXT NULL,
    action TEXT NOT NULL,
    target_type TEXT NULL,
    target_id TEXT NULL,
    result TEXT NOT NULL DEFAULT 'SUCCESS',
    details TEXT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

DEFAULT_ROLES = [
    ("Python Developer", "python-developer", "Python, OOP, REST APIs, Backend Frameworks", "Python, Django, Flask, FastAPI, OOP, SQL", "code", 1),
    ("Java Developer", "java-developer", "Java, Spring Boot, OOP, Multithreading", "Java, Spring Boot, Hibernate, OOP, Multithreading, SQL", "coffee", 1),
    ("Data Analyst", "data-analyst", "Data Cleaning, SQL, Power BI, Excel, Tableau", "SQL, Python, Excel, Power BI, Tableau, Statistics", "bar-chart", 1),
    ("Web Developer", "web-developer", "Frontend & Fullstack Web Development", "HTML5, CSS3, JavaScript, React, APIs, Responsive Design", "globe", 1)
]

def init_sqlite_db(db_path=SQLITE_DB_PATH):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    cur = conn.cursor()
    cur.executescript(SCHEMA_SQL)

    # 1. Seed default roles
    for r in DEFAULT_ROLES:
        cur.execute("SELECT id FROM Roles WHERE slug = ?", (r[1],))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO Roles (role_name, slug, description, topics, icon, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            """, r)
    conn.commit()

    # 2. Ensure default super admin account
    try:
        from auth_utils import hash_password
        cur.execute("SELECT id FROM Users WHERE email = ?", ("admin@ai-interview.com",))
        if not cur.fetchone():
            pwd_hash = hash_password("Admin@Interview2026!")
            cur.execute("""
                INSERT INTO Users (name, email, password_hash, is_admin, preferred_role, is_active)
                VALUES (?, ?, ?, 1, 'System Administrator', 1)
            """, ("System Administrator", "admin@ai-interview.com", pwd_hash))
            conn.commit()
            print("[SQLite Init] Default admin account seeded: admin@ai-interview.com")
    except Exception as exc:
        print(f"[SQLite Init] Notice: Could not seed admin: {exc}")

    # 3. Seed curated questions if table is empty
    try:
        cur.execute("SELECT COUNT(*) FROM Questions")
        q_count = cur.fetchone()[0]
        if q_count == 0:
            from populate_all_curated_questions import CURATED_ALL_ROLE_QUESTIONS
            inserted = 0
            for q_text, concepts in CURATED_ALL_ROLE_QUESTIONS.items():
                topics_str = ", ".join(concepts)
                clean_q = " ".join(q_text.strip().split())
                q_role = "Data Analyst"
                if any(term in clean_q for term in ["python", "django", "flask", "fastapi", "mro", "lambda", "yield", "args"]):
                    q_role = "Python Developer"
                elif any(term in clean_q for term in ["java", "jvm", "jdk", "jre", "hashmap", "arraylist", "maven", "jdbc", "stringbuilder"]):
                    q_role = "Java Developer"
                elif any(term in clean_q for term in ["html", "css", "dom", "cors", "flexbox", "grid", "react", "spa", "javascript", "browser"]):
                    q_role = "Web Developer"

                cur.execute("""
                    INSERT INTO Questions (role_name, category, difficulty, question_text, expected_topics, reference_answer, evaluation_guidance)
                    VALUES (?, 'Technical', 'Easy', ?, ?, '', '')
                """, (q_role, clean_q, topics_str))
                inserted += 1
            conn.commit()
            print(f"[SQLite Init] Seeded {inserted} curated interview questions across all 4 roles.")
    except Exception as exc:
        print(f"[SQLite Init] Notice: Questions seeding: {exc}")

    cur.close()
    conn.close()
    print("[SQLite Init] Database fully ready and synchronized.")

if __name__ == "__main__":
    init_sqlite_db()
