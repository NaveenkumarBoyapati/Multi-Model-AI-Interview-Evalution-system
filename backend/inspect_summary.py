import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import get_connection

def inspect_summary():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
    tables = [r[0] for r in cursor.fetchall()]
    print("ALL TABLES:", tables)

    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {t}")
        cnt = cursor.fetchone()[0]
        cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{t}'")
        cols = [r[0] for r in cursor.fetchall()]
        print(f"Table '{t}' has {cnt} rows. Cols: {cols}")

    print("\n--- InterviewHistory IDs ---")
    if "InterviewHistory" in tables:
        cursor.execute("SELECT TOP 20 id, role, overall_score, total_questions, created_at FROM InterviewHistory ORDER BY id DESC")
        for r in cursor.fetchall():
            print("  ", r)

    print("\n--- Interviews IDs ---")
    if "Interviews" in tables:
        cursor.execute("SELECT TOP 20 id, role, overall_score, total_questions, created_at FROM Interviews ORDER BY id DESC")
        for r in cursor.fetchall():
            print("  ", r)

    print("\n--- InterviewAnswers for recent interviews ---")
    if "InterviewAnswers" in tables:
        cursor.execute("""
            SELECT interview_id, COUNT(*) as total_rows, 
                   COUNT(answer_text) as non_null_answers,
                   COUNT(start_ms) as non_null_start_ms
            FROM InterviewAnswers 
            GROUP BY interview_id 
            ORDER BY interview_id DESC
        """)
        for r in cursor.fetchall():
            print("  interview_id:", r[0], "total_rows:", r[1], "non_null_answers:", r[2], "non_null_start_ms:", r[3])

    print("\n--- Detailed InterviewAnswers for interview 45 ---")
    if "InterviewAnswers" in tables:
        cursor.execute("SELECT id, interview_id, question_number, question_text, start_ms, end_ms, answer_text, word_count FROM InterviewAnswers WHERE interview_id = 45 ORDER BY question_number")
        for r in cursor.fetchall():
            print("  Q", r[2], ": start=", r[4], "end=", r[5], "words=", r[7], "ans=", repr(r[6]))

    print("\n--- Detailed InterviewAnswers for interview 40 ---")
    if "InterviewAnswers" in tables:
        cursor.execute("SELECT id, interview_id, question_number, question_text, start_ms, end_ms, answer_text, word_count FROM InterviewAnswers WHERE interview_id = 40 ORDER BY question_number")
        for r in cursor.fetchall():
            print("  Q", r[2], ": start=", r[4], "end=", r[5], "words=", r[7], "ans=", repr(r[6]))

    print("\n--- Detailed InterviewAnswers for interview 44 ---")
    if "InterviewAnswers" in tables:
        cursor.execute("SELECT id, interview_id, question_number, question_text, start_ms, end_ms, answer_text, word_count FROM InterviewAnswers WHERE interview_id = 44 ORDER BY question_number")
        for r in cursor.fetchall():
            print("  Q", r[2], ": start=", r[4], "end=", r[5], "words=", r[7], "ans=", repr(r[6]))

    cursor.close()
    conn.close()

if __name__ == "__main__":
    inspect_summary()
