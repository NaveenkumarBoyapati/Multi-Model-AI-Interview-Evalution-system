import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import get_connection

def inspect_data():
    conn = get_connection()
    cursor = conn.cursor()

    print("========================================")
    print("ALL ROWS IN InterviewHistory:")
    print("========================================")
    cursor.execute("SELECT * FROM InterviewHistory")
    col_names = [c[0] for c in cursor.description]
    for r in cursor.fetchall():
        print(dict(zip(col_names, r)))

    print("\n========================================")
    print("ALL ROWS IN EvaluationResults:")
    print("========================================")
    cursor.execute("SELECT * FROM EvaluationResults")
    col_names = [c[0] for c in cursor.description]
    for r in cursor.fetchall():
        print(dict(zip(col_names, r)))

    print("\n========================================")
    print("ALL ROWS IN Feedback:")
    print("========================================")
    cursor.execute("SELECT * FROM Feedback")
    col_names = [c[0] for c in cursor.description]
    for r in cursor.fetchall():
        print(dict(zip(col_names, r)))

    print("\n========================================")
    print("DISTINCT interview_id IN InterviewAnswers:")
    print("========================================")
    cursor.execute("""
        SELECT interview_id, COUNT(*) as row_count,
               MIN(question_number) as min_q, MAX(question_number) as max_q,
               COUNT(answer_text) as non_null_answers,
               COUNT(start_ms) as non_null_start_ms,
               MIN(created_at) as created_at
        FROM InterviewAnswers
        GROUP BY interview_id
        ORDER BY interview_id
    """)
    col_names = [c[0] for c in cursor.description]
    for r in cursor.fetchall():
        print(dict(zip(col_names, r)))

    print("\n========================================")
    print("LATEST ROWS IN Interviews (TOP 10):")
    print("========================================")
    cursor.execute("SELECT TOP 10 id, role, total_questions, overall_score, technical_score, created_at, transcript FROM Interviews ORDER BY id DESC")
    col_names = [c[0] for c in cursor.description]
    for r in cursor.fetchall():
        row_dict = dict(zip(col_names, r))
        if row_dict.get("transcript"):
            row_dict["transcript"] = row_dict["transcript"][:60] + "..."
        print(row_dict)

    cursor.close()
    conn.close()

if __name__ == "__main__":
    inspect_data()
