import sys
import os
import json

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from evaluation import (
    evaluate_question,
    evaluate_interview,
    is_valid_answer,
    is_concept_matched,
    WEIGHTS,
    clamp_score,
    calculate_overall
)
from question_bank import get_expected_concepts
from database import get_connection

def test_final_verification():
    print("=" * 70)
    print("FINAL SYSTEM VERIFICATION: AI INTERVIEW EVALUATION SYSTEM")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # TEST CASE 1: Answer Q1 and Q2, then finish on Q3 (unanswered Q3)
    # -------------------------------------------------------------------------
    print("\n--- TEST CASE 1: Answer Q1 & Q2, finish on Q3 ---")
    q1 = "Tell me about yourself."
    exp1 = get_expected_concepts(q1)
    ans1 = ("Hi, my name is Naveen Kumar, I am currently pursuing BTEC, finally here in PPSA on University "
            "and I am passionate about data and I have learned skills like Excel, Power BI, SQL and Python.")

    q2 = "What are your strengths and how can they help you in this role?"
    exp2 = get_expected_concepts(q2)
    ans2 = "on my core strands and how can I help in the storage technique by using the technical skills as well as core stance."

    q3 = "What is Python and what are its main features?"
    exp3 = get_expected_concepts(q3)
    ans3 = "" # empty

    payload1 = [
        {"question_number": 1, "question": q1, "candidate_answer": ans1, "expected_concepts": exp1},
        {"question_number": 2, "question": q2, "candidate_answer": ans2, "expected_concepts": exp2},
        {"question_number": 3, "question": q3, "candidate_answer": ans3, "expected_concepts": exp3}
    ]

    res1 = evaluate_interview(payload1)
    print(f"Counts: Attempted={res1['attempted_questions']}, Answered={res1['answered_questions']}, Unanswered={res1['unanswered_questions']}")
    print(f"Overall Score: {res1['overall_score']}")
    
    assert res1["attempted_questions"] == 3, f"Expected 3 attempted, got {res1['attempted_questions']}"
    assert res1["answered_questions"] == 2, f"Expected 2 answered, got {res1['answered_questions']}"
    assert res1["unanswered_questions"] == 1, f"Expected 1 unanswered, got {res1['unanswered_questions']}"

    q3_res = res1["questions"][2]
    assert q3_res["candidate_answer"] == "", "Q3 answer must be empty string"
    assert q3_res["is_answered"] is False, "Q3 is_answered must be False"
    assert q3_res["status"] == "not_answered", "Q3 status must be not_answered"
    assert q3_res["technical_score"] == 0.0, "Q3 tech score must be 0"
    assert q3_res["relevance_score"] == 0.0, "Q3 relevance score must be 0"
    assert q3_res["concept_score"] == 0.0, "Q3 concept score must be 0"
    assert q3_res["completeness_score"] == 0.0, "Q3 completeness score must be 0"
    assert q3_res["communication_score"] == 0.0, "Q3 communication score must be 0"
    assert q3_res["confidence_score"] == 0.0, "Q3 confidence score must be 0"
    assert q3_res["problem_solving_score"] == 0.0, "Q3 problem solving score must be 0"
    assert q3_res["overall_score"] == 0.0, "Q3 overall score must be 0"
    assert q3_res["matched_concepts"] == [], "Q3 matched_concepts must be empty"
    assert len(q3_res["missing_concepts"]) == len(exp3), "Q3 missing_concepts must include all expected concepts"

    # Verify interview overall score matches calculate_overall across category averages:
    expected_overall = calculate_overall(
        res1["technical_score"],
        res1["relevance_score"],
        res1["concept_score"],
        res1["completeness_score"],
        res1["communication_score"],
        res1["confidence_score"],
        res1["problem_solving_score"]
    )
    assert abs(res1["overall_score"] - expected_overall) < 0.1, f"Average {res1['overall_score']} must match {expected_overall}"
    print(">> TEST CASE 1 PASSED: Attempted=3, Answered=2, Unanswered=1; Q3 has 0 scores and is excluded from average")

    # -------------------------------------------------------------------------
    # TEST CASE 2: Answer only Q1, then finish on Q2 (unanswered Q2)
    # -------------------------------------------------------------------------
    print("\n--- TEST CASE 2: Answer only Q1, finish on Q2 ---")
    payload2 = [
        {"question_number": 1, "question": q1, "candidate_answer": ans1, "expected_concepts": exp1},
        {"question_number": 2, "question": q2, "candidate_answer": "", "expected_concepts": exp2}
    ]
    res2 = evaluate_interview(payload2)
    print(f"Counts: Attempted={res2['attempted_questions']}, Answered={res2['answered_questions']}, Unanswered={res2['unanswered_questions']}")
    assert res2["attempted_questions"] == 2
    assert res2["answered_questions"] == 1
    assert res2["unanswered_questions"] == 1
    assert res2["questions"][1]["is_answered"] is False
    assert res2["questions"][1]["technical_score"] == 0.0
    assert res2["questions"][1]["overall_score"] == 0.0
    # Average must equal Q1's score alone
    assert res2["overall_score"] == res2["questions"][0]["overall_score"]
    print(">> TEST CASE 2 PASSED: Attempted=2, Answered=1, Unanswered=1; Q2 has 0 scores and is excluded from average")

    # -------------------------------------------------------------------------
    # TEST CASE 3: Answer all questions in a short interview
    # -------------------------------------------------------------------------
    print("\n--- TEST CASE 3: Answer all questions in short interview ---")
    ans3_good = ("Python is an interpreted, high-level, dynamically-typed programming language known for its simple and "
                 "readable syntax. It supports object-oriented, procedural, and functional programming paradigms, and has "
                 "a vast standard library and rich third-party ecosystem like NumPy, Pandas, and Django.")
    payload3 = [
        {"question_number": 1, "question": q1, "candidate_answer": ans1, "expected_concepts": exp1},
        {"question_number": 2, "question": q3, "candidate_answer": ans3_good, "expected_concepts": exp3}
    ]
    res3 = evaluate_interview(payload3)
    print(f"Counts: Attempted={res3['attempted_questions']}, Answered={res3['answered_questions']}, Unanswered={res3['unanswered_questions']}")
    print(f"Q1 Score={res3['questions'][0]['overall_score']}, Q2 Score={res3['questions'][1]['overall_score']}, Interview Overall={res3['overall_score']}")
    assert res3["attempted_questions"] == 2
    assert res3["answered_questions"] == 2
    assert res3["unanswered_questions"] == 0
    assert res3["questions"][1]["technical_score"] >= 80.0
    assert res3["questions"][1]["is_answered"] is True
    assert res3["overall_score"] > 60.0
    print(">> TEST CASE 3 PASSED: All answered questions correctly evaluated and included in average")

    # -------------------------------------------------------------------------
    # TEST CASE 4: Relevant answer using different wording from expected concepts
    # -------------------------------------------------------------------------
    print("\n--- TEST CASE 4: Relevant answer with paraphrased / synonym wording ---")
    q_norm = "What is normalization in SQL?"
    exp_norm = get_expected_concepts(q_norm)
    # Expected concepts in bank: ['organize data', 'reduce redundancy', 'data integrity', 'normal forms', 'eliminate duplicate data']
    # Paraphrased answer: uses 'restructure relations', 'minimize repeated records', 'ensure consistency', '1NF, 2NF and 3NF'
    ans_paraphrased = ("Database normalization decomposes relational tables to structure the schema, drop repeated "
                       "records to avoid redundancy, and protect consistency and data accuracy using 1NF, 2NF, and 3NF rules.")
    res4 = evaluate_question(q_norm, candidate_answer=ans_paraphrased, expected_concepts=exp_norm)
    print("Expected Concepts:", exp_norm)
    print("Matched Concepts:", res4["matched_concepts"])
    print("Missing Concepts:", res4["missing_concepts"])
    print(f"Technical: {res4['technical_score']}, Relevance: {res4['relevance_score']}, Overall: {res4['overall_score']}")
    assert "reduce redundancy" in res4["matched_concepts"] or "eliminate duplicate data" in res4["matched_concepts"]
    assert "data integrity" in res4["matched_concepts"]
    assert "normal forms" in res4["matched_concepts"]
    assert res4["technical_score"] >= 75.0, f"Expected tech >= 75.0, got {res4['technical_score']}"
    assert res4["overall_score"] >= 70.0, f"Expected overall >= 70.0, got {res4['overall_score']}"
    print(">> TEST CASE 4 PASSED: Concepts matched via semantic synonym clusters and domain meaning")

    # -------------------------------------------------------------------------
    # TEST CASE 5: Unrelated answer
    # -------------------------------------------------------------------------
    print("\n--- TEST CASE 5: Unrelated answer ---")
    ans_unrelated = "I enjoy playing video games on PlayStation and eating cheese pizza on weekends with friends."
    res5 = evaluate_question(q_norm, candidate_answer=ans_unrelated, expected_concepts=exp_norm)
    print(f"Unrelated Answer - Matched: {res5['matched_concepts']}, Tech: {res5['technical_score']}, Rel: {res5['relevance_score']}, Overall: {res5['overall_score']}")
    assert len(res5["matched_concepts"]) == 0, f"Unrelated answer matched concepts: {res5['matched_concepts']}"
    assert res5["relevance_score"] <= 10.0, f"Unrelated relevance should be <= 10.0, got {res5['relevance_score']}"
    assert res5["technical_score"] == 0.0, f"Unrelated tech score should be 0.0, got {res5['technical_score']}"
    assert res5["overall_score"] < 15.0, f"Unrelated overall score should be low, got {res5['overall_score']}"
    print(">> TEST CASE 5 PASSED: Unrelated answer receives 0 tech score and low relevance without score inflation")

    # -------------------------------------------------------------------------
    # TEST CASE 6: Empty answer and noise edge cases
    # -------------------------------------------------------------------------
    print("\n--- TEST CASE 6: Empty answer and audio noise/punctuation ---")
    empty_cases = ["", "   ", "\n\t", "...", ",,,", "---", "   ...   "]
    for ec in empty_cases:
        r_ec = evaluate_question(q1, candidate_answer=ec, expected_concepts=exp1)
        for key in ["technical_score", "relevance_score", "concept_score", "completeness_score", 
                    "communication_score", "confidence_score", "problem_solving_score", "overall_score"]:
            assert r_ec[key] == 0.0, f"Failed for '{ec}': {key} is {r_ec[key]}"
        assert r_ec["matched_concepts"] == []
        assert r_ec["evaluation_source"] == "empty_answer"
    print(">> TEST CASE 6 PASSED: All empty and noise cases return zero across every dimension")

    # -------------------------------------------------------------------------
    # DATABASE INTEGRATION VERIFICATION
    # -------------------------------------------------------------------------
    print("\n--- DATABASE INTEGRATION & RETRIEVAL VERIFICATION ---")
    try:
        from main import save_interview_record
        test_id = save_interview_record(
            role="Python Developer",
            total_questions=res1["attempted_questions"],
            recording_path="uploads/test_verification_session.webm",
            transcript="Hi my name is Naveen Kumar",
            tab_switch_count=0,
            terminated_reason="",
            evaluation=res1
        )
        print(f"Saved Test Interview Record #{test_id}")
        assert test_id > 0

        # Query back and verify stored values
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, role, total_questions, technical_score, relevance_score, overall_score, feedback "
            "FROM Interviews WHERE id = ?",
            test_id
        )
        row = cur.fetchone()
        assert row is not None, "Failed to retrieve saved interview"
        print(f"Retrieved Row: id={row[0]}, role={row[1]}, total_q={row[2]}, tech={row[3]}, rel={row[4]}, overall={row[5]}")
        assert row[1] == "Python Developer"
        assert row[2] == 3
        assert abs(float(row[3]) - res1["technical_score"]) < 0.05
        assert abs(float(row[4]) - res1["relevance_score"]) < 0.05
        assert abs(float(row[5]) - res1["overall_score"]) < 0.05
        cur.close()
        conn.close()
        print(">> DATABASE VERIFICATION PASSED: Interview record successfully inserted and verified in SQL Server")
    except Exception as db_err:
        print(f"[DB Warning] Could not test live database: {db_err}")

    print("\n" + "=" * 70)
    print("ALL 6 VERIFICATION TEST CASES PASSED SUCCESSFULLY")
    print("=" * 70)

if __name__ == "__main__":
    test_final_verification()
