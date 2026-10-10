"""
PostgreSQL / Neon Production Initialization & Schema Management Module.
Provisions tables, sequences, default roles, admin account, and curated questions
when connecting to Neon Serverless PostgreSQL or any standard PostgreSQL instance.
"""

import os
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from env_loader import load_env
load_env()

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

SCHEMA_POSTGRES_SQL = """
CREATE TABLE IF NOT EXISTS Users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(200) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_admin INT NOT NULL DEFAULT 0,
    preferred_role VARCHAR(100) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    is_active INT NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Roles (
    id SERIAL PRIMARY KEY,
    role_name VARCHAR(100) NOT NULL,
    slug VARCHAR(80) NOT NULL UNIQUE,
    description TEXT NULL,
    topics TEXT NULL,
    icon VARCHAR(60) NULL,
    is_active INT NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Questions (
    id SERIAL PRIMARY KEY,
    role_name VARCHAR(100) NOT NULL,
    category VARCHAR(40) NOT NULL,
    difficulty VARCHAR(20) NOT NULL,
    question_text TEXT NOT NULL,
    expected_topics TEXT NULL,
    reference_answer TEXT NULL,
    evaluation_guidance TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    is_active INT NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Interviews (
    id SERIAL PRIMARY KEY,
    role VARCHAR(100) NOT NULL,
    total_questions INT DEFAULT 20,
    recording_path TEXT NULL,
    technical_score REAL DEFAULT 0,
    communication_score REAL DEFAULT 0,
    confidence_score REAL DEFAULT 0,
    problem_solving_score REAL DEFAULT 0,
    overall_score REAL DEFAULT 0,
    feedback TEXT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    transcript TEXT NULL,
    tab_switch_count INT NOT NULL DEFAULT 0,
    terminated_reason TEXT NULL,
    user_id INT NULL,
    status VARCHAR(50) NULL,
    relevance_score REAL NULL,
    duration_seconds REAL NULL,
    transcript_language VARCHAR(20) NULL,
    recording_filename VARCHAR(255) NULL,
    evaluation_method VARCHAR(50) NULL,
    completed_at TIMESTAMP NULL,
    question_timeline TEXT NULL,
    termination_type VARCHAR(50) NULL,
    security_violation INT NULL,
    terminated_at TIMESTAMP NULL
);

CREATE TABLE IF NOT EXISTS InterviewAnswers (
    id SERIAL PRIMARY KEY,
    interview_id INT NOT NULL,
    question_id INT NULL,
    question_number INT NOT NULL,
    question_text TEXT NULL,
    category VARCHAR(50) NULL,
    difficulty VARCHAR(50) NULL,
    start_ms INT NULL,
    end_ms INT NULL,
    answer_text TEXT NULL,
    word_count INT NULL,
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
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS EvaluationResults (
    id SERIAL PRIMARY KEY,
    interview_id INT NOT NULL,
    technical_score REAL NULL,
    communication_score REAL NULL,
    confidence_score REAL NULL,
    problem_solving_score REAL NULL,
    relevance_score REAL NULL,
    overall_score REAL NULL,
    answers_evaluated INT NULL,
    answered_count INT NULL,
    technical_coverage REAL NULL,
    strengths TEXT NULL,
    weaknesses TEXT NULL,
    recommendations TEXT NULL,
    evaluation_method VARCHAR(50) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS Feedback (
    id SERIAL PRIMARY KEY,
    interview_id INT NOT NULL,
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
    overall_score REAL NULL,
    technical_score REAL NULL,
    communication_score REAL NULL,
    confidence_score REAL NULL,
    problem_solving_score REAL NULL,
    relevance_score REAL NULL,
    completed_at TIMESTAMP NULL
);

CREATE TABLE IF NOT EXISTS PasswordResets (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS UserTokens (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    is_active INT NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS AdminAuditLogs (
    id SERIAL PRIMARY KEY,
    admin_id INT NULL,
    admin_name VARCHAR(120) NULL,
    admin_email VARCHAR(200) NULL,
    action VARCHAR(100) NOT NULL,
    target_type VARCHAR(100) NULL,
    target_id VARCHAR(100) NULL,
    result VARCHAR(50) NOT NULL DEFAULT 'SUCCESS',
    details TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- PostgreSQL DATEADD compatibility functions (for SQL Server query compatibility)
CREATE OR REPLACE FUNCTION DATEADD(unit text, amount integer, base_date timestamp with time zone)
RETURNS timestamp with time zone AS $$
BEGIN
    IF lower(unit) IN ('day', 'days', 'd') THEN
        RETURN base_date + (amount || ' days')::interval;
    ELSIF lower(unit) IN ('hour', 'hours', 'hh') THEN
        RETURN base_date + (amount || ' hours')::interval;
    ELSIF lower(unit) IN ('minute', 'minutes', 'mi') THEN
        RETURN base_date + (amount || ' minutes')::interval;
    ELSIF lower(unit) IN ('second', 'seconds', 'ss') THEN
        RETURN base_date + (amount || ' seconds')::interval;
    ELSIF lower(unit) IN ('month', 'months', 'm') THEN
        RETURN base_date + (amount || ' months')::interval;
    ELSIF lower(unit) IN ('year', 'years', 'yy', 'yyyy') THEN
        RETURN base_date + (amount || ' years')::interval;
    ELSE
        RETURN base_date + (amount || ' days')::interval;
    END IF;
END;
$$ LANGUAGE plpgsql STABLE;

CREATE OR REPLACE FUNCTION DATEADD(unit text, amount integer, base_date timestamp without time zone)
RETURNS timestamp without time zone AS $$
BEGIN
    IF lower(unit) IN ('day', 'days', 'd') THEN
        RETURN (base_date + (amount || ' days')::interval)::timestamp;
    ELSIF lower(unit) IN ('hour', 'hours', 'hh') THEN
        RETURN (base_date + (amount || ' hours')::interval)::timestamp;
    ELSIF lower(unit) IN ('minute', 'minutes', 'mi') THEN
        RETURN (base_date + (amount || ' minutes')::interval)::timestamp;
    ELSIF lower(unit) IN ('second', 'seconds', 'ss') THEN
        RETURN (base_date + (amount || ' seconds')::interval)::timestamp;
    ELSIF lower(unit) IN ('month', 'months', 'm') THEN
        RETURN (base_date + (amount || ' months')::interval)::timestamp;
    ELSIF lower(unit) IN ('year', 'years', 'yy', 'yyyy') THEN
        RETURN (base_date + (amount || ' years')::interval)::timestamp;
    ELSE
        RETURN (base_date + (amount || ' days')::interval)::timestamp;
    END IF;
END;
$$ LANGUAGE plpgsql STABLE;
"""

DEFAULT_ROLES = [
    ("Python Developer", "python-developer", "Python, OOP, REST APIs, Backend Frameworks", "Python, Django, Flask, FastAPI, OOP, SQL", "code", 1),
    ("Java Developer", "java-developer", "Java, Spring Boot, OOP, Multithreading", "Java, Spring Boot, Hibernate, OOP, Multithreading, SQL", "coffee", 1),
    ("Data Analyst", "data-analyst", "Data Cleaning, SQL, Power BI, Excel, Tableau", "SQL, Python, Excel, Power BI, Tableau, Statistics", "bar-chart", 1),
    ("Web Developer", "web-developer", "Frontend & Fullstack Web Development", "HTML5, CSS3, JavaScript, React, APIs, Responsive Design", "globe", 1)
]


def init_postgres_db(connection_url: str = None) -> bool:
    """
    Initializes PostgreSQL / Neon schema, default roles, default admin, and curated questions.
    Returns True if successfully connected and initialized, False otherwise.
    """
    target_url = (connection_url or DATABASE_URL).strip()
    if not target_url:
        print("[Neon Init] No DATABASE_URL provided. Skipping PostgreSQL initialization.")
        return False

    try:
        import psycopg2
    except ImportError:
        print("[Neon Init Warning] psycopg2 is not installed. Please install psycopg2-binary.")
        return False

    print(f"[Neon Init] Connecting to PostgreSQL database...")
    try:
        conn = psycopg2.connect(target_url)
        conn.autocommit = True
        cur = conn.cursor()

        # 1. Execute schema creation
        cur.execute(SCHEMA_POSTGRES_SQL)
        print("[Neon Init] Core tables verified/created successfully.")

        # 2. Seed default roles
        for r in DEFAULT_ROLES:
            cur.execute("SELECT id FROM Roles WHERE slug = %s", (r[1],))
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO Roles (role_name, slug, description, topics, icon, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, r)
        print("[Neon Init] Default roles verified.")

        # 3. Seed default super admin
        try:
            from auth_utils import hash_password
            cur.execute("SELECT id FROM Users WHERE email = %s", ("admin@ai-interview.com",))
            if not cur.fetchone():
                pwd_hash = hash_password("Admin@Interview2026!")
                cur.execute("""
                    INSERT INTO Users (name, email, password_hash, is_admin, preferred_role, is_active)
                    VALUES (%s, %s, %s, 1, 'System Administrator', 1)
                """, ("System Administrator", "admin@ai-interview.com", pwd_hash))
                print("[Neon Init] Default admin seeded: admin@ai-interview.com")
        except Exception as admin_err:
            print(f"[Neon Init] Notice: Admin seeding check: {admin_err}")

        # 4. Seed curated questions if empty
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
                        VALUES (%s, 'Technical', 'Easy', %s, %s, '', '')
                    """, (q_role, clean_q, topics_str))
                    inserted += 1
                print(f"[Neon Init] Seeded {inserted} curated interview questions across all 4 roles.")
        except Exception as q_err:
            print(f"[Neon Init] Notice: Questions seeding check: {q_err}")

        cur.close()
        conn.close()
        print("[Neon Init] Neon PostgreSQL database is fully ready and synchronized.")
        return True

    except Exception as exc:
        print(f"[Neon Init Error] Failed to connect/initialize PostgreSQL: {exc}")
        return False


if __name__ == "__main__":
    init_postgres_db()
