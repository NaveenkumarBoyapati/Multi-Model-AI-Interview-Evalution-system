import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import get_connection

def inspect_interview_records():
    conn = get_connection()
    cursor = conn.cursor()

    for iid in [38, 39, 40, 41, 42, 44, 45]:
        cursor.execute("SELECT * FROM Interviews WHERE id = ?", (iid,))
        row = cursor.fetchone()
        col_names = [c[0] for c in cursor.description]
        interviews_dict = dict(zip(col_names, row)) if row else None
        
        cursor.execute("SELECT COUNT(*) FROM InterviewAnswers WHERE interview_id = ?", (iid,))
        ans_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM InterviewAnswers WHERE interview_id = ? AND answer_text IS NOT NULL", (iid,))
        non_null_ans = cursor.fetchone()[0]

        print(f"\n=================== INTERVIEW {iid} ===================")
        if interviews_dict:
            print(f"Role: {interviews_dict['role']} | Total Q: {interviews_dict['total_questions']} | Overall: {interviews_dict['overall_score']} | Tech: {interviews_dict['technical_score']}")
            print(f"Created At: {interviews_dict['created_at']} | Status: {interviews_dict.get('status')}")
            print(f"Transcript: {repr(interviews_dict['transcript'][:60] if interviews_dict['transcript'] else None)}")
        else:
            print("Not in Interviews table!")
        print(f"InterviewAnswers total rows: {ans_count}, with non-null answers: {non_null_ans}")

        cursor.execute("SELECT question_number, question_id, start_ms, end_ms, word_count, answer_text, overall_answer_score FROM InterviewAnswers WHERE interview_id = ? ORDER BY question_number", (iid,))
        for a in cursor.fetchall():
            print(f"  Q{a[0]}: q_id={a[1]}, start_ms={a[2]}, end_ms={a[3]}, words={a[4]}, score={a[6]}, ans={repr(a[5][:40] if a[5] else None)}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    inspect_interview_records()
