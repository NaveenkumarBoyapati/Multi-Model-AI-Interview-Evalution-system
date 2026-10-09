"""
Fresh End-to-End Test for Python Developer Interview including Q3 "What is MRO in Python?"
Verifies:
1. End-to-end evaluation with candidate answering MRO thoroughly.
2. Persistence to SQL Server.
3. API payload retrieval via get_interview().
4. End-to-end evaluation with candidate leaving MRO unanswered.
5. Verification that result page displays expected and missing concepts for unanswered questions.
6. Absolute immutability of historical interviews #86, #83, #80, #79, #76.
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from question_bank import get_expected_concepts
from evaluation import evaluate_interview
from main import save_interview_record, get_interview, get_connection

def run_fresh_python_interview_test():
    print("=" * 70)
    print("RUNNING FRESH PYTHON DEVELOPER INTERVIEW & PERSISTENCE VERIFICATION")
    print("=" * 70)

    # -------------------------------------------------------------
    # 1. Fresh Interview with Answered MRO Question
    # -------------------------------------------------------------
    print("\n--- [Fresh Run 1] Candidate Answers MRO Thoroughly ---")
    q1_text = "Tell me about yourself."
    q2_text = "What are your strengths and how can they help you in this role?"
    q3_text = "What is MRO in Python?"

    q1_ans = (
        "Hi, my name is Alex. I graduated with a degree in Computer Science from State University. "
        "I have worked on several Python backend projects including REST APIs with FastAPI and data processing pipelines."
    )
    q2_ans = (
        "My key strengths are analytical problem-solving and proactive communication. "
        "For example, in my previous team project, I identified and resolved a deadlock issue in a multithreaded worker."
    )
    q3_ans = (
        "In Python, MRO stands for Method Resolution Order. It is the order in which Python searches for methods and "
        "attributes in a class hierarchy, especially important in multiple inheritance. Python uses the C3 linearization "
        "algorithm to determine this order, and developers can inspect it at runtime using ClassName.mro() or ClassName.__mro__."
    )

    qa_answered = [
        {
            "question_number": 1,
            "question": q1_text,
            "candidate_answer": q1_ans,
            "expected_concepts": get_expected_concepts(q1_text, role="Python Developer"),
            "category": "Introduction",
            "is_answered": True,
            "words_spoken": len(q1_ans.split()),
            "start_ms": 0,
            "end_ms": 15000
        },
        {
            "question_number": 2,
            "question": q2_text,
            "candidate_answer": q2_ans,
            "expected_concepts": get_expected_concepts(q2_text, role="Python Developer"),
            "category": "HR",
            "is_answered": True,
            "words_spoken": len(q2_ans.split()),
            "start_ms": 16000,
            "end_ms": 32000
        },
        {
            "question_number": 3,
            "question": q3_text,
            "candidate_answer": q3_ans,
            "expected_concepts": get_expected_concepts(q3_text, role="Python Developer"),
            "category": "Technical",
            "is_answered": True,
            "words_spoken": len(q3_ans.split()),
            "start_ms": 33000,
            "end_ms": 55000
        }
    ]

    eval_result_1 = evaluate_interview(qa_answered)
    print(f"Fresh Answered Interview Overall Score: {eval_result_1['overall_score']}")
    print(f"Technical: {eval_result_1['technical_score']}")
    print(f"Concepts: {eval_result_1['concept_score']}")

    q3_eval = eval_result_1["questions"][2]
    print("\nQ3 'What is MRO in Python?' Evaluation:")
    print(f"  Matched Concepts ({len(q3_eval['matched_concepts'])}): {q3_eval['matched_concepts']}")
    print(f"  Missing Concepts ({len(q3_eval['missing_concepts'])}): {q3_eval['missing_concepts']}")
    print(f"  Technical Score: {q3_eval['technical_score']}")
    print(f"  Overall Score: {q3_eval['overall_score']}")

    assert len(q3_eval["matched_concepts"]) == 5, f"Expected 5 matched concepts, got {len(q3_eval['matched_concepts'])}"
    assert len(q3_eval["missing_concepts"]) == 0, f"Expected 0 missing concepts, got {len(q3_eval['missing_concepts'])}"
    assert q3_eval["technical_score"] == 100.0, f"Expected 100.0 tech score, got {q3_eval['technical_score']}"
    assert q3_eval["overall_score"] >= 90.0, f"Expected overall >= 90.0, got {q3_eval['overall_score']}"

    # Persist to database
    question_data_list_1 = [
        {"question_number": 1, "question_text": q1_text, "relative_start": 0.0, "relative_end": 15.0},
        {"question_number": 2, "question_text": q2_text, "relative_start": 16.0, "relative_end": 32.0},
        {"question_number": 3, "question_text": q3_text, "relative_start": 33.0, "relative_end": 55.0},
    ]
    db_id_1 = save_interview_record(
        role="Python Developer",
        total_questions=3,
        recording_path="uploads/Python_Developer_fresh_e2e_test_answered.webm",
        transcript=f"{q1_ans} {q2_ans} {q3_ans}",
        tab_switch_count=0,
        terminated_reason="",
        evaluation=eval_result_1,
        question_data_list=question_data_list_1,
        language="en",
        filename="Python_Developer_fresh_e2e_test_answered.webm",
        user_id=14
    )
    print(f">> Persisted Fresh Answered Interview to DB with ID: {db_id_1}")

    # Fetch via API
    api_res_1 = get_interview(db_id_1)
    ans_3_api = api_res_1["answers"][2]
    matched_api_1 = json.loads(ans_3_api["matched_concepts"]) if isinstance(ans_3_api["matched_concepts"], str) else ans_3_api["matched_concepts"]
    assert ans_3_api["question_text"] == q3_text
    assert len(ans_3_api["expected_concepts"]) == 5
    assert len(matched_api_1) == 5
    assert ans_3_api["technical_score"] == 100.0
    print(f">> PASSED: Fresh answered interview persisted and verified via API.")

    # -------------------------------------------------------------
    # 2. Fresh Interview with Unanswered MRO Question
    # -------------------------------------------------------------
    print("\n--- [Fresh Run 2] Candidate Leaves MRO Unanswered ---")
    qa_unanswered = [
        {
            "question_number": 1,
            "question": q1_text,
            "candidate_answer": q1_ans,
            "expected_concepts": get_expected_concepts(q1_text, role="Python Developer"),
            "category": "Introduction",
            "is_answered": True,
            "words_spoken": len(q1_ans.split()),
            "start_ms": 0,
            "end_ms": 15000
        },
        {
            "question_number": 2,
            "question": q2_text,
            "candidate_answer": q2_ans,
            "expected_concepts": get_expected_concepts(q2_text, role="Python Developer"),
            "category": "HR",
            "is_answered": True,
            "words_spoken": len(q2_ans.split()),
            "start_ms": 16000,
            "end_ms": 32000
        },
        {
            "question_number": 3,
            "question": q3_text,
            "candidate_answer": "",
            "expected_concepts": get_expected_concepts(q3_text, role="Python Developer"),
            "category": "Technical",
            "is_answered": False,
            "words_spoken": 0,
            "start_ms": None,
            "end_ms": None
        }
    ]

    eval_result_2 = evaluate_interview(qa_unanswered)
    print(f"Fresh Unanswered Interview Overall Score: {eval_result_2['overall_score']}")
    q3_unans_eval = eval_result_2["questions"][2]
    print("\nQ3 Unanswered Evaluation:")
    print(f"  Matched Concepts: {q3_unans_eval['matched_concepts']}")
    print(f"  Missing Concepts ({len(q3_unans_eval['missing_concepts'])}): {q3_unans_eval['missing_concepts']}")
    print(f"  Technical Score: {q3_unans_eval['technical_score']}")
    print(f"  Overall Score: {q3_unans_eval['overall_score']}")

    assert q3_unans_eval["matched_concepts"] == []
    assert len(q3_unans_eval["missing_concepts"]) == 5
    assert q3_unans_eval["technical_score"] == 0.0
    assert q3_unans_eval["overall_score"] == 0.0

    # Persist to database
    question_data_list_2 = [
        {"question_number": 1, "question_text": q1_text, "relative_start": 0.0, "relative_end": 15.0},
        {"question_number": 2, "question_text": q2_text, "relative_start": 16.0, "relative_end": 32.0},
        {"question_number": 3, "question_text": q3_text, "relative_start": 33.0, "relative_end": 40.0},
    ]
    db_id_2 = save_interview_record(
        role="Python Developer",
        total_questions=3,
        recording_path="uploads/Python_Developer_fresh_e2e_test_unanswered.webm",
        transcript=f"{q1_ans} {q2_ans}",
        tab_switch_count=0,
        terminated_reason="",
        evaluation=eval_result_2,
        question_data_list=question_data_list_2,
        language="en",
        filename="Python_Developer_fresh_e2e_test_unanswered.webm",
        user_id=14
    )
    print(f">> Persisted Fresh Unanswered Interview to DB with ID: {db_id_2}")

    # Fetch via API
    api_res_2 = get_interview(db_id_2)
    ans_3_unans_api = api_res_2["answers"][2]
    missing_api_2 = json.loads(ans_3_unans_api["missing_concepts"]) if isinstance(ans_3_unans_api["missing_concepts"], str) else ans_3_unans_api["missing_concepts"]
    print(f"\nAPI Payload for Unanswered Q3 (Interview #{db_id_2}):")
    score_val = ans_3_unans_api.get('overall_answer_score') if 'overall_answer_score' in ans_3_unans_api else ans_3_unans_api.get('overall_score')
    print(f"  Overall Answer Score: {score_val}")

    assert len(ans_3_unans_api["expected_concepts"]) == 5, "Expected concepts must not be empty on result page!"
    assert len(missing_api_2) == 5, "Missing concepts must not be empty on result page!"
    assert score_val == 0.0, "Score must remain 0.0"
    print(">> PASSED: Unanswered Q3 correctly displays expected and missing concepts without 'No expected concepts defined'.")

    # -------------------------------------------------------------
    # 3. Immutability Verification for Historical Interviews
    # -------------------------------------------------------------
    print("\n--- [Audit] Immutability of Historical Interviews ---")
    conn = get_connection()
    cursor = conn.cursor()

    historical_expected = {
        86: {"role": "Python Developer", "score": 50.18, "status": "COMPLETED"},
        83: {"role": "Web Developer", "score": 43.35, "status": "COMPLETED"},
        80: {"role": "Data Analyst", "score": 39.31, "status": "COMPLETED"},
        79: {"role": "Java Developer", "score": 24.93, "status": "COMPLETED"},
        76: {"role": "Web Developer", "score": 34.53, "status": "COMPLETED"}
    }

    for i_id, exp in historical_expected.items():
        cursor.execute("SELECT id, role, overall_score, status FROM Interviews WHERE id = ?", (i_id,))
        row = cursor.fetchone()
        assert row is not None, f"Interview #{i_id} not found!"
        assert row[1] == exp["role"], f"Role mismatch for #{i_id}: expected {exp['role']}, got {row[1]}"
        assert abs(float(row[2]) - exp["score"]) < 0.01, f"Score mismatch for #{i_id}: expected {exp['score']}, got {row[2]}"
        assert row[3] == exp["status"], f"Status mismatch for #{i_id}: expected {exp['status']}, got {row[3]}"
        print(f"  Interview #{i_id}: Role={row[1]}, Score={float(row[2]):.2f}, Status={row[3]} [VERIFIED UNCHANGED]")

    conn.close()
    print("\n" + "=" * 70)
    print("ALL FRESH PYTHON DEVELOPER INTERVIEW TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_fresh_python_interview_test()
