from database import get_connection

def check_latest():
    conn = get_connection()
    cursor = conn.cursor()
    print("Latest 5 in Interviews:")
    cursor.execute("SELECT TOP 5 id, role, status, created_at, completed_at, duration_seconds FROM Interviews ORDER BY id DESC")
    for r in cursor.fetchall():
        print(" ", r)

    print("\nLatest 5 in InterviewAnswers:")
    cursor.execute("SELECT TOP 5 id, interview_id, question_number, question_text, answer_text, word_count, start_ms, end_ms, overall_answer_score FROM InterviewAnswers ORDER BY id DESC")
    for r in cursor.fetchall():
        print(" ", r)

    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_latest()
