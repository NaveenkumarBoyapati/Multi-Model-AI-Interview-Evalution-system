from database import get_connection
import json

def inspect_exact_format():
    conn = get_connection()
    cursor = conn.cursor()
    for table in ["Interviews", "EvaluationResults", "InterviewHistory", "Feedback", "InterviewAnswers"]:
        print(f"\n================ {table} (interview_id = 44) ================")
        cursor.execute(f"SELECT * FROM {table} WHERE interview_id = 44" if table != "Interviews" else "SELECT * FROM Interviews WHERE id = 44")
        cols = [c[0] for c in cursor.description]
        rows = cursor.fetchall()
        for r in rows[:2]:
            d = dict(zip(cols, r))
            print(d)

    cursor.close()
    conn.close()

if __name__ == "__main__":
    inspect_exact_format()
