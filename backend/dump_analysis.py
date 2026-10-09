import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import get_connection

def dump_analysis():
    conn = get_connection()
    cursor = conn.cursor()

    print("========================================")
    print("INTERVIEWHISTORY ROWS:")
    print("========================================")
    cursor.execute("SELECT * FROM InterviewHistory")
    cols = [c[0] for c in cursor.description]
    for r in cursor.fetchall():
        print(dict(zip(cols, r)))

    print("\n========================================")
    print("EVALUATIONRESULTS ROWS:")
    print("========================================")
    cursor.execute("SELECT * FROM EvaluationResults")
    cols = [c[0] for c in cursor.description]
    for r in cursor.fetchall():
        d = dict(zip(cols, r))
        print({k: v for k, v in d.items() if k not in ["strengths", "weaknesses", "recommendations"]})

    print("\n========================================")
    print("INTERVIEWS 38-45 vs 55-59:")
    print("========================================")
    cursor.execute("SELECT id, role, total_questions, status, overall_score, technical_score, created_at, completed_at, duration_seconds FROM Interviews WHERE id IN (38, 39, 40, 41, 42, 44, 45, 55, 56, 57, 58, 59) ORDER BY id")
    cols = [c[0] for c in cursor.description]
    for r in cursor.fetchall():
        print(dict(zip(cols, r)))

    print("\n========================================")
    print("SAMPLE QUESTION FROM Questions TABLE:")
    print("========================================")
    cursor.execute("SELECT TOP 5 id, role_name, category, difficulty, question_text FROM Questions")
    cols = [c[0] for c in cursor.description]
    for r in cursor.fetchall():
        print(dict(zip(cols, r)))

    print("\n========================================")
    print("QUESTION_ID LINKING IN InterviewAnswers:")
    print("========================================")
    cursor.execute("""
        SELECT TOP 5 ia.interview_id, ia.question_number, ia.question_id, q.question_text as q_table_text, ia.question_text as ia_text
        FROM InterviewAnswers ia
        LEFT JOIN Questions q ON ia.question_id = q.id
        WHERE ia.interview_id = 45
    """)
    for r in cursor.fetchall():
        print("  Q", r[1], "ia.q_id:", r[2], "| Q.text:", repr(r[3]), "| IA.text:", repr(r[4]))

    cursor.close()
    conn.close()

if __name__ == "__main__":
    dump_analysis()
