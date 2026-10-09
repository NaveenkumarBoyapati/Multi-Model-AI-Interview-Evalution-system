-- ====================================================================
-- AI Interview Evaluation System - Full Database Initialization Script
-- Engine: Azure SQL Database / Microsoft SQL Server
-- Note: In Azure SQL, connect directly to target database (e.g. AIInterviewDB)
-- ====================================================================


-- 1. Users Table
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Users')
BEGIN
    CREATE TABLE Users (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(120) NOT NULL,
        email NVARCHAR(200) NOT NULL UNIQUE,
        password_hash NVARCHAR(255) NOT NULL,
        is_admin BIT NOT NULL DEFAULT 0,
        preferred_role NVARCHAR(100) NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        is_active BIT NOT NULL DEFAULT 1
    );
END
GO

-- 2. Roles Table
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Roles')
BEGIN
    CREATE TABLE Roles (
        id INT IDENTITY(1,1) PRIMARY KEY,
        role_name NVARCHAR(100) NOT NULL,
        slug NVARCHAR(80) NOT NULL,
        description NVARCHAR(500) NULL,
        topics NVARCHAR(500) NULL,
        icon NVARCHAR(60) NULL,
        is_active BIT NOT NULL DEFAULT 1
    );
END
GO

-- 3. Questions Table
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Questions')
BEGIN
    CREATE TABLE Questions (
        id INT IDENTITY(1,1) PRIMARY KEY,
        role_name NVARCHAR(100) NOT NULL,
        category NVARCHAR(40) NOT NULL,
        difficulty NVARCHAR(20) NOT NULL,
        question_text NVARCHAR(1000) NOT NULL,
        expected_topics NVARCHAR(1000) NULL,
        reference_answer NVARCHAR(MAX) NULL,
        evaluation_guidance NVARCHAR(1000) NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        is_active BIT NOT NULL DEFAULT 1
    );
END
GO

-- 4. Interviews Table
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Interviews')
BEGIN
    CREATE TABLE Interviews (
        id INT IDENTITY(1,1) PRIMARY KEY,
        role VARCHAR(100) NOT NULL,
        total_questions INT NULL DEFAULT 20,
        recording_path VARCHAR(500) NULL,
        technical_score FLOAT NULL DEFAULT 0,
        communication_score FLOAT NULL DEFAULT 0,
        confidence_score FLOAT NULL DEFAULT 0,
        problem_solving_score FLOAT NULL DEFAULT 0,
        overall_score FLOAT NULL DEFAULT 0,
        feedback VARCHAR(MAX) NULL,
        created_at DATETIME NULL DEFAULT GETDATE(),
        transcript NVARCHAR(MAX) NULL,
        tab_switch_count INT NOT NULL DEFAULT 0,
        terminated_reason NVARCHAR(255) NULL,
        user_id INT NULL,
        status NVARCHAR(20) NULL,
        relevance_score FLOAT NULL,
        duration_seconds FLOAT NULL,
        transcript_language NVARCHAR(10) NULL,
        recording_filename NVARCHAR(255) NULL,
        evaluation_method NVARCHAR(60) NULL,
        completed_at DATETIME2 NULL,
        question_timeline NVARCHAR(MAX) NULL,
        termination_type NVARCHAR(50) NULL,
        security_violation BIT NULL,
        terminated_at DATETIME2 NULL
    );
END
GO

-- 5. InterviewAnswers Table
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'InterviewAnswers')
BEGIN
    CREATE TABLE InterviewAnswers (
        id INT IDENTITY(1,1) PRIMARY KEY,
        interview_id INT NOT NULL,
        question_id INT NULL,
        question_number INT NOT NULL,
        question_text NVARCHAR(1000) NULL,
        category NVARCHAR(40) NULL,
        difficulty NVARCHAR(20) NULL,
        start_ms INT NULL,
        end_ms INT NULL,
        answer_text NVARCHAR(MAX) NULL,
        word_count INT NULL,
        speech_duration_seconds FLOAT NULL,
        technical_score FLOAT NULL,
        communication_score FLOAT NULL,
        confidence_score FLOAT NULL,
        problem_solving_score FLOAT NULL,
        relevance_score FLOAT NULL,
        completeness_score FLOAT NULL,
        overall_answer_score FLOAT NULL,
        semantic_similarity FLOAT NULL,
        matched_concepts NVARCHAR(1000) NULL,
        missing_concepts NVARCHAR(1000) NULL,
        strengths NVARCHAR(MAX) NULL,
        weaknesses NVARCHAR(MAX) NULL,
        feedback NVARCHAR(MAX) NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
    );
END
GO

-- 6. EvaluationResults Table
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'EvaluationResults')
BEGIN
    CREATE TABLE EvaluationResults (
        id INT IDENTITY(1,1) PRIMARY KEY,
        interview_id INT NOT NULL,
        technical_score FLOAT NULL,
        communication_score FLOAT NULL,
        confidence_score FLOAT NULL,
        problem_solving_score FLOAT NULL,
        relevance_score FLOAT NULL,
        overall_score FLOAT NULL,
        answers_evaluated INT NULL,
        answered_count INT NULL,
        technical_coverage FLOAT NULL,
        strengths NVARCHAR(MAX) NULL,
        weaknesses NVARCHAR(MAX) NULL,
        recommendations NVARCHAR(MAX) NULL,
        evaluation_method NVARCHAR(60) NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
    );
END
GO

-- 7. Feedback Table
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Feedback')
BEGIN
    CREATE TABLE Feedback (
        id INT IDENTITY(1,1) PRIMARY KEY,
        interview_id INT NOT NULL,
        overall_performance NVARCHAR(MAX) NULL,
        strengths NVARCHAR(MAX) NULL,
        weaknesses NVARCHAR(MAX) NULL,
        areas_to_improve NVARCHAR(MAX) NULL,
        technical_suggestions NVARCHAR(MAX) NULL,
        communication_suggestions NVARCHAR(MAX) NULL,
        confidence_suggestions NVARCHAR(MAX) NULL,
        problem_solving_suggestions NVARCHAR(MAX) NULL,
        practice_areas NVARCHAR(MAX) NULL,
        summary NVARCHAR(MAX) NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
    );
END
GO

-- 8. InterviewHistory Table
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
END
GO

-- 9. PasswordResets Table
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'PasswordResets')
BEGIN
    CREATE TABLE PasswordResets (
        id INT IDENTITY(1,1) PRIMARY KEY,
        user_id INT NOT NULL,
        token_hash NVARCHAR(64) NOT NULL,
        expires_at DATETIME2 NOT NULL,
        used_at DATETIME2 NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
END
GO

-- 10. UserTokens Table
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'UserTokens')
BEGIN
    CREATE TABLE UserTokens (
        id INT IDENTITY(1,1) PRIMARY KEY,
        user_id INT NOT NULL,
        token_hash NVARCHAR(64) NOT NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        expires_at DATETIME2 NOT NULL,
        is_active BIT NOT NULL DEFAULT 1
    );
END
GO

-- 11. AdminAuditLogs Table
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'AdminAuditLogs')
BEGIN
    CREATE TABLE AdminAuditLogs (
        id INT IDENTITY(1,1) PRIMARY KEY,
        admin_id INT NULL,
        admin_name NVARCHAR(255) NULL,
        admin_email NVARCHAR(255) NULL,
        action NVARCHAR(100) NOT NULL,
        target_type NVARCHAR(100) NULL,
        target_id NVARCHAR(100) NULL,
        result NVARCHAR(50) NOT NULL DEFAULT 'SUCCESS',
        details NVARCHAR(MAX) NULL,
        created_at DATETIME NOT NULL DEFAULT GETDATE()
    );
END
GO

-- 12. Seed Default Interview Roles
IF NOT EXISTS (SELECT * FROM Roles WHERE slug = 'python-developer')
BEGIN
    INSERT INTO Roles (role_name, slug, description, topics, icon, is_active)
    VALUES ('Python Developer', 'python-developer', 'Python, OOP, REST APIs, Backend Frameworks', 'Python, Django, Flask, FastAPI, OOP, SQL', 'code', 1);
END
IF NOT EXISTS (SELECT * FROM Roles WHERE slug = 'java-developer')
BEGIN
    INSERT INTO Roles (role_name, slug, description, topics, icon, is_active)
    VALUES ('Java Developer', 'java-developer', 'Java, Spring Boot, OOP, Multithreading', 'Java, Spring Boot, Hibernate, OOP, Multithreading, SQL', 'coffee', 1);
END
IF NOT EXISTS (SELECT * FROM Roles WHERE slug = 'data-analyst')
BEGIN
    INSERT INTO Roles (role_name, slug, description, topics, icon, is_active)
    VALUES ('Data Analyst', 'data-analyst', 'Data Cleaning, SQL, Power BI, Excel, Tableau', 'SQL, Python, Excel, Power BI, Tableau, Statistics', 'bar-chart', 1);
END
IF NOT EXISTS (SELECT * FROM Roles WHERE slug = 'web-developer')
BEGIN
    INSERT INTO Roles (role_name, slug, description, topics, icon, is_active)
    VALUES ('Web Developer', 'web-developer', 'Frontend & Fullstack Web Development', 'HTML5, CSS3, JavaScript, React, APIs, Responsive Design', 'globe', 1);
END
GO

