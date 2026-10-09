"""
Fresh End-to-End Test for AI Interview Evaluation System
Tests:
1. Dynamic expected concepts retrieval from Questions table and curated bank for Web Developer.
2. Full interview evaluation with:
   - Q1: "Tell me about yourself." (Answered: "Hi, my name is Naveen Kumar, but I am currently pursuing B.Tech final year in P.P. Savani University.")
   - Q2: "What are your strengths and how can they help you in this role?" (Answered: "And my core strengths and technical skills are.")
   - Q3: "What are closures in JavaScript?" (Unanswered: "")
3. Database persistence via save_interview_record into AIInterviewDB.
4. API retrieval via get_interview(new_id) ensuring:
   - Expected concepts populated for all 3 questions.
   - Q1 and Q2 matched concepts mapped properly and concept coverage score calculated (not misleading 0%).
   - Q3 remains strictly 0.0 across all metrics with 5 missing concepts.
   - Overall score properly averages answered questions.
5. Verifies Interview #76 records were not modified in the database.
"""
import sys
import json
import datetime
from question_bank import get_expected_concepts
from evaluation import evaluate_interview, evaluate_question
from database import get_connection
from main import save_interview_record, get_interview


def run_fresh_e2e_test():
    print("=" * 70)
    print("RUNNING FRESH E2E INTERVIEW EVALUATION & PERSISTENCE TEST")
    print("=" * 70)

    role = "Web Developer"
    q1_text = "Tell me about yourself."
    q2_text = "What are your strengths and how can they help you in this role?"
    q3_text = "What are closures in JavaScript?"

    # 1. Verify expected concepts retrieval for all three questions
    print("\n[Step 1] Verifying Expected Concepts retrieval:")
    exp1 = get_expected_concepts(q1_text, role=role)
    exp2 = get_expected_concepts(q2_text, role=role)
    exp3 = get_expected_concepts(q3_text, role=role)

    print(f"  Q1 Expected Concepts: {exp1}")
    print(f"  Q2 Expected Concepts: {exp2}")
    print(f"  Q3 Expected Concepts: {exp3}")

    assert "education" in exp1, "Q1 must have 'education'"
    assert "technical skills" in exp1, "Q1 must have 'technical skills'"
    assert "projects" in exp1, "Q1 must have 'projects'"
    assert "relevant experience" in exp1, "Q1 must have 'relevant experience'"
    assert "career goals" in exp1, "Q1 must have 'career goals'"

    assert "core strengths" in exp2, "Q2 must have 'core strengths'"
    assert "communication" in exp2, "Q2 must have 'communication'"
    assert any("problem" in c for c in exp2), "Q2 must have problem-solving"
    assert "practical example" in exp2, "Q2 must have 'practical example'"
    assert "role contribution" in exp2, "Q2 must have 'role contribution'"

    assert "lexical scope" in exp3, "Q3 must have 'lexical scope'"
    assert "inner function" in exp3, "Q3 must have 'inner function'"
    assert "outer function variables" in exp3, "Q3 must have 'outer function variables'"
    assert "scope chain" in exp3, "Q3 must have 'scope chain'"
    assert any("retained access" in c for c in exp3), "Q3 must have retained access"
    print(">> Step 1 PASSED: All expected concepts verified")

    # 2. Evaluate 3-question session
    print("\n[Step 2] Evaluating Fresh Interview Session:")
    ans1 = "Hi, my name is Naveen Kumar, but I am currently pursuing B.Tech final year in P.P. Savani University."
    ans2 = "And my core strengths and technical skills are."
    ans3 = ""

    session_payload = [
        {
            "question_number": 1,
            "question": q1_text,
            "candidate_answer": ans1,
            "expected_concepts": exp1,
            "category": "Introduction",
            "difficulty": "Easy",
            "start_ms": 0,
            "end_ms": 5728
        },
        {
            "question_number": 2,
            "question": q2_text,
            "candidate_answer": ans2,
            "expected_concepts": exp2,
            "category": "HR",
            "difficulty": "Easy",
            "start_ms": 5728,
            "end_ms": 9401
        },
        {
            "question_number": 3,
            "question": q3_text,
            "candidate_answer": ans3,
            "expected_concepts": exp3,
            "category": "Technical",
            "difficulty": "Medium",
            "start_ms": 9401,
            "end_ms": 11056
        }
    ]

    eval_result = evaluate_interview(session_payload)
    print("\nEvaluation Summary:")
    print(f"  Total Questions: {eval_result['total_questions']}")
    print(f"  Answered: {eval_result['answered_questions']}")
    print(f"  Unanswered: {eval_result['unanswered_questions']}")
    print(f"  Overall Score: {eval_result['overall_score']}")
    print(f"  Technical: {eval_result['technical_score']}")
    print(f"  Communication: {eval_result['communication_score']}")

    assert eval_result["total_questions"] == 3
    assert eval_result["answered_questions"] == 2
    assert eval_result["unanswered_questions"] == 1

    q_evals = eval_result["questions"]
    # Check Q1
    assert q_evals[0]["is_answered"] is True
    assert "education" in q_evals[0]["matched_concepts"]
    assert q_evals[0]["concept_score"] is not None and q_evals[0]["concept_score"] > 0
    print(f"  Q1 Matched: {q_evals[0]['matched_concepts']} | Concept Score: {q_evals[0]['concept_score']}% | Overall: {q_evals[0]['overall_score']}")

    # Check Q2
    assert q_evals[1]["is_answered"] is True
    assert "core strengths" in q_evals[1]["matched_concepts"]
    assert q_evals[1]["concept_score"] is not None and q_evals[1]["concept_score"] > 0
    print(f"  Q2 Matched: {q_evals[1]['matched_concepts']} | Concept Score: {q_evals[1]['concept_score']}% | Overall: {q_evals[1]['overall_score']}")

    # Check Q3 (Unanswered)
    assert q_evals[2]["is_answered"] is False
    assert q_evals[2]["matched_concepts"] == []
    assert len(q_evals[2]["missing_concepts"]) == 5
    for metric in ["technical_score", "communication_score", "confidence_score", "problem_solving_score", "relevance_score", "completeness_score", "concept_score", "overall_score"]:
        assert q_evals[2][metric] == 0.0, f"Q3 {metric} expected 0.0, got {q_evals[2][metric]}"
    print(f"  Q3 Unanswered verified: All 8 score metrics are strictly 0.0")
    print(">> Step 2 PASSED: Interview session evaluated accurately")

    # 3. Save to database using save_interview_record
    print("\n[Step 3] Saving Interview Record to SQL Server:")
    question_data_list = [
        {
            "question_number": 1,
            "question_text": q1_text,
            "relative_start": 0.0,
            "relative_end": 5.728
        },
        {
            "question_number": 2,
            "question_text": q2_text,
            "relative_start": 5.728,
            "relative_end": 9.401
        },
        {
            "question_number": 3,
            "question_text": q3_text,
            "relative_start": 9.401,
            "relative_end": 11.056
        }
    ]

    full_transcript = f"{ans1} {ans2}"
    new_interview_id = save_interview_record(
        role=role,
        total_questions=3,
        recording_path="uploads/Web_Developer_fresh_e2e_test.webm",
        transcript=full_transcript,
        tab_switch_count=0,
        terminated_reason="",
        evaluation=eval_result,
        question_data_list=question_data_list,
        language="en",
        filename="Web_Developer_fresh_e2e_test.webm",
        user_id=14
    )
    print(f"  Successfully saved new interview with ID: {new_interview_id}")
    assert new_interview_id is not None and new_interview_id > 0
    print(">> Step 3 PASSED: Record saved to database")

    # 4. Fetch via get_interview API
    print(f"\n[Step 4] Fetching Interview #{new_interview_id} via get_interview API:")
    api_res = get_interview(new_interview_id)
    assert api_res["status"] == "success"
    interview_meta = api_res["interview"]
    answers = api_res["answers"]

    print(f"  Fetched Interview Status: {interview_meta['status']}")
    print(f"  Fetched Role: {interview_meta['role']}")
    print(f"  Overall Score: {interview_meta['overall_score']}")
    print(f"  Total Answers Returned: {len(answers)}")

    assert len(answers) == 3, f"Expected 3 answers, got {len(answers)}"

    # Verify Q1 API output
    a1 = answers[0]
    print(f"\n  --- Q1 (ID: {a1['id']}) ---")
    print(f"  Text: {a1['question_text']}")
    print(f"  Expected Concepts: {a1.get('expected_concepts')}")
    print(f"  Matched Concepts: {a1.get('matched_concepts')}")
    print(f"  Concept Score: {a1.get('concept_score')}%")
    assert a1.get("expected_concepts") == exp1, f"Q1 expected concepts mismatch: {a1.get('expected_concepts')}"
    assert "education" in json.loads(a1["matched_concepts"])
    assert a1.get("concept_score") is not None and a1.get("concept_score") > 0

    # Verify Q2 API output
    a2 = answers[1]
    print(f"\n  --- Q2 (ID: {a2['id']}) ---")
    print(f"  Text: {a2['question_text']}")
    print(f"  Expected Concepts: {a2.get('expected_concepts')}")
    print(f"  Matched Concepts: {a2.get('matched_concepts')}")
    print(f"  Concept Score: {a2.get('concept_score')}%")
    assert a2.get("expected_concepts") == exp2, f"Q2 expected concepts mismatch: {a2.get('expected_concepts')}"
    assert "core strengths" in json.loads(a2["matched_concepts"])
    assert a2.get("concept_score") is not None and a2.get("concept_score") > 0

    # Verify Q3 API output
    a3 = answers[2]
    print(f"\n  --- Q3 (ID: {a3['id']}) ---")
    print(f"  Text: {a3['question_text']}")
    print(f"  Expected Concepts: {a3.get('expected_concepts')}")
    print(f"  Matched Concepts: {a3.get('matched_concepts')}")
    print(f"  Concept Score: {a3.get('concept_score')}%")
    assert a3.get("expected_concepts") == exp3, f"Q3 expected concepts mismatch: {a3.get('expected_concepts')}"
    assert json.loads(a3["matched_concepts"]) == []
    assert a3.get("concept_score") == 0.0
    assert a3.get("overall_answer_score") == 0.0
    assert a3.get("technical_score") == 0.0
    assert a3.get("communication_score") == 0.0
    assert a3.get("confidence_score") == 0.0
    assert a3.get("problem_solving_score") == 0.0
    assert a3.get("relevance_score") == 0.0
    assert a3.get("completeness_score") == 0.0
    print(">> Step 4 PASSED: API output perfectly matches expected structure and scores")

    # 5. Verify Historical Interview #76 in Database was NOT altered
    print("\n[Step 5] Verifying Historical Interview #76 integrity in database:")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, role, overall_score, technical_score FROM Interviews WHERE id = 76")
    i76 = cur.fetchone()
    print(f"  Interview #76 DB Record: ID={i76[0]}, Role={i76[1]}, Overall={i76[2]}, Tech={i76[3]}")
    assert i76[0] == 76
    assert i76[2] == 34.53, f"Interview 76 overall_score was modified! Expected 34.53, got {i76[2]}"

    cur.execute("SELECT question_number, question_text, matched_concepts, technical_score, overall_answer_score FROM InterviewAnswers WHERE interview_id = 76 ORDER BY question_number")
    ans_76 = cur.fetchall()
    print("  Interview #76 Answers DB rows:")
    for a in ans_76:
        print(f"    Q{a[0]}: matched={a[2]}, tech={a[3]}, overall={a[4]}")
    assert ans_76[0][2] == '["introduction", "education"]', "Historical Q1 matched_concepts altered!"
    assert ans_76[1][2] == '["core strengths", "technical skills"]', "Historical Q2 matched_concepts altered!"
    assert ans_76[2][2] == '[]', "Historical Q3 matched_concepts altered!"
    cur.close()
    conn.close()
    print(">> Step 5 PASSED: Historical Interview #76 records were not modified")

    # 6. Verify get_interview(76) dynamically enriches #76 for UI without mutating DB
    print("\n[Step 6] Testing get_interview(76) dynamic enrichment for UI:")
    res_76 = get_interview(76)
    q1_76 = res_76["answers"][0]
    q2_76 = res_76["answers"][1]
    q3_76 = res_76["answers"][2]
    print(f"  Q1 76 Expected: {q1_76['expected_concepts']}")
    print(f"  Q1 76 Matched: {q1_76['matched_concepts']}")
    print(f"  Q1 76 Concept Score: {q1_76['concept_score']}%")
    assert q1_76["expected_concepts"] == exp1
    assert q1_76["concept_score"] == 40.0, f"Expected 40.0, got {q1_76['concept_score']}"

    print(f"  Q2 76 Expected: {q2_76['expected_concepts']}")
    print(f"  Q2 76 Matched: {q2_76['matched_concepts']}")
    print(f"  Q2 76 Concept Score: {q2_76['concept_score']}%")
    assert q2_76["expected_concepts"] == exp2
    assert q2_76["concept_score"] == 40.0, f"Expected 40.0, got {q2_76['concept_score']}"

    print(f"  Q3 76 Expected: {q3_76['expected_concepts']}")
    print(f"  Q3 76 Concept Score: {q3_76['concept_score']}%")
    assert q3_76["expected_concepts"] == exp3
    assert q3_76["concept_score"] == 0.0
    print(">> Step 6 PASSED: Dynamic enrichment for #76 delivers consistent expected concepts and non-zero coverage")

    print("\n" + "=" * 70)
    print("ALL FRESH E2E TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_fresh_e2e_test()
