from database import get_connection

def inspect_all_answers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT interview_id, COUNT(*) as total_rows,
               SUM(CASE WHEN answer_text IS NOT NULL THEN 1 ELSE 0 END) as non_null_answers,
               SUM(CASE WHEN start_ms IS NOT NULL THEN 1 ELSE 0 END) as non_null_start_ms,
               SUM(CASE WHEN word_count IS NOT NULL AND word_count > 0 THEN 1 ELSE 0 END) as non_zero_words,
               MIN(created_at) as created_at
        FROM InterviewAnswers
        GROUP BY interview_id
        ORDER BY interview_id
    """)
    rows = cursor.fetchall()
    print("InterviewAnswers summary by interview_id:")
    for r in rows:
        print(f"interview_id: {r[0]} | total: {r[1]} | non-null ans: {r[2]} | non-null start_ms: {r[3]} | words>0: {r[4]} | created: {r[5]}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    inspect_all_answers()
