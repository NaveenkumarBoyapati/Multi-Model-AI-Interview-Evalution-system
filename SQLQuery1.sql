CREATE DATABASE AIInterviewDB;
GO

USE AIInterviewDB;
GO

CREATE TABLE Interviews (
    id INT IDENTITY(1,1) PRIMARY KEY,
    role VARCHAR(100) NOT NULL,
    total_questions INT DEFAULT 20,
    recording_path VARCHAR(500),
    technical_score FLOAT DEFAULT 0,
    communication_score FLOAT DEFAULT 0,
    confidence_score FLOAT DEFAULT 0,
    problem_solving_score FLOAT DEFAULT 0,
    overall_score FLOAT DEFAULT 0,
    feedback VARCHAR(MAX),
    created_at DATETIME DEFAULT GETDATE()
);
GO