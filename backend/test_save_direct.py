import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main import save_interview_record
from database import get_connection

def test_save_direct():
    eval_mock = {
        "overall_score": 75.5,
        "technical_score": 70.0,
        "communication_score": 80.0,
        "confidence_score": 75.0,
        "problem_solving_score": 72.0,
        "relevance_score": 85.0,
        "completeness_score": 70.0,
        "attempted_questions": 3,
        "answered_questions": 2,
        "unanswered_questions": 1,
        "strengths": ["Clear explanation of lists and tuples"],
        "improvements": ["Add more technical depth on memory management"],
        "questions": [
            {
                "question_number": 1,
                "question": "Tell me about yourself.",
                "candidate_answer": "I am a computer science graduate passionate about software engineering.",
                "is_answered": True,
                "technical_score": 75.0,
                "communication_score": 80.0,
                "confidence_score": 75.0,
                "problem_solving_score": 70.0,
                "relevance_score": 85.0,
                "completeness_score": 75.0,
                "overall_score": 76.0,
                "matched_concepts": ["education", "experience"],
                "missing_concepts": [],
                "feedback": "Strong concise introduction."
            },
            {
                "question_number": 2,
                "question": "What is the difference between a list and a tuple?",
                "candidate_answer": "Lists are mutable sequences while tuples are immutable in Python.",
                "is_answered": True,
                "technical_score": 85.0,
                "communication_score": 80.0,
                "confidence_score": 80.0,
                "problem_solving_score": 75.0,
                "relevance_score": 90.0,
                "completeness_score": 80.0,
                "overall_score": 82.0,
                "matched_concepts": ["mutable", "immutable"],
                "missing_concepts": [],
                "feedback": "Accurate distinction."
            },
            {
                "question_number": 3,
                "question": "How does Python manage memory?",
                "candidate_answer": "",
                "is_answered": False,
                "technical_score": 0.0,
                "communication_score": 0.0,
                "confidence_score": 0.0,
                "problem_solving_score": 0.0,
                "relevance_score": 0.0,
                "completeness_score": 0.0,
                "overall_score": 0.0,
                "matched_concepts": [],
                "missing_concepts": ["reference counting", "garbage collector", "memory heap"],
                "feedback": "No answer detected for this question."
            }
        ]
    }

    q_data_mock = [
        {"question_number": 1, "question": "Tell me about yourself.", "relative_start": 0.0, "relative_end": 12.5},
        {"question_number": 2, "question": "What is the difference between a list and a tuple?", "relative_start": 12.5, "relative_end": 28.0},
        {"question_number": 3, "question": "How does Python manage memory?", "relative_start": 28.0, "relative_end": 35.0}
    ]

    print("Calling save_interview_record...")
    new_id = save_interview_record(
        role="Python Developer",
        total_questions=3,
        recording_path="uploads/test_direct.webm",
        transcript="I am a computer science graduate. Lists are mutable sequences while tuples are immutable in Python.",
        tab_switch_count=0,
        terminated_reason="",
        evaluation=eval_mock,
        question_data_list=q_data_mock,
        language="en",
        filename="test_direct.webm"
    )

    print(f"Returned interview_id: {new_id}")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, role, status, duration_seconds, overall_score FROM Interviews WHERE id = ?", (new_id,))
    print("Interviews row:", cur.fetchone())

    cur.execute("SELECT question_number, question_id, question_text, answer_text, word_count, start_ms, end_ms, overall_answer_score FROM InterviewAnswers WHERE interview_id = ? ORDER BY question_number", (new_id,))
    print("\nInterviewAnswers rows:")
    for r in cur.fetchall():
        print(" ", r)

    cur.execute("SELECT interview_id, overall_score, answered_count, answers_evaluated FROM EvaluationResults WHERE interview_id = ?", (new_id,))
    print("\nEvaluationResults row:", cur.fetchone())

    cur.execute("SELECT interview_id, role, overall_score FROM InterviewHistory WHERE interview_id = ?", (new_id,))
    print("\nInterviewHistory row:", cur.fetchone())

    cur.execute("SELECT interview_id, overall_performance FROM Feedback WHERE interview_id = ?", (new_id,))
    print("\nFeedback row:", cur.fetchone())

    cur.close()
    conn.close()

if __name__ == "__main__":
    test_save_direct()
