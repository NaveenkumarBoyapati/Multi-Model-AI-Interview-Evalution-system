from database import get_connection

def inspect_sample_rows():
    conn = get_connection()
    cursor = conn.cursor()
    for iid in [40, 44, 45]:
        print(f"\n================ INTERVIEW {iid} ================")
        cursor.execute("""
            SELECT TOP 4 question_number, question_id, question_text, category, difficulty,
                         start_ms, end_ms, answer_text, word_count, overall_answer_score
            FROM InterviewAnswers
            WHERE interview_id = ?
            ORDER BY question_number
        """, (iid,))
        cols = [c[0] for c in cursor.description]
        for r in cursor.fetchall():
            print(dict(zip(cols, r)))

    cursor.close()
    conn.close()

if __name__ == "__main__":
    inspect_sample_rows()
